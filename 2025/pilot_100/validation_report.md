# 2025 Pilot Text Extraction Validation Report

Updated: 2026-07-29

## Result

`PASS` — analysis-ready text extraction completed with retained section
warnings.

- Input HTML and matching source SHA-256: 100/100.
- Analysis, structure-preserved, and table-text files: 100 each.
- Empty analysis files and output SHA mismatches: 0.
- Total analysis words: 6,172,973.
- Company word counts: minimum 9,287; median 55,105; maximum 237,550.
- Analysis-text bytes / source-HTML bytes: 9.22%.
- Paragraphs: 141,796 rows and unique IDs across 100 companies.
- Sentences: 298,250 rows and unique IDs across 100 companies.
- HTML tag, script/style, XBRL namespace, and broken-character errors: 0.
- Parser attempts: 100 succeeded on attempt 1; no attempt 2/3 or failures.
- Idempotent rerun: 100 SHA-matched companies skipped.

## Major Item detection

| Item | Companies detected |
| --- | ---: |
| Item 1 | 72 |
| Item 1A | 84 |
| Item 7 | 84 |
| Item 8 | 85 |

Across the ten requested Items, 163 company-section rows are `not_present`.
There are 137 section-level boundary warnings. Optional absence is not a
failure. Company-level quality warnings are retained for 41 companies where a
core Item is missing or its detected boundary is unusually short or weak.

## Manual review

Five distinct companies were selected by minimum/maximum HTML size,
minimum/maximum analysis word count, and fixed seed `20250729`.

- Pass: NVR and CPRT.
- Warning: WFC likely lost material narrative because of table-based layout.
- Warning: D retained extensive text but Item 7 was not detected.
- Warning: ETR's Item 7 boundary is a short cross-reference in a
  multi-registrant filing.

These warnings remain in `failed_or_warning_cases.csv`; they were not
reclassified as successful section detection.

## Validation

All 30 tests, `py_compile`, annual constituent validation, extraction quality
checks, source/output SHA checks, and `git diff --check` pass. Detailed
paragraph and sentence tables are gzip CSVs to keep each repository file below
20 MB.

No AI classification, language-variable calculation, NLP model fitting,
financial-control collection, or sample expansion was performed. The next
stage is a 3-5 company language-variable smoke test.

## Step 4A smoke-test addendum

`PARTIAL` — five-company execution and structural validation pass, while five
dictionary/model-dependent constructs are explicitly blocked.

- Selected/input SHA matched: 5/5; unique company, CIK, accession: 5/5.
- Selected: NVDA (178 preliminary terms), HPE (168), TECH (0), WAT (23),
  and NSC (2).
- AI disclosure: 4 companies; non-disclosure: 1; direct AI sentences: 273.
- Company AI sentences: NVDA 137, HPE 119, TECH 0, WAT 16, NSC 1.
- Fog: NVDA 24.3196, HPE 28.6375, WAT 26.6898, NSC 30.0000; TECH is
  missing because its AI-sentence denominator is zero.
- Manual-review candidates: 31, all retained as `needs_manual_review`.
- Ratio-range errors, negative counts, infinity, structural errors, and
  `failed_after_3_attempts`: 0.
- Blocked: Brysbaert and Loughran-McDonald dictionaries; dependency parser
  for tense/passive.
- Idempotent rerun: five input-SHA/version matched companies skipped.
- No 100-company expansion, R2 operation, SEC request, or external financial
  data collection occurred.

All 45 repository tests, `py_compile`, smoke-test quality validation, and
`git diff --check` pass.
