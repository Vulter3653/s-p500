from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from extract_10k_analysis_text import parse_with_retries  # noqa: E402
from parse_sec_10k_html import PARSER_VERSION, parse_html  # noqa: E402


def plain_text_fixture() -> bytes:
    business = " ".join(
        "Empire Petroleum develops and manages oil and gas properties while "
        "evaluating operating risks and capital requirements."
        for _ in range(18)
    )
    risks = " ".join(
        "Our operations depend on commodity prices, available financing, "
        "regulatory approvals, and successful drilling activity."
        for _ in range(12)
    )
    discussion = " ".join(
        "Management reviews liquidity, operating expenses, production "
        "activity, and future development plans for each reporting period."
        for _ in range(12)
    )
    text = f"""<DOCUMENT>
<TYPE>10-K
<SEQUENCE>1
<FILENAME>r10k-2010.txt
<DESCRIPTION>FORM 10-K
<TEXT>
UNITED STATES SECURITIES AND EXCHANGE COMMISSION
FORM 10-K

ITEM 1. BUSINESS
{business}

<TABLE>
Year      Revenue      Expense
2010      100          80
2009      90           75
</TABLE>

ITEM 1A. RISK FACTORS
{risks}

ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
{discussion}

ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA
The audited financial statements follow in the filing.
</TEXT>
</DOCUMENT>
"""
    return text.encode("utf-8")


def test_plain_text_sec_submission_uses_fallback_parser():
    parsed = parse_html(plain_text_fixture())
    narrative = [block for block in parsed["blocks"] if not block.is_table]
    assert PARSER_VERSION == "1.0.5"
    assert sum(len(block.text.split()) for block in narrative) >= 100
    assert any(block.source_element == "plain_text" for block in narrative)
    assert parsed["table_texts"]
    assert any(block.is_table for block in parsed["blocks"])
    assert parsed["sections"]["item_1"]["status"] == "detected"
    assert parsed["sections"]["item_1a"]["status"] == "detected"
    assert parsed["sections"]["item_7"]["status"] == "detected"
    assert parsed["sections"]["item_8"]["status"] == "detected"


def test_plain_text_submission_passes_extraction_retry_guard():
    parsed, attempts, error = parse_with_retries(plain_text_fixture())
    assert parsed is not None
    assert attempts == 1
    assert error == ""
