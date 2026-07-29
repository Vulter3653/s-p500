"""Dependency-free report-level controls plus explicit dictionary-blocked fields."""

import math

try:
    from .language_measurement_common import ai_matches, numeric_token_ratio, readability, safe_ratio, tokens
except ImportError:
    from language_measurement_common import ai_matches, numeric_token_ratio, readability, safe_ratio, tokens


def measure_report_controls(text: str, sentences: list[str], paragraph_count: int,
                            table_text: str, source_bytes: int, analysis_bytes: int) -> dict:
    read = readability(sentences)
    word_count = len(tokens(text))
    table_words = len(tokens(table_text))
    result = {
        "report_word_count": word_count,
        "log_report_word_count": math.log(word_count) if word_count else None,
        "report_sentence_count": len(sentences),
        "report_paragraph_count": paragraph_count,
        "report_mean_sentence_length": safe_ratio(word_count, len(sentences)),
        "report_fog_index": read["fog_index"],
        "report_numeric_token_ratio": numeric_token_ratio(text),
        "report_ai_term_count": len(ai_matches(text)),
        "report_ai_terms_per_1000_words": safe_ratio(len(ai_matches(text)) * 1000, word_count),
        "report_table_text_word_count": table_words,
        "report_table_text_ratio": safe_ratio(table_words, word_count + table_words),
        "source_html_bytes": source_bytes,
        "analysis_text_bytes": analysis_bytes,
        "analysis_text_to_html_ratio": safe_ratio(analysis_bytes, source_bytes),
        "report_control_status": "partial_dictionary_missing",
    }
    for name in ("positive_count", "negative_count", "net_tone", "uncertainty_count",
                 "uncertainty_ratio", "weak_modal_count", "weak_modal_ratio",
                 "strong_modal_count", "strong_modal_ratio", "litigious_count",
                 "litigious_ratio", "constraining_count", "constraining_ratio",
                 "forward_looking_count", "forward_looking_ratio"):
        result[f"report_{name}"] = None
    return result
