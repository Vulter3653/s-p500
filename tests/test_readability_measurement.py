import unittest
from scripts.measure_readability import measure_readability
from scripts.language_measurement_common import count_syllables


class ReadabilityTests(unittest.TestCase):
    def test_fog_and_complex_words(self):
        self.assertGreaterEqual(count_syllables("artificial"), 3)
        result = measure_readability(["Artificial intelligence improves operations."])
        self.assertEqual(result["ai_sentence_count_for_readability"], 1)
        self.assertGreater(result["ai_fog_index"], 0)

    def test_zero_sentences_is_missing(self):
        self.assertIsNone(measure_readability([])["ai_fog_index"])
