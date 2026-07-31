#!/usr/bin/env python3
"""Write Korean descriptive-analysis reports from generated tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def fmt(value) -> str:
    if pd.isna(value):
        return "결측"
    if isinstance(value, (float, np.floating)):
        return f"{value:.4f}"
    return str(value)


def korean_table(frame: pd.DataFrame, columns: dict[str, str] | None = None) -> str:
    if frame.empty:
        return "(자료 없음)"
    view = frame.copy()
    if columns:
        view = view.rename(columns=columns)
    return view.to_markdown(index=False, floatfmt=".4f")


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

    balanced = panel.groupby("company_id")["report_year"].nunique().eq(6).sum()
    ai_count = int(panel["ai_disclosure"].sum())
    warning_count = int(panel.get("has_any_warning", pd.Series(dtype=int)).sum())
    report_lines = [
        "# 2020–2025년 S&P 500 기업 10-K 언어 특성 분석",
        "",
        "## 1. 분석 목적",
        "",
        "2020–2025년 firm-year 패널에서 AI disclosure와 문서 언어 특성의 기술통계, 연도별 변화, 기업 내 변화를 정리한다. 본 분석은 기술통계와 상관관계에 한정하며 인과효과를 추정하지 않는다.",
        "",
        "## 2. 분석 표본",
        "",
        f"전체 표본은 {len(panel):,} firm-year이고 고유 기업은 {panel['company_id'].nunique():,}개이다. 6개 연도가 모두 관측된 균형 패널 기업은 {balanced:,}개이며 나머지는 불균형 패널이다.",
        "",
        korean_table(sample, {"report_year": "보고연도", "firm_year_count": "firm-year 수", "unique_company_count": "고유 기업 수", "ai_disclosure_count": "AI 공시 수", "ai_disclosure_rate": "AI 공시 비율"}),
        "",
        "## 3. 변수 및 측정 방법",
        "",
        "기존 패널의 측정값은 그대로 사용했고, 시제와 수동태는 spaCy 3.8.7 및 en_core_web_sm 3.8.0의 POS/dependency 결과로 산출했다. AI 직접 문장 수준 변수는 AI disclosure firm-year에 조건부이며, 분모가 존재하지 않는 경우 결측으로 유지했다.",
        "",
        "## 4. 전체 기술통계",
        "",
        "전체 기술통계는 `table_02_overall_descriptive_statistics.csv`와 `table_03_binary_variable_statistics.csv`에 기록했다. AI 직접 문장 수 0은 실제 0으로 유지하고 AI 수준 평균·비율은 구조적 결측으로 처리했다.",
        "",
        "## 5. 연도별 기술통계",
        "",
        korean_table(yearly.head(6)),
        "",
        "## 6. AI 공시 여부별 비교",
        "",
        "다음 표의 평균 차이는 기술적 비교이며 AI disclosure의 인과효과를 의미하지 않는다.",
        "",
        korean_table(groups, {"variable": "변수", "disclosure_N": "공시 N", "disclosure_mean": "공시 평균", "non_disclosure_N": "미공시 N", "non_disclosure_mean": "미공시 평균", "mean_difference": "평균 차이", "standardized_mean_difference": "표준화 평균 차이"}),
        "",
        "## 7. 연도별 변화",
        "",
        "연도별 평균 변화는 표본 구성 변화의 영향을 받을 수 있다. 절대 변화와 변화율은 `table_06_year_over_year_aggregate_changes.csv`에 저장했다.",
        "",
        korean_table(changes.head(20)),
        "",
        "## 8. 동일 기업 내 전년 대비 변화",
        "",
        "동일 `company_id`에서 연도 차이가 정확히 1년인 쌍만 사용했다. 불균형 패널의 비연속 관측치는 변화량 계산에서 제외했다.",
        "",
        korean_table(within.head(20)),
        "",
        "## 9. Pearson 상관관계",
        "",
        "전체 표본 Pearson 상관계수와 pairwise N은 별도 CSV로 제공한다. 상관관계는 변수 간 선형 연관성만 나타낸다.",
        "",
        "## 10. Spearman 상관관계",
        "",
        "Spearman 상관계수는 순위 기반 연관성을 보조적으로 제시한다. AI 직접 문장 변수는 AI 공시 firm-year만 사용했다.",
        "",
        "## 11. 다중공선성 예비 점검",
        "",
        korean_table(vif, {"variable": "변수", "VIF": "VIF", "N": "관측치 수"}),
        "",
        "기계적으로 파생된 count·share·log 변수, Fog Index와 문장 길이 변수는 동일 회귀식에 동시에 포함할 때 중복 가능성이 있다.",
        "",
        "## 12. 주요 결과",
        "",
        f"AI disclosure firm-year는 {ai_count:,}개이고 미공시는 {len(panel)-ai_count:,}개이다. 경고가 표시된 firm-year는 {warning_count:,}개이다. 연도별 방향과 평균은 산출 CSV 및 그림의 실제 값에 근거해 해석해야 한다.",
        "",
        "## 13. 해석상 주의점",
        "",
        "AI 관련 변수는 AI adoption이 아니라 text-based AI communication의 대리 측정치이다. 기술통계와 상관관계는 인과관계를 의미하지 않으며, 표본 구성 변화와 불균형 패널을 고려해야 한다.",
        "",
        "## 14. 분석의 한계",
        "",
        "사전 기반 감성은 문맥과 부정 표현을 완전히 반영하지 못할 수 있다. 시제와 passive voice는 자동 NLP 측정 오차가 있을 수 있고, Fog Index는 문서의 실질적 정보 품질을 직접 측정하지 않는다. 재무·기업 통제변수는 이번 단계에서 외부 대규모 수집을 하지 않았다.",
        "",
        "## 15. 생성된 산출물",
        "",
        "확장 패널, 변수 사전, 측정 감사표, 품질 요약, 기술통계표, 상관표, VIF표, 집계 CSV 및 PNG/SVG 그림을 `analysis/descriptive_2020_2025/` 아래에 저장했다.",
    ]
    (output / "descriptive_analysis_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    notes = """# 측정 방법 기록

