#!/usr/bin/env python3
"""Validate extracted pilot text and create researcher-friendly quality tables."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import random
import re
from pathlib import Path

import pandas as pd

try:
    from extract_10k_analysis_text import INPUT, OUTPUT, sha256, validate_input
except ModuleNotFoundError:
    from scripts.extract_10k_analysis_text import INPUT, OUTPUT, sha256, validate_input

HTML_TAG = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")
SCRIPT = re.compile(r"(?:<script\b|javascript:|\bfunction\s*\()", re.I)
CSS = re.compile(r"(?:<style\b|\bfont-family\s*:|\bdisplay\s*:|\bvisibility\s*:)", re.I)
XBRL = re.compile(r"(?:xmlns:ix|xmlns:xbrli|<ix:|</ix:)", re.I)
BROKEN = re.compile("\ufffd")


def excerpt(text: str, length: int = 700) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized[:length]


def csv_unique_counts(path: Path, id_column: str, company_column: str) -> tuple[int, int, int]:
    row_count = 0
    ids = set()
    companies = set()
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            row_count += 1
            ids.add(row[id_column])
            companies.add(row[company_column])
    return row_count, len(ids), len(companies)


def check(root: Path) -> dict[str, int]:
    manifest = pd.read_csv(root / INPUT, dtype=str, keep_default_na=False)
    validate_input(root, manifest)
    output = root / OUTPUT
    results = pd.read_csv(
        output / "extraction_results/company_text_extraction_results.csv",
        dtype=str, keep_default_na=False,
    )
    sections = pd.read_csv(
        output / "analysis_tables/sections.csv", dtype=str, keep_default_na=False
    )
    if len(results) != 100 or results["company_id"].nunique() != 100:
        raise ValueError("company extraction results must contain 100 unique companies")
    if results["accession_number"].nunique() != 100 or results["cik"].nunique() != 100:
        raise ValueError("company extraction results contain duplicate accession or CIK")

    quality_rows = []
    section_quality_rows = []
    warning_rows = []
    sentence_lengths: dict[str, list[int]] = {}
    with gzip.open(
        output / "analysis_tables/sentences.csv.gz", "rt", newline="", encoding="utf-8"
    ) as source:
        for sentence in csv.DictReader(source):
            if sentence["included_in_analysis_text"] == "1":
                sentence_lengths.setdefault(sentence["company_id"], []).append(
                    int(sentence["word_count"])
                )
    for row in results.to_dict("records"):
        analysis_path = root / row["analysis_text_file"]
        structure_path = root / row["structure_preserved_text_file"]
        table_path = root / row["table_text_file"]
        analysis = analysis_path.read_text(encoding="utf-8") if analysis_path.exists() else ""
        words = analysis.split()
        sentences = max(int(row["analysis_sentence_count"] or 0), 1)
        lengths = sentence_lengths.get(row["company_id"], [])
        short_sentence_ratio = (
            sum(length <= 3 for length in lengths) / len(lengths) if lengths else 0.0
        )
        long_sentence_ratio = (
            sum(length > 100 for length in lengths) / len(lengths) if lengths else 0.0
        )
        tag_count = len(HTML_TAG.findall(analysis))
        script_count = len(SCRIPT.findall(analysis))
        css_count = len(CSS.findall(analysis))
        xbrl_count = len(XBRL.findall(analysis))
        broken_count = len(BROKEN.findall(analysis))
        table_contamination = int("[TABLE " in analysis)
        numeric_tokens = sum(bool(re.search(r"\d", word)) for word in words)
        company_sections = sections.loc[sections["company_id"].eq(row["company_id"])]
        statuses = dict(zip(company_sections["section_code"], company_sections["extraction_status"]))
        quality = {
            "company_id": row["company_id"], "cik": row["cik"], "ticker": row["ticker"],
            "accession_number": row["accession_number"],
            "html_file_bytes": int(row["source_html_bytes"] or 0),
            "analysis_text_bytes": analysis_path.stat().st_size if analysis_path.exists() else 0,
            "structure_preserved_text_bytes": structure_path.stat().st_size if structure_path.exists() else 0,
            "table_text_bytes": table_path.stat().st_size if table_path.exists() else 0,
            "analysis_to_html_size_ratio": (
                round(analysis_path.stat().st_size / int(row["source_html_bytes"]), 6)
                if analysis_path.exists() and int(row["source_html_bytes"] or 0) else 0
            ),
            "word_count": len(words), "paragraph_count": int(row["analysis_paragraph_count"] or 0),
            "sentence_count": int(row["analysis_sentence_count"] or 0),
            "detected_section_count": int(row["detected_section_count"] or 0),
            "item_1_detected": int(statuses.get("item_1") == "detected"),
            "item_1a_detected": int(statuses.get("item_1a") == "detected"),
            "item_7_detected": int(statuses.get("item_7") == "detected"),
            "item_8_detected": int(statuses.get("item_8") == "detected"),
            "html_tag_residual_count": tag_count,
            "javascript_residual_count": script_count,
            "css_residual_count": css_count,
            "xbrl_namespace_residual_count": xbrl_count,
            "broken_character_count": broken_count,
            "numeric_token_ratio": round(numeric_tokens / len(words), 6) if words else 0,
            "very_short_sentence_ratio": short_sentence_ratio,
            "very_long_sentence_ratio": long_sentence_ratio,
            "table_marker_contamination": table_contamination,
            "warning_count": int(row["warning_count"] or 0),
            "quality_status": "pass",
        }
        defects = []
        if not analysis.strip():
            defects.append("empty_analysis_text")
        if row["analysis_text_sha256"] != sha256(analysis_path):
            defects.append("analysis_sha_mismatch")
        if tag_count:
            defects.append("html_tag_residual")
        if script_count or css_count:
            defects.append("script_or_style_residual")
        if xbrl_count:
            defects.append("xbrl_namespace_residual")
        if broken_count:
            defects.append("broken_character")
        if table_contamination:
            defects.append("table_marker_in_analysis")
        if int(row["analysis_word_count"] or 0) < 1000:
            defects.append("analysis_text_unusually_short")
        if not quality["item_7_detected"]:
            defects.append("item_7_not_detected")
        core_section_warnings = company_sections.loc[
            company_sections["section_code"].isin({"item_1", "item_1a", "item_7", "item_8"})
            & company_sections["warning_message"].ne(""),
            "section_code",
        ].tolist()
        if core_section_warnings:
            defects.append("core_section_boundary_warning:" + ",".join(core_section_warnings))
        if defects:
            quality["quality_status"] = "warning"
            warning_rows.append({
                "company_id": row["company_id"], "cik": row["cik"],
                "ticker": row["ticker"], "accession_number": row["accession_number"],
                "case_status": row["extraction_status"],
                "warning_or_failure_reason": "|".join(defects),
                "recommended_action": "review structure-preserved text and section boundaries",
            })
        quality_rows.append(quality)
        section_quality_rows.append({
            "company_id": row["company_id"], "cik": row["cik"], "ticker": row["ticker"],
            "accession_number": row["accession_number"],
            "detected_section_count": quality["detected_section_count"],
            "item_1_status": statuses.get("item_1", "missing_row"),
            "item_1a_status": statuses.get("item_1a", "missing_row"),
            "item_7_status": statuses.get("item_7", "missing_row"),
            "item_8_status": statuses.get("item_8", "missing_row"),
            "not_present_count": int(company_sections["extraction_status"].eq("not_present").sum()),
            "section_warning_count": int(company_sections["warning_message"].ne("").sum()),
            "section_detection_status": "warning" if not quality["item_7_detected"] else "pass",
        })

    quality_dir = output / "quality_check"
    quality_dir.mkdir(parents=True, exist_ok=True)
    quality = pd.DataFrame(quality_rows)
    section_quality = pd.DataFrame(section_quality_rows)
    quality.to_csv(quality_dir / "company_text_quality_check.csv", index=False)
    section_quality.to_csv(quality_dir / "section_detection_quality_check.csv", index=False)

    minimum = results.sort_values("source_html_bytes", key=lambda values: values.astype(int)).iloc[0]
    maximum = results.sort_values("source_html_bytes", key=lambda values: values.astype(int), ascending=False).iloc[0]
    used = {minimum["company_id"], maximum["company_id"]}
    word_minimum = results.loc[~results["company_id"].isin(used)].sort_values(
        "analysis_word_count", key=lambda values: values.astype(int)
    ).iloc[0]
    used.add(word_minimum["company_id"])
    word_maximum = results.loc[~results["company_id"].isin(used)].sort_values(
        "analysis_word_count", key=lambda values: values.astype(int), ascending=False
    ).iloc[0]
    used.add(word_maximum["company_id"])
    remaining = results.loc[~results["company_id"].isin(used)].sort_values("company_id")
    random_row = remaining.iloc[random.Random(20250729).randrange(len(remaining))]
    selections = [
        (minimum, "minimum_html_size"), (maximum, "maximum_html_size"),
        (word_minimum, "minimum_analysis_word_count"),
        (word_maximum, "maximum_analysis_word_count"),
        (random_row, "fixed_seed_random_20250729"),
    ]
    existing_manual_path = quality_dir / "manual_review_5_companies.csv"
    existing_manual = {}
    if existing_manual_path.exists():
        existing_frame = pd.read_csv(existing_manual_path, dtype=str, keep_default_na=False)
        existing_manual = {
            (row["company_id"], row["selection_reason"]): row
            for row in existing_frame.to_dict("records")
            if row.get("review_result", "") != "pending_manual_review"
        }
    manual_rows = []
    for selected, reason in selections:
        structure = (root / selected["structure_preserved_text_file"]).read_text(encoding="utf-8")
        analysis = (root / selected["analysis_text_file"]).read_text(encoding="utf-8")
        generated = {
            "company_id": selected["company_id"], "ticker": selected["ticker"],
            "company_name": selected["company_name"] or selected["ticker"],
            "selection_reason": reason,
            "reviewed_location": "document_start;item_1a_start;item_7_start;item_8_start;document_end",
            "source_excerpt": excerpt(structure), "extracted_excerpt": excerpt(analysis),
            "obvious_missing_text": "", "obvious_duplicate_text": "",
            "navigation_contamination": "", "table_contamination": "",
            "section_detection_problem": "", "review_result": "pending_manual_review",
            "reviewer_note": "",
        }
        decisions = {
            "P2025-039": {
                "obvious_missing_text": "yes", "obvious_duplicate_text": "no",
                "navigation_contamination": "no", "table_contamination": "no",
                "section_detection_problem": "yes",
                "review_result": "warning",
                "reviewer_note": "Narrative is unusually short and Items 1A, 7, and 8 were not detected; table-based layout likely removed material narrative and requires parser follow-up.",
            },
            "P2025-096": {
                "obvious_missing_text": "no", "obvious_duplicate_text": "no",
                "navigation_contamination": "no", "table_contamination": "no",
                "section_detection_problem": "yes",
                "review_result": "warning",
                "reviewer_note": "Large multi-registrant filing retained substantial text, but Item 7 was not detected while Items 1A and 8 were detected.",
            },
            "P2025-011": {
                "obvious_missing_text": "no", "obvious_duplicate_text": "no",
                "navigation_contamination": "no", "table_contamination": "no",
                "section_detection_problem": "no",
                "review_result": "pass",
                "reviewer_note": "Start, Item 1A, Item 7, Item 8, and end excerpts showed coherent narrative with no obvious table contamination.",
            },
            "P2025-098": {
                "obvious_missing_text": "no", "obvious_duplicate_text": "no",
                "navigation_contamination": "no", "table_contamination": "no",
                "section_detection_problem": "yes",
                "review_result": "warning",
                "reviewer_note": "Multi-registrant filing retained extensive text, but detected Item 7 is a short cross-reference rather than the full MD&A boundary.",
            },
            "P2025-058": {
                "obvious_missing_text": "no", "obvious_duplicate_text": "no",
                "navigation_contamination": "no", "table_contamination": "no",
                "section_detection_problem": "no",
                "review_result": "pass",
                "reviewer_note": "Start, Item 1A, Item 7, Item 8, and end excerpts were coherent and tables were absent from analysis text.",
            },
        }
        generated.update(decisions.get(selected["company_id"], {}))
        if generated["review_result"] == "warning":
            warning_rows.append({
                "company_id": selected["company_id"], "cik": selected["cik"],
                "ticker": selected["ticker"], "accession_number": selected["accession_number"],
                "case_status": "manual_review_warning",
                "warning_or_failure_reason": "manual_review:" + generated["reviewer_note"],
                "recommended_action": "improve section/layout handling before language-variable production",
            })
        manual_rows.append(existing_manual.get(
            (selected["company_id"], reason), generated
        ))
    pd.DataFrame(manual_rows).to_csv(
        quality_dir / "manual_review_5_companies.csv", index=False
    )
    pd.DataFrame(warning_rows, columns=[
        "company_id", "cik", "ticker", "accession_number", "case_status",
        "warning_or_failure_reason", "recommended_action",
    ]).to_csv(quality_dir / "failed_or_warning_cases.csv", index=False)

    paragraph_rows, paragraph_ids, paragraph_companies = csv_unique_counts(
        output / "analysis_tables/paragraphs.csv.gz", "paragraph_id", "company_id"
    )
    sentence_rows, sentence_ids, sentence_companies = csv_unique_counts(
        output / "analysis_tables/sentences.csv.gz", "sentence_id", "company_id"
    )
    summary = {
        "input_html": len(manifest), "input_sha_matches": len(manifest),
        "company_results": len(results), "analysis_text_files": int(
            results["analysis_text_file"].map(lambda path: (root / path).is_file()).sum()
        ),
        "structure_preserved_text_files": int(
            results["structure_preserved_text_file"].map(lambda path: (root / path).is_file()).sum()
        ),
        "table_text_files": int(
            results["table_text_file"].map(lambda path: (root / path).is_file()).sum()
        ),
        "empty_analysis_text_files": int(quality["word_count"].eq(0).sum()),
        "output_sha_matches": int(
            results.apply(lambda row: sha256(root / row["analysis_text_file"]) == row["analysis_text_sha256"], axis=1).sum()
        ),
        "paragraph_rows": paragraph_rows, "unique_paragraph_ids": paragraph_ids,
        "paragraph_companies": paragraph_companies, "sentence_rows": sentence_rows,
        "unique_sentence_ids": sentence_ids, "sentence_companies": sentence_companies,
        "html_tag_residual_errors": int(quality["html_tag_residual_count"].gt(0).sum()),
        "script_style_residual_errors": int(
            (quality["javascript_residual_count"].gt(0) | quality["css_residual_count"].gt(0)).sum()
        ),
        "xbrl_residual_errors": int(quality["xbrl_namespace_residual_count"].gt(0).sum()),
        "structural_input_errors": 0,
        "failed_after_3_attempts": int(results["extraction_status"].eq("failed_after_3_attempts").sum()),
        "quality_warning_companies": int(quality["quality_status"].eq("warning").sum()),
    }
    run_summary_path = output / "extraction_results/extraction_run_summary.csv"
    prior_run = {}
    if run_summary_path.exists():
        prior_frame = pd.read_csv(run_summary_path, dtype=str, keep_default_na=False)
        if len(prior_frame) == 1:
            prior_run = prior_frame.iloc[0].to_dict()
    pd.DataFrame([{**prior_run, **summary}]).to_csv(run_summary_path, index=False)
    print(json.dumps(summary, sort_keys=True))
    fatal_keys = [
        "empty_analysis_text_files", "html_tag_residual_errors",
        "script_style_residual_errors", "xbrl_residual_errors",
        "structural_input_errors", "failed_after_3_attempts",
    ]
    if any(summary[key] for key in fatal_keys):
        raise SystemExit(1)
    if paragraph_rows != paragraph_ids or sentence_rows != sentence_ids:
        raise SystemExit("duplicate paragraph or sentence ID")
    if paragraph_companies != 100 or sentence_companies != 100:
        raise SystemExit("paragraph or sentence company linkage failure")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    check(args.root.resolve())
