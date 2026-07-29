# 2025 Pilot HTML Collection Validation Report

Updated: 2026-07-29

## Result

`PASS` — HTML collection completed.

- Input: only `sample/final_analysis_sample_100.csv`.
- Input rows and downloaded SEC primary filings: 100.
- HTML files and manifest rows: 100 each.
- Unique accessions and SHA-256 digests: 100 each.
- Empty or zero-byte files: 0.
- HTTP failures: 0.
- Retry events: 0.
- reportDate mismatches: 0.
- Maximum filing size: 18,147,230 bytes.
- Total HTML size: 448,173,188 bytes.

Every input row has exact form `10-K`, a reportDate in 2025, a filingDate no
later than 2026-07-29, and nonempty accession and primary-document fields.
Downloaded paths use `html/raw/<CIK>/<accession>.html`. The manifest records
the SHA-256 and byte size of each file.

The downloader was run a second time to verify idempotency. All 100 existing
files matched their recorded SHA-256 and were skipped without network
requests. The request log therefore remains at 100 successful HTTP 200 rows.
It contains only URL, start/end timestamps, status code, and retry flag; it
does not contain the SEC User-Agent value.

## Validation

The following completed successfully:

```bash
python scripts/download_10k_html.py
python -m unittest discover -s tests -p 'test_*.py' -v
python -m py_compile scripts/*.py tests/*.py
git diff --check
```

The suite ran 19 tests. SHA-256 values were recalculated from all 100 local
files and matched the manifest. No parsing, body extraction, NLP, AI analysis,
or linguistic-variable measurement was performed.
