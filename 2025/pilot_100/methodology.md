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
