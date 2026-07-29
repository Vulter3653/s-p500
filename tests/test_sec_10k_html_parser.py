import unittest

from scripts.parse_sec_10k_html import normalize_text, parse_html


class SecHtmlParserTests(unittest.TestCase):
    def test_removes_noncontent_and_preserves_visible_text(self):
        parsed = parse_html(b"""
        <html><head><style>.x{display:none}</style><script>alert(1)</script></head>
        <body><div style="display:none">SECRET</div><ix:header>metadata</ix:header>
        <p>Visible&nbsp;text \xc2\xad here.</p></body></html>
        """)
        text = " ".join(block.text for block in parsed["blocks"])
        self.assertIn("Visible text here.", text)
        self.assertNotIn("SECRET", text)
        self.assertNotIn("alert", text)
        self.assertNotIn("metadata", text)

    def test_table_is_separated_from_analysis(self):
        parsed = parse_html(b"<html><body><p>Before.</p><table><tr><td>Revenue</td><td>10</td></tr></table><p>After.</p></body></html>")
        narrative = [block.text for block in parsed["blocks"] if not block.is_table]
        tables = [block.text for block in parsed["blocks"] if block.is_table]
        self.assertEqual(narrative, ["Before.", "After."])
        self.assertEqual(tables, ["Revenue 10"])

    def test_unicode_normalization(self):
        self.assertEqual(normalize_text("ＡＢＣ\u00a0test\u200b"), "ABC test")


if __name__ == "__main__":
    unittest.main()
