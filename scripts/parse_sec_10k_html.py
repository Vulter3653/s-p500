#!/usr/bin/env python3
"""Parse SEC 10-K HTML into narrative, table, and section blocks."""

from __future__ import annotations

import html as html_module
import re
import unicodedata
from dataclasses import dataclass

from lxml import etree, html

PARSER_VERSION = "1.0.4"
BLOCK_TAGS = {
    "p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "pre", "center", "section", "article",
}
REMOVE_TAGS = {
    "script", "style", "noscript", "svg", "canvas", "object", "embed",
    "nav", "header", "footer", "iframe",
}
XBRL_METADATA_TAGS = {
    "header", "hidden", "resources", "references", "context", "unit",
    "schemaref", "linkbaseref", "roletype", "arcroletype",
}
ZERO_WIDTH = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")
SPACE = re.compile(r"[ \t\f\v]+")
PAGE_NUMBER = re.compile(r"^(?:page\s+)?\d{1,4}$", re.I)
ITEM_PATTERN = re.compile(
    r"^\s*(?:part\s+[ivx]+\s*[-—:]\s*)?item\s+"
    r"(1a|1b|1c|1|2|3|5|7a|7|8)(?=$|\s|[.:\-—])\s*[.:\-—]?\s*(.*)$",
    re.I,
)
LAYOUT_ITEM_PATTERN = re.compile(
    r"\bitem\s+(?:1a|1b|1c|1|2|3|5|7a|7|8)(?=$|\s|[.:\-—])",
    re.I,
)

SECTIONS = [
    ("item_1", "Business", "item_1_business.txt"),
    ("item_1a", "Risk Factors", "item_1a_risk_factors.txt"),
    ("item_1b", "Unresolved Staff Comments", "item_1b_unresolved_staff_comments.txt"),
    ("item_1c", "Cybersecurity", "item_1c_cybersecurity.txt"),
    ("item_2", "Properties", "item_2_properties.txt"),
    ("item_3", "Legal Proceedings", "item_3_legal_proceedings.txt"),
    ("item_5", "Market for Registrant's Common Equity", "item_5_stock_market_information.txt"),
    ("item_7", "Management's Discussion and Analysis", "item_7_management_discussion_and_analysis.txt"),
    ("item_7a", "Market Risk", "item_7a_market_risk.txt"),
    ("item_8", "Financial Statements and Supplementary Data", "item_8_financial_statements.txt"),
]
SECTION_BY_TOKEN = {
    code.removeprefix("item_"): (code, name) for code, name, _ in SECTIONS
}


@dataclass
class TextBlock:
    order: int
    text: str
    source_element: str
    is_heading: bool = False
    is_table: bool = False
    table_number: int = 0
    section_code: str = "unclassified"
    section_name: str = "Unclassified"


def local_name(element) -> str:
    try:
        return etree.QName(element).localname.lower()
    except (ValueError, TypeError):
        return str(getattr(element, "tag", "")).split(":")[-1].lower()


def normalize_text(value: str, *, preserve_newlines: bool = False) -> str:
    value = html_module.unescape(value or "")
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\xa0", " ").replace("\u00ad", "")
    value = ZERO_WIDTH.sub("", value)
    value = re.sub(r"(?<=\w)-\s*\n\s*(?=[a-z])", "", value)
    if preserve_newlines:
        lines = [SPACE.sub(" ", line).strip() for line in value.splitlines()]
        value = "\n".join(line for line in lines if line)
        return re.sub(r"\n{3,}", "\n\n", value).strip()
    return SPACE.sub(" ", re.sub(r"[\r\n]+", " ", value)).strip()


def visible_text(element) -> str:
    return normalize_text(" ".join(element.itertext()))


def is_hidden(element) -> bool:
    style = re.sub(r"\s+", "", element.get("style", "").lower())
    classes = element.get("class", "").lower().split()
    return (
        element.get("hidden") is not None
        or element.get("aria-hidden", "").lower() == "true"
        or "display:none" in style
        or "visibility:hidden" in style
        or "hidden" in classes
    )


