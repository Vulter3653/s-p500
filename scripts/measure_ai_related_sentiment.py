"""Loughran-McDonald financial sentiment dependency status."""

STATUS = "blocked_dictionary_missing"

try:
    from .language_measurement_common import safe_ratio, tokens
except ImportError:
    from language_measurement_common import safe_ratio, tokens


def net_tone(positive: int, negative: int):
    denominator = positive + negative
    return None if denominator == 0 else (positive - negative) / denominator


def measure_sentiment(text: str, dictionary=None) -> dict:
    if dictionary is not None:
        words = [word.lower() for word in tokens(text) if word.isalpha()]
        if not words:
            return {
                "ai_positive_count": None, "ai_negative_count": None,
                "ai_positive_ratio": None, "ai_negative_ratio": None,
                "ai_net_tone": None, "ai_sentiment_word_coverage": None,
                "ai_net_tone_by_words": None, "ai_total_lm_matched_word_count": None,
                "ai_total_eligible_word_count": 0,
                "sentiment_status": "warning_denominator_zero",
            }
        positive = sum(word in dictionary and dictionary[word]["active"]["positive"] for word in words)
        negative = sum(word in dictionary and dictionary[word]["active"]["negative"] for word in words)
        matched = sum(
            word in dictionary and any(dictionary[word]["active"].values()) for word in words
        )
        return {
            "ai_positive_count": positive, "ai_negative_count": negative,
            "ai_positive_ratio": safe_ratio(positive, len(words)),
            "ai_negative_ratio": safe_ratio(negative, len(words)),
            "ai_net_tone": net_tone(positive, negative),
            "ai_sentiment_word_coverage": safe_ratio(positive + negative, len(words)),
            "ai_net_tone_by_words": safe_ratio(positive - negative, len(words)),
            "ai_total_lm_matched_word_count": matched,
            "ai_total_eligible_word_count": len(words),
            "sentiment_status": "success",
        }
    result = {
        "ai_positive_count": None, "ai_negative_count": None,
        "ai_positive_ratio": None, "ai_negative_ratio": None,
        "ai_net_tone": None, "ai_sentiment_word_coverage": None,
        "ai_net_tone_by_words": None,
        "ai_total_lm_matched_word_count": None,
        "ai_total_eligible_word_count": None,
    }
    result["sentiment_status"] = STATUS if dictionary is None else "not_implemented"
    return result
