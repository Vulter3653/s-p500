#!/usr/bin/env python3
"""Generate read-only research dashboard data from existing analysis artifacts.

No statistics are stored in frontend source. This script is the single build-time
source for web/public/data and the paper-ready variable-definition downloads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis/descriptive_2020_2025"
TABLES = ANALYSIS / "tables"
FIGURES = ANALYSIS / "figures"
PANEL = ANALYSIS / "firm_year_language_extended.csv"
DEFAULT_OUT = ROOT / "web/public/data"

REQUIRED_SOURCES = {
    "yearly_statistics": TABLES / "table_04_descriptive_statistics_by_year.csv",
    "sample_by_year": TABLES / "table_01_sample_by_year.csv",
    "descriptive_statistics": TABLES / "table_02_overall_descriptive_statistics.csv",
    "binary_statistics": TABLES / "table_03_binary_variable_statistics.csv",
    "disclosure_comparison": TABLES / "table_05_ai_disclosure_group_comparison.csv",
    "within_firm_changes": TABLES / "table_07_within_firm_annual_changes.csv",
    "year_over_year_changes": TABLES / "table_06_year_over_year_aggregate_changes.csv",
    "pearson_full": TABLES / "table_08_pearson_correlation_full_sample.csv",
    "spearman_full": TABLES / "table_09_spearman_correlation_full_sample.csv",
    "pearson_ai": TABLES / "table_10_pearson_correlation_ai_disclosers.csv",
    "spearman_ai": TABLES / "table_11_spearman_correlation_ai_disclosers.csv",
    "correlation_pvalues": TABLES / "table_13_correlation_pvalues.csv",
    "high_correlations": TABLES / "table_14_high_correlation_pairs.csv",
    "vif": TABLES / "table_15_vif_diagnostics.csv",
    "aggregate_figures": FIGURES / "figure_aggregate_data.csv",
    "ai_group_figures": FIGURES / "figure_ai_group_data.csv",
    "within_change_figures": FIGURES / "figure_within_firm_change_data.csv",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    return value


def records(frame: pd.DataFrame) -> list[dict]:
    return [{key: clean(value) for key, value in row.items()} for row in frame.to_dict("records")]


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def generic_definition(column: str) -> dict:
    if column.endswith(("_share", "_ratio", "_coverage")):
        unit, formula = "Proportion", f"{column} = source-defined numerator / source-defined denominator"
    elif column.endswith(("_count", "_word_count", "_sentence_count", "_bytes", "_character_count")):
        unit, formula = "Count", f"{column} = source-defined eligible unit count"
    elif column.startswith("is_") or column.startswith("has_") or column.endswith("_flag"):
        unit, formula = "Binary indicator", f"{column} = source-defined indicator"
    else:
        unit, formula = "Source value", f"{column} = copied source value"
    display_parts = ["Loughran–McDonald" if part.lower() == "lm" else part.title() for part in column.split("_")]
    return {
        "display_name": " ".join(display_parts), "group": "Source / Derived",
        "analysis_level": "Firm-year", "definition": f"{column} is retained from the validated extended panel without remeasurement.",
        "conceptual_meaning": "Source-defined panel value.", "operationalization": "Value copied from the source extended panel.",
        "formula": formula, "numerator": "Source-defined or not applicable", "denominator": "Source-defined or not applicable",
        "unit": unit, "token_rule": "Inherited from source measurement.", "sentence_rule": "Inherited from source measurement.",
        "method": "Existing source measurement", "preprocessing": "No transformation beyond serialization.",
        "missing_rule": "원자료의 결측값은 결측으로 유지한다.", "zero_rule": "원자료의 0은 0으로 유지한다.",
        "conditional_sample": "Source-defined sample", "source_columns": [column],
        "source_dataset": "analysis/descriptive_2020_2025/firm_year_language_extended.csv",
        "source_scripts": ["scripts/build_extended_language_panel.py"],
        "validation_rule": "원자료 열의 존재와 결측 의미를 검증한다.",
        "interpretation": "Interpret according to the source variable dictionary.",
        "limitation": "This generated generic description must be supplemented before publication if the variable is used as a primary construct.",
        "aliases": [],
    }


def load_definitions(panel_columns: list[str]) -> list[dict]:
    config_path = ROOT / "config/variable_definitions.yaml"
    configured = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    definitions = []
    for column in panel_columns:
        definition = dict(configured.get(column, generic_definition(column)))
        definition["variable"] = column
        definition.setdefault("source_columns", [column])
        if not set(definition["source_columns"]).issubset(panel_columns):
            missing = sorted(set(definition["source_columns"]) - set(panel_columns))
            raise ValueError(f"Variable {column} references missing source columns: {missing}")
        for required in ("formula", "numerator", "denominator", "missing_rule", "source_scripts"):
            if not definition.get(required):
                raise ValueError(f"Variable {column} lacks required metadata: {required}")
        source_dataset = definition.get("source_dataset")
        if source_dataset and not (ROOT / source_dataset).exists():
            raise ValueError(f"Variable {column} references missing source dataset: {source_dataset}")
        missing_scripts = [script for script in definition.get("source_scripts", []) if not (ROOT / script).exists()]
        if missing_scripts:
            raise ValueError(f"Variable {column} references missing source scripts: {missing_scripts}")
        definitions.append(definition)
    return definitions


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def definition_rows(definitions: list[dict]) -> list[dict]:
    fields = ["variable", "display_name", "group", "analysis_level", "definition", "formula", "numerator", "denominator", "unit", "token_rule", "sentence_rule", "method", "preprocessing", "missing_rule", "zero_rule", "conditional_sample", "source_columns", "source_dataset", "source_scripts", "validation_rule", "interpretation", "limitation", "aliases"]
    rows = []
    for item in definitions:
        row = {field: item.get(field, "") for field in fields}
        row["source_columns"] = "|".join(row["source_columns"] or [])
        row["source_scripts"] = "|".join(row["source_scripts"] or [])
        row["aliases"] = "|".join(row["aliases"] or [])
        rows.append(row)
    return rows


def dashboard_descriptive_rows(frame: pd.DataFrame) -> list[dict]:
    """Normalize source table names for the read-only dashboard renderer."""
    rows = []
    for row in records(frame):
        variable = row.get("variable", "")
        kind = "share" if variable.endswith(("_share", "_ratio", "_coverage")) else "number" if variable.endswith(("_count", "_words", "_word_count", "_sentence_count")) else "continuous"
        rows.append({
            **row,
            "label": variable.replace("_", " ").title(),
            "kind": kind,
            "n": row.get("N"),
            "sd": row.get("standard_deviation"),
            "q1": row.get("p25"),
            "q3": row.get("p75"),
        })
    return rows


def write_definition_markdown(path: Path, definitions: list[dict]) -> None:
    panels = {
        "Identification": "패널 A. 식별 변수", "AI Communication": "패널 B. AI 커뮤니케이션 변수",
        "Concreteness": "패널 C. 구체성 변수", "Loughran–McDonald": "패널 D. Loughran–McDonald 변수",
        "Tense": "패널 E. 시제 변수", "Passive Voice": "패널 F. 수동태 변수",
        "Readability": "패널 G. 가독성 변수", "Lexical Controls": "패널 H. 어휘 통제변수",
    }
    lines = ["# 부록 A. 변수 정의", "", "각 변수의 정의는 실제 패널 열, 측정 script 및 검증 규칙에 연결된다.", ""]
    for group in list(panels) + ["Source / Derived"]:
        rows = [item for item in definitions if item["group"] == group]
        if not rows:
            continue
        lines += [f"## {panels.get(group, '패널 I. 패널 구조 및 파생 변수')}", ""]
        for item in rows:
            lines += [f"### `{item['variable']}` — {item['display_name']}", "", f"**상세 정의:** {item['definition']}", "", f"**분석 수준:** {item['analysis_level']}  ", f"**수식:** `{item['formula']}`  ", f"**분자:** {item['numerator']}  ", f"**분모:** {item['denominator']}  ", f"**단위:** {item['unit']}  ", f"**토큰 규칙:** {item['token_rule']}  ", f"**문장 규칙:** {item['sentence_rule']}  ", f"**사전/NLP:** {item['method']}  ", f"**전처리:** {item['preprocessing']}  ", f"**결측:** {item['missing_rule']}  ", f"**0 처리:** {item['zero_rule']}  ", f"**조건부 표본:** {item['conditional_sample']}  ", f"**Source column:** `{', '.join(item['source_columns'])}`  ", f"**Source dataset:** `{item['source_dataset']}`  ", f"**Measurement script:** `{', '.join(item['source_scripts'])}`  ", f"**검증:** {item['validation_rule']}  ", f"**해석:** {item['interpretation']}  ", f"**한계:** {item['limitation']}  ", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(line.rstrip() for line in lines), encoding="utf-8")


def generate(output: Path) -> dict:
    panel = pd.read_csv(PANEL)
    sources = {key: pd.read_csv(path) for key, path in REQUIRED_SOURCES.items()}
    if set(sources["sample_by_year"]["report_year"].astype(int)) != set(range(2020, 2026)):
        raise ValueError("Generated web data do not match analysis period")
    if len(panel) != int(sources["sample_by_year"]["firm_year_count"].sum()):
        raise ValueError("Generated web data do not match panel row count")
    if panel.duplicated(["company_id", "report_year"]).any():
        raise ValueError("Generated web data do not match unique firm-year key")
    if int(panel["ai_disclosure"].sum()) != int(sources["sample_by_year"]["ai_disclosure_count"].sum()):
        raise ValueError("AI disclosure source mismatch")
    proportion_columns = [c for c in panel.columns if c.endswith(("_share", "_coverage")) or c in {"ai_sentence_ratio", "report_numeric_token_ratio", "report_table_text_ratio", "ai_sentiment_word_coverage"}]
    for column in proportion_columns:
        values = pd.to_numeric(panel[column], errors="coerce").dropna()
        if ((values < 0) | (values > 1)).any():
            raise ValueError(f"Invalid proportion values: {column}")
    numeric = panel.select_dtypes(include="number")
    if numeric.isin([float("inf"), float("-inf")]).any().any():
        raise ValueError("Generated web data contain Infinity")

    definitions = load_definitions(list(panel.columns))
    now = datetime.now(timezone.utc).isoformat()
    commit = git_commit()
    manifest = {"analysis_period": "2020-2025", "unit_of_analysis": "firm-year", "git_commit": commit, "generated_at": now, "sources": []}
    for key, path in REQUIRED_SOURCES.items():
        manifest["sources"].append({"dataset_id": key, "source_file": str(path.relative_to(ROOT)), "source_sha256": sha256(path), "source_columns": list(sources[key].columns), "generation_script": "scripts/generate_web_analysis_data.py"})
    manifest["sources"].append({"dataset_id": "extended_panel", "source_file": str(PANEL.relative_to(ROOT)), "source_sha256": sha256(PANEL), "source_columns": list(panel.columns), "generation_script": "scripts/generate_web_analysis_data.py"})

    # Figure data are copied from the existing, reproducibly generated figure
    # tables.  The frontend receives only these records; it never embeds
    # analysis values in React source.
    aggregate_for_web = sources["aggregate_figures"].merge(
        sources["yearly_statistics"][["report_year", "mean_ai_sentence_count_disclosers"]],
        on="report_year", how="left", validate="one_to_one",
    )
    figure_sources = {
        "aggregate": aggregate_for_web,
        "ai_group": sources["ai_group_figures"],
        "within_change": sources["within_change_figures"],
        "comparison": sources["disclosure_comparison"],
        "pearson": sources["pearson_full"],
        "vif": sources["vif"],
    }
    figure_data = {name: records(frame) for name, frame in figure_sources.items()}
    write_json(output / "figure-data.json", figure_data)
    figure_manifest = []
    figure_specs = [
        ("figure-01", "Figure 1", "연도별 AI 공시 확산", "line", "aggregate", ["report_year", "ai_disclosure_rate"], "전체 firm-year; 연도별 N을 분모로 사용", None, "figures/01_ai_disclosure_rate_by_year.svg", "figure_aggregate_data.csv"),
        ("figure-02", "Figure 2", "AI 커뮤니케이션 강도 추이", "line", "aggregate", ["report_year", "mean_ai_sentence_count_all", "mean_ai_sentence_count_disclosers"], "전체 firm-year 평균과 AI 공시 firm-year 조건부 평균", "ai_disclosure=1은 조건부 표본", "figures/02_mean_ai_sentence_count_by_year.svg", "figure_aggregate_data.csv"),
        ("figure-03", "Figure 3", "구체성 추이", "line", "aggregate", ["report_year", "whole_report_concreteness", "ai_concreteness"], "전체 보고서와 AI 직접 문장 수준", "AI 구체성은 AI 공시 firm-year 조건부", "figures/03_whole_report_concreteness_by_year.svg", "figure_aggregate_data.csv"),
        ("figure-04", "Figure 4", "시제 구성 변화", "line", "aggregate", ["report_year", "past_tense_share", "present_tense_share", "future_tense_share"], "전체 firm-year; finite tense count 분모", "미래 표지는 제한적 조동사 조건부", "figures/05_tense_shares_by_year.svg", "figure_aggregate_data.csv"),
        ("figure-05", "Figure 5", "AI 직접 문장의 Loughran–McDonald 언어 추이", "line", "aggregate", ["report_year", "ai_lm_positive_share", "ai_lm_negative_share", "ai_lm_uncertainty_share"], "AI 공시 firm-year 조건부", "Loughran–McDonald 금융사전 기반 상대 빈도", "figures/09_ai_sentiment_by_year.svg", "figure_aggregate_data.csv"),
        ("figure-06", "Figure 6", "AI 공시·미공시 표준화 평균 차이", "effect", "comparison", ["variable", "standardized_mean_difference"], "전체 firm-year 단순 집단 비교", "연도·산업·규모를 통제하지 않은 비교", None, "table_05_ai_disclosure_group_comparison.csv"),
        ("figure-07", "Figure 7", "동일 기업 내 전년 대비 변화", "change", "within_change", ["variable", "report_year", "mean_within_firm_change"], "연속된 두 연도의 firm pair", "변수별 단위가 다르므로 패널을 분리해 해석", None, "figure_within_firm_change_data.csv"),
    ]
    for figure_id, number, title, chart_type, dataset_id, columns, sample, condition, static_svg, source_name in figure_specs:
        source_key = {"aggregate": "aggregate_figures", "ai_group": "ai_group_figures", "within_change": "within_change_figures", "comparison": "disclosure_comparison"}[dataset_id]
        if figure_id == "figure-02":
            source_key = "yearly_statistics"
        source_path = REQUIRED_SOURCES[source_key]
        figure_manifest.append({
            "figure_id": figure_id, "number": number, "title": title, "type": chart_type,
            "section": "7. 분석 결과", "source_file": str(source_path.relative_to(ROOT)),
            "source_sha256": sha256(source_path), "source_columns": columns, "sample": sample,
            "n_rule": "연도별 또는 pairwise 유효 관측치", "conditional_sample": condition,
            "missing_rule": "원자료의 결측은 그래프에서 제외하며 0으로 대체하지 않음",
            "generation_script": "scripts/generate_web_analysis_data.py",
            "chart_component": {"line": "LineFigure", "effect": "EffectSizeFigure", "change": "WithinChangeFigure"}[chart_type],
            "static_svg": static_svg, "source_download": f"/downloads/{source_name}",
            "notes": ["기술통계 및 연관성 결과이며 인과효과를 의미하지 않음"],
            "git_commit": commit, "generated_at": now,
        })
    write_json(output / "figure-manifest.json", figure_manifest)

    sample_rows = {int(row["report_year"]): row for row in records(sources["sample_by_year"])}
    yearly_source = records(sources["aggregate_figures"])
    years = []
    for row in yearly_source:
        year = int(row["report_year"])
        sample = sample_rows[year]
        years.append({"year": year, "observations": int(sample["firm_year_count"]), "disclosure": int(sample["ai_disclosure_count"]), "aiSentenceCount": row.get("mean_ai_sentence_count_all"), "wholeReportConcreteness": row.get("whole_report_concreteness"), "aiConcreteness": row.get("ai_concreteness"), "past": row.get("past_tense_share"), "present": row.get("present_tense_share"), "future": row.get("future_tense_share"), "uncertainty": row.get("lm_uncertainty_share"), "passive": row.get("passive_voice_sentence_share"), "fog": row.get("fog_index"), "reportWords": row.get("report_word_count"), "aiPositive": row.get("ai_lm_positive_share"), "aiNegative": row.get("ai_lm_negative_share"), "aiUncertainty": row.get("ai_lm_uncertainty_share")})
    high_pairs = records(sources["high_correlations"])
    summary = {"panel": {"observations": len(panel), "companies": int(panel.company_id.nunique()), "balanced_companies": int(panel.groupby("company_id").report_year.nunique().eq(6).sum()), "unbalanced_companies": int(panel.company_id.nunique() - panel.groupby("company_id").report_year.nunique().eq(6).sum())}, "years": years, "descriptiveTable": dashboard_descriptive_rows(sources["descriptive_statistics"]), "correlations": high_pairs[:10], "generated_at": now, "git_commit": commit}
    payloads = {
        "analysis-summary.json": summary,
        "yearly-statistics.json": records(sources["yearly_statistics"]),
        "descriptive-statistics.json": records(sources["descriptive_statistics"]),
        "disclosure-comparison.json": records(sources["disclosure_comparison"]),
        "within-firm-changes.json": records(sources["within_firm_changes"]),
        "correlations.json": {"pearson_full": records(sources["pearson_full"]), "spearman_full": records(sources["spearman_full"]), "pearson_ai": records(sources["pearson_ai"]), "spearman_ai": records(sources["spearman_ai"]), "pvalues": records(sources["correlation_pvalues"]), "high_pairs": records(sources["high_correlations"])},
        "vif.json": records(sources["vif"]), "pearson-correlations.json": records(sources["pearson_full"]), "spearman-correlations.json": records(sources["spearman_full"]), "variable-definitions.json": definitions,
        "source-manifest.json": manifest, "build-metadata.json": {"generated_at": now, "git_commit": commit, "analysis_period": "2020-2025", "version": (ROOT / "VERSION").read_text().strip()},
        "year-over-year-changes.json": records(sources["year_over_year_changes"]),
        "sample-audit.json": {"panel_rows": len(panel), "year_rows": records(sources["sample_by_year"]), "duplicate_company_year": int(panel.duplicated(["company_id", "report_year"]).sum()), "duplicate_accession": int(panel.duplicated(["accession_number"]).sum())},
        "quality-control.json": {"panel_rows": len(panel), "infinity_rows": 0, "share_range_validated": True, "source_columns": len(panel.columns)},
    }
    for filename, payload in payloads.items():
        write_json(output / filename, payload)
    rows = definition_rows(definitions)
    output.joinpath("variable-definitions.csv").write_text(pd.DataFrame(rows).to_csv(index=False), encoding="utf-8")
    downloads = ROOT / "web/public/downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    downloads.joinpath("table-variable-definitions.csv").write_text(pd.DataFrame(rows).to_csv(index=False), encoding="utf-8")
    csv_exports = {"disclosure-comparison": sources["disclosure_comparison"], "within-firm-changes": sources["within_firm_changes"], "pearson-correlations": sources["pearson_full"], "spearman-correlations": sources["spearman_full"], "vif": sources["vif"], "year-over-year-changes": sources["year_over_year_changes"], "figure-aggregate-data": aggregate_for_web, "figure-ai-group-data": sources["ai_group_figures"], "figure-within-firm-change-data": sources["within_change_figures"]}
    for name, frame in csv_exports.items():
        downloads.joinpath(f"{name}.csv").write_text(frame.to_csv(index=False), encoding="utf-8")
    write_definition_markdown(downloads / "variable-definitions.md", definitions)
    (ROOT / "web/docs").mkdir(parents=True, exist_ok=True)
    write_definition_markdown(ROOT / "web/docs/research-dashboard-variable-definitions.md", definitions)
    # The report UI renders these audited Markdown sources inside the integrated
    # document. Keep a generated, public copy so the browser never depends on
    # files outside the Vite public tree.
    public_docs = ROOT / "web/public/docs"
    public_docs.mkdir(parents=True, exist_ok=True)
    for source_name in (
        "research-dashboard-methodology.md",
        "research-dashboard-results.md",
        "research-dashboard-limitations.md",
        "research-dashboard-reproducibility.md",
        "figure-audit.md",
    ):
        source = ROOT / "web/docs" / source_name
        public_docs.joinpath(source_name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return {"panel_rows": len(panel), "definition_count": len(definitions), "source_count": len(manifest["sources"]), "generated_at": now, "git_commit": commit}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(generate(args.output_dir), ensure_ascii=False))


if __name__ == "__main__":
    main()
