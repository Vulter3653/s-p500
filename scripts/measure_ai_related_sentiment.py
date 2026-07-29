"""Loughran-McDonald financial sentiment dependency status."""

STATUS = "blocked_dictionary_missing"


def net_tone(positive: int, negative: int):
    denominator = positive + negative
    return None if denominator == 0 else (positive - negative) / denominator


def measure_sentiment(_text: str, dictionary=None) -> dict:
    result = {
        "ai_positive_count": None, "ai_negative_count": None,
        "ai_positive_ratio": None, "ai_negative_ratio": None,
        "ai_net_tone": None, "ai_sentiment_word_coverage": None,
        "ai_net_tone_by_words": None,
    }
    result["sentiment_status"] = STATUS if dictionary is None else "not_implemented"
    return result
