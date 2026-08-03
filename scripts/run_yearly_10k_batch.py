#!/usr/bin/env python3
"""Run one yearly 10-K batch and preserve extraction failure evidence."""

from __future__ import annotations

import traceback

try:
    from . import run_yearly_10k_batch_core as core
    from .run_yearly_10k_batch_core import *  # noqa: F401,F403
except ImportError:
    import run_yearly_10k_batch_core as core
    from run_yearly_10k_batch_core import *  # noqa: F401,F403


def preserve_extraction_diagnostics(
    work_root: core.Path,
    output_root: core.Path,
    arguments,
    failed_stage: str,
    error: BaseException,
) -> None:
    """Copy extraction evidence before TemporaryDirectory removes it."""
    diagnostics_root = output_root / "extraction_diagnostics"
    diagnostics_root.mkdir(parents=True, exist_ok=True)
    sample_root = stage_root(
        work_root, arguments.report_year, arguments.sample_namespace
    )
    sources = {
        "html_manifest": sample_root / "html/manifest",
        "extraction_results": sample_root / "text/extraction_results",
        "processing_logs": sample_root / "text/processing_logs",
        "analysis_tables": sample_root / "text/analysis_tables",
    }
    copied_paths = {}
    for name, source in sources.items():
        destination = diagnostics_root / name
        exists = source.exists()
        copied_paths[name] = {
            "source": str(source),
            "destination": str(destination),
            "copied": exists,
        }
        if not exists:
            continue
        if source.is_dir():
            core.shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            core.shutil.copy2(source, destination)

    metadata = {
        "preserved_at": utc_now(),
        "report_year": arguments.report_year,
        "sample_namespace": arguments.sample_namespace,
        "batch_id": arguments.batch_id,
        "failed_stage": failed_stage,
        "exception_type": type(error).__name__,
        "exception_message": str(error),
        "temporary_root": str(work_root),
        "output_root": str(output_root),
        "source_manifest": str(arguments.manifest.resolve()),
        "runner_arguments": {
            "run_collection": arguments.run_collection,
            "run_extraction": arguments.run_extraction,
            "run_language": arguments.run_language,
            "force": arguments.force,
        },
        "copied_paths": copied_paths,
    }
    (diagnostics_root / "diagnostic_metadata.json").write_text(
        core.json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (diagnostics_root / "traceback.txt").write_text(
        "".join(
            traceback.format_exception(
                type(error), error, error.__traceback__
            )
        ),
        encoding="utf-8",
    )


def write_diagnostic_hook_failure(
    output_root: core.Path, diagnostic_error: BaseException
) -> None:
    """Best-effort logging that never masks the original extraction error."""
    try:
        diagnostics_root = output_root / "extraction_diagnostics"
        diagnostics_root.mkdir(parents=True, exist_ok=True)
        (diagnostics_root / "diagnostic_hook_failure.txt").write_text(
            "".join(
                traceback.format_exception(
                    type(diagnostic_error),
                    diagnostic_error,
                    diagnostic_error.__traceback__,
                )
            ),
            encoding="utf-8",
        )
    except Exception:
        pass


def run_batch(arguments) -> dict:
    started = core.time.monotonic()
    manifest_path = arguments.manifest.resolve()
    output_root = arguments.output_dir.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    fields, source_rows = read_manifest(manifest_path)
    source_rows = validate_source_manifest(source_rows, arguments.report_year)
    rows = split_batch(source_rows, arguments.batch_id)
    validate_batch(rows)
    batch_manifest = output_root / "batch_manifest.csv"
    write_batch_manifest(batch_manifest, fields, rows)
    write_empty_support_files(output_root)
    summary = {
        "report_year": arguments.report_year,
        "sample_namespace": arguments.sample_namespace,
        "batch_id": arguments.batch_id,
        "source_manifest": manifest_path.name,
        "source_rows": len(source_rows),
        "manifest_row_count": len(source_rows),
        "batch_size_limit": BATCH_SIZE,
        "batch_count": batch_count(len(source_rows)),
        "batch_start_index": (arguments.batch_id - 1) * BATCH_SIZE,
        "batch_end_index_exclusive": (
            (arguments.batch_id - 1) * BATCH_SIZE + len(rows)
        ),
        "batch_row_count": len(rows),
        "maximum_sample_size": MAX_SAMPLE_SIZE,
        "duplicate_count": 0,
        "missing_count": 0,
        "batch_rows": len(rows),
        "row_start": (arguments.batch_id - 1) * BATCH_SIZE + 1,
        "row_end": (arguments.batch_id - 1) * BATCH_SIZE + len(rows),
        "run_collection": arguments.run_collection,
        "run_extraction": arguments.run_extraction,
        "run_language": arguments.run_language,
        "force": arguments.force,
        "status": "empty" if not rows else "success",
        "failed_stage": "",
        "error_type": "",
        "elapsed_seconds": 0,
        "completed_at": "",
    }
    if not rows:
        summary["elapsed_seconds"] = round(core.time.monotonic() - started, 3)
        summary["completed_at"] = utc_now()
        (output_root / "batch_summary.json").write_text(
            core.json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(core.json.dumps(summary, sort_keys=True))
        return summary

    failed_stage = "preparation"
    try:
        with core.tempfile.TemporaryDirectory(
            prefix=f"s-p500-{arguments.report_year}-batch-{arguments.batch_id}-"
        ) as temporary:
            work_root = core.Path(temporary)
            try:
                sample_root = stage_root(
                    work_root,
                    arguments.report_year,
                    arguments.sample_namespace,
                )
                fixed_sample = sample_root / "sample/batch_manifest.csv"
                write_batch_manifest(fixed_sample, fields, rows)
                if arguments.run_collection:
                    failed_stage = "collection"
                    collect_and_upload(
                        work_root,
                        output_root,
                        rows,
                        arguments.report_year,
                        arguments.sample_namespace,
                    )
                if arguments.run_extraction:
                    failed_stage = "extraction_input"
                    if not arguments.run_collection:
                        download_html_from_r2(
                            work_root,
                            output_root,
                            rows,
                            arguments.report_year,
                            arguments.sample_namespace,
                        )
                    failed_stage = "extraction"
                    extraction_summary = extract(
                        work_root,
                        input_relative=sample_root.relative_to(work_root)
                        / "html/manifest/html_manifest.csv",
                        output_relative=sample_root.relative_to(work_root)
                        / "text",
                        retry_warning=arguments.force,
                        retry_failed=arguments.force,
                    )
                    if int(extraction_summary["failed"]):
                        raise RuntimeError(
                            "one or more extraction records failed"
                        )
                    copy_extraction_artifacts(
                        work_root,
                        output_root,
                        arguments.report_year,
                        arguments.sample_namespace,
                    )
                if arguments.run_language:
                    failed_stage = "language_input"
                    if not arguments.run_extraction:
                        stage_existing_text(
                            work_root,
                            manifest_path,
                            rows,
                            arguments.report_year,
                            arguments.sample_namespace,
                        )
                    failed_stage = "language"
                    run_language(
                        work_root,
                        output_root,
                        arguments.report_year,
                        arguments.sample_namespace,
                    )
            except Exception as error:
                if failed_stage == "extraction":
                    try:
                        preserve_extraction_diagnostics(
                            work_root,
                            output_root,
                            arguments,
                            failed_stage,
                            error,
                        )
                    except Exception as diagnostic_error:
                        write_diagnostic_hook_failure(
                            output_root, diagnostic_error
                        )
                raise
        failed_stage = ""
    except Exception as error:
        summary["status"] = "failed"
        summary["failed_stage"] = failed_stage
        summary["error_type"] = type(error).__name__
        write_csv(
            output_root / "quality_check/failed_companies.csv",
            [
                {
                    "company_id": row["final_sample_id"],
                    "cik": row["cik"],
                    "accession_number": row["accession_number"],
                    "failure_stage": failed_stage,
                    "failure_reason": type(error).__name__,
                }
                for row in rows
            ],
            [
                "company_id",
                "cik",
                "accession_number",
                "failure_stage",
                "failure_reason",
            ],
        )
        summary["elapsed_seconds"] = round(
            core.time.monotonic() - started, 3
        )
        summary["completed_at"] = utc_now()
        (output_root / "batch_summary.json").write_text(
            core.json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(core.json.dumps(summary, sort_keys=True))
        raise

    summary["elapsed_seconds"] = round(core.time.monotonic() - started, 3)
    summary["completed_at"] = utc_now()
    (output_root / "batch_summary.json").write_text(
        core.json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(core.json.dumps(summary, sort_keys=True))
    return summary


def parse_arguments():
    parser = core.argparse.ArgumentParser()
    parser.add_argument("--report-year", required=True)
    parser.add_argument("--batch-id", required=True, type=int)
    parser.add_argument("--manifest", required=True, type=core.Path)
    parser.add_argument("--sample-namespace", default="sample_500")
    parser.add_argument("--run-collection", action="store_true")
    parser.add_argument("--run-extraction", action="store_true")
    parser.add_argument("--run-language", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--output-dir", required=True, type=core.Path)
    arguments = parser.parse_args()
    if not core.re.fullmatch(r"\d{4}", arguments.report_year):
        parser.error("--report-year must be a four-digit year")
    if arguments.batch_id < 1:
        parser.error("--batch-id must be at least 1")
    return arguments


if __name__ == "__main__":
    try:
        run_batch(parse_arguments())
    except Exception as error:
        print(
            f"batch_failed={type(error).__name__}",
            file=core.sys.stderr,
        )
        raise SystemExit(1)
