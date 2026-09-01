#!/usr/bin/env python3
"""Plan and execute verified R2 cleanup without exposing research data.

Only objects backed by an exact, previously validated Drive migration record
and current Drive ID/size evidence can become deletion candidates. Live deletion
requires an immutable approved plan and revalidates both stores object by object.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import boto3
import pandas as pd
from botocore.config import Config
from botocore.exceptions import ClientError


DELETE_CLASS = "DELETE_CANDIDATE_VERIFIED_DRIVE_COPY"
KEEP_CLASSES = {
    "KEEP_METADATA",
    "KEEP_NOT_MIGRATED",
    "KEEP_VERIFICATION_INCOMPLETE",
    "KEEP_RESEARCH_DEPENDENCY",
    "REVIEW_AMBIGUOUS",
}
BATCH_DELETE_SIZE = 1000


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(retries={"max_attempts": 4, "mode": "adaptive"}),
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory_r2(client, bucket: str) -> list[dict[str, Any]]:
    rows, token = [], None
    while True:
        kwargs: dict[str, Any] = {"Bucket": bucket, "MaxKeys": 1000}
        if token:
            kwargs["ContinuationToken"] = token
        response = client.list_objects_v2(**kwargs)
        rows.extend(
            {
                "bucket": bucket,
                "r2_key": item["Key"],
                "r2_size": int(item["Size"]),
                "r2_etag": item["ETag"].strip('"'),
                "r2_last_modified": item["LastModified"].isoformat(),
                "r2_storage_class": item.get("StorageClass", ""),
            }
            for item in response.get("Contents", [])
        )
        if not response.get("IsTruncated"):
            return rows
        token = response["NextContinuationToken"]


def load_drive_inventory(directory: Path) -> dict[str, dict[str, Any]]:
    inventory: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            file_id = str(row.get("ID") or "")
            if file_id:
                if file_id in inventory:
                    raise ValueError(f"duplicate Drive file ID: {file_id}")
                inventory[file_id] = {"drive_size_live": int(row["Size"]), "drive_path_live": row["Path"]}
    return inventory


def _metadata_key(key: str, size: int) -> bool:
    suffix = Path(key).suffix.lower()
    return size <= 10 * 1024 * 1024 and suffix in {".json", ".jsonl", ".csv", ".txt", ".yaml", ".yml"}


def build_plan(
    inventory: list[dict[str, Any]],
    migration: pd.DataFrame,
    dependency_keys: set[str],
    drive_live: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if migration["r2_object_key"].duplicated().any():
        raise ValueError("duplicate R2 assignments in migration manifest")
    migration_by_key = migration.set_index("r2_object_key", drop=False).to_dict("index")
    plan = []
    for item in inventory:
        key, size = item["r2_key"], item["r2_size"]
        row = dict(item)
        row.update(
            {
                "drive_file_id": "",
                "drive_path": "",
                "drive_size": None,
                "drive_checksum": "",
                "verification_method": "",
                "delete_eligible": False,
            }
        )
        if key in dependency_keys:
            classification, reason = "KEEP_RESEARCH_DEPENDENCY", "current canonical filing manifest references this R2 key"
        elif key in migration_by_key:
            evidence = migration_by_key[key]
            file_id = str(evidence.get("drive_file_id") or "")
            live = drive_live.get(file_id)
            checks = {
                "migration_status": evidence.get("migration_status") in {"uploaded", "skipped_existing_match"},
                "verification_status": evidence.get("verification_status") == "verified_size_and_sha",
                "manifest_sha": str(evidence.get("r2_sha256")) == str(evidence.get("drive_sha256_app_property")),
                "manifest_size": int(evidence.get("r2_html_bytes")) == int(evidence.get("drive_size")),
                "live_r2_size": size == int(evidence.get("r2_html_bytes")),
                "live_drive": live is not None,
                "live_drive_size": live is not None and int(live["drive_size_live"]) == int(evidence.get("drive_size")),
            }
            row.update(
                {
                    "drive_file_id": file_id,
                    "drive_path": live["drive_path_live"] if live else "",
                    "drive_size": int(evidence.get("drive_size")),
                    "drive_checksum": str(evidence.get("r2_sha256")),
                }
            )
            if all(checks.values()):
                classification, reason = DELETE_CLASS, "trusted SHA-256 migration manifest plus current R2/Drive size and Drive ID"
                row["delete_eligible"] = True
                row["verification_method"] = "SHA256_MIGRATION_MANIFEST+LIVE_R2_SIZE+LIVE_DRIVE_ID_SIZE"
            else:
                classification = "KEEP_VERIFICATION_INCOMPLETE"
                reason = "failed checks: " + ",".join(name for name, passed in checks.items() if not passed)
        elif _metadata_key(key, size):
            classification, reason = "KEEP_METADATA", "small metadata or state object"
        else:
            classification, reason = "KEEP_NOT_MIGRATED", "no verified Drive migration mapping"
        row.update({"classification": classification, "reason": reason})
        plan.append(row)
    return plan


def balance_shards(candidates: list[dict[str, Any]], shard_count: int) -> list[list[dict[str, Any]]]:
    shards: list[list[dict[str, Any]]] = [[] for _ in range(max(1, shard_count))]
    totals = [0] * len(shards)
    seen: set[str] = set()
    for row in sorted(candidates, key=lambda value: value["r2_size"], reverse=True):
        if row["r2_key"] in seen:
            raise ValueError(f"duplicate shard assignment: {row['r2_key']}")
        index = min(range(len(shards)), key=totals.__getitem__)
        shards[index].append(row)
        totals[index] += int(row["r2_size"])
        seen.add(row["r2_key"])
    return shards


def summarize(plan: list[dict[str, Any]], shards: list[list[dict[str, Any]]]) -> dict[str, Any]:
    counts, sizes = Counter(), Counter()
    for row in plan:
        counts[row["classification"]] += 1
        sizes[row["classification"]] += int(row["r2_size"])
    total_objects, total_bytes = len(plan), sum(int(row["r2_size"]) for row in plan)
    delete_objects, delete_bytes = counts[DELETE_CLASS], sizes[DELETE_CLASS]
    return {
        "total_r2_objects": total_objects,
        "total_r2_bytes": total_bytes,
        "classification_object_counts": dict(counts),
        "classification_bytes": dict(sizes),
        "delete_candidate_objects": delete_objects,
        "delete_candidate_bytes": delete_bytes,
        "retained_objects": total_objects - delete_objects,
        "retained_bytes": total_bytes - delete_bytes,
        "expected_storage_reduction_pct": 100 * delete_bytes / total_bytes if total_bytes else 0,
        "shard_count": len(shards),
        "objects_per_shard": [len(shard) for shard in shards],
        "bytes_per_shard": [sum(int(row["r2_size"]) for row in shard) for shard in shards],
        "batch_delete_size": BATCH_DELETE_SIZE,
        "duplicate_shard_assignments": 0,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def create_plan(args: argparse.Namespace) -> None:
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    inventory = inventory_r2(s3_client(), os.environ["R2_BUCKET_NAME"])
    migration = pd.read_csv(args.migration_manifest)
    dependencies = set(pd.read_parquet(args.filing_manifest)["r2_object_key"])
    plan = build_plan(inventory, migration, dependencies, load_drive_inventory(Path(args.drive_inventory_dir)))
    candidates = [row for row in plan if row["delete_eligible"]]
    shards = balance_shards(candidates, args.shard_count)
    write_jsonl(output / "r2_inventory_before.jsonl", inventory)
    write_jsonl(output / "r2_cleanup_plan.jsonl", plan)
    shard_dir = output / "shards"
    shard_dir.mkdir(exist_ok=True)
    for index, shard in enumerate(shards):
        write_jsonl(shard_dir / f"shard_{index:03d}.jsonl", shard)
    summary = summarize(plan, shards)
    summary.update({"execute_delete": False, "objects_deleted": 0, "bytes_deleted": 0, "plan_sha256": sha256_file(output / "r2_cleanup_plan.jsonl")})
    (output / "r2_cleanup_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    checksums = {str(path.relative_to(output)): sha256_file(path) for path in output.rglob("*") if path.is_file()}
    (output / "checksums.json").write_text(json.dumps(checksums, indent=2, sort_keys=True) + "\n")


def _head_matches(client, bucket: str, row: dict[str, Any]) -> tuple[bool, str]:
    try:
        head = client.head_object(Bucket=bucket, Key=row["r2_key"])
    except ClientError as error:
        status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        return False, "ALREADY_ABSENT" if status == 404 else f"HEAD_FAILED_{status}"
    etag = str(head.get("ETag", "")).strip('"')
    return (int(head["ContentLength"]) == int(row["r2_size"]) and etag == row["r2_etag"], "MATCH" if int(head["ContentLength"]) == int(row["r2_size"]) and etag == row["r2_etag"] else "R2_CHANGED_AFTER_PLAN")


def execute_shard(args: argparse.Namespace) -> None:
    rows = read_jsonl(Path(args.shard))
    if any(row["classification"] != DELETE_CLASS or not row["delete_eligible"] for row in rows):
        raise ValueError("shard contains object outside verified deletion plan")
    drive = load_drive_inventory(Path(args.drive_inventory_dir))
    client, bucket = s3_client(), os.environ["R2_BUCKET_NAME"]
    started = time.monotonic()
    eligible, results = [], []
    with ThreadPoolExecutor(max_workers=min(16, max(1, args.max_parallel))) as pool:
        checks = list(pool.map(lambda row: _head_matches(client, bucket, row), rows))
    for row, (r2_ok, r2_status) in zip(rows, checks):
        live = drive.get(row["drive_file_id"])
        drive_ok = live is not None and int(live["drive_size_live"]) == int(row["drive_size"])
        if r2_ok and drive_ok:
            eligible.append(row)
            results.append({"r2_key": row["r2_key"], "status": "WOULD_DELETE" if not args.execute_delete else "PENDING_DELETE", "size": row["r2_size"]})
        else:
            results.append({"r2_key": row["r2_key"], "status": "SKIP_DELETE", "reason": r2_status if not r2_ok else "DRIVE_LIVE_VERIFICATION_FAILED", "size": row["r2_size"]})
    delete_calls = 0
    if args.execute_delete:
        for start in range(0, len(eligible), BATCH_DELETE_SIZE):
            batch = eligible[start : start + BATCH_DELETE_SIZE]
            response = client.delete_objects(Bucket=bucket, Delete={"Objects": [{"Key": row["r2_key"]} for row in batch], "Quiet": False})
            delete_calls += 1
            errors = {item["Key"]: item for item in response.get("Errors", [])}
            for result in results:
                if result["status"] == "PENDING_DELETE" and result["r2_key"] in {row["r2_key"] for row in batch}:
                    result["status"] = "DELETE_FAILED" if result["r2_key"] in errors else "DELETED_PENDING_VERIFY"
        for result in results:
            if result["status"] == "DELETED_PENDING_VERIFY":
                exists, status = _head_matches(client, bucket, next(row for row in rows if row["r2_key"] == result["r2_key"]))
                result["status"] = "DELETE_VERIFICATION_FAILED" if exists or status != "ALREADY_ABSENT" else "DELETED_VERIFIED_ABSENT"
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "delete_results.jsonl", results)
    elapsed = time.monotonic() - started
    deleted = [row for row in results if row["status"] == "DELETED_VERIFIED_ABSENT"]
    summary = {
        "execute_delete": args.execute_delete,
        "planned_objects": len(rows),
        "verified_for_action": len(eligible),
        "objects_deleted": len(deleted),
        "bytes_deleted": sum(int(row["size"]) for row in deleted),
        "skipped_objects": sum(row["status"] == "SKIP_DELETE" for row in results),
        "failed_deletions": sum("FAILED" in row["status"] for row in results),
        "delete_api_calls": delete_calls,
        "max_parallel": args.max_parallel,
        "elapsed_seconds": elapsed,
        "objects_per_second": len(deleted) / elapsed if elapsed else 0,
        "bytes_per_second": sum(int(row["size"]) for row in deleted) / elapsed if elapsed else 0,
    }
    (output / "shard_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--migration-manifest", required=True)
    plan.add_argument("--filing-manifest", required=True)
    plan.add_argument("--drive-inventory-dir", required=True)
    plan.add_argument("--output-dir", required=True)
    plan.add_argument("--shard-count", type=int, default=8)
    execute = sub.add_parser("execute-shard")
    execute.add_argument("--shard", required=True)
    execute.add_argument("--drive-inventory-dir", required=True)
    execute.add_argument("--output-dir", required=True)
    execute.add_argument("--max-parallel", type=int, default=8)
    execute.add_argument("--execute-delete", action="store_true")
    return root


if __name__ == "__main__":
    arguments = parser().parse_args()
    create_plan(arguments) if arguments.command == "plan" else execute_shard(arguments)
