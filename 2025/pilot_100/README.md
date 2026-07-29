# 2025 100-Company 10-K Pilot

This directory contains a reproducible metadata and HTML-collection pilot, not
research results. The sample uses seed `20250729` and GICS proportional allocation from
487 eligible companies. It excludes 13 companies with missing sector metadata,
which must be addressed before expansion.

Current stage:

- Initial 100-company sample preserved without using AI text outcomes.
- TXT replaced by deterministic Industrials reserve ITW (`P2025-R001`) without
  a new random draw.
- Final sample fixed at 100 companies and 100 eligible 2025 report-year 10-Ks.
- 10-K/A recorded separately.
- SEC primary filing HTML collection completed for all 100 final-sample filings.
- Analysis-ready text extraction completed for all 100 filings.
- A five-company language-measurement smoke test was run; it is not a
  full-sample research result.

`sample/pilot_sample_100.csv` is the original draw, while
`sample/final_analysis_sample_100.csv` is the sole input for future filing HTML
downloads. `sample/` also contains reserve ordering. `metadata/` contains
small, Git-eligible indexes and manifests. `logs/sec_requests.jsonl` is an
audit log without the User-Agent value. `cache/` contains ignored SEC responses.
`html/raw/` contains one immutable downloaded primary HTML per company;
`html/manifest/` records SHA-256 and file sizes, and `html/logs/` records
request timing and HTTP status without the User-Agent value.
`text/company_text/` contains analysis, structure-preserved, and excluded-table
text. `text/section_text/` contains major 10-K Item files. Detailed paragraph
and sentence tables are gzip-compressed CSVs under `text/analysis_tables/`.
`language_smoke_test/` contains the five-company selection, direct AI-term
sentence matches, dependency-free readability and report controls, explicit
blocked-dependency statuses, review candidates, and reproducibility inventories.

Run:

```bash
python scripts/build_pilot_sample.py
python scripts/collect_sec_filing_metadata.py
python scripts/apply_pilot_replacement.py
python scripts/download_10k_html.py
python scripts/extract_10k_analysis_text.py
python scripts/check_extracted_text_quality.py
python scripts/select_language_smoke_test_companies.py
python scripts/run_language_smoke_test.py
python scripts/check_language_smoke_test_quality.py
python -m unittest discover -s tests -p 'test_*.py' -v
```

The collector requires a real `SEC_USER_AGENT` environment variable.
