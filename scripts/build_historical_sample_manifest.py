#!/usr/bin/env python3
"""Build one collection-ready historical manifest using the existing SEC selector."""

from __future__ import annotations

import argparse
import csv
import io
from datetime import date
from pathlib import Path

try:
    from scripts import build_2020_sample_500 as selector
    from scripts import build_annual_constituents as constituents
    from scripts.sec_client import SecClient, normalize_cik
except ModuleNotFoundError:
    import build_2020_sample_500 as selector
    import build_annual_constituents as constituents
    from sec_client import SecClient, normalize_cik


FIELDS = [
    "sample_order", "company_id", "final_sample_id", "ticker", "symbol",
    "company_name", "security", "_company_key", "cik", "gics_sector",
    "gics_sub_industry", "accession_number", "primary_document", "form",
    "filing_date", "report_date", "report_year", "filing_url",
    "source_manifest", "sample_group", "batch_id", "r2_object_key",
    "universe_order",
]


def ensure_historical_universe(root: Path, report_year: int) -> Path:
    """Create a missing annual constituent universe before manifest selection.

    The reconstruction is cache-first for local raw inputs and SEC ticker metadata.
    Only the requested year is written, so protected existing annual snapshots are not
    regenerated or overwritten.
    """
    universe_path = root / str(report_year) / "sp500_companies.csv"
    if universe_path.is_file():
        return universe_path

    source_date = date.today().isoformat()
    wikipedia_path = root / "data" / "raw" / f"wikipedia_sp500_{source_date}.html"
    if wikipedia_path.is_file():
        wikipedia_content = wikipedia_path.read_bytes()
    else:
        wikipedia_content = constituents.fetch_source(wikipedia_path)

    sec_content, _ = constituents.resolve_sec_ticker_cache(root, source_date)
    sec_map = constituents.sec_ticker_map(sec_content)

    historical_path = (
        root
        / "data"
        / "raw"
        / f"sp500_historical_components_{source_date}.csv"
    )
    if historical_path.is_file():
        historical_content = historical_path.read_bytes()
    else:
        historical_content = constituents.fetch_url(
            constituents.HISTORICAL_COMPONENTS_URL,
            historical_path,
        )

    history = constituents.pd.read_csv(io.BytesIO(historical_content))
    history["date"] = constituents.pd.to_datetime(history["date"], errors="coerce")
    snapshot_date = constituents.pd.Timestamp(
        year=report_year + 1,
        month=1,
        day=1,
    )
    eligible = history.loc[history["date"] <= snapshot_date]
    if eligible.empty:
        raise ValueError(
            f"No historical constituent row for {snapshot_date.date()}"
        )
    validated_tickers = {
        constituents.clean_symbol(ticker)
        for ticker in eligible.iloc[-1]["tickers"].split(",")
    }

    components = constituents.normalize_components(
        constituents.load_components(wikipedia_content)
    )
    changes = constituents.parse_changes(wikipedia_content)
    reconstructed = {
        row["symbol"]: row.to_dict() for _, row in components.iterrows()
    }
    for _, change in changes[
        changes["effective_date"] > snapshot_date
    ].iterrows():
        constituents.reverse_change(reconstructed, change)

    constituents.write_snapshot(
        report_year,
        date(report_year + 1, 1, 1),
        reconstructed,
        root,
        sec_map,
        validated_tickers,
    )
    if not universe_path.is_file():
        raise FileNotFoundError(
            f"historical constituent reconstruction did not create {universe_path}"
        )
    return universe_path


def build(root: Path, report_year: int, output: Path) -> dict[str, int]:
    universe_path = ensure_historical_universe(root, report_year)
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
