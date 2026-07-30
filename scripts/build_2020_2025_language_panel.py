#!/usr/bin/env python3
"""Build the read-only 2020-2025 firm-year language panel."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
YEARS = tuple(range(2020, 2026))
EXPECTED_ROWS = {
    2020: 446,
    2021: 462,
    2022: 471,
    2023: 479,
    2024: 487,
    2025: 484,
}
CORE_LAG_VARIABLES = (
    "ai_disclosure_flag",
    "ai_sentence_count",
    "ai_concreteness_mean",
    "report_concreteness_mean",
    "ai_positive_count",
    "ai_negative_count",
    "ai_uncertainty_count",
    "report_positive_count",
    "report_negative_count",
    "report_uncertainty_count",
)
IDENTIFIER_COLUMNS = {
    "company_id",
    "source_company_id",
    "cik",
    "ticker",
    "company_name",
    "accession_number",
    "form",
    "r2_object_key",
}
INTEGER_COLUMNS = {
    "report_year",
    "sample_order",
    "batch_id",
    "ai_disclosure_binary",
    "ai_disclosure_flag",
    "has_extraction_warning",
    "has_single_ai_sentence_warning",
    "has_stem_collision_warning",
    "has_denominator_zero_warning",
    "has_any_warning",
    "has_failed_status",
    "warning_count",
    "panel_start_year",
    "panel_end_year",
    "panel_year_count",
    "is_balanced_2020_2025",
    "first_observed_year",
    "last_observed_year",
    "has_gap_within_observed_period",
    "ticker_changed_within_panel",
    "company_name_changed_within_panel",
    "cik_changed_within_panel",
}


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, dtype=str, keep_default_na=False, **kwargs)


def normalize_cik(value: str) -> str:
    value = str(value).strip()
    if not value:
        return ""
    return value.zfill(10)


def panel_company_id(manifest_row: pd.Series) -> str:
    key = str(manifest_row.get("_company_key", "")).strip()
    if key:
        return key
    cik = normalize_cik(manifest_row.get("cik", ""))
    if cik:
        return f"cik:{cik}"
    raise ValueError("stable company identifier unavailable")


def merge_one_year(root: Path, year: int) -> tuple[pd.DataFrame, dict]:
    sample = root / str(year) / "sample_500"
    result_path = sample / "language_results/company_language_results.csv"
    manifest_path = sample / f"sample_manifest_{year}_500.csv"
    warning_path = sample / "quality_check/warning_cases.csv"
    failed_path = sample / "quality_check/failed_companies.csv"
    r2_path = sample / "r2_storage/html_r2_manifest.csv"

    results = read_csv(result_path)
    manifest = read_csv(manifest_path)
    warnings = read_csv(warning_path)
    failed = read_csv(failed_path)
    r2 = read_csv(r2_path)

    expected = EXPECTED_ROWS[year]
    if len(results) != expected or len(manifest) != expected:
        raise ValueError(f"{year}: expected {expected} rows")
    if set(results["company_id"]) != set(manifest["company_id"]):
        raise ValueError(f"{year}: result/manifest company IDs differ")

    manifest = manifest.copy()
    manifest["source_company_id"] = manifest["company_id"]
    manifest["company_id"] = manifest.apply(panel_company_id, axis=1)
    manifest["cik"] = manifest["cik"].map(normalize_cik)
    keep = [
        "company_id",
        "source_company_id",
        "sample_order",
        "batch_id",
        "report_date",
        "form",
        "r2_object_key",
    ]
    manifest_for_merge = manifest[keep]

    results = results.rename(columns={"company_id": "source_company_id"})
    results["cik"] = results["cik"].map(normalize_cik)
    merged = manifest_for_merge.merge(
        results,
        on="source_company_id",
        how="left",
        validate="one_to_one",
    )
    if merged["accession_number"].eq("").any():
        raise ValueError(f"{year}: missing merged result")

    warning_counts = warnings.groupby("company_id").size().to_dict()
    warning_types = (
        warnings.groupby("company_id")["warning_type"]
        .agg(lambda values: set(values))
        .to_dict()
        if not warnings.empty
        else {}
    )
    failed_ids = set(failed["company_id"]) if not failed.empty else set()
    merged["warning_count"] = merged["source_company_id"].map(
        lambda value: int(warning_counts.get(value, 0))
    )
    merged["has_single_ai_sentence_warning"] = merged[
        "source_company_id"
    ].map(lambda value: int("single_ai_sentence" in warning_types.get(value, set())))
    merged["has_stem_collision_warning"] = merged[
        "source_company_id"
    ].map(lambda value: int("stem_collisions" in warning_types.get(value, set())))
    merged["has_denominator_zero_warning"] = merged[
        "source_company_id"
    ].map(lambda value: int("denominator_zero" in warning_types.get(value, set())))
    merged["has_extraction_warning"] = merged["source_company_id"].map(
        lambda value: int(
            any(
                warning.startswith("extraction")
                or warning.startswith("section")
                for warning in warning_types.get(value, set())
            )
        )
    )
    merged["has_any_warning"] = (merged["warning_count"] > 0).astype(int)
    merged["has_failed_status"] = merged["source_company_id"].isin(
        failed_ids
    ).astype(int)

    r2_keys = r2.set_index("company_id")["object_key"].to_dict()
    expected_keys = merged["source_company_id"].map(r2_keys)
    if not expected_keys.fillna("").eq(merged["r2_object_key"]).all():
        raise ValueError(f"{year}: manifest/R2 object keys differ")

    merged["ai_disclosure_flag"] = pd.to_numeric(
        merged["ai_sentence_count"], errors="coerce"
    ).map(lambda value: pd.NA if pd.isna(value) else int(value >= 1))
    merged["ai_disclosure_flag"] = merged["ai_disclosure_flag"].astype("Int64")

    metadata = {
        "year": year,
        "result_path": result_path.relative_to(root).as_posix(),
        "manifest_path": manifest_path.relative_to(root).as_posix(),
        "warning_path": warning_path.relative_to(root).as_posix(),
        "failed_path": failed_path.relative_to(root).as_posix(),
        "r2_path": r2_path.relative_to(root).as_posix(),
        "rows": len(merged),
        "source_columns": list(results.columns),
    }
    return merged, metadata


def coerce_types(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()
    date_columns = {"filing_date", "report_date"}
    for column in panel.columns:
        if column in IDENTIFIER_COLUMNS or column in date_columns:
            panel[column] = panel[column].astype("string")
            continue
        if column == "log_report_word_count":
            panel[column] = pd.to_numeric(panel[column], errors="coerce")
            continue
        if column in INTEGER_COLUMNS or column.endswith("_count"):
            panel[column] = pd.to_numeric(
                panel[column], errors="coerce"
            ).astype("Int64")
            continue
        if (
            column.endswith("_bytes")
            or column.endswith("_word_count")
            or column.endswith("_sentence_count")
            or column.endswith("_paragraph_count")
            or column.endswith("_token_count")
            or column.endswith("_entries")
        ):
            panel[column] = pd.to_numeric(
                panel[column], errors="coerce"
            ).astype("Int64")
            continue
        if any(
            marker in column
            for marker in (
                "_ratio",
                "_mean",
                "_median",
                "_standard_deviation",
                "_min",
                "_max",
                "_tone",
                "_coverage",
                "per_1000",
                "fog_index",
                "log_report",
            )
        ):
            panel[column] = pd.to_numeric(panel[column], errors="coerce")
        else:
            panel[column] = panel[column].astype("string")
    return panel


def add_panel_structure(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = panel.copy()
    summaries = []
    for company_id, group in panel.groupby("company_id", sort=False):
        group = group.sort_values("report_year")
        years = [int(value) for value in group["report_year"]]
        observed = set(years)
        first, last = min(years), max(years)
        has_gap = any(year not in observed for year in range(first, last + 1))
        summary = {
            "company_id": company_id,
            "cik_first": group.iloc[0]["cik"],
            "ticker_first": group.iloc[0]["ticker"],
            "ticker_last": group.iloc[-1]["ticker"],
            "company_name_first": group.iloc[0]["company_name"],
            "company_name_last": group.iloc[-1]["company_name"],
            "first_observed_year": first,
            "last_observed_year": last,
            "panel_year_count": len(years),
            "is_balanced_2020_2025": int(observed == set(YEARS)),
            "has_gap_within_observed_period": int(has_gap),
            "ticker_changed_within_panel": int(group["ticker"].nunique() > 1),
            "company_name_changed_within_panel": int(
                group["company_name"].nunique() > 1
            ),
            "cik_changed_within_panel": int(group["cik"].nunique() > 1),
            "observed_years": "|".join(map(str, years)),
        }
        summaries.append(summary)
    balance = pd.DataFrame(summaries).sort_values("company_id")
    structure = balance.rename(
        columns={
            "first_observed_year": "panel_start_year",
            "last_observed_year": "panel_end_year",
        }
    )[
        [
            "company_id",
            "panel_start_year",
            "panel_end_year",
            "panel_year_count",
            "is_balanced_2020_2025",
            "has_gap_within_observed_period",
            "ticker_changed_within_panel",
            "company_name_changed_within_panel",
            "cik_changed_within_panel",
        ]
    ]
    panel = panel.merge(structure, on="company_id", validate="many_to_one")
    panel["first_observed_year"] = panel["panel_start_year"]
    panel["last_observed_year"] = panel["panel_end_year"]
    return panel, balance


def add_lags(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.sort_values(
        ["company_id", "report_year", "accession_number"]
    ).copy()
    for variable in CORE_LAG_VARIABLES:
        if variable not in panel.columns:
            raise ValueError(f"required lag variable missing: {variable}")
        panel[variable] = pd.to_numeric(panel[variable], errors="coerce")
        previous_value = panel.groupby("company_id")[variable].shift(1)
        previous_year = panel.groupby("company_id")["report_year"].shift(1)
        consecutive = panel["report_year"] - previous_year == 1
        lag = previous_value.where(consecutive)
        panel[f"{variable}_lag1"] = lag
        panel[f"{variable}_change"] = (panel[variable] - lag).where(
            consecutive & panel[variable].notna() & lag.notna()
        )
    return panel


def variable_group(column: str) -> str:
    if column in IDENTIFIER_COLUMNS:
        return "identifier"
    if column in {"report_year", "filing_date", "report_date"}:
        return "time"
    if column.endswith("_lag1") or column.endswith("_change"):
        return "lag_change"
    if column.startswith("has_") or column == "warning_count":
        return "quality_control"
    if column.startswith("panel_") or column in {
        "is_balanced_2020_2025",
        "first_observed_year",
        "last_observed_year",
        "ticker_changed_within_panel",
        "company_name_changed_within_panel",
        "cik_changed_within_panel",
    }:
        return "panel_structure"
    if column.startswith("ai_concreteness"):
        return "concreteness_ai_level"
    if column.startswith("report_concreteness"):
        return "concreteness_report_level"
    if column.startswith("report_") and any(
        term in column
        for term in (
            "positive",
            "negative",
            "uncertainty",
            "litigious",
            "modal",
            "constraining",
            "tone",
            "sentiment",
            "lm_",
        )
    ):
        return "lm_report_level"
    if column.startswith("ai_") and any(
        term in column
        for term in (
            "positive",
            "negative",
            "uncertainty",
            "litigious",
            "modal",
            "constraining",
            "tone",
            "sentiment",
            "lm_",
        )
    ):
        return "lm_ai_level"
    if column.startswith("ai_") or column.startswith("total_analysis"):
        return "ai_disclosure"
    return "report_control"


def data_type(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series.dtype):
        return "nullable_integer"
    if pd.api.types.is_float_dtype(series.dtype):
        return "float"
    return "string"


def make_dictionary(panel: pd.DataFrame, metadata: list[dict]) -> pd.DataFrame:
    source_columns = set(metadata[0]["source_columns"])
    rows = []
    for column in panel.columns:
        group = variable_group(column)
        source_column = column if column in source_columns else ""
        source_file = (
            "{year}/sample_500/language_results/"
            "company_language_results.csv"
            if source_column
            else "constructed by scripts/build_2020_2025_language_panel.py"
        )
        construction = "copied without value transformation"
        notes = ""
        if column == "company_id":
            source_file = "{year}/sample_500/sample_manifest_{year}_500.csv"
            source_column = "_company_key"
            construction = "stable CIK-based manifest company key"
            notes = "Annual source ID is retained as source_company_id."
        elif column == "source_company_id":
            source_column = "company_id"
            construction = "original annual sample identifier"
        elif column == "ai_disclosure_flag":
            source_column = "ai_sentence_count"
            construction = "1 when direct AI sentence count is at least one; else 0"
            notes = "Original ai_disclosure_binary is retained separately."
        elif column.startswith("has_") or column == "warning_count":
            source_file = (
                "{year}/sample_500/quality_check/"
                "warning_cases.csv or failed_companies.csv"
            )
            source_column = "warning_type or company_id"
            construction = "company-year indicator/count from annual QC files"
        elif column.endswith("_lag1"):
            base = column.removesuffix("_lag1")
            source_column = base
            construction = "previous value only when prior observation is year t-1"
        elif column.endswith("_change"):
            base = column.removesuffix("_change")
            source_column = base
            construction = "current minus lag1; missing across year gaps"
        elif group == "panel_structure":
            source_file = "constructed from firm-year panel"
            source_column = "company_id and report_year"
            construction = "within-company observed-year summary"

        missing_rule = "empty CSV field / null Parquet value retained"
        if column.startswith("has_") or column in {
            "warning_count",
            "ai_disclosure_flag",
        }:
            missing_rule = "0 is substantive; source missing remains null"
        unit = "value"
        if column.endswith("_count"):
            unit = "count"
        elif "ratio" in column or "coverage" in column:
            unit = "proportion"
        elif column.endswith("_flag") or column.startswith("has_"):
            unit = "binary"
        elif column.endswith("_year") or column == "report_year":
            unit = "year"
        rows.append(
            {
                "variable_name": column,
                "variable_label": column.replace("_", " "),
                "variable_group": group,
                "source_file": source_file,
                "source_column": source_column,
                "data_type": data_type(panel[column]),
                "unit": unit,
                "missing_value_rule": missing_rule,
                "construction_rule": construction,
                "notes": notes,
            }
        )
    return pd.DataFrame(rows)


def make_quality(panel: pd.DataFrame) -> pd.DataFrame:
    coverage_columns = [column for column in panel if "coverage" in column]
    coverage_bad = pd.Series(False, index=panel.index)
    for column in coverage_columns:
        values = pd.to_numeric(panel[column], errors="coerce")
        coverage_bad |= values.notna() & ~values.between(0, 1)
    numeric = panel.select_dtypes(include=["number"])
    infinity_rows = (
        pd.Series(False, index=panel.index)
        if numeric.empty
        else pd.Series(np.isinf(numeric.astype(float)).any(axis=1), index=panel.index)
    )
    string_bad = panel.astype("string").apply(
        lambda series: series.str.strip().str.lower().isin(
            {"nan", "none", "null"}
        )
    ).any(axis=1)

    metrics = {
        "total_rows": len(panel),
        "total_unique_companies": panel["company_id"].nunique(),
        "total_years": panel["report_year"].nunique(),
        "min_year": panel["report_year"].min(),
        "max_year": panel["report_year"].max(),
        "duplicate_company_year": panel.duplicated(
            ["company_id", "report_year"]
        ).sum(),
        "duplicate_cik_year": panel.duplicated(["cik", "report_year"]).sum(),
        "duplicate_accession": panel["accession_number"].duplicated().sum(),
        "missing_company_id": panel["company_id"].isna().sum(),
        "missing_cik": panel["cik"].isna().sum(),
        "missing_accession": panel["accession_number"].isna().sum(),
        "missing_report_year": panel["report_year"].isna().sum(),
        "failed_rows": panel["has_failed_status"].sum(),
        "warning_rows": panel["has_any_warning"].sum(),
        "ai_disclosure_rows": panel["ai_disclosure_flag"].eq(1).sum(),
        "ai_non_disclosure_rows": panel["ai_disclosure_flag"].eq(0).sum(),
        "invalid_coverage_rows": coverage_bad.sum(),
        "infinity_rows": infinity_rows.sum(),
        "string_nan_rows": string_bad.sum(),
    }
    rows = [
        {"scope": "all_years", "report_year": "", "metric": key, "value": value}
        for key, value in metrics.items()
    ]
    for year, group in panel.groupby("report_year", sort=True):
        year_metrics = {
            "row_count": len(group),
            "unique_company_count": group["company_id"].nunique(),
            "ai_disclosure_count": group["ai_disclosure_flag"].eq(1).sum(),
            "ai_non_disclosure_count": group["ai_disclosure_flag"].eq(0).sum(),
            "warning_count": group["has_any_warning"].sum(),
            "failed_count": group["has_failed_status"].sum(),
        }
        rows.extend(
            {
                "scope": "report_year",
                "report_year": int(year),
                "metric": key,
                "value": value,
            }
            for key, value in year_metrics.items()
        )
    return pd.DataFrame(rows)


def validate(panel: pd.DataFrame, balance: pd.DataFrame) -> None:
    if len(panel) != sum(EXPECTED_ROWS.values()):
        raise ValueError("panel row count mismatch")
    actual = panel.groupby("report_year").size().to_dict()
    if actual != EXPECTED_ROWS:
        raise ValueError(f"annual row counts differ: {actual}")
    if panel.duplicated(["company_id", "report_year"]).any():
        raise ValueError("duplicate company-year")
    if panel.duplicated(["cik", "report_year"]).any():
        raise ValueError("duplicate CIK-year")
    if panel["accession_number"].duplicated().any():
        raise ValueError("duplicate accession")
    if not panel["report_year"].between(2020, 2025).all():
        raise ValueError("report year outside 2020-2025")
    zero_ai = panel["ai_sentence_count"].eq(0)
    if panel.loc[zero_ai, "ai_concreteness_mean"].notna().any():
        raise ValueError("zero-AI row has AI concreteness")
    for column in [value for value in panel if "coverage" in value]:
        values = pd.to_numeric(panel[column], errors="coerce")
        if (values.notna() & ~values.between(0, 1)).any():
            raise ValueError(f"invalid coverage: {column}")
    numeric = panel.select_dtypes(include=["number"])
    if np.isinf(numeric.astype(float)).any().any():
        raise ValueError("infinite numeric value")
    string_values = panel.astype("string")
    if string_values.apply(
        lambda series: series.str.strip().str.lower().isin(
            {"nan", "none", "null"}
        )
    ).any().any():
        raise ValueError("literal missing-value string")
    for variable in CORE_LAG_VARIABLES:
        lag = panel[f"{variable}_lag1"]
        prior_year = panel.groupby("company_id")["report_year"].shift(1)
        invalid = lag.notna() & (panel["report_year"] - prior_year != 1)
        if invalid.any():
            raise ValueError(f"nonconsecutive lag: {variable}")
    if balance["company_id"].duplicated().any():
        raise ValueError("duplicate balance-summary company")


def build(root: Path, output_dir: Path) -> dict:
    frames = []
    metadata = []
    source_headers = None
    for year in YEARS:
        frame, year_metadata = merge_one_year(root, year)
        header = year_metadata["source_columns"]
        if source_headers is not None and header != source_headers:
            raise ValueError(f"{year}: annual language schema differs")
        source_headers = header
        frames.append(frame)
        metadata.append(year_metadata)

    panel = pd.concat(frames, ignore_index=True, sort=False)
    panel = coerce_types(panel)
    panel, balance = add_panel_structure(panel)
    panel = add_lags(panel)
    panel = panel.sort_values(
        ["company_id", "report_year", "accession_number"]
    ).reset_index(drop=True)
    validate(panel, balance)

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "firm_year_language_panel.csv"
    parquet_path = output_dir / "firm_year_language_panel.parquet"
    panel.to_csv(
        csv_path,
        index=False,
        na_rep="",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    panel.to_parquet(parquet_path, index=False, engine="pyarrow")
    dictionary = make_dictionary(panel, metadata)
    dictionary.to_csv(
        output_dir / "panel_variable_dictionary.csv",
        index=False,
        lineterminator="\n",
    )
    quality = make_quality(panel)
    quality.to_csv(
        output_dir / "panel_quality_summary.csv",
        index=False,
        lineterminator="\n",
    )
    balance.to_csv(
        output_dir / "panel_balance_summary.csv",
        index=False,
        lineterminator="\n",
    )

    parquet = pd.read_parquet(parquet_path, engine="pyarrow")
    if len(parquet) != len(panel):
        raise ValueError("CSV/Parquet row count mismatch")
    key = ["company_id", "report_year", "accession_number"]
    if not parquet[key].equals(panel[key]):
        raise ValueError("CSV/Parquet key mismatch")

    balanced = int(balance["is_balanced_2020_2025"].sum())
    summary = {
        "input_years": "2020|2021|2022|2023|2024|2025",
        **{f"rows_{year}": EXPECTED_ROWS[year] for year in YEARS},
        "panel_rows": len(panel),
        "unique_companies": panel["company_id"].nunique(),
        "balanced_companies": balanced,
        "unbalanced_companies": len(balance) - balanced,
        "mean_years_per_company": round(
            float(balance["panel_year_count"].mean()), 6
        ),
        "min_years_per_company": int(balance["panel_year_count"].min()),
        "max_years_per_company": int(balance["panel_year_count"].max()),
        "ai_disclosure_firm_years": int(panel["ai_disclosure_flag"].sum()),
        "ai_non_disclosure_firm_years": int(
            panel["ai_disclosure_flag"].eq(0).sum()
        ),
        "warning_firm_years": int(panel["has_any_warning"].sum()),
        "failed_firm_years": int(panel["has_failed_status"].sum()),
        "lag_change_variables": "|".join(CORE_LAG_VARIABLES),
        "annual_results_modified": "append_only_recovered_firm_years",
        "annual_existing_rows_modified": "no",
        "original_html_used": "no",
        "language_remeasurement": "no",
    }
    (output_dir / "run_summary.md").write_text(
        "# 2020-2025 Firm-Year Language Panel Run Summary\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in summary.items())
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "panel_2020_2025",
    )
    args = parser.parse_args()
    build(args.root.resolve(), args.output_dir.resolve())
