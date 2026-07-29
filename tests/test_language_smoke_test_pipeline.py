import unittest
from pathlib import Path
from scripts.check_language_smoke_test_quality import validate
from scripts.language_measurement_common import SMOKE_ROOT, read_csv, run_with_attempts, sha256_file


class PipelineTests(unittest.TestCase):
    def test_artifacts_have_five_unique_companies_and_sha(self):
        result = validate()
        self.assertEqual(result["combined_rows"], 5)
        selected = read_csv(SMOKE_ROOT / "selected_companies/selected_5_companies.csv")
        self.assertEqual(len({row["company_id"] for row in selected}), 5)
        summary = read_csv(SMOKE_ROOT / "processing_logs/language_smoke_test_run_summary.csv")[0]
        combined = SMOKE_ROOT / "combined_language_results/company_language_smoke_test_results.csv"
        self.assertEqual(summary["combined_output_sha256"], sha256_file(combined))

    def test_maximum_three_attempts(self):
        calls = []
        def operation(attempt):
            calls.append(attempt)
            if attempt < 3:
                raise ValueError("retry")
            return "ok"
        value, attempts = run_with_attempts(operation)
        self.assertEqual((value, attempts), ("ok", 3))
        self.assertEqual(calls, [1, 2, 3])

    def test_blocked_dependencies_and_warning_are_preserved(self):
        rows = read_csv(SMOKE_ROOT / "quality_check/failed_or_warning_cases.csv")
        self.assertTrue(any(row["case_status"] == "blocked_dependency" for row in rows))

    def test_lm_outputs_and_original_ai_counts(self):
        combined = read_csv(SMOKE_ROOT / "combined_language_results/company_language_smoke_test_results.csv")
        by_ticker = {row["ticker"]: row for row in combined}
        self.assertEqual(sum(int(row["ai_sentence_count"]) for row in combined), 273)
        self.assertEqual(by_ticker["TECH"]["ai_total_eligible_word_count"], "0")
        self.assertEqual(by_ticker["TECH"]["ai_positive_ratio"], "")
        self.assertNotEqual(by_ticker["TECH"]["report_positive_count"], "")
        self.assertEqual(by_ticker["NSC"]["ai_sentence_count"], "1")
        self.assertEqual(by_ticker["TECH"]["uncertainty_status"], "warning_denominator_zero")
        self.assertEqual(by_ticker["TECH"]["sentiment_status"], "warning_denominator_zero")
        self.assertTrue(all(row["uncertainty_status"] == "success" for row in combined if row["ticker"] != "TECH"))
        self.assertTrue(all(row["sentiment_status"] == "success" for row in combined if row["ticker"] != "TECH"))