## 기존 변수

기존 `ai_disclosure_flag`, Loughran–McDonald 범주, Brysbaert concreteness, `report_fog_index` 및 보고서 길이 변수는 기존 결과를 그대로 사용했다.

## 신규 시제 변수

`past_tense_count`, `present_tense_count`, `future_tense_count`는 spaCy POS tag를 기준으로 분류했다. 과거는 `VBD`, 현재는 `VBP`·`VBZ`, 미래는 `will`·`shall`·`'ll` 보조 표지를 사용했다. share의 분모는 분류 가능한 세 시제 count의 합이다.

## 신규 수동태 변수

`passive_voice_sentence_count`는 spaCy dependency의 `auxpass` 또는 `nsubjpass` 관계가 있는 문장을 세었다. share의 분모는 spaCy가 분리한 문장 수이다. 문장 구조가 복잡한 경우 오탐·누락 가능성이 있다.

## AI 수준 변수

`ai_` 접두사가 있는 변수는 AI 직접 문장만을 대상으로 한다. AI 문장이 없으면 count는 0이지만 평균·share·Fog Index와 같이 유효 분모가 필요한 값은 결측이다.

## 결측 및 0

실제 count 0과 구조적 결측을 구분했다. 전년 관측이 없거나 분모가 0인 변화량·비율은 0으로 대체하지 않았다.

## 재현성

측정 실행은 `scripts/measure_extended_language_features.py`와 연도별 GitHub Actions artifact를 사용했다. 원본 HTML을 다시 수집하거나 기존 언어 측정값을 재계산하지 않았다.
"""
    (output / "measurement_notes.md").write_text(notes, encoding="utf-8")

    limitations = """# 분석의 한계

- AI 관련 변수는 AI adoption이 아니라 text-based AI communication proxy이다.
- 현재 2020–2025년 firm-year 패널은 불균형 패널이다.
- AI 직접 문장 변수는 AI disclosure firm-year에 조건부이다.
- Loughran–McDonald와 같은 사전 기반 감성은 문맥, 부정 표현 및 다의어를 완전히 반영하지 못할 수 있다.
- 시제와 passive voice는 자동 NLP 측정 오차를 포함할 수 있다.
- Fog Index는 문서의 실질적 정보 품질을 직접 의미하지 않는다.
- 기술통계와 상관관계만으로 인과관계를 판단할 수 없다.
- 이번 단계에서는 재무·기업 통제변수를 대규모로 새로 수집하지 않았다.
"""
    (output / "limitations.md").write_text(limitations, encoding="utf-8")

    summary = f"""# 실행 결과 요약

## 실행 상태

실행 상태: `SUCCESS`(성공)

## 입력 데이터

입력 패널: `{panel_path}`
분석 기간: 2020–2025년

## 분석 표본

전체 firm-year: {len(panel):,}행, 고유 기업: {panel['company_id'].nunique():,}개
연도별 행 수: {sample[['report_year', 'firm_year_count']].to_dict('records')}
AI 공시 firm-year: {ai_count:,}개, AI 미공시 firm-year: {len(panel)-ai_count:,}개

## 확장 패널 결과

기존 열은 변경하지 않고 신규 측정 변수만 결합했다. 상세 품질 수치는 `measurement_quality_summary.csv`에 기록했다.

## 기술통계 및 상관분석

기술통계표, 연도별 변화표, Pearson·Spearman 상관표 및 VIF표를 `tables/`에 생성했다.

## 그래프

연도별 핵심 변수와 AI disclosure 그룹별 그림을 `figures/`에 생성했다.

## 결측 및 warning

AI 문장 0개에 대한 AI 수준 평균·비율과 전년 부재 lag는 결측으로 유지했다. 기존 warning은 관측치 삭제 없이 보존했다.

## 원본 보존

기존 패널·연도별 결과·Google Drive 원본 HTML·R2 객체는 수정하지 않았다. SEC 재수집과 기존 정상 firm-year 재처리는 수행하지 않았다.
"""
    (output / "run_summary.md").write_text(summary, encoding="utf-8")

    # A compact Korean integrated table for manuscript drafting.
    panels = [
        ("패널 A: 표본 및 AI 공시", sample),
        ("패널 B: 언어적 특성", yearly.filter(regex="report_year|mean_(whole_report|past|present|future|lm_uncertainty|passive|fog)")),
        ("패널 C: AI 직접 문장 특성", yearly.filter(regex="report_year|mean_ai_")),
        ("패널 D: 가독성 및 문서 통제변수", yearly.filter(regex="report_year|report_word_count")),
        ("패널 E: 금융 사전 기반 변수", yearly.filter(regex="report_year|lm_|ai_lm_")),
    ]
    parts = ["# 기술통계 통합표", "", "firm-year 단위의 연도별 기술통계이다."]
    for title, frame in panels:
        parts.extend(["", f"## {title}", "", korean_table(frame.head(6))])
    (output / "descriptive_tables.md").write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    write_reports(args.panel, args.output_dir)


if __name__ == "__main__":
    main()
