import unittest
from scripts.measure_uncertainty_language import measure_uncertainty


class UncertaintyTests(unittest.TestCase):
    def test_missing_lm_dictionary_is_blocked(self):
        result = measure_uncertainty("may adversely affect")
        self.assertEqual(result["uncertainty_status"], "blocked_dictionary_missing")
        self.assertIsNone(result["ai_uncertainty_count"])

    def test_all_financial_language_categories(self):
        dictionary = {
            "may": {"active": {"uncertainty": True, "litigious": False, "weak_modal": True,
                               "strong_modal": False, "constraining": False}},
            "must": {"active": {"uncertainty": False, "litigious": False, "weak_modal": False,
                                "strong_modal": True, "constraining": True}},
            "claim": {"active": {"uncertainty": False, "litigious": True, "weak_modal": False,
                                 "strong_modal": False, "constraining": False}},
        }
        result = measure_uncertainty("MAY maybe must claim", dictionary)
        self.assertEqual(result["ai_uncertainty_count"], 1)
        self.assertEqual(result["ai_weak_modal_count"], 1)
        self.assertEqual(result["ai_strong_modal_count"], 1)
        self.assertEqual(result["ai_litigious_count"], 1)
        self.assertEqual(result["ai_constraining_count"], 1)
