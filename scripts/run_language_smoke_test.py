"""Run the reproducible five-company language-measurement smoke test."""

from __future__ import annotations

import csv
import gzip
import argparse
import json
import platform
import random
import statistics
import time
from datetime import datetime, timezone

from detect_ai_disclosure import measure_ai_disclosure
from extract_ai_related_sentences import extract_ai_sentences
from language_measurement_common import (
    AI_TERMS, LANGUAGE_MEASUREMENT_VERSION, RANDOM_SEED, ROOT, SMOKE_ROOT,
    ai_matches, display, read_csv, run_with_attempts, sha256_file, stable_row_sha,
    tokens, write_csv,
)
from measure_ai_related_sentiment import measure_sentiment
from measure_linguistic_concreteness import measure_concreteness
from measure_passive_voice import measure_passive
from measure_readability import measure_readability
from measure_report_level_controls import measure_report_controls
from measure_tense_usage import measure_tense
from measure_uncertainty_language import measure_uncertainty
from select_language_smoke_test_companies import OUTPUT as SELECTED_PATH, select_companies

SENTENCES = ROOT / "2025/pilot_100/text/analysis_tables/sentences.csv.gz"
PARAGRAPHS = ROOT / "2025/pilot_100/text/analysis_tables/paragraphs.csv.gz"
EXTRACTION = ROOT / "2025/pilot_100/text/extraction_results/company_text_extraction_results.csv"
SAMPLE = ROOT / "2025/pilot_100/sample/final_analysis_sample_100.csv"


def _empty(path, fields):
    write_csv(path, [], fields)


def _filtered_gzip(path, ids):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row["company_id"] in ids]


def _dependency_rows(selected, status_key, status):
    return [{"company_id": row["company_id"], "ticker": row["ticker"], status_key: status}
            for row in selected]


def _write_definitions(path):
    definitions = [
        ("ai_disclosure_binary", "AI 공시 여부", "AI disclosure", "whole report",
         "유효 AI 사전 용어가 1회 이상이면 1", "AI 용어 존재", "해당 없음", "binary",
         "pilot AI term dictionary", LANGUAGE_MEASUREMENT_VERSION, "입력 누락 시 missing",
         "해당 없음", "primary", "Cooper et al. (2022)", "measured", ""),
        ("ai_terms_per_1000_words", "10-K 본문 1,000단어당 AI 관련 용어 수", "AI disclosure",
         "whole report", "AI 용어 빈도의 보고서 길이 표준화", "AI 용어 수",
         "전체 분석 단어 수", "per 1,000 words", "pilot AI term dictionary",
         LANGUAGE_MEASUREMENT_VERSION, "분모 0이면 missing", "missing and logged", "primary",
         "Cooper et al. (2022)", "measured", ""),
        ("ai_sentence_ratio", "전체 문장 중 AI 관련 문장 비율", "AI disclosure", "whole report",
         "AI 용어가 직접 포함된 narrative 문장 비율", "AI 관련 문장 수", "전체 분석 문장 수",
         "ratio", "pilot AI term dictionary", LANGUAGE_MEASUREMENT_VERSION,
         "분모 0이면 missing", "missing and logged", "primary", "Cooper et al. (2022)",
         "measured", ""),
        ("ai_concreteness_mean", "AI 문장의 평균 어휘 구체성", "concreteness", "AI sentences",
         "사전 점수가 있는 alphabetic token 평균", "구체성 점수 합", "사전 매칭 token 수",
         "dictionary score", "Brysbaert lexical concreteness dictionary", "not installed",
         "사전 없으면 missing", "missing", "primary", "Brysbaert approach",
         "blocked_dictionary_missing", "가짜 점수를 생성하지 않음"),
        ("ai_future_tense_ratio", "AI 문장의 미래 시제 비율", "tense", "AI sentences",
         "dependency/POS로 확인한 미래 표지 구성 비율", "미래 표지 구성 수", "finite verb 수",
         "ratio", "dependency parser", "not installed", "모델 없으면 missing", "missing",
         "primary", "linguistic tense measurement", "blocked_model_missing", ""),
        ("ai_passive_sentence_ratio", "AI 문장의 수동태 문장 비율", "passive voice",
         "AI sentences", "dependency 근거가 있는 수동태 문장 비율", "수동태 문장 수",
         "AI 문장 수", "ratio", "dependency parser", "not installed", "모델 없으면 missing",
         "missing", "primary", "dependency-based passive detection", "blocked_model_missing", ""),
        ("ai_fog_index", "AI 관련 문장의 Gunning Fog Index", "readability", "AI sentences",
         "0.4 × (평균 문장 길이 + 3음절 이상 단어 비율×100)", "공식", "AI 문장",
         "index", "deterministic syllable heuristic", LANGUAGE_MEASUREMENT_VERSION,
         "AI 문장 0이면 missing", "missing and logged", "primary", "Gunning Fog",
         "measured", "고유명사와 약어 과대계상 가능"),
        ("ai_net_tone", "AI 관련 금융 순감성", "sentiment", "AI sentences",
         "(긍정-부정)/(긍정+부정)", "긍정-부정", "긍정+부정", "ratio",
         "Loughran-McDonald", "not installed", "사전 없으면 missing",
         "0 denominator이면 missing", "primary", "Loughran-McDonald",
         "blocked_dictionary_missing", ""),
        ("report_word_count", "전체 10-K 분석 단어 수", "report control", "whole report",
         "정제 본문의 token 수", "token 수", "해당 없음", "count", "repository tokenizer",
         LANGUAGE_MEASUREMENT_VERSION, "입력 누락 시 missing", "해당 없음", "primary",
         "Cooper et al. (2022)", "measured", ""),
        ("report_numeric_token_ratio", "전체 10-K 숫자 token 비율", "report control",
         "whole report", "숫자 token/전체 token", "숫자 token 수", "전체 token 수", "ratio",
         "repository tokenizer", LANGUAGE_MEASUREMENT_VERSION, "분모 0이면 missing",
         "missing and logged", "auxiliary", "pilot control", "measured", ""),
    ]
    fields = ["variable_name", "user_friendly_name", "construct", "analysis_scope", "definition",
              "numerator", "denominator", "unit", "dictionary_or_model", "version", "missing_rule",
              "zero_denominator_rule", "primary_or_auxiliary", "literature_basis", "pilot_status", "note"]
    write_csv(path, [dict(zip(fields, row)) for row in definitions], fields)


