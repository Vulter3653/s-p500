#!/usr/bin/env python3
"""Batch-extract analysis-ready text from the 100 downloaded pilot filings."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

try:
    from parse_sec_10k_html import PARSER_VERSION, SECTIONS, parse_html, sentence_split
except ModuleNotFoundError:
    from scripts.parse_sec_10k_html import PARSER_VERSION, SECTIONS, parse_html, sentence_split

INPUT = Path("2025/pilot_100/html/manifest/html_manifest.csv")
OUTPUT = Path("2025/pilot_100/text")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_input(root: Path, manifest: pd.DataFrame) -> None:
    required = {
        "final_sample_id", "cik", "symbol", "accession_number",
        "primary_document", "html_path", "sha256", "file_size",
        "download_status",
    }
    if not required.issubset(manifest.columns):
        raise ValueError(f"missing input columns: {sorted(required - set(manifest.columns))}")
    if not 1 <= len(manifest) <= 100:
        raise ValueError("HTML manifest must contain between 1 and 100 rows")
    if manifest["final_sample_id"].duplicated().any():
        raise ValueError("duplicate company ID")
    if manifest["cik"].duplicated().any():
        raise ValueError("duplicate CIK")
    if manifest["accession_number"].duplicated().any():
        raise ValueError("duplicate accession")
    if not manifest["download_status"].isin({"downloaded", "skipped_sha_match"}).all():
        raise ValueError("input contains unsuccessful download status")
    for row in manifest.to_dict("records"):
        path = root / row["html_path"]
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing or empty HTML: {row['accession_number']}")
        if sha256(path) != row["sha256"]:
            raise ValueError(f"HTML SHA mismatch: {row['accession_number']}")


def file_paths(root: Path, row: dict, output_relative: Path = OUTPUT) -> dict[str, Path]:
    company = root / output_relative / "company_text" / row["cik"]
    accession = row["accession_number"]
    section = root / output_relative / "section_text" / row["cik"] / accession
    return {
        "analysis": company / f"{accession}_analysis_text.txt",
        "structure": company / f"{accession}_structure_preserved_text.txt",
        "table": company / f"{accession}_table_text.txt",
        "section": section,
    }


def can_skip(
    root: Path,
    row: dict,
    prior: dict[str, dict],
    output_relative: Path = OUTPUT,
) -> bool:
    previous = prior.get(row["accession_number"])
    if not previous:
        return False
    paths = file_paths(root, row, output_relative)
    return (
        previous.get("source_html_sha256") == row["sha256"]
        and previous.get("parser_version") == PARSER_VERSION
        and previous.get("extraction_status") in {"success", "warning"}
        and paths["analysis"].is_file()
        and previous.get("analysis_text_sha256") == sha256(paths["analysis"])
    )


def parse_with_retries(payload: bytes, parser=parse_html, maximum_attempts: int = 3):
    error = ""
    for attempt in range(1, maximum_attempts + 1):
        try:
            parsed = parser(payload)
            narrative = [block for block in parsed["blocks"] if not block.is_table]
            if not narrative or sum(len(block.text.split()) for block in narrative) < 100:
                raise ValueError("analysis output is empty or implausibly short")
            return parsed, attempt, ""
        except Exception as exception:
            error = f"{type(exception).__name__}: {exception}"
    return None, maximum_attempts, error


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n" if text.strip() else "", encoding="utf-8")


def extract(
    root: Path,
    *,
    input_relative: Path = INPUT,
    output_relative: Path = OUTPUT,
    retry_warning: bool = False,
    retry_failed: bool = False,
) -> dict:
    manifest = pd.read_csv(root / input_relative, dtype=str, keep_default_na=False)
    validate_input(root, manifest)
    output = root / output_relative
    tables_dir = output / "analysis_tables"
    results_dir = output / "extraction_results"
    logs_dir = output / "processing_logs"
    for directory in (tables_dir, results_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    results_path = results_dir / "company_text_extraction_results.csv"
    prior_frame = (
        pd.read_csv(results_path, dtype=str, keep_default_na=False)
        if results_path.exists() else pd.DataFrame()
    )
    prior = (
        {row["accession_number"]: row for row in prior_frame.to_dict("records")}
        if not prior_frame.empty else {}
    )
    all_skipped = bool(prior) and all(
        can_skip(root, row, prior, output_relative)
        for row in manifest.to_dict("records")
    )
    if all_skipped and not retry_warning and not retry_failed:
        summary = {
            "input_html": len(manifest), "processed": 0, "skipped": len(manifest),
            "warning": int(prior_frame["warning_count"].astype(int).gt(0).sum()),
            "failed": 0, "parser_version": PARSER_VERSION, "completed_at": now(),
        }
        pd.DataFrame([summary]).to_csv(results_dir / "extraction_run_summary.csv", index=False)
        return summary
    paragraphs_path = tables_dir / "paragraphs.csv.gz"
    sentences_path = tables_dir / "sentences.csv.gz"
    sections_path = tables_dir / "sections.csv"

    paragraph_columns = [
        "company_id", "final_sample_id", "cik", "ticker", "accession_number",
        "paragraph_id", "paragraph_order", "section_code", "section_name",
        "source_html_element", "is_section_heading", "is_table_text",
        "included_in_analysis_text", "paragraph_text", "character_count",
        "word_count", "extraction_status",
    ]
    sentence_columns = [
        "company_id", "final_sample_id", "cik", "ticker", "accession_number",
        "sentence_id", "sentence_order", "paragraph_id", "section_code",
        "section_name", "is_table_text", "included_in_analysis_text",
        "sentence_text", "character_count", "word_count", "sentence_split_status",
    ]
    section_columns = [
        "company_id", "final_sample_id", "cik", "ticker", "accession_number",
        "section_code", "section_name", "section_order", "heading_text",
        "extraction_status", "first_paragraph_order", "last_paragraph_order",
        "paragraph_count", "sentence_count", "word_count", "character_count",
        "analysis_text_file", "warning_message",
    ]
    result_columns = [
        "company_id", "cik", "ticker", "company_name", "accession_number",
        "source_html_file", "source_html_sha256", "analysis_text_file",
        "analysis_text_sha256", "structure_preserved_text_file", "table_text_file",
        "source_html_bytes", "analysis_text_bytes", "structure_preserved_text_bytes",
        "table_text_bytes", "analysis_word_count", "analysis_paragraph_count",
        "analysis_sentence_count", "detected_section_count", "detected_table_count",
        "duplicate_blocks_removed", "processing_attempts", "extraction_status",
        "warning_count", "parser_version", "processed_at",
    ]
    company_results = []
    section_rows = []
    counts = {"processed": 0, "skipped": 0, "warning": 0, "failed": 0}

    with (
        gzip.open(paragraphs_path, "wt", newline="", encoding="utf-8") as paragraph_file,
        gzip.open(sentences_path, "wt", newline="", encoding="utf-8") as sentence_file,
    ):
        paragraph_writer = csv.DictWriter(paragraph_file, fieldnames=paragraph_columns)
        sentence_writer = csv.DictWriter(sentence_file, fieldnames=sentence_columns)
        paragraph_writer.writeheader()
        sentence_writer.writeheader()

        for row in manifest.to_dict("records"):
            paths = file_paths(root, row, output_relative)
            previous = prior.get(row["accession_number"], {})
            skip = can_skip(root, row, prior, output_relative)
            if retry_warning and int(previous.get("warning_count", "0") or 0) > 0:
                skip = False
            if skip:
                counts["skipped"] += 1
            attempts = 0
            parsed = None
            error = ""
            if not skip:
                parsed, attempts, error = parse_with_retries(
                    (root / row["html_path"]).read_bytes()
                )
                if parsed is None:
                    counts["failed"] += 1
                    company_results.append({
                        **{column: "" for column in result_columns},
                        "company_id": row["final_sample_id"], "cik": row["cik"],
                        "ticker": row["symbol"], "accession_number": row["accession_number"],
                        "source_html_file": row["html_path"],
                        "source_html_sha256": row["sha256"],
                        "processing_attempts": attempts,
                        "extraction_status": "failed_after_3_attempts",
                        "parser_version": PARSER_VERSION, "processed_at": now(),
                    })
                    with (logs_dir / "text_extraction_log.jsonl").open("a", encoding="utf-8") as log:
                        log.write(json.dumps({
                            "company_id": row["final_sample_id"],
                            "accession_number": row["accession_number"],
                            "processed_at": now(), "status": "failed_after_3_attempts",
                            "attempts": attempts, "error": error,
                        }) + "\n")
                    continue
                counts["processed"] += 1
            else:
                parsed = parse_html((root / row["html_path"]).read_bytes())

            blocks = parsed["blocks"]
            analysis_blocks = [block for block in blocks if not block.is_table]
            structure_lines = [
                (
                    f"[TABLE {block.table_number:03d} REMOVED FROM ANALYSIS TEXT]"
                    if block.is_table else block.text
                )
                for block in blocks
            ]
            table_lines = []
            for number, text in enumerate(parsed["table_texts"], 1):
                table_lines.extend([f"[TABLE {number:03d}]", text, f"[END TABLE {number:03d}]", ""])
            write_text(paths["analysis"], "\n\n".join(block.text for block in analysis_blocks))
            write_text(paths["structure"], "\n\n".join(structure_lines))
            write_text(paths["table"], "\n".join(table_lines))

            sentence_total = 0
            analysis_paragraphs = 0
            section_sentence_counts: dict[str, int] = {}
            section_paragraph_counts: dict[str, int] = {}
            section_word_counts: dict[str, int] = {}
            section_character_counts: dict[str, int] = {}
            section_first: dict[str, int] = {}
            section_last: dict[str, int] = {}
            for block in blocks:
                paragraph_id = f"{row['final_sample_id']}-P{block.order:06d}"
                included = int(not block.is_table)
                paragraph_writer.writerow({
                    "company_id": row["final_sample_id"], "final_sample_id": row["final_sample_id"],
                    "cik": row["cik"], "ticker": row["symbol"],
                    "accession_number": row["accession_number"], "paragraph_id": paragraph_id,
                    "paragraph_order": block.order, "section_code": block.section_code,
                    "section_name": block.section_name, "source_html_element": block.source_element,
                    "is_section_heading": int(block.is_heading), "is_table_text": int(block.is_table),
                    "included_in_analysis_text": included, "paragraph_text": block.text,
                    "character_count": len(block.text), "word_count": len(block.text.split()),
                    "extraction_status": "success",
                })
                if included:
                    analysis_paragraphs += 1
                sentences = sentence_split(block.text)
                for sentence in sentences:
                    sentence_total += 1
                    sentence_writer.writerow({
                        "company_id": row["final_sample_id"], "final_sample_id": row["final_sample_id"],
                        "cik": row["cik"], "ticker": row["symbol"],
                        "accession_number": row["accession_number"],
                        "sentence_id": f"{row['final_sample_id']}-S{sentence_total:07d}",
                        "sentence_order": sentence_total, "paragraph_id": paragraph_id,
                        "section_code": block.section_code, "section_name": block.section_name,
                        "is_table_text": int(block.is_table),
                        "included_in_analysis_text": included, "sentence_text": sentence,
                        "character_count": len(sentence), "word_count": len(sentence.split()),
                        "sentence_split_status": "rule_based_protected_abbreviations",
                    })
                code = block.section_code
                section_sentence_counts[code] = section_sentence_counts.get(code, 0) + len(sentences)
                section_paragraph_counts[code] = section_paragraph_counts.get(code, 0) + 1
                section_word_counts[code] = section_word_counts.get(code, 0) + len(block.text.split())
                section_character_counts[code] = section_character_counts.get(code, 0) + len(block.text)
                section_first.setdefault(code, block.order)
                section_last[code] = block.order

            warnings = []
            detected_count = 0
            for section_order, (code, name, filename) in enumerate(SECTIONS, 1):
                detection = parsed["sections"][code]
                status = detection["status"]
                if status == "detected":
                    detected_count += 1
                    section_blocks = [
                        block for block in blocks
                        if block.section_code == code and not block.is_table
                    ]
                    write_text(paths["section"] / filename, "\n\n".join(b.text for b in section_blocks))
                else:
                    write_text(paths["section"] / filename, "")
                warning = detection.get("warning", "")
                if warning and code in {"item_1", "item_1a", "item_7", "item_8"}:
                    warnings.append(f"{code}:{warning}")
                section_rows.append({
                    "company_id": row["final_sample_id"], "final_sample_id": row["final_sample_id"],
                    "cik": row["cik"], "ticker": row["symbol"],
                    "accession_number": row["accession_number"], "section_code": code,
                    "section_name": name, "section_order": section_order,
                    "heading_text": detection.get("heading_text", ""),
                    "extraction_status": status,
                    "first_paragraph_order": section_first.get(code, ""),
                    "last_paragraph_order": section_last.get(code, ""),
                    "paragraph_count": section_paragraph_counts.get(code, 0),
                    "sentence_count": section_sentence_counts.get(code, 0),
                    "word_count": section_word_counts.get(code, 0),
                    "character_count": section_character_counts.get(code, 0),
                    "analysis_text_file": (paths["section"] / filename).relative_to(root).as_posix(),
                    "warning_message": warning,
                })
            unclassified = [block for block in blocks if block.section_code == "unclassified" and not block.is_table]
            write_text(paths["section"] / "unclassified_text.txt", "\n\n".join(b.text for b in unclassified))
            if parsed["sections"]["item_7"]["status"] != "detected":
                warnings.append("item_7:not_detected")
            status = "success" if not warnings else "warning"
            if warnings:
                counts["warning"] += 1
            company_name = row.get("security", row.get("company_name", ""))
            result = {
                "company_id": row["final_sample_id"], "cik": row["cik"],
                "ticker": row["symbol"], "company_name": company_name,
                "accession_number": row["accession_number"], "source_html_file": row["html_path"],
                "source_html_sha256": row["sha256"],
                "analysis_text_file": paths["analysis"].relative_to(root).as_posix(),
                "analysis_text_sha256": sha256(paths["analysis"]),
                "structure_preserved_text_file": paths["structure"].relative_to(root).as_posix(),
                "table_text_file": paths["table"].relative_to(root).as_posix(),
                "source_html_bytes": (root / row["html_path"]).stat().st_size,
                "analysis_text_bytes": paths["analysis"].stat().st_size,
                "structure_preserved_text_bytes": paths["structure"].stat().st_size,
                "table_text_bytes": paths["table"].stat().st_size,
                "analysis_word_count": sum(len(block.text.split()) for block in analysis_blocks),
                "analysis_paragraph_count": analysis_paragraphs,
                "analysis_sentence_count": sum(
                    len(sentence_split(block.text)) for block in analysis_blocks
                ),
                "detected_section_count": detected_count,
                "detected_table_count": len(parsed["table_texts"]),
                "duplicate_blocks_removed": parsed["duplicate_blocks_removed"],
                "processing_attempts": attempts if attempts else previous.get("processing_attempts", "1"),
                "extraction_status": status, "warning_count": len(warnings),
                "parser_version": PARSER_VERSION, "processed_at": now(),
            }
            company_results.append(result)
            with (logs_dir / "text_extraction_log.jsonl").open("a", encoding="utf-8") as log:
                log.write(json.dumps({
                    "company_id": row["final_sample_id"],
                    "accession_number": row["accession_number"], "processed_at": now(),
                    "status": "skipped" if skip else status,
                    "attempts": 0 if skip else attempts, "warning_count": len(warnings),
                }) + "\n")

    pd.DataFrame(section_rows, columns=section_columns).to_csv(sections_path, index=False)
    pd.DataFrame(company_results, columns=result_columns).to_csv(results_path, index=False)
    summary = {
        "input_html": len(manifest), "processed": counts["processed"],
        "skipped": counts["skipped"], "warning": counts["warning"],
        "failed": counts["failed"], "parser_version": PARSER_VERSION,
        "completed_at": now(),
    }
    pd.DataFrame([summary]).to_csv(results_dir / "extraction_run_summary.csv", index=False)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--input-relative", type=Path, default=INPUT)
    parser.add_argument("--output-relative", type=Path, default=OUTPUT)
    parser.add_argument("--retry-warning", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            extract(
                args.root.resolve(),
                input_relative=args.input_relative,
                output_relative=args.output_relative,
                retry_warning=args.retry_warning,
                retry_failed=args.retry_failed,
            ),
            sort_keys=True,
        )
    )
