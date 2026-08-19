# Agent Operating Guide

Updated: 2026-08-19

이 저장소에서 작업하는 모든 AI 에이전트와 기여자는 파일을 수정하기 전에 이 문서를 따라야 한다.

## 작업 시작 절차

먼저 다음 명령으로 현재 상태와 최근 이력을 확인한다.

```bash
git status --short --branch
git log --oneline -8
```

그다음 다음 문서를 순서대로 읽는다.

```text
docs/research-blueprint.md
docs/writing-rules.md
docs/progress.md
CHANGELOG.md
docs/debug-log.md
```

과거 대화나 모델의 기억보다 저장소 문서를 우선하고, 저장소에 기록된 문서를 현재 상태의 기준으로 사용한다. 연구 관련 작업에서는 `docs/research-blueprint.md`를 먼저 확인하고 현재 연구질문, 변수 상태 및 확정·보류·예정 사항의 기준으로 삼는다. 이 문서에서 `보류`, `임시`, `미확정`, `예정`으로 표시된 사항은 사용자의 새로운 명시적 지시 없이 `확정`으로 바꾸거나 연구 방향을 변경하지 않는다.

## Reuse-before-create policy

새 코드를 만들기 전에 반드시 기존 구현을 먼저 찾는다. 이 정책은 Python script, module, helper, function, class, workflow, GitHub Actions YAML, test, data generator, parser, runner, migration·validation·analysis script, web utility, configuration file 및 같은 기능을 수행할 수 있는 모든 실행 코드에 적용한다.

새 코드 파일을 만들기 전에는 다음 targeted search 절차를 따른다.

1. 작업 목적을 2~5개의 핵심 검색어로 정의한다.
2. `rg`, `grep`, `find` 또는 Git search로 관련 기능을 직접 검색한다.
3. 파일명뿐 아니라 함수명, CLI argument, output path 및 workflow job 이름도 검색한다.
4. 검색 결과에서 관련성이 높은 기존 구현 1~5개를 먼저 읽는다.
5. 필요할 때만 `git log`, `docs/progress.md`, `CHANGELOG.md`, `docs/debug-log.md`에서 구현 및 실패 이력을 확인하고 검색 범위를 확대한다.
6. 동일하거나 유사한 구현이 있으면 새 파일을 만들지 않고 기존 구현을 그대로 재사용하거나 최소 수정한다.

예를 들어 historical runner는 기존 `run_yearly_10k_batch.py`, `continuous_backfill.py` 및 호출 workflow를 먼저 찾고, web data generator는 기존 `generate_web_analysis_data.py`를 먼저 확장하며, validator는 `tests/`, `scripts/`, workflow의 기존 검증을 먼저 재사용한다.

구현 선택 순서는 다음과 같다.

```text
REUSE → EXTEND → REFACTOR → CREATE NEW
```

1순위는 그대로 재사용, 2순위는 기존 함수·스크립트의 최소 수정, 3순위는 기존 공통 기능을 이용한 작은 확장 또는 필요한 refactor이며, 새 파일 생성은 마지막 선택지다.

다음과 같은 duplicate implementation은 금지한다.

- 동일 목적의 script를 이름만 바꾸어 생성하거나 기존 runner 옆에 별도 runner 추가
- 동일 계산식을 여러 파일에 복사하거나 재사용 가능한 helper 대신 새 helper 작성
- 같은 산출물을 만드는 병렬 generator 또는 같은 목적의 workflow YAML 추가
- 기존 test를 확장할 수 있는데 중복 test 파일 생성
- 임시 문제 해결 script를 저장소에 남기거나 canonical implementation을 우회하는 병렬 구현 생성
- 기존 parser·analysis script를 고치지 않고 `parser_v2.py`, `analysis_new.py` 같은 우회 구현을 먼저 생성