def should_remove(element) -> bool:
    name = local_name(element)
    prefix = getattr(element, "prefix", None)
    if name in REMOVE_TAGS or is_hidden(element):
        return True
    if prefix and prefix.lower() == "ix" and name in XBRL_METADATA_TAGS:
        return True
    if name in {"context", "unit", "schemaref"} and prefix:
        return True
    return False


def is_layout_table(table) -> bool:
    """Return True for legacy layout tables that contain filing narrative.

    Older SEC filings frequently wrap most or all narrative content in a table.
    Dropping those tables as if they were financial data tables removes the
    complete document body. Preserve a table as layout when it contains a
    substantial amount of text and either multiple block descendants or
    several Form 10-K item headings.
    """
    text = visible_text(table)
    word_count = len(text.split())
    if word_count < 500:
        return False
    block_descendants = table.xpath(
        ".//*[local-name()='p' or local-name()='div' or "
        "local-name()='h1' or local-name()='h2' or local-name()='h3' or "
        "local-name()='h4' or local-name()='h5' or local-name()='h6' or "
        "local-name()='li' or local-name()='blockquote' or "
        "local-name()='pre' or local-name()='center' or "
        "local-name()='section' or local-name()='article']"
    )
    item_heading_count = len(LAYOUT_ITEM_PATTERN.findall(text))
    return len(block_descendants) >= 5 or item_heading_count >= 3


def clean_tree(root) -> tuple[object, list[str]]:
    table_texts: list[str] = []
    for comment in root.xpath("//comment()"):
        parent = comment.getparent()
        if parent is not None:
            parent.remove(comment)
    for element in list(root.iter()):
        if not isinstance(element.tag, str):
            continue
        if should_remove(element):
            element.drop_tree()
    for table in list(root.xpath("//*[local-name()='table']")):
        if table.getparent() is None:
            continue
        if is_layout_table(table):
            table.drop_tag()
            continue
        text = visible_text(table)
        if text:
            table_texts.append(text)
            marker = html.Element("p")
            marker.set("data-sec-table-number", str(len(table_texts)))
            marker.text = f"[TABLE {len(table_texts):03d} REMOVED FROM ANALYSIS TEXT]"
            table.addprevious(marker)
        table.drop_tree()
    return root, table_texts


def has_block_child(element) -> bool:
    return any(
        isinstance(child.tag, str) and local_name(child) in BLOCK_TAGS
        for child in element
    )


def extract_blocks(root, table_texts: list[str]) -> tuple[list[TextBlock], int]:
    blocks: list[TextBlock] = []
    duplicates = 0
    previous = ""
    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        name = local_name(element)
        if name not in BLOCK_TAGS:
            continue
        table_number = int(element.get("data-sec-table-number", "0"))
        if table_number:
            text = table_texts[table_number - 1]
        else:
            if name in {"div", "section", "article"} and has_block_child(element):
                continue
            text = visible_text(element)
            text = re.sub(
                r"\s*\[TABLE \d{3} REMOVED FROM ANALYSIS TEXT\]\s*",
                " ",
                text,
            ).strip()
        if not text:
            continue
        if not table_number and (
            text.lower() in {"table of contents", "end privacy-enhanced message"}
            or PAGE_NUMBER.fullmatch(text)
        ):
            continue
        canonical = re.sub(r"\s+", " ", text).strip()
        if canonical == previous:
            duplicates += 1
            continue
        previous = canonical
        blocks.append(
            TextBlock(
                order=len(blocks) + 1,
                text=text,
                source_element=name,
                is_heading=name.startswith("h") or bool(ITEM_PATTERN.match(text[:300])),
                is_table=bool(table_number),
                table_number=table_number,
            )
        )
    return blocks, duplicates


