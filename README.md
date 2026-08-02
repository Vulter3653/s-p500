# S&P 500 10-K 언어 분석 프로젝트

이 저장소는 S&P 500 구성종목의 SEC Form 10-K를 firm-year 단위로 수집·추출·측정하고, 언어 분석 결과를 재현 가능하게 관리하는 프로젝트다.

## 현재 상태

- 완료된 분석 연도: 2020–2025
- 기존 firm-year 패널: 2,829행
- 기존 연도별 결과와 Google Drive raw HTML: 보존
- R2: 이전 삭제 검증 후 빈 상태이며, 역사 연도 신규 수집 시에만 사용
- 역사 확장 계획: 2019 → 2018 → 2017
- 역사 연도 처리: 503 securities 목표, 실제 SEC 적격 filing만 포함
- Free Tier 보호: 한 번에 한 연도, 기본 `max-parallel: 1`, checkpoint·resume, rate-limit 지연

역사 연도 작업은 기존 2020–2025 실행기를 전역 수정하지 않고 전용 runner/workflow로 분리한다. 현재 역사 연도 workflow는 아직 실행되지 않았다.

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

역사 확장은 다음 순서로 한 연도씩 진행한다.

```text
2019 → 2018 → 2017
```

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
