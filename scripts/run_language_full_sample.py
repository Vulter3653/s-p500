#!/usr/bin/env python3
"""Apply the validated language pipeline to the 2025 pilot sample of 100 firms."""

from __future__ import annotations

import csv
import math
import statistics
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from extract_ai_related_sentences import extract_ai_sentences
from detect_ai_disclosure import measure_ai_disclosure
from language_measurement_common import (
    LANGUAGE_MEASUREMENT_VERSION,
    ROOT,
    display,
    read_csv,
    write_csv,
)
from measure_ai_related_sentiment import measure_sentiment
from measure_linguistic_concreteness import (
    MATCHING_STRATEGY_VERSION,
    PREPROCESSING_VERSION,
    TOKEN_RE,
    build_stem_index,
    normalize_token,
    porter_stem,
)
from measure_report_level_controls import measure_report_controls
from measure_uncertainty_language import measure_uncertainty


FULL_ROOT = ROOT / "2025/pilot_100/language_full_sample"
SAMPLE_PATH = ROOT / "2025/pilot_100/sample/final_analysis_sample_100.csv"
EXTRACTION_PATH = (
    ROOT
    / "2025/pilot_100/text/extraction_results/company_text_extraction_results.csv"
)
SENTENCE_PATH = ROOT / "2025/pilot_100/text/analysis_tables/sentences.csv.gz"
PARAGRAPH_PATH = ROOT / "2025/pilot_100/text/analysis_tables/paragraphs.csv.gz"
LM_PATH = (
    ROOT
    / "references/dictionaries/loughran_mcdonald_master_dictionary/"
    "analysis_ready_dictionary/financial_language_categories_1993_2025.csv"
)
BRYSBAERT_PATH = (
    ROOT
    / "references/dictionaries/brysbaert_concreteness/"
    "analysis_ready_dictionary/brysbaert_concreteness_analysis_ready.csv"
)
SMART_PATH = (
    ROOT
    / "references/dictionaries/brysbaert_concreteness/"
    "analysis_ready_dictionary/smart_stopwords_tidytext_0.3.1.txt"
)

LM_CATEGORIES = (
    "positive",
    "negative",
    "uncertainty",
    "litigious",
    "strong_modal",
    "weak_modal",
    "constraining",
)


def load_analysis_ready_lm() -> dict[str, dict]:
    dictionary = {}
    with LM_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            word = row["normalized_word"]
            active = {
                category: row[f"{category}_active"] == "1"
                for category in LM_CATEGORIES
            }
            dictionary[word] = {"active": active}
    return dictionary


def load_analysis_ready_concreteness() -> dict[str, dict]:
    dictionary = {}
    with BRYSBAERT_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            word = row["normalized_entry"]
            dictionary[word] = {
                "dictionary_entry": row["dictionary_entry"],
                "entry_type": row["entry_type"],
                "score": float(row["concreteness_score"]),
                "dictionary_row_number": int(row["dictionary_row_number"]),
            }
    return dictionary


