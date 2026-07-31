#!/usr/bin/env python3
"""Create descriptive, change, correlation, and VIF tables."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor


CORE_CONTINUOUS = [
    "ai_sentence_count", "log1p_ai_sentence_count",
    "whole_report_concreteness", "ai_concreteness",
    "past_tense_share", "present_tense_share", "future_tense_share",
    "ai_past_tense_share", "ai_present_tense_share", "ai_future_tense_share",
    "lm_positive_share", "lm_negative_share", "lm_uncertainty_share",
    "passive_voice_sentence_share", "fog_index",
    "ai_lm_positive_share", "ai_lm_negative_share", "ai_lm_uncertainty_share",
    "ai_passive_voice_sentence_share", "ai_fog_index",
    "log_report_word_count", "report_word_count", "numeric_token_share",
    "average_word_length", "lexical_density", "root_type_token_ratio",
]
FULL_CORRELATION = ["ai_disclosure"] + CORE_CONTINUOUS
AI_CORRELATION = [
    "ai_sentence_count", "log1p_ai_sentence_count", "ai_concreteness",
    "ai_past_tense_share", "ai_present_tense_share", "ai_future_tense_share",
    "ai_lm_positive_share", "ai_lm_negative_share", "ai_lm_uncertainty_share",
    "ai_passive_voice_sentence_share", "ai_fog_index", "log_report_word_count",
]
YEARLY_VARIABLES = [
    "ai_disclosure", "ai_sentence_count", "whole_report_concreteness",
    "ai_concreteness", "past_tense_share", "present_tense_share",
    "future_tense_share", "lm_uncertainty_share",
    "passive_voice_sentence_share", "fog_index",
    "ai_lm_positive_share", "ai_lm_negative_share", "ai_lm_uncertainty_share",
    "report_word_count",
]
WITHIN_VARIABLES = [
    "whole_report_concreteness", "past_tense_share", "present_tense_share",
    "future_tense_share", "lm_uncertainty_share",
    "passive_voice_sentence_share", "fog_index", "ai_sentence_count",
    "ai_net_tone",
]
VIF_VARIABLES = [
    "whole_report_concreteness", "lm_uncertainty_share",
    "lm_positive_share", "lm_negative_share", "passive_voice_sentence_share",
    "fog_index", "log_report_word_count", "numeric_token_share",
]


def available(frame: pd.DataFrame, variables: list[str]) -> list[str]:
    return [variable for variable in variables if variable in frame]


def overall_descriptives(frame: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    rows = []
    for variable in variables:
        values = pd.to_numeric(frame[variable], errors="coerce")
        valid = values.dropna()
        rows.append({
            "variable": variable, "N": len(valid), "missing_N": values.isna().sum(),
            "mean": valid.mean(), "standard_deviation": valid.std(ddof=1),
            "minimum": valid.min(), "p25": valid.quantile(.25),
            "median": valid.median(), "p75": valid.quantile(.75),
            "maximum": valid.max(),
        })
    return pd.DataFrame(rows)


def binary_descriptives(frame: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    rows = []
    for variable in variables:
        values = pd.to_numeric(frame[variable], errors="coerce")
        valid = values.dropna()
        rows.append({
            "variable": variable, "N": len(valid), "zero_count": int((valid == 0).sum()),
            "one_count": int((valid == 1).sum()), "one_proportion": (valid == 1).mean(),
            "missing_N": int(values.isna().sum()),
        })
    return pd.DataFrame(rows)


def sample_by_year(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.groupby("report_year", as_index=False).agg(
        firm_year_count=("company_id", "size"),
        unique_company_count=("company_id", "nunique"),
        ai_disclosure_count=("ai_disclosure", "sum"),
        ai_disclosure_rate=("ai_disclosure", "mean"),
    )


def descriptives_by_year(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, group in frame.groupby("report_year", sort=True):
        base = {
            "report_year": year, "firm_year_count": len(group),
            "unique_company_count": group["company_id"].nunique(),
            "ai_disclosure_count": int(group["ai_disclosure"].sum()),
            "ai_disclosure_rate": group["ai_disclosure"].mean(),
        }
        disclosers = group[group["ai_disclosure"] == 1]
        for variable in available(group, YEARLY_VARIABLES):
            base[f"mean_{variable}_all"] = pd.to_numeric(
                group[variable], errors="coerce"
            ).mean()
            if variable.startswith("ai_"):
                base[f"mean_{variable}_disclosers"] = pd.to_numeric(
                    disclosers[variable], errors="coerce"
                ).mean()
        rows.append(base)
    return pd.DataFrame(rows)


def standardized_mean_difference(one: pd.Series, zero: pd.Series):
    one, zero = one.dropna(), zero.dropna()
    if len(one) < 2 or len(zero) < 2:
        return np.nan
    pooled = np.sqrt(((len(one)-1)*one.var(ddof=1)+(len(zero)-1)*zero.var(ddof=1))
                     / (len(one)+len(zero)-2))
    return np.nan if pooled == 0 else (one.mean()-zero.mean())/pooled


def group_comparison(frame: pd.DataFrame) -> pd.DataFrame:
    variables = [
        "whole_report_concreteness", "past_tense_share", "present_tense_share",
        "future_tense_share", "lm_uncertainty_share", "passive_voice_sentence_share",
        "fog_index", "report_word_count", "lm_positive_share", "lm_negative_share",
    ]
    rows = []
    for variable in available(frame, variables):
        one = pd.to_numeric(frame.loc[frame.ai_disclosure == 1, variable], errors="coerce")
        zero = pd.to_numeric(frame.loc[frame.ai_disclosure == 0, variable], errors="coerce")
        test = stats.ttest_ind(one.dropna(), zero.dropna(), equal_var=False)
        rows.append({
            "variable": variable, "disclosure_N": one.notna().sum(),
            "disclosure_mean": one.mean(), "non_disclosure_N": zero.notna().sum(),
            "non_disclosure_mean": zero.mean(), "mean_difference": one.mean()-zero.mean(),
            "standardized_mean_difference": standardized_mean_difference(one, zero),
            "welch_t": test.statistic, "welch_pvalue": test.pvalue,
        })
    return pd.DataFrame(rows)


def aggregate_changes(yearly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    mean_columns = [column for column in yearly if column.startswith("mean_")]
    for column in mean_columns:
        series = yearly.set_index("report_year")[column]
        first = series.iloc[0]
        for year, value in series.items():
            previous = series.get(year - 1, np.nan)
            rows.append({
                "variable": column.removeprefix("mean_"),
                "report_year": year, "mean_value": value,
                "year_over_year_absolute_change": value - previous if pd.notna(previous) else np.nan,
                "year_over_year_change_rate": (
                    (value - previous) / abs(previous)
                    if pd.notna(previous) and previous != 0 else np.nan
                ),
                "change_from_2020": value - first if pd.notna(first) else np.nan,
            })
    return pd.DataFrame(rows)


def within_firm_changes(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ordered = frame.sort_values(["company_id", "report_year"])
    for variable in available(frame, WITHIN_VARIABLES):
        previous_value = ordered.groupby("company_id")[variable].shift()
        previous_year = ordered.groupby("company_id")["report_year"].shift()
        changes = pd.to_numeric(ordered[variable], errors="coerce") - pd.to_numeric(
            previous_value, errors="coerce"
        )
        valid = previous_year.eq(ordered["report_year"] - 1) & changes.notna()
        temp = pd.DataFrame({"report_year": ordered["report_year"], "change": changes})[valid]
        for year, group in temp.groupby("report_year"):
            rows.append({
                "variable": variable, "report_year": year,
                "paired_firm_count": len(group), "mean_within_firm_change": group.change.mean(),
                "median_within_firm_change": group.change.median(),
                "standard_deviation": group.change.std(ddof=1),
                "p25": group.change.quantile(.25), "p75": group.change.quantile(.75),
            })
    return pd.DataFrame(rows)


def correlation_outputs(
    frame: pd.DataFrame, variables: list[str], method: str, sample_name: str
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    variables = available(frame, variables)
    coefficients = pd.DataFrame(index=variables, columns=variables, dtype=float)
    sample_sizes = pd.DataFrame(index=variables, columns=variables, dtype="Int64")
    long_rows = []
    for first in variables:
        for second in variables:
            if first == second:
                pair = pd.DataFrame({first: pd.to_numeric(frame[first], errors="coerce")}).dropna()
            else:
                pair = frame[[first, second]].apply(pd.to_numeric, errors="coerce").dropna()
            n = len(pair)
            if n < 3 or pair[first].nunique() < 2 or pair[second].nunique() < 2:
                coefficient, pvalue = np.nan, np.nan
            elif method == "pearson":
                coefficient, pvalue = stats.pearsonr(pair[first], pair[second])
            else:
                coefficient, pvalue = stats.spearmanr(pair[first], pair[second])
            coefficients.loc[first, second] = coefficient
            sample_sizes.loc[first, second] = n
            if variables.index(first) <= variables.index(second):
                long_rows.append({
                    "sample": sample_name, "method": method, "variable_1": first,
                    "variable_2": second, "correlation": coefficient,
                    "pairwise_N": n, "pvalue": pvalue,
                })
    coefficients.index.name = "variable"
    sample_sizes.index.name = "variable"
    return coefficients, sample_sizes, long_rows


def vif_table(frame: pd.DataFrame) -> pd.DataFrame:
    variables = available(frame, VIF_VARIABLES)
    data = frame[variables].apply(pd.to_numeric, errors="coerce").dropna()
    standardized = (data - data.mean()) / data.std(ddof=0)
    rows = []
    for index, variable in enumerate(variables):
        rows.append({
            "variable": variable, "N": len(standardized),
            "VIF": variance_inflation_factor(standardized.values, index),
        })
    return pd.DataFrame(rows)


def run(panel_path: Path, output_dir: Path) -> dict[str, pd.DataFrame]:
    frame = pd.read_parquet(panel_path)
    tables = output_dir / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    outputs = {
        "table_01_sample_by_year": sample_by_year(frame),
        "table_02_overall_descriptive_statistics": overall_descriptives(
            frame, available(frame, CORE_CONTINUOUS)
        ),
        "table_03_binary_variable_statistics": binary_descriptives(
            frame, ["ai_disclosure"]
        ),
        "table_04_descriptive_statistics_by_year": descriptives_by_year(frame),
        "table_05_ai_disclosure_group_comparison": group_comparison(frame),
    }
    outputs["table_06_year_over_year_aggregate_changes"] = aggregate_changes(
        outputs["table_04_descriptive_statistics_by_year"]
    )
    outputs["table_07_within_firm_annual_changes"] = within_firm_changes(frame)
    pearson_full, n_full, p_full = correlation_outputs(
        frame, FULL_CORRELATION, "pearson", "full_sample"
    )
    spearman_full, _, p_sfull = correlation_outputs(
        frame, FULL_CORRELATION, "spearman", "full_sample"
    )
    ai = frame[frame["ai_disclosure"] == 1]
    pearson_ai, n_ai, p_ai = correlation_outputs(
        ai, AI_CORRELATION, "pearson", "ai_disclosers"
    )
    spearman_ai, _, p_sai = correlation_outputs(
        ai, AI_CORRELATION, "spearman", "ai_disclosers"
    )
    outputs.update({
        "table_08_pearson_correlation_full_sample": pearson_full.reset_index(),
        "table_09_spearman_correlation_full_sample": spearman_full.reset_index(),
        "table_10_pearson_correlation_ai_disclosers": pearson_ai.reset_index(),
        "table_11_spearman_correlation_ai_disclosers": spearman_ai.reset_index(),
    })
    n_long = []
    for sample, matrix in [("full_sample", n_full), ("ai_disclosers", n_ai)]:
        for first in matrix.index:
            for second in matrix.columns:
                if list(matrix.index).index(first) <= list(matrix.columns).index(second):
                    n_long.append({
                        "sample": sample, "variable_1": first, "variable_2": second,
                        "pairwise_N": matrix.loc[first, second],
                    })
    outputs["table_12_pairwise_sample_sizes"] = pd.DataFrame(n_long)
    pvalues = pd.DataFrame(p_full + p_sfull + p_ai + p_sai)
    outputs["table_13_correlation_pvalues"] = pvalues
    high = pvalues[
        pvalues.variable_1.ne(pvalues.variable_2)
        & pvalues["correlation"].abs().ge(.70)
    ].copy()
    high["absolute_correlation"] = high["correlation"].abs()
    outputs["table_14_high_correlation_pairs"] = high.sort_values(
        ["sample", "method", "absolute_correlation"], ascending=[True, True, False]
    )
    outputs["table_15_vif_diagnostics"] = vif_table(frame)
    for name, table in outputs.items():
        table.to_csv(tables / f"{name}.csv", index=False, lineterminator="\n")
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.panel, args.output_dir)
