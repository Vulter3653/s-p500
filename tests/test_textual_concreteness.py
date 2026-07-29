import unittest

from scripts.load_brysbaert_concreteness_dictionary import load_dictionary
from scripts.load_smart_stopwords import load_smart_stopwords
from scripts.measure_linguistic_concreteness import (
    measure_concreteness, preprocess_and_match,
)


def entry(word, score, row, kind="single_word"):
    return {
        "dictionary_entry": word, "normalized_entry": word,
        "entry_type": kind, "score": score, "dictionary_row_number": row,
    }


class TextualConcretenessTests(unittest.TestCase):
    def test_exact_unique_stem_collision_boundary_and_statistics(self):
        dictionary = {
            "risk": entry("risk", 2.0, 2),
            "perform": entry("perform", 3.0, 3),
            "performance": entry("performance", 4.0, 4),
            "cat": entry("cat", 5.0, 5),
            "can't": entry("can't", 2.5, 6),
            "risk-based": entry("risk-based", 3.5, 7),
        }
        result = measure_concreteness(
            ["THE RISK cats performed performance risky can't risk-based"],
            dictionary, {"the"},
        )
        self.assertEqual(result["ai_concreteness_matched_token_count"], 5)
        self.assertEqual(result["ai_concreteness_eligible_token_count"], 7)
        self.assertGreater(result["ai_concreteness_standard_deviation"], 0)
        self.assertEqual(result["ai_concreteness_stem_collision_count"], 1)
        details = result["match_details"]
        self.assertEqual(details[0]["stopword_removed"], 1)
        self.assertTrue(any(row["match_method"] == "exact_original" for row in details))
        self.assertTrue(any(row["match_method"] == "unique_porter_stem" for row in details))
        self.assertTrue(any(row["match_method"] == "ambiguous_stem_unmatched" for row in details))

    def test_zero_denominator_is_missing(self):
        result = measure_concreteness(["the is"], {}, {"the", "is"})
        self.assertIsNone(result["ai_concreteness_mean"])
        self.assertIsNone(result["ai_concreteness_coverage"])
        self.assertEqual(result["concreteness_status"], "warning_denominator_zero")

    def test_paper_examples(self):
        dictionary, _ = load_dictionary()
        stopwords, _ = load_smart_stopwords()
        physics = measure_concreteness(["The subject is physics."], dictionary, stopwords)
        science = measure_concreteness(["The subject is science."], dictionary, stopwords)
        self.assertEqual(round(physics["ai_concreteness_mean"], 2), 3.10)
        self.assertEqual(round(science["ai_concreteness_mean"], 2), 2.96)
        self.assertEqual(physics["ai_concreteness_matched_token_count"], 2)
