import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_figure_manifest_has_core_figures_and_sources():
    manifest = json.loads((ROOT / "web/public/data/figure-manifest.json").read_text(encoding="utf-8"))
    assert [item["figure_id"] for item in manifest] == [f"figure-{index:02d}" for index in range(1, 8)]
    for item in manifest:
        assert item["source_file"]
        assert item["source_sha256"]
        assert item["source_columns"]
        assert item["generation_script"] == "scripts/generate_web_analysis_data.py"


def test_figure_data_contains_no_non_finite_values():
    payload = json.loads((ROOT / "web/public/data/figure-data.json").read_text(encoding="utf-8"))
    text = json.dumps(payload, ensure_ascii=False).lower()
    assert "nan" not in text
    assert "infinity" not in text
    assert "-infinity" not in text
