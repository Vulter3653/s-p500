#!/usr/bin/env python3
"""Build the deterministic 2025 300-firm manifest without changing the pilot."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    from build_pilot_sample import allocate
    from sec_client import SecClient, normalize_cik
    from select_2025_10k_filings import merge_filings, select_filings
except ModuleNotFoundError:
    from scripts.build_pilot_sample import allocate
    from scripts.sec_client import SecClient, normalize_cik
    from scripts.select_2025_10k_filings import merge_filings, select_filings

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://data.sec.gov/submissions"
TARGET = 300


def filing_for(client: SecClient, candidate: dict) -> dict | None:
    cik = normalize_cik(candidate["cik"])
    response = client.get_json(f"{BASE}/CIK{cik}.json", cik)
    if normalize_cik(response.get("cik", "")) != cik:
        raise ValueError(f"SEC CIK mismatch for {cik}")
    parts = [("recent", response.get("filings", {}).get("recent", {}))]
    for fragment in response.get("filings", {}).get("files", []):
        start = str(fragment.get("filingFrom", ""))
        end = str(fragment.get("filingTo", ""))
        if start and end and (end < "2025-01-01" or start > "2026-07-29"):
            continue
        name = str(fragment.get("name", ""))
        if name:
            parts.append((name, client.get_json(f"{BASE}/{name}", cik)))
    selected = select_filings(merge_filings(parts))
    if selected["status"] != "eligible":
        return None
    filing = selected["candidates"][0]
    return {
        "accession_number": filing["accessionNumber"],
        "form": filing["form"],
        "filing_date": filing["filingDate"],
        "report_date": filing["reportDate"],
        "primary_document": filing["primaryDocument"],
    }


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(root: Path, output: Path) -> None:
    frame = pd.read_csv(
        root / "2025/pilot_100/sample/pilot_sampling_frame.csv",
        dtype=str,
        keep_default_na=False,
    )
    pilot = pd.read_csv(
        root / "2025/pilot_100/sample/final_analysis_sample_100.csv",
        dtype=str,
        keep_default_na=False,
    )
    if len(frame) != 487 or len(pilot) != 100:
        raise ValueError("unexpected deterministic frame or pilot size")
    allocations = allocate(frame.groupby("gics_sector").size().sort_index(), TARGET)
    pilot_keys = set(pilot["_company_key"])
    client = SecClient(
        root / "2025/sample_300/cache/sec_submissions",
        root / "2025/sample_300/metadata/sec_requests.jsonl",
    )

    expansion: list[dict] = []
    excluded: list[dict] = []
    for sector, target in allocations.items():
        existing = pilot.loc[pilot["gics_sector"].eq(sector)]
        needed = target - len(existing)
        candidates = frame.loc[
            frame["gics_sector"].eq(sector)
            & ~frame["_company_key"].isin(pilot_keys)
        ].sort_values("within_sector_random_order", key=lambda x: x.astype(int))
        accepted = 0
        for candidate in candidates.to_dict("records"):
            filing = filing_for(client, candidate)
            if filing is None:
                excluded.append(
                    {
                        "_company_key": candidate["_company_key"],
                        "cik": candidate["cik"],
                        "ticker": candidate["symbol"],
                        "gics_sector": sector,
                        "within_sector_random_order": candidate[
                            "within_sector_random_order"
                        ],
                        "reason": "no_unique_eligible_2025_report_date_10k",
                    }
                )
                continue
            expansion.append({**candidate, **filing})
            accepted += 1
            if accepted == needed:
                break
        if accepted != needed:
            raise ValueError(f"insufficient eligible candidates in {sector}")

    expansion.sort(
        key=lambda row: (
            row["gics_sector"],
            int(row["within_sector_random_order"]),
        )
    )
    if len(expansion) != 200:
        raise ValueError(f"expected 200 expansion firms, got {len(expansion)}")

    fields = [
        "sample_order", "company_id", "final_sample_id", "ticker", "symbol",
        "company_name", "security", "_company_key", "cik", "gics_sector",
        "gics_sub_industry", "accession_number", "primary_document", "form",
        "filing_date", "report_date", "report_year", "filing_url",
        "source_manifest", "sample_group", "batch_id", "sampling_seed",
        "within_sector_random_order",
    ]
    rows: list[dict] = []
    for index, row in enumerate(pilot.to_dict("records"), 1):
        rows.append(
            {
                "sample_order": index,
                "company_id": row["final_sample_id"],
                "final_sample_id": row["final_sample_id"],
                "ticker": row["symbol"],
                "symbol": row["symbol"],
                "company_name": row["security"],
                "security": row["security"],
                "_company_key": row["_company_key"],
                "cik": row["cik"],
                "gics_sector": row["gics_sector"],
                "gics_sub_industry": row["gics_sub_industry"],
                "accession_number": row["accession_number"],
                "primary_document": row["primary_document"],
                "form": row["form"],
                "filing_date": row["filing_date"],
                "report_date": row["report_date"],
                "report_year": "2025",
                "filing_url": (
                    "https://www.sec.gov/Archives/edgar/data/"
                    f"{int(row['cik'])}/{row['accession_number'].replace('-', '')}/"
                    f"{row['primary_document']}"
                ),
                "source_manifest": "2025/pilot_100/sample/final_analysis_sample_100.csv",
                "sample_group": "pilot_100",
                "batch_id": 1,
                "sampling_seed": row["sampling_seed"],
                "within_sector_random_order": row["within_sector_random_order"],
            }
        )
    for offset, row in enumerate(expansion, 101):
        company_id = f"S2025-{offset:03d}"
        rows.append(
            {
                "sample_order": offset,
                "company_id": company_id,
                "final_sample_id": company_id,
                "ticker": row["symbol"],
                "symbol": row["symbol"],
                "company_name": row["security"],
                "security": row["security"],
                "_company_key": row["_company_key"],
                "cik": normalize_cik(row["cik"]),
                "gics_sector": row["gics_sector"],
                "gics_sub_industry": row["gics_sub_industry"],
                "accession_number": row["accession_number"],
                "primary_document": row["primary_document"],
                "form": row["form"],
                "filing_date": row["filing_date"],
                "report_date": row["report_date"],
                "report_year": "2025",
                "filing_url": (
                    "https://www.sec.gov/Archives/edgar/data/"
                    f"{int(row['cik'])}/{row['accession_number'].replace('-', '')}/"
                    f"{row['primary_document']}"
                ),
                "source_manifest": "2025/pilot_100/sample/pilot_sampling_frame.csv",
                "sample_group": "expansion_200",
                "batch_id": 2 if offset <= 200 else 3,
                "sampling_seed": row["sampling_seed"],
                "within_sector_random_order": row["within_sector_random_order"],
            }
        )
    for field in ("company_id", "cik", "accession_number"):
        values = [row[field] for row in rows]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {field}")
    write_csv(output, rows, fields)
    write_csv(
        output.parent / "quality_check/metadata_exclusions.csv",
        excluded,
        [
            "_company_key", "cik", "ticker", "gics_sector",
            "within_sector_random_order", "reason",
        ],
    )
    print(
        f"manifest_rows={len(rows)} expansion_rows={len(expansion)} "
        f"metadata_exclusions={len(excluded)}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("2025/sample_300/sample_manifest_2025_300.csv"),
    )
    args = parser.parse_args()
    build(args.root.resolve(), args.output.resolve())
