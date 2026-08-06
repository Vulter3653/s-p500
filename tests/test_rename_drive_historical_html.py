from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from scripts.rename_drive_historical_html import main, plan_year, sanitize_company_name


FIELDS = "sample_order,company_name,ticker,cik,accession_number,report_year,r2_object_key\n"


def setup_year(tmp_path: Path, filename="0000002488-20-000008.html"):
    repo = tmp_path / "repo"
    drive = tmp_path / "drive"
    manifest = repo / "2019/sample_503/sample/final_analysis_sample_503.csv"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(FIELDS + "1,Acme O'Brien / Holdings,BRK.B,2488,0000002488-20-000008,2019,2019/sample_503/html/raw/0000002488/0000002488-20-000008.html\n", encoding="utf-8")
    for year in range(2006, 2019):
        other = repo / str(year) / "sample_503/sample/final_analysis_sample_503.csv"
        other.parent.mkdir(parents=True, exist_ok=True)
        other.write_text(FIELDS, encoding="utf-8")
    source = drive / "2019/0000002488-20-000008.html"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"html")
    return repo, drive, source


def test_exact_accession_mapping_and_name(tmp_path):
    repo, drive, _ = setup_year(tmp_path)
    rows = plan_year(drive, repo, 2019)
    assert rows[0]["status"] == "planned"
    assert rows[0]["new_filename"] == "001_2019_Acme_OBrien_Holdings_BRK-B_0000002488.html"


def test_sanitize_company_name():
    assert sanitize_company_name(" A/B: O'Reilly  Co. ") == "AB_OReilly_Co"


def test_dry_run_does_not_change_files(tmp_path, monkeypatch):
    repo, drive, source = setup_year(tmp_path)
    monkeypatch.setattr("sys.argv", ["rename", "--drive-root", str(drive), "--repo-root", str(repo), "--start-year", "2019", "--end-year", "2006", "--dry-run"])
    assert main() == 0
    assert source.exists()
    assert not (drive / "2019/001_2019_Acme_OBrien_Holdings_BRK-B_0000002488.html").exists()


def test_execute_requires_confirmation(tmp_path, monkeypatch):
    repo, drive, _ = setup_year(tmp_path)
    monkeypatch.setattr("sys.argv", ["rename", "--drive-root", str(drive), "--repo-root", str(repo), "--start-year", "2019", "--end-year", "2006", "--execute"])
    with pytest.raises(SystemExit, match="requires confirmation"):
        main()


def test_execute_renames_and_writes_rollback(tmp_path, monkeypatch):
    repo, drive, source = setup_year(tmp_path)
    monkeypatch.setattr("sys.argv", ["rename", "--drive-root", str(drive), "--repo-root", str(repo), "--start-year", "2019", "--end-year", "2006", "--execute", "--confirmation", "RENAME_HISTORICAL_HTML_2006_2019"])
    assert main() == 0
    target = drive / "2019/001_2019_Acme_OBrien_Holdings_BRK-B_0000002488.html"
    assert target.read_bytes() == b"html"
    assert not source.exists()
    assert "original_path" in (drive / "rename_audit_2006_2019/rollback_manifest.csv").read_text()


def test_destination_conflict_fails_closed(tmp_path):
    repo, drive, source = setup_year(tmp_path)
    target = drive / "2019/001_2019_Acme_OBrien_Holdings_BRK-B_0000002488.html"
    target.write_bytes(b"different")
    rows = plan_year(drive, repo, 2019)
    assert rows[0]["status"] == "failed"
    assert source.exists()


def test_missing_drive_root_reports_mount_requirement(tmp_path, monkeypatch):
    repo, _, _ = setup_year(tmp_path)
    missing = tmp_path / "not-mounted-drive"
    monkeypatch.setattr("sys.argv", ["rename", "--drive-root", str(missing), "--repo-root", str(repo), "--start-year", "2019", "--end-year", "2006", "--dry-run"])
    with pytest.raises(SystemExit, match="Mount Google Drive"):
        main()


def test_manifest_duplicate_fails_closed(tmp_path):
    repo, drive, _ = setup_year(tmp_path)
    path = repo / "2019/sample_503/sample/final_analysis_sample_503.csv"
    path.write_text(FIELDS + "1,A,A,1,acc1,2019,key\n1,B,B,2,acc2,2019,key\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate_sample_order"):
        plan_year(drive, repo, 2019)


def test_standard_file_is_validated_and_2020_not_touched(tmp_path):
    repo, drive, source = setup_year(tmp_path)
    target = drive / "2019/001_2019_Acme_OBrien_Holdings_BRK-B_0000002488.html"
    source.rename(target)
    (drive / "2020").mkdir()
    other = drive / "2020/legacy.html"
    other.write_text("x", encoding="utf-8")
    rows = plan_year(drive, repo, 2019)
    assert any(row["status"] == "already_standard" for row in rows)
    assert other.exists()
