from pathlib import Path
from types import SimpleNamespace
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import run_yearly_10k_batch as runner


def test_extraction_failure_diagnostics_survive_temporary_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "final_sample_id,company_id,cik,symbol,ticker,security,"
        "accession_number,primary_document,form,report_date\n"
        "TEST,TEST,0000000001,TST,TST,Test Company,"
        "0000000001-10-000001,test10k.htm,10-K,2010-12-31\n",
        encoding="utf-8",
    )
    output_root = tmp_path / "output"
    arguments = SimpleNamespace(
        report_year="2010",
        batch_id=1,
        manifest=manifest,
        sample_namespace="sample_503",
        run_collection=True,
        run_extraction=True,
        run_language=False,
        force=False,
        output_dir=output_root,
    )

    def fake_collect(
        work_root, output_root, rows, report_year, sample_namespace
    ):
        sample_root = runner.stage_root(
            work_root, report_year, sample_namespace
        )
        html_manifest = sample_root / "html/manifest"
        html_manifest.mkdir(parents=True, exist_ok=True)
        (html_manifest / "html_manifest.csv").write_text(
            "final_sample_id,cik,accession_number\n"
            "TEST,0000000001,0000000001-10-000001\n",
            encoding="utf-8",
        )
        return []

    def fake_extract(work_root, **kwargs):
        sample_root = runner.stage_root(
            work_root, "2010", "sample_503"
        )
        extraction_results = sample_root / "text/extraction_results"
        processing_logs = sample_root / "text/processing_logs"
        analysis_tables = sample_root / "text/analysis_tables"
        extraction_results.mkdir(parents=True, exist_ok=True)
        processing_logs.mkdir(parents=True, exist_ok=True)
        analysis_tables.mkdir(parents=True, exist_ok=True)
        (
            extraction_results
            / "company_text_extraction_results.csv"
        ).write_text(
            "company_id,extraction_status\n"
            "TEST,failed_after_3_attempts\n",
            encoding="utf-8",
        )
        (processing_logs / "text_extraction_log.jsonl").write_text(
            '{"company_id":"TEST","error":"forced parser failure"}\n',
            encoding="utf-8",
        )
        (analysis_tables / "sections.csv").write_text(
            "company_id,section_code\n",
            encoding="utf-8",
        )
        raise ValueError("forced parser failure")

    monkeypatch.setattr(runner, "collect_and_upload", fake_collect)
    monkeypatch.setattr(runner, "extract", fake_extract)

    with pytest.raises(ValueError, match="forced parser failure"):
        runner.run_batch(arguments)

    diagnostics = output_root / "extraction_diagnostics"
    metadata = json.loads(
        (diagnostics / "diagnostic_metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert metadata["failed_stage"] == "extraction"
    assert metadata["exception_type"] == "ValueError"
    assert metadata["exception_message"] == "forced parser failure"
    assert not Path(metadata["temporary_root"]).exists()
    assert "forced parser failure" in (
        diagnostics / "traceback.txt"
    ).read_text(encoding="utf-8")
    assert (
        diagnostics / "html_manifest/html_manifest.csv"
    ).is_file()
    assert (
        diagnostics
        / "extraction_results/company_text_extraction_results.csv"
    ).is_file()
    assert (
        diagnostics
        / "processing_logs/text_extraction_log.jsonl"
    ).is_file()
    assert (
        diagnostics / "analysis_tables/sections.csv"
    ).is_file()


def test_core_runner_api_remains_available():
    assert runner.batch_count(46) == 1
    assert runner.MAX_SAMPLE_SIZE == 503
