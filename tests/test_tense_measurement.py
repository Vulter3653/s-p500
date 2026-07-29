import unittest
from scripts.measure_tense_usage import measure_tense


class TenseTests(unittest.TestCase):
    def test_missing_dependency_model_is_blocked(self):
        result = measure_tense(["We will improve."])
        self.assertEqual(result["tense_status"], "blocked_model_missing")
        self.assertIsNone(result["ai_future_tense_count"])
