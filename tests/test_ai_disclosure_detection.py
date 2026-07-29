import unittest
from scripts.language_measurement_common import ai_matches, safe_ratio


class AiDetectionTests(unittest.TestCase):
    def test_phrase_hyphen_plural_and_boundaries(self):
        text = "Artificial intelligence, AI-driven neural networks and LLMs."
        terms = {row["dictionary_term"] for row in ai_matches(text)}
        self.assertTrue({"artificial intelligence", "AI-driven", "neural networks", "LLMs"} <= terms)

    def test_abbreviation_does_not_match_inside_word(self):
        self.assertEqual(ai_matches("paid chair"), [])
        self.assertIsNone(safe_ratio(1, 0))

    def test_longest_dictionary_match_prevents_nested_double_count(self):
        matches = ai_matches("We use generative artificial intelligence.")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["dictionary_term"], "generative artificial intelligence")
