"""Dependency-free report-level controls plus explicit dictionary-blocked fields."""

import math

try:
    from .language_measurement_common import ai_matches, numeric_token_ratio, readability, safe_ratio, tokens
except ImportError:
    from language_measurement_common import ai_matches, numeric_token_ratio, readability, safe_ratio, tokens


def measure_report_controls(text: str, sentences: list[str], paragraph_count: int,
                            table_text: str, source_bytes: int, analysis_bytes: int,
                            lm_dictionary=None) -> dict:
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
        "report_control_status": "partial_dictionary_missing" if lm_dictionary is None else "success",
    }
    for name in ("positive_count", "negative_count", "net_tone", "uncertainty_count",
                 "uncertainty_ratio", "weak_modal_count", "weak_modal_ratio",
                 "strong_modal_count", "strong_modal_ratio", "litigious_count",
                 "litigious_ratio", "constraining_count", "constraining_ratio",
                 "forward_looking_count", "forward_looking_ratio"):
        result[f"report_{name}"] = None
    if lm_dictionary is not None:
        words = [word.lower() for word in tokens(text) if word.isalpha()]
        for category in ("positive", "negative", "uncertainty", "litigious",
                         "strong_modal", "weak_modal", "constraining"):
            count = sum(
                word in lm_dictionary and lm_dictionary[word]["active"][category]
                for word in words
            )
            result[f"report_{category}_count"] = count
            result[f"report_{category}_ratio"] = safe_ratio(count, len(words))
        positive = result["report_positive_count"]
        negative = result["report_negative_count"]
        sentiment_denominator = positive + negative
        result["report_net_tone"] = safe_ratio(positive - negative, sentiment_denominator)
        result["report_net_tone_by_words"] = safe_ratio(positive - negative, len(words))
        result["report_sentiment_word_coverage"] = safe_ratio(sentiment_denominator, len(words))
        result["report_total_lm_matched_word_count"] = sum(
            word in lm_dictionary and any(lm_dictionary[word]["active"].values())
            for word in words
        )
        result["report_total_eligible_word_count"] = len(words)
    return result
