#!/usr/bin/env python3
"""Run the reproducible descriptive-language analysis pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(command: list[str]) -> None:
    print("[pipeline]", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--feature-dir", type=Path)
    parser.add_argument("--extended-panel", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--statistics-only", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    extended = args.extended_panel or output / "firm_year_language_extended.parquet"
    if not args.statistics_only:
        if args.panel is None or args.feature_dir is None:
            raise SystemExit("--panel and --feature-dir are required unless --statistics-only is used")
        features = sorted(args.feature_dir.glob("year_*/extended_features_*.csv"))
        if not features:
            features = sorted(args.feature_dir.glob("*/extended_language_features.csv"))
        if len(features) != 6:
            raise SystemExit(f"expected six feature files, found {len(features)}")
        run([sys.executable, str(root / "scripts/build_extended_language_panel.py"),
             "--panel", str(args.panel), "--features", *map(str, features),
             "--output-dir", str(output)])
    elif not extended.exists():
        raise SystemExit(f"extended panel not found: {extended}")

    run([sys.executable, str(root / "scripts/run_descriptive_statistics.py"),
         "--panel", str(extended), "--output-dir", str(output)])
    run([sys.executable, str(root / "scripts/create_descriptive_figures.py"),
         "--panel", str(extended), "--output-dir", str(output)])
    run([sys.executable, str(root / "scripts/write_descriptive_reports.py"),
         "--panel", str(extended), "--output-dir", str(output)])

    if args.cleanup:
        print("[pipeline] cleanup is limited to caller-managed temporary artifacts", flush=True)


if __name__ == "__main__":
    main()
