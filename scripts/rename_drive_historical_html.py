#!/usr/bin/env python3
"""Safely rename historical Google Drive HTML files using repository manifests.

The script operates on a mounted Drive directory.  It never talks to Drive and
does not alter file contents; a complete dry-run plan is built before execute.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

YEARS = tuple(range(2006, 2020))
MANIFEST_FIELDS = {"sample_order", "company_name", "ticker", "cik", "accession_number", "report_year", "r2_object_key"}
STANDARD = re.compile(r"^(\d{3})_20(?:0[6-9]|1[0-9])_.+_[A-Z0-9-]+_(\d{10})\.html$")
INVALID = re.compile(r"[\\/:*?\"<>|]")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_company_name(value: str) -> str:
    value = INVALID.sub("", value.strip()).replace("'", "")
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._")
    return value or "unknown"


def sanitize_ticker(value: str) -> str:
    value = value.strip().replace(".", "-")
    return re.sub(r"[^A-Za-z0-9-]", "", value).upper() or "UNKNOWN"


def normalized_cik(value: str) -> str:
    digits = re.sub(r"\D", "", str(value))
    if not digits:
        raise ValueError("missing_cik")
    return digits.zfill(10)


def manifest_path(repo_root: Path, year: int) -> Path:
    return repo_root / str(year) / "sample_503" / "sample" / "final_analysis_sample_503.csv"


def read_manifest(path: Path, year: int) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = MANIFEST_FIELDS - fields
        if missing:
            raise ValueError(f"manifest_missing_columns:{path}:{sorted(missing)}")
        rows = [dict(row) for row in reader]
    orders = [row["sample_order"].strip() for row in rows]
    accessions = [row["accession_number"].strip() for row in rows]
    if len(orders) != len(set(orders)):
        raise ValueError(f"duplicate_sample_order:{year}")
    if len(accessions) != len(set(accessions)):
        raise ValueError(f"duplicate_accession_number:{year}")
    for row in rows:
        if str(row["report_year"]).strip() != str(year):
            raise ValueError(f"report_year_mismatch:{year}:{row['report_year']}")
    return rows


def plan_year(drive_root: Path, repo_root: Path, year: int) -> list[dict[str, str]]:
    manifest = read_manifest(manifest_path(repo_root, year), year)
    by_accession = {row["accession_number"].strip(): row for row in manifest}
    html_files = sorted((drive_root / str(year)).rglob("*.html")) if (drive_root / str(year)).exists() else []
    matched: dict[str, list[Path]] = {}
    standard_rows: dict[tuple[str, str], list[Path]] = {}
    for path in html_files:
        standard = STANDARD.match(path.name)
        if standard:
            standard_rows.setdefault((standard.group(1), standard.group(2)), []).append(path)
            continue
        accession = path.stem
        if accession in by_accession:
            matched.setdefault(accession, []).append(path)

    result: list[dict[str, str]] = []
    seen_paths: set[Path] = set()
    destinations: dict[str, str] = {}
    for row in manifest:
        accession = row["accession_number"].strip()
        candidates = matched.get(accession, [])
        name = f"{int(row['sample_order']):03d}_{year}_{sanitize_company_name(row['company_name'])}_{sanitize_ticker(row['ticker'])}_{normalized_cik(row['cik'])}.html"
        destination = str(drive_root / str(year) / name)
        status, reason, source = "failed", "unmatched_manifest_row", ""
        if len(candidates) == 1:
            source_path = candidates[0]
            seen_paths.add(source_path)
            source = str(source_path)
            if name in destinations and destinations[name] != source:
                reason = "duplicate_destination_filename"
            elif Path(destination).exists() and Path(destination) != source_path:
                reason = "destination_exists"
            elif source_path.name == name:
                status, reason = "already_standard", "already_standard_filename"
            else:
                status, reason = "planned", "accession_exact_match"
        elif len(candidates) > 1:
            reason = "multiple_source_files_for_manifest_row"
        destinations[name] = source
        result.append({"year": str(year), "sample_order": row["sample_order"], "accession_number": accession,
                       "company_name": row["company_name"], "ticker": row["ticker"], "cik": normalized_cik(row["cik"]),
                       "old_path": source, "new_path": destination, "old_filename": Path(source).name if source else "",
                       "new_filename": name, "match_method": "accession_exact" if source else "", "status": status, "reason": reason})
    for (order, cik), paths in standard_rows.items():
        matches = [r for r in manifest if f"{int(r['sample_order']):03d}" == order and normalized_cik(r["cik"]) == cik]
        if len(paths) != 1 or len(matches) != 1:
            result.append({"year": str(year), "sample_order": order, "accession_number": "", "company_name": "", "ticker": "", "cik": cik,
                         "old_path": str(paths[0]) if paths else "", "new_path": "", "old_filename": paths[0].name if paths else "", "new_filename": "",
                         "match_method": "standard_filename_validation", "status": "failed", "reason": "standard_filename_manifest_mismatch"})
        else:
            seen_paths.add(paths[0])
            result.append({"year": str(year), "sample_order": order, "accession_number": matches[0]["accession_number"], "company_name": matches[0]["company_name"],
                         "ticker": matches[0]["ticker"], "cik": cik, "old_path": str(paths[0]), "new_path": str(paths[0]), "old_filename": paths[0].name,
                         "new_filename": paths[0].name, "match_method": "standard_filename_validation", "status": "already_standard", "reason": "already_standard_filename"})
    for path in html_files:
        if path not in seen_paths and not STANDARD.match(path.name):
            result.append({"year": str(year), "sample_order": "", "accession_number": "", "company_name": "", "ticker": "", "cik": "",
                           "old_path": str(path), "new_path": "", "old_filename": path.name, "new_filename": "", "match_method": "", "status": "unmatched_file", "reason": "accession_not_in_manifest"})
    return result


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drive-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--confirmation", default="")
    args = parser.parse_args()
    if (args.start_year, args.end_year) != (2019, 2006):
        raise SystemExit("this tool is restricted to years 2019 through 2006")
    if args.execute and args.confirmation != "RENAME_HISTORICAL_HTML_2006_2019":
        raise SystemExit("--execute requires confirmation RENAME_HISTORICAL_HTML_2006_2019")
    if not args.drive_root.exists():
        raise SystemExit(
            f"drive root does not exist: {args.drive_root}. "
            "Mount Google Drive (for example in Colab) before running this command."
        )
    if not args.drive_root.is_dir():
        raise SystemExit(f"drive root is not a directory: {args.drive_root}")
    audit = args.drive_root / "rename_audit_2006_2019"
    audit.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for year in range(args.start_year, args.end_year - 1, -1):
        rows.extend(plan_year(args.drive_root, args.repo_root, year))
    fields = ["year", "sample_order", "accession_number", "company_name", "ticker", "cik", "old_path", "new_path", "old_filename", "new_filename", "match_method", "status", "reason"]
    write_csv(audit / "rename_plan.csv", rows, fields)
    failures = [r for r in rows if r["status"] in {"failed", "unmatched_file", "unmatched_manifest_row"}]
    if failures:
        write_csv(audit / "conflicts.csv", failures, fields)
        raise SystemExit(f"validation failed: {len(failures)} unmatched/conflicting entries")
    changed: list[dict[str, str]] = []
    if args.execute:
        for row in rows:
            if row["status"] != "planned":
                continue
            source, destination = Path(row["old_path"]), Path(row["new_path"])
            source.rename(destination)
            changed.append({"year": row["year"], "renamed_path": str(destination), "original_path": str(source)})
    write_csv(audit / "rename_result.csv", rows, fields)
    write_csv(audit / "rollback_manifest.csv", changed, ["year", "renamed_path", "original_path"])
    write_csv(audit / "unmatched_files.csv", [r for r in rows if r["status"] == "unmatched_file"], fields)
    write_csv(audit / "unmatched_manifest_rows.csv", [r for r in rows if r["status"] == "unmatched_manifest_row"], fields)
    (audit / "summary.json").write_text(json.dumps({"mode": "execute" if args.execute else "dry-run", "rows": len(rows), "planned": sum(r["status"] == "planned" for r in rows), "already_standard": sum(r["status"] == "already_standard" for r in rows), "renamed": len(changed), "external_requests": 0}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
