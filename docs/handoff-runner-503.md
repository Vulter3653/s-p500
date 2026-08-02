# 503개 yearly 10-K runner 인수인계

## 원격 기준

- Repository: `Vulter3653/s-p500`
- Branch: `codex/generalize-yearly-10k-runner-503`
- Runner implementation commit: `24fb65db13f1c15b0554335d86d42e9820a1bd61`
- Latest handoff commits: `c0e51c9111be4bfc3932d9383ea0d441e9e771d7`, `296bea64e72d689b0f5053430ad8366032fda82a`
- Base main: `eb7d410daf10f1271f313b1cd0e0bc63d6db2ab5`
- VERSION: `0.12.0`

이 문서는 runner branch와 dashboard 작업선을 분리하고, Codespaces가 종료된 뒤
원격 branch에서 작업을 재개하기 위한 기록이다. 로컬 작업공간이 아니라 원격
commit과 Pull Request를 재개 기준으로 사용한다.

## 상태

- fixture/mock validation: `PASS` (34 tests)
- actual historical collection: 실행하지 않음
- main merge: 수행하지 않음
- runner PR: [#3](https://github.com/Vulter3653/s-p500/pull/3)
- runner Actions: [run 30741703453](https://github.com/Vulter3653/s-p500/actions/runs/30741703453), 성공
- 실제 SEC/R2/Google Drive 쓰기: 0

## 상수와 분할 규칙

- `MAX_SAMPLE_SIZE = 503`
- `BATCH_SIZE = 100`
- `MAX_BATCH_COUNT = 6`
- 503개 표본은 `100/100/100/100/100/3`으로 원래 manifest 순서를 유지해 분할한다.
- 504개, 0개, batch 0, 음수 및 실제 batch 수를 초과한 ID는 거부한다.

## 작업선 분리

### Dashboard

`main` 또는 `origin/main`에서 별도 branch를 사용한다. `web/`와 dashboard 문서·
테스트만 수정하며 yearly runner 파일을 변경하지 않는다.

### Historical runner

이 branch는 다음 파일과 직접 관련 문서·테스트만 담당한다.

- `.github/workflows/process-10k-yearly-batches.yml`
- `.github/workflows/test-yearly-runner-generalization.yml`
- `scripts/run_yearly_10k_batch.py`
- `scripts/extract_10k_analysis_text.py`
- `scripts/run_language_full_sample.py`
- `scripts/merge_yearly_10k_batches.py`
- `tests/test_yearly_batch_generalization.py`

PR #2 `codex/extend-historical-constituents`와 이 branch를 합치지 않는다.

## 새 Codespaces에서 재개

```bash
git clone https://github.com/Vulter3653/s-p500.git
cd s-p500
git fetch --all --prune
git switch codex/generalize-yearly-10k-runner-503
git pull --ff-only origin codex/generalize-yearly-10k-runner-503
git status --short
git rev-parse HEAD
git rev-parse origin/codex/generalize-yearly-10k-runner-503
python -m pip install -r requirements.txt
python -m py_compile \
  scripts/run_yearly_10k_batch.py \
  scripts/extract_10k_analysis_text.py \
  scripts/run_language_full_sample.py \
  scripts/merge_yearly_10k_batches.py
pytest -q tests/test_yearly_batch_generalization.py
```

Dashboard를 이어서 작업할 때는 runner branch를 사용하지 않는다.

```bash
git switch main
git pull --ff-only origin main
git switch -c codex/dashboard-small-fixes origin/main
```

## 보호 대상과 다음 단계

- `panel_2020_2025/` 변경 없음
- `analysis/descriptive_2020_2025/` 변경 없음
- `web/` 및 `web/public/data/` 변경 없음
- 기존 raw HTML, R2, Google Drive 변경 없음
- 다음 단계는 PR check 검토, PR #2 별도 검토, 사용자 승인 후 historical pilot이다.
- historical 실행 전에는 실제 collection, R2 write, Drive write를 수행하지 않는다.
