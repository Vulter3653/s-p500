#!/usr/bin/env python3
"""Audit excluded firm-years and build manifests for unique panel-CIK recoveries."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

try:
    from sec_client import SecClient, normalize_cik
    from select_2025_10k_filings import merge_filings
except ModuleNotFoundError:
    from scripts.sec_client import SecClient, normalize_cik
    from scripts.select_2025_10k_filings import merge_filings


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://data.sec.gov/submissions"
ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
AUDIT_FIELDS = [
    "report_year",
    "original_ticker",
    "original_company_name",
    "original_exclusion_reason",
    "matched_panel_company_id",
    "matched_panel_cik",
    "matched_panel_ticker_history",
    "matched_panel_company_name_history",
    "candidate_cik_count",
    "identity_match_method",
    "identity_match_status",
    "sec_lookup_status",
    "eligible_filing_count",
    "selected_accession_number",
    "selected_filing_date",
    "selected_report_date",
    "selected_primary_document",
    "recovery_status",
    "recovery_reason",
    "requires_manual_review",
]
RECOVERY_FIELDS = [
    "report_year",
    "company_id",
    "source_company_id",
    "ticker",
    "company_name",
    "cik",
    "accession_number",
    "form",
    "filing_date",
    "report_date",
    "filing_url",
    "primary_document",
    "r2_object_key",
    "recovery_source",
    "original_exclusion_reason",
]


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", str(value))
        .encode("ascii", "ignore")
        .decode()
        .lower()
    )
    return re.sub(r"[^a-z0-9]", "", ascii_value)


def ticker_parts(value: str) -> set[str]:
    return {
        normalize_text(part)
        for part in re.split(r"[|/]", str(value))
        if normalize_text(part)
    }


def exclusions(root: Path) -> list[dict]:
    rows = []
    for year in range(2020, 2026):
        path = root / f"{year}/sample_500/quality_check/excluded_companies.csv"
        if year == 2025 and not path.exists():
            path = root / "2025/sample_500/quality_check/metadata_exclusions.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                rows.append(
                    {
                        "report_year": year,
                        "ticker": row.get("ticker", ""),
                        "company_name": row.get("company_name", ""),
                        "cik": row.get("cik", ""),
                        "reason": row.get("reason")
                        or row.get("exclusion_reason", ""),
                    }
                )
    return rows


def eligible_filings(
    client: SecClient, cik: str, report_year: int
) -> list[dict]:
    response = client.get_json(f"{BASE}/CIK{cik}.json", cik)
    if normalize_cik(response.get("cik", "")) != cik:
        raise ValueError(f"SEC CIK mismatch for {cik}")
    parts = [("recent", response.get("filings", {}).get("recent", {}))]
    for fragment in response.get("filings", {}).get("files", []):
        start = str(fragment.get("filingFrom", ""))
        end = str(fragment.get("filingTo", ""))
        if start and end and (
            end < f"{report_year}-01-01" or start > "2026-07-30"
        ):
            continue
        name = str(fragment.get("name", ""))
        if name:
            parts.append((name, client.get_json(f"{BASE}/{name}", cik)))
    unique = {}
    for row in merge_filings(parts):
        if row.get("form") != "10-K":
            continue
        accession = str(row.get("accessionNumber", ""))
        primary = str(row.get("primaryDocument", "")).strip()
        try:
            report = date.fromisoformat(str(row.get("reportDate", "")))
            filing = date.fromisoformat(str(row.get("filingDate", "")))
        except ValueError:
            continue
        if (
            report.year == report_year
            and filing <= date(2026, 7, 30)
            and ACCESSION_RE.fullmatch(accession)
            and primary
        ):
            unique[(accession, primary)] = row
    return sorted(
        unique.values(),
        key=lambda row: (
            str(row.get("filingDate", "")),
            str(row.get("accessionNumber", "")),
        ),
    )


def audit(root: Path, output: Path) -> dict:
    panel = pd.read_parquet(
        root / "panel_2020_2025/firm_year_language_panel.parquet"
    )
    panel["ticker_normalized"] = panel["ticker"].map(normalize_text)
    panel["name_normalized"] = panel["company_name"].map(normalize_text)
    panel["cik"] = panel["cik"].astype(str).str.zfill(10)
    client = SecClient(
        output / "cache/sec_submissions",
        output / "sec_requests.jsonl",
    )
    annual_counts = {}
    for year in range(2020, 2026):
        with (
            root / f"{year}/sample_500/sample_manifest_{year}_500.csv"
        ).open(encoding="utf-8-sig", newline="") as handle:
            annual_counts[year] = len(list(csv.DictReader(handle)))

    audit_rows, recovered, failures = [], [], []
    for excluded in exclusions(root):
        year = excluded["report_year"]
        reason = excluded["reason"]
        ticker_candidates = ticker_parts(excluded["ticker"])
        name_candidate = normalize_text(excluded["company_name"])
        ticker_ciks = set(
            panel.loc[
                panel["ticker_normalized"].isin(ticker_candidates), "cik"
            ]
        )
        name_ciks = (
            set(panel.loc[panel["name_normalized"].eq(name_candidate), "cik"])
            if name_candidate
            else set()
        )
        candidates = (
            ticker_ciks & name_ciks
            if ticker_ciks and name_ciks
            else ticker_ciks or name_ciks
        )
        target = reason.startswith("cik_missing_in_")
        identity_status = "no_panel_match"
        method = ""
        if len(candidates) == 1:
            identity_status = "unique_panel_cik_match"
            method = (
                "normalized_ticker_and_company_name"
                if ticker_ciks and name_ciks
                else "normalized_company_name"
                if name_ciks
                else "normalized_ticker"
            )
        elif len(candidates) > 1:
            identity_status = "ambiguous_panel_identity"
            method = "multiple_panel_cik_candidates"

        matched_cik = next(iter(candidates)) if len(candidates) == 1 else ""
        matched = panel.loc[panel["cik"].eq(matched_cik)]
        base = {
            "report_year": year,
            "original_ticker": excluded["ticker"],
            "original_company_name": excluded["company_name"],
            "original_exclusion_reason": reason,
            "matched_panel_company_id": (
                matched.iloc[0]["company_id"] if not matched.empty else ""
            ),
            "matched_panel_cik": matched_cik,
            "matched_panel_ticker_history": (
                "|".join(map(str, matched.sort_values("report_year")["ticker"].unique()))
                if not matched.empty
                else ""
            ),
            "matched_panel_company_name_history": (
                "|".join(
                    map(
                        str,
                        matched.sort_values("report_year")[
                            "company_name"
                        ].unique(),
                    )
                )
                if not matched.empty
                else ""
            ),
            "candidate_cik_count": len(candidates),
            "identity_match_method": method,
            "identity_match_status": identity_status,
            "sec_lookup_status": "not_attempted_not_identity_recovery_target",
            "eligible_filing_count": "",
            "selected_accession_number": "",
            "selected_filing_date": "",
            "selected_report_date": "",
            "selected_primary_document": "",
            "recovery_status": "not_recovered_other",
            "recovery_reason": "outside_primary_identity_recovery_scope",
            "requires_manual_review": 0,
        }
        if not target:
            if reason.startswith("ambiguous_multiple_eligible_"):
                base["requires_manual_review"] = 1
            audit_rows.append(base)
            continue
        if identity_status == "no_panel_match":
            base["sec_lookup_status"] = "not_attempted_no_panel_cik"
            base["recovery_status"] = "not_recovered_other"
            base["recovery_reason"] = "no_panel_match"
            audit_rows.append(base)
            continue
        if identity_status == "ambiguous_panel_identity":
            base["sec_lookup_status"] = "not_attempted_identity_ambiguous"
            base["recovery_status"] = "not_recovered_identity_ambiguous"
            base["recovery_reason"] = "multiple_panel_cik_candidates"
            base["requires_manual_review"] = 1
            audit_rows.append(base)
            continue
        try:
            filings = eligible_filings(client, matched_cik, year)
            base["sec_lookup_status"] = "success"
            base["eligible_filing_count"] = len(filings)
            if not filings:
                base["recovery_status"] = "not_recovered_no_filing"
                base["recovery_reason"] = "no_exact_report_date_10k"
            elif len(filings) > 1:
                base["recovery_status"] = "not_recovered_multiple_filings"
                base["recovery_reason"] = "multiple_distinct_accessions"
                base["requires_manual_review"] = 1
            else:
                filing = filings[0]
                accession = filing["accessionNumber"]
                primary = filing["primaryDocument"]
                source_id = f"S{year}-{annual_counts[year] + 1:03d}"
                filing_url = (
                    "https://www.sec.gov/Archives/edgar/data/"
                    f"{int(matched_cik)}/{accession.replace('-', '')}/{primary}"
                )
                base.update(
                    {
                        "selected_accession_number": accession,
                        "selected_filing_date": filing["filingDate"],
                        "selected_report_date": filing["reportDate"],
                        "selected_primary_document": primary,
                        "recovery_status": "recovered",
                        "recovery_reason": "unique_panel_cik_and_unique_filing",
                    }
                )
                recovered.append(
                    {
                        "report_year": year,
                        "company_id": matched.iloc[0]["company_id"],
                        "source_company_id": source_id,
                        "ticker": excluded["ticker"],
                        "company_name": excluded["company_name"],
                        "cik": matched_cik,
                        "accession_number": accession,
                        "form": "10-K",
                        "filing_date": filing["filingDate"],
                        "report_date": filing["reportDate"],
                        "filing_url": filing_url,
                        "primary_document": primary,
                        "r2_object_key": (
                            f"{year}/sample_500/html/raw/{matched_cik}/"
                            f"{accession}.html"
                        ),
                        "recovery_source": "unique_panel_cik_match",
                        "original_exclusion_reason": reason,
                    }
                )
                annual_counts[year] += 1
        except Exception as error:
            base["sec_lookup_status"] = "failed"
            base["recovery_status"] = "failed"
            base["recovery_reason"] = type(error).__name__
            failures.append(
                {
                    "report_year": year,
                    "ticker": excluded["ticker"],
                    "cik": matched_cik,
                    "failure_stage": "sec_metadata",
                    "failure_reason": type(error).__name__,
                }
            )
        audit_rows.append(base)

    write_csv(output / "excluded_firm_year_recovery_audit.csv", AUDIT_FIELDS, audit_rows)
    write_csv(output / "recovered_firm_year_manifest.csv", RECOVERY_FIELDS, recovered)
    write_csv(
        output / "recovery_failed_cases.csv",
        ["report_year", "ticker", "cik", "failure_stage", "failure_reason"],
        failures,
    )

    processing_fields = [
        "sample_order",
        "company_id",
        "final_sample_id",
        "ticker",
        "symbol",
        "company_name",
        "security",
        "_company_key",
        "cik",
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
    ]
    for year in range(2020, 2026):
        rows = []
        for item in recovered:
            if item["report_year"] != year:
                continue
            rows.append(
                {
                    "sample_order": annual_counts[year],
                    "company_id": item["source_company_id"],
                    "final_sample_id": item["source_company_id"],
                    "ticker": item["ticker"],
                    "symbol": item["ticker"],
                    "company_name": item["company_name"],
                    "security": item["company_name"],
                    "_company_key": item["company_id"],
                    "cik": item["cik"],
                    "accession_number": item["accession_number"],
                    "primary_document": item["primary_document"],
                    "form": item["form"],
                    "filing_date": item["filing_date"],
                    "report_date": item["report_date"],
                    "report_year": year,
                    "filing_url": item["filing_url"],
                    "source_manifest": (
                        "panel_2020_2025/recovery/"
                        "recovered_firm_year_manifest.csv"
                    ),
                    "sample_group": "recovered_panel_identity",
                    "batch_id": 1,
                    "r2_object_key": item["r2_object_key"],
                }
            )
        if rows:
            write_csv(
                output / f"processing_manifests/recovery_{year}.csv",
                processing_fields,
                rows,
            )

    reasons = Counter(row["identity_match_status"] for row in audit_rows)
    filing_counts = Counter(
        str(row["eligible_filing_count"])
        for row in audit_rows
        if row["sec_lookup_status"] == "success"
    )
    summary = {
        "total_excluded_reviewed": len(audit_rows),
        "cik_missing_reviewed": sum(
            row["original_exclusion_reason"].startswith("cik_missing_in_")
            for row in audit_rows
        ),
        "unique_panel_cik_matches": sum(
            row["original_exclusion_reason"].startswith("cik_missing_in_")
            and row["identity_match_status"] == "unique_panel_cik_match"
            for row in audit_rows
        ),
        "ambiguous_panel_matches": reasons["ambiguous_panel_identity"],
        "no_panel_matches": sum(
            row["original_exclusion_reason"].startswith("cik_missing_in_")
            and row["identity_match_status"] == "no_panel_match"
            for row in audit_rows
        ),
        "sec_eligible_filing_zero": filing_counts["0"],
        "sec_eligible_filing_one": filing_counts["1"],
        "sec_eligible_filing_multiple": sum(
            count
            for value, count in filing_counts.items()
            if value.isdigit() and int(value) > 1
        ),
        "recovered_firm_years": len(recovered),
        "collection_failed": 0,
        "extraction_failed": 0,
        "language_failed": 0,
        "r2_conflicts": 0,
        "final_panel_rows": 2827,
        "added_panel_rows": 0,
    }
    write_csv(
        output / "recovery_summary.csv",
        ["metric", "value"],
        [{"metric": key, "value": value} for key, value in summary.items()],
    )
    (output / "run_summary.md").write_text(
        "# Excluded Firm-Year Recovery Run Summary\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in summary.items())
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    audit(arguments.root.resolve(), arguments.output_dir.resolve())
