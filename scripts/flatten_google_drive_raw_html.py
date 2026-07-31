#!/usr/bin/env python3
"""Flatten migrated Google Drive raw HTML folders without changing files."""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from googleapiclient.errors import HttpError

from migrate_r2_html_to_google_drive import (
    DRIVE_SCOPE,
    credentials,
    drive_service,
    find_child,
    safe_drive_call,
)

FOLDER_MIME = "application/vnd.google-apps.folder"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_children(service, parent_id: str, *, folders_only: bool = False) -> list[dict]:
    terms = [f"'{parent_id}' in parents", "trashed = false"]
    if folders_only:
        terms.append(f"mimeType = '{FOLDER_MIME}'")
    files: list[dict] = []
    page_token = None
    while True:
        response = safe_drive_call(
            service.files().list(
                q=" and ".join(terms),
                spaces="drive",
                fields="nextPageToken,files(id,name,mimeType,size,parents)",
                pageSize=1000,
                pageToken=page_token,
            )
        )
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            return files


def one_folder(service, parent_id: str, name: str) -> dict:
    matches = find_child(service, parent_id, name, FOLDER_MIME)
    if len(matches) != 1:
        raise RuntimeError(f"expected_one_folder:{name}:found={len(matches)}")
    return matches[0]


def folder_chain(service, root_id: str, year: str) -> dict[str, dict]:
    year_folder = one_folder(service, root_id, year)
    sample = one_folder(service, year_folder["id"], "sample_500")
    html = one_folder(service, sample["id"], "html")
    raw = one_folder(service, html["id"], "raw")
    return {"year": year_folder, "sample": sample, "html": html, "raw": raw}


def move_folder(service, folder: dict, old_parent: str, new_parent: str) -> dict:
    return safe_drive_call(
        service.files().update(
            fileId=folder["id"],
            addParents=new_parent,
            removeParents=old_parent,
            fields="id,name,parents",
        )
    )


def delete_empty_folder(service, folder: dict) -> None:
    children = list_children(service, folder["id"])
    if children:
        raise RuntimeError(f"folder_not_empty:{folder['name']}")
    safe_drive_call(service.files().delete(fileId=folder["id"]))


def process_year(service, root_id: str, year: str, execute: bool, remove_wrappers: bool) -> list[dict]:
    chain = folder_chain(service, root_id, year)
    year_id = chain["year"]["id"]
    raw_id = chain["raw"]["id"]
    leaves = list_children(service, raw_id, folders_only=True)
    results: list[dict] = []
    for leaf in sorted(leaves, key=lambda item: item["name"]):
        destination = find_child(service, year_id, leaf["name"], FOLDER_MIME)
        source_children = list_children(service, leaf["id"])
        result = {
            "report_year": year,
            "folder_name": leaf["name"],
            "folder_id": leaf["id"],
            "source_parent_id": raw_id,
            "destination_parent_id": year_id,
            "file_count": len(source_children),
            "status": "planned" if not execute else "failed",
            "error": "",
            "processed_at_utc": now(),
        }
        try:
            if len(destination) > 1:
                raise RuntimeError("ambiguous_duplicate_destination_folder")
            if destination:
                raise RuntimeError("destination_folder_already_exists")
            if execute:
                moved = move_folder(service, leaf, raw_id, year_id)
                if year_id not in moved.get("parents", []):
                    raise RuntimeError("move_parent_verification_failed")
                result["status"] = "moved"
            else:
                result["status"] = "planned"
        except Exception as error:  # keep other leaf folders independent
            result["status"] = "failed"
            result["error"] = str(error)
        results.append(result)

    if execute and remove_wrappers and all(item["status"] == "moved" for item in results):
        for key in ("raw", "html", "sample"):
            wrapper = chain[key]
            try:
                delete_empty_folder(service, wrapper)
                results.append({
                    "report_year": year,
                    "folder_name": wrapper["name"],
                    "folder_id": wrapper["id"],
                    "source_parent_id": "",
                    "destination_parent_id": "",
                    "file_count": 0,
                    "status": "removed_empty_wrapper",
                    "error": "",
                    "processed_at_utc": now(),
                })
            except Exception as error:
                results.append({
                    "report_year": year,
                    "folder_name": wrapper["name"],
                    "folder_id": wrapper["id"],
                    "source_parent_id": "",
                    "destination_parent_id": "",
                    "file_count": 0,
                    "status": "wrapper_not_removed",
                    "error": str(error),
                    "processed_at_utc": now(),
                })
    return results


def write_outputs(output_dir: Path, rows: list[dict], years: list[str], mode: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fields = [
        "report_year", "folder_name", "folder_id", "source_parent_id",
        "destination_parent_id", "file_count", "status", "error", "processed_at_utc",
    ]
    with (output_dir / "flatten_google_drive_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "mode": mode,
        "years": years,
        "leaf_folders": sum(row["status"] in {"planned", "moved", "failed"} for row in rows),
        "planned": sum(row["status"] == "planned" for row in rows),
        "moved": sum(row["status"] == "moved" for row in rows),
        "failed": sum(row["status"] == "failed" for row in rows),
        "removed_empty_wrappers": sum(row["status"] == "removed_empty_wrapper" for row in rows),
        "wrapper_not_removed": sum(row["status"] == "wrapper_not_removed" for row in rows),
        "file_count_in_leaf_folders": sum(int(row["file_count"]) for row in rows if row["status"] in {"planned", "moved", "failed"}),
    }
    (output_dir / "flatten_google_drive_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "run_summary.md").write_text(
        "# Google Drive raw HTML 폴더 평탄화 결과\n\n"
        f"- 실행 모드: `{mode}`\n"
        f"- 대상 연도: {', '.join(years)}\n"
        f"- leaf 폴더 수: {summary['leaf_folders']}\n"
        f"- 이동 성공: {summary['moved']}\n"
        f"- 실패: {summary['failed']}\n"
        f"- 빈 wrapper 제거: {summary['removed_empty_wrappers']}\n"
        f"- 파일 수(leaf 폴더 기준): {summary['file_count_in_leaf_folders']}\n\n"
        "파일 내용과 파일명은 변경하지 않았으며, 폴더 parent만 변경했다.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", default="2020,2021,2022,2023,2024,2025")
    parser.add_argument("--drive-root-folder-id", default=os.environ.get("GOOGLE_DRIVE_ROOT_FOLDER_ID", ""))
    parser.add_argument("--mode", choices=("dry_run", "execute"), default="dry_run")
    parser.add_argument("--remove-empty-wrappers", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("google_drive_flattening"))
    args = parser.parse_args()
    if not args.drive_root_folder_id:
        raise RuntimeError("Google Drive root folder ID is required")
    years = [year.strip() for year in args.years.split(",") if year.strip()]
    service = drive_service()
    root = safe_drive_call(service.files().get(fileId=args.drive_root_folder_id, fields="id,name,mimeType,trashed"))
    if root.get("mimeType") != FOLDER_MIME or root.get("trashed"):
        raise RuntimeError("configured Drive root is not an active folder")
    all_rows: list[dict] = []
    for year in years:
        print(f"[flatten] year={year} mode={args.mode}", flush=True)
        all_rows.extend(process_year(service, args.drive_root_folder_id, year, args.mode == "execute", args.remove_empty_wrappers))
    write_outputs(args.output_dir, all_rows, years, args.mode)
    failed = [row for row in all_rows if row["status"] == "failed"]
    if failed:
        raise RuntimeError(f"flattening failed for {len(failed)} folder(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
