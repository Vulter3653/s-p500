#!/usr/bin/env python3
"""Conservative cached client for official SEC JSON endpoints."""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

PLACEHOLDER = "Researcher Name researcher-email@example.com"
RETRYABLE = {429, 500, 502, 503, 504}
ALLOWED_HOST = "data.sec.gov"


def validate_user_agent(value: str | None = None) -> str:
    value = value if value is not None else os.environ.get("SEC_USER_AGENT", "")
    if not value.strip():
        raise ValueError("SEC_USER_AGENT is not set")
    if value.strip() == PLACEHOLDER:
        raise ValueError("SEC_USER_AGENT is the example placeholder")
    return value.strip()


def normalize_cik(value: str | int) -> str:
    digits = str(value).strip()
    if not digits.isdigit() or len(digits) > 10:
        raise ValueError(f"invalid CIK: {value!r}")
    return digits.zfill(10)


class SecClient:
    def __init__(
        self,
        cache_dir: Path,
        log_path: Path,
        *,
        user_agent: str | None = None,
        interval: float = 0.25,
        timeout: float = 30,
        max_retries: int = 4,
        opener: Callable = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        self.user_agent = validate_user_agent(user_agent)
        self.cache_dir = Path(cache_dir)
        self.log_path = Path(log_path)
        self.interval = max(interval, 0.2)
        self.timeout = timeout
        self.max_retries = max_retries
        self.opener = opener
        self.sleeper = sleeper
        self.last_request_at = 0.0
        self.seen: dict[str, dict] = {}
        self.stats = {"log_entries": 0, "cache_hits": 0, "http_429": 0, "retry_events": 0, "errors": 0}

    def _log(self, cik: str, url: str, status, retry: int, cache: bool, elapsed: float, error=""):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "cik": cik,
            "url": url,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "http_status": status,
            "retry_count": retry,
            "cache_used": cache,
            "elapsed_seconds": round(elapsed, 6),
            "error_type": error,
        }
        with self.log_path.open("a", encoding="utf-8") as out:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.stats["log_entries"] += 1
        self.stats["cache_hits"] += int(cache)
        self.stats["http_429"] += int(status == 429)
        self.stats["retry_events"] += int(retry > 0)
        self.stats["errors"] += int(bool(error))

    def get_json(self, url: str, cik: str) -> dict:
        cik = normalize_cik(cik)
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
            raise ValueError("only official data.sec.gov HTTPS endpoints are allowed")
        if url in self.seen:
            return self.seen[url]
        cache_path = self.cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()}.json"
        started = time.monotonic()
        if cache_path.is_file():
            try:
                data = json.loads(cache_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("cached JSON root is not an object")
                self._log(cik, url, 200, 0, True, time.monotonic() - started)
                self.seen[url] = data
                return data
            except (json.JSONDecodeError, ValueError):
                cache_path.unlink()

        last_error: Exception | None = None
        for retry in range(self.max_retries + 1):
            wait = self.interval - (time.monotonic() - self.last_request_at)
            if wait > 0:
                self.sleeper(wait)
            attempt = time.monotonic()
            try:
                request = Request(url, headers={"User-Agent": self.user_agent, "Accept": "application/json"})
                self.last_request_at = time.monotonic()
                with self.opener(request, timeout=self.timeout) as response:
                    status = getattr(response, "status", 200)
                    raw = response.read()
                data = json.loads(raw)
                if status != 200 or not isinstance(data, dict):
                    raise ValueError(f"invalid SEC JSON response status={status}")
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(raw)
                self._log(cik, url, status, retry, False, time.monotonic() - attempt)
                self.seen[url] = data
                return data
            except HTTPError as exc:
                last_error = exc
                self._log(cik, url, exc.code, retry, False, time.monotonic() - attempt, "HTTPError")
                if exc.code not in RETRYABLE or retry >= self.max_retries:
                    break
            except (URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                self._log(cik, url, None, retry, False, time.monotonic() - attempt, type(exc).__name__)
                if retry >= self.max_retries:
                    break
            self.sleeper(self.interval * (2 ** retry))
        raise RuntimeError(f"SEC request failed for CIK {cik}: {type(last_error).__name__}") from last_error
