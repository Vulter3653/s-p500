#!/usr/bin/env python3
"""Build a persistent, verified R2-to-Drive manifest from yearly batch artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

REQUIRED = ("report_year", "cik", "accession_number", "r2_object_key", "r2_html_bytes", "r2_sha256")


def read_rows(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows.extend(csv.DictReader(handle))
    return rows


def build(batch_root: Path, report_year: str, sample_namespace: str, output: Path) -> dict:
    collection = sorted(batch_root.rglob("collection/r2_object_manifest.csv"))
    if not collection:
        raise ValueError(f"no R2 manifests under {batch_root}")
    batch_rows = read_rows(sorted(batch_root.rglob("batch_manifest.csv")))
    identity = {}
    for row in batch_rows:
        key = (row.get("cik", "").strip().zfill(10), row.get("accession_number", "").strip())
        if key[0] and key[1]:
            identity[key] = row
    merged: list[dict] = []
    seen: set[str] = set()
    prefix = f"{report_year}/{sample_namespace}/html/raw/"
    for source in read_rows(collection):
        cik = source.get("cik", "").strip().zfill(10)
        accession = source.get("accession_number", "").strip()
        key = source.get("object_key", "").strip()
        sha = source.get("sha256", "").strip().lower()
        size = source.get("file_size", "").strip()
        if not (cik and accession and key.startswith(prefix) and len(sha) == 64 and size.isdigit()):
            raise ValueError(f"invalid R2 manifest row: {source}")
        if key in seen:
            raise ValueError(f"duplicate R2 object key: {key}")
        seen.add(key)
        extra = identity.get((cik, accession), {})
        merged.append({
            "report_year": str(report_year),
            "sample_namespace": sample_namespace,
            "sample_order": extra.get("sample_order", ""),
            "company_id": extra.get("company_id", source.get("company_id", "")),
            "source_company_id": extra.get("source_company_id", source.get("company_id", "")),
            "ticker": extra.get("ticker", extra.get("symbol", source.get("ticker", ""))),
            "company_name": extra.get("company_name", source.get("company_name", "")),
            "cik": cik,
            "accession_number": accession,
            "r2_object_key": key,
            "r2_html_bytes": size,
            "r2_sha256": sha,
            "source_upload_status": source.get("upload_status", ""),
        })
    if not merged:
        raise ValueError("R2 manifest is empty")
    merged.sort(key=lambda row: (int(row["sample_order"]) if str(row["sample_order"]).isdigit() else 10**9, row["cik"], row["accession_number"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(merged[0])
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(merged)
    summary = {
        "report_year": str(report_year),
        "sample_namespace": sample_namespace,
        "rows": len(merged),
        "unique_r2_object_keys": len(seen),
        "sha256_rows": len(merged),
        "validation": "PASS",
        "source_files": [str(path) for path in collection],
    }
    summary_path = output.with_suffix(".json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-root", type=Path, required=True)
    parser.add_argument("--report-year", required=True)
    parser.add_argument("--sample-namespace", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.batch_root, args.report_year, args.sample_namespace, args.output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
