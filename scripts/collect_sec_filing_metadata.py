#!/usr/bin/env python3
"""Collect SEC submissions metadata for the fixed 2025 pilot sample."""

from __future__ import annotations

import argparse
import csv
from datetime import date
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

try:
    from sec_client import SecClient, normalize_cik
    from select_2025_10k_filings import merge_filings, select_filings
except ModuleNotFoundError:  # imported as scripts.collect_sec_filing_metadata in tests
    from scripts.sec_client import SecClient, normalize_cik
    from scripts.select_2025_10k_filings import merge_filings, select_filings

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://data.sec.gov/submissions"


def fragment_may_contain_target(fragment: dict) -> bool:
    """Keep fragments whose filing-date span can contain a qualifying filing."""
    try:
        start = date.fromisoformat(str(fragment.get("filingFrom", "")))
        end = date.fromisoformat(str(fragment.get("filingTo", "")))
    except ValueError:
        return True
    return end >= date(2025, 1, 1) and start <= date(2026, 7, 29)


def normalize_name(value: str) -> str:
    import re
    value = re.sub(r"[^a-z0-9 ]", " ", value.casefold())
    suffixes = {"inc", "incorporated", "corp", "corporation", "company", "co", "plc", "ltd"}
    return " ".join(x for x in value.split() if x not in suffixes)


def identity_status(expected_cik: str, response: dict) -> str:
    try:
        return "match" if normalize_cik(response.get("cik", "")) == normalize_cik(expected_cik) else "identity_mismatch"
    except ValueError:
        return "identity_mismatch"


