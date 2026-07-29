import tempfile
import unittest
from pathlib import Path

import pandas as pd
import pyreadr

from scripts.load_smart_stopwords import (
    DEFAULT_PATH, StopwordValidationError, load_smart_stopwords, sha256_file,
)


class SmartStopwordTests(unittest.TestCase):
    def fixture(self, rows):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "stop_words.rda"
        pyreadr.write_rdata(path, pd.DataFrame(rows), df_name="stop_words")
        return path

    def test_subset_normalization_duplicate_and_sha(self):
        path = self.fixture({
            "word": ["the", "is", "would", "would", "other"],
            "lexicon": ["SMART", "SMART", "SMART", "SMART", "onix"],
        })
        words, metadata = load_smart_stopwords(
            path, sha256_file(path), expected_total=5
        )
        self.assertEqual(words, {"the", "is", "would"})
        self.assertEqual(metadata["smart_row_count"], 4)
        self.assertEqual(metadata["smart_entry_count"], 3)
        self.assertEqual(metadata["duplicate_entry_count"], 1)

    def test_missing_and_sha_mismatch(self):
        with self.assertRaises(FileNotFoundError):
            load_smart_stopwords(Path("/tmp/no-stopwords.rda"))
        path = self.fixture({"word": ["the"], "lexicon": ["SMART"]})
        with self.assertRaises(StopwordValidationError):
            load_smart_stopwords(path, "0" * 64, expected_total=1)

    @unittest.skipUnless(DEFAULT_PATH.is_file(), "official tidytext source not installed")
    def test_official_tidytext_counts(self):
        words, metadata = load_smart_stopwords()
        self.assertEqual(metadata["total_stop_words_rows"], 1149)
        self.assertEqual(metadata["smart_row_count"], 571)
        self.assertEqual(len(words), 570)
        self.assertIn("the", words)
        self.assertIn("is", words)
