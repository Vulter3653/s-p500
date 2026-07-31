from pathlib import Path
import re


ROOT = Path("analysis/descriptive_2020_2025")
REPORTS = [
    ROOT / "descriptive_analysis_report.md",
    ROOT / "descriptive_tables.md",
    ROOT / "run_summary.md",
    ROOT / "measurement_notes.md",
    ROOT / "limitations.md",
]


def test_markdown_has_no_raw_missing_values():
    text = "\n".join(path.read_text(encoding="utf-8") for path in REPORTS)
    assert not re.search(r"(?i)(?<![A-Za-z])(nan|none|null)(?![A-Za-z])", text)


def test_markdown_year_counts_are_integers():
    text = (ROOT / "descriptive_tables.md").read_text(encoding="utf-8")
    assert "2020.0000" not in text
    assert "2020 |" in text
    assert "446 |" in text


def test_report_tables_are_split_into_korean_panels():
    text = (ROOT / "descriptive_analysis_report.md").read_text(encoding="utf-8")
    for title in ["패널 A: 표본과 AI 공시", "패널 B: 구체성 및 시제", "패널 C: 불확실성·수동태·가독성", "패널 D: AI 직접 문장 감성"]:
        assert title in text
    assert re.search(r"\|\s+보고연도", text)
    assert "|   report_year" not in text
