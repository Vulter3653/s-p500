"""Passive-voice dependency status."""

STATUS = "blocked_model_missing"


def measure_passive(_sentences: list[str], dependency_model=None) -> dict:
    result = {
        "ai_passive_sentence_count": None, "ai_passive_sentence_ratio": None,
        "ai_passive_verb_count": None, "ai_passive_verb_ratio": None,
    }
    result["passive_voice_status"] = STATUS if dependency_model is None else "not_implemented"
    return result
