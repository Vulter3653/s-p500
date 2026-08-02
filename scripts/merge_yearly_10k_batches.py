#!/usr/bin/env python3
"""Merge available yearly batch artifacts without including original HTML."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


BATCH_SIZE = 100
MAX_SAMPLE_SIZE = 503
MAX_BATCH_COUNT = 6


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
    def sort_key(path: Path) -> tuple[int, str]:
        match = next(
            (part.removeprefix("batch_") for part in path.parts if part.startswith("batch_")),
            "",
        )
        return (int(match) if match.isdigit() else MAX_BATCH_COUNT + 1, str(path))

    for path in sorted(root.rglob(filename), key=sort_key):
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


def validate_batch_summaries(
    summaries: list[dict], expected_batches: set[int]
) -> dict:
    if any(batch < 1 or batch > MAX_BATCH_COUNT for batch in expected_batches):
        raise ValueError("expected batch IDs must be between 1 and 6")
    present: dict[int, dict] = {}
    for item in summaries:
        value = str(item.get("batch_id", ""))
        if not value.isdigit():
            continue
        batch_id = int(value)
        if batch_id < 1 or batch_id > MAX_BATCH_COUNT:
            raise ValueError(f"invalid batch ID in summary: {batch_id}")
        if batch_id in present:
            raise ValueError(f"duplicate batch summary: {batch_id}")
        present[batch_id] = item

    ranges = []
    manifest_counts = set()
    calculated_batch_counts = set()
    for batch_id, item in present.items():
        source_rows = item.get("manifest_row_count", item.get("source_rows", ""))
        if str(source_rows).isdigit():
            source_rows = int(source_rows)
            if not 1 <= source_rows <= MAX_SAMPLE_SIZE:
                raise ValueError(f"invalid manifest row count: {source_rows}")
            manifest_counts.add(source_rows)
        count = item.get("batch_count", "")
        if str(count).isdigit():
            count = int(count)
            if not 1 <= count <= MAX_BATCH_COUNT:
                raise ValueError(f"invalid batch count: {count}")
            calculated_batch_counts.add(count)
        start = item.get("batch_start_index", "")
        end = item.get("batch_end_index_exclusive", "")
        if not (str(start).isdigit() and str(end).isdigit()):
            row_start = item.get("row_start", "")
            row_end = item.get("row_end", "")
            if str(row_start).isdigit() and str(row_end).isdigit():
                start, end = int(row_start) - 1, int(row_end)
        if str(start).isdigit() and str(end).isdigit():
            start, end = int(start), int(end)
            if end <= start or end - start > BATCH_SIZE:
                raise ValueError(f"invalid row range for batch {batch_id}")
            if source_rows and end > source_rows:
                raise ValueError(f"batch range exceeds manifest for batch {batch_id}")
            if source_rows and batch_id > (source_rows + BATCH_SIZE - 1) // BATCH_SIZE:
                raise ValueError(
                    f"batch {batch_id} exceeds manifest batch count {source_rows}"
                )
            ranges.append((start, end, batch_id))

    ranges.sort()
    for previous, current in zip(ranges, ranges[1:]):
        if current[0] < previous[1]:
            raise ValueError(
                f"overlapping batch ranges: {previous[2]} and {current[2]}"
            )
    if len(manifest_counts) > 1:
        raise ValueError("batch summaries disagree on manifest row count")
    if len(calculated_batch_counts) > 1:
        raise ValueError("batch summaries disagree on batch count")

    return {
        "present_batches": sorted(present),
        "manifest_row_count": next(iter(manifest_counts), None),
        "batch_count": next(iter(calculated_batch_counts), None),
        "ranges": ranges,
    }


def merge(
    input_root: Path,
    output_root: Path,
    report_year: str,
    expected_batches: set[int] | None = None,
) -> dict:
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
    expected_batches = expected_batches or set(range(1, 6))
    batch_validation = validate_batch_summaries(summaries, expected_batches)
    missing_batches = sorted(expected_batches - present_batches)
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
        "expected_batches": sorted(expected_batches),
        "manifest_row_count": batch_validation["manifest_row_count"],
        "batch_count": batch_validation["batch_count"],
        "batch_size_limit": BATCH_SIZE,
        "maximum_sample_size": MAX_SAMPLE_SIZE,
        "batch_ranges": [
            {
                "batch_id": batch_id,
                "start_index": start,
                "end_index_exclusive": end,
            }
            for start, end, batch_id in batch_validation["ranges"]
        ],
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
    parser.add_argument("--expected-batches", default="1,2,3,4,5")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    expected = {int(value) for value in args.expected_batches.split(",") if value}
    merge(
        args.input_dir.resolve(),
        args.output_dir.resolve(),
        args.report_year,
        expected,
    )
