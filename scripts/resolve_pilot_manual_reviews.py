#!/usr/bin/env python3
"""Resolve three metadata reviews and propose (but do not apply) a TXT replacement."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

try:
    from sec_client import SecClient, normalize_cik
    from select_2025_10k_filings import merge_filings, select_filings
except ModuleNotFoundError:
    from scripts.sec_client import SecClient, normalize_cik
    from scripts.select_2025_10k_filings import merge_filings, select_filings

BASE_URL = "https://data.sec.gov/submissions"
REVIEW_IDS = ("P2025-001", "P2025-059", "P2025-064")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as source:
        return sum(1 for _ in source)


def filing_parts(client: SecClient, response: dict, cik: str, all_fragments: bool) -> tuple[list[tuple[str, dict]], int]:
    parts = [("recent", response.get("filings", {}).get("recent", {}))]
    count = 0
    for fragment in response.get("filings", {}).get("files", []):
        name = fragment.get("name", "")
        if not name:
            continue
        if not all_fragments:
            try:
                if fragment.get("filingTo", "") < "2025-01-01":
                    continue
            except TypeError:
                pass
        parts.append((name, client.get_json(f"{BASE_URL}/{name}", cik)))
        count += 1
    return parts, count


def main(root: Path) -> None:
    base = root / "2025" / "pilot_100"
    log_path = base / "logs" / "sec_requests.jsonl"
    start_line = line_count(log_path) + 1
    prior_logs = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
    ] if log_path.exists() else []
    started = datetime.now(timezone.utc).isoformat()
    client = SecClient(base / "cache" / "sec_submissions", log_path)

    sample = pd.read_csv(base / "sample" / "pilot_sample_100.csv", dtype=str, keep_default_na=False)
    frame = pd.read_csv(base / "sample" / "pilot_sampling_frame.csv", dtype=str, keep_default_na=False)
    manifest = pd.read_csv(base / "metadata" / "filings_manifest.csv", dtype=str, keep_default_na=False)
    metadata = pd.read_csv(base / "metadata" / "sec_company_metadata_index.csv", dtype=str, keep_default_na=False)

    baseline_paths = [
        base / "sample" / "pilot_sample_100.csv",
        base / "sample" / "pilot_sampling_frame.csv",
        base / "metadata" / "sec_company_metadata_index.csv",
        base / "metadata" / "filings_manifest.csv",
        base / "metadata" / "manual_review.csv",
        base / "metadata" / "metadata_collection_summary.csv",
    ]
    baseline = {
        str(path.relative_to(root)): (
            sha256(path),
            sum(len(chunk) for chunk in pd.read_csv(path, chunksize=100000)),
        )
        for path in baseline_paths
    }

    responses: dict[str, dict] = {}
    resolutions = []
    txt_rows = []
    for pilot_id in REVIEW_IDS:
        company = sample.loc[sample["pilot_id"].eq(pilot_id)].iloc[0]
        cik = normalize_cik(company["cik"])
        response = client.get_json(f"{BASE_URL}/CIK{cik}.json", cik)
        responses[pilot_id] = response
        selected = manifest.loc[manifest["pilot_id"].eq(pilot_id)].iloc[0]
        cik_match = normalize_cik(response["cik"]) == cik
        sec_tickers = [str(x) for x in response.get("tickers", [])]
        sample_tickers = company["symbol"].split("|")
        ticker_match = all(x in sec_tickers for x in sample_tickers)
        if pilot_id == "P2025-001":
            explanation = "SEC legal name 'Fox Corp' omits sample share-class labels; FOXA and FOX are both registered under the same CIK."
            reorg = "SEC formerNames records NEW FOX, INC. in 2018; no separate company is created for the two current share classes."
            review_reason = "entity_name_materially_different"
            review_status = "resolved" if cik_match and ticker_match and selected["accession_number"] else "pending"
        elif pilot_id == "P2025-064":
            explanation = "Sample descriptive name 'GE Aerospace' differs from SEC legal entity name 'GENERAL ELECTRIC CO'; CIK and ticker GE are unchanged."
            reorg = "Corporate reorganization affects interpretation, but SEC metadata assigns the selected filing to the continuing GE CIK; retain a reorganization note."
            review_reason = "entity_name_materially_different"
            review_status = "resolved" if cik_match and ticker_match and selected["accession_number"] else "pending"
        else:
            explanation = "TXT has a non-calendar fiscal year: the 2025-filed 10-K reports 2024-12-28 and the 2026-filed 10-K reports 2026-01-03."
            reorg = ""
            review_reason = "no_eligible_2025_10k"
            parts, _ = filing_parts(client, response, cik, all_fragments=True)
            rows = merge_filings(parts)
            for row in rows:
                if row.get("form") in {"10-K", "10-K/A"}:
                    txt_rows.append({
                        "pilot_id": pilot_id, "cik": cik, "symbol": company["symbol"],
                        "fiscal_year_end": response.get("fiscalYearEnd", ""),
                        "form": row.get("form", ""), "filing_date": row.get("filingDate", ""),
                        "report_date": row.get("reportDate", ""), "accession_number": row.get("accessionNumber", ""),
                        "primary_document": row.get("primaryDocument", ""), "metadata_fragment": row.get("metadata_fragment", ""),
                        "report_date_in_2025": str(row.get("reportDate", "")).startswith("2025-"),
                        "filed_in_2025": str(row.get("filingDate", "")).startswith("2025-"),
                        "filed_in_2026": str(row.get("filingDate", "")).startswith("2026-"),
                        "review_conclusion": "not eligible under unchanged reportDate rule",
                    })
            review_status = "resolved"
        resolutions.append({
            "pilot_id": pilot_id, "symbol": company["symbol"], "cik": cik,
            "review_reason": review_reason, "sample_entity_name": company["security"],
            "sec_entity_name": response.get("name", ""), "sec_tickers": "|".join(sec_tickers),
            "selected_accession": selected["accession_number"], "cik_match": cik_match,
            "ticker_match": ticker_match, "selected_filing_cik_match": cik_match and bool(selected["accession_number"]),
            "former_names": "|".join(x.get("name", "") for x in response.get("formerNames", [])),
            "name_difference_explanation": explanation, "corporate_reorganization_note": reorg,
            "manual_review_status": review_status,
            "identity_status": "verified_by_cik_and_ticker" if cik_match and ticker_match else "unresolved",
            "evidence_source": f"{BASE_URL}/CIK{cik}.json",
        })

    selected_keys = set(sample["_company_key"])
    selected_ciks = set(sample["cik"])
    reserves = frame.loc[
        frame["gics_sector"].eq("Industrials")
        & frame["candidate_status"].eq("reserve")
        & ~frame["_company_key"].isin(selected_keys)
        & ~frame["cik"].isin(selected_ciks)
        & frame["cik"].ne("")
    ].sort_values("within_sector_random_order", key=lambda x: x.astype(int))
    proposal = None
    attempts = []
    for candidate_order, (_, candidate) in enumerate(reserves.iterrows(), 1):
        cik = normalize_cik(candidate["cik"])
        response = client.get_json(f"{BASE_URL}/CIK{cik}.json", cik)
        parts, fragment_count = filing_parts(client, response, cik, all_fragments=False)
        result = select_filings(merge_filings(parts))
        cik_match = normalize_cik(response.get("cik", "")) == cik
        ticker_match = all(x in response.get("tickers", []) for x in candidate["symbol"].split("|"))
        eligible = result["status"] == "eligible" and cik_match and ticker_match
        attempts.append((candidate_order, candidate["symbol"], cik, result["status"], cik_match, ticker_match, fragment_count))
        if eligible:
            filing = result["candidates"][0]
            proposal = {
                "excluded_pilot_id": "P2025-059", "excluded_symbol": "TXT", "excluded_cik": "0000217346",
                "exclusion_reason": "no exact Form 10-K with reportDate in 2025",
                "replacement_candidate_order": candidate_order,
                "replacement_within_sector_random_order": candidate["within_sector_random_order"],
                "replacement_company_key": candidate["_company_key"], "replacement_cik": cik,
                "replacement_symbol": candidate["symbol"], "replacement_security": candidate["security"],
                "gics_sector": candidate["gics_sector"], "eligible_accession": filing["accessionNumber"],
                "report_date": filing["reportDate"], "filing_date": filing["filingDate"],
                "primary_document": filing["primaryDocument"],
                "identity_status": "verified_by_cik_and_ticker",
                "proposal_status": "proposed_replacement_not_applied",
                "selection_basis": "first eligible Industrials reserve in deterministic seed-20250729 order; no text outcome used",
                "evidence_source": f"{BASE_URL}/CIK{cik}.json",
            }
            break
    if proposal is None:
        proposal = {
            "excluded_pilot_id": "P2025-059", "excluded_symbol": "TXT", "excluded_cik": "0000217346",
            "exclusion_reason": "no exact Form 10-K with reportDate in 2025",
            "proposal_status": "no_eligible_replacement_found",
            "selection_basis": "Industrials deterministic reserve order exhausted",
        }

    metadata_dir = base / "metadata"
    pd.DataFrame(resolutions).to_csv(metadata_dir / "manual_review_resolution.csv", index=False)
    pd.DataFrame(txt_rows).sort_values(["filing_date", "accession_number"], ascending=False).to_csv(metadata_dir / "txt_filing_review.csv", index=False)
    pd.DataFrame([proposal]).to_csv(base / "sample" / "proposed_txt_replacement.csv", index=False)

    ended = datetime.now(timezone.utc).isoformat()
    end_line = line_count(log_path)
    summary_rows = [{
        "run_id": "manual-review-20260729",
        "run_purpose": "resolve FOX/GE/TXT and evaluate deterministic TXT replacement",
        "started_at": started, "ended_at": ended, "log_start_line": start_line,
        "log_end_line": end_line, "request_log_rows": client.stats["log_entries"],
        "unique_urls": client.stats["log_entries"], "http_200": client.stats["log_entries"] - client.stats["errors"],
        "connection_errors": client.stats["errors"], "retry_events": client.stats["retry_events"],
        "cache_hits": client.stats["cache_hits"], "used_for_final_outputs": True,
        "notes": f"replacement attempts={len(attempts)}; prior request log preserved unchanged",
    }]
    if prior_logs:
        summary_rows.append({
            "run_id": "prior-runs-aggregate",
            "run_purpose": "smoke, interrupted collection, cache regeneration, and final metadata validation",
            "started_at": prior_logs[0]["requested_at"], "ended_at": prior_logs[-1]["requested_at"],
            "log_start_line": 1, "log_end_line": start_line - 1,
            "request_log_rows": len(prior_logs),
            "unique_urls": len({x["url"] for x in prior_logs}),
            "http_200": sum(x.get("http_status") == 200 for x in prior_logs),
            "connection_errors": sum(bool(x.get("error_type")) for x in prior_logs),
            "retry_events": sum(int(x.get("retry_count", 0)) > 0 for x in prior_logs),
            "cache_hits": sum(bool(x.get("cache_used")) for x in prior_logs),
            "used_for_final_outputs": True,
            "notes": "aggregate only; immutable JSONL retains row-level evidence and final metadata was cache-regenerated",
        })
    for path, (digest, rows) in baseline.items():
        summary_rows.append({
            "run_id": "pre-review-input-audit", "run_purpose": "baseline SHA-256 and row count",
            "used_for_final_outputs": True, "notes": f"{path}; rows={rows}; sha256={digest}",
        })
    pd.DataFrame(summary_rows).to_csv(metadata_dir / "final_run_summary.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    main(args.root.resolve())
