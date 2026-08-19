# Baek et al. preprocessing reproduction

Primary order: alphabetic tokenization, NFKC lowercase normalization, SMART removal, Porter stemming, and Brysbaert score matching.

The official tidytext 0.3.1 documentation says `stop_words` has 1,149 total rows across SMART, onix, and snowball. Its RDA contains 571 SMART rows and 570 unique SMART entries because `would` appears twice. This differs from Appendix A's statement that SMART itself has 1,149 stopwords. The implementation uses the actual SMART subset and does not add entries.

Porter stemming uses NLTK 3.10.0 `PorterStemmer` in `ORIGINAL_ALGORITHM` mode. The pinned R 4.3.3 and SnowballC 0.7.0 environment was subsequently installed and checked. A 2026-08-19 validation found identical stems for all 37,058 Brysbaert single-word entries and all 32,009 eligible unique tokens in the existing 2025 pilot 100-company analysis text. See `analysis/concreteness_validation/concreteness_validation_report.md`.

Matching hierarchy:

1. Exact lowercase original single-word entry.
2. If absent, a Porter stem mapping to exactly one single-word dictionary entry.
3. A stem mapping to multiple entries remains unmatched and is flagged.

Scores are never averaged across a collision. Two-word expressions are preserved and validated in the source dictionary but are not used by the primary word-token pipeline because Baek et al. describe word tokenization before matching.

The official XLSX records `subject` as 3.14 although Baek et al. print 3.13. Official scores produce raw means 3.105 and 2.965; Python two-decimal rounding reproduces the reported 3.10 and 2.96.
