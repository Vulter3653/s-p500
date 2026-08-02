import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_generated_summary_matches_panel():
    summary = json.loads((ROOT / "web/public/data/analysis-summary.json").read_text())
    assert summary["panel"]["observations"] == 2829
    assert [item["year"] for item in summary["years"]] == list(range(2020, 2026))


def test_generated_data_has_no_nonfinite_strings():
    for path in (ROOT / "web/public/data").glob("*.json"):
        text = path.read_text()
        assert "NaN" not in text and "Infinity" not in text and "None" not in text


def test_required_generated_files_exist():
    for name in ("analysis-summary.json", "yearly-statistics.json", "descriptive-statistics.json", "variable-definitions.json", "variable-definitions.csv", "source-manifest.json"):
        assert (ROOT / "web/public/data" / name).exists()


def test_dashboard_summary_normalizes_descriptive_statistics_fields():
    summary = json.loads((ROOT / "web/public/data/analysis-summary.json").read_text())
    first = summary["descriptiveTable"][0]
    for field in ("n", "sd", "q1", "q3", "kind", "label"):
        assert field in first


def test_source_paths_are_real_files():
    manifest = json.loads((ROOT / "web/public/data/source-manifest.json").read_text())
    for source in manifest["sources"]:
        assert (ROOT / source["source_file"]).exists()