def heading_candidates(blocks: list[TextBlock]) -> dict[str, list[tuple[int, int]]]:
    candidates: dict[str, list[tuple[int, int]]] = {}
    total = max(len(blocks), 1)
    for index, block in enumerate(blocks):
        if block.is_table or len(block.text) > 350:
            continue
        match = ITEM_PATTERN.match(block.text)
        if not match:
            continue
        token = match.group(1).lower()
        score = 0
        score += 4 if block.source_element.startswith("h") else 0
        score += 3 if index > total * 0.08 else -3
        score += 2 if len(block.text) < 180 else 0
        following_words = sum(
            len(next_block.text.split())
            for next_block in blocks[index + 1:index + 8]
            if not next_block.is_table
        )
        score += min(following_words // 100, 4)
        candidates.setdefault(token, []).append((index, score))
    return candidates


def detect_sections(blocks: list[TextBlock]) -> dict[str, dict]:
    candidates = heading_candidates(blocks)
    detected: dict[str, dict] = {}
    previous_index = -1
    for code, name, filename in SECTIONS:
        token = code.removeprefix("item_")
        viable = [
            (index, score) for index, score in candidates.get(token, [])
            if index > previous_index and score >= 2
        ]
        if not viable:
            detected[code] = {
                "code": code,
                "name": name,
                "filename": filename,
                "status": "not_present",
                "heading_index": None,
                "heading_text": "",
                "warning": "",
            }
            continue
        index, score = max(viable, key=lambda item: (item[1], item[0]))
        detected[code] = {
            "code": code,
            "name": name,
            "filename": filename,
            "status": "detected",
            "heading_index": index,
            "heading_text": blocks[index].text,
            "warning": "low_heading_score" if score < 3 else "",
        }
        previous_index = index

    starts = sorted(
        (entry["heading_index"], code)
        for code, entry in detected.items()
        if entry["heading_index"] is not None
    )
    for position, (start, code) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(blocks)
        entry = detected[code]
        entry["start"] = start
        entry["end"] = end
        narrative_words = sum(
            len(block.text.split()) for block in blocks[start:end]
            if not block.is_table
        )
        if narrative_words < 50:
            entry["warning"] = ";".join(
                filter(None, [entry["warning"], "section_too_short"])
            )
        for block in blocks[start:end]:
            block.section_code = code
            block.section_name = entry["name"]
    return detected


def sentence_split(text: str) -> list[str]:
    protected = re.sub(
        r"\b(Inc|Corp|Co|Ltd)\.\s+(?=[A-Z])",
        lambda match: f"{match.group(1)}.¶",
        text,
    )
    replacements = {
        "U.S.": "U§S§",
        "U.K.": "U§K§",
        "Inc.": "Inc§",
        "Corp.": "Corp§",
        "Co.": "Co§",
        "Ltd.": "Ltd§",
        "No.": "No§",
        "Fig.": "Fig§",
        "Mr.": "Mr§",
        "Ms.": "Ms§",
        "Dr.": "Dr§",
    }
    for original, replacement in replacements.items():
        protected = protected.replace(original, replacement)
    protected = re.sub(r"(?<=\d)\.(?=\d)", "§", protected)
    protected = re.sub(r"\b([A-Z])\.(?=\s*[A-Z]\.)", r"\1§", protected)
    parts = re.split(r"¶|(?<=[.!?])\s+(?=(?:[\"'(]?[A-Z0-9]))", protected)
    sentences = []
    for part in parts:
        restored = part.replace("§", ".").strip()
        if restored:
            sentences.append(restored)
    return sentences


def parse_html(payload: bytes) -> dict:
    parser = html.HTMLParser(encoding="utf-8", recover=True, huge_tree=True)
    root = html.fromstring(payload, parser=parser)
    root, table_texts = clean_tree(root)
    blocks, duplicates = extract_blocks(root, table_texts)
    sections = detect_sections(blocks)
    return {
        "blocks": blocks,
        "table_texts": table_texts,
        "sections": sections,
        "duplicate_blocks_removed": duplicates,
    }
