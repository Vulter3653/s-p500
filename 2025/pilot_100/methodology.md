# Pilot Metadata Methodology

Updated: 2026-07-29

The sampling frame is the 2025 S&P 500 company file after excluding records
without verified CIK or GICS sector. The target of 100 is allocated across
sectors by proportional quotas and largest remainders. A deterministic
sector-specific ordering uses seed `20250729`; AI mentions or other document
content are not used.

The initial draw remains immutable. TXT (`P2025-059`) was excluded because no
exact Form 10-K has a reportDate in 2025. ITW was the first deterministic
same-sector reserve (Industrials order 17) and was added as `P2025-R001`.
There was no new random draw and the original sector allocation is unchanged.
The frame contained 487 eligible companies; 13 records lacking GICS sector,
including three also lacking verified CIK, were excluded before sampling.

The filing unit is one company and one Form 10-K whose SEC `reportDate`, rather
than filing year, falls in 2025. The filing-date cutoff is 2026-07-29. Missing
or invalid accession numbers and primary documents are review defects.
Multiple eligible filings are not resolved automatically.

CIK is the legal-entity identity key. Names are compared after case folding,
punctuation removal, whitespace normalization, and removal of common corporate
suffixes. Low name similarity and missing current ticker matches are review
signals only.

This stage measures collection feasibility only. It does not download HTML,
construct linguistic variables, test hypotheses, estimate causal effects, or
support Construal Level Theory claims.

`sample/final_analysis_sample_100.csv` is the only input to the next HTML
download stage. TXT remains in audit metadata.

## HTML collection

The HTML collector uses only `sample/final_analysis_sample_100.csv`. For each
of its 100 rows it requests the exact SEC Archives accession and primary
document, at no more than one request per second. Responses are stored by CIK
and accession, with SHA-256, byte size, UTC download time, HTTP status, and
idempotent skip status in the HTML manifest. HTTP 429, 500, 502, and 503 are
eligible for exponential-backoff retry.

HTML collection is complete. No HTML parsing, body-text extraction, NLP,
language-variable measurement, or substantive analysis has been performed.

## Analysis-ready text

Following the general cleaning sequence in Cooper, Ewing, and Mishra (2022),
modern SEC inline-XBRL HTML is parsed as visible text. Script, style, hidden
content, XBRL metadata, navigation markup, comments, standalone page numbers,
and repeated consecutive blocks are removed. Unicode and HTML entities are
normalized without stemming, lemmatization, spelling correction, stopword
removal, or case folding.

Tables are excluded from the primary language-analysis text but retained in
separate table-text files, with removal markers in the structure-preserved
version. Paragraph, sentence, and major Item boundaries retain company, CIK,
and accession lineage. Missing optional sections are recorded as
`not_present`, not as extraction failures.

Five companies were reviewed at document start, Items 1A/7/8, and document
end. WFC showed likely material narrative loss from a table-based layout; D
did not yield an Item 7 boundary; and ETR's detected Item 7 was a short
cross-reference. These remain explicit warnings. Language variables and AI
classification have not been applied to the full 100-company sample.

## Five-company language smoke test

Seed `20250729` selected NVDA and HPE by the highest preliminary AI-term
counts, TECH by the lowest count, WAT by proximity to the eligible median
analysis length, and NSC by fixed-seed random selection. Only extraction
`success` and quality `pass` companies were eligible; WFC, D, and ETR were
explicitly excluded.

AI sentences are narrative sentence-corpus rows containing a direct,
alphabetically bounded pilot-dictionary match. Adjacent sentences are retained
only as review context. Tables are excluded. Fog uses the standard formula and
a deterministic vowel-group syllable heuristic; proper nouns and abbreviations
can inflate complex-word counts.

No locally sourced, license-documented Brysbaert concreteness or
Loughran-McDonald dictionary, spaCy package, or English dependency model was
available. Concreteness, uncertainty, financial sentiment, tense, and passive
voice therefore remain missing with explicit blocked statuses; no invented
dictionary, LIWC substitution, or `be + participle` shortcut was used.
