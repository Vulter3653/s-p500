import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from scripts.load_brysbaert_concreteness_dictionary import (
    DEFAULT_PATH, DictionaryValidationError, load_dictionary, sha256_file,
)


class BrysbaertLoaderTests(unittest.TestCase):
    def fixture(self, rows, headers=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "dictionary.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Sheet1"
        headers = headers or [
            "Word", "Bigram", "Conc.M", "Conc.SD", "Unknown", "Total",
            "Percent_known", "SUBTLEX",
        ]
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        workbook.save(path)
        return path

    def test_small_valid_dictionary_and_two_word_expression(self):
        path = self.fixture([
            ["subject", 0, 3.14, 1.68, 0, 29, 1.0, 1885],
            ["vice president", 1, 4.31, 1.23, 0, 29, 1.0, 0],
        ])
        dictionary, metadata = load_dictionary(
            path, sha256_file(path), expected_count=2, expected_single=1,
            expected_bigram=1,
        )
        self.assertEqual(dictionary["subject"]["score"], 3.14)
        self.assertEqual(dictionary["vice president"]["entry_type"], "two_word_expression")
        self.assertEqual(metadata["row_count"], 2)

    def test_missing_file_sha_columns_score_and_duplicate(self):
        with self.assertRaises(FileNotFoundError):
            load_dictionary(Path("/tmp/no-brysbaert.xlsx"))
        path = self.fixture([["word", 0, 3, 1, 0, 20, 1, 2]])
        with self.assertRaises(DictionaryValidationError):
            load_dictionary(path, "0" * 64, 1, 1, 0)
        missing = self.fixture([["word"]], ["Word"])
        with self.assertRaises(DictionaryValidationError):
            load_dictionary(missing, sha256_file(missing), 1, 1, 0)
        bad = self.fixture([["word", 0, "x", 1, 0, 20, 1, 2]])
        with self.assertRaises(DictionaryValidationError):
            load_dictionary(bad, sha256_file(bad), 1, 1, 0)
        outside = self.fixture([["word", 0, 6, 1, 0, 20, 1, 2]])
        with self.assertRaises(DictionaryValidationError):
            load_dictionary(outside, sha256_file(outside), 1, 1, 0)
        duplicate = self.fixture([
            ["Word", 0, 3, 1, 0, 20, 1, 2],
            ["word", 0, 3, 1, 0, 20, 1, 2],
        ])
        with self.assertRaises(DictionaryValidationError):
            load_dictionary(duplicate, sha256_file(duplicate), 2, 2, 0)

    @unittest.skipUnless(DEFAULT_PATH.is_file(), "official local dictionary not installed")
    def test_official_counts(self):
        _, metadata = load_dictionary()
        self.assertEqual(metadata["row_count"], 39954)
        self.assertEqual(metadata["single_word_count"], 37058)
        self.assertEqual(metadata["two_word_expression_count"], 2896)
        self.assertGreaterEqual(metadata["score_min"], 1)
        self.assertLessEqual(metadata["score_max"], 5)
