from pathlib import Path
import importlib.util

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "storage" / "build_r2_verified_drive_cleanup.py"
spec = importlib.util.spec_from_file_location("cleanup", MODULE_PATH)
cleanup = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(cleanup)


def migration(key="legacy/a.html", drive_id="drive-a", size=100):
    sha = "a" * 64
    return {
        "r2_object_key": key,
        "r2_html_bytes": str(size),
        "r2_sha256": sha,
        "drive_file_id": drive_id,
        "drive_size": str(size),
        "drive_sha256_app_property": sha,
        "migration_status": "uploaded",
        "verification_status": "verified_size_and_sha",
    }


def inventory(key="legacy/a.html", size=100):
    return {
        "r2_key": key,
        "r2_size": size,
        "r2_etag": "etag",
        "r2_last_modified": "2026-01-01T00:00:00+00:00",
    }


def test_valid_row_becomes_candidate_only_when_global_gate_open():
    row = migration()
    drive = {"drive-a": {"drive_size_live": 100}}
    plan = cleanup.build_plan([inventory()], [row], set(), drive, allow_candidates=True)
    assert plan[0]["classification"] == cleanup.DELETE_CLASS
    assert plan[0]["delete_eligible"] is True

    blocked = cleanup.build_plan([inventory()], [row], set(), drive, allow_candidates=False)
    assert blocked[0]["classification"] == cleanup.REVIEW_GLOBAL_GATE
    assert blocked[0]["delete_eligible"] is False


def test_research_dependency_always_wins():
    row = migration()
    drive = {"drive-a": {"drive_size_live": 100}}
    plan = cleanup.build_plan([inventory()], [row], {"legacy/a.html"}, drive, allow_candidates=True)
    assert plan[0]["classification"] == cleanup.KEEP_RESEARCH
    assert plan[0]["delete_eligible"] is False


def test_drive_size_mismatch_fails_closed():
    row = migration()
    drive = {"drive-a": {"drive_size_live": 99}}
    plan = cleanup.build_plan([inventory()], [row], set(), drive, allow_candidates=True)
    assert plan[0]["classification"] == cleanup.KEEP_INCOMPLETE
    assert plan[0]["delete_eligible"] is False
    assert plan[0]["checks"]["current_drive_size_match"] is False


def test_manifest_sha_mismatch_fails_closed():
    row = migration()
    row["drive_sha256_app_property"] = "b" * 64
    drive = {"drive-a": {"drive_size_live": 100}}
    plan = cleanup.build_plan([inventory()], [row], set(), drive, allow_candidates=True)
    assert plan[0]["delete_eligible"] is False
    assert plan[0]["checks"]["manifest_sha_match"] is False


def test_close_all_candidates_removes_all_eligibility():
    row = migration()
    drive = {"drive-a": {"drive_size_live": 100}}
    plan = cleanup.build_plan([inventory()], [row], set(), drive, allow_candidates=True)
    cleanup.close_all_candidates(plan, "blocked")
    assert not any(item["delete_eligible"] for item in plan)
    assert plan[0]["classification"] == cleanup.REVIEW_GLOBAL_GATE


def test_balance_shards_assigns_every_key_once():
    rows = [
        {"r2_key": f"k{i}", "r2_size": size, "delete_eligible": True}
        for i, size in enumerate([50, 40, 30, 20, 10, 5])
    ]
    shards = cleanup.balance_shards(rows, 3)
    keys = [row["r2_key"] for shard in shards for row in shard]
    assert sorted(keys) == sorted(row["r2_key"] for row in rows)
    assert len(keys) == len(set(keys))


def test_summary_conserves_objects_and_bytes():
    rows = [
        {**inventory("a", 10), "classification": cleanup.DELETE_CLASS, "delete_eligible": True},
        {**inventory("b", 20), "classification": cleanup.KEEP_RESEARCH, "delete_eligible": False},
    ]
    shards = [[rows[0]]]
    summary = cleanup.summarize_plan(rows, shards)
    assert summary["total_r2_objects"] == 2
    assert summary["total_r2_bytes"] == 30
    assert summary["delete_candidate_objects"] == 1
    assert summary["delete_candidate_bytes"] == 10
    assert summary["retained_objects"] == 1
    assert summary["retained_bytes"] == 20


def test_endpoint_validation():
    assert cleanup.validate_r2_endpoint("https://abc.r2.cloudflarestorage.com/") == "https://abc.r2.cloudflarestorage.com"
    with pytest.raises(ValueError):
        cleanup.validate_r2_endpoint("http://abc.r2.cloudflarestorage.com")
    with pytest.raises(ValueError):
        cleanup.validate_r2_endpoint("https://example.com")
