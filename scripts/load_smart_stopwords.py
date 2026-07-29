"""Load the exact SMART subset embedded in tidytext 0.3.1 stop_words.rda."""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path

import pyreadr

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "references/dictionaries/brysbaert_concreteness"
DEFAULT_PATH = BASE / "original_source_files/tidytext_0.3.1_stop_words.rda"
ANALYSIS_PATH = BASE / "analysis_ready_dictionary/smart_stopwords_tidytext_0.3.1.txt"
EXPECTED_SHA256 = "5caf3d61176b8163cc0a7013389362f7b09fd230d3d3feeccfa8fa9e6d04c713"
TIDYTEXT_SOURCE_SHA256 = "30b96058d69733a5f49cff4ff471605f47deb549a40d4517dcdffc7f4b534fa0"
LOADER_VERSION = "1.0.0"


class StopwordValidationError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_smart_stopwords(path: Path = DEFAULT_PATH,
                         expected_sha256: str = EXPECTED_SHA256,
                         expected_total: int = 1149,
                         write_analysis_file: bool = False) -> tuple[set[str], dict]:
    if not path.is_file():
        raise FileNotFoundError(f"tidytext 0.3.1 stop_words.rda missing: {path}")
    actual = sha256_file(path)
    if expected_sha256 and actual != expected_sha256:
        raise StopwordValidationError(
            f"SMART source SHA-256 mismatch: expected {expected_sha256}, got {actual}"
        )
    objects = pyreadr.read_r(str(path))
    if "stop_words" not in objects:
        raise StopwordValidationError("stop_words object missing from RDA")
    frame = objects["stop_words"]
    if set(frame.columns) != {"word", "lexicon"}:
        raise StopwordValidationError(f"unexpected stop_words columns: {list(frame.columns)}")
    if len(frame) != expected_total:
        raise StopwordValidationError(
            f"tidytext stop_words total must be {expected_total}, got {len(frame)}"
        )
    smart_rows = frame[frame["lexicon"] == "SMART"]["word"].tolist()
    normalized = [
        unicodedata.normalize("NFKC", str(word)).strip().lower() for word in smart_rows
    ]
    if any(not word for word in normalized):
        raise StopwordValidationError("empty SMART entry")
    unique = set(normalized)
    canonical = "\n".join(sorted(unique)) + "\n"
    list_sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    metadata = {
        "source": "tidytext 0.3.1 CRAN archive stop_words.rda",
        "tidytext_version": "0.3.1", "total_stop_words_rows": len(frame),
        "smart_row_count": len(normalized), "smart_entry_count": len(unique),
        "duplicate_entry_count": len(normalized) - len(unique),
        "smart_list_sha256": list_sha,
        "rda_sha256": actual, "tidytext_source_tar_sha256": TIDYTEXT_SOURCE_SHA256,
        "paper_reported_smart_count": 1149,
        "count_discrepancy": "paper reports 1149 as SMART; official tidytext data has 1149 total, 571 SMART rows, and 570 unique SMART entries",
        "loader_version": LOADER_VERSION,
    }
    if write_analysis_file:
        ANALYSIS_PATH.parent.mkdir(parents=True, exist_ok=True)
        ANALYSIS_PATH.write_text(canonical, encoding="utf-8")
    return unique, metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--write-analysis-file", action="store_true")
    arguments = parser.parse_args()
    _, info = load_smart_stopwords(write_analysis_file=arguments.write_analysis_file)
    print(json.dumps(info, ensure_ascii=False, sort_keys=True))
