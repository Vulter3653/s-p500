"""Loughran-McDonald uncertainty dependency status."""

STATUS = "blocked_dictionary_missing"


def measure_uncertainty(_text: str, dictionary=None) -> dict:
    keys = ("ai_uncertainty_count", "ai_uncertainty_ratio", "ai_weak_modal_count",
            "ai_weak_modal_ratio", "ai_strong_modal_count", "ai_strong_modal_ratio",
            "ai_constraining_count", "ai_constraining_ratio")
    result = {key: None for key in keys}
    result["uncertainty_status"] = STATUS if dictionary is None else "not_implemented"
    return result
