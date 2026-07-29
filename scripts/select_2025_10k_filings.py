#!/usr/bin/env python3
"""Pure filing-selection rules for the 2025 reporting-year pilot."""

from __future__ import annotations

import re
from datetime import date

ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
CUTOFF = date(2026, 7, 29)


def rows_from_columnar(filings: dict, fragment: str) -> list[dict]:
    if not isinstance(filings, dict):
        return []
    keys = list(filings)
    size = max((len(v) for v in filings.values() if isinstance(v, list)), default=0)
    return [
        {**{key: filings.get(key, [""] * size)[i] if i < len(filings.get(key, [])) else "" for key in keys}, "metadata_fragment": fragment}
        for i in range(size)
    ]


def merge_filings(parts: list[tuple[str, dict]]) -> list[dict]:
    merged, seen = [], set()
    for name, columns in parts:
        for row in rows_from_columnar(columns, name):
            accession = str(row.get("accessionNumber", ""))
            key = accession or (row.get("form"), row.get("filingDate"), row.get("primaryDocument"))
            if key not in seen:
                seen.add(key)
                merged.append(row)
    return merged


def _parse_date(value: str):
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def select_filings(rows: list[dict]) -> dict:
    amendments = []
    for row in rows:
        if row.get("form") != "10-K/A":
            continue
        report = _parse_date(row.get("reportDate", ""))
        filing = _parse_date(row.get("filingDate", ""))
        if report and filing and date(2025, 1, 1) <= report <= date(2025, 12, 31) and filing <= CUTOFF:
            amendments.append(row)
    candidates, defects = [], []
    for row in rows:
        if row.get("form") != "10-K":
            continue
        report = _parse_date(row.get("reportDate", ""))
        filing = _parse_date(row.get("filingDate", ""))
        if report is None or filing is None:
            defects.append({**row, "review_reason": "date_parse_error"})
            continue
        if not (date(2025, 1, 1) <= report <= date(2025, 12, 31)) or filing > CUTOFF:
            continue
        if not ACCESSION_RE.fullmatch(str(row.get("accessionNumber", ""))):
            defects.append({**row, "review_reason": "accession_missing_or_invalid"})
            continue
        if not str(row.get("primaryDocument", "")).strip():
            defects.append({**row, "review_reason": "primary_document_missing"})
            continue
        candidates.append(row)
    status = (
        "eligible" if len(candidates) == 1
        else "no_eligible_2025_10k" if len(candidates) == 0
        else "ambiguous_multiple_eligible"
    )
    candidate_reports = {x.get("reportDate") for x in candidates}
    amendment_link_clear = all(x.get("reportDate") in candidate_reports for x in amendments)
    return {
        "status": status, "candidates": candidates, "amendments": amendments,
        "defects": defects, "amendment_link_clear": amendment_link_clear,
    }
