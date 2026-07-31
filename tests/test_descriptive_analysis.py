from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.run_descriptive_statistics import correlation_outputs, within_firm_changes


def test_within_changes_require_consecutive_years():
    frame = pd.DataFrame({
        "company_id": ["A", "A", "A", "B", "B"],
        "report_year": [2020, 2021, 2023, 2020, 2022],
        "whole_report_concreteness": [1.0, 1.5, 2.0, 1.0, 3.0],
        "past_tense_share": [0.2, 0.3, 0.4, 0.1, 0.2],
        "present_tense_share": [0.3, 0.2, 0.1, 0.4, 0.3],
        "future_tense_share": [0.5, 0.5, 0.5, 0.5, 0.5],
        "lm_uncertainty_share": [0.1, 0.2, 0.3, 0.1, 0.2],
        "passive_voice_sentence_share": [0.1, 0.2, 0.3, 0.2, 0.4],
        "fog_index": [10, 11, 12, 9, 10],
        "ai_sentence_count": [0, 2, 3, 1, 2],
        "ai_net_tone": [np.nan, .2, .3, .1, .2],
    })
    changes = within_firm_changes(frame)
    concreteness = changes[changes.variable == "whole_report_concreteness"]
    assert len(concreteness) == 1
    assert concreteness.iloc[0].paired_firm_count == 1
    assert concreteness.iloc[0].mean_within_firm_change == 0.5


def test_correlation_output_range_and_pairwise_n():
    frame = pd.DataFrame({"x": [1, 2, 3, 4], "y": [4, 3, 2, 1], "z": [1, np.nan, 2, 3]})
    matrix, pair_n, pvalues = correlation_outputs(frame, ["x", "y", "z"], "pearson", "fixture")
    assert np.allclose(matrix.loc["x", "y"], -1.0)
    assert matrix.equals(matrix.T)
    assert pair_n.loc["x", "z"] == 3
    assert all(abs(row["correlation"]) <= 1 for row in pvalues if pd.notna(row["correlation"]))
