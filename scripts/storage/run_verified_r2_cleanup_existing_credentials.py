#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import build_r2_verified_drive_cleanup as cleanup


ROOT = Path(__file__).resolve().parents[2]

ADMIN = (
    ROOT
    / "storage_admin"
    / "verified_r2_cleanup"
)

TOKEN_URI = "https://oauth2.googleapis.com/token"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"

_thread_local = threading.local()


def require_environment(names):
    missing = []

    for name in names:
        value = os.environ.get(name)

        if value:
            print(f"{name}=set")
        else:
            print(f"{name}=missing")
            missing.append(name)

    if missing:
        raise RuntimeError(
            "missing required environment variables: "
            + ", ".join(missing)
        )


def make_credentials():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_DRIVE_REFRESH_TOKEN"],
        token_uri=TOKEN_URI,
        client_id=os.environ["GOOGLE_DRIVE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_DRIVE_CLIENT_SECRET"],
        scopes=[DRIVE_SCOPE],
    )

    creds.refresh(Request())

    return creds


def drive_service():
    service = getattr(_thread_local, "drive_service", None)

    if service is None:
        service = build(
            "drive",
            "v3",
            credentials=make_credentials(),
            cache_discovery=False,
        )

        _thread_local.drive_service = service

    return service


def verify_drive_file(file_id):
    try:
        response = (
            drive_service()
            .files()
            .get(
                fileId=file_id,
                fields="id,name,size,trashed",
                supportsAllDrives=True,
            )
            .execute()
        )

        if response.get("trashed", False):
            return file_id, None, "TRASHED"

        size = response.get("size")

        if size is None:
            return file_id, None, "SIZE_MISSING"

        return (
            file_id,
            {
                "drive_size_live": int(size),
                "drive_path_live": response.get("name", ""),
            },
            "VERIFIED",
        )

    except HttpError as error:
        status = getattr(error.resp, "status", "unknown")

        return file_id, None, f"HTTP_{status}"

    except Exception as error:
        return (
            file_id,
            None,
            f"{type(error).__name__}",
        )


def main():
    require_environment(
        [
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
            "R2_ENDPOINT_URL",
            "R2_BUCKET_NAME",
            "GOOGLE_DRIVE_CLIENT_ID",
            "GOOGLE_DRIVE_CLIENT_SECRET",
            "GOOGLE_DRIVE_REFRESH_TOKEN",
        ]
    )

    migration_path = (
        ADMIN
        / "raw_html_google_drive_manifest.csv"
    )

    protected_path = (
        ADMIN
        / "protected_current_research_r2_keys.csv"
    )

    migration = pd.read_csv(migration_path)

    protected_df = pd.read_csv(protected_path)

    protected = set(
        protected_df["r2_object_key"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    if len(protected) != 5355:
        raise RuntimeError(
            f"protected key count mismatch: {len(protected)} != 5355"
        )

    # --------------------------------------------------------
    # Drive file IDs to verify
    # --------------------------------------------------------

    required_columns = {
        "r2_object_key",
        "r2_html_bytes",
        "r2_sha256",
        "drive_file_id",
        "drive_size",
        "drive_sha256_app_property",
        "migration_status",
        "verification_status",
    }

    missing_columns = required_columns - set(migration.columns)

    if missing_columns:
        raise RuntimeError(
            "migration manifest missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    drive_ids = sorted(
        {
            str(value).strip()
            for value in migration["drive_file_id"].dropna()
            if str(value).strip()
        }
    )

    print(f"drive_file_ids_to_verify={len(drive_ids)}")

    drive_live = {}
    drive_failures = {}

    # bounded parallel verification
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(
                verify_drive_file,
                file_id
            ): file_id
            for file_id in drive_ids
        }

        for future in as_completed(futures):
            file_id = futures[future]

            try:
                returned_id, evidence, status = future.result()
            except Exception as error:
                drive_failures[file_id] = type(error).__name__
                continue

            if evidence is not None:
                drive_live[returned_id] = evidence
            else:
                drive_failures[returned_id] = status

    print(
        f"drive_live_verified={len(drive_live)}"
    )

    print(
        f"drive_live_failed={len(drive_failures)}"
    )

    # --------------------------------------------------------
    # Current R2 inventory
    # --------------------------------------------------------

    client = cleanup.s3_client()

    inventory = cleanup.inventory_r2(
        client,
        os.environ["R2_BUCKET_NAME"],
    )

    print(f"current_r2_objects={len(inventory)}")

    print(
        "current_r2_bytes="
        + str(
            sum(
                int(row["r2_size"])
                for row in inventory
            )
        )
    )

    # --------------------------------------------------------
    # Build fail-closed deletion plan
    # --------------------------------------------------------

    plan = cleanup.build_plan(
        inventory,
        migration,
        protected,
        drive_live,
    )

    candidates = [
        row
        for row in plan
        if row["delete_eligible"]
    ]

    shards = cleanup.balance_shards(
        candidates,
        8,
    )

    output = (
        ADMIN
        / "dry_run"
    )

    output.mkdir(
        parents=True,
        exist_ok=True,
    )

    cleanup.write_jsonl(
        output
        / "r2_cleanup_plan.jsonl",
        plan,
    )

    cleanup.write_jsonl(
        output
        / "r2_inventory_before.jsonl",
        inventory,
    )

    shard_dir = output / "shards"

    shard_dir.mkdir(
        exist_ok=True
    )

    for index, shard in enumerate(shards):
        cleanup.write_jsonl(
            shard_dir
            / f"shard_{index:03d}.jsonl",
            shard,
        )

    summary = cleanup.summarize(
        plan,
        shards,
    )

    plan_sha = cleanup.sha256_file(
        output
        / "r2_cleanup_plan.jsonl"
    )

    summary.update(
        {
            "execute_delete": False,
            "objects_deleted": 0,
            "bytes_deleted": 0,
            "delete_api_calls": 0,

            "protected_current_research_keys":
                len(protected),

            "drive_file_ids_requested":
                len(drive_ids),

            "drive_live_verified":
                len(drive_live),

            "drive_live_failed":
                len(drive_failures),

            "plan_sha256":
                plan_sha,
        }
    )

    (
        output
        / "r2_cleanup_summary.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    (
        output
        / "drive_verification_failures.json"
    ).write_text(
        json.dumps(
            drive_failures,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Absolute dry-run safety assertions
    # --------------------------------------------------------

    assert summary["execute_delete"] is False

    assert summary["objects_deleted"] == 0

    assert summary["bytes_deleted"] == 0

    assert summary["delete_api_calls"] == 0

    assert len(protected) == 5355

    print("DRY_RUN_ONLY=PASS")

    print(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
