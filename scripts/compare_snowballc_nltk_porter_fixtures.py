#!/usr/bin/env python3
"""Compare pinned SnowballC and NLTK Porter stems for a small fixed fixture."""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from nltk.stem import PorterStemmer


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SNOWBALLC_LIBRARY = (
    REPOSITORY_ROOT / "references/software/r_library/snowballc_0_7_0"
)
OUTPUT_DIRECTORY = (
    REPOSITORY_ROOT / "references/software/r_snowballc_environment"
)
CSV_PATH = OUTPUT_DIRECTORY / "snowballc_nltk_fixture_comparison.csv"
MARKDOWN_PATH = OUTPUT_DIRECTORY / "snowballc_nltk_fixture_comparison.md"

# Small, fixed coverage of ordinary forms, inflections, multi-step suffixes,
# research-relevant vocabulary, and classic Porter boundary cases.
FIXTURE_WORDS = [
    "science",
    "physics",
    "subject",
    "technology",
    "intelligence",
    "artificial",
    "organization",
    "organizations",
    "organized",
    "organizing",
    "performance",
    "performed",
    "performing",
    "risks",
    "markets",
    "agreed",
    "disabled",
    "relational",
    "conditional",
    "rational",
    "digitizer",
    "vietnamization",
    "predication",
    "operator",
    "feudalism",
    "decisiveness",
    "hopefulness",
    "callousness",
    "formaliti",
    "sensitiviti",
    "sensibiliti",
    "triplicate",
    "formalize",
    "electriciti",
    "generously",
    "communism",
]

R_EXPRESSION = """
args <- commandArgs(trailingOnly = TRUE)
library_path <- args[[1]]
words <- args[-1]
.libPaths(c(library_path, .libPaths()))
if (as.character(packageVersion("SnowballC")) != "0.7.0") {
  stop("SnowballC 0.7.0 is required.")
}
cat(SnowballC::wordStem(words, language = "porter"), sep = "\\n")
"""


def snowballc_stems(words: list[str]) -> list[str]:
    command = [
        "Rscript",
        "--vanilla",
        "-e",
        R_EXPRESSION,
        str(SNOWBALLC_LIBRARY),
        *words,
    ]
    completed = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    stems = completed.stdout.splitlines()
    if len(stems) != len(words):
        raise RuntimeError(
            f"SnowballC returned {len(stems)} stems for {len(words)} words."
        )
    return stems


def main() -> None:
    if not SNOWBALLC_LIBRARY.is_dir():
        raise FileNotFoundError(
            "Pinned SnowballC library not found; run "
            "scripts/install_snowballc_0_7_0.R first."
        )

    r_stems = snowballc_stems(FIXTURE_WORDS)
    nltk_stemmer = PorterStemmer(mode=PorterStemmer.ORIGINAL_ALGORITHM)
    nltk_stems = [nltk_stemmer.stem(word) for word in FIXTURE_WORDS]
    rows = [
        {
            "original_token": word,
            "snowballc_stem": r_stem,
            "nltk_porter_stem": nltk_stem,
            "is_equal": str(r_stem == nltk_stem).lower(),
        }
        for word, r_stem, nltk_stem in zip(
            FIXTURE_WORDS, r_stems, nltk_stems, strict=True
        )
    ]
    differences = [row for row in rows if row["is_equal"] == "false"]

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    difference_lines = (
        [
            f"- `{row['original_token']}`: SnowballC `{row['snowballc_stem']}`, "
            f"NLTK `{row['nltk_porter_stem']}`"
            for row in differences
        ]
        if differences
        else ["- 없음"]
    )
    summary = [
        "# SnowballC and NLTK Porter fixture comparison",
        "",
        "- SnowballC: 0.7.0, `wordStem(language = \"porter\")`",
        "- NLTK: 3.10.0, `PorterStemmer(mode=ORIGINAL_ALGORITHM)`",
        f"- Fixture words: {len(rows)}",
        f"- Equal stems: {len(rows) - len(differences)}",
        f"- Different stems: {len(differences)}",
        "",
        "## Differences",
        "",
        *difference_lines,
        "",
        "이 결과는 소규모 고정 fixture 비교이며 두 구현의 전체 동등성 검증이 "
        "아니다. 기존 5개 기업 구체성 측정 결과는 변경하지 않았다. 차이가 "
        "발견된 경우에만 후속 확대 비교를 검토한다.",
        "",
    ]
    MARKDOWN_PATH.write_text("\n".join(summary), encoding="utf-8")

    print(f"fixture_words={len(rows)}")
    print(f"equal_stems={len(rows) - len(differences)}")
    print(f"different_stems={len(differences)}")
    print(f"csv={CSV_PATH.relative_to(REPOSITORY_ROOT)}")
    print(f"markdown={MARKDOWN_PATH.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
