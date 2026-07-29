"""Loughran-McDonald uncertainty and financial-language measures."""

STATUS = "blocked_dictionary_missing"

try:
    from .language_measurement_common import safe_ratio, tokens
except ImportError:
    from language_measurement_common import safe_ratio, tokens


def measure_uncertainty(text: str, dictionary=None) -> dict:
    categories = ("uncertainty", "litigious", "weak_modal", "strong_modal", "constraining")
    if dictionary is None:
        result = {f"ai_{key}_{suffix}": None for key in categories for suffix in ("count", "ratio")}
        result["ai_total_eligible_word_count"] = None
        result["uncertainty_status"] = STATUS
        return result
    words = [word.lower() for word in tokens(text) if word.isalpha()]
    if not words:
        result = {f"ai_{key}_{suffix}": None for key in categories for suffix in ("count", "ratio")}
        result["ai_total_eligible_word_count"] = 0
        result["uncertainty_status"] = "warning_denominator_zero"
        return result
    result = {}
    for key in categories:
        count = sum(
            word in dictionary and dictionary[word]["active"][key] for word in words
        )
        result[f"ai_{key}_count"] = count
        result[f"ai_{key}_ratio"] = safe_ratio(count, len(words))
    result["ai_total_eligible_word_count"] = len(words)
    result["uncertainty_status"] = "success"
    return result
