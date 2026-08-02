# S&P 500 10-K 언어 분석 프로젝트 인수인계

## 현재 저장소 상태

- branch: `main`
- 현재 VERSION: `0.12.0`
- 기준 연도 결과: 2020–2025
- 기존 firm-year 패널: 2,829행
- 현재 HEAD와 `origin/main`: `65d35c4b03ecc2ba3240698cc542fe21c54d84cb`
- working tree: clean

## 완료된 분석

| 연도 | 적격 firm-year |
| ---: | ---: |
| 2020 | 445 |
| 2021 | 461 |
| 2022 | 471 |
| 2023 | 479 |
| 2024 | 487 |
| 2025 | 484 |

기존 연도별 manifest, extraction 결과, language 결과, 패널 및 Google Drive raw HTML은 읽기 전용으로 보존한다.

## 저장소 상태

- Google Drive 신규 기본 형식: `연도/번호_연도_기업명_SYMBOL_CIK.html`
- R2: 이전 완료 객체 삭제 후 API 목록 기준 빈 상태
- historical 구성종목 PR #2: 검토 상태이며 실제 workflow 실행 전
- VERSION: 기존 버전 `0.12.0` 유지

## 다음 작업 계획

역사 확장은 다음 순서로 한 연도씩 진행한다.

```text
2019 → 2018 → 2017
```

목표는 historical S&P 500 503 securities지만 실제 SEC 적격 Form `10-K`가 유일하게 확정되는 행만 포함한다. 503개는 `100·100·100·100·100·3`의 6개 batch로 분할한다.

각 연도 처리 순서:

1. historical membership 기반 manifest 생성
2. SEC `reportDate`와 Form `10-K` 검증
3. R2 raw HTML 수집·SHA·크기 검증
4. 본문 추출과 기존 언어 pipeline 실행
5. 연도별 결과와 품질검사 생성
6. Google Drive 이전 및 size·SHA 검증
7. checkpoint와 artifact 확인 후 다음 연도 시작

Free Tier 보호를 위해 여러 연도와 batch를 동시에 실행하지 않고, `max-parallel: 1`, `concurrency`, rate-limit 지연, checkpoint·resume을 사용한다.

## 확인된 구현 주의사항

기존 `process-10k-yearly-batches.yml`, `run_yearly_10k_batch.py`, 추출기와 language runner는 2025 pilot 경로 및 1–5 batch를 전제로 한다. 기존 2020–2025 결과를 보호하기 위해 historical 처리는 전용 runner/workflow로 분리해야 한다. 기존 실행기를 전역 수정하거나 기존 결과를 재처리하지 않는다.

## 금지 사항

- 기존 2020–2025 결과 재측정·재추출 금지
- 기존 Google Drive 파일과 R2 manifest 삭제·overwrite 금지
- raw HTML의 Git 추가 금지
- secret·token·endpoint·bucket 이름 기록 금지
- VERSION 임의 변경 금지
- 전체 테스트 68개 실행 금지

세부 계획과 감사 결과는 `docs/historical-reconstruction-2019-2017-plan.md`, 진행 기록은 `docs/progress.md`, 오류 기록은 `docs/debug-log.md`를 기준으로 한다.
