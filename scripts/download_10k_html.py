#!/usr/bin/env python3
"""Download the 100 final-pilot SEC 10-K primary HTML documents."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

INPUT_RELATIVE = Path("2025/pilot_100/sample/final_analysis_sample_100.csv")
OUTPUT_RELATIVE = Path("2025/pilot_100/html")
CUTOFF = "2026-07-29"
RETRYABLE = {429, 500, 502, 503}
ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")

MANIFEST_COLUMNS = [
    "final_sample_id", "cik", "symbol", "accession_number",
    "primary_document", "html_path", "sha256", "file_size",
    "download_timestamp", "http_status", "download_status",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_user_agent(value: str | None = None) -> str:
    user_agent = value if value is not None else os.environ.get("SEC_USER_AGENT", "")
    if not user_agent.strip():
        raise ValueError("SEC_USER_AGENT is not set")
    return user_agent.strip()


def archive_url(cik: str, accession: str, primary_document: str) -> str:
    return (
        "https://www.sec.gov/Archives/edgar/data/"
        f"{int(cik)}/{accession.replace('-', '')}/{primary_document}"
    )


def validate_input(frame: pd.DataFrame) -> None:
    required = {
        "final_sample_id", "cik", "symbol", "accession_number",
        "primary_document", "form", "report_date", "filing_date",
        "analysis_included",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"input missing columns: {sorted(missing)}")
    if len(frame) != 100:
        raise ValueError("final analysis input must contain exactly 100 rows")
    if frame["final_sample_id"].duplicated().any():
        raise ValueError("final sample IDs are not unique")
    if frame["cik"].duplicated().any():
        raise ValueError("CIKs are not unique")
    if frame["accession_number"].duplicated().any():
        raise ValueError("accessions are not unique")
    if not frame["cik"].str.fullmatch(r"\d{10}").all():
        raise ValueError("CIK format error")
    if not frame["accession_number"].map(lambda value: bool(ACCESSION_RE.fullmatch(value))).all():
        raise ValueError("accession format error")
    if not frame["primary_document"].str.fullmatch(r"[^/\\]+").all():
        raise ValueError("primary document must be a basename")
    if not frame["form"].eq("10-K").all():
        raise ValueError("input contains a non-10-K filing")
    if not frame["report_date"].str.startswith("2025-").all():
        raise ValueError("input reportDate is outside 2025")
    if not frame["filing_date"].le(CUTOFF).all():
        raise ValueError("input filingDate exceeds cutoff")
    if not frame["analysis_included"].eq("1").all():
        raise ValueError("input contains an excluded company")


class HtmlDownloader:
    def __init__(
        self,
        *,
        user_agent: str,
        log_path: Path,
        interval: float = 1.0,
        timeout: float = 60.0,
        max_retries: int = 4,
        opener: Callable = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        self.user_agent = validate_user_agent(user_agent)
        self.log_path = log_path
        self.interval = max(1.0, interval)
        self.timeout = timeout
        self.max_retries = max_retries
        self.opener = opener
        self.sleeper = sleeper
        self.last_request = 0.0
        self.retry_count = 0

    def _wait(self) -> None:
        delay = self.interval - (time.monotonic() - self.last_request)
        if delay > 0:
            self.sleeper(delay)

    def _log(self, url: str, started: str, ended: str, status: int | str, retry: bool) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "url": url,
            "start_time": started,
            "end_time": ended,
            "status_code": status,
            "retry": retry,
        }
        with self.log_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")

    def download(self, url: str) -> tuple[bytes, int, str]:
        last_error = ""
        for attempt in range(self.max_retries + 1):
            self._wait()
            started = utc_now()
            status: int | str = ""
            try:
                request = Request(
                    url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml",
                    },
                )
                with self.opener(request, timeout=self.timeout) as response:
                    status = int(getattr(response, "status", response.getcode()))
                    payload = response.read()
                ended = utc_now()
                self.last_request = time.monotonic()
                self._log(url, started, ended, status, attempt > 0)
                if status == 200:
                    return payload, status, ended
                last_error = f"HTTP {status}"
            except HTTPError as error:
                status = error.code
                ended = utc_now()
                self.last_request = time.monotonic()
                self._log(url, started, ended, status, attempt > 0)
                last_error = f"HTTP {status}"
            except URLError as error:
                ended = utc_now()
                self.last_request = time.monotonic()
                self._log(url, started, ended, "network_error", attempt > 0)
                last_error = type(error.reason).__name__

            if status not in RETRYABLE or attempt >= self.max_retries:
                break
            self.retry_count += 1
            self.sleeper(float(2**attempt))
        raise RuntimeError(f"download failed after retries: {last_error}")


def load_prior_manifest(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    prior = pd.read_csv(path, dtype=str, keep_default_na=False)
    if not set(MANIFEST_COLUMNS).issubset(prior.columns):
        return {}
    return {row["accession_number"]: row for row in prior.to_dict("records")}


def collect(
    root: Path,
    *,
    user_agent: str | None = None,
    opener: Callable = urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, int]:
    input_path = root / INPUT_RELATIVE
    output = root / OUTPUT_RELATIVE
    raw_dir = output / "raw"
    manifest_dir = output / "manifest"
    manifest_path = manifest_dir / "html_manifest.csv"
    summary_path = manifest_dir / "html_download_summary.csv"
    log_path = output / "logs" / "html_download_log.jsonl"

    frame = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    validate_input(frame)
    prior = load_prior_manifest(manifest_path)
    downloader = HtmlDownloader(
        user_agent=validate_user_agent(user_agent),
        log_path=log_path,
        opener=opener,
        sleeper=sleeper,
    )
    rows: list[dict[str, str | int]] = []
    counts = {"downloaded": 0, "skipped": 0, "failed": 0}

    for company in frame.to_dict("records"):
        accession = company["accession_number"]
        relative_path = Path("2025/pilot_100/html/raw") / company["cik"] / f"{accession}.html"
        destination = root / relative_path
        previous = prior.get(accession, {})
        current_sha = sha256_file(destination) if destination.exists() and destination.stat().st_size else ""
        if (
            current_sha
            and previous.get("sha256") == current_sha
            and previous.get("download_status") in {"downloaded", "skipped_sha_match"}
        ):
            row = {
                **{key: company[key] for key in [
                    "final_sample_id", "cik", "symbol", "accession_number", "primary_document"
                ]},
                "html_path": relative_path.as_posix(),
                "sha256": current_sha,
                "file_size": destination.stat().st_size,
                "download_timestamp": previous["download_timestamp"],
                "http_status": previous.get("http_status", "200"),
                "download_status": "skipped_sha_match",
            }
            counts["skipped"] += 1
        else:
            url = archive_url(company["cik"], accession, company["primary_document"])
            try:
                payload, status, timestamp = downloader.download(url)
                if not payload:
                    raise RuntimeError("empty response body")
                destination.parent.mkdir(parents=True, exist_ok=True)
                temporary = destination.with_suffix(".html.part")
                temporary.write_bytes(payload)
                temporary.replace(destination)
                row = {
                    **{key: company[key] for key in [
                        "final_sample_id", "cik", "symbol", "accession_number", "primary_document"
                    ]},
                    "html_path": relative_path.as_posix(),
                    "sha256": sha256_file(destination),
                    "file_size": destination.stat().st_size,
                    "download_timestamp": timestamp,
                    "http_status": status,
                    "download_status": "downloaded",
                }
                counts["downloaded"] += 1
            except Exception:
                counts["failed"] += 1
                row = {
                    **{key: company[key] for key in [
                        "final_sample_id", "cik", "symbol", "accession_number", "primary_document"
                    ]},
                    "html_path": relative_path.as_posix(),
                    "sha256": "", "file_size": 0, "download_timestamp": utc_now(),
                    "http_status": "", "download_status": "failed",
                }
        rows.append(row)

    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
    manifest.to_csv(manifest_path, index=False, quoting=csv.QUOTE_MINIMAL)
    summary = {
        "input_path": INPUT_RELATIVE.as_posix(),
        "input_rows": len(frame),
        "manifest_rows": len(manifest),
        "html_files": sum((root / path).is_file() for path in manifest["html_path"]),
        "downloaded": counts["downloaded"],
        "skipped_sha_match": counts["skipped"],
        "failed": counts["failed"],
        "retry_count": downloader.retry_count,
        "successful_files": int(
            manifest["download_status"].isin({"downloaded", "skipped_sha_match"}).sum()
        ),
        "http_failures": int(manifest["http_status"].astype(str).ne("200").sum()),
        "unique_accessions": manifest["accession_number"].nunique(),
        "unique_sha256": manifest.loc[manifest["sha256"].ne(""), "sha256"].nunique(),
        "zero_size_files": int(manifest["file_size"].astype(int).eq(0).sum()),
        "collection_status": "completed" if not counts["failed"] else "partial",
        "completed_at": utc_now(),
    }
    pd.DataFrame([summary]).to_csv(summary_path, index=False)
    return {key: int(value) for key, value in summary.items() if isinstance(value, int)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = collect(args.root.resolve())
    print(json.dumps(result, sort_keys=True))
    if result["failed"] or result["http_failures"]:
        raise SystemExit(1)
