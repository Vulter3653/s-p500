# Brysbaert textual concreteness resources

The official aggregated Springer supplementary XLSX and tidytext source files are local-only and Git-ignored.

Expected paths:

- `original_source_files/concreteness_ratings_brysbaert_et_al_2014.xlsx`
- `original_source_files/tidytext_0.3.1_stop_words.rda`

Validation:

```bash
python scripts/load_brysbaert_concreteness_dictionary.py --validate-only
python scripts/load_smart_stopwords.py --validate-only
```

Optional local analysis-ready generation:

```bash
python scripts/load_brysbaert_concreteness_dictionary.py --validate-only --write-analysis-file
python scripts/load_smart_stopwords.py --validate-only --write-analysis-file
```

Measurement:

```bash
python scripts/run_language_smoke_test.py --retry-blocked-concreteness
python scripts/check_language_smoke_test_quality.py
```
