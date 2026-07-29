import unittest
from pathlib import Path

import pandas as pd

from scripts.apply_pilot_replacement import CUTOFF, ITW_ID, SEED, TXT_ID


class PilotReplacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = Path("2025/pilot_100")
        cls.original = pd.read_csv(base / "sample/pilot_sample_100.csv", dtype=str, keep_default_na=False)
        cls.final = pd.read_csv(base / "sample/final_analysis_sample_100.csv", dtype=str, keep_default_na=False)
        cls.manifest = pd.read_csv(base / "metadata/filings_manifest.csv", dtype=str, keep_default_na=False)
        cls.reviews = pd.read_csv(base / "metadata/manual_review_resolution.csv", dtype=str, keep_default_na=False)
        cls.audit = pd.read_csv(base / "metadata/txt_filing_review.csv", dtype=str, keep_default_na=False)

    def test_membership_ids_and_lineage(self):
        self.assertEqual(len(self.final), 100)
        self.assertFalse(self.final["symbol"].eq("TXT").any())
        itw = self.final.loc[self.final["symbol"].eq("ITW")].iloc[0]
        self.assertEqual(itw["final_sample_id"], ITW_ID)
        self.assertNotEqual(itw["final_sample_id"], TXT_ID)
        self.assertEqual(itw["original_pilot_id"], TXT_ID)
        self.assertEqual(itw["replacement_for"], TXT_ID)
        self.assertEqual(itw["sampling_seed"], SEED)
        self.assertEqual(itw["reserve_order"], "1")
        self.assertEqual(itw["within_sector_random_order"], "17")
        self.assertIn("no_text_outcome_used", itw["selection_reason"])

    def test_final_keys_filings_and_sector_allocation(self):
        for column in ["final_sample_id", "_company_key", "cik", "accession_number"]:
            self.assertEqual(self.final[column].nunique(), 100)
        self.assertEqual((self.final["gics_sector"] == "Industrials").sum(), 16)
        self.assertEqual(
            self.final["gics_sector"].value_counts().sort_index().to_dict(),
            self.original["gics_sector"].value_counts().sort_index().to_dict(),
        )
        self.assertTrue((self.final["analysis_included"] == "1").all())
        self.assertTrue((self.final["form"] == "10-K").all())
        self.assertTrue(self.final["report_date"].str.startswith("2025-").all())
        self.assertTrue((self.final["filing_date"] <= CUTOFF).all())
        self.assertTrue(self.final["primary_document"].ne("").all())

    def test_txt_audit_and_analysis_manifest(self):
        txt = self.manifest.loc[self.manifest["pilot_id"].eq(TXT_ID)].iloc[0]
        self.assertEqual(txt["analysis_included"], "0")
        self.assertEqual(txt["replacement_reason"], "no_eligible_2025_report_date_10k")
        self.assertGreaterEqual(len(self.audit), 2)
        self.assertFalse(self.audit["report_date_in_2025"].eq("True").any())
        eligible = self.manifest.loc[self.manifest["analysis_included"].eq("1")]
        self.assertEqual(len(eligible), 100)
        self.assertEqual(eligible["cik"].nunique(), 100)
        self.assertEqual(eligible["accession_number"].nunique(), 100)

    def test_all_manual_reviews_resolved(self):
        self.assertEqual(set(self.reviews["symbol"]), {"FOXA|FOX", "TXT", "GE", "ITW"})
        self.assertTrue((self.reviews["manual_review_status"] == "resolved").all())
        self.assertTrue((self.reviews["identity_status"] == "verified_by_cik_and_ticker").all())


if __name__ == "__main__":
    unittest.main()
