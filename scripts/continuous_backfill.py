#!/usr/bin/env python3
"""Small, fail-closed helpers for the descending historical backfill chain.

The module deliberately contains no network or GitHub code.  The workflow uses
these functions after the existing yearly runner has produced a validated
firm-year result.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


AI_KEYWORD_COLUMN = "ai_term_count"
REQUIRED_KEYS = ("company_id", "report_year", "accession_number")

# These aliases are the canonical names emitted by the existing extended-panel
# builder. Historical rows must be converted to this schema before append.
CANONICAL_ALIASES = {
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


STRUCTURAL_COLUMNS = {
    "source_company_id", "sample_order", "batch_id", "report_date", "form",
    "r2_object_key", "warning_count", "has_single_ai_sentence_warning",
    "has_stem_collision_warning", "has_denominator_zero_warning",
    "has_extraction_warning", "has_any_warning", "has_failed_status",
    "panel_start_year", "panel_end_year", "panel_year_count",
    "is_balanced_2020_2025", "has_gap_within_observed_period",
    "ticker_changed_within_panel", "company_name_changed_within_panel",
    "cik_changed_within_panel", "first_observed_year", "last_observed_year",
}


def _add_structural_columns(frame: pd.DataFrame, missing: list[str]) -> pd.DataFrame:
    frame = frame.copy()
    year = pd.to_numeric(frame["report_year"], errors="coerce")
    for column in missing:
        if column == "source_company_id":
            frame[column] = frame["company_id"].astype("string")
        elif column == "report_date":
            frame[column] = frame.get("filing_date", year.astype("string"))
        elif column == "form":
            frame[column] = "10-K"
        elif column in {"sample_order", "batch_id"}:
            frame[column] = pd.Series(range(1, len(frame) + 1), index=frame.index)
        elif column in {"panel_start_year", "panel_end_year", "first_observed_year", "last_observed_year"}:
            frame[column] = year
        elif column == "panel_year_count":
            frame[column] = 1
        elif column == "r2_object_key":
            frame[column] = ""
        elif column.endswith("_lag1") or column.endswith("_change"):
            frame[column] = pd.NA
        else:
            frame[column] = 0
    return frame


def canonicalize_panel(current: pd.DataFrame, prior: pd.DataFrame) -> pd.DataFrame:
    """Apply the existing extended-panel aliases before a cumulative append.

    The prior verified panel is the schema contract. Missing measured columns are
    a hard failure; silently filling them with NA was the cause of the 2019
    publication error.
    """
    frame = current.copy()
    if "ai_disclosure_flag" not in frame.columns:
        if "ai_sentence_count" in frame.columns:
            frame["ai_disclosure_flag"] = (
                pd.to_numeric(frame["ai_sentence_count"], errors="coerce") >= 1
            ).astype("Int64")
        elif "ai_disclosure_binary" in frame.columns:
            frame["ai_disclosure_flag"] = pd.to_numeric(
                frame["ai_disclosure_binary"], errors="coerce"
            ).astype("Int64")
    if "log1p_ai_sentence_count" in prior.columns and "log1p_ai_sentence_count" not in frame.columns:
        counts = pd.to_numeric(frame.get("ai_sentence_count"), errors="coerce")
        if counts is not None:
            if counts.isna().any():
                raise ValueError("ai_sentence_count contains missing values; cannot derive log1p")
            frame["log1p_ai_sentence_count"] = (counts.clip(lower=0) + 1).map(math.log)
    for alias, source in CANONICAL_ALIASES.items():
        if alias not in frame.columns and source in frame.columns:
            frame[alias] = frame[source]
    missing = [column for column in prior.columns if column not in frame.columns]
    structural = [column for column in missing if column in STRUCTURAL_COLUMNS or column.endswith(("_lag1", "_change"))]
    if structural:
        frame = _add_structural_columns(frame, structural)
        missing = [column for column in prior.columns if column not in frame.columns]
    if missing:
        raise ValueError(
            "historical schema incompatible; missing canonical measured columns: "
            + ", ".join(missing)
        )
    # The established panel controls column order. Extra experimental columns
    # are not allowed to change the production schema.
    return frame.loc[:, list(prior.columns)].copy()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def next_year(current_year: int, visited_years: list[int] | set[int], minimum_year: int) -> int | None:
    """Return exactly one lower year, or None at the configured lower bound."""
    candidate = int(current_year) - 1
    visited = {int(year) for year in visited_years}
    if candidate in visited:
        raise ValueError(f"year already visited: {candidate}")
    if candidate >= int(current_year):
        raise ValueError("next year must be lower than current year")
    return candidate if candidate >= int(minimum_year) else None


def update_zero_streak(prior_streak: int, annual_status: str, annual_count) -> int:
    """Update streak only for a fully successful, measured annual result."""
    if annual_status != "success":
        raise ValueError("failed or partial years cannot update zero streak")
    if annual_count is None or isinstance(annual_count, bool):
        raise ValueError("annual AI keyword count is missing")
    try:
        value = int(annual_count)
    except (TypeError, ValueError) as exc:
        raise ValueError("annual AI keyword count must be an integer") from exc
    if value < 0:
        raise ValueError("annual AI keyword count cannot be negative")
    return int(prior_streak) + 1 if value == 0 else 0


def annual_ai_keyword_count(frame: pd.DataFrame, column: str = AI_KEYWORD_COLUMN) -> int:
    """Sum the existing AI keyword mention count without treating missing as zero."""
    if column not in frame.columns:
        raise ValueError(f"AI keyword source column is missing: {column}")
    values = pd.to_numeric(frame[column], errors="coerce")
    if values.isna().any():
        raise ValueError("AI keyword count contains missing or non-numeric values")
    if (values < 0).any():
        raise ValueError("AI keyword count contains negative values")
    return int(values.sum())


def _validate_keys(frame: pd.DataFrame, label: str) -> None:
    missing = [key for key in REQUIRED_KEYS if key not in frame.columns]
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")
    for key in REQUIRED_KEYS:
        if frame[key].isna().any() or (frame[key].astype(str).str.strip() == "").any():
            raise ValueError(f"{label} contains missing {key}")
    if frame.duplicated(list(REQUIRED_KEYS)).any():
        raise ValueError(f"{label} contains duplicate firm-year keys")


def _atomic_write(path: Path, writer) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        writer(temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def append_panel(
    prior_path: Path | None,
    current_path: Path,
    output_csv: Path,
    output_parquet: Path | None = None,
    protected_path: Path | None = None,
    dry_run: bool = False,
) -> dict:
    """Append one validated year and atomically publish CSV/Parquet candidates."""
    current = pd.read_parquet(current_path) if current_path.suffix == ".parquet" else pd.read_csv(current_path)
    _validate_keys(current, "current panel")
    prior = None
    if prior_path and prior_path.exists():
        prior = pd.read_parquet(prior_path) if prior_path.suffix == ".parquet" else pd.read_csv(prior_path)
        _validate_keys(prior, "prior panel")
        current = canonicalize_panel(current, prior)
    combined = pd.concat([prior, current], ignore_index=True) if prior is not None else current
    _validate_keys(combined, "combined panel")
    if protected_path and protected_path.exists():
        protected = pd.read_parquet(protected_path) if protected_path.suffix == ".parquet" else pd.read_csv(protected_path)
        _validate_keys(protected, "protected panel")
        keys = set(zip(protected.company_id.astype(str), protected.report_year.astype(str), protected.accession_number.astype(str)))
        combined_keys = set(zip(combined.company_id.astype(str), combined.report_year.astype(str), combined.accession_number.astype(str)))
        if not keys.issubset(combined_keys):
            raise ValueError("combined candidate dropped protected panel rows")
    combined = combined.sort_values(["report_year", "company_id"], kind="mergesort").reset_index(drop=True)
    result = {"prior_rows": 0 if prior is None else len(prior), "current_rows": len(current), "candidate_rows": len(combined), "validation": "PASS"}
    if dry_run:
        return result
    _atomic_write(output_csv, lambda path: combined.to_csv(path, index=False))
    if output_parquet is not None:
        _atomic_write(output_parquet, lambda path: combined.to_parquet(path, index=False))
    return result


def write_json_atomic(path: Path, payload: dict) -> None:
    _atomic_write(path, lambda temporary: temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"))


def build_state(args: argparse.Namespace, annual_count: int | None, panel_result: dict | None,
                sec_metadata: dict | None = None) -> dict:
    prior_streak = int(args.zero_streak)
    status = args.annual_status
    streak = update_zero_streak(prior_streak, status, annual_count) if not args.dry_run else prior_streak
    current = int(args.current_year)
    visited = [int(value) for value in args.visited_years.split(",") if value.strip()]
    if current not in visited:
        visited.append(current)
    next_value = None if streak >= 3 or args.dry_run else next_year(current, visited, int(args.minimum_year))
    return {
        "chain_id": args.chain_id,
        "sample_namespace": getattr(args, "sample_namespace", "sample_503"),
        "start_year": int(args.start_year),
        "current_year": current,
        "last_completed_year": current if status == "success" else (visited[-2] if len(visited) > 1 else None),
        "processed_year_count": len(visited),
        "visited_years": visited,
        "zero_streak": streak,
        "annual_ai_keyword_count": annual_count,
        "next_year": next_value,
        "status": "completed" if streak >= 3 else status,
        "stop_reason": "three_consecutive_verified_zero_ai_keyword_years" if streak >= 3 else None,
        "panel": panel_result or {},
        "sec_ticker_metadata": sec_metadata or {},
        "generated_at": utc_now(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-panel", type=Path)
    parser.add_argument("--prior-panel", type=Path)
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--output-parquet", type=Path)
    parser.add_argument("--protected-panel", type=Path)
    parser.add_argument("--keyword-column", default=AI_KEYWORD_COLUMN)
    parser.add_argument("--chain-state", type=Path, required=True)
    parser.add_argument("--chain-id", required=True)
    parser.add_argument("--sample-namespace", default="sample_503")
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--current-year", type=int, required=True)
    parser.add_argument("--minimum-year", type=int, default=0)
    parser.add_argument("--zero-streak", type=int, default=0)
    parser.add_argument("--visited-years", default="")
    parser.add_argument("--annual-status", default="success")
    parser.add_argument("--annual-keyword-count", type=int)
    parser.add_argument("--sec-metadata", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    panel_result = None
    count = args.annual_keyword_count
    if args.current_panel:
        frame = pd.read_parquet(args.current_panel) if args.current_panel.suffix == ".parquet" else pd.read_csv(args.current_panel)
        count = annual_ai_keyword_count(frame, args.keyword_column) if count is None else count
        if not args.dry_run:
            if not args.output_csv:
                raise SystemExit("--output-csv is required when publishing a panel")
            panel_result = append_panel(args.prior_panel, args.current_panel, args.output_csv, args.output_parquet, args.protected_panel, False)
    sec_metadata = None
    if args.sec_metadata:
        sec_metadata = json.loads(args.sec_metadata.read_text(encoding="utf-8"))
    state = build_state(args, count, panel_result, sec_metadata)
    if not args.dry_run:
        write_json_atomic(args.chain_state, state)
    print(json.dumps(state, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