기존 코드가 일부 기능만 제공하면 전체를 다시 작성하지 않고 부족한 부분만 확장한다. 기존 workflow는 parameter 또는 condition을 확장하고, 기존 parser의 오류는 해당 parser를 진단·수정하며, 기존 분석 구조에는 필요한 변수나 output만 추가한다.

새 코드 파일은 기존 구현이 실제로 없거나, 기존 구현에 추가하면 책임 분리가 명백히 깨지거나 기존 결과를 위험하게 변경하는 경우, 사용자 요구상 독립 모듈이 필수인 경우, 또는 test·workflow 격리가 기술적으로 필요한 경우에만 허용한다. 새 파일을 만들면 완료 보고 또는 `docs/progress.md`에 검토한 기존 구현과 재사용할 수 없었던 이유를 한 줄로 기록한다. 편의, 미관 또는 단기 작성 속도는 신규 생성 사유가 아니다.

동일 기능이 여러 곳에 있으면 현재 production 또는 pipeline이 호출하는 canonical implementation을 우선한다. Canonical 여부가 불명확하면 실제 workflow 호출, README, `docs/progress.md`, `CHANGELOG.md`, 최근 Git history 순으로 빠르게 확인한다. 기존 결과를 위험하게 바꿀 수 있으면 임의로 통합하지 말고 상태를 보고한다.

동일 문제를 다시 다룰 때는 `docs/debug-log.md`를 먼저 검색한다. 실패했던 접근은 현재 조건이 달라졌을 때만 재시도하고 무엇이 달라졌는지 기록한다. 이유 없이 동일 실패 접근을 반복하지 않는다.

새 코드 파일을 만들기 직전에 다음 세 질문을 확인한다.

1. 같은 기능이 이미 존재하는가?
2. 기존 기능을 확장하면 해결되는가?
3. 정말 새 파일이 필요한가?

1번 또는 2번이 `Yes`이면 새 파일을 만들지 않는다.

검색 자체도 시간 효율적으로 수행한다. 단순한 수정마다 저장소 전체를 전수조사하거나 관련성이 낮은 파일까지 모두 읽지 않고, targeted search 결과의 관련 파일부터 확인한다. 기존 산출물이 유효하면 재생성하지 않고, 입력이 바뀌지 않은 기존 계산을 반복하지 않으며, 검증된 다운로드와 기존 raw data를 다시 수집하지 않는다. 문서만 변경하면 전체 분석·test·build를 실행하지 않고 변경 범위에 필요한 최소 검증만 수행한다. 입력이나 코드가 바뀌지 않은 고비용 PASS 작업도 반복하지 않는다. 다만 실제 데이터 정합성 또는 안전 검증이 필요하면 시간 절약을 이유로 생략하지 않는다.

## 브랜치와 버전 관리

- 개인 저장소의 기준 브랜치는 `origin/main`이다.
- 작업 전 원격 상태를 확인하고, 이미 존재하는 사용자 변경을 보존한다.
- 의미 있는 변경은 하나의 명확한 목적을 가진 커밋으로 기록한다.
- 커밋 메시지는 변경 내용을 구체적으로 설명한다.
- 실험적이거나 위험한 변경은 별도 브랜치에서 수행한다.
- 사용자의 명시적 지시 없이 기존 커밋을 강제로 덮어쓰거나 기록을 재작성하지 않는다.
- 버전은 `VERSION` 파일과 `CHANGELOG.md`에서 함께 관리한다.
- 버전 규칙은 Semantic Versioning의 `MAJOR.MINOR.PATCH` 형식을 따른다.

## Default Git completion policy

사용자가 해당 작업에서 명시적으로 금지하지 않는 한, Codex는 정상 완료한 작업을 다음 순서로 마무리한다.

1. 변경 범위에 필요한 검증을 수행한다.
2. 검증이 통과하면 이번 작업에서 변경한 파일만 stage한다.
3. 작업 내용을 설명하는 하나의 명확한 commit을 생성한다.
4. 현재 작업 브랜치를 동일한 이름의 `origin` 브랜치로 push한다.
5. 완료 보고에 commit SHA와 push 대상 브랜치를 기록한다.

