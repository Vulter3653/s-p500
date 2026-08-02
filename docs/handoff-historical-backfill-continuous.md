# 연속 historical backfill 인수인계

이 문서는 Codespace 종료 후 `codex/historical-backfill-continuous` 작업을 안전하게 재개하기 위한 원격 기준 기록이다. 현재 단계에서는 실제 historical 수집이나 publication을 실행하지 않았다.

## 원격 기준

- 저장소: `Vulter3653/s-p500`
- integration branch: `codex/historical-backfill-continuous`
- integration branch는 runner branch `codex/generalize-yearly-10k-runner-503`의 원격 최신 상태에서 생성되었다.
- runner PR: [PR #3](https://github.com/Vulter3653/s-p500/pull/3)
- historical constituent PR: PR #2, branch `codex/extend-historical-constituents`
- main 기준선: `eb7d410daf10f1271f313b1cd0e0bc63d6db2ab5`
- runner 구현 기준: `24fb65db13f1c15b0554335d86d42e9820a1bd61`
- runner fixture Actions: run `30741703453` 성공
- publication branch 예정: `historical-dashboard-data`

원격 Git branch와 커밋이 Codespace 로컬 상태보다 우선한다. 로컬 Git 저장소가 읽기 전용인 경우에도 원격 branch를 기준으로 작업을 재개한다.

## 현재 상태

- 503개 yearly runner 일반화는 PR #3에서 보존되어 있다.
- `MAX_SAMPLE_SIZE=503`, `BATCH_SIZE=100`, `MAX_BATCH_COUNT=6`이다.
- 503개 표본은 100/100/100/100/100/3으로 분할한다.
- batch 6을 지원하고 batch 7·0·음수 및 504개 manifest를 거부하는 fixture 검증이 포함되어 있다.
- 동적 `report_year/sample_namespace` staging path와 기존 R2 key 호환성이 구현되어 있다.
- 실제 historical collection, extraction, language measurement, cumulative panel update, dashboard publication은 아직 실행하지 않았다.
- SEC 요청, R2 쓰기, Google Drive 쓰기 및 main 병합은 0회이다.
- 기존 `panel_2020_2025/`, `analysis/descriptive_2020_2025/`, 기존 web generated data와 원본 HTML은 보호 대상이며 변경하지 않는다.

## 다음 구현 목표

한 Actions run은 한 연도만 처리하고, 성공한 경우에만 다음 연도 `current_year - 1`을 dispatch한다.

```text
2019 → 2018 → 2017 → 2016 → 2015 → …
```

2017에서 중단하지 않는다. source-supported earliest year와 사용자가 지정한 하한을 넘지 않는 범위에서 계속한다. 연도 간 병렬 실행은 금지하고, 연도 내부 batch만 병렬화한다.

종료 조건은 완전히 검증된 연도 3개에서 `annual_ai_keyword_count=0`이 연속되는 경우뿐이다. 결측, 수집·추출·언어 측정·분석·publication 실패, partial 결과는 0으로 처리하지 않는다. 세 번째 0 연도도 panel과 dashboard에 먼저 반영한 뒤 chain을 종료한다.

## 후속 작업 순서

1. 새 Codespace에서 원격 branch를 clone/fetch하고 integration branch로 전환한다.
2. PR #2의 historical constituent 구현을 검토하고 integration branch에 안전하게 통합한다. PR #2와 PR #3 원 branch는 직접 수정하지 않는다.
3. 실제 패널 schema와 기존 AI detector output을 확인하여 `annual_ai_keyword_count`의 source column과 계산 규칙을 확정한다. 새 사전은 만들지 않는다.
4. descending orchestration workflow, chain state, zero-streak state machine, source-supported earliest-year 검증을 구현한다.
5. historical candidate panel을 별도 경로에서 원자적으로 갱신한다. 기존 2020–2025 패널은 덮어쓰지 않는다.
6. full candidate panel을 source로 historical dashboard data와 Figure source를 재생성한다. UI 대규모 재설계는 하지 않는다.
7. publication branch `historical-dashboard-data`에 panel·dashboard data·manifest·build metadata를 동일 commit으로 기록하고 Cloudflare preview만 사용한다.
8. fixture/mock 테스트와 dry-run을 먼저 통과시킨다.
9. 사용자의 별도 승인과 `execute=true`, `confirmation=RUN_CONTINUOUS_HISTORICAL_BACKFILL` 확인 없이는 2019 실제 수집을 dispatch하지 않는다.

## 권장 후보 경로

```text
panel_historical_candidate/
analysis/historical_backfill/<year>/
analysis/historical_candidate/
automation/historical_backfill/
web/public/data/historical-candidate/
web/public/downloads/historical-candidate/
```

구체적인 기존 CLI와 schema를 확인하기 전에는 이 경로에 실제 파일을 만들거나 기존 generator를 가정하여 수정하지 않는다.

## 재접속 명령

```bash
git clone https://github.com/Vulter3653/s-p500.git
cd s-p500
git fetch --all --prune
git switch codex/historical-backfill-continuous
git pull --ff-only origin codex/historical-backfill-continuous
git status --short
git rev-parse HEAD
git branch -vv
```

그 다음 저장소의 `AGENTS.md`, `docs/writing-rules.md`, `docs/progress.md`, `CHANGELOG.md`, `docs/debug-log.md`를 먼저 읽고, PR #2·PR #3·현재 workflow와 실제 CLI를 재감사한다.

## 안전 정책

- force push, reset, 기존 커밋 삭제, main 자동 merge를 하지 않는다.
- raw HTML, credential, secret, 대용량 임시 text artifact를 commit하지 않는다.
- dry-run에서는 SEC request, R2/Drive write, panel/dashboard commit, next-year dispatch가 모두 0이어야 한다.
- panel 또는 dashboard 검증·publication이 실패하면 다음 연도를 dispatch하지 않는다.
- Cloudflare production은 사용자 승인 없이는 변경하지 않고 branch preview만 사용한다.

## 예상 소요 시간

새 Codespace에서 실제 구현을 시작할 때의 보수적 예상은 다음과 같다.

- 저장소·PR·schema 재감사: 20–40분
- orchestration 및 state machine 구현: 60–120분
- panel atomic update와 dashboard generator 연결: 60–120분
- fixture/mock·dry-run·workflow 검증: 45–90분
- 첫 실제 2019 run 전 preflight와 smoke 검증: 30–60분

따라서 실제 수집을 시작하기 전 코드·테스트·dry-run까지 약 3–6시간이 필요할 수 있다. 이는 구현 복잡도와 Actions 환경에 따른 추정이며, 연도별 SEC/R2 수집 시간은 별도 측정 전에는 확정하지 않는다.
