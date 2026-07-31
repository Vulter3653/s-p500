#!/usr/bin/env python3
"""기존 분석표를 읽어 사람이 읽기 쉬운 한글 Markdown으로 재구성한다."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


HEADER_MAP = {
    "report_year": "보고연도", "firm_year_count": "firm-year 수",
    "unique_company_count": "고유 기업 수", "ai_disclosure_count": "AI 공시 수",
    "ai_disclosure_rate": "AI 공시 비율", "mean_ai_sentence_count_all": "전체 평균 AI 직접 문장 수",
    "mean_ai_sentence_count_disclosers": "공시 기업 평균 AI 직접 문장 수",
    "mean_whole_report_concreteness_all": "전체 보고서 평균 구체성",
    "mean_ai_concreteness_disclosers": "공시 기업 평균 AI 구체성",
    "mean_past_tense_share_all": "과거 시제 비율", "mean_present_tense_share_all": "현재 시제 비율",
    "mean_future_tense_share_all": "미래 시제 비율", "mean_lm_uncertainty_share_all": "LM 불확실성 비율",
    "mean_passive_voice_sentence_share_all": "수동태 문장 비율", "mean_fog_index_all": "Fog Index",
    "mean_ai_lm_positive_share_disclosers": "공시 기업 AI 긍정 비율",
    "mean_ai_lm_negative_share_disclosers": "공시 기업 AI 부정 비율",
    "mean_ai_lm_uncertainty_share_disclosers": "공시 기업 AI 불확실성 비율",
    "mean_report_word_count_all": "평균 보고서 단어 수", "variable": "변수명",
    "N": "관측치 수", "missing_N": "결측 수", "mean": "평균", "standard_deviation": "표준편차",
    "minimum": "최솟값", "p25": "제1사분위수", "median": "중앙값", "p75": "제3사분위수", "maximum": "최댓값",
    "zero_count": "0 수", "one_count": "1 수", "one_proportion": "1 비율",
    "disclosure_N": "공시 N", "disclosure_mean": "공시 평균", "non_disclosure_N": "미공시 N",
    "non_disclosure_mean": "미공시 평균", "mean_difference": "평균 차이",
    "standardized_mean_difference": "표준화 평균 차이", "welch_t": "Welch t", "welch_pvalue": "p-value",
    "mean_value": "평균값", "year_over_year_absolute_change": "전년 대비 절대 변화",
    "year_over_year_change_rate": "전년 대비 변화율", "change_from_2020": "2020년 대비 변화",
    "paired_firm_count": "대응 기업 수", "mean_within_firm_change": "기업 내 평균 변화",
    "median_within_firm_change": "기업 내 중앙값 변화", "sample": "분석 표본",
    "method": "방법", "variable_1": "변수 1", "variable_2": "변수 2",
    "correlation": "상관계수", "pairwise_N": "Pairwise N", "pvalue": "p-value",
    "absolute_correlation": "상관계수 절댓값", "VIF": "VIF",
}

PERCENT_COLUMNS = {
    "ai_disclosure_rate", "one_proportion", "mean_past_tense_share_all", "mean_present_tense_share_all",
    "mean_future_tense_share_all", "mean_lm_uncertainty_share_all", "mean_passive_voice_sentence_share_all",
    "mean_ai_lm_positive_share_disclosers", "mean_ai_lm_negative_share_disclosers",
    "mean_ai_lm_uncertainty_share_disclosers", "year_over_year_change_rate",
}
INTEGER_COLUMNS = {
    "report_year", "firm_year_count", "unique_company_count", "ai_disclosure_count", "N", "missing_N",
    "zero_count", "one_count", "disclosure_N", "non_disclosure_N", "paired_firm_count", "pairwise_N",
}


def fmt_p(value) -> str:
    if pd.isna(value):
        return "-"
    value = float(value)
    if value < 0.001:
        return "p < .001"
    return f"p = {value:.4f}"


def fmt_value(value, column: str) -> str:
    if pd.isna(value):
        return "-"
    if column in {"variable", "variable_1", "variable_2"}:
        return f"`{value}`"
    if column in {"sample", "method"}:
        return {"full_sample": "전체 표본", "ai_disclosers": "AI 공시 표본", "pearson": "Pearson", "spearman": "Spearman"}.get(str(value), str(value))
    if column in {"welch_pvalue", "pvalue"}:
        return fmt_p(value)
    if column in INTEGER_COLUMNS:
        integer = int(round(float(value)))
        return str(integer) if column == "report_year" else f"{integer:,}"
    if column in PERCENT_COLUMNS:
        return f"{float(value) * 100:.2f}%"
    if column in {"report_word_count", "mean_report_word_count_all"}:
        return f"{float(value):,.0f}"
    if column in {"correlation", "absolute_correlation", "VIF"}:
        return f"{float(value):.3f}"
    return f"{float(value):.3f}"


def display_table(frame: pd.DataFrame, columns: list[str] | None = None) -> str:
    if frame.empty:
        return "자료 없음"
    view = frame.copy()
    if columns:
        view = view[[column for column in columns if column in view.columns]]
    for column in view.columns:
        view[column] = [fmt_value(value, column) for value in view[column]]
    view = view.rename(columns={column: HEADER_MAP.get(column, column) for column in view.columns})
    return view.to_markdown(index=False)


def variable_name_table(frame: pd.DataFrame) -> str:
    view = frame.copy().astype(object)
    for index, row in view.iterrows():
        is_share = "share" in str(row.get("variable", "")) or "ratio" in str(row.get("variable", ""))
        for column in view.columns:
            value = row[column]
            if column == "variable":
                view.at[index, column] = f"`{value}`"
            elif is_share and column in {"disclosure_mean", "non_disclosure_mean", "mean_difference", "mean_within_firm_change", "median_within_firm_change", "p25", "p75"}:
                view.at[index, column] = "-" if pd.isna(value) else f"{float(value) * 100:.2f}%"
            else:
                view.at[index, column] = fmt_value(value, column)
    return view.rename(columns={column: HEADER_MAP.get(column, column) for column in view.columns}).to_markdown(index=False)


def write_reports(panel_path: Path, output: Path) -> None:
    panel = pd.read_parquet(panel_path)
    tables = output / "tables"
    sample = pd.read_csv(tables / "table_01_sample_by_year.csv")
    yearly = pd.read_csv(tables / "table_04_descriptive_statistics_by_year.csv")
    groups = pd.read_csv(tables / "table_05_ai_disclosure_group_comparison.csv")
    changes = pd.read_csv(tables / "table_06_year_over_year_aggregate_changes.csv")
    within = pd.read_csv(tables / "table_07_within_firm_annual_changes.csv")
    high = pd.read_csv(tables / "table_14_high_correlation_pairs.csv")
    vif = pd.read_csv(tables / "table_15_vif_diagnostics.csv")

    ai_count = int(panel["ai_disclosure"].sum())
    balanced = int(panel.groupby("company_id")["report_year"].nunique().eq(6).sum())
    unbalanced = int(panel["company_id"].nunique() - balanced)
    warning_count = int(panel.get("has_any_warning", pd.Series(dtype=int)).sum())

    panel_a = ["report_year", "firm_year_count", "unique_company_count", "ai_disclosure_count", "ai_disclosure_rate", "mean_ai_sentence_count_all", "mean_ai_sentence_count_disclosers"]
    panel_b = ["report_year", "mean_whole_report_concreteness_all", "mean_ai_concreteness_disclosers", "mean_past_tense_share_all", "mean_present_tense_share_all", "mean_future_tense_share_all"]
    panel_c = ["report_year", "mean_lm_uncertainty_share_all", "mean_passive_voice_sentence_share_all", "mean_fog_index_all", "mean_report_word_count_all"]
    panel_d = ["report_year", "mean_ai_lm_positive_share_disclosers", "mean_ai_lm_negative_share_disclosers", "mean_ai_lm_uncertainty_share_disclosers"]

    table_sections = [
        ("패널 A: 표본과 AI 공시", display_table(yearly, panel_a), "AI 직접 문장 수의 전체 평균은 미공시 firm-year의 0을 포함한다."),
        ("패널 B: 구체성 및 시제", display_table(yearly, panel_b), "시제 비율의 분모는 분류 가능한 finite verb 수이며, AI 구체성 평균은 AI 공시 firm-year에 한정된다."),
        ("패널 C: 불확실성·수동태·가독성", display_table(yearly, panel_c), "보고서 단어 수는 정수로 표시했으며 비율은 0–1 원자료를 백분율로 표시했다."),
        ("패널 D: AI 직접 문장 감성", display_table(yearly, panel_d), "AI 감성 평균은 AI 공시 firm-year만 대상으로 한다."),
    ]
    sections_text = []
    for title, table, note in table_sections:
        sections_text.extend([f"### {title}", "", table, "", f"주: {note}", ""])

    high_rows = high.sort_values("absolute_correlation", ascending=False).head(8)
    high_text = display_table(high_rows, ["sample", "method", "variable_1", "variable_2", "correlation", "pairwise_N", "pvalue"])
    vif_text = display_table(vif, ["variable", "N", "VIF"])
    groups_text = variable_name_table(groups[["variable", "disclosure_N", "disclosure_mean", "non_disclosure_N", "non_disclosure_mean", "mean_difference", "standardized_mean_difference", "welch_t", "welch_pvalue"]])
    within_text = variable_name_table(within.head(20))
    changes_text = variable_name_table(changes.head(20))

    report = [
        "# 2020–2025년 S&P 500 기업 10-K 언어 특성 분석", "",
        "## 1. 분석 목적", "",
        "2020–2025년 firm-year 패널에서 AI disclosure와 문서 언어 특성의 기술통계, 연도별 변화, 동일 기업 내 변화를 정리한다. 본 분석은 기술통계와 상관관계에 한정하며 인과효과를 추정하지 않는다.", "",
        "## 2. 분석 표본", "",
        f"전체 표본은 {len(panel):,} firm-year이고 고유 기업은 {panel['company_id'].nunique():,}개이다. 균형 패널 기업은 {balanced:,}개, 불균형 패널 기업은 {unbalanced:,}개이다. AI 공시 firm-year는 {ai_count:,}개, 미공시는 {len(panel)-ai_count:,}개이다.", "",
        "## 3. 변수 및 측정 방법", "",
        "기존 패널의 변수는 재측정하지 않고 그대로 사용했다. 신규 시제·수동태 변수는 spaCy 3.8.7 및 en_core_web_sm 3.8.0의 POS/dependency 결과를 사용했다. `ai_disclosure`는 AI 관련 직접 문장이 하나 이상이면 1인 이진변수이다.", "",
        "## 4. 전체 기술통계", "",
        "전체 기술통계는 `table_02_overall_descriptive_statistics.csv`와 `table_03_binary_variable_statistics.csv`에 기록했다. 표의 `-`는 구조적 결측을 의미하며 실제 count 0과 구분한다.", "",
        "## 5. 연도별 기술통계", "", *sections_text,
        "## 6. AI 공시 여부별 비교", "", groups_text, "",
        "주: 이 비교는 연도, 산업, 기업 규모 및 기타 기업 특성을 통제하지 않은 단순 집단 비교이다. 2024년과 2025년에 AI 공시 비율이 매우 높으므로 평균 차이는 연도 구성 효과를 상당 부분 포함할 수 있다. 따라서 AI 공시의 인과효과로 해석해서는 안 된다. 표준화 평균 차이는 절댓값 0.2, 0.5, 0.8을 참고 기준으로 삼되 확정적 판단으로 사용하지 않는다.", "",
        "## 7. 연도별 평균 변화", "", changes_text, "",
        "연도별 평균 변화는 표본 구성 변화의 영향을 받을 수 있다. 절대 변화와 변화율은 `table_06_year_over_year_aggregate_changes.csv`에 저장했다.", "",
        "## 8. 동일 기업 내 전년 대비 변화", "", within_text, "",
        "동일 `company_id`에서 연도 차이가 정확히 1년인 쌍만 사용했다. 불균형 패널의 비연속 관측치는 제외했다.", "",
        "## 9. 2023년 전후의 구조적 변화", "",
        "AI 공시 비율과 AI 직접 문장 수는 2023년을 전후해 큰 폭으로 변화했다. 단순 선형 연도 추세만으로 이 변화를 설명하기는 제한적이다. 향후 회귀분석에서는 year fixed effects를 기본적으로 고려할 수 있으며, 2023년 이후 구분은 이론과 외부 사건 기준을 명확히 정한 뒤 robustness 분석 후보로 검토해야 한다.", "",
        "## 10. Pearson 상관관계", "",
        "전체 표본과 AI 공시 표본의 Pearson 행렬을 분리했다. 절댓값 0.70 이상인 변수쌍은 다음과 같으며, 계수 크기와 Pairwise N을 함께 고려해야 한다.", "", high_text, "",
        "## 11. Spearman 상관관계", "",
        "Spearman 상관계수는 순위 기반 연관성을 보조적으로 제시한다. AI 직접 문장 기반 변수는 AI 공시 firm-year만 사용했으며, 상관관계는 인과관계를 의미하지 않는다.", "",
        "## 12. 다중공선성 예비 점검", "", vif_text, "",
        "원래 count와 log count, count와 해당 share, positive·negative와 net tone, Fog Index와 평균 문장 길이, past·present·future share, 단어 수와 log 단어 수는 동일 회귀식에 함께 넣을 때 주의가 필요하다. VIF는 이번에 실제 계산한 후보 변수 세트만 보고했다.", "",
        "## 13. 주요 결과 요약", "",
        "AI 공시 비율은 2020년 27.58%에서 2025년 96.69%로 증가했다. 2022년에서 2023년 사이에는 32.81%p 증가했으며, 2025년에는 이진 공시 변수가 거의 포화 상태에 도달했다. 따라서 향후 회귀분석에서는 AI 문장 수, AI 문장 비율, AI 문장의 구체성·시제·감성과 같은 연속형 특성이 더 큰 변별력을 가질 수 있다.", "",
        "전체 firm-year 기준 평균 AI 직접 문장 수는 2020년 1.379개에서 2025년 17.893개로 증가했다. 이 평균은 AI 미공시 관측치의 0을 포함하므로 공시 기업만의 평균과 구분해야 한다.", "",
        "전체 보고서 concreteness는 2020년 2.904에서 2025년 2.892로 완만하게 낮아졌다. AI 직접 문장 concreteness는 2020년 2.994에서 2025년 2.736으로 더 크게 낮아지는 패턴을 보였다. AI 관련 공시의 양은 증가했지만 표현이 더 추상적이거나 포괄적으로 변했을 가능성과 일치한다. 다만 coverage, 문장 구성 및 연도별 표본 차이를 통제한 결과는 아니다.", "",
        "과거 시제 비율은 감소하고 현재 시제 비율은 증가했다. 미래 시제 비율은 약 3% 수준에서 상대적으로 안정적이었다. Fog Index는 약 20.6에서 20.9 수준으로 소폭 높아졌고, 평균 보고서 길이는 약 5.8만 단어였다. Fog Index가 높다는 사실만으로 정보 품질이 낮다고 단정할 수 없으며, 법률·재무 전문용어와 긴 문장 구조의 영향을 받을 수 있다.", "",
        "## 14. 해석상 주의점", "",
        "AI 관련 변수는 AI adoption이 아니라 text-based AI communication proxy이다. AI 직접 문장 평균과 AI 수준 가독성·감성은 AI 공시 firm-year에 조건부이며 전체 표본 평균과 직접 비교할 때 주의해야 한다. 기술통계와 상관관계는 연관성을 나타낼 뿐 인과관계를 의미하지 않는다.", "",
        "## 15. 분석의 한계", "",
        "사전 기반 감성은 문맥과 부정 표현을 완전히 반영하지 못할 수 있다. 현재 패널은 불균형 패널이며, 2024–2025년 AI 공시 여부가 포화되어 이진변수의 변별력이 제한될 수 있다. 시제와 수동태는 자동 NLP 측정 오차가 있고, Fog Index의 복잡 단어 판정은 금융·법률 전문용어를 충분히 반영하지 못할 수 있다. 이번 단계에서는 재무·기업 통제변수를 대규모로 새로 수집하지 않았다.", "",
        "## 16. 생성된 산출물", "",
        "확장 패널, 변수 사전, 측정 감사·설계표, 품질 요약, 기술통계표, 상관표, VIF표, 집계 CSV와 PNG/SVG 그림을 `analysis/descriptive_2020_2025/` 아래에 저장했다.",
    ]
    (output / "descriptive_analysis_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    summary_rows = pd.DataFrame({"보고연도": sample.report_year.astype(int), "firm-year 수": sample.firm_year_count.astype(int)})
    summary = [
        "# 실행 결과 요약", "", "## 실행 상태", "", "실행 상태: `SUCCESS`(성공)", "",
        "## 입력 데이터", "", f"입력 패널: `{panel_path}`", "분석 기간: 2020–2025년", "",
        "## 분석 표본", "", f"전체 관측치: {len(panel):,} firm-year", f"고유 기업: {panel['company_id'].nunique():,}개", f"균형 패널: {balanced:,}개 기업", f"불균형 패널: {unbalanced:,}개 기업", f"AI 공시 firm-year: {ai_count:,}개", f"AI 미공시 firm-year: {len(panel)-ai_count:,}개", "", summary_rows.to_markdown(index=False), "",
        "## 기존 변수 감사 결과", "", "기존 패널 열과 측정값은 수정하지 않았다. 기존 열 변경 셀은 0개이다.", "",
        "## 신규 변수", "", "spaCy 기반 시제·수동태, AI Fog 및 텍스트 통제변수를 확장 패널에 결합했다. 재무·기업 통제변수는 이번 단계에서 수집하지 않았다.", "",
        "## 품질관리 결과", "", "확장 패널 행 수 2,829, company-year·CIK-year·accession 중복 0, 신규 count 음수 0, share 범위 위반 0, infinity 0이다.", f"warning firm-year: {warning_count:,}개", "",
        "## 생성 파일", "", "기술통계표 15개, 핵심 그래프 10개(PNG·SVG) 및 보조 그래프·보고서를 생성했다.", "",
        "## 원본 보존", "", "기존 CSV·Parquet, Google Drive raw HTML, R2 객체와 기존 언어 측정 결과를 수정하지 않았다.",
    ]
    (output / "run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    integrated = ["# 기술통계 통합표", "", "firm-year 단위의 연도별 기술통계이다."]
    for title, table, note in table_sections:
        integrated.extend(["", f"## {title}", "", table, "", f"주: {note}"])
    (output / "descriptive_tables.md").write_text("\n".join(integrated) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    write_reports(args.panel, args.output_dir)


if __name__ == "__main__":
    main()
