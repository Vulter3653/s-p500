"""Preserve yearly extraction diagnostics before TemporaryDirectory cleanup.

Python imports ``sitecustomize`` during interpreter startup when this module is
available on ``sys.path``. The hook is deliberately inactive except for
``run_yearly_10k_batch.py`` executions that include ``--run-extraction``.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def _argument_value(name: str) -> str | None:
    try:
        index = sys.argv.index(name)
    except ValueError:
        return None
    if index + 1 >= len(sys.argv):
        return None
    return sys.argv[index + 1]


def _active() -> bool:
    return (
        bool(sys.argv)
        and Path(sys.argv[0]).name == "run_yearly_10k_batch.py"
        and "--run-extraction" in sys.argv
        and _argument_value("--output-dir") is not None
    )


if _active():
    _original_cleanup = tempfile.TemporaryDirectory.cleanup
    _output_root = Path(_argument_value("--output-dir") or ".").resolve()

    def _copy_diagnostics(source_root: Path) -> dict[str, object]:
        destination = _output_root / "extraction_diagnostics"
        copied: list[str] = []
        errors: list[str] = []

        for source in source_root.glob("*/*/text"):
            if not source.is_dir():
                continue
            try:
                shutil.copytree(source, destination / "text", dirs_exist_ok=True)
                copied.append(str(source))
            except Exception as error:  # diagnostic hook must never mask root error
                errors.append(f"{type(error).__name__}: {error}")

        for source in source_root.glob("*/*/html/manifest"):
            if not source.is_dir():
                continue
            try:
                shutil.copytree(
                    source,
                    destination / "html_manifest",
                    dirs_exist_ok=True,
                )
                copied.append(str(source))
            except Exception as error:
                errors.append(f"{type(error).__name__}: {error}")

        destination.mkdir(parents=True, exist_ok=True)
        metadata = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "temporary_root": str(source_root),
            "copied_sources": copied,
            "copy_errors": errors,
            "argv": sys.argv,
        }
        (destination / "diagnostic_hook.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return metadata

    def _diagnostic_cleanup(self) -> None:
        try:
            _copy_diagnostics(Path(self.name))
        except Exception as error:  # preserve original cleanup semantics
            try:
                destination = _output_root / "extraction_diagnostics"
                destination.mkdir(parents=True, exist_ok=True)
                (destination / "diagnostic_hook_failure.txt").write_text(
                    f"{type(error).__name__}: {error}\n",
                    encoding="utf-8",
                )
            except Exception:
                pass
        _original_cleanup(self)

    tempfile.TemporaryDirectory.cleanup = _diagnostic_cleanup
