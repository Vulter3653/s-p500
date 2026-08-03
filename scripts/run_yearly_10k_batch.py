#!/usr/bin/env python3
"""Split and orchestrate one independent yearly 10-K batch."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from botocore.exceptions import ClientError

try:
    from .download_10k_html import HtmlDownloader, archive_url
    from .extract_10k_analysis_text import extract
    from .language_measurement_common import ROOT, write_csv
    from .load_brysbaert_concreteness_dictionary import (
        DEFAULT_PATH as BRYSBAERT_SOURCE,
        DIRECT_URL as BRYSBAERT_URL,
        EXPECTED_SHA256 as BRYSBAERT_SHA256,
        load_dictionary as load_brysbaert,
    )
    from .load_loughran_mcdonald_dictionary import (
        DEFAULT_PATH as LM_SOURCE,
        DIRECT_URL as LM_URL,
        EXPECTED_SHA256 as LM_SHA256,
        load_dictionary as load_lm,
    )
    from .load_smart_stopwords import (
        DEFAULT_PATH as SMART_SOURCE,
        EXPECTED_SHA256 as SMART_SHA256,
        TIDYTEXT_SOURCE_SHA256,
        load_smart_stopwords,
    )
except ImportError:
    from download_10k_html import HtmlDownloader, archive_url
    from extract_10k_analysis_text import extract
    from language_measurement_common import ROOT, write_csv
    from load_brysbaert_concreteness_dictionary import (
        DEFAULT_PATH as BRYSBAERT_SOURCE,
        DIRECT_URL as BRYSBAERT_URL,
        EXPECTED_SHA256 as BRYSBAERT_SHA256,
        load_dictionary as load_brysbaert,
    )
    from load_loughran_mcdonald_dictionary import (
        DEFAULT_PATH as LM_SOURCE,
        DIRECT_URL as LM_URL,
        EXPECTED_SHA256 as LM_SHA256,
        load_dictionary as load_lm,
    )
    from load_smart_stopwords import (
        DEFAULT_PATH as SMART_SOURCE,
        EXPECTED_SHA256 as SMART_SHA256,
        TIDYTEXT_SOURCE_SHA256,
        load_smart_stopwords,
    )


MAX_SAMPLE_SIZE = 503
BATCH_SIZE = 100
MAX_BATCH_COUNT = 6
TIDYTEXT_URL = (
    "https://cran.r-project.org/src/contrib/Archive/tidytext/tidytext_0.3.1.tar.gz"
)
LM_ANALYSIS = (
    ROOT
    / "references/dictionaries/loughran_mcdonald_master_dictionary/"
    "analysis_ready_dictionary/financial_language_categories_1993_2025.csv"
)
BRYSBAERT_ANALYSIS = (
    ROOT
    / "references/dictionaries/brysbaert_concreteness/"
    "analysis_ready_dictionary/brysbaert_concreteness_analysis_ready.csv"
)
SMART_ANALYSIS = (
    ROOT
    / "references/dictionaries/brysbaert_concreteness/"
    "analysis_ready_dictionary/smart_stopwords_tidytext_0.3.1.txt"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        rows = list(reader)
    if not fields:
        raise ValueError("sample manifest has no header")
    return fields, rows


def normalized_row(row: dict) -> dict:
    item = dict(row)
    item["final_sample_id"] = (
        item.get("final_sample_id") or item.get("company_id") or ""
    )
    item["company_id"] = item.get("company_id") or item["final_sample_id"]
    item["symbol"] = item.get("symbol") or item.get("ticker") or ""
    item["ticker"] = item.get("ticker") or item["symbol"]
    item["security"] = item.get("security") or item.get("company_name") or ""
    return item


def batch_count(row_count: int) -> int:
    if row_count < 1:
        raise ValueError("manifest must contain at least one row")
    if row_count > MAX_SAMPLE_SIZE:
        raise ValueError(
            f"manifest exceeds maximum sample size: {row_count} > {MAX_SAMPLE_SIZE}"
        )
    count = (row_count + BATCH_SIZE - 1) // BATCH_SIZE
    if count > MAX_BATCH_COUNT:
        raise ValueError(
            f"manifest requires too many batches: {count} > {MAX_BATCH_COUNT}"
        )
    return count


def validate_source_manifest(rows: list[dict], report_year: str) -> list[dict]:
    normalized = [normalized_row(row) for row in rows]
    batch_count(len(normalized))
    required = {
        "final_sample_id",
        "cik",
        "accession_number",
        "form",
        "report_date",
    }
    if not normalized:
        raise ValueError("manifest must contain at least one row")
    missing = required - set(normalized[0])
    if missing:
        raise ValueError(f"manifest missing columns: {sorted(missing)}")
    for field in ("final_sample_id", "cik", "accession_number"):
        values = [row.get(field, "") for row in normalized]
        if any(not value for value in values):
            raise ValueError(f"manifest contains an empty {field}")
        if len(values) != len(set(values)):
            raise ValueError(f"manifest contains duplicate {field}")
    for row in normalized:
        if row["form"] != "10-K":
            raise ValueError(f"non-10-K input: {row['final_sample_id']}")
        if not row["report_date"].startswith(f"{report_year}-"):
            raise ValueError(f"report year mismatch: {row['final_sample_id']}")
    return normalized


def split_batch(rows: list[dict], batch_id: int) -> list[dict]:
    total_batches = batch_count(len(rows))
    if batch_id < 1:
        raise ValueError("batch_id must be at least 1")
    if batch_id > total_batches:
        raise ValueError(
            f"batch_id {batch_id} exceeds manifest batch count {total_batches}"
        )
    start = (batch_id - 1) * BATCH_SIZE
    end = min(start + BATCH_SIZE, len(rows))
    return rows[start:end]


def validate_batch(rows: list[dict]) -> None:
    if len(rows) > BATCH_SIZE:
        raise ValueError("batch exceeds 100 rows")
    if not rows:
        return
    required = {"final_sample_id", "cik", "accession_number"}
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"batch manifest missing columns: {sorted(missing)}")
    for field in ("final_sample_id", "cik", "accession_number"):
        values = [row[field] for row in rows]
        if any(not value for value in values):
            raise ValueError(f"batch contains an empty {field}")
        if len(values) != len(set(values)):
            raise ValueError(f"batch contains duplicate {field}")


def write_batch_manifest(path: Path, fields: list[str], rows: list[dict]) -> None:
    output_fields = list(fields)
    for field in ("final_sample_id", "company_id", "symbol", "ticker", "security"):
        if field not in output_fields:
            output_fields.append(field)
    write_csv(path, rows, output_fields)


def stage_root(work_root: Path, report_year: str, sample_namespace: str) -> Path:
    return work_root / report_year / sample_namespace


def require_environment(names: tuple[str, ...]) -> None:
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            "required environment variables are not configured: "
            + ", ".join(missing)
        )


def r2_client():
    require_environment(
        (
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
            "R2_ENDPOINT_URL",
            "R2_BUCKET_NAME",
        )
    )
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(
            retries={"max_attempts": 5, "mode": "standard"},
            connect_timeout=20,
            read_timeout=120,
        ),
    )


def r2_key(report_year: str, sample_namespace: str, row: dict) -> str:
    return (
        f"{report_year}/{sample_namespace}/html/raw/{row['cik']}/"
        f"{row['accession_number']}.html"
    )


def remote_head(client, key: str):
    try:
        return client.head_object(
            Bucket=os.environ["R2_BUCKET_NAME"],
            Key=key,
        )
    except ClientError as error:
        status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        code = str(error.response.get("Error", {}).get("Code", ""))
        if status == 404 or code in {"404", "NoSuchKey", "NotFound"}:
            return None
        raise


def upload_without_overwrite(client, path: Path, key: str, row: dict) -> str:
    size = path.stat().st_size
    digest = sha256_file(path)
    existing = remote_head(client, key)
    if existing is not None:
        metadata = existing.get("Metadata", {})
        if (
            int(existing["ContentLength"]) == size
            and metadata.get("sha256", "").lower() == digest
        ):
            return "skipped_existing_sha_match"
        raise RuntimeError(
            f"R2 object conflict for accession {row['accession_number']}"
        )
    client.upload_file(
        str(path),
        os.environ["R2_BUCKET_NAME"],
        key,
        ExtraArgs={
            "ContentType": "text/html; charset=utf-8",
            "Metadata": {
                "sha256": digest,
                "source-size": str(size),
                "accession-number": row["accession_number"],
                "cik": row["cik"],
            },
        },
    )
    verified = remote_head(client, key)
    if (
        verified is None
        or int(verified["ContentLength"]) != size
        or verified.get("Metadata", {}).get("sha256", "").lower() != digest
    ):
        raise RuntimeError(
            f"R2 verification failed for accession {row['accession_number']}"
        )
    return "uploaded"


def validate_collection_rows(rows: list[dict], report_year: str) -> None:
    required = {
        "final_sample_id",
        "cik",
        "symbol",
        "accession_number",
        "primary_document",
        "form",
        "report_date",
    }
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"collection input missing columns: {sorted(missing)}")
    for row in rows:
        if row["form"] != "10-K":
            raise ValueError(f"non-10-K input: {row['final_sample_id']}")
        if not row["report_date"].startswith(f"{report_year}-"):
            raise ValueError(
                f"report year mismatch: {row['final_sample_id']}"
            )
        if not re.fullmatch(r"\d{10}", row["cik"]):
            raise ValueError(f"invalid CIK: {row['final_sample_id']}")
        if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", row["accession_number"]):
            raise ValueError(f"invalid accession: {row['final_sample_id']}")
        if "/" in row["primary_document"] or "\\" in row["primary_document"]:
            raise ValueError(
                f"primary document is not a basename: {row['final_sample_id']}"
            )


def collect_and_upload(
    work_root: Path,
    output_root: Path,
    rows: list[dict],
    report_year: str,
    sample_namespace: str,
) -> list[dict]:
    validate_collection_rows(rows, report_year)
    require_environment(("SEC_USER_AGENT",))
    client = r2_client()
    request_log = output_root / "collection/sec_request_log.jsonl"
    downloader = HtmlDownloader(
        user_agent=os.environ["SEC_USER_AGENT"],
        log_path=request_log,
    )
    html_manifest = []
    object_rows = []
    sample_root = stage_root(work_root, report_year, sample_namespace)
    for row in rows:
        accession = row["accession_number"]
        relative = Path(
            report_year,
            sample_namespace,
            "html",
            "raw",
            row["cik"],
            f"{accession}.html",
        )
        destination = work_root / relative
        payload, status, timestamp = downloader.download(
            archive_url(row["cik"], accession, row["primary_document"])
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        digest = sha256_file(destination)
        object_key = r2_key(report_year, sample_namespace, row)
        upload_status = upload_without_overwrite(
            client, destination, object_key, row
        )
        html_manifest.append(
            {
                "final_sample_id": row["final_sample_id"],
                "cik": row["cik"],
                "symbol": row["symbol"],
                "accession_number": accession,
                "primary_document": row["primary_document"],
                "html_path": relative.as_posix(),
                "sha256": digest,
                "file_size": destination.stat().st_size,
                "download_timestamp": timestamp,
                "http_status": status,
                "download_status": "downloaded",
            }
        )
        object_rows.append(
            {
                "company_id": row["final_sample_id"],
                "cik": row["cik"],
                "accession_number": accession,
                "object_key": object_key,
                "sha256": digest,
                "file_size": destination.stat().st_size,
                "upload_status": upload_status,
            }
        )
    write_csv(
        sample_root / "html/manifest/html_manifest.csv",
        html_manifest,
        list(html_manifest[0]),
    )
    write_csv(
        output_root / "collection/r2_object_manifest.csv",
        object_rows,
        list(object_rows[0]),
    )
    return object_rows


def download_html_from_r2(
    work_root: Path,
    output_root: Path,
    rows: list[dict],
    report_year: str,
    sample_namespace: str,
) -> list[dict]:
    client = r2_client()
    html_manifest = []
    object_rows = []
    sample_root = stage_root(work_root, report_year, sample_namespace)
    for row in rows:
        key = r2_key(report_year, sample_namespace, row)
        head = remote_head(client, key)
        if head is None:
            raise FileNotFoundError(
                f"R2 HTML missing for accession {row['accession_number']}"
            )
        digest = head.get("Metadata", {}).get("sha256", "")
        size = int(head["ContentLength"])
        if not digest or size <= 0:
            raise ValueError(
                f"R2 metadata incomplete for accession {row['accession_number']}"
            )
        relative = Path(
            report_year,
            sample_namespace,
            "html",
            "raw",
            row["cik"],
            f"{row['accession_number']}.html",
        )
        destination = work_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(
            os.environ["R2_BUCKET_NAME"], key, str(destination)
        )
        if destination.stat().st_size != size:
            raise ValueError(
                f"R2 download size mismatch for {row['accession_number']}"
            )
        html_manifest.append(
            {
                "final_sample_id": row["final_sample_id"],
                "cik": row["cik"],
                "symbol": row["symbol"],
                "accession_number": row["accession_number"],
                "primary_document": row["primary_document"],
                "html_path": relative.as_posix(),
                "sha256": digest,
                "file_size": size,
                "download_timestamp": utc_now(),
                "http_status": 200,
                "download_status": "skipped_sha_match",
            }
        )
        object_rows.append(
            {
                "company_id": row["final_sample_id"],
                "cik": row["cik"],
                "accession_number": row["accession_number"],
                "object_key": key,
                "sha256": digest,
                "file_size": size,
                "upload_status": "downloaded_for_extraction",
            }
        )
    write_csv(
        sample_root / "html/manifest/html_manifest.csv",
        html_manifest,
        list(html_manifest[0]),
    )
    write_csv(
        output_root / "collection/r2_object_manifest.csv",
        object_rows,
        list(object_rows[0]),
    )
    return object_rows


def filter_gzip_csv(source: Path, destination: Path, ids: set[str]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (
        gzip.open(source, "rt", encoding="utf-8", newline="") as input_handle,
        gzip.open(destination, "wt", encoding="utf-8", newline="") as output_handle,
    ):
        reader = csv.DictReader(input_handle)
        writer = csv.DictWriter(
            output_handle, fieldnames=reader.fieldnames, lineterminator="\n"
        )
        writer.writeheader()
        for row in reader:
            if row["company_id"] in ids:
                writer.writerow(row)


def find_existing_text_root(
    manifest_path: Path, report_year: str, sample_namespace: str = "sample_500"
) -> Path:
    candidates = [
        manifest_path.resolve().parent.parent / "text",
        ROOT / report_year / sample_namespace / "text",
        ROOT / report_year / "sample_500/text",
        ROOT / report_year / "pilot_100/text",
    ]
    for candidate in candidates:
        if (
            candidate / "extraction_results/company_text_extraction_results.csv"
        ).is_file():
            return candidate
    raise FileNotFoundError(
        "existing extracted text was not found; enable --run-extraction"
    )


def stage_existing_text(
    work_root: Path,
    manifest_path: Path,
    rows: list[dict],
    report_year: str,
    sample_namespace: str = "sample_500",
) -> None:
    source_text = find_existing_text_root(
        manifest_path, report_year, sample_namespace
    )
    ids = {row["final_sample_id"] for row in rows}
    extraction_path = (
        source_text
        / "extraction_results/company_text_extraction_results.csv"
    )
    fields, extraction_rows = read_manifest(extraction_path)
    selected = [row for row in extraction_rows if row["company_id"] in ids]
    if len(selected) != len(ids):
        raise ValueError("existing extraction results do not cover the batch")
    destination_text = stage_root(work_root, report_year, sample_namespace) / "text"
    staged_rows = []
    for row in selected:
        staged = dict(row)
        for field in ("analysis_text_file", "table_text_file"):
            source = ROOT / row[field]
            if not source.is_file():
                raise FileNotFoundError(f"missing existing {field}: {row[field]}")
            try:
                suffix = source.relative_to(source_text).as_posix()
            except ValueError:
                suffix = Path(row[field]).name
            destination = destination_text / suffix
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            staged[field] = destination.relative_to(work_root).as_posix()
        staged_rows.append(staged)
    write_csv(
        destination_text
        / "extraction_results/company_text_extraction_results.csv",
        staged_rows,
        fields,
    )
    filter_gzip_csv(
        source_text / "analysis_tables/sentences.csv.gz",
        destination_text / "analysis_tables/sentences.csv.gz",
        ids,
    )
    filter_gzip_csv(
        source_text / "analysis_tables/paragraphs.csv.gz",
        destination_text / "analysis_tables/paragraphs.csv.gz",
        ids,
    )


def download_file(url: str, destination: Path, expected_sha: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = Request(url, headers={"User-Agent": "s-p500-research-workflow"})
    with urlopen(request, timeout=180) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output)
    if sha256_file(temporary) != expected_sha:
        temporary.unlink(missing_ok=True)
        raise ValueError(f"download SHA mismatch for {destination.name}")
    temporary.replace(destination)


def ensure_language_resources() -> None:
    if LM_ANALYSIS.is_file() and BRYSBAERT_ANALYSIS.is_file() and SMART_ANALYSIS.is_file():
        return
    if not LM_SOURCE.is_file():
        download_file(LM_URL, LM_SOURCE, LM_SHA256)
    load_lm(write_analysis_file=True)
    if not BRYSBAERT_SOURCE.is_file():
        download_file(BRYSBAERT_URL, BRYSBAERT_SOURCE, BRYSBAERT_SHA256)
    load_brysbaert(write_analysis_file=True)
    if not SMART_SOURCE.is_file():
        archive = SMART_SOURCE.parent / "tidytext_0.3.1.tar.gz"
        if not archive.is_file():
            download_file(TIDYTEXT_URL, archive, TIDYTEXT_SOURCE_SHA256)
        with tarfile.open(archive, "r:gz") as bundle:
            member = bundle.getmember("tidytext/data/stop_words.rda")
            source = bundle.extractfile(member)
            if source is None:
                raise ValueError("stop_words.rda missing from tidytext archive")
            SMART_SOURCE.write_bytes(source.read())
        if sha256_file(SMART_SOURCE) != SMART_SHA256:
            raise ValueError("extracted SMART source SHA mismatch")
    load_smart_stopwords(write_analysis_file=True)


def copy_extraction_artifacts(
    work_root: Path,
    output_root: Path,
    report_year: str = "2025",
    sample_namespace: str = "sample_500",
) -> None:
    source = stage_root(work_root, report_year, sample_namespace) / "text"
    shutil.copytree(source, output_root / "extraction", dirs_exist_ok=True)


def run_language(
    work_root: Path,
    output_root: Path,
    report_year: str,
    sample_namespace: str = "sample_500",
) -> None:
    ensure_language_resources()
    environment = os.environ.copy()
    environment["S_P500_PIPELINE_ROOT"] = str(work_root)
    environment["S_P500_LANGUAGE_OUTPUT_DIR"] = str(
        output_root / "language"
    )
    environment["S_P500_REPORT_YEAR"] = report_year
    sample_root = stage_root(work_root, report_year, sample_namespace)
    environment["S_P500_LANGUAGE_SAMPLE_PATH"] = str(
        sample_root / "sample" / "batch_manifest.csv"
    )
    environment["S_P500_LANGUAGE_EXTRACTION_PATH"] = str(
        sample_root / "text/extraction_results/company_text_extraction_results.csv"
    )
    environment["S_P500_LANGUAGE_SENTENCE_PATH"] = str(
        sample_root / "text/analysis_tables/sentences.csv.gz"
    )
    environment["S_P500_LANGUAGE_PARAGRAPH_PATH"] = str(
        sample_root / "text/analysis_tables/paragraphs.csv.gz"
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_language_full_sample.py")],
        cwd=ROOT,
        env=environment,
        check=True,
    )


def write_empty_support_files(output_root: Path) -> None:
    write_csv(
        output_root / "collection/r2_object_manifest.csv",
        [],
        [
            "company_id",
            "cik",
            "accession_number",
            "object_key",
            "sha256",
            "file_size",
            "upload_status",
        ],
    )
    write_csv(
        output_root / "quality_check/failed_companies.csv",
        [],
        [
            "company_id",
            "cik",
            "accession_number",
            "failure_stage",
            "failure_reason",
        ],
    )
    write_csv(
        output_root / "quality_check/warning_cases.csv",
        [],
        ["company_id", "cik", "accession_number", "warning_type", "warning_detail"],
    )


def run_batch(arguments) -> dict:
    started = time.monotonic()
    manifest_path = arguments.manifest.resolve()
    output_root = arguments.output_dir.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    fields, source_rows = read_manifest(manifest_path)
    source_rows = validate_source_manifest(source_rows, arguments.report_year)
    rows = split_batch(source_rows, arguments.batch_id)
    validate_batch(rows)
    batch_manifest = output_root / "batch_manifest.csv"
    write_batch_manifest(batch_manifest, fields, rows)
    write_empty_support_files(output_root)
    summary = {
        "report_year": arguments.report_year,
        "sample_namespace": arguments.sample_namespace,
        "batch_id": arguments.batch_id,
        "source_manifest": manifest_path.name,
        "source_rows": len(source_rows),
        "manifest_row_count": len(source_rows),
        "batch_size_limit": BATCH_SIZE,
        "batch_count": batch_count(len(source_rows)),
        "batch_start_index": (arguments.batch_id - 1) * BATCH_SIZE,
        "batch_end_index_exclusive": (
            (arguments.batch_id - 1) * BATCH_SIZE + len(rows)
        ),
        "batch_row_count": len(rows),
        "maximum_sample_size": MAX_SAMPLE_SIZE,
        "duplicate_count": 0,
        "missing_count": 0,
        "batch_rows": len(rows),
        "row_start": (arguments.batch_id - 1) * BATCH_SIZE + 1,
        "row_end": (arguments.batch_id - 1) * BATCH_SIZE + len(rows),
        "run_collection": arguments.run_collection,
        "run_extraction": arguments.run_extraction,
        "run_language": arguments.run_language,
        "force": arguments.force,
        "status": "empty" if not rows else "success",
        "failed_stage": "",
        "error_type": "",
        "elapsed_seconds": 0,
        "completed_at": "",
    }
    if not rows:
        summary["elapsed_seconds"] = round(time.monotonic() - started, 3)
        summary["completed_at"] = utc_now()
        (output_root / "batch_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(summary, sort_keys=True))
        return summary

    failed_stage = "preparation"
    try:
        with tempfile.TemporaryDirectory(
            prefix=f"s-p500-{arguments.report_year}-batch-{arguments.batch_id}-"
        ) as temporary:
            work_root = Path(temporary)
            sample_root = stage_root(
                work_root, arguments.report_year, arguments.sample_namespace
            )
            fixed_sample = sample_root / "sample/batch_manifest.csv"
            write_batch_manifest(fixed_sample, fields, rows)
            if arguments.run_collection:
                failed_stage = "collection"
                collect_and_upload(
                    work_root,
                    output_root,
                    rows,
                    arguments.report_year,
                    arguments.sample_namespace,
                )
            if arguments.run_extraction:
                failed_stage = "extraction_input"
                if not arguments.run_collection:
                    download_html_from_r2(
                        work_root,
                        output_root,
                        rows,
                        arguments.report_year,
                        arguments.sample_namespace,
                    )
                failed_stage = "extraction"
                extraction_summary = extract(
                    work_root,
                    input_relative=sample_root.relative_to(work_root)
                    / "html/manifest/html_manifest.csv",
                    output_relative=sample_root.relative_to(work_root) / "text",
                    retry_warning=arguments.force,
                    retry_failed=arguments.force,
                )
                if int(extraction_summary["failed"]):
                    raise RuntimeError("one or more extraction records failed")
                copy_extraction_artifacts(
                    work_root,
                    output_root,
                    arguments.report_year,
                    arguments.sample_namespace,
                )
            if arguments.run_language:
                failed_stage = "language_input"
                if not arguments.run_extraction:
                    stage_existing_text(
                        work_root,
                        manifest_path,
                        rows,
                        arguments.report_year,
                        arguments.sample_namespace,
                    )
                failed_stage = "language"
                run_language(
                    work_root,
                    output_root,
                    arguments.report_year,
                    arguments.sample_namespace,
                )
        failed_stage = ""
    except Exception as error:
        summary["status"] = "failed"
        summary["failed_stage"] = failed_stage
        summary["error_type"] = type(error).__name__
        write_csv(
            output_root / "quality_check/failed_companies.csv",
            [
                {
                    "company_id": row["final_sample_id"],
                    "cik": row["cik"],
                    "accession_number": row["accession_number"],
                    "failure_stage": failed_stage,
                    "failure_reason": type(error).__name__,
                }
                for row in rows
            ],
            [
                "company_id",
                "cik",
                "accession_number",
                "failure_stage",
                "failure_reason",
            ],
        )
        summary["elapsed_seconds"] = round(time.monotonic() - started, 3)
        summary["completed_at"] = utc_now()
        (output_root / "batch_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(summary, sort_keys=True))
        raise

    summary["elapsed_seconds"] = round(time.monotonic() - started, 3)
    summary["completed_at"] = utc_now()
    (output_root / "batch_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))
    return summary


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-year", required=True)
    parser.add_argument("--batch-id", required=True, type=int)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--sample-namespace", default="sample_500")
    parser.add_argument("--run-collection", action="store_true")
    parser.add_argument("--run-extraction", action="store_true")
    parser.add_argument("--run-language", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--output-dir", required=True, type=Path)
    arguments = parser.parse_args()
    if not re.fullmatch(r"\d{4}", arguments.report_year):
        parser.error("--report-year must be a four-digit year")
    if arguments.batch_id < 1:
        parser.error("--batch-id must be at least 1")
    return arguments


if __name__ == "__main__":
    try:
        run_batch(parse_arguments())
    except Exception as error:
        print(f"batch_failed={type(error).__name__}", file=sys.stderr)
        raise SystemExit(1)
