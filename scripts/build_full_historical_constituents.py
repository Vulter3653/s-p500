#!/usr/bin/env python3
"""Reconstruct annual S&P 500 snapshots for the full source-supported period.

The historical-components CSV is the membership source of truth. Wikipedia's
current table and selected changes, the SEC ticker snapshot, and the existing
legacy map are used only to enrich identifiers and descriptive metadata.
Existing 2020-2025 outputs are not overwritten unless --overwrite-existing is
explicitly supplied.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from datetime import date
from pathlib import Path

import pandas as pd

from build_annual_constituents import (
    HISTORICAL_COMPONENTS_URL,
    HISTORICAL_TICKER_METADATA,
    SEC_TICKERS_URL,
    SOURCE_URL,
    clean_symbol,
    fetch_source,
    fetch_url,
    load_components,
    normalize_components,
    sec_ticker_map,
)


def load_history(content: bytes) -> pd.DataFrame:
    history = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False)
    required = {"date", "tickers"}
    missing = required - set(history.columns)
    if missing:
        raise ValueError(f"historical source missing columns: {sorted(missing)}")
    history["date"] = pd.to_datetime(history["date"], errors="coerce")
    history = history.loc[history["date"].notna() & history["tickers"].ne("")].copy()
    if history.empty:
        raise ValueError("historical source contains no usable rows")
    history = history.sort_values("date", kind="stable").drop_duplicates("date", keep="last")
    return history.reset_index(drop=True)


def supported_years(history: pd.DataFrame, start_year: int | None, end_year: int | None) -> list[int]:
    earliest_date = history["date"].min().date()
    latest_date = history["date"].max().date()

    # Research-year t uses the latest membership record on or before t+1-01-01.
    earliest_supported = earliest_date.year - 1 if earliest_date.month == 1 and earliest_date.day == 1 else earliest_date.year
    latest_supported = latest_date.year - 1 if latest_date.month == 1 and latest_date.day == 1 else latest_date.year

    first = earliest_supported if start_year is None else max(start_year, earliest_supported)
    last = latest_supported if end_year is None else min(end_year, latest_supported)
    if first > last:
        raise ValueError(
            f"requested range has no source-supported years: requested={start_year}-{end_year}, "
            f"supported={earliest_supported}-{latest_supported}"
        )
    return list(range(first, last + 1))


def ticker_set_at(history: pd.DataFrame, snapshot: pd.Timestamp) -> tuple[pd.Timestamp, list[str]]:
    eligible = history.loc[history["date"] <= snapshot]
    if eligible.empty:
        raise ValueError(f"no historical row on or before {snapshot.date()}")
    row = eligible.iloc[-1]
    tickers = sorted({clean_symbol(value) for value in str(row["tickers"]).split(",") if clean_symbol(value)})
    if not tickers:
        raise ValueError(f"empty ticker set for {snapshot.date()}")
    return row["date"], tickers


def metadata_lookup(current: pd.DataFrame, sec_map: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    lookup = {row["symbol"]: row.to_dict() for _, row in current.iterrows()}
    for symbol, values in sec_map.items():
        lookup.setdefault(
            symbol,
            {
                "symbol": symbol,
                "security": values.get("security", ""),
                "gics_sector": "",
                "gics_sub_industry": "",
                "headquarters": "",
                "date_added": "",
                "cik": values.get("cik", ""),
                "founded": "",
                "metadata_status": "sec_current_ticker_snapshot",
            },
        )
    for symbol, (security, cik) in HISTORICAL_TICKER_METADATA.items():
        lookup.setdefault(
            symbol,
            {
                "symbol": symbol,
                "security": security,
                "gics_sector": "",
                "gics_sub_industry": "",
                "headquarters": "",
                "date_added": "",
                "cik": cik,
                "founded": "",
                "metadata_status": "curated_legacy_ticker_map",
            },
        )
    return lookup


def build_rows(year: int, snapshot: pd.Timestamp, source_row_date: pd.Timestamp, tickers: list[str], lookup: dict[str, dict[str, str]]) -> pd.DataFrame:
    rows: list[dict[str, str | int]] = []
    for symbol in tickers:
        metadata = lookup.get(symbol, {})
        rows.append(
            {
                "sample_year": year,
                "snapshot_date": snapshot.date().isoformat(),
                "historical_source_date": source_row_date.date().isoformat(),
                "symbol": symbol,
                "security": metadata.get("security", ""),
                "gics_sector": metadata.get("gics_sector", ""),
                "gics_sub_industry": metadata.get("gics_sub_industry", ""),
                "headquarters": metadata.get("headquarters", ""),
                "date_added": metadata.get("date_added", ""),
                "cik": metadata.get("cik", ""),
                "founded": metadata.get("founded", ""),
                "metadata_status": metadata.get("metadata_status", "historical_membership_only"),
                "membership_source": HISTORICAL_COMPONENTS_URL,
                "metadata_source": SOURCE_URL if symbol in lookup else "",
            }
        )
    return pd.DataFrame(rows)


def company_frame(securities: pd.DataFrame) -> pd.DataFrame:
    frame = securities.copy()
    frame["_company_key"] = frame.apply(
        lambda row: f"cik:{row['cik']}" if row["cik"] else f"symbol:{row['symbol']}", axis=1
    )

    def join_unique(values: pd.Series) -> str:
        return "|".join(dict.fromkeys(value for value in values.astype(str) if value))

    columns = [
        "sample_year", "snapshot_date", "historical_source_date", "symbol", "security",
        "gics_sector", "gics_sub_industry", "headquarters", "date_added", "cik",
        "founded", "metadata_status", "membership_source", "metadata_source",
    ]
    aggregations = {column: ("first" if column in {"sample_year", "snapshot_date", "historical_source_date", "cik", "membership_source"} else join_unique) for column in columns}
    return frame.groupby("_company_key", as_index=False, sort=False).agg(aggregations).sort_values(["security", "symbol"], kind="stable")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-date", default=date.today().isoformat())
    parser.add_argument("--start-year", type=int)
    parser.add_argument("--end-year", type=int)
    parser.add_argument("--overwrite-existing", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    raw = root / "data" / "raw"
    wiki_path = raw / f"wikipedia_sp500_{args.source_date}.html"
    sec_path = raw / f"sec_company_tickers_{args.source_date}.json"
    historical_path = raw / f"sp500_historical_components_{args.source_date}.csv"

    wiki_content = wiki_path.read_bytes() if wiki_path.exists() else fetch_source(wiki_path)
    sec_content = sec_path.read_bytes() if sec_path.exists() else fetch_url(SEC_TICKERS_URL, sec_path)
    historical_content = historical_path.read_bytes() if historical_path.exists() else fetch_url(HISTORICAL_COMPONENTS_URL, historical_path)

    history = load_history(historical_content)
    years = supported_years(history, args.start_year, args.end_year)
    current = normalize_components(load_components(wiki_content))
    lookup = metadata_lookup(current, sec_ticker_map(sec_content))

    audit_rows: list[dict[str, object]] = []
    skipped_existing: list[int] = []
    for year in years:
        year_dir = root / str(year)
        securities_path = year_dir / "sp500_securities.csv"
        companies_path = year_dir / "sp500_companies.csv"
        if not args.overwrite_existing and (securities_path.exists() or companies_path.exists()):
            skipped_existing.append(year)
            continue

        snapshot = pd.Timestamp(year=year + 1, month=1, day=1)
        source_row_date, tickers = ticker_set_at(history, snapshot)
        securities = build_rows(year, snapshot, source_row_date, tickers, lookup)
        companies = company_frame(securities)
        year_dir.mkdir(parents=True, exist_ok=True)
        securities.to_csv(securities_path, index=False, quoting=csv.QUOTE_MINIMAL)
        companies.to_csv(companies_path, index=False, quoting=csv.QUOTE_MINIMAL)
        audit_rows.append(
            {
                "sample_year": year,
                "snapshot_date": snapshot.date().isoformat(),
                "historical_source_date": source_row_date.date().isoformat(),
                "security_rows": len(securities),
                "company_rows": len(companies),
                "rows_with_cik": int(securities["cik"].ne("").sum()),
                "rows_missing_cik": int(securities["cik"].eq("").sum()),
                "membership_only_rows": int(securities["metadata_status"].eq("historical_membership_only").sum()),
                "security_output": str(securities_path.relative_to(root)),
                "company_output": str(companies_path.relative_to(root)),
            }
        )

    manifest = {
        "generated_on": date.today().isoformat(),
        "source_retrieved_on": args.source_date,
        "supported_first_year": years[0],
        "supported_last_year": years[-1],
        "requested_start_year": args.start_year,
        "requested_end_year": args.end_year,
        "overwrite_existing": args.overwrite_existing,
        "skipped_existing_years": skipped_existing,
        "historical_components_url": HISTORICAL_COMPONENTS_URL,
        "historical_components_sha256": hashlib.sha256(historical_content).hexdigest(),
        "wikipedia_url": SOURCE_URL,
        "wikipedia_sha256": hashlib.sha256(wiki_content).hexdigest(),
        "sec_tickers_url": SEC_TICKERS_URL,
        "sec_tickers_sha256": hashlib.sha256(sec_content).hexdigest(),
        "method": "latest historical membership row on or before research-year plus one January 1; metadata enrichment is non-authoritative",
        "generated_snapshots": audit_rows,
    }
    output = root / "data" / "processed" / "full_historical_constituents_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
