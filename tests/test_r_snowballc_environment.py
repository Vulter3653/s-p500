import csv
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE_HASHES = {
    "2025/pilot_100/language_smoke_test/textual_concreteness/company_concreteness_results.csv":
        "d4a327d37a1828e901f5514dcf8a9996c044af7af1f386fbbff4700b72b892e2",
    "2025/pilot_100/language_smoke_test/combined_language_results/company_language_smoke_test_results.csv":
        "7bde999445620ac851931695b192c9bf8d41d7802e8dd0213f9a3c4c170e4099",
    "2025/pilot_100/language_smoke_test/textual_concreteness/ai_concreteness_word_matches.csv.gz":
        "aff312571043ed06fa2adca308b374204af644c95c86a7e4828c0091f9e370b0",
}


class RSnowballCEnvironmentTests(unittest.TestCase):
    def test_required_environment_files_exist(self):
        required = [
            "scripts/install_snowballc_0_7_0.R",
            "scripts/check_snowballc_0_7_0.R",
            "references/software/r_snowballc_environment/README.md",
            "references/software/r_snowballc_environment/installation_metadata.csv",
            "references/software/r_snowballc_environment/package_checksums.csv",
            "references/software/r_snowballc_environment/session_info.txt",
        ]
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_pinned_version_and_ignored_library(self):
        self.assertEqual((ROOT / "VERSION").read_text().strip(), "0.12.0")
        install_script = (ROOT / "scripts/install_snowballc_0_7_0.R").read_text()
        self.assertIn("SnowballC_0.7.0.tar.gz", install_script)
        self.assertIn('identical(actual_version, "0.7.0")', install_script)
        gitignore = (ROOT / ".gitignore").read_text()
        self.assertIn("references/software/r_library/", gitignore)

    def test_metadata_reports_snowballc_0_7_0(self):
        path = ROOT / "references/software/r_snowballc_environment/installation_metadata.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        snowball = next(row for row in rows if row["component"] == "SnowballC")
        self.assertEqual(snowball["version"], "0.7.0")

    def test_concreteness_outputs_are_unchanged(self):
        for relative, expected in BASELINE_HASHES.items():
            actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)


if __name__ == "__main__":
    unittest.main()
