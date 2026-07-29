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
