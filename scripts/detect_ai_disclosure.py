"""AI dictionary matching used by the language smoke test."""

try:
    from .language_measurement_common import AI_TERMS, ai_matches, safe_ratio
except ImportError:
    from language_measurement_common import AI_TERMS, ai_matches, safe_ratio


def measure_ai_disclosure(text: str, sentence_count: int) -> dict:
    matches = ai_matches(text)
    word_count = len(text.split())
    return {
        "ai_disclosure_binary": int(bool(matches)),
        "ai_term_count": len(matches),
        "ai_terms_per_1000_words": safe_ratio(len(matches) * 1000, word_count),
        "total_analysis_word_count": word_count,
        "total_analysis_sentence_count": sentence_count,
    }
