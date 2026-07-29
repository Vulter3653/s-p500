# R and SnowballC 0.7.0 environment

This environment pins the `SnowballC` version used by Baek, Ihm, and Kang
(2023). This step only establishes and validates the software environment; it
does not compare stems with NLTK or rerun the five-company measurements.

Install Ubuntu R first:

```bash
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y r-base r-base-dev
```

Install and validate the pinned package:

```bash
Rscript scripts/install_snowballc_0_7_0.R
Rscript scripts/check_snowballc_0_7_0.R
```

The project-relative library is
`references/software/r_library/snowballc_0_7_0`. Compiled packages and the
cached source archive under `references/software/r_library/` are excluded from
Git. Reinstallation uses the same install command and skips when version 0.7.0
is already valid.
