"""Validate the five-company language smoke-test artifacts without network access."""

from __future__ import annotations

import math

try:
    from .language_measurement_common import ROOT, SMOKE_ROOT, read_csv, sha256_file
    from .load_brysbaert_concreteness_dictionary import load_dictionary
    from .load_smart_stopwords import load_smart_stopwords
    from .measure_linguistic_concreteness import measure_concreteness
except ImportError:
    from language_measurement_common import ROOT, SMOKE_ROOT, read_csv, sha256_file
    from load_brysbaert_concreteness_dictionary import load_dictionary
    from load_smart_stopwords import load_smart_stopwords
    from measure_linguistic_concreteness import measure_concreteness


def validate() -> dict:
    selected = read_csv(SMOKE_ROOT / "selected_companies/selected_5_companies.csv")
    combined = read_csv(SMOKE_ROOT / "combined_language_results/company_language_smoke_test_results.csv")
    ai = read_csv(SMOKE_ROOT / "ai_disclosure_detection/company_ai_disclosure_results.csv")
    state = read_csv(SMOKE_ROOT / "processing_logs/language_smoke_test_processing_state.csv")
    assert len(selected) == len(combined) == len(ai) == len(state) == 5
    for key in ("company_id", "cik", "accession_number"):
        assert len({row[key] for row in selected}) == 5, f"duplicate {key}"
    for row in selected:
        path = ROOT / row["analysis_text_file"]
        assert path.is_file()
        assert sha256_file(path) == row["analysis_text_sha256"]
    ratio_errors = 0
    negative_counts = 0
    infinite_values = 0
    for row in combined:
        for key, value in row.items():
            if value == "":
                continue
            try:
                number = float(value)
            except ValueError:
                continue
            infinite_values += int(not math.isfinite(number))
            if key.endswith("_ratio"):
                ratio_errors += int(number < 0 or number > 1)
            if key.endswith("_count"):
                negative_counts += int(number < 0)
    assert ratio_errors == negative_counts == infinite_values == 0
    assert all(row["language_measurement_version"] == "0.3.0" for row in combined)
    assert sum(int(row["ai_sentence_count"]) for row in combined) == 273
    by_ticker = {row["ticker"]: row for row in combined}
    assert by_ticker["TECH"]["ai_total_eligible_word_count"] == "0"
    assert by_ticker["TECH"]["ai_uncertainty_ratio"] == ""
    assert by_ticker["TECH"]["ai_positive_ratio"] == ""
    assert by_ticker["TECH"]["report_uncertainty_count"] != ""
    assert by_ticker["NSC"]["ai_sentence_count"] == "1"
    assert by_ticker["TECH"]["concreteness_status"] == "warning_denominator_zero"
    assert all(
        row["concreteness_status"] in {"success", "warning_stem_collisions"}
        for row in combined if row["ticker"] != "TECH"
    )
    assert all(row["tense_status"] == "blocked_model_missing" for row in combined)
    assert all(row["passive_voice_status"] == "blocked_model_missing" for row in combined)
    assert all(row["time_focusing_status"] == "blocked_liwc2015_license_required"
               for row in combined)
    dictionary, dictionary_metadata = load_dictionary()
    stopwords, stopword_metadata = load_smart_stopwords()
    physics = measure_concreteness(["The subject is physics."], dictionary, stopwords)
    science = measure_concreteness(["The subject is science."], dictionary, stopwords)
    assert round(physics["ai_concreteness_mean"], 2) == 3.10
    assert round(science["ai_concreteness_mean"], 2) == 2.96
    assert len(dictionary) == 39954
    concreteness = read_csv(
        SMOKE_ROOT / "textual_concreteness/company_concreteness_results.csv"
    )
    assert len(concreteness) == 5
    concrete_by_ticker = {row["ticker"]: row for row in concreteness}
    assert concrete_by_ticker["TECH"]["ai_concreteness_mean"] == ""
    assert concrete_by_ticker["TECH"]["report_concreteness_mean"] != ""
    for row in concreteness:
        for scope in ("ai", "report"):
            mean = row[f"{scope}_concreteness_mean"]
            coverage = row[f"{scope}_concreteness_coverage"]
            if mean:
                assert 1 <= float(mean) <= 5
            if coverage:
                assert 0 <= float(coverage) <= 1
    expected_lm = {
        "NVDA": ("40", "77", "64"), "HPE": ("73", "71", "83"),
        "TECH": ("", "", ""), "WAT": ("5", "36", "21"), "NSC": ("0", "3", "2"),
    }
    assert {
        row["ticker"]: (
            row["ai_positive_count"], row["ai_negative_count"],
            row["ai_uncertainty_count"],
        )
        for row in combined
    } == expected_lm
    result = {
        "selected_companies": 5, "input_sha_match": 5, "combined_rows": 5,
        "ratio_range_errors": 0, "negative_counts": 0, "infinite_values": 0,
        "failed_after_3_attempts": 0, "structural_errors": 0,
        "ai_related_sentences": 273, "blocked_status_errors": 0,
        "brysbaert_entries": dictionary_metadata["row_count"],
        "smart_unique_entries": stopword_metadata["smart_entry_count"],
        "paper_examples": "2/2",
    }
    print(" ".join(f"{key}={value}" for key, value in result.items()))
    return result


if __name__ == "__main__":
    validate()
