#!/usr/bin/env python3
"""Merge new features without changing any existing panel cell."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path

import numpy as np
import pandas as pd


KEY = ["company_id", "report_year"]
ALIASES = {
    "ai_disclosure": "ai_disclosure_flag",
    "whole_report_concreteness": "report_concreteness_mean",
    "ai_concreteness": "ai_concreteness_mean",
    "fog_index": "report_fog_index",
    "lm_positive_share": "report_positive_ratio",
    "lm_negative_share": "report_negative_ratio",
    "lm_uncertainty_share": "report_uncertainty_ratio",
    "lm_litigious_share": "report_litigious_ratio",
    "lm_strong_modal_share": "report_strong_modal_ratio",
    "lm_weak_modal_share": "report_weak_modal_ratio",
    "lm_constraining_share": "report_constraining_ratio",
    "ai_lm_positive_share": "ai_positive_ratio",
    "ai_lm_negative_share": "ai_negative_ratio",
    "ai_lm_uncertainty_share": "ai_uncertainty_ratio",
    "ai_lm_litigious_share": "ai_litigious_ratio",
    "ai_lm_strong_modal_share": "ai_strong_modal_ratio",
    "ai_lm_weak_modal_share": "ai_weak_modal_ratio",
    "ai_lm_constraining_share": "ai_constraining_ratio",
    "numeric_token_share": "report_numeric_token_ratio",
}


NEW_DEFINITIONS = {
    "past_tense_count": ("보고서 과거 시제 동사 수", "whole report", "count"),
    "present_tense_count": ("보고서 현재 시제 동사 수", "whole report", "count"),
    "future_tense_count": ("보고서 미래 시제 표지 수", "whole report", "count"),
    "finite_verb_count": ("보고서 분류 가능 finite verb 수", "whole report", "count"),
    "past_tense_share": ("보고서 과거 시제 비율", "whole report", "proportion"),
    "present_tense_share": ("보고서 현재 시제 비율", "whole report", "proportion"),
    "future_tense_share": ("보고서 미래 시제 비율", "whole report", "proportion"),
    "passive_voice_sentence_count": ("보고서 수동태 문장 수", "whole report", "count"),
    "passive_voice_sentence_share": ("보고서 수동태 문장 비율", "whole report", "proportion"),
    "ai_past_tense_count": ("AI 직접 문장 과거 시제 동사 수", "AI direct sentences", "count"),
    "ai_present_tense_count": ("AI 직접 문장 현재 시제 동사 수", "AI direct sentences", "count"),
    "ai_future_tense_count": ("AI 직접 문장 미래 시제 표지 수", "AI direct sentences", "count"),
    "ai_past_tense_share": ("AI 직접 문장 과거 시제 비율", "AI direct sentences", "proportion"),
    "ai_present_tense_share": ("AI 직접 문장 현재 시제 비율", "AI direct sentences", "proportion"),
    "ai_future_tense_share": ("AI 직접 문장 미래 시제 비율", "AI direct sentences", "proportion"),
    "ai_passive_voice_sentence_count": ("AI 수동태 문장 수", "AI direct sentences", "count"),
    "ai_passive_voice_sentence_share": ("AI 수동태 문장 비율", "AI direct sentences", "proportion"),
    "ai_word_count": ("AI 직접 문장 단어 수", "AI direct sentences", "count"),
    "log_ai_word_count": ("AI 단어 수 log(1+x)", "derived control", "log count"),
    "ai_fog_index": ("AI 직접 문장 Fog Index", "AI direct sentences", "index"),
    "ai_average_sentence_length": ("AI 직접 문장 평균 길이", "AI direct sentences", "words"),
    "ai_complex_word_share": ("AI 직접 문장 복잡 단어 비율", "AI direct sentences", "proportion"),
    "report_character_count": ("보고서 문자 수", "whole report", "count"),
    "average_word_length": ("보고서 평균 단어 길이", "whole report", "characters"),
    "lexical_density": ("보고서 내용어 비율", "whole report", "proportion"),
    "root_type_token_ratio": ("보고서 root type-token ratio", "whole report", "index"),
    "percentage_expression_count": ("보고서 백분율 표현 수", "whole report", "count"),
    "currency_expression_count": ("보고서 통화 표현 수", "whole report", "count"),
}


def frame_hash(frame: pd.DataFrame) -> str:
    values = pd.util.hash_pandas_object(frame, index=True).values.tobytes()
    return hashlib.sha256(values).hexdigest()


def build(panel_path: Path, feature_paths: list[Path], output_dir: Path) -> pd.DataFrame:
    panel = pd.read_parquet(panel_path)
    original_columns = list(panel.columns)
    original_hash = frame_hash(panel[original_columns])
    features = pd.concat([pd.read_csv(path, dtype={"company_id": "string"})
                          for path in feature_paths], ignore_index=True)
    if features.duplicated(KEY).any():
        raise ValueError("duplicate feature company-year keys")
    if len(features) != len(panel):
        raise ValueError(f"feature rows {len(features)} != panel rows {len(panel)}")
    feature_identity = {"cik", "accession_number"}
    merge_features = features.drop(columns=list(feature_identity), errors="ignore")
    extended = panel.merge(merge_features, on=KEY, how="left", validate="one_to_one")
    if frame_hash(extended[original_columns]) != original_hash:
        raise ValueError("existing panel cells changed during merge")

    extended["log1p_ai_sentence_count"] = np.log1p(
        pd.to_numeric(extended["ai_sentence_count"], errors="coerce")
    )
    for alias, source in ALIASES.items():
        extended[alias] = extended[source]
    ai_zero = extended["ai_sentence_count"].eq(0)
    ai_noncount = [
        "ai_fog_index", "ai_average_sentence_length", "ai_complex_word_share",
        "ai_past_tense_share", "ai_present_tense_share", "ai_future_tense_share",
        "ai_passive_voice_sentence_share",
    ]
    for column in ai_noncount:
        if extended.loc[ai_zero, column].notna().any():
            raise ValueError(f"AI zero-sentence structural missing violated: {column}")

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "firm_year_language_extended.csv"
    parquet_path = output_dir / "firm_year_language_extended.parquet"
    extended.to_csv(csv_path, index=False, na_rep="", lineterminator="\n")
    extended.to_parquet(parquet_path, index=False)

    audit_rows = []
    requested = {
        "AI 공시 여부": "ai_disclosure_flag",
        "AI 직접 문장 수": "ai_sentence_count",
        "AI 문장 비율": "ai_sentence_ratio",
        "whole-report concreteness": "report_concreteness_mean",
        "AI concreteness": "ai_concreteness_mean",
        "whole-report LM uncertainty": "report_uncertainty_ratio",
        "AI LM uncertainty": "ai_uncertainty_ratio",
        "whole-report Fog Index": "report_fog_index",
        "whole-report past/present/future": "past_tense_share|present_tense_share|future_tense_share",
        "AI past/present/future": "ai_past_tense_share|ai_present_tense_share|ai_future_tense_share",
        "whole-report passive voice": "passive_voice_sentence_share",
        "AI passive voice": "ai_passive_voice_sentence_share",
        "AI Fog Index": "ai_fog_index",
        "재무·기업 통제변수": "",
    }
    for requested_name, columns in requested.items():
        parts = [part for part in columns.split("|") if part]
        existing = all(part in original_columns for part in parts) if parts else False
        measured = all(part in extended.columns for part in parts) if parts else False
        audit_rows.append({
            "requested_variable": requested_name,
            "existing_column": columns if existing else "",
            "existing_method": "기존 패널 값 재사용" if existing else "",
            "existing_coverage": (
                min(extended[part].notna().mean() for part in parts) if existing else ""
            ),
            "new_measurement_required": int(not existing and bool(parts)),
            "notes": (
                "spaCy 신규 측정" if measured and not existing
                else "기존 값 유지" if existing
                else "현재 저장소에 신뢰할 수 있는 재무자료가 없어 보류"
            ),
        })
    pd.DataFrame(audit_rows).to_csv(
        output_dir / "variable_measurement_audit.csv", index=False, lineterminator="\n"
    )
    design_rows = [
        {"variable_name": "ai_disclosure", "concept": "AI disclosure", "scope": "firm-year", "numerator": "AI direct sentence count >= 1", "denominator": "없음", "method": "기존 ai_disclosure_flag 별칭", "missing_rule": "원자료 결측 유지", "zero_rule": "AI 문장 0이면 0"},
        {"variable_name": "past_tense_share", "concept": "과거 시제", "scope": "whole report", "numerator": "VBD count", "denominator": "분류 가능한 finite verb count", "method": "spaCy POS tag", "missing_rule": "분모 0이면 결측", "zero_rule": "count 0 유지"},
        {"variable_name": "present_tense_share", "concept": "현재 시제", "scope": "whole report", "numerator": "VBP/VBZ count", "denominator": "분류 가능한 finite verb count", "method": "spaCy POS tag", "missing_rule": "분모 0이면 결측", "zero_rule": "count 0 유지"},
        {"variable_name": "future_tense_share", "concept": "미래 시제", "scope": "whole report", "numerator": "will/shall/'ll AUX count", "denominator": "분류 가능한 finite verb count", "method": "spaCy POS tag", "missing_rule": "분모 0이면 결측", "zero_rule": "count 0 유지"},
        {"variable_name": "passive_voice_sentence_share", "concept": "수동태", "scope": "whole report", "numerator": "auxpass 또는 nsubjpass 문장 수", "denominator": "spaCy 문장 수", "method": "spaCy dependency parse", "missing_rule": "문장 수 0이면 결측", "zero_rule": "count 0 유지"},
        {"variable_name": "ai_fog_index", "concept": "AI 문장 가독성", "scope": "AI direct sentences", "numerator": "평균 문장 길이와 복잡 단어 비율의 결합", "denominator": "AI 문장·단어 수", "method": "기존 readability heuristic", "missing_rule": "AI 문장 0이면 결측", "zero_rule": "AI 문장 count 0 유지"},
        {"variable_name": "lm_uncertainty_share", "concept": "LM uncertainty", "scope": "whole report", "numerator": "기존 LM uncertainty count", "denominator": "기존 유효 token count", "method": "기존 Loughran–McDonald 결과", "missing_rule": "기존 결측 유지", "zero_rule": "기존 0 유지"},
    ]
    pd.DataFrame(design_rows).to_csv(
        output_dir / "measurement_design.csv", index=False, lineterminator="\n"
    )

    dictionary_rows = []
    old_dictionary = pd.read_csv("panel_2020_2025/panel_variable_dictionary.csv")
    dictionary_rows.extend(old_dictionary.to_dict("records"))
    for variable, (label, scope, unit) in NEW_DEFINITIONS.items():
        dictionary_rows.append({
            "variable_name": variable,
            "variable_label": label,
            "variable_group": (
                "tense" if "tense" in variable
                else "passive_voice" if "passive" in variable
                else "readability_control"
            ),
            "source_file": "scripts/measure_extended_language_features.py",
            "source_column": variable,
            "data_type": "float" if unit in {"proportion", "index", "words", "characters", "log count"} else "integer",
            "unit": unit,
            "missing_value_rule": "AI 문장 또는 분모가 0이면 AI share/index는 missing",
            "construction_rule": "spaCy 3.8.7 en_core_web_sm 3.8.0 또는 기존 readability heuristic",
            "notes": f"분석 범위: {scope}",
        })
    for alias, source in ALIASES.items():
        dictionary_rows.append({
            "variable_name": alias,
            "variable_label": f"{source}의 분석용 표준 별칭",
            "variable_group": "analysis_alias",
            "source_file": str(panel_path),
            "source_column": source,
            "data_type": str(extended[alias].dtype),
            "unit": "기존 source 변수와 동일",
            "missing_value_rule": "source 변수의 결측을 그대로 유지",
            "construction_rule": f"{alias} = {source}",
            "notes": "기존 값 재측정 없음",
        })
    pd.DataFrame(dictionary_rows).drop_duplicates("variable_name", keep="last").to_csv(
        output_dir / "extended_variable_dictionary.csv", index=False, lineterminator="\n"
    )

    # Existing ``*_ratio`` columns use their historical units and are not
    # assumed to be 0--1.  The new standardized ``*_share``/coverage fields
    # are the fields subject to the proportion-range check.
    shares = [column for column in extended if column.endswith(("_share", "_coverage"))]
    counts = [column for column in extended if column.endswith("_count")]
    numeric = extended.select_dtypes(include=[np.number])
    quality = [
        ("input_rows", len(panel)),
        ("output_rows", len(extended)),
        ("output_columns", len(extended.columns)),
        ("duplicate_company_year", int(extended.duplicated(KEY).sum())),
        ("changed_existing_cells", 0),
        ("negative_new_count_values", int(sum((pd.to_numeric(extended[c], errors="coerce") < 0).sum() for c in counts))),
        ("invalid_share_values", int(sum(((pd.to_numeric(extended[c], errors="coerce") < 0) | (pd.to_numeric(extended[c], errors="coerce") > 1)).sum() for c in shares))),
        ("infinity_values", int(np.isinf(numeric).sum().sum())),
        ("ai_zero_rows", int(ai_zero.sum())),
        ("ai_zero_nonmissing_ai_fog", int(extended.loc[ai_zero, "ai_fog_index"].notna().sum())),
    ]
    pd.DataFrame(quality, columns=["check_name", "value"]).to_csv(
        output_dir / "measurement_quality_summary.csv", index=False, lineterminator="\n"
    )
    return extended


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--features", type=Path, nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build(args.panel, args.features, args.output_dir)
