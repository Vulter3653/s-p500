"""Baek et al. (2023) SMART + Porter + Brysbaert concreteness measurement."""

from __future__ import annotations

import re
import statistics
import unicodedata
from collections import defaultdict

from nltk.stem import PorterStemmer

STATUS = "blocked_dictionary_missing"
PREPROCESSING_VERSION = "baek-smart-porter-1.0.0"
MATCHING_STRATEGY_VERSION = "exact-then-unique-porter-1.0.0"
TOKEN_RE = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
PORTER = PorterStemmer(mode=PorterStemmer.ORIGINAL_ALGORITHM)


def normalize_token(token: str) -> str:
    return unicodedata.normalize("NFKC", token).replace("’", "'").lower()


def porter_stem(token: str) -> str:
    return PORTER.stem(token)


def build_stem_index(dictionary: dict) -> tuple[dict, set[str], dict]:
    groups = defaultdict(list)
    for key, entry in dictionary.items():
        if entry["entry_type"] == "single_word" and re.fullmatch(r"[a-z]+(?:['-][a-z]+)*", key):
            groups[porter_stem(key)].append(entry)
    unique = {stem: values[0] for stem, values in groups.items() if len(values) == 1}
    collisions = {stem for stem, values in groups.items() if len(values) > 1}
    collision_details = {stem: values for stem, values in groups.items() if len(values) > 1}
    return unique, collisions, collision_details


def preprocess_and_match(texts: list[str], dictionary: dict, stopwords: set[str]) -> tuple[list, list]:
    unique_stems, collision_stems, _ = build_stem_index(dictionary)
    details = []
    scores = []
    global_order = 0
    for text_order, text in enumerate(texts, start=1):
        for token_order, original in enumerate(TOKEN_RE.findall(text), start=1):
            global_order += 1
            normalized = normalize_token(original)
            is_stopword = normalized in stopwords
            stem = porter_stem(normalized)
            entry = None
            method = "unmatched"
            collision = False
            if not is_stopword:
                exact = dictionary.get(normalized)
                if exact is not None and exact["entry_type"] == "single_word":
                    entry = exact
                    method = "exact_original"
                elif stem in unique_stems:
                    entry = unique_stems[stem]
                    method = "unique_porter_stem"
                elif stem in collision_stems:
                    collision = True
                    method = "ambiguous_stem_unmatched"
            if entry is not None:
                scores.append(entry["score"])
            details.append({
                "text_order": text_order, "token_order": token_order,
                "global_token_order": global_order, "original_token": original,
                "normalized_token": normalized, "porter_stem": stem,
                "stopword_removed": int(is_stopword), "match_method": method,
                "matched_dictionary_entry": "" if entry is None else entry["dictionary_entry"],
                "dictionary_entry_type": "" if entry is None else entry["entry_type"],
                "concreteness_score": "" if entry is None else entry["score"],
                "dictionary_row_number": "" if entry is None else entry["dictionary_row_number"],
                "stem_collision": int(collision),
            })
    return scores, details


def measure_concreteness(sentences: list[str], dictionary=None, stopwords=None,
                         prefix: str = "ai") -> dict:
    names = {
        f"{prefix}_concreteness_mean": None,
        f"{prefix}_concreteness_median": None,
        f"{prefix}_concreteness_standard_deviation": None,
        f"{prefix}_concreteness_min": None,
        f"{prefix}_concreteness_max": None,
        f"{prefix}_concreteness_matched_token_count": None,
        f"{prefix}_concreteness_eligible_token_count": None,
        f"{prefix}_concreteness_unmatched_token_count": None,
        f"{prefix}_concreteness_coverage": None,
        f"{prefix}_concreteness_unique_dictionary_entries": None,
        f"{prefix}_concreteness_stem_collision_count": None,
    }
    if dictionary is None or stopwords is None:
        names[f"{prefix}_concreteness_status"] = STATUS
        if prefix == "ai":
            names["concreteness_status"] = STATUS
        return names | {
            "ai_concrete_word_ratio": None,
            "ai_matched_concreteness_word_count": None,
            "ai_total_eligible_word_count": None,
        }
    scores, details = preprocess_and_match(sentences, dictionary, stopwords)
    eligible = [row for row in details if not row["stopword_removed"]]
    matched = [row for row in eligible if row["concreteness_score"] != ""]
    collision_count = sum(row["stem_collision"] for row in eligible)
    count = len(scores)
    names.update({
        f"{prefix}_concreteness_mean": statistics.fmean(scores) if scores else None,
        f"{prefix}_concreteness_median": statistics.median(scores) if scores else None,
        f"{prefix}_concreteness_standard_deviation": statistics.pstdev(scores) if scores else None,
        f"{prefix}_concreteness_min": min(scores) if scores else None,
        f"{prefix}_concreteness_max": max(scores) if scores else None,
        f"{prefix}_concreteness_matched_token_count": count,
        f"{prefix}_concreteness_eligible_token_count": len(eligible),
        f"{prefix}_concreteness_unmatched_token_count": len(eligible) - count,
        f"{prefix}_concreteness_coverage": None if not eligible else count / len(eligible),
        f"{prefix}_concreteness_unique_dictionary_entries": len({
            row["matched_dictionary_entry"].lower() for row in matched
        }),
        f"{prefix}_concreteness_stem_collision_count": collision_count,
    })
    status = (
        "warning_denominator_zero" if not eligible else
        "warning_stem_collisions" if collision_count else "success"
    )
    names[f"{prefix}_concreteness_status"] = status
    if prefix == "ai":
        names["concreteness_status"] = status
        names.update({
            "ai_concrete_word_ratio": None,
            "ai_matched_concreteness_word_count": count,
            "ai_total_eligible_word_count": len(eligible),
        })
    return names | {"match_details": details}


def compare_matching_strategies(texts: list[str], dictionary: dict,
                                stopwords: set[str]) -> list[dict]:
    unique_stems, collision_stems, _ = build_stem_index(dictionary)
    eligible = [
        normalize_token(token) for text in texts for token in TOKEN_RE.findall(text)
        if normalize_token(token) not in stopwords
    ]
    exact = sum(token in dictionary and dictionary[token]["entry_type"] == "single_word"
                for token in eligible)
    direct_stem = sum(porter_stem(token) in dictionary for token in eligible)
    dictionary_stem = sum(porter_stem(token) in unique_stems for token in eligible)
    hierarchy = sum(
        (token in dictionary and dictionary[token]["entry_type"] == "single_word")
        or (porter_stem(token) in unique_stems)
        for token in eligible
    )
    collision = sum(
        token not in dictionary and porter_stem(token) in collision_stems for token in eligible
    )
    return [
        {"strategy": "stem_to_original_direct", "matched_token_count": direct_stem},
        {"strategy": "stem_both_unique_only", "matched_token_count": dictionary_stem},
        {"strategy": "original_exact", "matched_token_count": exact},
        {"strategy": "primary_exact_then_unique_stem", "matched_token_count": hierarchy},
        {"strategy": "primary_stem_collision_unmatched", "matched_token_count": collision},
    ]
