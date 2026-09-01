#!/usr/bin/env python3
"""Fail-closed planning primitives for R2 -> Google Drive cleanup.

This module is intentionally incapable of deleting objects. It can only:
- validate local migration/protection manifests,
- read current R2 object metadata,
- evaluate current Google Drive evidence supplied by the runner,
- classify every R2 object, and
- create a deterministic dry-run plan and balanced shards.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import boto3
from botocore.config import Config


DELETE_CLASS = "DELETE_CANDIDATE_VERIFIED_DRIVE_COPY"
KEEP_RESEARCH = "KEEP_RESEARCH_DEPENDENCY"
KEEP_NOT_MIGRATED = "KEEP_NOT_IN_VERIFIED_MIGRATION"
KEEP_INCOMPLETE = "KEEP_VERIFICATION_INCOMPLETE"
REVIEW_GLOBAL_GATE = "REVIEW_GLOBAL_GATE_FAILED"

MIGRATION_OK = {"uploaded", "skipped_existing_match"}
VERIFICATION_OK = "verified_size_and_sha"

REQUIRED_MIGRATION_COLUMNS = {
    "r2_object_key",
    "r2_html_bytes",
    "r2_sha256",
    "drive_file_id",
    "drive_size",
    "drive_sha256_app_property",
    "migration_status",
    "verification_status",
}
REQUIRED_PROTECTED_COLUMNS = {"r2_object_key"}


def text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def sha256_text(value: Any) -> str:
    return text(value).lower()


def exact_int(value: Any, field: str) -> int:
    raw = text(value)
    if not raw:
        raise ValueError(f"missing integer field: {field}")
    try:
        number = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid integer field {field}: {raw!r}") from exc
    if number != number.to_integral_value():
        raise ValueError(f"non-integral value in {field}: {raw!r}")
    return int(number)


def validate_r2_endpoint(endpoint: str) -> str:
    normalized = text(endpoint).rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme != "https":
        raise ValueError("R2 endpoint must use https")
    if not parsed.hostname or not parsed.hostname.endswith(".r2.cloudflarestorage.com"):
        raise ValueError("R2 endpoint hostname is not a Cloudflare R2 S3 endpoint")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise ValueError("R2 endpoint must not contain a path, query, or fragment")
    return normalized


def make_r2_client(endpoint: str, access_key_id: str, secret_access_key: str):
    """Create the Cloudflare R2 S3 client used only for reads in this module."""
    return boto3.client(
        service_name="s3",
        endpoint_url=validate_r2_endpoint(endpoint),
        aws_access_key_id=text(access_key_id),
        aws_secret_access_key=text(secret_access_key),
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            retries={"max_attempts": 5, "mode": "standard"},
        ),
    )


def probe_r2(client, bucket: str) -> None:
    client.list_objects_v2(Bucket=text(bucket), MaxKeys=1)


def list_r2_inventory(client, bucket: str) -> list[dict[str, Any]]:
    bucket_name = text(bucket)
    paginator = client.get_paginator("list_objects_v2")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for page in paginator.paginate(Bucket=bucket_name, PaginationConfig={"PageSize": 1000}):
        for item in page.get("Contents", []):
            key = text(item.get("Key"))
            if not key:
                raise ValueError("R2 inventory returned an empty object key")
            if key in seen:
                raise ValueError(f"duplicate R2 key in live inventory: {key}")
            seen.add(key)
            modified = item.get("LastModified")
            rows.append(
                {
                    "r2_key": key,
                    "r2_size": int(item.get("Size", 0)),
                    "r2_etag": text(item.get("ETag")).strip('"'),
                    "r2_last_modified": modified.isoformat() if modified is not None else "",
                }
            )

    rows.sort(key=lambda row: row["r2_key"])
    return rows


def read_csv(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = required_columns - columns
        if missing:
            raise ValueError(f"{path} missing columns: {', '.join(sorted(missing))}")
        return [dict(row) for row in reader]


def load_migration_manifest(path: Path) -> list[dict[str, str]]:
    rows = read_csv(path, REQUIRED_MIGRATION_COLUMNS)
    seen_keys: set[str] = set()
    seen_drive_ids: set[str] = set()

    for row in rows:
        key = text(row.get("r2_object_key"))
        drive_id = text(row.get("drive_file_id"))
        if not key or not drive_id:
            raise ValueError("migration manifest contains an empty R2 key or Drive file ID")
        if key in seen_keys:
            raise ValueError(f"duplicate R2 key in migration manifest: {key}")
        if drive_id in seen_drive_ids:
            raise ValueError(f"duplicate Drive file ID in migration manifest: {drive_id}")
        seen_keys.add(key)
        seen_drive_ids.add(drive_id)

        r2_bytes = exact_int(row.get("r2_html_bytes"), "r2_html_bytes")
        drive_bytes = exact_int(row.get("drive_size"), "drive_size")
        if r2_bytes < 0 or drive_bytes < 0:
            raise ValueError("negative object size in migration manifest")

        r2_sha = sha256_text(row.get("r2_sha256"))
        drive_sha = sha256_text(row.get("drive_sha256_app_property"))
        if len(r2_sha) != 64 or len(drive_sha) != 64:
            raise ValueError(f"invalid SHA-256 length for migration key: {key}")

    return rows


def load_protected_keys(path: Path) -> set[str]:
    rows = read_csv(path, REQUIRED_PROTECTED_COLUMNS)
    keys = [text(row.get("r2_object_key")) for row in rows]
    if any(not key for key in keys):
        raise ValueError("protected-key manifest contains an empty R2 key")
    if len(keys) != len(set(keys)):
        raise ValueError("protected-key manifest contains duplicate R2 keys")
    return set(keys)


def migration_index(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {text(row["r2_object_key"]): row for row in rows}


def migration_row_checks(
    live_r2: dict[str, Any],
    migration: dict[str, str],
    drive_live: dict[str, dict[str, Any]],
) -> dict[str, bool]:
    drive_id = text(migration.get("drive_file_id"))
    drive_evidence = drive_live.get(drive_id)
    expected_r2_size = exact_int(migration.get("r2_html_bytes"), "r2_html_bytes")
    expected_drive_size = exact_int(migration.get("drive_size"), "drive_size")

    return {
        "migration_status": text(migration.get("migration_status")) in MIGRATION_OK,
        "verification_status": text(migration.get("verification_status")) == VERIFICATION_OK,
        "manifest_sha_match": sha256_text(migration.get("r2_sha256"))
        == sha256_text(migration.get("drive_sha256_app_property")),
        "manifest_size_match": expected_r2_size == expected_drive_size,
        "current_r2_size_match": int(live_r2["r2_size"]) == expected_r2_size,
        "current_drive_file_present": drive_evidence is not None,
        "current_drive_size_match": drive_evidence is not None
        and int(drive_evidence["drive_size_live"]) == expected_drive_size,
    }


def build_plan(
    inventory: list[dict[str, Any]],
    migration_rows: list[dict[str, str]],
    protected_keys: set[str],
    drive_live: dict[str, dict[str, Any]],
    allow_candidates: bool,
) -> list[dict[str, Any]]:
    migrations = migration_index(migration_rows)
    plan: list[dict[str, Any]] = []

    for live in inventory:
        key = text(live["r2_key"])
        row: dict[str, Any] = {
            **live,
            "classification": KEEP_NOT_MIGRATED,
            "delete_eligible": False,
            "reason": "not present in verified Drive migration manifest",
            "drive_file_id": "",
            "expected_sha256": "",
            "checks": {},
        }

        if key in protected_keys:
            row.update(
                {
                    "classification": KEEP_RESEARCH,
                    "reason": "current research dependency; protected unconditionally",
                }
            )
        elif key in migrations:
            migration = migrations[key]
            checks = migration_row_checks(live, migration, drive_live)
            failed = [name for name, passed in checks.items() if not passed]
            row.update(
                {
                    "drive_file_id": text(migration.get("drive_file_id")),
                    "expected_sha256": sha256_text(migration.get("r2_sha256")),
                    "checks": checks,
                }
            )
            if failed:
                row.update(
                    {
                        "classification": KEEP_INCOMPLETE,
                        "reason": "failed checks: " + ",".join(failed),
                    }
                )
            elif allow_candidates:
                row.update(
                    {
                        "classification": DELETE_CLASS,
                        "delete_eligible": True,
                        "reason": "all manifest and current Drive/R2 size checks passed",
                    }
                )
            else:
                row.update(
                    {
                        "classification": REVIEW_GLOBAL_GATE,
                        "reason": "row checks passed but global approval gate is closed",
                    }
                )

        plan.append(row)

    return plan


def close_all_candidates(plan: list[dict[str, Any]], reason: str) -> None:
    for row in plan:
        if row.get("delete_eligible"):
            row["delete_eligible"] = False
            row["classification"] = REVIEW_GLOBAL_GATE
            row["reason"] = reason


def balance_shards(candidates: list[dict[str, Any]], shard_count: int) -> list[list[dict[str, Any]]]:
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    shards: list[list[dict[str, Any]]] = [[] for _ in range(shard_count)]
    byte_totals = [0 for _ in range(shard_count)]
    assigned: set[str] = set()

    for row in sorted(candidates, key=lambda item: (-int(item["r2_size"]), item["r2_key"])):
        key = text(row["r2_key"])
        if key in assigned:
            raise ValueError(f"duplicate candidate assignment: {key}")
        index = min(range(shard_count), key=lambda idx: (byte_totals[idx], idx))
        shards[index].append(row)
        byte_totals[index] += int(row["r2_size"])
        assigned.add(key)

    return shards


def summarize_plan(plan: list[dict[str, Any]], shards: list[list[dict[str, Any]]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    sizes: Counter[str] = Counter()
    for row in plan:
        label = text(row["classification"])
        counts[label] += 1
        sizes[label] += int(row["r2_size"])

    total_objects = len(plan)
    total_bytes = sum(int(row["r2_size"]) for row in plan)
    candidates = [row for row in plan if bool(row.get("delete_eligible"))]
    candidate_bytes = sum(int(row["r2_size"]) for row in candidates)

    return {
        "total_r2_objects": total_objects,
        "total_r2_bytes": total_bytes,
        "classification_object_counts": dict(sorted(counts.items())),
        "classification_bytes": dict(sorted(sizes.items())),
        "delete_candidate_objects": len(candidates),
        "delete_candidate_bytes": candidate_bytes,
        "retained_objects": total_objects - len(candidates),
        "retained_bytes": total_bytes - candidate_bytes,
        "expected_storage_reduction_pct": (100.0 * candidate_bytes / total_bytes) if total_bytes else 0.0,
        "shard_count": len(shards),
        "objects_per_shard": [len(shard) for shard in shards],
        "bytes_per_shard": [sum(int(row["r2_size"]) for row in shard) for shard in shards],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
