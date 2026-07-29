"""Shared, dependency-light helpers for the five-company language smoke test."""

from __future__ import annotations

import csv
import gzip
import hashlib
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE_ROOT = ROOT / "2025/pilot_100/language_smoke_test"
LANGUAGE_MEASUREMENT_VERSION = "0.1.0"
RANDOM_SEED = 20250729

AI_TERMS = [
    ("artificial intelligence", "exact_phrase"),
    ("generative artificial intelligence", "exact_phrase"),
    ("machine learning", "technology_term"),
    ("deep learning", "technology_term"),
    ("natural language processing", "technology_term"),
    ("computer vision", "technology_term"),
    ("reinforcement learning", "technology_term"),
    ("generative AI", "exact_phrase"),
    ("large language models", "plural_variant"),
    ("large language model", "technology_term"),
    ("neural networks", "plural_variant"),
    ("neural network", "technology_term"),
    ("AI-enabled", "hyphen_variant"),
    ("AI-driven", "hyphen_variant"),
    ("AI driven", "hyphen_variant"),
    ("LLMs", "plural_variant"),
    ("LLM", "abbreviation"),
    ("AI", "abbreviation"),
]

WORD_RE = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*|\d+(?:[.,]\d+)*%?")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_row_sha(row: dict) -> str:
    value = "\x1f".join(f"{key}={row.get(key, '')}" for key in sorted(row))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if path.suffix == ".gz" else open
    kwargs = {"encoding": "utf-8", "newline": ""}
    with opener(path, "wt", **kwargs) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def tokens(text: str) -> list[str]:
    return WORD_RE.findall(text)


def safe_ratio(numerator: float, denominator: float):
    return None if denominator == 0 else numerator / denominator


def ai_matches(text: str) -> list[dict]:
    matches = []
    occupied: list[tuple[int, int]] = []
    for term, match_type in sorted(AI_TERMS, key=lambda item: len(item[0]), reverse=True):
        escaped = re.escape(term).replace(r"\ ", r"\s+")
        pattern = re.compile(rf"(?<![A-Za-z]){escaped}(?![A-Za-z])", re.IGNORECASE)
        for match in pattern.finditer(text):
            span = match.span()
            if any(span[0] < old[1] and span[1] > old[0] for old in occupied):
                continue
            occupied.append(span)
            matches.append(
                {
                    "matched_term": match.group(0),
                    "dictionary_term": term,
                    "match_type": match_type,
                    "start_character": span[0],
                    "end_character": span[1],
                }
            )
    return sorted(matches, key=lambda value: value["start_character"])


def count_syllables(word: str) -> int:
    """Deterministic pilot heuristic; proper nouns and abbreviations are not exempt."""
    clean = re.sub(r"[^a-z]", "", word.lower())
    if not clean:
        return 0
    groups = re.findall(r"[aeiouy]+", clean)
    count = len(groups)
    if clean.endswith("e") and not clean.endswith(("le", "ye")) and count > 1:
        count -= 1
    return max(1, count)


def readability(texts: list[str]) -> dict:
    words = [word for text in texts for word in tokens(text) if re.search("[A-Za-z]", word)]
    sentence_count = len([text for text in texts if text.strip()])
    complex_count = sum(count_syllables(word) >= 3 for word in words)
    mean_length = safe_ratio(len(words), sentence_count)
    complex_ratio = safe_ratio(complex_count, len(words))
    fog = None if mean_length is None or complex_ratio is None else 0.4 * (
        mean_length + complex_ratio * 100
    )
    return {
        "word_count": len(words),
        "sentence_count": sentence_count,
        "complex_word_count": complex_count,
        "mean_sentence_length": mean_length,
        "complex_word_ratio": complex_ratio,
        "fog_index": fog,
    }


def numeric_token_ratio(text: str):
    all_tokens = tokens(text)
    numeric = sum(bool(re.fullmatch(r"\d+(?:[.,]\d+)*%?", item)) for item in all_tokens)
    return safe_ratio(numeric, len(all_tokens))


def display(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.8f}"
    return str(value)


def run_with_attempts(operation, maximum: int = 3):
    last_error = None
    for attempt in range(1, maximum + 1):
        try:
            return operation(attempt), attempt
        except Exception as error:  # caller records the final error
            last_error = error
    raise RuntimeError(f"failed_after_{maximum}_attempts: {last_error}") from last_error
