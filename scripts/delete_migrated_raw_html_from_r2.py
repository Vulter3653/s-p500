#!/usr/bin/env python3
"""Delete only manifest-pinned R2 raw HTML after verified Drive migration."""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import boto3
from botocore.config import Config


SUCCESS_MIGRATION_STATUSES = {"uploaded", "skipped_existing_match"}
SUCCESS_VERIFICATION_STATUS = "verified_size_and_sha"
CHECKPOINT_FIELDS = [
    "object_key",
    "delete_attempted",
    "delete_api_error",
    "error_code",
    "error_message",
    "deleted_at_utc",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_and_validate_manifest(path: Path, expected_count: int) -> tuple[list[str], dict[str, int | bool]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"r2_object_key", "migration_status", "verification_status"}
    columns = set(rows[0]) if rows else set()
    missing_columns = sorted(required - columns)
    if missing_columns:
        raise ValueError("missing required manifest columns: " + ", ".join(missing_columns))

    keys = [row["r2_object_key"].strip() for row in rows]
    counts = Counter(keys)
    blank_count = sum(not key for key in keys)
    duplicate_count = sum(count - 1 for key, count in counts.items() if key and count > 1)
    invalid_status_count = sum(
        row["migration_status"].strip() not in SUCCESS_MIGRATION_STATUSES
        or row["verification_status"].strip() != SUCCESS_VERIFICATION_STATUS
        for row in rows
    )
    summary: dict[str, int | bool] = {
        "manifest_rows": len(rows),
        "unique_object_keys": len({key for key in keys if key}),
        "eligible_delete_count": len(rows) - invalid_status_count - blank_count,
        "invalid_status_count": invalid_status_count,
        "duplicate_key_count": duplicate_count,
        "blank_key_count": blank_count,
        "expected_count_match": len(rows) == expected_count,
    }
    errors = []
    if len(rows) != expected_count:
        errors.append(f"manifest row count {len(rows)} != expected count {expected_count}")
    if blank_count:
        errors.append(f"blank object keys: {blank_count}")
    if duplicate_count:
        errors.append(f"duplicate object keys: {duplicate_count}")
    if invalid_status_count:
        errors.append(f"invalid migration or verification statuses: {invalid_status_count}")
    if errors:
        raise ValueError("; ".join(errors))
    return keys, summary


def make_r2_client():
    required = [
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_ENDPOINT_URL",
        "R2_BUCKET_NAME",
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError("missing required environment variables: " + ", ".join(missing))
    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(retries={"max_attempts": 8, "mode": "standard"}),
    )


def chunks(values: list[str], size: int = 1000) -> Iterable[list[str]]:
    for start in range(0, len(values), size):
        yield values[start:start + size]


def delete_manifest_keys(client, bucket: str, keys: list[str]) -> tuple[list[dict], int]:
    results: list[dict] = []
    batch_count = 0
    for batch in chunks(keys):
        batch_count += 1
        attempted_at = utc_now()
        try:
            response = client.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": key} for key in batch], "Quiet": True},
            )
            errors_by_key = {
                item.get("Key", ""): item for item in response.get("Errors", [])
            }
            for key in batch:
                error = errors_by_key.get(key)
                results.append({
                    "object_key": key,
                    "delete_attempted": 1,
                    "delete_api_error": int(error is not None),
                    "error_code": error.get("Code", "") if error else "",
                    "error_message": error.get("Message", "") if error else "",
                    "deleted_at_utc": attempted_at,
                })
        except Exception as error:  # batch failure must be auditable per key
            for key in batch:
                results.append({
                    "object_key": key,
                    "delete_attempted": 1,
                    "delete_api_error": 1,
                    "error_code": type(error).__name__,
                    "error_message": str(error)[:500],
                    "deleted_at_utc": attempted_at,
                })
    return results, batch_count


def inspect_bucket_manifest_keys(
    client, bucket: str, keys: list[str]
) -> tuple[list[str], int, int]:
    target_keys = set(keys)
    remaining: list[str] = []
    bucket_object_count = 0
    bucket_total_bytes = 0
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for item in page.get("Contents", []):
            bucket_object_count += 1
            bucket_total_bytes += int(item.get("Size", 0))
            key = item.get("Key", "")
            if key in target_keys:
                remaining.append(key)
    return sorted(remaining), bucket_object_count, bucket_total_bytes


def write_outputs(
    output_dir: Path,
    validation: dict[str, int | bool],
    results: list[dict],
    batch_count: int,
    mode: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    failed = [row for row in results if row["delete_api_error"]]
    attempted = sum(int(row["delete_attempted"]) for row in results)

    with (output_dir / "r2_deletion_checkpoint.jsonl").open("w", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    with (output_dir / "r2_deletion_failed_cases.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=CHECKPOINT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(failed)

    summary = dict(validation)
    summary.update({
        "mode": mode,
        "delete_batch_count": batch_count,
        "delete_attempt_count": attempted,
        "delete_api_success_count": attempted - len(failed),
        "delete_api_error_count": len(failed),
    })
    with (output_dir / "r2_deletion_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["metric", "value"])
        writer.writerows(summary.items())
    with (output_dir / "run_summary.md").open("w", encoding="utf-8") as handle:
        handle.write("# Google Drive 이전 완료 R2 원본 HTML 삭제 결과\n\n")
        handle.write("## 실행 결과\n\n")
        for key, value in summary.items():
            handle.write(f"- {key}: {str(value).lower() if isinstance(value, bool) else value}\n")
        handle.write("\n## 보존 확인\n\n")
        handle.write("- R2 버킷 삭제 여부: 아니요\n")
        handle.write("- manifest 외 객체 삭제 대상 포함 여부: 아니요\n")
        handle.write("- Google Drive 파일 수정 여부: 아니요\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify-absence", action="store_true")
    parser.add_argument("--expected-count", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    keys, validation = load_and_validate_manifest(args.manifest, args.expected_count)
    for key, value in validation.items():
        print(f"{key}={str(value).lower() if isinstance(value, bool) else value}")
    if args.dry_run:
        write_outputs(args.output_dir, validation, [], 0, "dry_run")
        print("delete_api_called=false")
        return 0

    client = make_r2_client()
    if args.verify_absence:
        remaining, bucket_object_count, bucket_total_bytes = inspect_bucket_manifest_keys(
            client, os.environ["R2_BUCKET_NAME"], keys
        )
        validation.update({
            "remaining_manifest_objects": len(remaining),
            "bucket_object_count": bucket_object_count,
            "bucket_total_bytes": bucket_total_bytes,
            "manifest_external_object_count": bucket_object_count - len(remaining),
        })
        results = [{
            "object_key": key,
            "delete_attempted": 0,
            "delete_api_error": 1,
            "error_code": "ObjectStillPresent",
            "error_message": "manifest object remains in R2 after deletion run",
            "deleted_at_utc": "",
        } for key in remaining]
        write_outputs(args.output_dir, validation, results, 0, "verify_absence")
        print(f"remaining_manifest_objects={len(remaining)}")
        print(f"bucket_object_count={bucket_object_count}")
        print(f"bucket_total_bytes={bucket_total_bytes}")
        print(f"manifest_external_object_count={bucket_object_count - len(remaining)}")
        return 1 if remaining else 0

    results, batch_count = delete_manifest_keys(client, os.environ["R2_BUCKET_NAME"], keys)
    write_outputs(args.output_dir, validation, results, batch_count, "execute")
    error_count = sum(int(row["delete_api_error"]) for row in results)
    print(f"delete_attempted={len(results)}")
    print(f"delete_batches={batch_count}")
    print(f"delete_api_errors={error_count}")
    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