def collect(root: Path, limit: int | None = None) -> None:
    base = root / "2025" / "pilot_100"
    sample = pd.read_csv(base / "sample" / "pilot_sample_100.csv", dtype=str, keep_default_na=False)
    if limit:
        sample = sample.head(limit)
    client = SecClient(base / "cache" / "sec_submissions", base / "logs" / "sec_requests.jsonl")
    metadata, manifests, reviews = [], [], []
    for company in sample.to_dict("records"):
        cik = normalize_cik(company["cik"])
        now = datetime.now(timezone.utc).isoformat()
        try:
            response = client.get_json(f"{BASE}/CIK{cik}.json", cik)
            if identity_status(cik, response) != "match":
                raise ValueError("identity_mismatch")
            sec_name = str(response.get("name", ""))
            tickers = "|".join(map(str, response.get("tickers", [])))
            exchanges = "|".join(map(str, response.get("exchanges", [])))
            similarity = SequenceMatcher(None, normalize_name(company["security"]), normalize_name(sec_name)).ratio()
            identity_review = similarity < 0.45
            parts = [("recent", response.get("filings", {}).get("recent", {}))]
            fragment_count = 0
            for fragment in response.get("filings", {}).get("files", []):
                if not fragment_may_contain_target(fragment):
                    continue
                name = fragment.get("name", "")
                if not name:
                    continue
                fragment_count += 1
                payload = client.get_json(f"{BASE}/{name}", cik)
                parts.append((name, payload))
            rows = merge_filings(parts)
            result = select_filings(rows)
            metadata.append({
                "pilot_id": company["pilot_id"], "_company_key": company["_company_key"],
                "cik": cik, "symbol": company["symbol"], "security": company["security"],
                "sec_entity_name": sec_name, "sec_tickers": tickers, "sec_exchanges": exchanges,
                "sic": response.get("sic", ""), "sic_description": response.get("sicDescription", ""),
                "state_of_incorporation": response.get("stateOfIncorporation", ""),
                "fiscal_year_end": response.get("fiscalYearEnd", ""), "metadata_source": f"{BASE}/CIK{cik}.json",
                "metadata_status": "identity_review" if identity_review else "success",
                "historical_fragment_count": fragment_count, "retrieved_at": now,
            })
            amendment_accessions = "|".join(str(x.get("accessionNumber", "")) for x in result["amendments"] if x.get("accessionNumber"))
            amendment_dates = "|".join(str(x.get("filingDate", "")) for x in result["amendments"])
            amendment_reports = "|".join(str(x.get("reportDate", "")) for x in result["amendments"])
            for filing in result["candidates"] or [{}]:
                manifests.append({
                    "pilot_id": company["pilot_id"], "_company_key": company["_company_key"], "cik": cik,
                    "symbol": company["symbol"], "security": company["security"],
                    "form": filing.get("form", ""), "filing_date": filing.get("filingDate", ""),
                    "report_date": filing.get("reportDate", ""), "acceptance_datetime": filing.get("acceptanceDateTime", ""),
                    "accession_number": filing.get("accessionNumber", ""), "primary_document": filing.get("primaryDocument", ""),
                    "primary_doc_description": filing.get("primaryDocDescription", ""), "file_number": filing.get("fileNumber", ""),
                    "film_number": filing.get("filmNumber", ""), "is_xbrl": filing.get("isXBRL", ""),
                    "is_inline_xbrl": filing.get("isInlineXBRL", ""), "metadata_fragment": filing.get("metadata_fragment", ""),
                    "eligible_2025_10k": result["status"] == "eligible", "selection_status": result["status"],
                    "selection_reason": "exact Form 10-K; reportDate in 2025; filingDate <= 2026-07-29",
                    "amendment_exists": bool(result["amendments"]), "amendment_accession_numbers": amendment_accessions,
                    "amendment_filing_dates": amendment_dates, "amendment_report_dates": amendment_reports,
                    "amendment_link_status": "linked_by_report_date" if result["amendments"] and result["amendment_link_clear"] else ("unclear" if result["amendments"] else "not_applicable"),
                    "manual_review_required": result["status"] != "eligible" or identity_review or bool(result["defects"]),
                })
            reasons = []
            if result["status"] != "eligible": reasons.append(result["status"])
            if identity_review: reasons.append("entity_name_materially_different")
            if result["amendments"] and not result["amendment_link_clear"]: reasons.append("amendment_link_unclear")
            reasons.extend(x["review_reason"] for x in result["defects"])
            for reason in dict.fromkeys(reasons):
                reviews.append({"pilot_id": company["pilot_id"], "cik": cik, "symbol": company["symbol"], "security": company["security"], "review_reason": reason, "status": "pending"})
        except Exception as exc:
            error_status = "identity_mismatch" if str(exc) == "identity_mismatch" else "metadata_error"
            metadata.append({"pilot_id": company["pilot_id"], "_company_key": company["_company_key"], "cik": cik, "symbol": company["symbol"], "security": company["security"], "metadata_status": error_status, "retrieved_at": now})
            manifests.append({"pilot_id": company["pilot_id"], "_company_key": company["_company_key"], "cik": cik, "symbol": company["symbol"], "security": company["security"], "eligible_2025_10k": False, "selection_status": error_status, "selection_reason": type(exc).__name__, "manual_review_required": True})
            reviews.append({"pilot_id": company["pilot_id"], "cik": cik, "symbol": company["symbol"], "security": company["security"], "review_reason": error_status, "status": "pending"})
    out = base / "metadata"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(metadata).to_csv(out / "sec_company_metadata_index.csv", index=False)
    pd.DataFrame(manifests).to_csv(out / "filings_manifest.csv", index=False)
    pd.DataFrame(reviews).to_csv(out / "manual_review.csv", index=False)
    summary = pd.DataFrame([{
        "requested_companies": len(sample),
        "metadata_success": sum(x.get("metadata_status") in {"success", "identity_review"} for x in metadata),
        "metadata_errors": sum(x.get("metadata_status") == "metadata_error" for x in metadata),
        "identity_mismatches": sum(x.get("metadata_status") == "identity_mismatch" for x in metadata),
        "cache_hits_this_run": client.stats["cache_hits"],
        "request_log_entries_this_run": client.stats["log_entries"],
        "http_429_this_run": client.stats["http_429"],
        "retry_events_this_run": client.stats["retry_events"],
        "historical_fragments_queried": sum(int(x.get("historical_fragment_count", 0) or 0) for x in metadata),
        "amendment_companies": len({x["pilot_id"] for x in manifests if x.get("amendment_exists")}),
        "manual_review_rows": len(reviews),
        **{f"selection_{s}": sum(x.get("selection_status") == s for x in manifests) for s in ("eligible", "no_eligible_2025_10k", "ambiguous_multiple_eligible", "identity_mismatch", "metadata_error")
    }}])
    summary.to_csv(out / "metadata_collection_summary.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    collect(args.root.resolve(), args.limit)
