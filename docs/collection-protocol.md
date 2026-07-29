# SEC Filing Metadata Collection Protocol

Updated: 2026-07-29

## Scope

This stage finalizes metadata for the 2025 pilot. The immutable initial draw is
`2025/pilot_100/sample/pilot_sample_100.csv`; the sole downstream filing-HTML
input is `2025/pilot_100/sample/final_analysis_sample_100.csv`. It does not download filing HTML,
extract text, measure language, or expand to 500 companies.

The 100 companies were selected from 487 companies with both verified CIK and
nonmissing GICS sector. Thirteen companies with missing GICS sector were
excluded, including three whose CIK was also unverified. This is a pilot
limitation that must be resolved before full-sample expansion.

## SEC rules

- Endpoint: official `https://data.sec.gov/submissions/` only.
- Identity key: zero-padded 10-digit CIK. Names and tickers are review aids and
  never replace the CIK.
- User-Agent: supplied only through `SEC_USER_AGENT`; its value is never stored.
- Rate: at least 0.25 seconds between network requests, no parallel requests.
- Reliability: 30-second timeout, four retries, exponential backoff for 429 and
  5xx responses, URL-keyed local JSON cache, and duplicate-URL suppression.
- Audit log: CIK, URL, UTC time, HTTP status, retry count, cache flag, elapsed
  time, and error type only.
- Cache path `2025/pilot_100/cache/` is ignored by Git.

`filings.recent` and historical fragments whose filing-date coverage can
overlap 2025-01-01 through the 2026-07-29 cutoff are searched.

## Filing selection

The primary filing must have exact form `10-K`, `reportDate` within calendar
2025, filing date no later than 2026-07-29, a valid SEC accession number, and a
nonempty primary document. One candidate is `eligible`, none is
`no_eligible_2025_10k`, and multiple candidates are
`ambiguous_multiple_eligible`. Form `10-K/A` is never substituted for the
primary filing; relevant amendments are linked by report date and recorded
separately.

CIK mismatch is an identity error. Entity names are normalized by lowercasing,
removing punctuation and common corporate suffixes; low name similarity is
manual review, not automatic rejection. All SEC tickers and exchanges are
preserved because ticker changes and multiple share classes are possible.

## Approved replacement

TXT (`P2025-059`) has no exact Form 10-K with a reportDate in calendar 2025 and
remains in audit files with `analysis_included=0`. ITW is the first
deterministic Industrials reserve under seed `20250729` (within-sector order
17), receives `P2025-R001`, and has `analysis_included=1`. No new random draw,
AI-related information, or filing text was used. The replacement preserves the
original sector allocation and yields 100 eligible primary filings.

## Text extraction

The sole extraction input is `html/manifest/html_manifest.csv`, whose 100
source SHA-256 values are revalidated before parsing. The parser follows the
cleaning principles of Cooper, Ewing, and Mishra (2022), adapted to modern
inline XBRL. It removes hidden and executable markup, separates tables from
narrative text, normalizes Unicode, preserves punctuation and case, and links
paragraphs, sentences, and detected Items to the original accession.

Detailed paragraph and sentence tables are gzip-compressed CSV files because
their uncompressed forms exceed 20 MB. Section warnings and `not_present`
statuses are retained for audit. No SEC network request occurs in this stage.
