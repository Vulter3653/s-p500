"""Tense dependency status; avoids substituting word-presence for grammatical tense."""

STATUS = "blocked_model_missing"


def measure_tense(_sentences: list[str], dependency_model=None) -> dict:
    if dependency_model is None:
        return {
            "ai_past_tense_count": None, "ai_present_tense_count": None,
            "ai_future_tense_count": None, "ai_total_finite_verb_count": None,
            "ai_past_tense_ratio": None, "ai_present_tense_ratio": None,
            "ai_future_tense_ratio": None, "ai_past_minus_future": None,
            "ai_future_orientation": None, "tense_status": STATUS,
        }
    raise NotImplementedError("dependency model adapter is not configured")
