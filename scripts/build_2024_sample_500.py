#!/usr/bin/env python3
"""Build the ordered 2024 S&P 500 manifest using exact reportDate 10-Ks."""

from __future__ import annotations

import argparse
import csv
import re
from datetime import date
from pathlib import Path

try:
    from sec_client import SecClient, normalize_cik
    from select_2025_10k_filings import merge_filings
except ModuleNotFoundError:
    from scripts.sec_client import SecClient, normalize_cik
    from scripts.select_2025_10k_filings import merge_filings


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://data.sec.gov/submissions"
ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def eligible_filing(client: SecClient, cik: str) -> tuple[dict | None, str]:
    response = client.get_json(f"{BASE}/CIK{cik}.json", cik)
    if normalize_cik(response.get("cik", "")) != cik:
        raise ValueError(f"SEC CIK mismatch for {cik}")
    parts = [("recent", response.get("filings", {}).get("recent", {}))]
    for fragment in response.get("filings", {}).get("files", []):
        start = str(fragment.get("filingFrom", ""))
        end = str(fragment.get("filingTo", ""))
        if start and end and (end < "2024-01-01" or start > "2026-07-30"):
            continue
        name = str(fragment.get("name", ""))
        if name:
            parts.append((name, client.get_json(f"{BASE}/{name}", cik)))
    candidates = []
    for row in merge_filings(parts):
        if row.get("form") != "10-K":
            continue
        try:
            report = date.fromisoformat(str(row.get("reportDate", "")))
            filing = date.fromisoformat(str(row.get("filingDate", "")))
        except ValueError:
            continue
        accession = str(row.get("accessionNumber", ""))
        primary = str(row.get("primaryDocument", "")).strip()
        if (
            report.year == 2024
            and filing <= date(2026, 7, 30)
            and ACCESSION_RE.fullmatch(accession)
            and primary
        ):
            candidates.append(row)
    if len(candidates) != 1:
        reason = (
            "no_unique_eligible_2024_report_date_10k"
            if not candidates
            else "ambiguous_multiple_eligible_2024_report_date_10k"
        )
        return None, reason
    row = candidates[0]
    return (
        {
            "accession_number": row["accessionNumber"],
            "primary_document": row["primaryDocument"],
            "form": row["form"],
            "filing_date": row["filingDate"],
            "report_date": row["reportDate"],
        },
        "",
    )


def build(root: Path, output: Path) -> None:
    universe_path = root / "2024/sp500_companies.csv"
    with universe_path.open(encoding="utf-8-sig", newline="") as handle:
        universe = list(csv.DictReader(handle))
    if len(universe) != 500:
        raise ValueError(f"expected 500 universe rows, got {len(universe)}")

    client = SecClient(
        root / "2024/sample_500/cache/sec_submissions",
        root / "2024/sample_500/metadata/sec_requests.jsonl",
    )
    accepted: list[dict] = []
    excluded: list[dict] = []
    for universe_order, company in enumerate(universe, 1):
        raw_cik = company.get("cik", "").strip()
        if not raw_cik:
            excluded.append(
                {
                    "universe_order": universe_order,
                    "_company_key": company["_company_key"],
                    "ticker": company["symbol"],
                    "company_name": company["security"],
                    "cik": "",
                    "reason": "cik_missing_in_2024_universe",
                }
            )
            continue
        cik = normalize_cik(raw_cik)
        filing, reason = eligible_filing(client, cik)
        if filing is None:
            excluded.append(
                {
                    "universe_order": universe_order,
                    "_company_key": company["_company_key"],
                    "ticker": company["symbol"],
                    "company_name": company["security"],
                    "cik": cik,
                    "reason": reason,
                }
            )
            continue
        accepted.append(
            {
                "universe_order": universe_order,
                "company": company,
                "filing": filing,
            }
        )

    fields = [
        "sample_order",
        "company_id",
        "final_sample_id",
        "ticker",
        "symbol",
        "company_name",
        "security",
        "_company_key",
        "cik",
        "gics_sector",
        "gics_sub_industry",
        "accession_number",
        "primary_document",
        "form",
        "filing_date",
        "report_date",
        "report_year",
        "filing_url",
        "source_manifest",
        "sample_group",
        "batch_id",
        "r2_object_key",
        "universe_order",
    ]
    rows = []
    for sample_order, item in enumerate(accepted, 1):
        company = item["company"]
        filing = item["filing"]
        cik = normalize_cik(company["cik"])
        company_id = f"S2024-{sample_order:03d}"
        accession = filing["accession_number"]
        rows.append(
            {
                "sample_order": sample_order,
                "company_id": company_id,
                "final_sample_id": company_id,
                "ticker": company["symbol"],
                "symbol": company["symbol"],
                "company_name": company["security"],
                "security": company["security"],
                "_company_key": company["_company_key"],
                "cik": cik,
                "gics_sector": company["gics_sector"],
                "gics_sub_industry": company["gics_sub_industry"],
                "accession_number": accession,
                "primary_document": filing["primary_document"],
                "form": filing["form"],
                "filing_date": filing["filing_date"],
                "report_date": filing["report_date"],
                "report_year": "2024",
                "filing_url": (
                    "https://www.sec.gov/Archives/edgar/data/"
                    f"{int(cik)}/{accession.replace('-', '')}/"
                    f"{filing['primary_document']}"
                ),
                "source_manifest": "2024/sp500_companies.csv",
                "sample_group": "sample_2024",
                "batch_id": ((sample_order - 1) // 100) + 1,
                "r2_object_key": (
                    f"2024/sample_500/html/raw/{cik}/{accession}.html"
                ),
                "universe_order": item["universe_order"],
            }
        )

    for field in ("company_id", "_company_key", "cik", "accession_number"):
        values = [row[field] for row in rows]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {field}")
    if [int(row["sample_order"]) for row in rows] != list(
        range(1, len(rows) + 1)
    ):
        raise ValueError("sample order is not contiguous")
    if any(
        row["form"] != "10-K"
        or not row["report_date"].startswith("2024-")
        or not row["filing_url"]
        for row in rows
    ):
        raise ValueError("non-eligible filing in 2024 manifest")

    write_csv(output, rows, fields)
    write_csv(
        output.parent / "quality_check/excluded_companies.csv",
        excluded,
        [
            "universe_order",
            "_company_key",
            "ticker",
            "company_name",
            "cik",
            "reason",
        ],
    )
    print(
        f"universe_rows={len(universe)} manifest_rows={len(rows)} "
        f"excluded_rows={len(excluded)}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("2024/sample_500/sample_manifest_2024_500.csv"),
    )
    args = parser.parse_args()
    build(args.root.resolve(), args.output.resolve())
