import json
import sys
from argparse import Namespace
from pathlib import Path
from urllib.error import HTTPError

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import build_annual_constituents as constituents
from scripts.continuous_backfill import build_state


def cache_payload():
    return {"0": {"cik_str": 123456, "ticker": "ABC", "title": "Example Corp"}}


def write_cache(root: Path, name: str, payload=None) -> Path:
    path = root / "data" / "raw" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache_payload() if payload is None else payload), encoding="utf-8")
    return path


def test_valid_local_cache_avoids_network_and_records_source(monkeypatch, tmp_path):
    path = write_cache(tmp_path, "sec_company_tickers_2026-07-24.json")

    def fail_network(*args, **kwargs):
        raise AssertionError("SEC network must not be called for a valid cache")

    monkeypatch.setattr(constituents, "urlopen", fail_network)
    content, metadata = constituents.resolve_sec_ticker_cache(tmp_path, "2026-07-24")

    assert json.loads(content) == cache_payload()
    assert metadata["source_path"] == str(path.relative_to(tmp_path))
    assert metadata["source_sha256"]
    assert metadata["network_requested"] is False
    _, second_metadata = constituents.resolve_sec_ticker_cache(tmp_path, "2018")
    assert second_metadata["source_sha256"] == metadata["source_sha256"]
    assert second_metadata["network_requested"] is False


def test_missing_cache_makes_at_most_one_request(monkeypatch, tmp_path):
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(cache_payload()).encode()

    def fake_network(request, timeout):
        calls.append(request.get_header("User-agent"))
        return Response()

    monkeypatch.setenv("SEC_USER_AGENT", "researcher@example.org")
    monkeypatch.setattr(constituents, "urlopen", fake_network)
    _, metadata = constituents.resolve_sec_ticker_cache(tmp_path, "2026-07-24")

    assert len(calls) == 1
    assert calls == ["researcher@example.org"]
    assert metadata["network_requested"] is True
    assert metadata["source_sha256"]


def test_missing_cache_without_user_agent_fails_before_network(monkeypatch, tmp_path):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    monkeypatch.setattr(constituents, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network")))

    with pytest.raises(constituents.SecMetadataError) as error:
        constituents.resolve_sec_ticker_cache(tmp_path, "2026-07-24")

    assert error.value.metadata["network_requested"] is False
    assert error.value.metadata["retryable"] is False


def test_http_403_is_non_retryable_and_recorded(monkeypatch, tmp_path):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(1)
        raise HTTPError("https://www.sec.gov/files/company_tickers.json", 403, "Forbidden", {}, None)

    monkeypatch.setenv("SEC_USER_AGENT", "researcher@example.org")
    monkeypatch.setattr(constituents, "urlopen", forbidden)
    with pytest.raises(constituents.SecMetadataError) as error:
        constituents.resolve_sec_ticker_cache(tmp_path, "2026-07-24")

    assert len(calls) == 1
    assert error.value.metadata["retryable"] is False
    assert error.value.metadata["http_status"] == 403
    sidecar = json.loads((tmp_path / "data/processed/sec_ticker_metadata.json").read_text())
    assert sidecar["retryable"] is False


def test_corrupt_cache_is_rejected():
    with pytest.raises(ValueError):
        constituents.validate_sec_ticker_cache(b"{not-json}")
    with pytest.raises(ValueError):
        constituents.validate_sec_ticker_cache(json.dumps({"0": {"ticker": "ABC"}}).encode())


def test_multiple_caches_use_deterministic_first_source(monkeypatch, tmp_path):
    first = write_cache(tmp_path, "sec_company_tickers_2026-07-24.json")
    write_cache(tmp_path, "sec_company_tickers_2026-07-25.json", {"1": {"cik_str": 654321, "ticker": "XYZ", "title": "Other Corp"}})
    monkeypatch.setattr(constituents, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network")))

    _, metadata = constituents.resolve_sec_ticker_cache(tmp_path)

    assert metadata["source_path"] == str(first.relative_to(tmp_path))


def test_chain_state_records_sec_source_metadata():
    args = Namespace(
        zero_streak=0, annual_status="success", dry_run=False, current_year=2019,
        visited_years="", minimum_year=1900, chain_id="test", start_year=2019,
    )
    state = build_state(args, 0, None, {
        "source_path": "data/raw/sec_company_tickers_2026-07-24.json",
        "source_sha256": "abc", "source_origin": "current_branch_data_raw",
        "network_requested": False, "retrieved_at_utc": "2026-07-24T00:00:00+00:00",
    })
    assert state["sec_ticker_metadata"]["source_path"].endswith(".json")
    assert state["sec_ticker_metadata"]["source_sha256"] == "abc"
    assert state["sec_ticker_metadata"]["network_requested"] is False
