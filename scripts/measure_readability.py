"""Gunning Fog measurement using the documented deterministic syllable heuristic."""

try:
    from .language_measurement_common import count_syllables, readability
except ImportError:
    from language_measurement_common import count_syllables, readability


def measure_readability(sentences: list[str]) -> dict:
    values = readability(sentences)
    return {
        "ai_fog_index": values["fog_index"],
        "ai_mean_sentence_length": values["mean_sentence_length"],
        "ai_complex_word_ratio": values["complex_word_ratio"],
        "ai_word_count": values["word_count"],
        "ai_sentence_count_for_readability": values["sentence_count"],
        "ai_complex_word_count": values["complex_word_count"],
        "readability_status": "success" if values["sentence_count"] else "not_applicable_zero_ai_sentences",
    }
