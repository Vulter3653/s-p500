import unittest
from scripts.measure_linguistic_concreteness import measure_concreteness


class ConcretenessTests(unittest.TestCase):
    def test_missing_dictionary_is_blocked_not_imputed(self):
        result = measure_concreteness(["A concrete sentence."])
        self.assertEqual(result["concreteness_status"], "blocked_dictionary_missing")
        self.assertIsNone(result["ai_concreteness_mean"])
