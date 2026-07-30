#!/usr/bin/env python3
"""Create repository 2020 results from the five completed batch artifacts."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAIRS = {
    "company_language_results.csv": (
        "combined_language_results/company_language_full_sample_results.csv"
    ),
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
    paths: list[Path], output: Path, order: dict[str, int]
) -> list[dict]:
    fields: list[str] = []
    rows: list[dict] = []
    for path in paths:
        current_fields, current = read_csv(path)
        if fields and current_fields != fields:
            raise ValueError(f"incompatible columns: {path}")
        fields = current_fields
        rows.extend(current)
    rows.sort(key=lambda row: order[row["company_id"]])
    write_csv(output, fields, rows)
    return rows


def merge_sentences(
    paths: list[Path], output: Path, order: dict[str, int]
) -> int:
    fields: list[str] = []
    rows: list[dict] = []
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if fields and reader.fieldnames != fields:
                raise ValueError("incompatible AI sentence columns")
            fields = reader.fieldnames or []
            rows.extend(reader)
    rows.sort(
        key=lambda row: (
            order[row["company_id"]],
            int(row.get("sentence_order", 0)),
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def merge(root: Path, artifacts: Path) -> dict:
    sample = root / "2020/sample_500"
    _, manifest = read_csv(sample / "sample_manifest_2020_500.csv")
    order = {row["company_id"]: int(row["sample_order"]) for row in manifest}
    batch_roots = [
        artifacts / f"10k-2020-batch-{batch}" for batch in range(1, 6)
    ]
    language = sample / "language_results"
    outputs: dict[str, list[dict]] = {}
    for output_name, relative in PAIRS.items():
        outputs[output_name] = merge_csv(
            [root_path / "language" / relative for root_path in batch_roots],
            language / output_name,
            order,
        )
    combined = outputs["company_language_results.csv"]
    sentence_count = merge_sentences(
        [
            root_path
            / "language/ai_related_sentences/ai_related_sentences.csv.gz"
            for root_path in batch_roots
        ],
        language / "ai_related_sentences.csv.gz",
        order,
    )

    merged_root = artifacts / "10k-2020-sample_500-merged-results"
    object_fields, objects = read_csv(
        merged_root / "r2_object_manifest.csv"
    )
    objects.sort(key=lambda row: order[row["company_id"]])
    write_csv(sample / "r2_storage/html_r2_manifest.csv", object_fields, objects)
    warning_fields, warnings = read_csv(merged_root / "warning_cases.csv")
    write_csv(
        sample / "quality_check/warning_cases.csv",
        warning_fields,
        warnings,
    )
    failed_fields, failed = read_csv(merged_root / "failed_companies.csv")
    write_csv(
        sample / "quality_check/failed_companies.csv",
        failed_fields,
        failed,
    )

    extraction_statuses: list[str] = []
    batch_rows = {}
    for batch, batch_root in enumerate(batch_roots, 1):
        _, extraction_rows = read_csv(
            batch_root
            / "extraction/extraction_results/"
            "company_text_extraction_results.csv"
        )
        extraction_statuses.extend(
            row["extraction_status"] for row in extraction_rows
        )
        batch_summary = json.loads(
            (batch_root / "batch_summary.json").read_text(encoding="utf-8")
        )
        batch_rows[f"batch_{batch}_rows"] = batch_summary["batch_rows"]

    expected = len(manifest)
    for output_name, rows in outputs.items():
        if len(rows) != expected:
            raise ValueError(f"{output_name} does not match manifest rows")
    if len(objects) != expected:
        raise ValueError("R2 object manifest does not match sample manifest")
    for field in ("company_id", "cik", "accession_number"):
        values = [row[field] for row in combined]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate merged {field}")
    expected_sentences = sum(int(row["ai_sentence_count"]) for row in combined)
    if sentence_count != expected_sentences:
        raise ValueError("AI sentence detail/count mismatch")

    summary = {
        "final_status": (
            "partial_final_sample_below_500"
            if expected < 500
            else "success"
        ),
        "workflow_run_id": 30536764397,
        "workflow_url": (
            "https://github.com/Vulter3653/s-p500/actions/runs/30536764397"
        ),
        **batch_rows,
        "merge_job_status": "success",
        "manifest_rows": expected,
        "combined_rows": len(combined),
        "r2_rows": len(objects),
        "r2_uploaded": sum(
            row["upload_status"] == "uploaded" for row in objects
        ),
        "r2_skipped": sum(
            row["upload_status"].startswith("skipped") for row in objects
        ),
        "r2_conflicts": 0,
        "extraction_success": sum(
            status == "success" for status in extraction_statuses
        ),
        "extraction_warning": sum(
            status == "warning" for status in extraction_statuses
        ),
        "extraction_failed": sum(
            status.startswith("failed") for status in extraction_statuses
        ),
        "language_completed": len(combined) - len(failed),
        "failed_rows": len(failed),
        "warning_rows": len(warnings),
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
        "# 2020 10-K Language Sample Run Summary\n\n"
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
