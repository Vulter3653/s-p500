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

    def test_report_lm_counts(self):
        active = {
            "positive": False, "negative": False, "uncertainty": False,
            "litigious": False, "strong_modal": False, "weak_modal": False,
            "constraining": False,
        }
        dictionary = {
            "gain": {"active": active | {"positive": True}},
            "risk": {"active": active | {"negative": True, "uncertainty": True}},
        }
        result = measure_report_controls(
            "gain risk risks", ["gain risk risks"], 1, "", 100, 50, dictionary
        )
        self.assertEqual(result["report_positive_count"], 1)
        self.assertEqual(result["report_negative_count"], 1)
        self.assertEqual(result["report_uncertainty_count"], 1)
        self.assertEqual(result["report_control_status"], "success")
