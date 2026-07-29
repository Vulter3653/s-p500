import unittest

from scripts.parse_sec_10k_html import detect_sections, extract_blocks, parse_html


class SectionDetectionTests(unittest.TestCase):
    def test_detects_actual_headings_after_table_of_contents(self):
        filler = "Business discussion and operating information. " * 20
        payload = f"""<html><body>
        <p>Table of Contents</p><p>Item 1. Business 10 Item 1A. Risk Factors 20 Item 7. MD&amp;A 50</p>
        <h1>Item 1. Business</h1><p>{filler}</p>
        <h1>Item 1A. Risk Factors</h1><p>{filler}</p>
        <h1>Item 7. Management's Discussion and Analysis</h1><p>{filler}</p>
        <h1>Item 8. Financial Statements and Supplementary Data</h1><p>{filler}</p>
        </body></html>""".encode()
        parsed = parse_html(payload)
        for code in ("item_1", "item_1a", "item_7", "item_8"):
            self.assertEqual(parsed["sections"][code]["status"], "detected")
        self.assertGreater(parsed["sections"]["item_7"]["heading_index"], parsed["sections"]["item_1a"]["heading_index"])

    def test_optional_section_not_present(self):
        parsed = parse_html(b"<html><body><h1>Item 1. Business</h1><p>Business text.</p></body></html>")
        self.assertEqual(parsed["sections"]["item_1c"]["status"], "not_present")


if __name__ == "__main__":
    unittest.main()
