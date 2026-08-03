# Current historical backfill handoff

Updated: 2026-08-03 (codex)

## Remote source of truth

- Repository: Vulter3653/s-p500
- Main merge commit: e271eb31809f3d8d85a47cf625eb88843d7c7cf8
- Historical fixes are merged to `main`.
- Local Codespace branch may be behind; do not use it as source of truth.

## Active Actions run

- Run: 30794955519
- URL: https://github.com/Vulter3653/s-p500/actions/runs/30794955519
- Ref: main
- Inputs: 2019, execute=true, confirmation=RUN_CONTINUOUS_HISTORICAL_BACKFILL, reuse_run_id=30788897235
- Purpose: reuse completed 2019 batch artifacts; no collection/R2 re-upload.
- Last observed state: `finalize-and-publish` was running `Measure canonical language extensions from existing artifacts`; prepare and yearly batch merge had succeeded.
- Expected next checks: annual keyword validation, canonical panel append, dashboard generation/build, publication branch summary.
- Do not start a duplicate 2019 run while this run is in progress.

## Resume procedure

```bash
git fetch --all --prune
git switch main
git pull --ff-only origin main
gh run view 30794955519 --json status,conclusion,jobs
gh run view 30794955519 --log-failed
```

If the run fails, inspect the first failed step only. Reuse the existing 2019 artifacts; do not recollect SEC HTML or overwrite R2 objects. Apply any fix on a new branch from current `origin/main`, update CHANGELOG/progress/debug-log, merge through a reviewed PR, then rerun only the failed/recovery path.

PR #7 is an obsolete candidate and must not be merged without schema validation.
