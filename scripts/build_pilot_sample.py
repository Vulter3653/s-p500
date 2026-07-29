#!/usr/bin/env python3
"""Create the reproducible 2025 sector-stratified 100-company pilot sample."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

import pandas as pd

SEED = 20250729
TARGET = 100


def allocate(counts: pd.Series, target: int = TARGET) -> dict[str, int]:
    """Largest-remainder proportional allocation with one per nonempty stratum."""
    exact = counts * target / counts.sum()
    result = exact.astype(int).clip(lower=1)
    candidates = sorted(counts.index, key=lambda s: (-(exact[s] - int(exact[s])), s))
    for sector in candidates[: target - int(result.sum())]:
        result[sector] += 1
    while int(result.sum()) > target:
        candidates = sorted(
            (s for s in counts.index if result[s] > 1),
            key=lambda s: (exact[s] - int(exact[s]), s),
        )
        result[candidates[0]] -= 1
    return {str(k): int(v) for k, v in result.items()}


def build(root: Path, seed: int = SEED) -> None:
    source = root / "2025" / "sp500_companies.csv"
    output = root / "2025" / "pilot_100" / "sample"
    output.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(source, dtype=str, keep_default_na=False)
    required = {
        "sample_year", "snapshot_date", "_company_key", "cik", "symbol",
        "security", "gics_sector", "gics_sub_industry",
    }
    if not required.issubset(frame.columns):
        raise ValueError(f"missing columns: {sorted(required - set(frame.columns))}")
    if len(frame) != 500 or frame["_company_key"].duplicated().any():
        raise ValueError("population must contain 500 unique company keys")

    eligible = frame.loc[frame["cik"].ne("") & frame["gics_sector"].ne("")].copy()
    if eligible["cik"].duplicated().any():
        raise ValueError("eligible population contains duplicate CIK")
    counts = eligible.groupby("gics_sector").size().sort_index()
    allocations = allocate(counts)

    ranked = []
    for sector, group in eligible.groupby("gics_sector", sort=True):
        records = group.sort_values(["_company_key", "symbol"]).to_dict("records")
        random.Random(f"{seed}:{sector}").shuffle(records)
        for rank, record in enumerate(records, 1):
            record.update(
                sampling_seed=seed,
                sector_population_n=len(records),
                sector_target_n=allocations[sector],
                within_sector_random_order=rank,
                candidate_status="primary" if rank <= allocations[sector] else "reserve",
            )
            ranked.append(record)
    sampling_frame = pd.DataFrame(ranked).sort_values(
        ["gics_sector", "within_sector_random_order"]
    )
    sampling_frame.to_csv(output / "pilot_sampling_frame.csv", index=False)

    selected = sampling_frame.loc[sampling_frame["candidate_status"].eq("primary")].copy()
    selected = selected.sort_values(["gics_sector", "within_sector_random_order"]).reset_index(drop=True)
    selected.insert(0, "pilot_id", [f"P2025-{n:03d}" for n in range(1, len(selected) + 1)])
    selected["selection_status"] = "selected_pending_sec_validation"
    selected["replacement_for"] = ""
    selected["selection_reason"] = "sector_proportional_largest_remainder_seeded_order"
    columns = [
        "pilot_id", "sample_year", "snapshot_date", "_company_key", "cik", "symbol",
        "security", "gics_sector", "gics_sub_industry", "sampling_seed",
        "sector_population_n", "sector_target_n", "within_sector_random_order",
        "selection_status", "replacement_for", "selection_reason",
    ]
    selected[columns].to_csv(output / "pilot_sample_100.csv", index=False)

    excluded = frame.loc[~frame.index.isin(eligible.index)].copy()
    excluded["exclusion_reason"] = excluded.apply(
        lambda r: "CIK_unverified" if not r["cik"] else "GICS_sector_missing", axis=1
    )
    excluded["official_source_checked"] = (
        "data/raw/sec_company_tickers_2026-07-24.json (SEC official snapshot)"
    )
    excluded["replacement_status"] = "excluded_before_sampling; no one-for-one replacement"
    excluded.to_csv(output / "pilot_exclusions_and_replacements.csv", index=False)

    pd.DataFrame(
        [
            {
                "gics_sector": sector,
                "sector_population_n": int(counts[sector]),
                "exact_quota": counts[sector] * TARGET / counts.sum(),
                "sector_target_n": allocations[sector],
            }
            for sector in counts.index
        ]
    ).to_csv(output / "sector_allocation.csv", index=False, quoting=csv.QUOTE_MINIMAL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    build(args.root.resolve(), args.seed)
