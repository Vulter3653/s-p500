from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import pytest

from scripts.continuous_backfill import (
    annual_ai_keyword_count,
    append_panel,
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