다음 동작은 자동으로 수행하지 않는다.

- `main` 또는 `master` 브랜치에 직접 commit하거나 push
- force push, `--force-with-lease`, history rewrite, 기존 사용자 작업을 삭제하는 reset, 공유 브랜치 history를 변경하는 rebase
- PR 생성 또는 merge, production deploy, release 또는 tag 생성
- 사용자 소유의 unrelated 변경 stage, secret·token·credential commit
- 검증 실패 상태에서 commit 또는 push

현재 브랜치가 `main` 또는 `master`이면 자동 commit·push를 중단하고 별도 작업 브랜치가 필요함을 보고한다. Working tree에 unrelated 사용자 변경이 있으면 해당 파일을 stage하지 않으며, 작업 범위가 불명확하면 commit·push 전에 중단하고 보고한다. Push가 인증, branch protection 또는 remote rejection으로 실패하면 local commit을 보존하고 실패 이유와 commit SHA를 보고하며 강제 push나 우회 동작을 하지 않는다.

사용자가 `commit하지 마라`, `push하지 마라`, `로컬에만 둬라`, `검토만 해라` 또는 이에 준하는 제한을 명시하면 그 지시가 이 기본 정책보다 우선한다.

## 필수 기록

모든 의미 있는 변경은 다음 파일에 기록한다.

```text
CHANGELOG.md
```

작업 결과가 다음 작업자의 인수인계, 현재 상태 또는 후속 작업에 영향을 주면 다음 파일도 갱신한다.

```text
docs/progress.md
```

오류 조사, 원인 분석, 수정, 테스트 실패, 재현 절차 또는 검증 결과가 있으면 다음 파일도 갱신한다.

```text
docs/debug-log.md
```

## 기록 보존

- 기존 변경 이력, 진행 기록 및 디버그 기록을 삭제하거나 요약하여 덮어쓰지 않는다.
- 새로운 기록은 해당 문서의 최신 항목 위쪽에 역시간순으로 추가한다.
- 다른 기여자의 설명과 귀속 표시를 임의로 수정하지 않는다.
- 로그 파일을 수정한 뒤 기존 내용이 예상치 않게 줄어들지 않았는지 확인한다.

## 작성자 귀속

AI 에이전트가 작성한 의미 있는 기록은 다음 소문자 표기를 사용한다.

```text
(codex)
(gemini)
(claude)
```

기본 형식은 다음과 같다.

```text
- Changed: 변경 내용을 구체적으로 설명한다. (codex)
```

## 작업 범위와 안전

- 사용자가 요청한 범위의 파일만 수정한다.
- 데이터 원본은 명시적 요청 없이 삭제, 덮어쓰기 또는 재분류하지 않는다.
- 비밀 키, 토큰, 개인정보 및 실제 자격 증명을 커밋하지 않는다.
- 사용자 변경과 무관한 파일은 정리하거나 되돌리지 않는다.
- 파괴적 명령과 강제 푸시는 사용자가 정확한 대상을 명시적으로 승인한 경우에만 수행한다.

## 검증

변경 유형에 적합한 검증을 실행한다.

최소 공통 검증:

```bash
git diff --check
git status --short
```

코드, 데이터 또는 분석 파이프라인을 추가하면 해당 테스트와 재현 명령을 `README.md` 또는 관련 문서에 명시하고, 실행 결과를 `docs/progress.md`에 기록한다. 오류 조사와 해결 과정은 `docs/debug-log.md`에 기록한다.

## 작업 완료 보고

작업 완료 시 다음 사항을 명확히 보고한다.

- 변경한 파일
- 실행한 검증 명령과 결과
- 현재 버전
- 커밋 해시
- 푸시한 원격 저장소와 브랜치
- 남아 있는 위험, 미실행 테스트 또는 후속 작업
