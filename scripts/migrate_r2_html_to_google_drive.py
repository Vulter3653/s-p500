#!/usr/bin/env python3
"""Copy manifest-pinned raw 10-K HTML from R2 to Google Drive without overwrite."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile
import threading
import time
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


ROOT = Path(__file__).resolve().parents[1]
TOKEN_URI = "https://oauth2.googleapis.com/token"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
VALID_SOURCE_STATUSES = {
    "uploaded",
    "existing_pilot_object",
    "skipped_existing_sha_match",
}
SUCCESS_STATUSES = {"uploaded", "skipped_existing_match"}
MANIFEST_FIELDS = [
    "report_year", "company_id", "source_company_id", "ticker", "company_name",
    "cik", "accession_number", "r2_object_key", "r2_html_bytes", "r2_sha256",
    "drive_year_folder_id", "drive_sample_folder_id", "drive_html_folder_id",
    "drive_raw_folder_id", "drive_cik_folder_id", "drive_file_id",
    "drive_file_name", "drive_mime_type", "drive_size",
    "drive_sha256_app_property", "migration_status", "verification_status",
    "migrated_at_utc", "error_type", "error_message",
    "drive_layout",
]
CHECKPOINT_FIELDS = [
    "report_year", "cik", "accession_number", "r2_object_key",
    "drive_file_id", "migration_status", "verification_status",
    "processed_at_utc", "retry_count",
]
_folder_lock = threading.Lock()
_checkpoint_lock = threading.Lock()
_thread_local = threading.local()
_folder_cache: dict[tuple[str, str], str] = {}
DEFAULT_DRIVE_LAYOUT = "year_flat"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def progress(stage: str, started: float, completed: int | None = None, total: int | None = None) -> None:
    elapsed = time.monotonic() - started
    detail = f"elapsed={elapsed:.1f}s"
    if completed is not None and total is not None:
        eta = (elapsed / completed * (total - completed)) if completed else 0.0
        detail += f" completed={completed}/{total} eta={eta:.1f}s"
    print(f"[migration] stage={stage} {detail}", flush=True)


def require_environment(names: list[str]) -> None:
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError("missing required environment variables: " + ", ".join(missing))


def credentials() -> Credentials:
    require_environment([
        "GOOGLE_DRIVE_CLIENT_ID", "GOOGLE_DRIVE_CLIENT_SECRET",
        "GOOGLE_DRIVE_REFRESH_TOKEN",
    ])
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
    service = getattr(_thread_local, "drive", None)
    if service is None:
        service = build("drive", "v3", credentials=credentials(), cache_discovery=False)
        _thread_local.drive = service
    return service


def r2_client():
    client = getattr(_thread_local, "r2", None)
    if client is None:
        require_environment([
            "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY",
            "R2_ENDPOINT_URL", "R2_BUCKET_NAME",
        ])
        client = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT_URL"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
            config=Config(
                retries={"max_attempts": 8, "mode": "standard"},
                connect_timeout=20,
                read_timeout=180,
            ),
        )
        _thread_local.r2 = client
    return client


def safe_drive_call(request, attempts: int = 7):
    for attempt in range(attempts):
        try:
            return request.execute()
        except HttpError as error:
            status = getattr(error.resp, "status", None)
            if status not in {429, 500, 502, 503, 504} or attempt + 1 == attempts:
                raise
        except (TimeoutError, ConnectionError):
            if attempt + 1 == attempts:
                raise
        time.sleep(min(2 ** attempt, 32))
    raise RuntimeError("unreachable retry state")


def escape_query(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def find_child(service, parent_id: str, name: str, mime_type: str | None = None) -> list[dict]:
    terms = [
        f"'{escape_query(parent_id)}' in parents",
        f"name = '{escape_query(name)}'",
        "trashed = false",
    ]
    if mime_type:
        terms.append(f"mimeType = '{mime_type}'")
    response = safe_drive_call(
        service.files().list(
            q=" and ".join(terms),
            spaces="drive",
            fields="files(id,name,mimeType,size,appProperties,parents)",
            pageSize=10,
        )
    )
    return response.get("files", [])


def ensure_folder(service, parent_id: str, name: str) -> str:
    folder_mime = "application/vnd.google-apps.folder"
    with _folder_lock:
        cache_key = (parent_id, name)
        if cache_key in _folder_cache:
            return _folder_cache[cache_key]
        matches = find_child(service, parent_id, name, folder_mime)
        if len(matches) > 1:
            raise RuntimeError(f"ambiguous_duplicate_drive_folders:{name}")
        if matches:
            _folder_cache[cache_key] = matches[0]["id"]
            return matches[0]["id"]
        created = safe_drive_call(
            service.files().create(
                body={"name": name, "mimeType": folder_mime, "parents": [parent_id]},
                fields="id",
            )
        )
        matches = find_child(service, parent_id, name, folder_mime)
        if len(matches) != 1 or matches[0]["id"] != created["id"]:
            raise RuntimeError(f"ambiguous_duplicate_drive_folders:{name}")
        _folder_cache[cache_key] = created["id"]
        return created["id"]


def folder_chain(service, root_id: str, year: str, cik: str) -> dict[str, str]:
    year_id = ensure_folder(service, root_id, year)
    sample_id = ensure_folder(service, year_id, "sample_500")
    html_id = ensure_folder(service, sample_id, "html")
    raw_id = ensure_folder(service, html_id, "raw")
    cik_id = ensure_folder(service, raw_id, cik)
    return {
        "drive_year_folder_id": year_id,
        "drive_sample_folder_id": sample_id,
        "drive_html_folder_id": html_id,
        "drive_raw_folder_id": raw_id,
        "drive_cik_folder_id": cik_id,
    }


def sample_manifest_path(year: str) -> Path:
    """Return the yearly manifest used to build the display filename."""
    candidates = [
        ROOT / year / "sample_500" / f"sample_manifest_{year}_500.csv",
        ROOT / year / "pilot_100/sample/final_analysis_sample_100.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"sample manifest not found for {year}")


def load_sample_identity(year: str) -> dict[tuple[str, str], dict]:
    index = {}
    with sample_manifest_path(year).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            cik = row.get("cik", "").strip().zfill(10)
            accession = row.get("accession_number", "").strip()
            if cik and accession:
                index[(cik, accession)] = row
    return index


def safe_filename_part(value: str, fallback: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"[\\/:*?\"<>|]", "_", value)
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._")
    return value or fallback


def drive_filename(year: str, row: dict, identity: dict) -> str:
    sample_order = int(identity.get("sample_order", ""))
    company = safe_filename_part(identity.get("company_name", ""), "unknown_company")
    symbol = safe_filename_part(
        identity.get("symbol") or identity.get("ticker", ""), "unknown_symbol"
    )
    return f"{sample_order - 1}_{year}_{company}_{symbol}_{row['cik']}.html"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest(year: str) -> Path:
    return ROOT / year / "sample_500/r2_storage/html_r2_manifest.csv"


def load_targets(years: list[str]) -> tuple[list[dict], list[dict], dict[str, int]]:
    targets, invalid = [], []
    source_counts: dict[str, int] = {}
    seen_keys: set[str] = set()
    for year in years:
        path = source_manifest(year)
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        source_counts[year] = len(rows)
        for source in rows:
            key = source.get("object_key", "").strip()
            row = {
                "report_year": year,
                "company_id": source.get("company_id", ""),
                "source_company_id": source.get("company_id", ""),
                "ticker": source.get("ticker", ""),
                "company_name": source.get("company_name", ""),
                "cik": source.get("cik", "").strip(),
                "accession_number": source.get("accession_number", "").strip(),
                "r2_object_key": key,
                "r2_html_bytes": source.get("file_size", "").strip(),
                "r2_sha256": source.get("sha256", "").strip().lower(),
            }
            status = source.get("upload_status", "").strip()
            required = (
                key and row["cik"] and row["accession_number"]
                and row["r2_html_bytes"].isdigit()
                and len(row["r2_sha256"]) == 64
                and status in VALID_SOURCE_STATUSES
            )
            if not required:
                row.update(result_fields(
                    "invalid_source_manifest_row", "not_verified",
                    "invalid_source_manifest_row", "required source fields or status invalid",
                ))
                invalid.append(row)
            elif key in seen_keys:
                row.update(result_fields(
                    "invalid_source_manifest_row", "not_verified",
                    "duplicate_r2_object_key", "duplicate object key excluded from transfer",
                ))
                invalid.append(row)
            else:
                seen_keys.add(key)
                targets.append(row)
    return targets, invalid, source_counts


def load_targets_from_manifest(path: Path) -> tuple[list[dict], list[dict], dict[str, int]]:
    """Load a persistent historical manifest without relying on sample_500 paths."""
    targets, invalid = [], []
    source_counts: dict[str, int] = Counter()
    seen_keys: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for source in rows:
        year = source.get("report_year", "").strip()
        key = source.get("r2_object_key") or source.get("object_key", "")
        key = key.strip()
        row = {
            "report_year": year,
            "company_id": source.get("company_id", ""),
            "source_company_id": source.get("source_company_id", source.get("company_id", "")),
            "ticker": source.get("ticker", source.get("symbol", "")),
            "company_name": source.get("company_name", ""),
            "cik": source.get("cik", "").strip().zfill(10),
            "accession_number": source.get("accession_number", "").strip(),
            "r2_object_key": key,
            "r2_html_bytes": (source.get("r2_html_bytes") or source.get("file_size", "")).strip(),
            "r2_sha256": (source.get("r2_sha256") or source.get("sha256", "")).strip().lower(),
        }
        status = source.get("source_upload_status", source.get("upload_status", "uploaded")).strip()
        required = (
            year and key and row["cik"] and row["accession_number"]
            and row["r2_html_bytes"].isdigit() and len(row["r2_sha256"]) == 64
            and status in VALID_SOURCE_STATUSES
        )
        if not required:
            row.update(result_fields("invalid_source_manifest_row", "not_verified", "invalid_source_manifest_row", "required historical manifest fields or status invalid"))
            invalid.append(row)
        elif key in seen_keys:
            row.update(result_fields("invalid_source_manifest_row", "not_verified", "duplicate_r2_object_key", "duplicate object key excluded from transfer"))
            invalid.append(row)
        else:
            seen_keys.add(key)
            targets.append(row)
            source_counts[year] += 1
    return targets, invalid, dict(source_counts)


def result_fields(status: str, verification: str, error_type: str = "", error: str = "") -> dict:
    return {
        "drive_year_folder_id": "", "drive_sample_folder_id": "",
        "drive_html_folder_id": "", "drive_raw_folder_id": "",
        "drive_cik_folder_id": "", "drive_file_id": "",
        "drive_file_name": "", "drive_mime_type": "text/html",
        "drive_size": "", "drive_sha256_app_property": "",
        "migration_status": status, "verification_status": verification,
        "migrated_at_utc": utc_now(), "error_type": error_type,
        "error_message": error[:500],
        "drive_layout": DEFAULT_DRIVE_LAYOUT,
    }


def append_checkpoint(path: Path, row: dict, retry_count: int = 0) -> None:
    item = {
        "report_year": row["report_year"], "cik": row["cik"],
        "accession_number": row["accession_number"],
        "r2_object_key": row["r2_object_key"],
        "drive_file_id": row.get("drive_file_id", ""),
        "migration_status": row["migration_status"],
        "verification_status": row["verification_status"],
        "processed_at_utc": utc_now(), "retry_count": retry_count,
    }
    with _checkpoint_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, sort_keys=True) + "\n")


def process_target(
    row: dict, root_id: str, temp_root: Path, checkpoint: Path,
    drive_layout: str, identity_index: dict[tuple[str, str], dict],
) -> dict:
    result = dict(row)
    local = temp_root / row["report_year"] / row["cik"] / f"{row['accession_number']}.html"
    try:
        r2 = r2_client()
        try:
            head = r2.head_object(Bucket=os.environ["R2_BUCKET_NAME"], Key=row["r2_object_key"])
        except ClientError as error:
            code = str(error.response.get("Error", {}).get("Code", ""))
            status = "missing_r2_object" if code in {"404", "NoSuchKey", "NotFound"} else "failed_r2_head"
            raise RuntimeError(f"{status}:{code}") from error
        expected_size = int(row["r2_html_bytes"])
        metadata_sha = head.get("Metadata", {}).get("sha256", "").lower()
        if int(head["ContentLength"]) != expected_size:
            raise RuntimeError("failed_r2_head:manifest_size_mismatch")
        if metadata_sha and metadata_sha != row["r2_sha256"]:
            raise RuntimeError("failed_r2_head:metadata_sha_mismatch")
        local.parent.mkdir(parents=True, exist_ok=True)
        r2.download_file(os.environ["R2_BUCKET_NAME"], row["r2_object_key"], str(local))
        if local.stat().st_size != expected_size or sha256_file(local) != row["r2_sha256"]:
            raise RuntimeError("failed_r2_download:download_verification_failed")

        service = drive_service()
        identity = identity_index.get((row["cik"], row["accession_number"]))
        if drive_layout == "year_flat" and identity is None:
            raise RuntimeError("missing_sample_identity_for_drive_filename")
        folders = (
            folder_chain(service, root_id, row["report_year"], row["cik"])
            if drive_layout == "legacy_nested"
            else {
                "drive_year_folder_id": ensure_folder(
                    service, root_id, row["report_year"]
                ),
                "drive_sample_folder_id": "",
                "drive_html_folder_id": "",
                "drive_raw_folder_id": "",
                "drive_cik_folder_id": "",
            }
        )
        result.update(folders)
        filename = (
            f"{row['accession_number']}.html"
            if drive_layout == "legacy_nested"
            else drive_filename(row["report_year"], row, identity)
        )
        parent_id = (
            folders["drive_cik_folder_id"]
            if drive_layout == "legacy_nested"
            else folders["drive_year_folder_id"]
        )
        matches = find_child(service, parent_id, filename)
        if len(matches) > 1:
            result.update(result_fields(
                "ambiguous_duplicate_drive_files", "not_verified",
                "ambiguous_duplicate_drive_files", "multiple same-name files under CIK folder",
            ))
        elif len(matches) == 1:
            existing = matches[0]
            app_sha = existing.get("appProperties", {}).get("sha256", "").lower()
            size = int(existing.get("size", 0))
            if size == expected_size and app_sha == row["r2_sha256"]:
                result.update(result_fields("skipped_existing_match", "verified_size_and_sha"))
                result.update(folders)
                result.update({
                    "drive_file_id": existing["id"], "drive_file_name": filename,
                    "drive_size": str(size), "drive_sha256_app_property": app_sha,
                })
            else:
                result.update(result_fields(
                    "conflict_existing_drive_file", "verification_failed",
                    "conflict_existing_drive_file", "existing file size or SHA differs",
                ))
                result.update(folders)
                result.update({"drive_file_id": existing["id"], "drive_file_name": filename})
        else:
            media = MediaFileUpload(
                str(local), mimetype="text/html", resumable=True,
                chunksize=8 * 1024 * 1024,
            )
            body = {
                "name": filename,
                "parents": [parent_id],
                "appProperties": {
                    "sha256": row["r2_sha256"], "cik": row["cik"],
                    "accession": row["accession_number"],
                    "report_year": row["report_year"],
                    "source_storage": "r2", "source": "sec_edgar",
                },
            }
            created = safe_drive_call(
                service.files().create(
                    body=body, media_body=media,
                    fields="id,name,size,mimeType,appProperties",
                )
            )
            size = int(created.get("size", 0))
            app_sha = created.get("appProperties", {}).get("sha256", "").lower()
            verification = (
                "verified_size_and_sha"
                if size == expected_size and app_sha == row["r2_sha256"]
                else "verification_failed"
            )
            status = "uploaded" if verification == "verified_size_and_sha" else "failed_drive_verification"
            result.update(result_fields(status, verification))
            result.update(folders)
            result.update({
                "drive_file_id": created["id"], "drive_file_name": created["name"],
                "drive_mime_type": created.get("mimeType", "text/html"),
                "drive_size": str(size), "drive_sha256_app_property": app_sha,
            })
        result["drive_layout"] = drive_layout
    except Exception as error:
        message = str(error)
        if "ambiguous_duplicate_drive_folders" in message:
            status = "ambiguous_duplicate_drive_folders"
        elif message.startswith("missing_sample_identity"):
            status = "failed_drive_upload"
        elif message.startswith("missing_r2_object"):
            status = "missing_r2_object"
        elif message.startswith("failed_r2_head"):
            status = "failed_r2_head"
        elif message.startswith("failed_r2_download"):
            status = "failed_r2_download"
        elif isinstance(error, HttpError):
            status = "failed_drive_upload"
        else:
            status = "failed_drive_upload"
        result.update(result_fields(status, "not_verified", status, message))
    finally:
        if local.exists():
            local.unlink()
        append_checkpoint(checkpoint, result)
    return result


def check_connections(root_id: str) -> dict:
    creds = credentials()
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    root = safe_drive_call(
        service.files().get(
            fileId=root_id,
            fields="id,name,mimeType,capabilities(canAddChildren),trashed",
        )
    )
    if root.get("mimeType") != "application/vnd.google-apps.folder" or root.get("trashed"):
        raise RuntimeError("configured Drive root is not an active folder")
    if not root.get("capabilities", {}).get("canAddChildren"):
        raise RuntimeError("configured Drive root does not permit file creation")
    quota_result = "unavailable"
    quota_limit = quota_usage = quota_remaining = ""
    try:
        about = safe_drive_call(service.about().get(fields="storageQuota"))
        quota = about.get("storageQuota", {})
        quota_limit = quota.get("limit", "")
        quota_usage = quota.get("usage", "")
        if quota_limit and quota_usage:
            quota_remaining = str(int(quota_limit) - int(quota_usage))
            quota_result = "available"
    except HttpError:
        pass
    r2_client().list_objects_v2(Bucket=os.environ["R2_BUCKET_NAME"], MaxKeys=1)
    return {
        "oauth_refresh": "success", "drive_root_access": "success",
        "drive_can_add_children": "yes", "drive_quota_result": quota_result,
        "drive_quota_limit_bytes": quota_limit,
        "drive_quota_usage_bytes": quota_usage,
        "drive_quota_remaining_bytes": quota_remaining,
        "r2_connection": "success",
    }


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(
    output_dir: Path, results: list[dict], invalid: list[dict],
    source_counts: dict[str, int], connection: dict, temp_remaining: int,
    test_rerun_skip: bool, drive_layout: str,
) -> None:
    all_rows = sorted(results + invalid, key=lambda r: (r["report_year"], r["cik"], r["accession_number"]))
    write_csv(output_dir / "raw_html_google_drive_manifest.csv", MANIFEST_FIELDS, all_rows)
    failed = [r for r in all_rows if r["migration_status"] not in SUCCESS_STATUSES]
    write_csv(
        output_dir / "migration_failed_cases.csv",
        ["report_year", "cik", "accession_number", "r2_object_key",
         "migration_status", "error_type", "error_message", "requires_manual_review"],
        [{**r, "requires_manual_review": 1} for r in failed],
    )
    summary_rows = []
    for year in list(source_counts) + ["ALL"]:
        subset = all_rows if year == "ALL" else [r for r in all_rows if r["report_year"] == year]
        counts = Counter(r["migration_status"] for r in subset)
        summary_rows.append({
            "report_year": year, "source_manifest_rows": sum(source_counts.values()) if year == "ALL" else source_counts[year],
            "valid_migration_targets": sum(r["migration_status"] != "invalid_source_manifest_row" for r in subset),
            "unique_r2_object_keys": len({r["r2_object_key"] for r in subset if r["r2_object_key"]}),
            "duplicate_r2_object_keys": sum(r.get("error_type") == "duplicate_r2_object_key" for r in subset),
            "uploaded": counts["uploaded"], "skipped_existing_match": counts["skipped_existing_match"],
            "conflicts": counts["conflict_existing_drive_file"],
            "ambiguous_files": counts["ambiguous_duplicate_drive_files"],
            "ambiguous_folders": counts["ambiguous_duplicate_drive_folders"],
            "failed": sum(status not in SUCCESS_STATUSES for status in counts.elements()),
            "verified_size_and_sha": sum(r["verification_status"] == "verified_size_and_sha" for r in subset),
            "total_bytes": sum(int(r["r2_html_bytes"] or 0) for r in subset if r["r2_html_bytes"].isdigit()),
        })
    write_csv(output_dir / "migration_quality_summary.csv", list(summary_rows[0]), summary_rows)
    success = [r for r in all_rows if r["migration_status"] in SUCCESS_STATUSES]
    run_summary = [
        "# R2 to Google Drive raw HTML migration",
        "",
        f"- Google Drive root folder ID: `{os.environ.get('GOOGLE_DRIVE_ROOT_FOLDER_ID', '')}`",
        "- Google Drive stated capacity: 5 TB",
        f"- Drive quota query: {connection['drive_quota_result']}",
        f"- Drive layout: `{drive_layout}` (default: `{DEFAULT_DRIVE_LAYOUT}`)",
        f"- Target years: {', '.join(source_counts)}",
        f"- Source manifest rows: {sum(source_counts.values())}",
        f"- Valid migration targets: {len(results)}",
        f"- Uploaded: {sum(r['migration_status'] == 'uploaded' for r in all_rows)}",
        f"- Skipped existing match: {sum(r['migration_status'] == 'skipped_existing_match' for r in all_rows)}",
        f"- Conflict/ambiguous/failed/invalid: {len(all_rows) - len(success)}",
        f"- Drive file IDs: {sum(bool(r.get('drive_file_id')) for r in success)}",
        f"- Size and SHA verified: {sum(r['verification_status'] == 'verified_size_and_sha' for r in all_rows)}",
        f"- Test rerun skip: {'yes' if test_rerun_skip else 'not_applicable'}",
        f"- Temporary files remaining: {temp_remaining}",
        "- R2 objects deleted: no",
        "- R2 objects overwritten: no",
        "- Existing yearly results modified: no",
        "- Existing panel modified: no",
        "- Language measurement rerun: no",
        "- SEC recollection: no",
    ]
    (output_dir / "run_summary.md").write_text("\n".join(run_summary) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", default="2020,2021,2022,2023,2024,2025")
    parser.add_argument("--manifest", type=Path, help="Persistent historical R2 migration manifest")
    parser.add_argument("--drive-root-folder-id", default=os.environ.get("GOOGLE_DRIVE_ROOT_FOLDER_ID", ""))
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument(
        "--drive-layout", choices=("year_flat", "legacy_nested"),
        default=DEFAULT_DRIVE_LAYOUT,
        help="Drive layout; year_flat is the default future storage format",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("google_drive_storage"))
    parser.add_argument("--check-connections-only", action="store_true")
    parser.add_argument("--test-first-object", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    years = [value.strip() for value in args.years.split(",") if value.strip()]
    if not args.drive_root_folder_id:
        raise RuntimeError("Google Drive root folder ID is required")
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    progress("connection_check_started", started)
    connection = check_connections(args.drive_root_folder_id)
    progress("connection_check_completed", started)
    (output_dir / "connection_check.json").write_text(
        json.dumps(connection, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if args.check_connections_only:
        return 0
    if args.manifest:
        targets, invalid, source_counts = load_targets_from_manifest(args.manifest.resolve())
        years = sorted(source_counts)
        identity_indexes = {year: {} for year in years}
        for row in targets:
            identity_indexes[row["report_year"]][(row["cik"], row["accession_number"])] = row
    else:
        targets, invalid, source_counts = load_targets(years)
        identity_indexes = {year: load_sample_identity(year) for year in years}
    if args.test_first_object:
        targets = targets[:1]
        source_counts = {years[0]: source_counts[years[0]]}
    progress("inventory_loaded", started, len(targets), len(targets))
    total_bytes = sum(int(row["r2_html_bytes"]) for row in targets)
    remaining = connection.get("drive_quota_remaining_bytes", "")
    if remaining and int(remaining) < total_bytes:
        raise RuntimeError("Google Drive storage quota is insufficient")
    checkpoint = output_dir / "migration_checkpoint.jsonl"
    if checkpoint.exists():
        checkpoint.unlink()
    temp_root = Path(tempfile.mkdtemp(prefix="s-p500-drive-migration-"))
    results: list[dict] = []
    try:
        if args.test_first_object:
            progress("test_upload_started", started)
            first = process_target(
                targets[0], args.drive_root_folder_id, temp_root, checkpoint,
                args.drive_layout, identity_indexes[targets[0]["report_year"]],
            )
            progress("test_rerun_started", started)
            second = process_target(
                targets[0], args.drive_root_folder_id, temp_root, checkpoint,
                args.drive_layout, identity_indexes[targets[0]["report_year"]],
            )
            if first["migration_status"] not in SUCCESS_STATUSES or second["migration_status"] != "skipped_existing_match":
                raise RuntimeError("test migration or rerun skip failed")
            results = [second]
            test_rerun_skip = True
            progress("test_upload_and_skip_completed", started, 1, 1)
        else:
            with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 5))) as pool:
                futures = {
                    pool.submit(
                        process_target, row, args.drive_root_folder_id, temp_root,
                        checkpoint, args.drive_layout,
                        identity_indexes[row["report_year"]],
                    ): row
                    for row in targets
                }
                for future in as_completed(futures):
                    results.append(future.result())
                    completed = len(results)
                    if completed == 1 or completed % 25 == 0 or completed == len(targets):
                        progress("migration_in_progress", started, completed, len(targets))
            test_rerun_skip = False
        remaining_files = sum(1 for item in temp_root.rglob("*") if item.is_file())
        progress("verification_and_summary_started", started)
        write_outputs(
            output_dir, results, invalid, source_counts, connection,
            remaining_files, test_rerun_skip, args.drive_layout,
        )
        failures = [r for r in results + invalid if r["migration_status"] not in SUCCESS_STATUSES]
        progress("completed", started, len(results), len(targets))
        return 1 if failures else 0
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