def load_analysis_ready_smart() -> set[str]:
    return {
        line.strip()
        for line in SMART_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def measure_concreteness_summary(
    texts: list[str],
    dictionary: dict[str, dict],
    stopwords: set[str],
    stem_index: tuple[dict, set[str], dict],
    prefix: str,
) -> dict:
    unique_stems, collision_stems, _ = stem_index
    scores: list[float] = []
    matched_entries: set[str] = set()
    eligible_count = 0
    collision_count = 0

    for text in texts:
        for original in TOKEN_RE.findall(text):
            normalized = normalize_token(original)
            if normalized in stopwords:
                continue
            eligible_count += 1
            entry = dictionary.get(normalized)
            if entry is None or entry["entry_type"] != "single_word":
                stem = porter_stem(normalized)
                entry = unique_stems.get(stem)
                if entry is None and stem in collision_stems:
                    collision_count += 1
            if entry is not None:
                scores.append(entry["score"])
                matched_entries.add(entry["dictionary_entry"].lower())

    matched_count = len(scores)
    status = (
        "warning_denominator_zero"
        if eligible_count == 0
        else "warning_stem_collisions"
        if collision_count
        else "success"
    )
    return {
        f"{prefix}_concreteness_mean": statistics.fmean(scores) if scores else None,
        f"{prefix}_concreteness_median": statistics.median(scores) if scores else None,
        f"{prefix}_concreteness_standard_deviation": (
            statistics.pstdev(scores) if scores else None
        ),
        f"{prefix}_concreteness_min": min(scores) if scores else None,
        f"{prefix}_concreteness_max": max(scores) if scores else None,
        f"{prefix}_concreteness_matched_token_count": matched_count,
        f"{prefix}_concreteness_eligible_token_count": eligible_count,
        f"{prefix}_concreteness_unmatched_token_count": (
            eligible_count - matched_count
        ),
        f"{prefix}_concreteness_coverage": (
            matched_count / eligible_count if eligible_count else None
        ),
        f"{prefix}_concreteness_unique_dictionary_entries": len(matched_entries),
        f"{prefix}_concreteness_stem_collision_count": collision_count,
        f"{prefix}_concreteness_status": status,
    }


def load_corpus_rows(
    sample_ids: set[str],
) -> tuple[dict[str, list[dict]], dict[str, int]]:
    sentences_by_company = {company_id: [] for company_id in sample_ids}
    for row in read_csv(SENTENCE_PATH):
        if row["company_id"] in sample_ids:
            sentences_by_company[row["company_id"]].append(row)

    paragraph_counts = {company_id: 0 for company_id in sample_ids}
    for row in read_csv(PARAGRAPH_PATH):
        if (
            row["company_id"] in sample_ids
            and row["included_in_analysis_text"] == "1"
            and row["is_table_text"] == "0"
        ):
            paragraph_counts[row["company_id"]] += 1
    return sentences_by_company, paragraph_counts


def validate_inputs(
    sample_rows: list[dict], extraction_rows: list[dict]
) -> tuple[dict[str, dict], dict[str, dict]]:
    if len(sample_rows) != 100:
        raise ValueError(f"final sample must contain 100 rows, found {len(sample_rows)}")
    for field in ("final_sample_id", "cik", "accession_number"):
        values = [row[field] for row in sample_rows]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {field} in final sample")
    sample = {row["final_sample_id"]: row for row in sample_rows}
    extraction = {row["company_id"]: row for row in extraction_rows}
    if set(sample) != set(extraction):
        missing = sorted(set(sample) - set(extraction))
        extra = sorted(set(extraction) - set(sample))
        raise ValueError(f"sample/extraction ID mismatch: missing={missing}, extra={extra}")
    for company_id, sample_row in sample.items():
        ext = extraction[company_id]
        if (
            sample_row["cik"] != ext["cik"]
            or sample_row["accession_number"] != ext["accession_number"]
        ):
            raise ValueError(f"identity mismatch for {company_id}")
        for key in ("analysis_text_file", "table_text_file"):
            if not (ROOT / ext[key]).is_file():
                raise FileNotFoundError(f"missing {key} for {company_id}")
    return sample, extraction


def identity_row(sample_row: dict, ext: dict) -> dict:
    return {
        "company_id": sample_row["final_sample_id"],
        "cik": sample_row["cik"],
        "ticker": sample_row["symbol"],
        "company_name": sample_row["security"],
        "accession_number": sample_row["accession_number"],
        "report_year": sample_row["report_date"][:4],
        "filing_date": sample_row["filing_date"],
        "parser_version": ext["parser_version"],
        "language_measurement_version": LANGUAGE_MEASUREMENT_VERSION,
    }


def finite_values_only(rows: list[dict]) -> None:
    for row in rows:
        for key, value in row.items():
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(
                    f"non-finite value for {row.get('company_id')}:{key}"
                )


def run() -> dict:
    started = time.monotonic()
    sample_rows = read_csv(SAMPLE_PATH)
    extraction_rows = read_csv(EXTRACTION_PATH)
    sample, extraction = validate_inputs(sample_rows, extraction_rows)
    sample_ids = set(sample)
    sentences_by_company, paragraph_counts = load_corpus_rows(sample_ids)

    lm_dictionary = load_analysis_ready_lm()
    concreteness_dictionary = load_analysis_ready_concreteness()
    smart_stopwords = load_analysis_ready_smart()
    stem_index = build_stem_index(concreteness_dictionary)

    company_rows: list[dict] = []
    ai_sentence_rows: list[dict] = []
    ai_lm_rows: list[dict] = []
    report_lm_rows: list[dict] = []
    ai_concreteness_rows: list[dict] = []
    report_concreteness_rows: list[dict] = []
    warning_rows: list[dict] = []
    failed_rows: list[dict] = []

    for sample_row in sample_rows:
        company_id = sample_row["final_sample_id"]
        ext = extraction[company_id]
        identity = identity_row(sample_row, ext)
        try:
            text = (ROOT / ext["analysis_text_file"]).read_text(encoding="utf-8")
            table_text = (ROOT / ext["table_text_file"]).read_text(encoding="utf-8")
            sentence_rows = sentences_by_company[company_id]
            ai_rows = extract_ai_sentences(sentence_rows)
            for row in ai_rows:
                row["company_name"] = identity["company_name"]
            ai_sentence_rows.extend(ai_rows)
            ai_texts = [row["sentence_text"] for row in ai_rows]

            ai_detection = measure_ai_disclosure(text, len(sentence_rows))
            ai_detection.update(
                {
                    "ai_sentence_count": len(ai_rows),
                    "ai_sentence_ratio": (
                        len(ai_rows) / len(sentence_rows) if sentence_rows else None
                    ),
                    "ai_detection_status": "success",
                }
            )
            ai_uncertainty = measure_uncertainty(
                " ".join(ai_texts), lm_dictionary
            )
            ai_sentiment = measure_sentiment(" ".join(ai_texts), lm_dictionary)
            ai_lm = ai_uncertainty | ai_sentiment

            controls = measure_report_controls(
                text,
                [row["sentence_text"] for row in sentence_rows],
                paragraph_counts[company_id],
                table_text,
                int(ext["source_html_bytes"]),
                int(ext["analysis_text_bytes"]),
                lm_dictionary,
            )
            ai_concrete = measure_concreteness_summary(
                ai_texts,
                concreteness_dictionary,
                smart_stopwords,
                stem_index,
                "ai",
            )
            report_concrete = measure_concreteness_summary(
                [text],
                concreteness_dictionary,
                smart_stopwords,
                stem_index,
                "report",
            )
            row = (
                identity
                | ai_detection
                | ai_lm
                | ai_concrete
                | report_concrete
                | controls
            )
            row["concreteness_status"] = ai_concrete["ai_concreteness_status"]
            row["lm_ai_status"] = (
                "warning_denominator_zero"
                if len(ai_rows) == 0
                else "success"
            )
            row["lm_report_status"] = controls["report_control_status"]
            row["matching_strategy_version"] = MATCHING_STRATEGY_VERSION
            row["concreteness_preprocessing_version"] = PREPROCESSING_VERSION
            company_rows.append(row)

            ai_lm_rows.append(identity | ai_lm | {"lm_ai_status": row["lm_ai_status"]})
            report_lm_rows.append(
                identity
                | {
                    key: value
                    for key, value in controls.items()
                    if key.startswith("report_")
                    and any(
                        category in key
                        for category in (
                            *LM_CATEGORIES,
                            "net_tone",
                            "sentiment_word_coverage",
                            "total_lm_matched_word_count",
                            "total_eligible_word_count",
                        )
                    )
                }
                | {"lm_report_status": row["lm_report_status"]}
            )
            ai_concreteness_rows.append(identity | ai_concrete)
            report_concreteness_rows.append(identity | report_concrete)

            if not ai_rows:
                warning_rows.append(
                    identity
                    | {
                        "warning_type": "denominator_zero",
                        "warning_detail": "AI sentence count is zero; AI-level values are missing",
                    }
                )
            elif len(ai_rows) == 1:
                warning_rows.append(
                    identity
                    | {
                        "warning_type": "single_ai_sentence",
                        "warning_detail": "AI-level values retained from one direct AI sentence",
                    }
                )
            if (
                ai_concrete["ai_concreteness_stem_collision_count"] > 0
                or report_concrete[
                    "report_concreteness_stem_collision_count"
                ]
                > 0
            ):
                warning_rows.append(
                    identity
                    | {
                        "warning_type": "stem_collisions",
                        "warning_detail": (
                            "ambiguous Porter stems excluded without score averaging"
                        ),
                    }
                )
        except Exception as error:
            failed_rows.append(
                identity
                | {
                    "failure_status": "failed",
                    "failure_reason": str(error),
                }
            )

    finite_values_only(company_rows)

    ai_detection_fields = [
        "company_id",
        "cik",
        "ticker",
        "company_name",
        "accession_number",
        "report_year",
        "filing_date",
        "ai_disclosure_binary",
        "ai_term_count",
        "ai_terms_per_1000_words",
        "ai_sentence_count",
        "ai_sentence_ratio",
        "total_analysis_word_count",
        "total_analysis_sentence_count",
        "ai_detection_status",
    ]
    write_csv(
        FULL_ROOT / "ai_related_sentences/company_ai_disclosure_results.csv",
        company_rows,
        ai_detection_fields,
    )
    write_csv(
        FULL_ROOT / "ai_related_sentences/ai_related_sentences.csv.gz",
        ai_sentence_rows,
        [
            "company_id",
            "cik",
            "ticker",
            "company_name",
            "accession_number",
            "sentence_id",
            "paragraph_id",
            "section_code",
            "section_name",
            "sentence_order",
            "sentence_text",
            "matched_ai_terms",
            "matched_term_count",
            "ai_match_type",
            "included_in_measurement",
            "exclusion_reason",
            "previous_sentence_text",
            "next_sentence_text",
        ],
    )
    write_csv(
        FULL_ROOT / "loughran_mcdonald/company_ai_level_lm_results.csv",
        ai_lm_rows,
        list(ai_lm_rows[0]) if ai_lm_rows else [],
    )
    write_csv(
        FULL_ROOT / "loughran_mcdonald/company_report_level_lm_results.csv",
        report_lm_rows,
        list(report_lm_rows[0]) if report_lm_rows else [],
    )
    write_csv(
        FULL_ROOT
        / "textual_concreteness/company_ai_level_concreteness_results.csv",
        ai_concreteness_rows,
        list(ai_concreteness_rows[0]) if ai_concreteness_rows else [],
    )
    write_csv(
        FULL_ROOT
        / "textual_concreteness/company_report_level_concreteness_results.csv",
        report_concreteness_rows,
        list(report_concreteness_rows[0]) if report_concreteness_rows else [],
    )
    write_csv(
        FULL_ROOT
        / "combined_language_results/company_language_full_sample_results.csv",
        [
            {key: display(value) for key, value in row.items()}
            for row in company_rows
        ],
        list(company_rows[0]) if company_rows else [],
    )
    warning_fields = [
        "company_id",
        "cik",
        "ticker",
        "company_name",
        "accession_number",
        "report_year",
        "filing_date",
        "parser_version",
        "language_measurement_version",
        "warning_type",
        "warning_detail",
    ]
    write_csv(
        FULL_ROOT / "quality_check/failed_or_warning_cases.csv",
        warning_rows,
        warning_fields,
    )
    write_csv(
        FULL_ROOT / "quality_check/failed_companies.csv",
        failed_rows,
        [
            "company_id",
            "cik",
            "ticker",
            "company_name",
            "accession_number",
            "failure_status",
            "failure_reason",
        ],
    )

    ai_disclosure_count = sum(
        int(row["ai_disclosure_binary"]) for row in company_rows
    )
    denominator_zero_ids = {
        row["company_id"] for row in company_rows if row["ai_sentence_count"] == 0
    }
    single_sentence_ids = {
        row["company_id"] for row in company_rows if row["ai_sentence_count"] == 1
    }
    collision_ids = {
        row["company_id"]
        for row in company_rows
        if row["ai_concreteness_stem_collision_count"] > 0
        or row["report_concreteness_stem_collision_count"] > 0
    }
    elapsed = time.monotonic() - started
    summary = {
        "processed_companies": len(company_rows),
        "ai_disclosure_companies": ai_disclosure_count,
        "ai_non_disclosure_companies": len(company_rows) - ai_disclosure_count,
        "ai_related_sentences": len(ai_sentence_rows),
        "lm_completed_companies": len(ai_lm_rows),
        "concreteness_completed_companies": len(ai_concreteness_rows),
        "denominator_zero_companies": len(denominator_zero_ids),
        "single_ai_sentence_companies": len(single_sentence_ids),
        "stem_collision_warning_companies": len(collision_ids),
        "failed_companies": len(failed_rows),
        "elapsed_seconds": f"{elapsed:.3f}",
        "processed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    summary_lines = [
        "# 2025 pilot full-sample language measurement summary",
        "",
        *[
            f"- {key.replace('_', ' ')}: {value}"
            for key, value in summary.items()
        ],
        "",
        "The validated five-company pipeline was extended without changing the "
        "measurement rules. Existing HTML, extracted text, smoke-test outputs, "
        "and VERSION were not modified. LIWC time focusing, passive voice, human "
        "review, R2, and Colab remain outside this run.",
        "",
    ]
    (FULL_ROOT / "run_summary.md").write_text(
        "\n".join(summary_lines), encoding="utf-8"
    )

    print(
        " ".join(
            [
                f"processed={summary['processed_companies']}",
                f"ai_disclosure={summary['ai_disclosure_companies']}",
                f"ai_sentences={summary['ai_related_sentences']}",
                f"denominator_zero={summary['denominator_zero_companies']}",
                f"single_sentence={summary['single_ai_sentence_companies']}",
                f"collision_warning={summary['stem_collision_warning_companies']}",
                f"failed={summary['failed_companies']}",
                f"elapsed={summary['elapsed_seconds']}s",
            ]
        )
    )
    return summary


if __name__ == "__main__":
    run()
