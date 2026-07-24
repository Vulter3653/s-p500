#!/usr/bin/env python3
"""Validate generated annual S&P 500 company and security lists."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SECURITY_ROWS = {2020: 505, 2021: 505, 2022: 503, 2023: 503, 2024: 503, 2025: 503}
SECURITY_COLUMNS = {
    "sample_year",
    "snapshot_date",
    "symbol",
    "security",
    "gics_sector",
    "gics_sub_industry",
    "headquarters",
    "date_added",
    "cik",
    "founded",
    "metadata_status",
    "source_url",
}
COMPANY_COLUMNS = {"_company_key", *SECURITY_COLUMNS}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    manifest_path = ROOT / "data" / "processed" / "annual_constituents_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summaries = {item["sample_year"]: item for item in manifest["snapshots"]}
    assert set(summaries) == set(EXPECTED_SECURITY_ROWS), "manifest snapshot years"

    raw_sources = {
        "source_sha256": ROOT / "data" / "raw" / "wikipedia_sp500_2026-07-24.html",
        "sec_tickers_sha256": ROOT / "data" / "raw" / "sec_company_tickers_2026-07-24.json",
        "historical_components_sha256": (
            ROOT / "data" / "raw" / "sp500_historical_components_2026-07-24.csv"
        ),
    }
    for hash_field, source_path in raw_sources.items():
        assert source_path.is_file(), ("missing raw source", source_path)
        assert sha256(source_path) == manifest[hash_field], (
            "raw source hash mismatch",
            source_path,
        )

    for year, expected_security_rows in EXPECTED_SECURITY_ROWS.items():
        companies = pd.read_csv(ROOT / str(year) / "sp500_companies.csv", dtype=str)
        securities = pd.read_csv(ROOT / str(year) / "sp500_securities.csv", dtype=str)
        expected_date = f"{year + 1}-01-01"

        assert set(companies.columns) == COMPANY_COLUMNS, (year, "company columns")
        assert set(securities.columns) == SECURITY_COLUMNS, (year, "security columns")
        assert len(companies) == 500, (year, "company_rows", len(companies))
        assert len(securities) == expected_security_rows, (
            year,
            "security_rows",
            len(securities),
        )
        assert companies["_company_key"].notna().all(), (year, "missing company key")
        assert companies["_company_key"].is_unique, (year, "duplicate company key")
        assert companies["symbol"].notna().all(), (year, "missing company symbol")
        assert securities["symbol"].notna().all(), (year, "missing security symbol")
        assert securities["symbol"].is_unique, (year, "duplicate symbols")
        known_ciks = pd.concat([companies["cik"], securities["cik"]]).dropna()
        assert known_ciks.str.fullmatch(r"\d{10}").all(), (year, "invalid CIK format")
        assert set(companies["sample_year"]) == {str(year)}
        assert set(securities["sample_year"]) == {str(year)}
        assert set(companies["snapshot_date"]) == {expected_date}
        assert set(securities["snapshot_date"]) == {expected_date}
        assert summaries[year]["company_rows"] == len(companies)
        assert summaries[year]["security_rows"] == len(securities)
        assert summaries[year]["company_output"] == f"{year}/sp500_companies.csv"
        assert summaries[year]["security_audit_output"] == f"{year}/sp500_securities.csv"

    print(
        "PASS: annual schemas, keys, dates, row counts, manifest paths, "
        "CIK formats, and raw-source hashes are valid."
    )


if __name__ == "__main__":
    main()
