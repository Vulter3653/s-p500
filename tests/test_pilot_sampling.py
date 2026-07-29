import tempfile
import unittest
from pathlib import Path
from shutil import copytree

import pandas as pd

from scripts.build_pilot_sample import SEED, TARGET, build


class PilotSamplingTests(unittest.TestCase):
    def test_reproducible_unique_stratified_sample(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            for target in (first, second):
                Path(target, "2025").mkdir()
                copytree("2025", Path(target, "2025"), dirs_exist_ok=True)
                build(Path(target), SEED)
            path = "2025/pilot_100/sample/pilot_sample_100.csv"
            one = Path(first, path).read_bytes()
            two = Path(second, path).read_bytes()
            self.assertEqual(one, two)
            sample = pd.read_csv(Path(first, path), dtype=str)
            allocation = pd.read_csv(
                Path(first, "2025/pilot_100/sample/sector_allocation.csv")
            )
            self.assertEqual(len(sample), TARGET)
            self.assertEqual(sample["_company_key"].nunique(), TARGET)
            self.assertEqual(sample["cik"].nunique(), TARGET)
            self.assertEqual(int(allocation["sector_target_n"].sum()), TARGET)
            self.assertTrue((allocation["sector_target_n"] >= 1).all())
            self.assertNotIn("ai_binary", sample.columns)


if __name__ == "__main__":
    unittest.main()
