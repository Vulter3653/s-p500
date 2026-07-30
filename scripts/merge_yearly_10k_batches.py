#!/usr/bin/env python3
"""Merge available yearly batch artifacts without including original HTML."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def collect_rows(root: Path, filename: str) -> tuple[list[str], list[dict]]:
    fields: list[str] = []
    rows: list[dict] = []
    for path in sorted(root.rglob(filename)):
        current_fields, current_rows = read_csv(path)
        if current_fields and not fields:
            fields = current_fields
        elif current_fields and current_fields != fields:
            raise ValueError(f"incompatible columns while merging {filename}")
        rows.extend(current_rows)
    return fields, rows


def ensure_unique(rows: list[dict], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        values = [row.get(field, "") for row in rows if row.get(field, "")]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {field} in merged {label}")


def merge(input_root: Path, output_root: Path, report_year: str) -> dict:
    output_root.mkdir(parents=True, exist_ok=True)
    language_fields, language_rows = collect_rows(
        input_root, "company_language_full_sample_results.csv"
    )
    object_fields, object_rows = collect_rows(
        input_root, "r2_object_manifest.csv"
    )
    failed_fields = [
        "company_id",
        "cik",
        "accession_number",
        "failure_stage",
        "failure_reason",
    ]
    failed_rows = []
    for path in sorted(input_root.rglob("failed_companies.csv")):
        _, current_rows = read_csv(path)
        failed_rows.extend(
            {
                "company_id": row.get("company_id", ""),
                "cik": row.get("cik", ""),
                "accession_number": row.get("accession_number", ""),
                "failure_stage": row.get(
                    "failure_stage", row.get("failure_status", "")
                ),
                "failure_reason": row.get("failure_reason", ""),
            }
            for row in current_rows
        )
    warning_fields, warning_rows = collect_rows(input_root, "warning_cases.csv")
    language_warning_fields, language_warning_rows = collect_rows(
        input_root, "failed_or_warning_cases.csv"
    )
    if language_warning_fields:
        if warning_fields and language_warning_fields != warning_fields:
            warning_rows.extend(
                {
                    "company_id": row.get("company_id", ""),
                    "cik": row.get("cik", ""),
                    "accession_number": row.get("accession_number", ""),
                    "warning_type": row.get(
                        "warning_type", row.get("warning_reason", "")
                    ),
                    "warning_detail": row.get(
                        "warning_detail", row.get("recommended_action", "")
                    ),
                }
                for row in language_warning_rows
            )
        else:
            warning_fields = language_warning_fields
            warning_rows.extend(language_warning_rows)

    ensure_unique(
        language_rows,
        ("company_id", "cik", "accession_number"),
        "language results",
    )
    ensure_unique(
        object_rows,
        ("company_id", "cik", "accession_number", "object_key"),
        "R2 object manifest",
    )

    summaries = []
    for path in sorted(input_root.rglob("batch_summary.json")):
        try:
            summaries.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            summaries.append(
                {
                    "batch_id": "",
                    "status": "failed",
                    "error_type": "invalid_batch_summary",
                }
            )
    present_batches = {
        int(item["batch_id"])
        for item in summaries
        if str(item.get("batch_id", "")).isdigit()
    }
    missing_batches = sorted(set(range(1, 6)) - present_batches)
    failed_batches = sorted(
        int(item["batch_id"])
        for item in summaries
        if str(item.get("batch_id", "")).isdigit()
        and item.get("status") == "failed"
    )

    write_csv(
        output_root / "company_language_results.csv",
        language_fields
        or ["company_id", "cik", "ticker", "accession_number"],
        language_rows,
    )
    write_csv(
        output_root / "r2_object_manifest.csv",
        object_fields
        or [
            "company_id",
            "cik",
            "accession_number",
            "object_key",
            "sha256",
            "file_size",
            "upload_status",
        ],
        object_rows,
    )
    write_csv(
        output_root / "failed_companies.csv",
        failed_fields
        or [
            "company_id",
            "cik",
            "accession_number",
            "failure_stage",
            "failure_reason",
        ],
        failed_rows,
    )
    write_csv(
        output_root / "warning_cases.csv",
        warning_fields
        or [
            "company_id",
            "cik",
            "accession_number",
            "warning_type",
            "warning_detail",
        ],
        warning_rows,
    )
    summary = {
        "report_year": report_year,
        "expected_batches": 5,
        "available_batch_summaries": len(summaries),
        "missing_batches": missing_batches,
        "failed_batches": failed_batches,
        "language_result_rows": len(language_rows),
        "r2_object_rows": len(object_rows),
        "failed_company_rows": len(failed_rows),
        "warning_rows": len(warning_rows),
        "merge_status": (
            "partial" if missing_batches or failed_batches else "completed"
        ),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_root / "year_run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return summary


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-year", required=True)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    merge(args.input_dir.resolve(), args.output_dir.resolve(), args.report_year)
