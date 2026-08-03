#!/usr/bin/env python3
"""Measure reproducible tense, passive voice, and low-cost text controls."""

from __future__ import annotations

import argparse
import math
import os
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

try:
    from .measure_readability import measure_readability
except ImportError:
    from measure_readability import measure_readability


MODEL_NAME = "en_core_web_sm"
MODEL_VERSION = "3.8.0"
MEASUREMENT_VERSION = "1.0.0"
CONTENT_POS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}
WORD_PATTERN = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
PERCENT_PATTERN = re.compile(r"(?<!\w)(?:\d+(?:[.,]\d+)*)\s*%")
CURRENCY_PATTERN = re.compile(
    r"(?<!\w)(?:[$€£¥]\s*\d+(?:[.,]\d+)*|\d+(?:[.,]\d+)*\s*(?:dollars?|USD|EUR|GBP))",
    re.IGNORECASE,
)
_NLP = None


def initialize_model() -> None:
    global _NLP
    import spacy

    _NLP = spacy.load(MODEL_NAME, disable=["ner"])
    _NLP.max_length = 5_000_000


def split_text(text: str, maximum: int = 200_000) -> list[str]:
    if len(text) <= maximum:
        return [text]
    chunks, current, size = [], [], 0
    for paragraph in text.splitlines():
        if current and size + len(paragraph) + 1 > maximum:
            chunks.append("\n".join(current))
            current, size = [], 0
        if len(paragraph) > maximum:
            for start in range(0, len(paragraph), maximum):
                piece = paragraph[start:start + maximum]
                if current:
                    chunks.append("\n".join(current))
                    current, size = [], 0
                chunks.append(piece)
        else:
            current.append(paragraph)
            size += len(paragraph) + 1
    if current:
        chunks.append("\n".join(current))
    return [chunk for chunk in chunks if chunk.strip()]


def empty_counts() -> dict[str, int]:
    return {
        "past_tense_count": 0,
        "present_tense_count": 0,
        "future_tense_count": 0,
        "finite_verb_count": 0,
        "passive_voice_sentence_count": 0,
        "spacy_sentence_count": 0,
        "alphabetic_token_count": 0,
        "alphabetic_character_count": 0,
        "content_word_count": 0,
    }


def aggregate_docs(texts: list[str]) -> tuple[dict[str, int], set[str]]:
    if _NLP is None:
        initialize_model()
    counts = empty_counts()
    unique_words: set[str] = set()
    for doc in _NLP.pipe(texts, batch_size=8):
        for sentence in doc.sents:
            counts["spacy_sentence_count"] += 1
            if any(token.dep_ in {"auxpass", "nsubjpass"} for token in sentence):
                counts["passive_voice_sentence_count"] += 1
        for token in doc:
            if token.is_alpha:
                counts["alphabetic_token_count"] += 1
                counts["alphabetic_character_count"] += len(token.text)
                counts["content_word_count"] += int(token.pos_ in CONTENT_POS)
                unique_words.add(token.lower_)
            lower = token.lower_
            if token.tag_ == "VBD":
                counts["past_tense_count"] += 1
                counts["finite_verb_count"] += 1
            elif token.tag_ in {"VBP", "VBZ"}:
                counts["present_tense_count"] += 1
                counts["finite_verb_count"] += 1
            elif lower in {"will", "shall", "'ll", "’ll"} and token.pos_ == "AUX":
                counts["future_tense_count"] += 1
                counts["finite_verb_count"] += 1
    return counts, unique_words


def ratio(numerator: int | float, denominator: int | float):
    return None if denominator == 0 else numerator / denominator


def scope_result(prefix: str, counts: dict[str, int]) -> dict:
    finite = counts["finite_verb_count"]
    sentences = counts["spacy_sentence_count"]
    return {
        f"{prefix}past_tense_count": counts["past_tense_count"],
        f"{prefix}present_tense_count": counts["present_tense_count"],
        f"{prefix}future_tense_count": counts["future_tense_count"],
        f"{prefix}finite_verb_count": finite,
        f"{prefix}past_tense_share": ratio(counts["past_tense_count"], finite),
        f"{prefix}present_tense_share": ratio(counts["present_tense_count"], finite),
        f"{prefix}future_tense_share": ratio(counts["future_tense_count"], finite),
        f"{prefix}passive_voice_sentence_count": counts["passive_voice_sentence_count"],
        f"{prefix}passive_voice_sentence_share": ratio(
            counts["passive_voice_sentence_count"], sentences
        ),
        f"{prefix}spacy_sentence_count": sentences,
    }


