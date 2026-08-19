# S&P 500 10-K 언어 분석 프로젝트

이 저장소는 S&P 500 구성종목의 SEC Form 10-K를 기업-연도 단위로 수집·추출·측정하고, 언어 분석 결과를 재현 가능하게 관리하는 프로젝트다. 현재 연구의 상세한 확정·보류·예정 상태는 [`docs/research-blueprint.md`](docs/research-blueprint.md)를 기준으로 한다.

## 현재 상태

- 완료된 핵심 분석 연도: 2020–2025
- 기존 핵심 패널: 2,829개 기업-연도, 545개 고유 기업
- AI 관련 공시: 1,660개, AI 관련 문장: 19,577개
- historical candidate panel: 2006–2025, 4,897개 기업-연도, 584개 고유 기업
- historical backfill: 2019년부터 2006년까지 완료, chain status `completed`, validation `PASS`
- 기존 연도별 결과와 Google Drive raw HTML: 보존
- R2: 2020–2025 객체는 이전 후 삭제 검증을 완료했으나, 이후 historical 2,068개 객체는 Drive 이전 시 삭제하지 않았다. 현재 live 잔존 상태는 이 문서 갱신에서 재확인하지 않았다.
- historical candidate 상태와 연도별 검증 결과는 `automation/historical_backfill/` 및 `analysis/historical_candidate/`에 기록한다.
- 기존 2020–2025 패널·분석 결과는 보호하고 historical candidate를 별도 경로로 관리한다.

Historical candidate panel은 매년 완전한 S&P 500 전체 패널이 아니라 원천과 적격 filing이 확인된 관측치의 후보 패널이다.

## 현재 연구 우선순위

- RQ1 Tense: 보류. 기존 결과는 `spaCy 기반 임시 tense 분석`으로만 보존한다.
- RQ2 Concreteness: 현재 우선 진행. 핵심 관계는 `10-K Concreteness → Shareholder Reaction`이다.
- WRDS·Compustat·CRSP 결합과 CAR·BHAR 분석은 예정 상태이며 아직 실행하지 않았다.

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
3. Brysbaert 기반 10-K concreteness와 주주 반응의 관계를 우선 연구한다.
4. 향후 Compustat controls와 CRSP returns를 CIK–GVKEY–PERMNO 연결로 결합한다.

분석 단위는 기업-보고연도이며, `10-K/A`, `NT 10-K`, `8-K`, PDF annual report는 적격 filing에서 제외한다.

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
├── 2019/, 2020/ ... 2025/          # 현재 루트에 존재하는 연도별 자료
├── panel_2020_2025/                 # 기존 2020–2025 firm-year 패널
├── panel_historical_candidate/      # 2006–2025 historical candidate panel
├── analysis/descriptive_2020_2025/  # 기존 기술통계·상관분석 산출물
├── analysis/historical_candidate/   # historical candidate 분석 산출물
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

## Historical backfill 상태

Historical backfill은 source-supported 범위에서 다음 순서로 완료되었다.

```text
2019 → 2018 → … → 2006
```

각 연도 완료 여부와 누적 candidate panel의 상태는 `automation/historical_backfill/chain-state.json` 및 연도별 상태 파일에서 확인한다.

최종 chain status는 `completed`, candidate rows는 4,897, validation은 `PASS`다. 과거 연도로 갈수록 확인 가능한 관측치가 감소하므로 완전한 역사 패널로 해석하지 않는다.

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

현재 버전은 `VERSION`에서 확인한다. 현재 `VERSION`은 `0.14.0`이다.

현재 연구 청사진은 `docs/research-blueprint.md`, 인수인계 상태는 `docs/current_project_handover.md`, historical chain 검증은 `automation/historical_backfill/chain-state.json`을 기준으로 한다.
