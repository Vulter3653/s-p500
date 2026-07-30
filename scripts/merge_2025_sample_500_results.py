#!/usr/bin/env python3
"""Merge immutable sample 300 results with completed batch 4 and 5 artifacts."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAIRS = {
    "company_ai_disclosure_results.csv": (
        "ai_related_sentences/company_ai_disclosure_results.csv"
    ),
    "company_ai_level_lm_results.csv": (
        "loughran_mcdonald/company_ai_level_lm_results.csv"
    ),
    "company_report_level_lm_results.csv": (
        "loughran_mcdonald/company_report_level_lm_results.csv"
    ),
    "company_ai_level_concreteness_results.csv": (
        "textual_concreteness/company_ai_level_concreteness_results.csv"
    ),
    "company_report_level_concreteness_results.csv": (
        "textual_concreteness/company_report_level_concreteness_results.csv"
    ),
}


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def merge_csv(
    existing: Path, additions: list[Path], output: Path, order: dict[str, int]
) -> list[dict]:
    fields, existing_rows = read_csv(existing)
    rows = list(existing_rows)
    for path in additions:
        current_fields, current = read_csv(path)
        if current_fields != fields:
            raise ValueError(f"incompatible columns: {path}")
        rows.extend(current)
    rows.sort(key=lambda row: order[row["company_id"]])
    write_csv(output, fields, rows)
    if rows[: len(existing_rows)] != existing_rows:
        raise ValueError(f"existing rows changed while merging {output.name}")
    return rows


def merge_sentences(
    existing: Path, additions: list[Path], output: Path, order: dict[str, int]
) -> int:
    all_rows: list[dict] = []
    fields: list[str] = []
    for path in [existing, *additions]:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if fields and reader.fieldnames != fields:
                raise ValueError("incompatible AI sentence columns")
            fields = reader.fieldnames or []
            all_rows.extend(reader)
    all_rows.sort(
        key=lambda row: (
            order[row["company_id"]],
            int(row.get("sentence_order", 0)),
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(all_rows)
    return len(all_rows)


def merge(root: Path, artifacts: Path) -> dict:
    sample = root / "2025/sample_500"
    existing = root / "2025/sample_300"
    _, manifest = read_csv(sample / "sample_manifest_2025_500.csv")
    order = {row["company_id"]: int(row["sample_order"]) for row in manifest}
    batch_roots = [
        artifacts / "10k-2025-batch-4/language",
        artifacts / "10k-2025-batch-5/language",
    ]
    language = sample / "language_results"
    combined = merge_csv(
        existing / "language_results/company_language_results.csv",
        [
            path
            / "combined_language_results/company_language_full_sample_results.csv"
            for path in batch_roots
        ],
        language / "company_language_results.csv",
        order,
    )
    for output_name, relative in PAIRS.items():
        merge_csv(
            existing / f"language_results/{output_name}",
            [path / relative for path in batch_roots],
            language / output_name,
            order,
        )
    sentence_count = merge_sentences(
        existing / "language_results/ai_related_sentences.csv.gz",
        [
            path / "ai_related_sentences/ai_related_sentences.csv.gz"
            for path in batch_roots
        ],
        language / "ai_related_sentences.csv.gz",
        order,
    )

    object_fields, old_objects = read_csv(
        existing / "r2_storage/html_r2_manifest.csv"
    )
    current_fields, new_objects = read_csv(
        artifacts
        / "10k-2025-sample_500-merged-results/r2_object_manifest.csv"
    )
    if current_fields != object_fields:
        raise ValueError("incompatible R2 object manifest columns")
    objects = old_objects + new_objects
    objects.sort(key=lambda row: order[row["company_id"]])
    write_csv(sample / "r2_storage/html_r2_manifest.csv", object_fields, objects)
    if objects[: len(old_objects)] != old_objects:
        raise ValueError("existing R2 object rows changed")

    warning_fields, old_warnings = read_csv(
        existing / "quality_check/warning_cases.csv"
    )
    current_fields, new_warnings = read_csv(
        artifacts
        / "10k-2025-sample_500-merged-results/warning_cases.csv"
    )
    if current_fields != warning_fields:
        raise ValueError("incompatible warning columns")
    write_csv(
        sample / "quality_check/warning_cases.csv",
        warning_fields,
        old_warnings + new_warnings,
    )
    failed_fields, old_failed = read_csv(
        existing / "quality_check/failed_companies.csv"
    )
    current_fields, new_failed = read_csv(
        artifacts
        / "10k-2025-sample_500-merged-results/failed_companies.csv"
    )
    if current_fields != failed_fields:
        raise ValueError("incompatible failure columns")
    failed = old_failed + new_failed
    write_csv(
        sample / "quality_check/failed_companies.csv",
        failed_fields,
        failed,
    )

    extraction_statuses: list[str] = []
    for batch in (4, 5):
        _, extraction_rows = read_csv(
            artifacts
            / f"10k-2025-batch-{batch}/extraction/extraction_results/"
            "company_text_extraction_results.csv"
        )
        extraction_statuses.extend(
            row["extraction_status"] for row in extraction_rows
        )

    if len(combined) != len(manifest) or len(objects) != len(manifest):
        raise ValueError("merged company or R2 rows differ from manifest")
    for field in ("company_id", "cik", "accession_number"):
        values = [row[field] for row in combined]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate merged {field}")
    expected_sentences = sum(int(row["ai_sentence_count"]) for row in combined)
    if sentence_count != expected_sentences:
        raise ValueError("AI sentence detail/count mismatch")

    summary = {
        "final_status": "partial_final_sample_below_500",
        "workflow_run_id": 30528839298,
        "workflow_url": (
            "https://github.com/Vulter3653/s-p500/actions/runs/30528839298"
        ),
        "batch_4_status": "success",
        "batch_5_status": "success",
        "merge_job_status": "success",
        "manifest_rows": len(manifest),
        "existing_rows": len(combined) - len(new_objects),
        "new_rows": len(new_objects),
        "combined_rows": len(combined),
        "r2_rows": len(objects),
        "r2_uploaded_new": sum(
            row["upload_status"] == "uploaded" for row in new_objects
        ),
        "r2_skipped_new": sum(
            row["upload_status"].startswith("skipped") for row in new_objects
        ),
        "r2_conflicts_new": 0,
        "extraction_success_new": sum(
            status == "success" for status in extraction_statuses
        ),
        "extraction_warning_new": sum(
            status == "warning" for status in extraction_statuses
        ),
        "extraction_failed_new": sum(
            status.startswith("failed") for status in extraction_statuses
        ),
        "language_completed_new": len(new_objects) - len(new_failed),
        "failed_rows": len(failed),
        "warning_rows_new_batches": len(new_warnings),
        "ai_sentence_rows": sentence_count,
        "ai_disclosure_firms": sum(
            int(row["ai_disclosure_binary"]) for row in combined
        ),
        "ai_non_disclosure_firms": sum(
            not int(row["ai_disclosure_binary"]) for row in combined
        ),
        "single_ai_sentence_firms": sum(
            int(row["ai_sentence_count"]) == 1 for row in combined
        ),
        "stem_collision_warning_firms": sum(
            int(row["report_concreteness_stem_collision_count"] or 0) > 0
            or int(row["ai_concreteness_stem_collision_count"] or 0) > 0
            for row in combined
        ),
        "version": "0.12.0",
    }
    (sample / "run_summary.md").write_text(
        "# 2025 Final Sample Run Summary\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in summary.items())
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    merge(args.root.resolve(), args.artifacts.resolve())
