#!/usr/bin/env python3
"""Rename flattened Google Drive raw HTML files from year manifests."""

from __future__ import annotations

import argparse
import csv
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from migrate_r2_html_to_google_drive import drive_service, find_child, safe_drive_call

FOLDER_MIME = "application/vnd.google-apps.folder"
ROOT = Path(__file__).resolve().parents[1]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_children(service, parent_id: str) -> list[dict]:
    files: list[dict] = []
    token = None
    while True:
        response = safe_drive_call(
            service.files().list(
                q=f"'{parent_id}' in parents and trashed = false",
                spaces="drive",
                fields="nextPageToken,files(id,name,mimeType,parents)",
                pageSize=1000,
                pageToken=token,
            )
        )
        files.extend(response.get("files", []))
        token = response.get("nextPageToken")
        if not token:
            return files


def one_folder(service, parent_id: str, name: str) -> dict:
    matches = find_child(service, parent_id, name, FOLDER_MIME)
    if len(matches) != 1:
        raise RuntimeError(f"expected_one_folder:{name}:found={len(matches)}")
    return matches[0]


def safe_part(value: str) -> str:
    value = value.strip()
    value = re.sub(r"[\\/:*?\"<>|]", "_", value)
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._")
    return value or "unknown"


def manifest_index(year: str) -> dict[tuple[str, str], dict]:
    path = ROOT / year / "sample_500" / f"sample_manifest_{year}_500.csv"
    result: dict[tuple[str, str], dict] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            cik = row.get("cik", "").strip()
            accession = row.get("accession_number", "").strip()
            if not cik or not accession:
                continue
            key = (cik.zfill(10), accession)
            if key in result:
                raise RuntimeError(f"duplicate_manifest_key:{year}:{key}")
            result[key] = row
    return result


def rename_year(service, root_id: str, year: str, execute: bool) -> list[dict]:
    year_folder = one_folder(service, root_id, year)
    manifest = manifest_index(year)
    leaves = [item for item in list_children(service, year_folder["id"]) if item.get("mimeType") == FOLDER_MIME]
    results: list[dict] = []
    for leaf in sorted(leaves, key=lambda item: item["name"]):
        cik = leaf["name"].zfill(10)
        files = [item for item in list_children(service, leaf["id"]) if item.get("mimeType") != FOLDER_MIME]
        for source in files:
            accession = source["name"].removesuffix(".html")
            row = manifest.get((cik, accession))
            result = {
                "report_year": year,
                "folder_name": leaf["name"],
                "file_id": source["id"],
                "old_name": source["name"],
                "new_name": "",
                "sample_order": row.get("sample_order", "") if row else "",
                "status": "failed",
                "error": "",
                "processed_at_utc": now(),
            }
            try:
                if not row:
                    raise RuntimeError("manifest_match_not_found")
                order = int(row["sample_order"]) - 1
                new_name = (
                    f"{order}_{safe_part(row.get('company_name', ''))}_"
                    f"{safe_part(row.get('ticker', ''))}_{cik}.html"
                )
                result["new_name"] = new_name
                same_name = [item for item in files if item["name"] == new_name]
                if len(same_name) > 1 or (same_name and same_name[0]["id"] != source["id"]):
                    raise RuntimeError("duplicate_destination_filename")
                if source["name"] == new_name:
                    result["status"] = "skipped_existing_name"
                elif execute:
                    updated = safe_drive_call(
                        service.files().update(fileId=source["id"], body={"name": new_name}, fields="id,name")
                    )
                    if updated.get("name") != new_name:
                        raise RuntimeError("rename_verification_failed")
                    result["status"] = "renamed"
                else:
                    result["status"] = "planned"
            except Exception as error:  # continue with other files
                result["error"] = str(error)
            results.append(result)
    return results


def write_audit(output_dir: Path, rows: list[dict], mode: str, years: list[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fields = ["report_year", "folder_name", "file_id", "old_name", "new_name", "sample_order", "status", "error", "processed_at_utc"]
    with (output_dir / "rename_google_drive_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    (output_dir / "rename_google_drive_summary.md").write_text(
        "# Google Drive raw HTML 파일명 변경 결과\n\n"
        f"- 실행 모드: `{mode}`\n"
        f"- 대상 연도: {', '.join(years)}\n"
        f"- 처리 파일 수: {len(rows)}\n"
        f"- 상태별 집계: `{counts}`\n\n"
        "파일 내용과 Drive file ID는 변경하지 않고 파일명만 변경했다.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", default="2020,2021,2022,2023,2024,2025")
    parser.add_argument("--drive-root-folder-id", default=os.environ.get("GOOGLE_DRIVE_ROOT_FOLDER_ID", ""))
    parser.add_argument("--mode", choices=("dry_run", "execute"), default="dry_run")
    parser.add_argument("--output-dir", type=Path, default=Path("google_drive_rename"))
    args = parser.parse_args()
    if not args.drive_root_folder_id:
        raise RuntimeError("Google Drive root folder ID is required")
    years = [year.strip() for year in args.years.split(",") if year.strip()]
    service = drive_service()
    all_rows: list[dict] = []
    for year in years:
        print(f"[rename] year={year} mode={args.mode}", flush=True)
        all_rows.extend(rename_year(service, args.drive_root_folder_id, year, args.mode == "execute"))
    write_audit(args.output_dir, all_rows, args.mode, years)
    failed = [row for row in all_rows if row["status"] == "failed"]
    if failed:
        raise RuntimeError(f"rename failed for {len(failed)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
