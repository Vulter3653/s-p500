from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import pytest

from scripts.continuous_backfill import (
    annual_ai_keyword_count,
    append_panel,
    canonicalize_panel,
    next_year,
    update_zero_streak,
)


def test_descending_year_and_lower_bound():
    assert next_year(2019, [], 1900) == 2018
    assert next_year(2018, [2019, 2018], 2018) is None
    with pytest.raises(ValueError):
        next_year(2018, [2017], 1900)


def test_zero_streak_is_fail_closed():
    assert update_zero_streak(0, "success", 0) == 1
    assert update_zero_streak(1, "success", 0) == 2
    assert update_zero_streak(2, "success", 0) == 3
    assert update_zero_streak(2, "success", 4) == 0
    with pytest.raises(ValueError):
        update_zero_streak(2, "partial", 0)
    with pytest.raises(ValueError):
        update_zero_streak(2, "success", None)


def test_keyword_count_does_not_treat_missing_as_zero():
    assert annual_ai_keyword_count(pd.DataFrame({"ai_term_count": [0, 2, 3]})) == 5
    with pytest.raises(ValueError):
        annual_ai_keyword_count(pd.DataFrame({"ai_term_count": [0, None]}))


def test_atomic_panel_append_preserves_rows(tmp_path: Path):
    prior = pd.DataFrame({
        "company_id": ["A"], "report_year": [2020],
        "accession_number": ["a"], "ai_term_count": [3],
    })
    current = pd.DataFrame({
        "company_id": ["B"], "report_year": [2019],
        "accession_number": ["b"], "ai_term_count": [0],
    })
    prior_path = tmp_path / "prior.csv"
    current_path = tmp_path / "current.csv"
    output_path = tmp_path / "candidate.csv"
    prior.to_csv(prior_path, index=False)
    current.to_csv(current_path, index=False)
    result = append_panel(prior_path, current_path, output_path)
    assert result["candidate_rows"] == 2
    result_frame = pd.read_csv(output_path)
    assert result_frame["report_year"].tolist() == [2019, 2020]


def test_canonical_mapping_reuses_existing_measurement_columns():
    prior = pd.DataFrame({
        "company_id": ["A"], "report_year": [2020], "accession_number": ["a"],
        "ai_sentence_count": [2], "ai_term_count": [4],
        "ai_disclosure_flag": [1],
        "whole_report_concreteness": [2.5],
        "fog_index": [20.0],
    })
    current = pd.DataFrame({
        "company_id": ["B"], "report_year": [2019], "accession_number": ["b"],
        "ai_sentence_count": [1], "ai_term_count": [3],
        "report_concreteness_mean": [2.4],
        "report_fog_index": [19.0],
    })
    mapped = canonicalize_panel(current, prior)
    assert mapped["ai_disclosure_flag"].tolist() == [1]
    assert mapped["whole_report_concreteness"].tolist() == [2.4]
    assert mapped["fog_index"].tolist() == [19.0]
    assert list(mapped.columns) == list(prior.columns)


def test_canonical_mapping_fails_closed_for_missing_measurement():
    prior = pd.DataFrame({
        "company_id": ["A"], "report_year": [2020], "accession_number": ["a"],
        "whole_report_concreteness": [2.5],
    })
    current = pd.DataFrame({
        "company_id": ["B"], "report_year": [2019], "accession_number": ["b"],
    })
    with pytest.raises(ValueError, match="canonical columns"):
        canonicalize_panel(current, prior)
