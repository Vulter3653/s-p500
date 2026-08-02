import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_variable_definitions_cover_panel_columns():
    panel_columns = __import__("pandas").read_csv(ROOT / "analysis/descriptive_2020_2025/firm_year_language_extended.csv", nrows=0).columns
    definitions = json.loads((ROOT / "web/public/data/variable-definitions.json").read_text())
    defined = {item["variable"]: item for item in definitions}
    assert set(panel_columns) == set(defined)
    for item in definitions:
        assert item.get("formula")
        assert item.get("missing_rule")
        assert item.get("source_scripts")
        assert set(item.get("source_columns", [])) <= set(panel_columns)


def test_core_definitions_have_detailed_fields():
    definitions = {item["variable"]: item for item in json.loads((ROOT / "web/public/data/variable-definitions.json").read_text())}
    for name in ("fog_index", "past_tense_share", "passive_voice_sentence_share", "lm_uncertainty_share", "whole_report_concreteness"):
        item = definitions[name]
        assert item["numerator"]
        assert item["denominator"]
        assert item["method"]
        assert item["limitation"]


def test_dashboard_navigation_contains_research_pages():
    app = (ROOT / "web/src/App.jsx").read_text()
    for page in ("#variables", "#methods", "#results", "#reproducibility", "#limitations"):
        assert page in app
