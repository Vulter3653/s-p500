"""Concreteness dependency status.

No scores are imputed: a licensed/source-documented lexical dictionary is required.
"""

STATUS = "blocked_dictionary_missing"


def measure_concreteness(_sentences: list[str], dictionary=None) -> dict:
    if dictionary is None:
        return {
            "ai_concreteness_mean": None,
            "ai_concreteness_median": None,
            "ai_concreteness_coverage": None,
            "ai_concrete_word_ratio": None,
            "ai_matched_concreteness_word_count": None,
            "ai_total_eligible_word_count": None,
            "concreteness_status": STATUS,
        }
    raise NotImplementedError("dictionary adapter is not part of this smoke-test version")
