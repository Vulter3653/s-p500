from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from merge_yearly_10k_batches import merge  # noqa: E402
from run_yearly_10k_batch import (  # noqa: E402
    BATCH_SIZE,
    MAX_BATCH_COUNT,
    MAX_SAMPLE_SIZE,
    batch_count,
    run_batch,
    split_batch,
    validate_source_manifest,
)
import run_yearly_10k_batch as yearly_runner  # noqa: E402


def make_rows(count: int, year: str = "2019") -> list[dict]:
    return [
        {
            "sample_order": str(index + 1),
            "company_id": f"C{index + 1:03d}",
            "final_sample_id": f"C{index + 1:03d}",
            "symbol": f"T{index + 1:03d}",
            "security": f"Company {index + 1}",
            "cik": f"{index + 1:010d}",
            "accession_number": f"0000000000-19-{index + 1:06d}",
            "form": "10-K",
            "report_date": f"{year}-12-31",
            "filing_date": f"{int(year) + 1}-02-01",
            "primary_document": f"doc-{index + 1}.htm",
        }
        for index in range(count)
    ]


@pytest.mark.parametrize(
    ("row_count", "expected_batches"),
    [(1, 1), (100, 1), (101, 2), (500, 5), (501, 6), (502, 6), (503, 6)],
)
def test_batch_count_supports_up_to_503(row_count, expected_batches):
    assert batch_count(row_count) == expected_batches


@pytest.mark.parametrize("row_count", [0, 504])
def test_batch_count_rejects_out_of_range(row_count):
    with pytest.raises(ValueError):
        batch_count(row_count)


def test_503_rows_are_split_in_manifest_order():
    rows = make_rows(MAX_SAMPLE_SIZE)
    batches = [split_batch(rows, batch_id) for batch_id in range(1, 7)]
    assert [len(batch) for batch in batches] == [100, 100, 100, 100, 100, 3]
    assert [row["sample_order"] for batch in batches for row in batch] == [
        str(index) for index in range(1, 504)
    ]
    assert sum(len(batch) for batch in batches) == MAX_SAMPLE_SIZE


@pytest.mark.parametrize("batch_id", [0, -1, 7])
def test_invalid_batch_ids_are_rejected(batch_id):
    with pytest.raises(ValueError):
        split_batch(make_rows(MAX_SAMPLE_SIZE), batch_id)


def test_manifest_validation_rejects_duplicates_and_wrong_year():
    rows = make_rows(2)
    rows[1]["cik"] = rows[0]["cik"]
    with pytest.raises(ValueError, match="duplicate cik"):
        validate_source_manifest(rows, "2019")

    rows = make_rows(1)
    rows[0]["report_date"] = "2018-12-31"
    with pytest.raises(ValueError, match="report year mismatch"):
        validate_source_manifest(rows, "2019")


def test_batch_summary_contains_503_metadata_and_dynamic_stage(tmp_path):
    manifest = tmp_path / "manifest.csv"
    rows = make_rows(MAX_SAMPLE_SIZE)
    fields = list(rows[0])
    manifest.write_text(
        ",".join(fields)
        + "\n"
        + "\n".join(",".join(row[field] for field in fields) for row in rows)
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "output"
    summary = run_batch(
        SimpleNamespace(
            manifest=manifest,
            output_dir=output,
            report_year="2019",
            sample_namespace="sample_503",
            batch_id=6,
            run_collection=False,
            run_extraction=False,
            run_language=False,
            force=False,
        )
    )
    assert summary["batch_count"] == MAX_BATCH_COUNT
    assert summary["batch_row_count"] == 3
    assert summary["batch_start_index"] == 500
    assert summary["batch_end_index_exclusive"] == 503
    batch_rows = (output / "batch_manifest.csv").read_text(encoding="utf-8").splitlines()
    assert len(batch_rows) == 4


def test_merge_accepts_six_batches_and_preserves_ranges(tmp_path):
    input_root = tmp_path / "input"
    for batch_id in range(1, 7):
        directory = input_root / f"batch_{batch_id}"
        directory.mkdir(parents=True)
        start = (batch_id - 1) * BATCH_SIZE
        end = min(start + BATCH_SIZE, MAX_SAMPLE_SIZE)
        (directory / "batch_summary.json").write_text(
            json.dumps(
                {
                    "batch_id": batch_id,
                    "status": "success",
                    "manifest_row_count": MAX_SAMPLE_SIZE,
                    "batch_count": MAX_BATCH_COUNT,
                    "batch_start_index": start,
                    "batch_end_index_exclusive": end,
                    "batch_row_count": end - start,
                }
            ),
            encoding="utf-8",
        )
    summary = merge(
        input_root,
        tmp_path / "merged",
        "2019",
        expected_batches=set(range(1, 7)),
    )
    assert summary["merge_status"] == "completed"
    assert summary["missing_batches"] == []
    assert summary["manifest_row_count"] == MAX_SAMPLE_SIZE
    assert summary["batch_count"] == MAX_BATCH_COUNT
    assert [item["end_index_exclusive"] for item in summary["batch_ranges"]] == [
        100,
        200,
        300,
        400,
        500,
        503,
    ]


def test_collection_uses_dynamic_year_namespace_paths(monkeypatch, tmp_path):
    payload = b"<html>dynamic path fixture</html>"

    class Downloader:
        def __init__(self, **_kwargs):
            pass

        def download(self, _url):
            return payload, 200, "2026-08-02T00:00:00+00:00"

    class Client:
        def __init__(self):
            self.uploaded = {}

        def head_object(self, **kwargs):
            key = kwargs["Key"]
            if key not in self.uploaded:
                from botocore.exceptions import ClientError

                raise ClientError(
                    {"Error": {"Code": "404"}, "ResponseMetadata": {"HTTPStatusCode": 404}},
                    "HeadObject",
                )
            data = self.uploaded[key]
            return {"ContentLength": len(data), "Metadata": {"sha256": yearly_runner.hashlib.sha256(data).hexdigest()}}

        def upload_file(self, path, _bucket, key, **_kwargs):
            self.uploaded[key] = Path(path).read_bytes()

    client = Client()
    monkeypatch.setattr(yearly_runner, "HtmlDownloader", Downloader)
    monkeypatch.setattr(yearly_runner, "r2_client", lambda: client)
    monkeypatch.setenv("SEC_USER_AGENT", "fixture-agent")
    monkeypatch.setenv("R2_BUCKET_NAME", "fixture-bucket")
    rows = make_rows(1)
    output_root = tmp_path / "output"
    result = yearly_runner.collect_and_upload(
        tmp_path / "work", output_root, rows, "2019", "sample_503"
    )
    assert result[0]["object_key"].startswith("2019/sample_503/html/raw/")
    html_path = tmp_path / "work/2019/sample_503/html/manifest/html_manifest.csv"
    assert html_path.is_file()
    assert "2019/sample_503/html/raw" in html_path.read_text(encoding="utf-8")
