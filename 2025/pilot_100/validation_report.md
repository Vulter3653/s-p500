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
# Step 4B-2 validation

- Official source: University of Notre Dame SRAF, release 1993–2025, page updated March 2026.
- Original: 9,093,460 bytes; 86,553 data rows; 17 columns; SHA-256 `e2d1328682bab7d2187684fb9f5420bb730401c9eefc00daf835edd203f4859d`.
- Active words: Positive 347; Negative 2,345; Uncertainty 297; Litigious 903; Strong Modal 19; Weak Modal 27; Constraining 184.
- Removal markers: 19 negative source values; active inclusion errors 0.
- Sample: 5 unique companies; 273 unchanged AI sentences; TECH AI denominator zero; NSC one AI sentence.
- Outputs: uncertainty 5 rows; sentiment 5 rows; report controls 5 rows; combined results 5 rows.
- Quality: ratio range errors 0; negative counts 0; infinite values 0; structural errors 0; failed-after-three-attempts 0.
- Blocked statuses preserved: Brysbaert concreteness, dependency tense, dependency passive voice.
- Not performed: full 100-company language measurement, human truth labels, R2, external financial controls.
# Step 4C validation

- Official dictionary: 39,954 entries, 37,058 single words, 2,896 two-word expressions, 8 columns, score range 1.04–5.00.
- Dictionary SHA-256: `1673ead761e28833a40e82c0d20f10782955ced9366d600eafeefee0f2254545`.
- SMART: tidytext 0.3.1, 1,149 total dataset rows, 571 SMART rows, 570 unique SMART entries, one duplicated `would`.
- SMART canonical SHA-256: `220f9e4fde204eb4d4a216f4b5024633b61e41555809f95d9b12f0773be0a3f3`.
- Paper examples: physics 3.10 and science 2.96, both PASS.
- AI sentences: 273 unchanged; companies: 5 unchanged; LM reference counts unchanged.
- AI coverage: NVDA 0.651, HPE 0.665, WAT 0.701, NSC 0.842; TECH denominator zero.
- Report coverage range: 0.734–0.765.
- Ambiguous stems are excluded, not averaged; four AI-bearing companies retain collision warnings.
- Ratio, score-range, negative count, infinite, structural, and failed-after-three-attempt errors: 0.
- LIWC2015 time focusing and passive voice remain blocked. Full-sample and R2 work were not performed.
