#!/usr/bin/env python3
"""Build a manifest from the live R2 HTML inventory for Drive migration."""

from __future__ import annotations

import argparse
import csv
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import boto3
from botocore.config import Config

KEY_RE = re.compile(r"^(?P<year>\d{4})/[^/]+/html/raw/(?P<cik>\d{10})/(?P<accession>[^/]+)\.html$")


def client():
    required = ["R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT_URL", "R2_BUCKET_NAME"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError("missing required environment variables: " + ", ".join(missing))
    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(
            retries={"max_attempts": 5, "mode": "standard"},
            connect_timeout=10,
            read_timeout=30,
        ),
    )


def inspect_key(key: str) -> dict[str, str]:
    match = KEY_RE.match(key)
    if not match:
        raise RuntimeError(f"unexpected R2 object key: {key}")
    return {
        "report_year": match.group("year"),
        "company_id": "",
        "source_company_id": "",
        "ticker": "",
        "company_name": "",
        "cik": match.group("cik"),
        "accession_number": match.group("accession"),
        "r2_object_key": key,
    }


def build(years: list[str], output: Path, workers: int) -> int:
    listing_client = client()
    bucket = os.environ["R2_BUCKET_NAME"]
    keys: list[str] = []
    seen: set[str] = set()
    for year in years:
        prefix = f"{year}/sample_503/html/raw/"
        paginator = listing_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for item in page.get("Contents", []):
                key = item.get("Key", "")
                if key in seen:
                    raise RuntimeError(f"duplicate R2 object key: {key}")
                seen.add(key)
                keys.append(key)

    def head_one(key: str) -> dict[str, str]:
        metadata = client().head_object(Bucket=bucket, Key=key)
        sha = metadata.get("Metadata", {}).get("sha256", "").lower()
        if len(sha) != 64:
            raise RuntimeError(f"missing sha256 metadata: {key}")
        row = inspect_key(key)
        row.update({
            "r2_html_bytes": str(metadata["ContentLength"]),
            "r2_sha256": sha,
            "source_upload_status": "uploaded",
        })
        return row

    rows: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 16))) as pool:
        futures = {pool.submit(head_one, key): key for key in keys}
        for future in as_completed(futures):
            rows.append(future.result())
            if len(rows) % 250 == 0 or len(rows) == len(keys):
                print(f"r2_inventory_heads={len(rows)}/{len(keys)}", flush=True)

    rows.sort(key=lambda row: (row["report_year"], row["cik"], row["accession_number"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "report_year", "company_id", "source_company_id", "ticker", "company_name",
        "cik", "accession_number", "r2_object_key", "r2_html_bytes", "r2_sha256",
        "source_upload_status",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"r2_inventory_rows={len(rows)}")
    print(f"r2_inventory_years={','.join(years)}")
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    years = [value.strip() for value in args.years.split(",") if value.strip()]
    if not years:
        raise ValueError("years must not be empty")
    return 0 if build(years, args.output, args.workers) >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
