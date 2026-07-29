import unittest
from scripts.extract_ai_related_sentences import extract_ai_sentences


class AiSentenceTests(unittest.TestCase):
    def test_context_and_table_exclusion(self):
        base = {"company_id": "C", "ticker": "T", "cik": "1", "accession_number": "A",
                "paragraph_id": "P", "section_code": "item_1", "section_name": "Business",
                "included_in_analysis_text": "1"}
        rows = [
            base | {"sentence_id": "S1", "sentence_order": "1", "is_table_text": "0", "sentence_text": "Before."},
            base | {"sentence_id": "S2", "sentence_order": "2", "is_table_text": "0", "sentence_text": "We use machine learning."},
            base | {"sentence_id": "S3", "sentence_order": "3", "is_table_text": "1", "sentence_text": "AI table."},
        ]
        result = extract_ai_sentences(rows)
        self.assertEqual([row["sentence_id"] for row in result], ["S2"])
        self.assertEqual(result[0]["previous_sentence_text"], "Before.")