def run(force=False):
    started = time.monotonic()
    selected = select_companies()
    state_path = SMOKE_ROOT / "processing_logs/language_smoke_test_processing_state.csv"
    combined_path = SMOKE_ROOT / "combined_language_results/company_language_smoke_test_results.csv"
    prior_summary_path = SMOKE_ROOT / "processing_logs/language_smoke_test_run_summary.csv"
    if not force and state_path.is_file() and combined_path.is_file():
        state = read_csv(state_path)
        expected = {row["company_id"]: row["analysis_text_sha256"] for row in selected}
        valid = (
            len(state) == 5
            and {row["company_id"]: row["analysis_text_sha256"] for row in state} == expected
            and all(row["language_measurement_version"] == LANGUAGE_MEASUREMENT_VERSION for row in state)
            and prior_summary_path.is_file()
            and read_csv(prior_summary_path)[0]["combined_output_sha256"] == sha256_file(combined_path)
        )
        if valid:
            print("processed=0 skipped=5 warning=5 failed=0 blocked_dependency_constructs=5")
            return {"processed": 0, "skipped": 5, "warning": 5, "failed": 0}
    ids = {row["company_id"] for row in selected}
    sentence_rows = _filtered_gzip(SENTENCES, ids)
    paragraph_rows = _filtered_gzip(PARAGRAPHS, ids)
    extraction = {row["company_id"]: row for row in read_csv(EXTRACTION)}
    sample = {row["final_sample_id"]: row for row in read_csv(SAMPLE)}
    sentences_by_company = {company_id: [] for company_id in ids}
    paragraph_count = {company_id: 0 for company_id in ids}
    for row in sentence_rows:
        sentences_by_company[row["company_id"]].append(row)
    for row in paragraph_rows:
        if row["included_in_analysis_text"] == "1" and row["is_table_text"] == "0":
            paragraph_count[row["company_id"]] += 1

    ai_sentence_rows = []
    ai_match_rows = []
    company_rows = []
    readability_details = []
    denominator_zero = []
    warnings = []
    processing_state = []
    processed_at = datetime.now(timezone.utc).isoformat()

    def process_company(selected_row, _attempt):
        company_id = selected_row["company_id"]
        ext = extraction[company_id]
        analysis_path = ROOT / ext["analysis_text_file"]
        if sha256_file(analysis_path) != ext["analysis_text_sha256"]:
            raise ValueError("input SHA mismatch")
        text = analysis_path.read_text(encoding="utf-8")
        narrative = sentences_by_company[company_id]
        ai_rows = extract_ai_sentences(narrative)
        for row in ai_rows:
            row["company_name"] = selected_row["company_name"]
        ai_texts = [row["sentence_text"] for row in ai_rows]
        ai_disclosure = measure_ai_disclosure(text, len(narrative))
        ai_disclosure["ai_sentence_count"] = len(ai_rows)
        ai_disclosure["ai_sentence_ratio"] = (
            len(ai_rows) / len(narrative) if narrative else None
        )
        concrete = measure_concreteness(ai_texts)
        tense = measure_tense(ai_texts)
        uncertainty = measure_uncertainty(" ".join(ai_texts))
        passive = measure_passive(ai_texts)
        readable = measure_readability(ai_texts)
        sentiment = measure_sentiment(" ".join(ai_texts))
        table_text = (ROOT / ext["table_text_file"]).read_text(encoding="utf-8")
        controls = measure_report_controls(
            text, [row["sentence_text"] for row in narrative], paragraph_count[company_id],
            table_text, int(ext["source_html_bytes"]), int(ext["analysis_text_bytes"]),
        )
        identity = {
            "company_id": company_id, "cik": selected_row["cik"],
            "ticker": selected_row["ticker"], "company_name": selected_row["company_name"],
            "accession_number": selected_row["accession_number"], "report_year": "2025",
            "filing_date": sample[company_id]["filing_date"],
            "parser_version": selected_row["parser_version"],
            "language_measurement_version": LANGUAGE_MEASUREMENT_VERSION,
            "ai_detection_status": "success",
        }
        row = identity | ai_disclosure | concrete | tense | uncertainty | passive | readable | sentiment | controls
        return row, ai_rows

    attempts = {}
    for selected_row in selected:
        try:
            (row, rows), attempt = run_with_attempts(
                lambda number, item=selected_row: process_company(item, number), 3
            )
            attempts[row["company_id"]] = attempt
            company_rows.append(row)
            ai_sentence_rows.extend(rows)
        except Exception as error:
            raise RuntimeError(f"structural processing failure: {selected_row['company_id']}: {error}")

    for row in ai_sentence_rows:
        for match in ai_matches(row["sentence_text"]):
            ai_match_rows.append({
                "company_id": row["company_id"], "ticker": row["ticker"],
                "sentence_id": row["sentence_id"], **match,
            })
    for row in company_rows:
        if row["ai_sentence_count"] == 0:
            denominator_zero.append({
                "company_id": row["company_id"], "ticker": row["ticker"],
                "variable_group": "AI sentence measures", "zero_denominator": "ai_sentence_count",
                "handling": "missing; not replaced with zero",
            })
            warnings.append({
                "company_id": row["company_id"], "ticker": row["ticker"],
                "case_status": "warning", "construct": "AI disclosure",
                "warning_reason": "zero_ai_related_sentences", "recommended_action": "retain row and review dictionary coverage",
            })
        if row["ai_sentence_count"] == 1:
            warnings.append({
                "company_id": row["company_id"], "ticker": row["ticker"],
                "case_status": "warning", "construct": "AI disclosure",
                "warning_reason": "single_ai_related_sentence", "recommended_action": "manual review",
            })
        for construct, reason in (
            ("concreteness", "Brysbaert_dictionary_missing"),
            ("tense", "dependency_model_missing"),
            ("uncertainty", "Loughran_McDonald_dictionary_missing"),
            ("passive_voice", "dependency_model_missing"),
            ("sentiment", "Loughran_McDonald_dictionary_missing"),
        ):
            warnings.append({
                "company_id": row["company_id"], "ticker": row["ticker"],
                "case_status": "blocked_dependency", "construct": construct,
                "warning_reason": reason, "recommended_action": "install a source-documented dependency before full-sample expansion",
            })

    # Core outputs
    dictionary_rows = [
        {"term": term, "term_type": kind, "dictionary_version": LANGUAGE_MEASUREMENT_VERSION,
         "case_handling": "case-insensitive with alphabetic boundaries",
         "source": "user-specified pilot dictionary"}
        for term, kind in AI_TERMS
    ]
    write_csv(SMOKE_ROOT / "ai_disclosure_detection/ai_dictionary_terms.csv",
              dictionary_rows, list(dictionary_rows[0]))
    ai_company_fields = ["company_id", "cik", "ticker", "company_name", "accession_number",
                         "ai_disclosure_binary", "ai_term_count", "ai_sentence_count",
                         "ai_sentence_ratio", "ai_terms_per_1000_words",
                         "total_analysis_word_count", "total_analysis_sentence_count",
                         "ai_detection_status"]
    write_csv(SMOKE_ROOT / "ai_disclosure_detection/company_ai_disclosure_results.csv",
              company_rows, ai_company_fields)
    write_csv(SMOKE_ROOT / "ai_disclosure_detection/ai_term_match_details.csv.gz",
              ai_match_rows, ["company_id", "ticker", "sentence_id", "matched_term",
                              "dictionary_term", "match_type", "start_character", "end_character"])
    ai_sentence_fields = ["company_id", "cik", "ticker", "company_name", "accession_number",
                          "sentence_id", "paragraph_id", "section_code", "section_name",
                          "sentence_order", "sentence_text", "matched_ai_terms",
                          "matched_term_count", "ai_match_type", "included_in_measurement",
                          "exclusion_reason", "previous_sentence_text", "next_sentence_text"]
    write_csv(SMOKE_ROOT / "ai_related_sentences/ai_related_sentences.csv.gz",
              ai_sentence_rows, ai_sentence_fields)
    summaries = []
    for row in company_rows:
        summaries.append({"company_id": row["company_id"], "ticker": row["ticker"],
                          "ai_sentence_count": row["ai_sentence_count"],
                          "included_sentence_count": row["ai_sentence_count"],
                          "excluded_false_positive_count": 0,
                          "selection_rule": "direct valid dictionary match in narrative sentence"})
    write_csv(SMOKE_ROOT / "ai_related_sentences/ai_sentence_selection_summary.csv",
              summaries, list(summaries[0]))
    _empty(SMOKE_ROOT / "ai_related_sentences/excluded_false_positive_sentences.csv",
           ["company_id", "ticker", "sentence_id", "sentence_text", "exclusion_reason"])

    concept_specs = [
        ("linguistic_concreteness/company_concreteness_results.csv",
         ["company_id", "ticker", "ai_concreteness_mean", "ai_concreteness_median",
          "ai_concreteness_coverage", "ai_concrete_word_ratio",
          "ai_matched_concreteness_word_count", "ai_total_eligible_word_count", "concreteness_status"]),
        ("tense_measurement/company_tense_results.csv",
         ["company_id", "ticker", "ai_past_tense_count", "ai_present_tense_count",
          "ai_future_tense_count", "ai_total_finite_verb_count", "ai_past_tense_ratio",
          "ai_present_tense_ratio", "ai_future_tense_ratio", "ai_past_minus_future",
          "ai_future_orientation", "tense_status"]),
        ("uncertainty_language/company_uncertainty_results.csv",
         ["company_id", "ticker", "ai_uncertainty_count", "ai_uncertainty_ratio",
          "ai_weak_modal_count", "ai_weak_modal_ratio", "ai_strong_modal_count",
          "ai_strong_modal_ratio", "ai_constraining_count", "ai_constraining_ratio",
          "uncertainty_status"]),
        ("passive_voice/company_passive_voice_results.csv",
         ["company_id", "ticker", "ai_passive_sentence_count", "ai_passive_sentence_ratio",
          "ai_passive_verb_count", "ai_passive_verb_ratio", "passive_voice_status"]),
        ("readability_measurement/company_readability_results.csv",
         ["company_id", "ticker", "ai_fog_index", "ai_mean_sentence_length",
          "ai_complex_word_ratio", "ai_word_count", "ai_sentence_count_for_readability",
          "ai_complex_word_count", "readability_status"]),
        ("ai_related_sentiment/company_ai_sentiment_results.csv",
         ["company_id", "ticker", "ai_positive_count", "ai_negative_count", "ai_positive_ratio",
          "ai_negative_ratio", "ai_net_tone", "ai_sentiment_word_coverage",
          "ai_net_tone_by_words", "sentiment_status"]),
    ]
    for relative, fields in concept_specs:
        write_csv(SMOKE_ROOT / relative, company_rows, fields)
    for relative, fields in (
        ("linguistic_concreteness/word_concreteness_match_details.csv.gz",
         ["company_id", "sentence_id", "token", "score", "dictionary_status"]),
        ("tense_measurement/sentence_tense_details.csv.gz",
         ["company_id", "sentence_id", "past_count", "present_count", "future_count", "parser_status"]),
        ("uncertainty_language/uncertainty_word_match_details.csv.gz",
         ["company_id", "sentence_id", "token", "category", "dictionary_status"]),
        ("passive_voice/passive_sentence_details.csv.gz",
         ["company_id", "sentence_id", "passive_detected", "passive_rule", "passive_token",
          "auxiliary_token", "dependency_evidence", "parser_status"]),
        ("ai_related_sentiment/sentiment_word_match_details.csv.gz",
         ["company_id", "sentence_id", "token", "sentiment", "dictionary_status"]),
    ):
        _empty(SMOKE_ROOT / relative, fields)
    for sentence in ai_sentence_rows:
        metrics = measure_readability([sentence["sentence_text"]])
        readability_details.append({
            "company_id": sentence["company_id"], "sentence_id": sentence["sentence_id"],
            "sentence_text": sentence["sentence_text"], **metrics,
        })
    write_csv(SMOKE_ROOT / "readability_measurement/sentence_readability_details.csv.gz",
              readability_details, ["company_id", "sentence_id", "sentence_text", "ai_fog_index",
                                    "ai_mean_sentence_length", "ai_complex_word_ratio", "ai_word_count",
                                    "ai_sentence_count_for_readability", "ai_complex_word_count",
                                    "readability_status"])

    control_fields = ["company_id", "cik", "ticker", "company_name", "accession_number"] + [
        key for key in company_rows[0] if key.startswith("report_") or key in
        {"source_html_bytes", "analysis_text_bytes", "analysis_text_to_html_ratio"}
    ]
    write_csv(SMOKE_ROOT / "report_level_control_variables/company_report_control_variables.csv",
              company_rows, control_fields)
    control_defs = [
        {"variable_name": key, "definition": key.replace("_", " "),
         "status": "blocked_dictionary_missing" if company_rows[0].get(key) is None else "measured",
         "scope": "whole analysis text"}
        for key in control_fields[5:]
    ]
    write_csv(SMOKE_ROOT / "report_level_control_variables/control_variable_definitions.csv",
              control_defs, list(control_defs[0]))
    backlog = []
    for name, description, source in (
        ("firm_size", "기업 규모", "SEC XBRL or financial database"),
        ("total_assets", "총자산", "SEC XBRL"),
        ("sales", "매출", "SEC XBRL"), ("profitability", "수익성", "SEC XBRL"),
        ("leverage", "레버리지", "SEC XBRL"), ("r_and_d_intensity", "R&D 집약도", "SEC XBRL"),
        ("firm_age", "기업 연령", "SEC metadata"), ("market_to_book", "시장가치/장부가치", "market database"),
        ("industry", "산업", "existing sample"), ("stock_volatility", "주가 변동성", "market database"),
    ):
        backlog.append({"variable_name": name, "variable_description": description,
                        "literature_reason": "candidate control; literature confirmation required",
                        "text_or_external_data": "external_data", "current_availability": "not_collected",
                        "expected_data_source": source, "collection_stage": "after smoke test",
                        "priority": "to_be_assessed", "note": "no external collection in Step 4A"})
    write_csv(SMOKE_ROOT / "report_level_control_variables/control_variable_collection_backlog.csv",
              backlog, list(backlog[0]))

    combined_fields = list(company_rows[0])
    write_csv(SMOKE_ROOT / "combined_language_results/company_language_smoke_test_results.csv",
              [{key: display(value) for key, value in row.items()} for row in company_rows],
              combined_fields)
    _write_definitions(SMOKE_ROOT / "combined_language_results/variable_definitions.csv")

    # Review sample: first 3, last 2, and up to 5 deterministic random, without human verdicts.
    reviews = []
    for selected_row in selected:
        rows = [row for row in ai_sentence_rows if row["company_id"] == selected_row["company_id"]]
        chosen = rows[:3] + rows[-2:]
        remainder = [row for row in rows if row not in chosen]
        random.Random(RANDOM_SEED).shuffle(remainder)
        chosen += remainder[:5]
        seen = set()
        for row in chosen:
            if row["sentence_id"] in seen:
                continue
            seen.add(row["sentence_id"])
            reviews.append({
                "company_id": row["company_id"], "ticker": row["ticker"],
                "sentence_id": row["sentence_id"], "sentence_text": row["sentence_text"],
                "matched_ai_terms": row["matched_ai_terms"], "true_ai_reference": "",
                "false_positive": "", "ambiguous_reference": "",
                "review_result": "needs_manual_review", "reviewer_note": "",
            })
    write_csv(SMOKE_ROOT / "quality_check/manual_review_ai_sentences.csv", reviews,
              ["company_id", "ticker", "sentence_id", "sentence_text", "matched_ai_terms",
               "true_ai_reference", "false_positive", "ambiguous_reference", "review_result",
               "reviewer_note"])
    write_csv(SMOKE_ROOT / "quality_check/denominator_zero_cases.csv", denominator_zero,
              ["company_id", "ticker", "variable_group", "zero_denominator", "handling"])
    write_csv(SMOKE_ROOT / "quality_check/failed_or_warning_cases.csv", warnings,
              ["company_id", "ticker", "case_status", "construct", "warning_reason",
               "recommended_action"])
    quality_rows = []
    for row in company_rows:
        company_ai = [item for item in ai_sentence_rows if item["company_id"] == row["company_id"]]
        lengths = [len(tokens(item["sentence_text"])) for item in company_ai]
        quality_rows.append({
            "company_id": row["company_id"], "ticker": row["ticker"],
            "ai_term_count": row["ai_term_count"], "ai_sentence_count": row["ai_sentence_count"],
            "ai_sentence_ratio": display(row["ai_sentence_ratio"]),
            "ai_sentence_min_length": min(lengths) if lengths else "",
            "ai_sentence_max_length": max(lengths) if lengths else "",
            "duplicate_ai_sentence_count": len(company_ai) - len({item["sentence_text"] for item in company_ai}),
            "false_positive_candidate_count": 0, "concreteness_coverage": "",
            "finite_verb_count": "", "tense_ratio_sum": "", "uncertainty_match_count": "",
            "passive_sentence_count": "", "readability_sentence_count": row["ai_sentence_count_for_readability"],
            "fog_index": display(row["ai_fog_index"]), "positive_match_count": "",
            "negative_match_count": "", "denominator_zero": int(row["ai_sentence_count"] == 0),
            "missing_variable_count": sum(value is None for value in row.values()),
            "warning_count": sum(item["company_id"] == row["company_id"] for item in warnings),
        })
    write_csv(SMOKE_ROOT / "quality_check/language_measurement_quality_check.csv",
              quality_rows, list(quality_rows[0]))

    for row in company_rows:
        processing_state.append({
            "company_id": row["company_id"],
            "analysis_text_sha256": next(x["analysis_text_sha256"] for x in selected if x["company_id"] == row["company_id"]),
            "language_measurement_version": LANGUAGE_MEASUREMENT_VERSION,
            "dictionary_fingerprint": "pilot-ai-v0.1.0|brysbaert-missing|lm-missing",
            "nlp_model_version": "dependency-model-missing",
            "result_row_sha256": stable_row_sha(row), "processing_attempts": attempts[row["company_id"]],
            "processing_status": "warning_blocked_dependencies", "processed_at": processed_at,
        })
    write_csv(SMOKE_ROOT / "processing_logs/language_smoke_test_processing_state.csv",
              processing_state, list(processing_state[0]))
    log_path = SMOKE_ROOT / "processing_logs/language_smoke_test_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        for row in processing_state:
            handle.write(json.dumps({
                "company_id": row["company_id"], "event": "processed",
                "attempts": row["processing_attempts"], "status": row["processing_status"],
                "language_measurement_version": LANGUAGE_MEASUREMENT_VERSION,
                "timestamp": processed_at,
            }, ensure_ascii=False) + "\n")

    elapsed = time.monotonic() - started
    summary = [{
        "language_measurement_version": LANGUAGE_MEASUREMENT_VERSION, "random_seed": RANDOM_SEED,
        "selected_companies": len(selected), "processed": len(company_rows), "skipped": 0,
        "warning": len(company_rows), "failed": 0, "blocked_dependency_constructs": 5,
        "ai_disclosure_companies": sum(row["ai_disclosure_binary"] for row in company_rows),
        "ai_related_sentences": len(ai_sentence_rows), "manual_review_sentences": len(reviews),
        "elapsed_seconds": f"{elapsed:.6f}", "average_seconds_per_company": f"{elapsed/5:.6f}",
        "combined_output_sha256": sha256_file(combined_path), "processed_at": processed_at,
    }]
    write_csv(SMOKE_ROOT / "processing_logs/language_smoke_test_run_summary.csv",
              summary, list(summary[0]))

    repro = SMOKE_ROOT / "reproducibility"
    repro.mkdir(parents=True, exist_ok=True)
    (repro / "colab_reproduction_backlog.md").write_text(
        "# Colab reproduction backlog\n\n"
        "- Step 4A에서는 notebook을 만들거나 실행하지 않았다.\n"
        "- 전체 확장 전 Brysbaert 및 Loughran-McDonald 사전의 출처·라이선스·SHA를 확정한다.\n"
        "- dependency parser와 모델 버전을 고정한 뒤 설치 셀을 문서화한다.\n",
        encoding="utf-8",
    )
    write_csv(repro / "data_source_inventory.csv", [
        {"data_name": "selected analysis text", "path": "2025/pilot_100/text/company_text/",
         "expected_rows_or_files": 5, "actual_rows_or_files": 5, "sha_validation": "5/5"},
        {"data_name": "sentence corpus", "path": str(SENTENCES.relative_to(ROOT)),
         "expected_rows_or_files": "selected companies", "actual_rows_or_files": len(sentence_rows),
         "sha_validation": "repository input"},
    ], ["data_name", "path", "expected_rows_or_files", "actual_rows_or_files", "sha_validation"])
    write_csv(repro / "pipeline_execution_inventory.csv", [
        {"execution_order": 1, "script": "scripts/select_language_smoke_test_companies.py",
         "purpose": "select five companies", "seed": RANDOM_SEED},
        {"execution_order": 2, "script": "scripts/run_language_smoke_test.py",
         "purpose": "measure available variables and preserve blocked dependencies", "seed": RANDOM_SEED},
        {"execution_order": 3, "script": "scripts/check_language_smoke_test_quality.py",
         "purpose": "validate outputs", "seed": RANDOM_SEED},
    ], ["execution_order", "script", "purpose", "seed"])
    write_csv(repro / "software_and_dictionary_versions.csv", [
        {"component": "Python", "version": platform.python_version(), "sha256": "",
         "status": "available", "colab_install_note": "use compatible Python"},
        {"component": "pilot AI dictionary", "version": LANGUAGE_MEASUREMENT_VERSION,
         "sha256": sha256_file(SMOKE_ROOT / "ai_disclosure_detection/ai_dictionary_terms.csv"),
         "status": "available", "colab_install_note": "repository file"},
        {"component": "Brysbaert concreteness", "version": "", "sha256": "",
         "status": "blocked_dictionary_missing", "colab_install_note": "source and license required"},
        {"component": "Loughran-McDonald", "version": "", "sha256": "",
         "status": "blocked_dictionary_missing", "colab_install_note": "official dictionary required"},
        {"component": "dependency parser", "version": "", "sha256": "",
         "status": "blocked_model_missing", "colab_install_note": "pin package and English model"},
    ], ["component", "version", "sha256", "status", "colab_install_note"])
    output_inventory = []
    for path in sorted(SMOKE_ROOT.rglob("*")):
        if path.is_file() and path.name != "expected_outputs_inventory.csv":
            output_inventory.append({
                "output_file": str(path.relative_to(ROOT)), "actual_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
    write_csv(repro / "expected_outputs_inventory.csv", output_inventory,
              ["output_file", "actual_bytes", "sha256"])
    print(f"processed=5 skipped=0 warning=5 failed=0 blocked_dependency_constructs=5 elapsed={elapsed:.3f}s")
    return summary[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--retry-warning", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()
    run(force=arguments.force or arguments.retry_warning or arguments.retry_failed)
