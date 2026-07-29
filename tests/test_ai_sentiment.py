import unittest
from scripts.measure_ai_related_sentiment import measure_sentiment, net_tone


class SentimentTests(unittest.TestCase):
    def test_missing_dictionary_and_zero_denominator(self):
        self.assertEqual(measure_sentiment("positive")["sentiment_status"], "blocked_dictionary_missing")
        self.assertIsNone(net_tone(0, 0))
        self.assertEqual(net_tone(3, 1), 0.5)

    def test_dictionary_counts_boundaries_and_ratios(self):
        dictionary = {
            "gain": {"active": {"positive": True, "negative": False}},
            "loss": {"active": {"positive": False, "negative": True}},
        }
        result = measure_sentiment("GAIN gainful loss losses", dictionary)
        self.assertEqual(result["ai_positive_count"], 1)
        self.assertEqual(result["ai_negative_count"], 1)
        self.assertEqual(result["ai_net_tone"], 0)
