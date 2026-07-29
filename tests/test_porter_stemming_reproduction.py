import unittest

from scripts.measure_linguistic_concreteness import porter_stem


class PorterReproductionTests(unittest.TestCase):
    def test_porter_original_algorithm_fixture(self):
        expected = {
            "organization": "organ", "organizations": "organ",
            "organized": "organ", "organizational": "organiz",
            "technology": "technologi", "technologies": "technologi",
            "technological": "technolog", "perform": "perform",
            "performance": "perform", "performed": "perform",
            "science": "scienc", "physics": "physic", "subject": "subject",
            "artificial": "artifici", "intelligence": "intellig",
        }
        self.assertEqual({word: porter_stem(word) for word in expected}, expected)
