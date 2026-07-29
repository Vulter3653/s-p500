# 2025 Pilot Final Validation Report

Updated: 2026-07-29

## Result

`PASS` for final sample and SEC filing metadata.

- Final analysis sample: 100 rows.
- Eligible analysis filings: 100 exact Form 10-K filings.
- Unique final IDs, company keys, CIKs, and accessions: 100 each.
- TXT count: 0; ITW count: 1; Industrials count: 16.
- Missing primary documents: 0.
- Form, reportDate, and filingDate cutoff errors: 0.
- Unresolved manual reviews: 0.
- Relevant 10-K/A: 2 companies, preserved for audit only.

## Sampling and replacement

The initial proportional stratified sample was drawn from 487 companies with
verified CIK and GICS sector. Thirteen records with missing GICS, including
three with unverified CIK, were excluded from the frame. TXT (`P2025-059`) has
no 2025 reportDate Form 10-K and remains in audit records with
`analysis_included=0`.

ITW is the first deterministic eligible Industrials reserve under seed
`20250729`, within-sector order 17. It receives `P2025-R001`; no original ID is
reused. No new draw, AI information, filing text, or linguistic outcome
influenced the replacement.

| Sector | Final n |
| --- | ---: |
| Communication Services | 4 |
| Consumer Discretionary | 10 |
| Consumer Staples | 7 |
| Energy | 4 |
| Financials | 15 |
| Health Care | 12 |
| Industrials | 16 |
| Information Technology | 14 |
| Materials | 5 |
| Real Estate | 7 |
| Utilities | 6 |

FOXA/FOX, GE, TXT, and ITW reviews are resolved. The request log remains
unchanged at 769 rows and is not an analysis dataset.

## Validation

`python scripts/validate_annual_constituents.py`, 13 network-independent unit
tests, `python -m py_compile scripts/*.py tests/*.py`, repeat replacement
execution, and `git diff --check` passed on 2026-07-29. Integration smoke
testing was not repeated because SEC collection logic did not change.

Raw filing HTML, full text, and linguistic variables have not been created.
Future HTML collection must use only `sample/final_analysis_sample_100.csv`.
