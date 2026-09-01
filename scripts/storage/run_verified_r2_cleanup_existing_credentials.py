#!/usr/bin/env python3
"""Build a dry-run-only R2 cleanup plan using existing repository credentials.

No delete operation exists in this program. A nonzero exit status means the
plan is blocked and must not be used for any later live cleanup implementation.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from botocore.exceptions import ClientError
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials

import build_r2_verified_drive_cleanup as cleanup


ROOT = Path(__file__).resolve().parents[2]
ADMIN = ROOT / "storage_admin" / "verified_r2_cleanup"
OUTPUT = ADMIN / "dry_run"
MIGRATION_PATH = ADMIN / "raw_html_google_drive_manifest.csv"
PROTECTED_PATH = ADMIN / "protected_current_research_r2_keys.csv"

EXPECTED_PROTECTED_KEYS = 5355
EXPECTED_MIGRATION_RECORDS = 2068
EXPECTED_DRIVE_FILE_IDS = 2068
SHARD_COUNT = 8
MAX_DRIVE_WORKERS = 8
DRIVE_TIMEOUT_SECONDS = 30
DRIVE_MAX_ATTEMPTS = 4
TOKEN_URI = "https://oauth2.googleapis.com/token"

REQUIRED_ENV = (
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_ENDPOINT_URL",
    "R2_BUCKET_NAME",
    "GOOGLE_DRIVE_CLIENT_ID",
    "GOOGLE_DRIVE_CLIENT_SECRET",
    "GOOGLE_DRIVE_REFRESH_TOKEN",
)

_thread_local = threading.local()


def require_environment() -> None:
    missing: list[str] = []
    for name in REQUIRED_ENV:
        if os.environ.get(name, "").strip():
            print(f"{name}=set")
        else:
            print(f"{name}=missing")
            missing.append(name)
    if missing:
        raise RuntimeError("missing required environment variables: " + ", ".join(missing))


def refresh_drive_access_token() -> str:
    # Use the scopes originally granted to the existing refresh token. Do not
    # request a different scope during refresh.
    credentials = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_DRIVE_REFRESH_TOKEN"],
        token_uri=TOKEN_URI,
        client_id=os.environ["GOOGLE_DRIVE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_DRIVE_CLIENT_SECRET"],
    )
    credentials.refresh(GoogleAuthRequest())
    if not credentials.token:
        raise RefreshError("Google OAuth refresh returned no access token")
    return credentials.token


def drive_session() -> requests.Session:
    session = getattr(_thread_local, "drive_session", None)
    if session is None:
        session = requests.Session()
        _thread_local.drive_session = session
    return session


def verify_drive_file(file_id: str, access_token: str) -> tuple[str, dict[str, Any] | None, str]:
    url = "https://www.googleapis.com/drive/v3/files/" + quote(file_id, safe="")
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"fields": "id,size,trashed", "supportsAllDrives": "true"}

    for attempt in range(1, DRIVE_MAX_ATTEMPTS + 1):
        try:
            response = drive_session().get(
                url,
                headers=headers,
                params=params,
                timeout=DRIVE_TIMEOUT_SECONDS,
            )
        except requests.RequestException:
            if attempt == DRIVE_MAX_ATTEMPTS:
                return file_id, None, "NETWORK_ERROR"
            time.sleep(min(2 ** (attempt - 1), 8))
            continue

        if response.status_code == 200:
            payload = response.json()
            if payload.get("trashed") is True:
                return file_id, None, "TRASHED"
            size = payload.get("size")
            if size is None:
                return file_id, None, "SIZE_MISSING"
            return file_id, {"drive_size_live": int(size)}, "VERIFIED"

        if response.status_code in {429, 500, 502, 503, 504} and attempt < DRIVE_MAX_ATTEMPTS:
            time.sleep(min(2 ** (attempt - 1), 8))
            continue

        return file_id, None, f"HTTP_{response.status_code}"

    return file_id, None, "UNEXPECTED_RETRY_EXIT"


def verify_drive_files(file_ids: list[str], access_token: str) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    verified: dict[str, dict[str, Any]] = {}
    failures: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=MAX_DRIVE_WORKERS) as pool:
        futures = {pool.submit(verify_drive_file, file_id, access_token): file_id for file_id in file_ids}
        for future in as_completed(futures):
            file_id = futures[future]
            try:
                returned_id, evidence, status = future.result()
            except Exception as exc:
                failures[file_id] = type(exc).__name__
                continue
            if evidence is None:
                failures[returned_id] = status
            else:
                verified[returned_id] = evidence

    return verified, failures


def client_error_code(error: ClientError) -> str:
    return str(error.response.get("Error", {}).get("Code") or "ClientError")


def write_preflight(payload: dict[str, Any]) -> None:
    cleanup.write_json(OUTPUT / "preflight_summary.json", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    require_environment()

    migration_rows = cleanup.load_migration_manifest(MIGRATION_PATH)
    protected_keys = cleanup.load_protected_keys(PROTECTED_PATH)
    drive_file_ids = sorted({cleanup.text(row["drive_file_id"]) for row in migration_rows})

    preflight_reasons: list[str] = []
    if len(protected_keys) != EXPECTED_PROTECTED_KEYS:
        preflight_reasons.append(
            f"PROTECTED_KEY_COUNT_MISMATCH:{len(protected_keys)}!={EXPECTED_PROTECTED_KEYS}"
        )
    if len(migration_rows) != EXPECTED_MIGRATION_RECORDS:
        preflight_reasons.append(
            f"MIGRATION_RECORD_COUNT_MISMATCH:{len(migration_rows)}!={EXPECTED_MIGRATION_RECORDS}"
        )
    if len(drive_file_ids) != EXPECTED_DRIVE_FILE_IDS:
        preflight_reasons.append(
            f"DRIVE_FILE_ID_COUNT_MISMATCH:{len(drive_file_ids)}!={EXPECTED_DRIVE_FILE_IDS}"
        )
    overlap = protected_keys.intersection(cleanup.migration_index(migration_rows))
    if overlap:
        preflight_reasons.append(f"PROTECTED_MIGRATION_OVERLAP:{len(overlap)}")

    r2_client = cleanup.make_r2_client(
        os.environ["R2_ENDPOINT_URL"],
        os.environ["R2_ACCESS_KEY_ID"],
        os.environ["R2_SECRET_ACCESS_KEY"],
    )
    bucket = os.environ["R2_BUCKET_NAME"].strip()

    r2_probe_status = "PASS"
    try:
        cleanup.probe_r2(r2_client, bucket)
    except ClientError as error:
        r2_probe_status = client_error_code(error)
        preflight_reasons.append(f"R2_PREFLIGHT_FAILED:{r2_probe_status}")
    except Exception as error:
        r2_probe_status = type(error).__name__
        preflight_reasons.append(f"R2_PREFLIGHT_FAILED:{r2_probe_status}")

    drive_auth_status = "PASS"
    access_token: str | None = None
    try:
        access_token = refresh_drive_access_token()
    except Exception as error:
        drive_auth_status = type(error).__name__
        preflight_reasons.append(f"DRIVE_AUTH_FAILED:{drive_auth_status}")

    drive_live: dict[str, dict[str, Any]] = {}
    drive_failures: dict[str, str] = {}
    if access_token is not None:
        drive_live, drive_failures = verify_drive_files(drive_file_ids, access_token)
        if drive_failures:
            preflight_reasons.append(f"DRIVE_LIVE_VERIFICATION_FAILED:{len(drive_failures)}")

    drive_failure_counts = dict(sorted(Counter(drive_failures.values()).items()))
    preflight = {
        "dry_run_only": True,
        "r2_probe_status": r2_probe_status,
        "drive_auth_status": drive_auth_status,
        "protected_key_count": len(protected_keys),
        "migration_record_count": len(migration_rows),
        "drive_file_ids_requested": len(drive_file_ids),
        "drive_live_verified": len(drive_live),
        "drive_live_failed": len(drive_failures),
        "drive_failure_reason_counts": drive_failure_counts,
        "preflight_reasons": preflight_reasons,
        "objects_deleted": 0,
        "bytes_deleted": 0,
        "delete_api_calls": 0,
    }
    write_preflight(preflight)

    if r2_probe_status != "PASS":
        print("DRY_RUN_BLOCKED=R2_PREFLIGHT_FAILED")
        return 2

    inventory = cleanup.list_r2_inventory(r2_client, bucket)
    inventory_keys = {row["r2_key"] for row in inventory}
    missing_protected = protected_keys - inventory_keys
    if missing_protected:
        preflight_reasons.append(f"PROTECTED_KEYS_MISSING_FROM_R2:{len(missing_protected)}")

    preliminary_gate = not preflight_reasons
    plan = cleanup.build_plan(
        inventory=inventory,
        migration_rows=migration_rows,
        protected_keys=protected_keys,
        drive_live=drive_live,
        allow_candidates=preliminary_gate,
    )

    candidate_rows = [row for row in plan if row.get("delete_eligible")]
    final_reasons = list(preflight_reasons)
    if preliminary_gate and len(candidate_rows) != EXPECTED_MIGRATION_RECORDS:
        final_reasons.append(
            f"DELETE_CANDIDATE_COUNT_MISMATCH:{len(candidate_rows)}!={EXPECTED_MIGRATION_RECORDS}"
        )
        cleanup.close_all_candidates(
            plan,
            "global gate closed because exact expected candidate count did not match",
        )
        candidate_rows = []

    plan_approved = not final_reasons and len(candidate_rows) == EXPECTED_MIGRATION_RECORDS
    shards = cleanup.balance_shards(candidate_rows, SHARD_COUNT) if plan_approved else []

    cleanup.write_jsonl(OUTPUT / "r2_inventory_before.jsonl", inventory)
    cleanup.write_jsonl(OUTPUT / "r2_cleanup_plan.jsonl", plan)

    shard_dir = OUTPUT / "shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    for stale in shard_dir.glob("shard_*.jsonl"):
        stale.unlink()
    for index, shard in enumerate(shards):
        cleanup.write_jsonl(shard_dir / f"shard_{index:03d}.jsonl", shard)

    summary = cleanup.summarize_plan(plan, shards)
    summary.update(
        {
            "dry_run_only": True,
            "plan_approved": plan_approved,
            "approval_block_reasons": final_reasons,
            "expected_protected_keys": EXPECTED_PROTECTED_KEYS,
            "protected_current_research_keys": len(protected_keys),
            "protected_keys_missing_from_r2": len(missing_protected),
            "expected_migration_records": EXPECTED_MIGRATION_RECORDS,
            "migration_record_count": len(migration_rows),
            "drive_file_ids_requested": len(drive_file_ids),
            "drive_live_verified": len(drive_live),
            "drive_live_failed": len(drive_failures),
            "drive_failure_reason_counts": drive_failure_counts,
            "r2_probe_status": r2_probe_status,
            "drive_auth_status": drive_auth_status,
            "objects_deleted": 0,
            "bytes_deleted": 0,
            "delete_api_calls": 0,
        }
    )

    cleanup.write_json(OUTPUT / "r2_cleanup_summary.json", summary)
    plan_sha = cleanup.sha256_file(OUTPUT / "r2_cleanup_plan.jsonl")
    summary["plan_sha256"] = plan_sha
    cleanup.write_json(OUTPUT / "r2_cleanup_summary.json", summary)

    checksums = {
        "r2_cleanup_plan.jsonl": plan_sha,
        "r2_inventory_before.jsonl": cleanup.sha256_file(OUTPUT / "r2_inventory_before.jsonl"),
        "r2_cleanup_summary.json": cleanup.sha256_file(OUTPUT / "r2_cleanup_summary.json"),
        "preflight_summary.json": cleanup.sha256_file(OUTPUT / "preflight_summary.json"),
    }
    cleanup.write_json(OUTPUT / "checksums.json", checksums)

    print(json.dumps(summary, indent=2, sort_keys=True))
    if not plan_approved:
        print("DRY_RUN_BLOCKED=GLOBAL_APPROVAL_GATE_FAILED")
        return 3

    if summary["delete_candidate_objects"] != EXPECTED_MIGRATION_RECORDS:
        raise RuntimeError("post-summary candidate count invariant failed")
    if summary["shard_count"] != SHARD_COUNT:
        raise RuntimeError("post-summary shard count invariant failed")
    if summary["objects_deleted"] != 0 or summary["delete_api_calls"] != 0:
        raise RuntimeError("dry-run deletion invariant failed")

    print("DRY_RUN_ONLY=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
