"""Opt-in SEC integration smoke test (not included in unit-test discovery)."""

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.sec_client import SecClient, normalize_cik


def main() -> None:
    base = ROOT / "2025" / "pilot_100"
    sample = pd.read_csv(base / "sample" / "pilot_sample_100.csv", dtype=str).head(2)
    client = SecClient(base / "cache" / "sec_submissions", base / "logs" / "sec_requests.jsonl")
    for row in sample.to_dict("records"):
        cik = normalize_cik(row["cik"])
        payload = client.get_json(f"https://data.sec.gov/submissions/CIK{cik}.json", cik)
        assert normalize_cik(payload["cik"]) == cik
        assert isinstance(payload.get("filings", {}).get("recent"), dict)
    print("PASS: 2-company SEC submissions smoke test")


if __name__ == "__main__":
    main()
