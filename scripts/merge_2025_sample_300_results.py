#!/usr/bin/env python3
"""Merge the immutable pilot results with completed batch 2 and 3 artifacts."""

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
    pilot: Path, batches: list[Path], output: Path, order: dict[str, int]
) -> list[dict]:
    fields, rows = read_csv(pilot)
    for path in batches:
        current_fields, current = read_csv(path)
        if current_fields != fields:
            raise ValueError(f"incompatible columns: {path}")
        rows.extend(current)
    rows.sort(key=lambda row: order[row["company_id"]])
    write_csv(output, fields, rows)
    return rows


def merge_sentences(
    pilot: Path, batches: list[Path], output: Path, order: dict[str, int]
) -> int:
    all_rows: list[dict] = []
    fields: list[str] = []
    for path in [pilot, *batches]:
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


def merge(root: Path, artifacts: Path) -> None:
    sample = root / "2025/sample_300"
    pilot = root / "2025/pilot_100/language_full_sample"
    fields, manifest = read_csv(sample / "sample_manifest_2025_300.csv")
    del fields
    order = {row["company_id"]: int(row["sample_order"]) for row in manifest}
    batch_roots = [
        artifacts / "10k-2025-batch-2/language",
        artifacts / "10k-2025-batch-3/language",
    ]
    language = sample / "language_results"
    combined = merge_csv(
        pilot
        / "combined_language_results/company_language_full_sample_results.csv",
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
            pilot / relative,
            [path / relative for path in batch_roots],
            language / output_name,
            order,
        )
    sentence_count = merge_sentences(
        pilot / "ai_related_sentences/ai_related_sentences.csv.gz",
        [
            path / "ai_related_sentences/ai_related_sentences.csv.gz"
            for path in batch_roots
        ],
        language / "ai_related_sentences.csv.gz",
        order,
    )

    _, pilot_html = read_csv(
        root / "2025/pilot_100/html/manifest/html_manifest.csv"
    )
    old_objects = [
        {
            "company_id": row["final_sample_id"],
            "cik": row["cik"],
            "accession_number": row["accession_number"],
            "object_key": (
                f"2025/pilot_100/html/raw/{row['cik']}/"
                f"{row['accession_number']}.html"
            ),
            "sha256": row["sha256"],
            "file_size": row["file_size"],
            "upload_status": "existing_pilot_object",
        }
        for row in pilot_html
    ]
    object_fields, new_objects = read_csv(
        artifacts
        / "10k-2025-sample_300-merged-results/r2_object_manifest.csv"
    )
    objects = old_objects + new_objects
    objects.sort(key=lambda row: order[row["company_id"]])
    write_csv(
        sample / "r2_storage/html_r2_manifest.csv",
        object_fields,
        objects,
    )

    _, warnings = read_csv(
        artifacts
        / "10k-2025-sample_300-merged-results/warning_cases.csv"
    )
    failed_fields, failed = read_csv(
        artifacts
        / "10k-2025-sample_300-merged-results/failed_companies.csv"
    )
    write_csv(
        sample / "quality_check/failed_companies.csv",
        failed_fields,
        failed,
    )
    warning_fields = list(warnings[0]) if warnings else [
        "company_id", "cik", "accession_number", "warning_type", "warning_detail"
    ]
    write_csv(
        sample / "quality_check/warning_cases.csv",
        warning_fields,
        warnings,
    )

    if len(combined) != 300 or len(objects) != 300:
        raise ValueError("merged company or R2 result does not contain 300 rows")
    for field in ("company_id", "cik", "accession_number"):
        values = [row[field] for row in combined]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate merged {field}")
    expected_sentences = sum(int(row["ai_sentence_count"]) for row in combined)
    if sentence_count != expected_sentences:
        raise ValueError("AI sentence detail/count mismatch")
    summary = {
        "workflow_run_id": 30526454303,
        "workflow_url": (
            "https://github.com/Vulter3653/s-p500/actions/runs/30526454303"
        ),
        "batch_2_status": "success",
        "batch_3_status": "success",
        "merge_job_status": "success",
        "manifest_rows": len(manifest),
        "combined_rows": len(combined),
        "r2_rows": len(objects),
        "new_r2_rows": len(new_objects),
        "r2_uploaded": sum(
            row["upload_status"] == "uploaded" for row in new_objects
        ),
        "r2_skipped": sum(
            row["upload_status"].startswith("skipped") for row in new_objects
        ),
        "r2_conflicts": 0,
        "failed_rows": len(failed),
        "warning_rows_new_batches": len(warnings),
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
        "# 2025 Sample 300 Run Summary\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in summary.items())
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    merge(args.root.resolve(), args.artifacts.resolve())
