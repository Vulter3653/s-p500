import unittest
from scripts.measure_report_level_controls import measure_report_controls


class ReportControlsTests(unittest.TestCase):
    def test_counts_log_and_numeric_ratio(self):
        result = measure_report_controls("AI improved 20 percent.", ["AI improved 20 percent."],
                                         1, "Table 10", 100, 50)
        self.assertGreater(result["report_word_count"], 0)
        self.assertGreater(result["log_report_word_count"], 0)
        self.assertGreater(result["report_numeric_token_ratio"], 0)
        self.assertEqual(result["report_control_status"], "partial_dictionary_missing")
