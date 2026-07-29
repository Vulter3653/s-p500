"""Validate and load the official 1993-2025 Loughran-McDonald dictionary."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DICTIONARY_ROOT = ROOT / "references/dictionaries/loughran_mcdonald_master_dictionary"
DEFAULT_PATH = DICTIONARY_ROOT / "original_source_files/loughran_mcdonald_master_dictionary_1993_2025.csv"
ANALYSIS_PATH = DICTIONARY_ROOT / "analysis_ready_dictionary/financial_language_categories_1993_2025.csv"
EXPECTED_SHA256 = "e2d1328682bab7d2187684fb9f5420bb730401c9eefc00daf835edd203f4859d"
RELEASE = "1993-2025"
LOADER_VERSION = "1.0.0"
OFFICIAL_PAGE = "https://sraf.nd.edu/loughranmcdonald-master-dictionary/"
DIRECT_URL = "https://drive.usercontent.google.com/download?id=1iq2RUf8qGFEAk1g8wQntP3habOnR3fXF&export=download&confirm=t"
CATEGORIES = {
    "positive": "Positive", "negative": "Negative", "uncertainty": "Uncertainty",
    "litigious": "Litigious", "strong_modal": "Strong_Modal",
    "weak_modal": "Weak_Modal", "constraining": "Constraining",
}
REQUIRED = {"Word", *CATEGORIES.values(), "Syllables", "Source"}


class DictionaryValidationError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_word(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().lower()


def load_dictionary(path: Path = DEFAULT_PATH, expected_sha256: str = EXPECTED_SHA256,
                    write_analysis_file: bool = False) -> tuple[dict, dict]:
    if not path.is_file():
        raise FileNotFoundError(
            f"official LM dictionary missing: {path}; download it from {OFFICIAL_PAGE}"
        )
    actual_sha = sha256_file(path)
    if expected_sha256 and actual_sha != expected_sha256:
        raise DictionaryValidationError(
            f"LM dictionary SHA-256 mismatch: expected {expected_sha256}, got {actual_sha}"
        )
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise DictionaryValidationError(f"missing required LM columns: {sorted(missing)}")
        rows = list(reader)
    mappings: dict[str, dict] = {}
    duplicate_words: list[str] = []
    empty_words = 0
    negative_source_counts = {key: 0 for key in CATEGORIES}
    for source_row_number, row in enumerate(rows, start=2):
        word = normalize_word(row["Word"])
        if not word:
            empty_words += 1
            continue
        if word in mappings:
            duplicate_words.append(word)
            continue
        category_values = {}
        for key, column in CATEGORIES.items():
            try:
                value = int(float(row[column]))
            except (TypeError, ValueError) as error:
                raise DictionaryValidationError(
                    f"non-numeric {column} at source row {source_row_number}"
                ) from error
            category_values[key] = value
            negative_source_counts[key] += int(value < 0)
        mappings[word] = {
            "dictionary_word": row["Word"], "normalized_word": word,
            "values": category_values,
            "active": {key: value > 0 for key, value in category_values.items()},
            "syllable_count": row["Syllables"], "source_value": row["Source"],
            "source_row_number": source_row_number,
        }
    if empty_words:
        raise DictionaryValidationError(f"empty Word entries: {empty_words}")
    if duplicate_words:
        raise DictionaryValidationError(f"duplicate Word entries: {len(duplicate_words)}")
    counts = {
        key: sum(entry["active"][key] for entry in mappings.values()) for key in CATEGORIES
    }
    metadata = {
        "dictionary_name": "Loughran-McDonald Master Dictionary",
        "dictionary_release": RELEASE, "coverage_years": RELEASE,
        "source_url": OFFICIAL_PAGE, "direct_download_url": DIRECT_URL,
        "local_path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "sha256": actual_sha, "row_count": len(rows), "column_count": len(reader.fieldnames or []),
        "columns": reader.fieldnames, "category_word_counts": counts,
        "negative_source_value_counts": negative_source_counts,
        "license_status": "academic_research_use_permitted",
        "redistribution_status": "research_use_permitted_redistribution_unclear",
        "loader_version": LOADER_VERSION,
    }
    if write_analysis_file:
        ANALYSIS_PATH.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "dictionary_word", "normalized_word",
            *[f"{key}_active" for key in CATEGORIES],
            *[f"{key}_source_value" for key in CATEGORIES],
            "syllable_count", "source_value", "source_row_number",
        ]
        with ANALYSIS_PATH.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            for entry in mappings.values():
                output = {
                    "dictionary_word": entry["dictionary_word"],
                    "normalized_word": entry["normalized_word"],
                    "syllable_count": entry["syllable_count"],
                    "source_value": entry["source_value"],
                    "source_row_number": entry["source_row_number"],
                }
                output.update({f"{key}_active": int(entry["active"][key]) for key in CATEGORIES})
                output.update({f"{key}_source_value": entry["values"][key] for key in CATEGORIES})
                writer.writerow(output)
    return mappings, metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--write-analysis-file", action="store_true")
    arguments = parser.parse_args()
    _, info = load_dictionary(write_analysis_file=arguments.write_analysis_file)
    print(json.dumps(info, ensure_ascii=False, sort_keys=True))
