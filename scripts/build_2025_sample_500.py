#!/usr/bin/env python3
"""Extend the immutable 2025 sample 300 with every remaining eligible firm."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    from build_2025_sample_300 import filing_for
    from sec_client import SecClient, normalize_cik
except ModuleNotFoundError:
    from scripts.build_2025_sample_300 import filing_for
    from scripts.sec_client import SecClient, normalize_cik

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def object_key(row: dict) -> str:
    if row["sample_group"] == "pilot_100":
        namespace = "pilot_100"
    elif row["sample_group"] == "expansion_200":
        namespace = "sample_300"
    else:
        namespace = "sample_500"
    return (
        f"2025/{namespace}/html/raw/{row['cik']}/"
        f"{row['accession_number']}.html"
    )


def build(root: Path, output: Path) -> None:
    frame = pd.read_csv(
        root / "2025/pilot_100/sample/pilot_sampling_frame.csv",
        dtype=str,
        keep_default_na=False,
    )
    existing = pd.read_csv(
        root / "2025/sample_300/sample_manifest_2025_300.csv",
        dtype=str,
        keep_default_na=False,
    )
    if len(frame) != 487 or len(existing) != 300:
        raise ValueError("unexpected deterministic frame or sample 300 size")
    if existing["sample_order"].astype(int).tolist() != list(range(1, 301)):
        raise ValueError("sample 300 order is not 1 through 300")

    existing_keys = set(existing["_company_key"])
    candidates = frame.loc[~frame["_company_key"].isin(existing_keys)].copy()
    candidates["_sector_order"] = candidates["gics_sector"].astype(str)
    candidates["_rank_order"] = candidates[
        "within_sector_random_order"
    ].astype(int)
    candidates = candidates.sort_values(
        ["_sector_order", "_rank_order", "_company_key"]
    )

    client = SecClient(
        root / "2025/sample_500/cache/sec_submissions",
        root / "2025/sample_500/metadata/sec_requests.jsonl",
    )
    accepted: list[dict] = []
    excluded: list[dict] = []
    for candidate in candidates.to_dict("records"):
        filing = filing_for(client, candidate)
        if filing is None:
            excluded.append(
                {
                    "_company_key": candidate["_company_key"],
                    "cik": candidate["cik"],
                    "ticker": candidate["symbol"],
                    "gics_sector": candidate["gics_sector"],
                    "within_sector_random_order": candidate[
                        "within_sector_random_order"
                    ],
                    "reason": "no_unique_eligible_2025_report_date_10k",
                }
            )
            continue
        accepted.append({**candidate, **filing})

    fields = list(existing.columns)
    if "r2_object_key" not in fields:
        fields.append("r2_object_key")
    rows: list[dict] = []
    for row in existing.to_dict("records"):
        preserved = dict(row)
        preserved["r2_object_key"] = object_key(preserved)
        rows.append(preserved)

    for row in accepted:
        sample_order = len(rows) + 1
        company_id = f"S2025-{sample_order:03d}"
        new_row = {
            "sample_order": sample_order,
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
            "source_manifest": (
                "2025/pilot_100/sample/pilot_sampling_frame.csv"
            ),
            "sample_group": "expansion_200_final",
            "batch_id": 4 if sample_order <= 400 else 5,
            "sampling_seed": row["sampling_seed"],
            "within_sector_random_order": row[
                "within_sector_random_order"
            ],
        }
        new_row["r2_object_key"] = object_key(new_row)
        rows.append(new_row)

    for field in ("company_id", "_company_key", "cik", "accession_number"):
        values = [row[field] for row in rows]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {field}")
    if [int(row["sample_order"]) for row in rows] != list(
        range(1, len(rows) + 1)
    ):
        raise ValueError("final sample order is not contiguous")
    if any(
        row["form"] != "10-K"
        or not row["report_date"].startswith("2025-")
        for row in rows
    ):
        raise ValueError("non-eligible filing in final manifest")

    write_csv(output, rows, fields)
    write_csv(
        output.parent / "quality_check/metadata_exclusions.csv",
        excluded,
        [
            "_company_key",
            "cik",
            "ticker",
            "gics_sector",
            "within_sector_random_order",
            "reason",
        ],
    )
    print(
        f"manifest_rows={len(rows)} existing_rows=300 "
        f"new_rows={len(accepted)} metadata_exclusions={len(excluded)}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("2025/sample_500/sample_manifest_2025_500.csv"),
    )
    args = parser.parse_args()
    build(args.root.resolve(), args.output.resolve())
