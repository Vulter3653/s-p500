"""Select narrative sentences containing validated AI dictionary terms."""

try:
    from .language_measurement_common import ai_matches
except ImportError:
    from language_measurement_common import ai_matches


def extract_ai_sentences(rows: list[dict]) -> list[dict]:
    narrative = [
        row for row in rows
        if row.get("included_in_analysis_text") == "1" and row.get("is_table_text") == "0"
    ]
    output = []
    for index, row in enumerate(narrative):
        matches = ai_matches(row["sentence_text"])
        if not matches:
            continue
        item = dict(row)
        item.update(
            {
                "matched_ai_terms": "|".join(match["matched_term"] for match in matches),
                "matched_term_count": len(matches),
                "ai_match_type": "|".join(sorted({match["match_type"] for match in matches})),
                "included_in_measurement": 1,
                "exclusion_reason": "",
                "previous_sentence_text": narrative[index - 1]["sentence_text"] if index else "",
                "next_sentence_text": narrative[index + 1]["sentence_text"] if index + 1 < len(narrative) else "",
            }
        )
        output.append(item)
    return output
