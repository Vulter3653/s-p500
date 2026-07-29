import csv
import tempfile
import unittest
from pathlib import Path

from scripts.load_loughran_mcdonald_dictionary import (
    CATEGORIES, DictionaryValidationError, load_dictionary, sha256_file,
)


class LoughranMcDonaldLoaderTests(unittest.TestCase):
    def fixture(self, rows, columns=None):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "dictionary.csv"
        fields = columns or ["Word", *CATEGORIES.values(), "Syllables", "Source"]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        self.addCleanup(temporary.cleanup)
        return path

    def row(self, word="RISK", value=0):
        row = {"Word": word, "Syllables": "1", "Source": "12of12inf"}
        row.update({column: value for column in CATEGORIES.values()})
        return row

    def test_positive_zero_negative_and_multiple_categories(self):
        row = self.row()
        row["Positive"] = 2020
        row["Uncertainty"] = 2021
        row["Negative"] = -2014
        path = self.fixture([row])
        dictionary, metadata = load_dictionary(path, sha256_file(path))
        self.assertTrue(dictionary["risk"]["active"]["positive"])
        self.assertTrue(dictionary["risk"]["active"]["uncertainty"])
        self.assertFalse(dictionary["risk"]["active"]["negative"])
        self.assertFalse(dictionary["risk"]["active"]["litigious"])
        self.assertEqual(metadata["category_word_counts"]["positive"], 1)

    def test_missing_file_sha_and_required_column(self):
        with self.assertRaises(FileNotFoundError):
            load_dictionary(Path("/tmp/nonexistent-lm-dictionary.csv"), "x")
        path = self.fixture([self.row()])
        with self.assertRaises(DictionaryValidationError):
            load_dictionary(path, "0" * 64)
        bad = self.fixture([{"Word": "RISK"}], ["Word"])
        with self.assertRaises(DictionaryValidationError):
            load_dictionary(bad, sha256_file(bad))

    def test_duplicate_and_empty_words(self):
        duplicate = self.fixture([self.row(), self.row()])
        with self.assertRaises(DictionaryValidationError):
            load_dictionary(duplicate, sha256_file(duplicate))
        empty = self.fixture([self.row(" ")])
        with self.assertRaises(DictionaryValidationError):
            load_dictionary(empty, sha256_file(empty))

    def test_normalization_preserves_apostrophe_and_hyphen(self):
        rows = [self.row("DON'T"), self.row("RISK-BASED")]
        path = self.fixture(rows)
        dictionary, _ = load_dictionary(path, sha256_file(path))
        self.assertIn("don't", dictionary)
        self.assertIn("risk-based", dictionary)
