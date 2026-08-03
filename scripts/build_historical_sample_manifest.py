#!/usr/bin/env python3
"""Build one collection-ready historical manifest using the existing SEC selector."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    from scripts import build_2020_sample_500 as selector
    from scripts.sec_client import SecClient, normalize_cik
except ModuleNotFoundError:
    import build_2020_sample_500 as selector
    from sec_client import SecClient, normalize_cik


FIELDS = [
    "sample_order", "company_id", "final_sample_id", "ticker", "symbol",
    "company_name", "security", "_company_key", "cik", "gics_sector",
    "gics_sub_industry", "accession_number", "primary_document", "form",
    "filing_date", "report_date", "report_year", "filing_url",
    "source_manifest", "sample_group", "batch_id", "r2_object_key",
    "universe_order",
]


def build(root: Path, report_year: int, output: Path) -> dict[str, int]:
    universe_path = root / str(report_year) / "sp500_companies.csv"
    with universe_path.open(encoding="utf-8-sig", newline="") as handle:
        universe = list(csv.DictReader(handle))
    if not universe:
        raise ValueError(f"historical constituent universe is empty: {universe_path}")

    selector.REPORT_YEAR = report_year
    cache_dir = root / str(report_year) / "sample_503/cache/sec_submissions"
    log_path = root / str(report_year) / "sample_503/metadata/sec_requests.jsonl"
    client = SecClient(cache_dir, log_path)
    accepted: list[tuple[int, dict, dict]] = []
    excluded: list[dict[str, str | int]] = []
    for universe_order, company in enumerate(universe, 1):
        raw_cik = company.get("cik", "").strip()
        if not raw_cik:
            excluded.append({"universe_order": universe_order, "ticker": company.get("symbol", ""), "cik": "", "reason": "cik_missing_in_historical_universe"})
            continue
        cik = normalize_cik(raw_cik)
        filing, reason, candidates = selector.eligible_filing(client, cik)
        if filing is None:
            excluded.append({
                "universe_order": universe_order,
                "ticker": company.get("symbol", ""),
                "cik": cik,
                "reason": reason,
                "candidate_accessions": "|".join(str(row.get("accessionNumber", "")) for row in candidates),
            })
            continue
        accepted.append((universe_order, company, filing))

    rows = []
    for sample_order, (universe_order, company, filing) in enumerate(accepted, 1):
        cik = normalize_cik(company["cik"])
        accession = filing["accession_number"]
        company_id = f"S{report_year}-{sample_order:03d}"
        rows.append({
            "sample_order": sample_order,
            "company_id": company_id,
            "final_sample_id": company_id,
            "ticker": company.get("symbol", ""),
            "symbol": company.get("symbol", ""),
            "company_name": company.get("security", ""),
            "security": company.get("security", ""),
            "_company_key": company.get("_company_key", ""),
            "cik": cik,
            "gics_sector": company.get("gics_sector", ""),
            "gics_sub_industry": company.get("gics_sub_industry", ""),
            "accession_number": accession,
            "primary_document": filing["primary_document"],
            "form": filing["form"],
            "filing_date": filing["filing_date"],
            "report_date": filing["report_date"],
            "report_year": str(report_year),
            "filing_url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{filing['primary_document']}",
            "source_manifest": f"{report_year}/sp500_companies.csv",
            "sample_group": f"sample_{report_year}",
            "batch_id": ((sample_order - 1) // 100) + 1,
            "r2_object_key": f"{report_year}/sample_503/html/raw/{cik}/{accession}.html",
            "universe_order": universe_order,
        })

    for field in ("company_id", "cik", "accession_number"):
        values = [row[field] for row in rows]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {field}")
    if not rows:
        raise ValueError("no eligible historical filings found")
    if len(rows) > 503:
        raise ValueError(f"historical manifest exceeds runner limit: {len(rows)}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    excluded_path = output.parent.parent / "quality_check" / "excluded_companies.csv"
    excluded_path.parent.mkdir(parents=True, exist_ok=True)
    with excluded_path.open("w", encoding="utf-8", newline="") as handle:
        fields = sorted({key for row in excluded for key in row}) or ["reason"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(excluded)
    summary = {"universe_rows": len(universe), "manifest_rows": len(rows), "excluded_rows": len(excluded), "sec_cache_hits": client.stats["cache_hits"], "sec_network_log_entries": client.stats["log_entries"]}
    print(summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report-year", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.root.resolve(), args.report_year, args.output.resolve())
