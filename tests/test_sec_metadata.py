import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

from scripts.sec_client import SecClient, normalize_cik, validate_user_agent
from scripts.collect_sec_filing_metadata import fragment_may_contain_target, identity_status
from scripts.select_2025_10k_filings import merge_filings, select_filings


def filing(form="10-K", report="2025-12-31", filed="2026-02-20", accession="0000000001-26-000001", primary="doc.htm"):
    return {"form": form, "reportDate": report, "filingDate": filed, "accessionNumber": accession, "primaryDocument": primary}


class Response:
    status = 200
    def __init__(self, payload): self.payload = json.dumps(payload).encode()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.payload


class SecMetadataTests(unittest.TestCase):
    def test_cik_padding_and_user_agent_validation(self):
        self.assertEqual(normalize_cik("1234"), "0000001234")
        with self.assertRaises(ValueError): validate_user_agent("")
        with self.assertRaises(ValueError): validate_user_agent("Researcher Name researcher-email@example.com")

    def test_selection_rules_and_amendment(self):
        result = select_filings([
            filing(),
            filing(form="10-K/A", accession="0000000001-26-000002"),
            filing(form="10-K/A", report="2024-12-31", accession="0000000001-25-000010"),
            filing(form="8-K", accession="0000000001-26-000003"),
            filing(report="2024-12-31", accession="0000000001-25-000004"),
            filing(filed="2026-07-30", accession="0000000001-26-000005"),
        ])
        self.assertEqual(result["status"], "eligible")
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(len(result["amendments"]), 1)
        self.assertEqual(select_filings([])["status"], "no_eligible_2025_10k")
        self.assertEqual(select_filings([filing(), filing(accession="0000000001-26-000009")])["status"], "ambiguous_multiple_eligible")

    def test_invalid_accession_and_missing_primary_are_defects(self):
        result = select_filings([filing(accession="bad"), filing(accession="0000000001-26-000008", primary="")])
        self.assertEqual(result["status"], "no_eligible_2025_10k")
        self.assertEqual({x["review_reason"] for x in result["defects"]}, {"accession_missing_or_invalid", "primary_document_missing"})

    def test_historical_merge_deduplicates_accessions(self):
        recent = {k: [v] for k, v in filing().items()}
        historical = {k: [v] for k, v in filing().items()}
        self.assertEqual(len(merge_filings([("recent", recent), ("old.json", historical)])), 1)

    def test_only_relevant_historical_fragments_are_selected(self):
        self.assertFalse(fragment_may_contain_target({"filingFrom": "2000-01-01", "filingTo": "2014-12-31"}))
        self.assertTrue(fragment_may_contain_target({"filingFrom": "2025-01-01", "filingTo": "2025-12-31"}))
        self.assertTrue(fragment_may_contain_target({"name": "unknown-range.json"}))

    def test_identity_mismatch_is_classified_by_cik(self):
        self.assertEqual(identity_status("123", {"cik": "123"}), "match")
        self.assertEqual(identity_status("123", {"cik": "456"}), "identity_mismatch")

    def test_cache_hit_avoids_network_and_log_hides_user_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            def opener(*args, **kwargs):
                calls.append(1)
                return Response({"cik": "1", "filings": {"recent": {}}})
            client = SecClient(Path(tmp, "cache"), Path(tmp, "log.jsonl"), user_agent="Real Person real@example.org", opener=opener, sleeper=lambda _: None)
            url = "https://data.sec.gov/submissions/CIK0000000001.json"
            client.get_json(url, "1")
            client.seen.clear()
            client.get_json(url, "1")
            self.assertEqual(len(calls), 1)
            self.assertNotIn("Real Person", Path(tmp, "log.jsonl").read_text())

    def test_retry_429_and_500(self):
        for code in (429, 500):
            with tempfile.TemporaryDirectory() as tmp:
                calls = []
                def opener(request, timeout):
                    calls.append(1)
                    if len(calls) == 1:
                        raise HTTPError(request.full_url, code, "retry", {}, io.BytesIO())
                    return Response({"cik": "1"})
                client = SecClient(Path(tmp, "cache"), Path(tmp, "log"), user_agent="Real real@example.org", opener=opener, sleeper=lambda _: None)
                client.get_json("https://data.sec.gov/submissions/CIK0000000001.json", "1")
                self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
