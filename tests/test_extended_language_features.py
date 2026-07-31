import unittest

from scripts.measure_extended_language_features import (
    aggregate_docs,
    initialize_model,
    load_ai_sentences,
    scope_result,
)


class ExtendedLanguageFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_model()

    def test_tense_and_passive_fixture(self):
        counts, _ = aggregate_docs([
            "The company reported results. It reports results. Results will be reported."
        ])
        values = scope_result("", counts)
        self.assertGreaterEqual(values["past_tense_count"], 1)
        self.assertGreaterEqual(values["present_tense_count"], 1)
        self.assertGreaterEqual(values["future_tense_count"], 1)
        self.assertGreaterEqual(values["passive_voice_sentence_count"], 1)
        self.assertTrue(0 <= values["past_tense_share"] <= 1)
        self.assertTrue(0 <= values["passive_voice_sentence_share"] <= 1)

    def test_zero_denominator_is_missing(self):
        counts, _ = aggregate_docs(["Artificial intelligence."])
        values = scope_result("ai_", counts)
        self.assertIsNone(values["ai_past_tense_share"])
        self.assertIsNone(values["ai_passive_voice_sentence_share"] if not counts["spacy_sentence_count"] else None)


if __name__ == "__main__":
    unittest.main()
