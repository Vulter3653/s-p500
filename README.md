# S&P 500 10-K 언어 분석 프로젝트

이 저장소는 S&P 500 구성종목의 SEC Form 10-K를 firm-year 단위로 수집·추출·측정하고, 언어 분석 결과를 재현 가능하게 관리하는 프로젝트다.

## 현재 상태

- 완료된 분석 연도: 2020–2025
- 기존 firm-year 패널: 2,829행
- 기존 연도별 결과와 Google Drive raw HTML: 보존
- R2: 이전 삭제 검증 후 빈 상태이며, 역사 연도 신규 수집 시에만 사용
- 역사 확장: source-supported 범위에서 최신 연도부터 과거 연도 방향으로 순차 처리한다.
- 역사 연도 처리: firm-level manifest 상한 503개, batch당 최대 100개, 실제 SEC 적격 filing만 포함한다.
- historical candidate 상태와 연도별 검증 결과는 `automation/historical_backfill/` 및 `analysis/historical_candidate/`에 기록한다.
- 기존 2020–2025 패널·분석 결과는 보호하고 historical candidate를 별도 경로로 관리한다.
- Free Tier 보호: 한 번에 한 연도, 기본 `max-parallel: 1`, checkpoint·resume, rate-limit 지연.

## 2020–2025 구성종목 외부 원천 감사

현재 수집된 2020–2025 구성종목 CSV를 다음 독립 원천과 비교한 감사 결과를 문서화했다.

- [datasets/s-and-p-500-companies](https://github.com/datasets/s-and-p-500-companies)
- [hanshof/sp500_constituents](https://github.com/hanshof/sp500_constituents)
- 상세 감사: [`docs/constituent-source-comparison-2020-2025.md`](docs/constituent-source-comparison-2020-2025.md)

내부 CSV는 2020–2025 각 500행이며 snapshot date는 2021-01-01부터 2026-01-01이다. 2025 CSV와 datasets 현재 snapshot의 CIK 비교는 488개 교집합, 프로젝트 전용 9개, 외부 전용 11개였다. 외부 datasets 파일은 현재 구성 기준이며 2026년 유효일이 포함되므로 historical 연도의 정답으로 대체하지 않는다. hanshof historical 원본은 대용량 응답 제한으로 이번 감사에서 전체 행 대조를 완료하지 못했으며, 이를 문서에 미확인 상태로 기록했다.

이 감사에서 기존 패널·분석표·Figure·원본 HTML·R2·Google Drive는 수정하지 않았다.

## 연구 목적과 범위

1. 연도별 S&P 500 구성종목과 SEC CIK를 재현 가능한 기준으로 구축한다.
2. 정확한 `reportDate` 기준의 Form `10-K` filing metadata와 primary HTML을 연결한다.
3. 원문 추출, AI disclosure, Loughran–McDonald, Brysbaert concreteness 및 텍스트 통제변수를 측정한다.
4. 기존 결과를 변경하지 않고 연도별 결과와 통합 패널을 생성한다.

분석 단위는 기업-보고연도 `firm-year`이며, `10-K/A`, `NT 10-K`, `8-K`, PDF annual report는 적격 filing에서 제외한다.

## 연도별 기준일

연도 `t`의 구성종목은 다음 해 1월 1일 기준으로 확정한다.

| 연구연도 | 기준일 |
| ---: | --- |
| 2017 | 2018-01-01 |
| 2018 | 2019-01-01 |
| 2019 | 2020-01-01 |
| 2020 | 2021-01-01 |
| 2021 | 2022-01-01 |
| 2022 | 2023-01-01 |
| 2023 | 2024-01-01 |
| 2024 | 2025-01-01 |
| 2025 | 2026-01-01 |

역사 구성종목 원천자료가 제공하지 않는 기간은 추정하거나 보간하지 않는다.

## 저장소 구조

```text
s-p500/
├── 2017/ ... 2025/                 # 연도별 구성종목·manifest·결과
├── panel_2020_2025/                 # 기존 2020–2025 firm-year 패널
├── analysis/descriptive_2020_2025/  # 기존 기술통계·상관분석 산출물
├── data/raw/                        # 원천자료 snapshot
├── data/processed/                  # 구성종목 manifest
├── docs/                            # 방법·진행·디버그·역사 확장 계획
├── scripts/                         # 표본·수집·추출·측정·저장 실행기
├── .github/workflows/               # 수동·checkpoint 기반 workflow
├── AGENTS.md
├── CHANGELOG.md
├── VERSION
└── requirements.txt
```

## 역사 연도 처리 순서

역사 확장은 고정된 2017년에서 중단하지 않고 source-supported 범위에서 한 연도씩 역순으로 진행한다.

```text
2019 → 2018 → 2017 → 2016 → 2015 → …
```

각 연도 완료 여부와 누적 candidate panel의 상태는 `automation/historical_backfill/chain-state.json` 및 연도별 상태 파일에서 확인한다.

503 securities는 다음 6개 batch로 나눈다.

```text
100 · 100 · 100 · 100 · 100 · 3
```

각 연도는 manifest 생성 → SEC metadata 확정 → R2 수집·검증 → 추출·언어 측정 → Google Drive 이전·검증 순서로 처리한다. 다음 연도는 이전 연도의 품질검사가 끝난 뒤에만 시작한다.

## Google Drive 저장 형식

신규 이전의 기본 형식은 다음과 같다.

```text
연도/번호_연도_기업명_SYMBOL_CIK.html
```

기존 Drive 파일과 기존 패널·언어 결과는 읽기 전용으로 보존한다. R2 객체는 Drive 이전과 검증이 끝나기 전까지 삭제하지 않는다.

## 재현과 운영

작업 전 다음 문서를 순서대로 확인한다.

1. `AGENTS.md`
2. `docs/writing-rules.md`
3. `docs/progress.md`
4. `CHANGELOG.md`
5. `docs/debug-log.md`

현재 버전은 `VERSION`에서 확인한다. 현재 `VERSION`은 `0.12.0`이며, 역사 확장 실행기와 workflow가 실제로 추가·검증되기 전에는 임의로 변경하지 않는다.

역사 확장 계획과 기존 실행기의 규칙 감사 결과는 `docs/historical-reconstruction-2019-2017-plan.md`에 기록되어 있다.
