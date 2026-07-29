import unittest
from scripts.measure_uncertainty_language import measure_uncertainty


class UncertaintyTests(unittest.TestCase):
    def test_missing_lm_dictionary_is_blocked(self):
        result = measure_uncertainty("may adversely affect")
        self.assertEqual(result["uncertainty_status"], "blocked_dictionary_missing")
        self.assertIsNone(result["ai_uncertainty_count"])
