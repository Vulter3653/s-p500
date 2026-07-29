import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.extract_10k_analysis_text import (
    PARSER_VERSION, can_skip, parse_with_retries, sha256, validate_input,
)
from scripts.parse_sec_10k_html import sentence_split


class TextExtractionTests(unittest.TestCase):
    def test_sentence_split_protects_financial_abbreviations(self):
        text = "U.S. operations are managed by Example Inc. Revenue was 10.5 million. Risk increased."
        sentences = sentence_split(text)
        self.assertEqual(len(sentences), 3)
        self.assertTrue(sentences[0].startswith("U.S."))

    def test_sha_and_structural_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            html = root / "filing.html"
            html.write_text("<html>filing</html>")
            rows = []
            for number in range(100):
                rows.append({
                    "final_sample_id": f"C{number:03d}", "cik": f"{number + 1:010d}",
                    "symbol": f"T{number}", "accession_number": f"{number + 1:010d}-26-{number + 1:06d}",
                    "primary_document": "doc.htm", "html_path": "filing.html",
                    "sha256": sha256(html), "file_size": str(html.stat().st_size),
                    "download_status": "downloaded",
                })
            validate_input(root, pd.DataFrame(rows))

    def test_duplicate_accession_rejected(self):
        frame = pd.read_csv("2025/pilot_100/html/manifest/html_manifest.csv", dtype=str, keep_default_na=False)
        frame.loc[1, "accession_number"] = frame.loc[0, "accession_number"]
        with self.assertRaises(ValueError):
            validate_input(Path("."), frame)

    def test_parser_stops_after_three_attempts(self):
        calls = []

        def failing_parser(_payload):
            calls.append(1)
            raise ValueError("bad HTML")

        parsed, attempts, error = parse_with_retries(b"bad", parser=failing_parser)
        self.assertIsNone(parsed)
        self.assertEqual(attempts, 3)
        self.assertEqual(len(calls), 3)
        self.assertIn("bad HTML", error)

    def test_current_artifacts_are_sha_linked_and_skippable(self):
        root = Path(".")
        manifest = pd.read_csv(
            "2025/pilot_100/html/manifest/html_manifest.csv",
            dtype=str, keep_default_na=False,
        )
        results = pd.read_csv(
            "2025/pilot_100/text/extraction_results/company_text_extraction_results.csv",
            dtype=str, keep_default_na=False,
        )
        prior = {row["accession_number"]: row for row in results.to_dict("records")}
        self.assertEqual(len(results), 100)
        self.assertTrue(all(can_skip(root, row, prior) for row in manifest.to_dict("records")))
        self.assertEqual(set(results["parser_version"]), {PARSER_VERSION})

    def test_quality_summary_has_unique_paragraph_and_sentence_ids(self):
        summary = pd.read_csv(
            "2025/pilot_100/text/extraction_results/extraction_run_summary.csv"
        ).iloc[0]
        self.assertEqual(summary["paragraph_rows"], summary["unique_paragraph_ids"])
        self.assertEqual(summary["sentence_rows"], summary["unique_sentence_ids"])
        self.assertEqual(summary["paragraph_companies"], 100)
        self.assertEqual(summary["sentence_companies"], 100)


if __name__ == "__main__":
    unittest.main()
