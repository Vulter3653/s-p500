#!/usr/bin/env python3
"""Validate generated annual S&P 500 company and security lists."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SECURITY_ROWS = {2020: 505, 2021: 505, 2022: 503, 2023: 503, 2024: 503, 2025: 503}


def main() -> None:
    manifest_path = ROOT / "data" / "processed" / "annual_constituents_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summaries = {item["sample_year"]: item for item in manifest["snapshots"]}

    for year, expected_security_rows in EXPECTED_SECURITY_ROWS.items():
        companies = pd.read_csv(ROOT / str(year) / "sp500_companies.csv", dtype=str)
        securities = pd.read_csv(ROOT / str(year) / "sp500_securities.csv", dtype=str)
        expected_date = f"{year + 1}-01-01"

        assert len(companies) == 500, (year, "company_rows", len(companies))
        assert len(securities) == expected_security_rows, (
            year,
            "security_rows",
            len(securities),
        )
        assert securities["symbol"].is_unique, (year, "duplicate symbols")
        assert set(companies["snapshot_date"]) == {expected_date}
        assert set(securities["snapshot_date"]) == {expected_date}
        assert summaries[year]["company_rows"] == len(companies)
        assert summaries[year]["security_rows"] == len(securities)

    print("PASS: six annual lists contain 500 companies and expected security rows.")


if __name__ == "__main__":
    main()
