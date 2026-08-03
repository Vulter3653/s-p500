from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_yearly_10k_batch_core as core  # noqa: E402


def configure_paths(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(core, "LM_SOURCE", tmp_path / "lm.csv")
    monkeypatch.setattr(core, "LM_ANALYSIS", tmp_path / "analysis.csv")
    monkeypatch.setattr(core, "LM_URL", "primary")
    monkeypatch.setattr(core, "LM_FALLBACK_URL", "fallback")
    monkeypatch.setattr(
        core, "LM_SHA256", hashlib.sha256(b"primary").hexdigest()
    )
    monkeypatch.setattr(
        core,
        "LM_FALLBACK_SHA256",
        hashlib.sha256(b"fallback").hexdigest(),
    )
    monkeypatch.setattr(
        core,
        "LM_FALLBACK_ANALYSIS_SHA256",
        hashlib.sha256(b"analysis").hexdigest(),
    )
    monkeypatch.setattr(core, "LM_FALLBACK_EXPECTED_ROW_COUNT", 2)
    monkeypatch.setattr(
        core,
        "LM_FALLBACK_EXPECTED_CATEGORY_COUNTS",
        {"positive": 1},
    )
    monkeypatch.setattr(
        core,
        "LM_FALLBACK_EXPECTED_NEGATIVE_SOURCE_COUNTS",
        {"positive": 0},
    )


def valid_fallback_loader(*, expected_sha256: str, write_analysis_file: bool):
    assert expected_sha256 == core.LM_FALLBACK_SHA256
    assert write_analysis_file is True
    core.LM_ANALYSIS.parent.mkdir(parents=True, exist_ok=True)
    core.LM_ANALYSIS.write_bytes(b"analysis")
    return (
        {"alpha": {}, "beta": {}},
        {
            "row_count": 2,
            "category_word_counts": {"positive": 1},
            "negative_source_value_counts": {"positive": 0},
        },
    )


def test_primary_sha_failure_uses_validated_official_fallback(
    monkeypatch, tmp_path: Path
):
    configure_paths(monkeypatch, tmp_path)
    calls = []

    def fake_download(url: str, destination: Path, expected_sha: str):
        calls.append((url, expected_sha))
        if url == "primary":
            raise ValueError("download SHA mismatch for lm.csv")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"fallback")

    monkeypatch.setattr(core, "download_file", fake_download)
    monkeypatch.setattr(core, "load_lm", valid_fallback_loader)

    core.ensure_lm_resource()

    assert calls == [
        ("primary", core.LM_SHA256),
        ("fallback", core.LM_FALLBACK_SHA256),
    ]
    assert core.LM_ANALYSIS.read_bytes() == b"analysis"


def test_fallback_semantic_mismatch_is_rejected(monkeypatch, tmp_path: Path):
    configure_paths(monkeypatch, tmp_path)

    def fake_download(url: str, destination: Path, expected_sha: str):
        if url == "primary":
            raise ValueError("quota response")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"fallback")

    def bad_loader(*, expected_sha256: str, write_analysis_file: bool):
        core.LM_ANALYSIS.write_bytes(b"analysis")
        return (
            {"alpha": {}},
            {
                "row_count": 1,
                "category_word_counts": {"positive": 1},
                "negative_source_value_counts": {"positive": 0},
            },
        )

    monkeypatch.setattr(core, "download_file", fake_download)
    monkeypatch.setattr(core, "load_lm", bad_loader)

    with pytest.raises(ValueError, match="row count mismatch"):
        core.ensure_lm_resource()
    assert not core.LM_ANALYSIS.exists()


def test_both_download_paths_failing_preserves_failure(monkeypatch, tmp_path: Path):
    configure_paths(monkeypatch, tmp_path)

    def failed_download(url: str, destination: Path, expected_sha: str):
        raise ValueError(f"invalid response from {url}")

    monkeypatch.setattr(core, "download_file", failed_download)

    with pytest.raises(RuntimeError, match="both the primary"):
        core.ensure_lm_resource()
    assert not core.LM_SOURCE.exists()
    assert not core.LM_ANALYSIS.exists()
