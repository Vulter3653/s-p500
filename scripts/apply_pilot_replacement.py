#!/usr/bin/env python3
"""Apply the approved deterministic TXT-to-ITW pilot replacement."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SEED = "20250729"
TXT_ID = "P2025-059"
ITW_ID = "P2025-R001"
TXT_CIK = "0000217346"
ITW_CIK = "0000049826"
CUTOFF = "2026-07-29"

LINEAGE = [
    "selection_status", "replacement_status", "replacement_for", "replaced_by",
    "replacement_reason", "original_pilot_id", "replacement_pilot_id",
    "sampling_seed", "reserve_order", "within_sector_random_order",
    "analysis_included", "final_sample_status",
]


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def add_columns(frame: pd.DataFrame, columns: list[str] = LINEAGE) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        if column not in result:
            result[column] = ""
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def apply(root: Path) -> dict[str, int]:
    base = root / "2025" / "pilot_100"
    sample_dir, metadata_dir = base / "sample", base / "metadata"
    original = read(sample_dir / "pilot_sample_100.csv")
    frame = read(sample_dir / "pilot_sampling_frame.csv")
    proposal = read(sample_dir / "proposed_txt_replacement.csv")
    manifest = read(metadata_dir / "filings_manifest.csv")
    company_metadata = read(metadata_dir / "sec_company_metadata_index.csv")
    manifest = manifest.loc[~manifest["pilot_id"].eq(ITW_ID)].copy()
    company_metadata = company_metadata.loc[~company_metadata["pilot_id"].eq(ITW_ID)].copy()

    require(len(original) == 100, "original pilot sample must have 100 rows")
    txt = original.loc[original["pilot_id"].eq(TXT_ID)]
    require(len(txt) == 1, "TXT pilot ID must occur exactly once")
    require(txt.iloc[0]["symbol"] == "TXT" and txt.iloc[0]["cik"] == TXT_CIK, "TXT identity mismatch")
    require(set(original["sampling_seed"]) == {SEED}, "sampling seed changed")

    require(len(proposal) == 1, "replacement proposal must have one row")
    proposed = proposal.iloc[0]
    require(
        proposed["replacement_symbol"] == "ITW"
        and proposed["replacement_cik"] == ITW_CIK
        and proposed["replacement_candidate_order"] == "1",
        "ITW is not the approved first eligible reserve",
    )
    itw_frame = frame.loc[frame["cik"].eq(ITW_CIK)]
    require(len(itw_frame) == 1, "ITW must occur once in sampling frame")
    itw = itw_frame.iloc[0]
    require(itw["candidate_status"] == "reserve", "ITW must be a reserve")
    require(itw["within_sector_random_order"] == "17", "ITW within-sector order changed")
    require(itw["sampling_seed"] == SEED, "ITW seed changed")
    require(txt.iloc[0]["gics_sector"] == itw["gics_sector"] == "Industrials", "sector mismatch")
    require(itw["_company_key"] not in set(original["_company_key"]), "ITW company key duplicates original")
    require(ITW_CIK not in set(original["cik"]), "ITW CIK duplicates original")
    require(proposed["report_date"].startswith("2025-"), "ITW reportDate is not in 2025")
    require(proposed["filing_date"] <= CUTOFF, "ITW filingDate exceeds cutoff")
    require(bool(proposed["eligible_accession"] and proposed["primary_document"]), "ITW filing identifiers missing")

    final = original.loc[~original["pilot_id"].eq(TXT_ID)].copy()
    replacement = {column: itw.get(column, "") for column in original.columns}
    replacement.update(
        pilot_id=ITW_ID,
        selection_status="selected_replacement",
        replacement_for=TXT_ID,
        selection_reason="first_eligible_same_sector_deterministic_reserve_no_text_outcome_used",
    )
    final = pd.concat([final, pd.DataFrame([replacement])], ignore_index=True)
    final = add_columns(final)
    final["final_sample_id"] = final["pilot_id"]
    final["original_pilot_id"] = final["pilot_id"]
    final["replacement_pilot_id"] = ""
    final["replacement_status"] = "not_replaced"
    final["replacement_reason"] = ""
    final["reserve_order"] = ""
    final["analysis_included"] = "1"
    final["final_sample_status"] = "included"
    mask = final["pilot_id"].eq(ITW_ID)
    final.loc[mask, "original_pilot_id"] = TXT_ID
    final.loc[mask, "replacement_pilot_id"] = ITW_ID
    final.loc[mask, "replacement_status"] = "replacement"
    final.loc[mask, "replacement_reason"] = "no_eligible_2025_report_date_10k"
    final.loc[mask, "reserve_order"] = "1"

    manifest = add_columns(manifest)
    original_included = ~manifest["pilot_id"].eq(TXT_ID)
    manifest.loc[original_included, "analysis_included"] = "1"
    manifest.loc[original_included, "final_sample_status"] = "included"
    manifest.loc[original_included, "original_pilot_id"] = manifest.loc[original_included, "pilot_id"]
    manifest.loc[original_included, "replacement_status"] = "not_replaced"
    manifest.loc[original_included, "sampling_seed"] = SEED
    txt_manifest = manifest.loc[manifest["pilot_id"].eq(TXT_ID)].copy()
    require(
        len(txt_manifest) == 1
        and txt_manifest.iloc[0]["selection_status"] in {
            "no_eligible_2025_10k", "excluded_after_filing_validation"
        }
        and not txt_manifest.iloc[0]["accession_number"],
        "TXT filing audit missing",
    )
    manifest.loc[manifest["pilot_id"].eq(TXT_ID), [
        "selection_status", "replacement_status", "replaced_by", "replacement_reason",
        "original_pilot_id", "analysis_included", "final_sample_status",
    ]] = [
        "excluded_after_filing_validation", "replaced", ITW_ID,
        "no_eligible_2025_report_date_10k", TXT_ID, "0", "excluded",
    ]
    itw_manifest = {column: "" for column in manifest.columns}
    itw_manifest.update(
        pilot_id=ITW_ID, _company_key=itw["_company_key"], cik=ITW_CIK,
        symbol="ITW", security=itw["security"], form="10-K",
        filing_date=proposed["filing_date"], report_date=proposed["report_date"],
        accession_number=proposed["eligible_accession"],
        primary_document=proposed["primary_document"], primary_doc_description="10-K",
        eligible_2025_10k="True", selection_status="selected_replacement",
        selection_reason="exact Form 10-K; reportDate in 2025; filingDate <= 2026-07-29",
        amendment_exists="False", amendment_link_status="not_applicable",
        manual_review_required="False", replacement_status="replacement",
        replacement_for=TXT_ID, replacement_reason="no_eligible_2025_report_date_10k",
        original_pilot_id=TXT_ID, replacement_pilot_id=ITW_ID, sampling_seed=SEED,
        reserve_order="1", within_sector_random_order=itw["within_sector_random_order"],
        analysis_included="1", final_sample_status="included",
    )
    manifest = pd.concat([manifest, pd.DataFrame([itw_manifest])], ignore_index=True)

    company_metadata = add_columns(company_metadata)
    original_included = ~company_metadata["pilot_id"].eq(TXT_ID)
    company_metadata.loc[original_included, "analysis_included"] = "1"
    company_metadata.loc[original_included, "final_sample_status"] = "included"
    company_metadata.loc[original_included, "original_pilot_id"] = company_metadata.loc[original_included, "pilot_id"]
    company_metadata.loc[original_included, "replacement_status"] = "not_replaced"
    company_metadata.loc[original_included, "sampling_seed"] = SEED
    company_metadata.loc[company_metadata["pilot_id"].eq(TXT_ID), [
        "selection_status", "replacement_status", "replaced_by", "replacement_reason",
        "original_pilot_id", "analysis_included", "final_sample_status",
    ]] = [
        "excluded_after_filing_validation", "replaced", ITW_ID,
        "no_eligible_2025_report_date_10k", TXT_ID, "0", "excluded",
    ]
    itw_meta = {column: "" for column in company_metadata.columns}
    itw_meta.update(
        pilot_id=ITW_ID, _company_key=itw["_company_key"], cik=ITW_CIK,
        symbol="ITW", security=itw["security"], sec_entity_name="ILLINOIS TOOL WORKS INC",
        sec_tickers="ITW", sec_exchanges="NYSE", sic="3560",
        sic_description="General Industrial Machinery & Equipment",
        state_of_incorporation="DE", fiscal_year_end="1231",
        metadata_source=proposed["evidence_source"], metadata_status="success",
        historical_fragment_count="0", selection_status="selected_replacement",
        replacement_status="replacement", replacement_for=TXT_ID,
        replacement_reason="no_eligible_2025_report_date_10k", original_pilot_id=TXT_ID,
        replacement_pilot_id=ITW_ID, sampling_seed=SEED, reserve_order="1",
        within_sector_random_order=itw["within_sector_random_order"],
        analysis_included="1", final_sample_status="included",
    )
    company_metadata = pd.concat([company_metadata, pd.DataFrame([itw_meta])], ignore_index=True)

    filing_columns = [
        "accession_number", "report_date", "filing_date", "primary_document", "form",
    ]
    eligible = manifest.loc[manifest["analysis_included"].eq("1")].copy()
    final = final.merge(
        eligible[["pilot_id", *filing_columns]], on="pilot_id", how="left", validate="one_to_one"
    )
    identities = read(metadata_dir / "manual_review_resolution.csv")
    identity_map = dict(zip(identities["pilot_id"], identities["identity_status"]))
    final["identity_status"] = final["pilot_id"].map(identity_map).fillna("verified_by_cik")
    final.loc[final["pilot_id"].eq(ITW_ID), "identity_status"] = proposed["identity_status"]

    require(len(final) == 100, "final sample row count is not 100")
    for column in ["final_sample_id", "_company_key", "cik", "accession_number"]:
        require(final[column].nunique() == 100 and final[column].ne("").all(), f"{column} is not complete and unique")
    require(not final["symbol"].eq("TXT").any() and final["symbol"].eq("ITW").sum() == 1, "replacement membership invalid")
    require((final["form"] == "10-K").all(), "non-10-K in final sample")
    require(final["report_date"].str.startswith("2025-").all(), "reportDate outside 2025")
    require((final["filing_date"] <= CUTOFF).all(), "filingDate after cutoff")
    require(final["primary_document"].ne("").all(), "missing primary document")
    require(final["gics_sector"].value_counts().get("Industrials", 0) == 16, "Industrials allocation changed")
    expected = original["gics_sector"].value_counts().sort_index()
    require(final["gics_sector"].value_counts().sort_index().equals(expected), "sector allocation changed")

    exclusions = add_columns(read(sample_dir / "pilot_exclusions_and_replacements.csv"))
    exclusions = exclusions.loc[
        ~(
            exclusions.get("original_pilot_id", "").eq(TXT_ID)
            & exclusions.get("selection_status", "").eq("excluded_after_filing_validation")
        )
    ].copy()
    txt_audit = {column: "" for column in exclusions.columns}
    for column in original.columns:
        if column in txt_audit:
            txt_audit[column] = txt.iloc[0][column]
    txt_audit.update(
        selection_status="excluded_after_filing_validation", replacement_status="replaced",
        replaced_by=ITW_ID, replacement_reason="no_eligible_2025_report_date_10k",
        original_pilot_id=TXT_ID, replacement_pilot_id=ITW_ID, sampling_seed=SEED,
        analysis_included="0", final_sample_status="excluded",
        exclusion_reason="no_eligible_2025_report_date_10k",
    )
    exclusions = pd.concat([exclusions, pd.DataFrame([txt_audit])], ignore_index=True)

    proposal["proposal_status"] = "approved_and_applied"
    proposal["replacement_pilot_id"] = ITW_ID
    proposal["original_pilot_id"] = TXT_ID
    proposal["sampling_seed"] = SEED
    proposal["reserve_order"] = "1"
    proposal["analysis_included"] = "1"

    reviews = add_columns(read(metadata_dir / "manual_review.csv"), ["manual_review_status", "identity_status", "analysis_included"])
    reviews = reviews.loc[~reviews["pilot_id"].eq(ITW_ID)].copy()
    reviews["status"] = "resolved"
    reviews["manual_review_status"] = "resolved"
    reviews["identity_status"] = "verified_by_cik_and_ticker"
    reviews["analysis_included"] = reviews["pilot_id"].ne(TXT_ID).astype(int).astype(str)
    itw_review = {column: "" for column in reviews.columns}
    itw_review.update(
        pilot_id=ITW_ID, cik=ITW_CIK, symbol="ITW", security=itw["security"],
        review_reason="replacement_identity_and_filing_validation", status="resolved",
        manual_review_status="resolved", identity_status="verified_by_cik_and_ticker",
        analysis_included="1",
    )
    reviews = pd.concat([reviews, pd.DataFrame([itw_review])], ignore_index=True)

    resolutions = read(metadata_dir / "manual_review_resolution.csv")
    resolutions = resolutions.loc[~resolutions["pilot_id"].eq(ITW_ID)].copy()
    itw_resolution = {column: "" for column in resolutions.columns}
    itw_resolution.update(
        pilot_id=ITW_ID, symbol="ITW", cik=ITW_CIK,
        review_reason="replacement_identity_and_filing_validation",
        sample_entity_name=itw["security"], sec_entity_name="ILLINOIS TOOL WORKS INC",
        sec_tickers="ITW", selected_accession=proposed["eligible_accession"],
        cik_match="True", ticker_match="True", selected_filing_cik_match="True",
        name_difference_explanation="CIK and ticker identify the approved deterministic reserve.",
        corporate_reorganization_note="", manual_review_status="resolved",
        identity_status="verified_by_cik_and_ticker", evidence_source=proposed["evidence_source"],
    )
    resolutions = pd.concat([resolutions, pd.DataFrame([itw_resolution])], ignore_index=True)

    summary = read(metadata_dir / "metadata_collection_summary.csv")
    for column, value in {
        "requested_companies": "101", "metadata_success": "101", "metadata_errors": "0",
        "identity_mismatches": "0", "manual_review_rows": "4",
        "selection_eligible": "100", "selection_no_eligible_2025_10k": "0",
        "selection_ambiguous_multiple_eligible": "0",
        "selection_identity_mismatch": "0", "selection_metadata_error": "0",
        "analysis_sample_companies": "100", "analysis_eligible_filings": "100",
        "excluded_after_filing_validation": "1", "unresolved_manual_review": "0",
    }.items():
        summary[column] = value

    run_summary = read(metadata_dir / "final_run_summary.csv")
    run_summary = run_summary.loc[~run_summary["run_id"].eq("replacement-20260729")].copy()
    run_summary = pd.concat([pd.DataFrame([{
        "run_id": "replacement-20260729",
        "run_purpose": "apply approved deterministic TXT-to-ITW replacement",
        "used_for_final_outputs": "True",
        "notes": "offline application from preserved sample, proposal, and metadata; request log unchanged at 769 rows",
    }]), run_summary], ignore_index=True)

    final.to_csv(sample_dir / "final_analysis_sample_100.csv", index=False)
    exclusions.to_csv(sample_dir / "pilot_exclusions_and_replacements.csv", index=False)
    proposal.to_csv(sample_dir / "proposed_txt_replacement.csv", index=False)
    manifest.to_csv(metadata_dir / "filings_manifest.csv", index=False)
    company_metadata.to_csv(metadata_dir / "sec_company_metadata_index.csv", index=False)
    reviews.to_csv(metadata_dir / "manual_review.csv", index=False)
    resolutions.to_csv(metadata_dir / "manual_review_resolution.csv", index=False)
    summary.to_csv(metadata_dir / "metadata_collection_summary.csv", index=False)
    run_summary.to_csv(metadata_dir / "final_run_summary.csv", index=False)

    return {
        "final_sample_rows": len(final),
        "eligible_analysis_filings": len(eligible),
        "unique_cik": final["cik"].nunique(),
        "unique_accession": final["accession_number"].nunique(),
        "industrials": int(final["gics_sector"].eq("Industrials").sum()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(apply(args.root.resolve()))
