#!/usr/bin/env python3
"""Build annual S&P 500 constituent snapshots from the English Wikipedia tables."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd


SOURCE_URL = (
    "https://en.wikipedia.org/w/index.php?"
    "title=List_of_S%26P_500_companies&printable=yes"
)
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
HISTORICAL_COMPONENTS_URL = (
    "https://raw.githubusercontent.com/fja05680/sp500/master/"
    "S%26P%20500%20Historical%20Components%20%26%20Changes%20(Updated).csv"
)
USER_AGENT = "s-p500-research/0.5 (annual constituent reconstruction)"
YEARS = range(2020, 2026)
HISTORICAL_TICKER_METADATA = {
    "ABC": ("AmerisourceBergen", "0001140859"),
    "ANTM": ("Anthem", "0001156039"),
    "BK": ("Bank of New York Mellon", "0001390777"),
    "BLL": ("Ball Corporation", "0000009389"),
    "COG": ("Cabot Oil & Gas", "0000858470"),
    "FB": ("Facebook", "0001326801"),
    "FI": ("Fiserv", "0000798354"),
    "LB": ("L Brands", "0000701985"),
    "MMC": ("Marsh & McLennan", "0000062709"),
    "NLOK": ("NortonLifeLock", "0000849399"),
    "PARA": ("Paramount Global", "0000813828"),
    "PEAK": ("Healthpeak Properties", "0000765880"),
    "PKI": ("PerkinElmer", "0000031791"),
    "VIAC": ("ViacomCBS", "0000813828"),
    "WRK": ("WestRock", "0001732845"),
}


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def clean_symbol(value: object) -> str:
    return clean_text(value).replace(".", "-")


def flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result.columns = [
        clean_text(column[-1] if isinstance(column, tuple) else column)
        for column in result.columns
    ]
    return result


def fetch_source(path: Path) -> bytes:
    request = Request(SOURCE_URL, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        content = response.read()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return content


def fetch_url(url: str, path: Path) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        content = response.read()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return content


def load_components(content: bytes) -> pd.DataFrame:
    tables = [flatten_columns(table) for table in pd.read_html(io.BytesIO(content))]
    return next(
        table for table in tables if {"Symbol", "Security", "CIK"}.issubset(table.columns)
    )


def parse_changes(content: bytes) -> pd.DataFrame:
    raw_tables = pd.read_html(io.BytesIO(content))
    raw = next(
        table
        for table in raw_tables
        if isinstance(table.columns, pd.MultiIndex)
        and ("Added", "Ticker") in table.columns
        and ("Removed", "Ticker") in table.columns
    )
    changes = pd.DataFrame(
        {
            "effective_date": pd.to_datetime(
                raw[("Effective Date", "Effective Date")], errors="coerce"
            ),
            "added_symbol": raw[("Added", "Ticker")].map(clean_symbol),
            "added_security": raw[("Added", "Security")].map(clean_text),
            "removed_symbol": raw[("Removed", "Ticker")].map(clean_symbol),
            "removed_security": raw[("Removed", "Security")].map(clean_text),
            "reason": raw[("Reason", "Reason")].map(clean_text),
        }
    )
    return changes.dropna(subset=["effective_date"]).sort_values(
        "effective_date", ascending=False
    )


def normalize_components(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = frame.rename(
        columns={
            "Symbol": "symbol",
            "Security": "security",
            "GICS Sector": "gics_sector",
            "GICS Sub-Industry": "gics_sub_industry",
            "Headquarters Location": "headquarters",
            "Date added": "date_added",
            "CIK": "cik",
            "Founded": "founded",
        }
    )
    columns = [
        "symbol",
        "security",
        "gics_sector",
        "gics_sub_industry",
        "headquarters",
        "date_added",
        "cik",
        "founded",
    ]
    result = renamed[columns].copy()
    result["symbol"] = result["symbol"].map(clean_symbol)
    for column in set(columns) - {"symbol"}:
        result[column] = result[column].map(clean_text)
    result["cik"] = result["cik"].str.replace(r"\.0$", "", regex=True).str.zfill(10)
    result.loc[result["cik"] == "0000000000", "cik"] = ""
    result["metadata_status"] = "current_table"
    return result


def sec_ticker_map(content: bytes) -> dict[str, dict[str, str]]:
    records = json.loads(content)
    return {
        clean_symbol(record["ticker"]): {
            "cik": str(record["cik_str"]).zfill(10),
            "security": clean_text(record["title"]),
        }
        for record in records.values()
    }


def historical_ticker_sets(content: bytes) -> dict[int, set[str]]:
    history = pd.read_csv(io.BytesIO(content))
    history["date"] = pd.to_datetime(history["date"], errors="coerce")
    result: dict[int, set[str]] = {}
    for year in YEARS:
        snapshot_date = pd.Timestamp(year=year + 1, month=1, day=1)
        eligible = history.loc[history["date"] <= snapshot_date]
        if eligible.empty:
            raise ValueError(f"No historical constituent row for {snapshot_date.date()}")
        tickers = eligible.iloc[-1]["tickers"].split(",")
        result[year] = {clean_symbol(ticker) for ticker in tickers}
    return result


def reverse_change(
    constituents: dict[str, dict[str, str]], change: pd.Series
) -> None:
    added_symbol = change["added_symbol"]
    removed_symbol = change["removed_symbol"]

    if added_symbol:
        constituents.pop(added_symbol, None)

    if removed_symbol:
        existing = constituents.get(removed_symbol, {})
        restored = {
            "symbol": removed_symbol,
            "security": change["removed_security"],
            "gics_sector": existing.get("gics_sector", ""),
            "gics_sub_industry": existing.get("gics_sub_industry", ""),
            "headquarters": existing.get("headquarters", ""),
            "date_added": existing.get("date_added", ""),
            "cik": existing.get("cik", ""),
            "founded": existing.get("founded", ""),
            "metadata_status": (
                existing.get("metadata_status", "restored_from_change_history")
            ),
        }
        constituents[removed_symbol] = restored


def write_snapshot(
    year: int,
    snapshot_date: date,
    constituents: dict[str, dict[str, str]],
    root: Path,
    sec_map: dict[str, dict[str, str]],
    validated_tickers: set[str],
) -> dict[str, object]:
    frame = pd.DataFrame(constituents.values())
    reconstructed_tickers = set(frame["symbol"])
    frame = frame.loc[frame["symbol"].isin(validated_tickers)].copy()
    missing_tickers = sorted(validated_tickers - reconstructed_tickers)
    if missing_tickers:
        additions = []
        for symbol in missing_tickers:
            sec_match = sec_map.get(symbol, {})
            legacy_security, legacy_cik = HISTORICAL_TICKER_METADATA.get(
                symbol, ("", "")
            )
            additions.append(
                {
                    "symbol": symbol,
                    "security": sec_match.get("security", legacy_security),
                    "gics_sector": "",
                    "gics_sub_industry": "",
                    "headquarters": "",
                    "date_added": "",
                    "cik": sec_match.get("cik", legacy_cik),
                    "founded": "",
                    "metadata_status": "added_from_historical_validation",
                }
            )
        frame = pd.concat([frame, pd.DataFrame(additions)], ignore_index=True)
    for index, row in frame.loc[frame["cik"].eq("")].iterrows():
        match = sec_map.get(row["symbol"])
        if match:
            frame.at[index, "cik"] = match["cik"]
            frame.at[index, "metadata_status"] = "cik_enriched_from_sec_ticker_map"
    frame.insert(0, "sample_year", year)
    frame.insert(1, "snapshot_date", snapshot_date.isoformat())
    frame["source_url"] = SOURCE_URL
    frame = frame.sort_values(["security", "symbol"], kind="stable")
    security_output = root / str(year) / "sp500_securities.csv"
    security_output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(security_output, index=False, encoding="utf-8")

    frame["_company_key"] = frame.apply(
        lambda row: (
            f"cik:{row['cik']}"
            if row["cik"]
            else (
                f"name:{row['security'].casefold()}"
                if row["security"]
                else f"symbol:{row['symbol']}"
            )
        ),
        axis=1,
    )

    def join_unique(values: pd.Series) -> str:
        return "|".join(dict.fromkeys(value for value in values if value))

    companies = (
        frame.groupby("_company_key", sort=False, as_index=False)
        .agg(
            {
                "sample_year": "first",
                "snapshot_date": "first",
                "symbol": join_unique,
                "security": join_unique,
                "gics_sector": join_unique,
                "gics_sub_industry": join_unique,
                "headquarters": join_unique,
                "date_added": join_unique,
                "cik": "first",
                "founded": join_unique,
                "metadata_status": join_unique,
                "source_url": "first",
            }
        )
        .sort_values(["security", "symbol"], kind="stable")
    )
    company_output = root / str(year) / "sp500_companies.csv"
    companies.to_csv(company_output, index=False, encoding="utf-8")

    cik_count = int(frame["cik"].ne("").sum())
    unique_ciks = int(frame.loc[frame["cik"].ne(""), "cik"].nunique())
    return {
        "sample_year": year,
        "snapshot_date": snapshot_date.isoformat(),
        "security_rows": len(frame),
        "company_rows": len(companies),
        "rows_with_cik": cik_count,
        "unique_known_ciks": unique_ciks,
        "rows_missing_cik": int(frame["cik"].eq("").sum()),
        "duplicate_known_cik_rows": cik_count - unique_ciks,
        "reverse_only_tickers_removed": sorted(
            reconstructed_tickers - validated_tickers
        ),
        "validation_only_tickers_added": missing_tickers,
        "company_output": str(company_output.relative_to(root)),
        "security_audit_output": str(security_output.relative_to(root)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-date", default=date.today().isoformat())
    args = parser.parse_args()

    root = args.root.resolve()
    raw_path = root / "data" / "raw" / f"wikipedia_sp500_{args.source_date}.html"
    content = fetch_source(raw_path)
    sec_raw_path = root / "data" / "raw" / f"sec_company_tickers_{args.source_date}.json"
    sec_content = fetch_url(SEC_TICKERS_URL, sec_raw_path)
    sec_map = sec_ticker_map(sec_content)
    historical_raw_path = (
        root
        / "data"
        / "raw"
        / f"sp500_historical_components_{args.source_date}.csv"
    )
    historical_content = fetch_url(HISTORICAL_COMPONENTS_URL, historical_raw_path)
    validated_ticker_sets = historical_ticker_sets(historical_content)
    components_raw = load_components(content)
    components = normalize_components(components_raw)
    changes = parse_changes(content)

    constituents = {
        row["symbol"]: row.to_dict() for _, row in components.iterrows()
    }
    summaries: list[dict[str, object]] = []
    for year in reversed(list(YEARS)):
        snapshot_date = date(year + 1, 1, 1)
        for _, change in changes[
            changes["effective_date"].dt.date > snapshot_date
        ].iterrows():
            reverse_change(constituents, change)
        changes = changes[changes["effective_date"].dt.date <= snapshot_date]
        summaries.append(
            write_snapshot(
                year,
                snapshot_date,
                constituents,
                root,
                sec_map,
                validated_ticker_sets[year],
            )
        )

    manifest = {
        "generated_on": date.today().isoformat(),
        "source_retrieved_on": args.source_date,
        "source_url": SOURCE_URL,
        "source_sha256": hashlib.sha256(content).hexdigest(),
        "sec_tickers_url": SEC_TICKERS_URL,
        "sec_tickers_sha256": hashlib.sha256(sec_content).hexdigest(),
        "historical_components_url": HISTORICAL_COMPONENTS_URL,
        "historical_components_sha256": hashlib.sha256(
            historical_content
        ).hexdigest(),
        "method": "reverse changes with effective_date later than each snapshot_date",
        "snapshots": list(reversed(summaries)),
    }
    manifest_path = root / "data" / "processed" / "annual_constituents_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