def measure_one(item: tuple[dict, str, list[str]]) -> dict:
    identity, text_path, ai_sentences = item
    text = Path(text_path).read_text(encoding="utf-8")
    report_counts, unique_words = aggregate_docs(split_text(text))
    ai_counts, _ = aggregate_docs(ai_sentences) if ai_sentences else (empty_counts(), set())
    readable = measure_readability(ai_sentences)
    report_words = WORD_PATTERN.findall(text)
    result = dict(identity)
    result.update(scope_result("", report_counts))
    result.update(scope_result("ai_", ai_counts))
    result.update({
        "report_character_count": len(text),
        "average_word_length": ratio(
            report_counts["alphabetic_character_count"],
            report_counts["alphabetic_token_count"],
        ),
        "lexical_density": ratio(
            report_counts["content_word_count"],
            report_counts["alphabetic_token_count"],
        ),
        "root_type_token_ratio": ratio(
            len(unique_words), math.sqrt(report_counts["alphabetic_token_count"])
        ),
        "type_token_ratio": ratio(len(unique_words), report_counts["alphabetic_token_count"]),
        "percentage_expression_count": len(PERCENT_PATTERN.findall(text)),
        "currency_expression_count": len(CURRENCY_PATTERN.findall(text)),
        "ai_word_count": readable["ai_word_count"],
        "log_ai_word_count": math.log1p(readable["ai_word_count"]),
        "ai_fog_index": readable["ai_fog_index"],
        "ai_average_sentence_length": readable["ai_mean_sentence_length"],
        "ai_complex_word_share": readable["ai_complex_word_ratio"],
        "tense_measurement_status": "success",
        "passive_voice_measurement_status": "success",
        "dependency_model": MODEL_NAME,
        "dependency_model_version": MODEL_VERSION,
        "extended_measurement_version": MEASUREMENT_VERSION,
    })
    return result


def index_text_paths(artifact_root: Path, repository_root: Path) -> dict[str, str]:
    paths = list(artifact_root.rglob("*_analysis_text.txt"))
    paths += list(
        (repository_root / "2025/pilot_100/text/company_text").rglob(
            "*_analysis_text.txt"
        )
    )
    indexed: dict[str, str] = {}
    for path in paths:
        accession = path.name.removesuffix("_analysis_text.txt")
        if accession in indexed:
            raise ValueError(f"duplicate analysis text accession: {accession}")
        indexed[accession] = str(path)
    return indexed


def load_ai_sentences(
    repository_root: Path,
    artifact_root: Path,
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    # Reuse sentence-level artifacts from the current run when present. This
    # avoids a second SEC/R2 collection pass for historical years.
    for path in sorted(artifact_root.rglob("ai_related_sentences.csv.gz")):
        rows = pd.read_csv(
            path,
            compression="gzip",
            dtype={"accession_number": "string"},
        )
        for accession, group in rows.groupby("accession_number", sort=False):
            grouped.setdefault(str(accession), []).extend(
                group["sentence_text"].fillna("").tolist()
            )
    for year in range(2020, 2026):
        path = repository_root / (
            f"{year}/sample_500/language_results/ai_related_sentences.csv.gz"
        )
        if not path.exists():
            continue
        rows = pd.read_csv(path, dtype={"accession_number": "string"})
        for accession, group in rows.groupby("accession_number", sort=False):
            grouped.setdefault(str(accession), []).extend(
                group["sentence_text"].fillna("").tolist()
            )
    return grouped


def select_smoke(panel: pd.DataFrame) -> pd.DataFrame:
    selected = []
    for _, group in panel.groupby("report_year", sort=True):
        ordered = group.sort_values("report_word_count")
        disclosers = ordered[ordered["ai_disclosure_flag"] == 1]
        non_disclosers = ordered[ordered["ai_disclosure_flag"] == 0]
        candidates = [
            disclosers.iloc[0],
            non_disclosers.iloc[len(non_disclosers) // 2],
            disclosers.iloc[-1],
        ]
        selected.extend(candidates)
    return pd.DataFrame(selected).drop_duplicates(["company_id", "report_year"])


def run(
    panel_path: Path,
    artifact_root: Path,
    output_path: Path,
    workers: int,
    smoke: bool,
    years: set[int] | None = None,
) -> pd.DataFrame:
    repository_root = Path(__file__).resolve().parents[1]
    panel = pd.read_parquet(panel_path)
    if years:
        panel = panel[panel["report_year"].astype(int).isin(years)].copy()
    if smoke:
        panel = select_smoke(panel)
    paths = index_text_paths(artifact_root, repository_root)
    ai_by_key = load_ai_sentences(repository_root, artifact_root)
    missing = panel[~panel["accession_number"].astype(str).isin(paths)]
    if not missing.empty:
        raise ValueError(f"missing analysis text files: {len(missing)}")
    items = []
    for row in panel.to_dict("records"):
        identity = {
            "company_id": str(row["company_id"]),
            "report_year": int(row["report_year"]),
            "cik": str(row["cik"]),
            "accession_number": str(row["accession_number"]),
        }
        items.append((
            identity,
            paths[identity["accession_number"]],
            ai_by_key.get(identity["accession_number"], []),
        ))
    results = []
    with ProcessPoolExecutor(
        max_workers=workers, initializer=initialize_model
    ) as executor:
        futures = [executor.submit(measure_one, item) for item in items]
        for completed, future in enumerate(as_completed(futures), 1):
            results.append(future.result())
            if completed % 10 == 0 or completed == len(futures):
                print(f"processed={completed}/{len(futures)}", flush=True)
    result = pd.DataFrame(results).sort_values(["company_id", "report_year"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, lineterminator="\n")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=max(1, min(4, os.cpu_count() or 1)))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--years", default="")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    years = {int(value) for value in args.years.split(",") if value.strip()}
    run(
        args.panel, args.artifact_root, args.output, args.workers, args.smoke,
        years or None,
    )
