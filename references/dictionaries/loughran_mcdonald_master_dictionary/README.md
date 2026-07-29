# Loughran-McDonald financial dictionary

This directory stores reproducibility metadata for the official 1993–2025 Master Dictionary. The original and complete analysis-ready files are intentionally Git-ignored because public redistribution permission is unclear.

Expected local source:

`original_source_files/loughran_mcdonald_master_dictionary_1993_2025.csv`

Validation:

```bash
python scripts/load_loughran_mcdonald_dictionary.py --validate-only
```

Generate the local analysis-ready file:

```bash
python scripts/load_loughran_mcdonald_dictionary.py --validate-only --write-analysis-file
```

The loader includes a category only when its source value is positive. Zero means not a member; negative values mark removals and are excluded. Membership in multiple categories is retained independently.
