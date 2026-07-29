"""Select the deterministic five-company language-measurement smoke test."""

from __future__ import annotations

import random
import statistics
from pathlib import Path

from language_measurement_common import (
    RANDOM_SEED,
    ROOT,
    SMOKE_ROOT,
    ai_matches,
    read_csv,
    sha256_file,
    write_csv,
)

RESULTS = ROOT / "2025/pilot_100/text/extraction_results/company_text_extraction_results.csv"
QUALITY = ROOT / "2025/pilot_100/text/quality_check/company_text_quality_check.csv"
SAMPLE = ROOT / "2025/pilot_100/sample/final_analysis_sample_100.csv"
OUTPUT = SMOKE_ROOT / "selected_companies/selected_5_companies.csv"


def select_companies() -> list[dict]:
    result_rows = read_csv(RESULTS)
    quality = {row["company_id"]: row for row in read_csv(QUALITY)}
    samples = {row["final_sample_id"]: row for row in read_csv(SAMPLE)}
    eligible = []
    for row in result_rows:
        if row["ticker"] in {"WFC", "D", "ETR"}:
            continue
        if row["extraction_status"] != "success":
            continue
        quality_row = quality[row["company_id"]]
        if quality_row["quality_status"] != "pass":
            continue
        path = ROOT / row["analysis_text_file"]
        if not path.is_file() or sha256_file(path) != row["analysis_text_sha256"]:
            raise ValueError(f"analysis text integrity failure: {row['company_id']}")
        if int(row["analysis_word_count"]) < 1_000:
            continue
        text = path.read_text(encoding="utf-8")
        candidate = dict(row)
        candidate["company_name"] = samples[row["company_id"]]["security"]
        candidate["preliminary_ai_term_count"] = len(ai_matches(text))
        candidate["section_warning_status"] = "none"
        eligible.append(candidate)
    if len(eligible) < 5:
        raise ValueError("fewer than five eligible companies")

    selected: list[tuple[dict, str]] = []
    ranked = sorted(eligible, key=lambda row: (-row["preliminary_ai_term_count"], row["company_id"]))
    selected.extend((row, "highest_preliminary_ai_term_count") for row in ranked[:2])
    used = {row["company_id"] for row, _ in selected}
    remaining = [row for row in eligible if row["company_id"] not in used]
    low = min(remaining, key=lambda row: (row["preliminary_ai_term_count"], row["company_id"]))
    selected.append((low, "lowest_preliminary_ai_term_count"))
    used.add(low["company_id"])
    remaining = [row for row in eligible if row["company_id"] not in used]
    median_words = statistics.median(int(row["analysis_word_count"]) for row in eligible)
    median = min(
        remaining,
        key=lambda row: (abs(int(row["analysis_word_count"]) - median_words), row["company_id"]),
    )
    selected.append((median, "analysis_word_count_nearest_eligible_median"))
    used.add(median["company_id"])
    remaining = sorted(
        [row for row in eligible if row["company_id"] not in used],
        key=lambda row: row["company_id"],
    )
    random_row = random.Random(RANDOM_SEED).choice(remaining)
    selected.append((random_row, "fixed_seed_random"))

    output = []
    for row, reason in selected:
        output.append(
            {
                "company_id": row["company_id"],
                "cik": row["cik"],
                "ticker": row["ticker"],
                "company_name": row["company_name"],
                "accession_number": row["accession_number"],
                "selection_reason": reason,
                "analysis_word_count": row["analysis_word_count"],
                "preliminary_ai_term_count": row["preliminary_ai_term_count"],
                "extraction_status": row["extraction_status"],
                "section_warning_status": row["section_warning_status"],
                "random_seed": RANDOM_SEED,
                "analysis_text_file": row["analysis_text_file"],
                "analysis_text_sha256": row["analysis_text_sha256"],
                "parser_version": row["parser_version"],
            }
        )
    write_csv(OUTPUT, output, list(output[0]))
    return output


if __name__ == "__main__":
    rows = select_companies()
    print(f"selected={len(rows)} tickers={','.join(row['ticker'] for row in rows)} seed={RANDOM_SEED}")
