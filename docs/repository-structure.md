# Repository Structure and File Guide

Updated: 2026-07-24

이 문서는 `main` 브랜치의 디렉터리 구조, 각 파일의 역할, 수정 원칙 및
파일 간 생성 관계를 설명한다. 실제 파일을 추가·이동·삭제할 때는 이 문서와
루트 `README.md`의 트리를 함께 갱신한다.

## 주석형 트리

```text
s-p500/
├── 2020/ ... 2025/                    # 연구연도별 최종 표본 저장 영역
│   ├── README.md                      # 연도별 기준일과 파일 안내
│   ├── sp500_companies.csv            # 기업 단위 분석·10-K 수집의 기준 목록
│   └── sp500_securities.csv           # 주식 종류를 보존한 추적·감사용 목록
├── data/
│   ├── raw/                           # 수집 당시 상태를 보존하는 읽기 전용 원천자료
│   │   ├── wikipedia_sp500_2026-07-24.html
│   │   │                                  # Wikipedia 현재 표와 변경 이력 HTML
│   │   ├── sp500_historical_components_2026-07-24.csv
│   │   │                                  # 기준일별 ticker 집합 교차검증 자료
│   │   └── sec_company_tickers_2026-07-24.json
│   │                                      # SEC ticker-CIK 매핑 스냅숏
│   └── processed/
│       └── annual_constituents_manifest.json
│                                          # 원본 URL·해시·생성법·연도별 품질 요약
├── docs/
│   ├── repository-structure.md            # 현재 문서: 구조 및 파일 역할
│   ├── sample-definition.md               # 연구연도와 S&P 500 기준일 정의
│   ├── constituent-data-method.md         # 연도별 목록 생성·보정 방법
│   ├── writing-rules.md                   # 문서·데이터·분석 기록 규칙
│   ├── progress.md                        # 최신 진행 상태와 인수인계
│   └── debug-log.md                       # 오류·원인·조치·검증 기록
├── scripts/
│   ├── build_annual_constituents.py       # raw 자료를 읽어 연도별 CSV와 manifest 생성
│   └── validate_annual_constituents.py    # 산출물 구조와 무결성을 읽기 전용 검증
├── AGENTS.md                              # 작업 시작·버전·기록·검증 의무
├── CHANGELOG.md                           # 최신 버전부터 역순으로 쌓는 변경 이력
├── VERSION                                # 현재 버전 한 줄
├── requirements.txt                       # pandas와 lxml 버전 범위
├── README.md                              # 프로젝트 목적·기준·구조·재현 진입점
└── .gitignore                             # Python cache 등 비산출물 제외
```

## 연도별 CSV 역할

### `sp500_companies.csv`

- 목적: 기업-연도 분석과 SEC 10-K 수집에 사용하는 기본 표본이다.
- 행 단위: 연구연도별 하나의 기업이다.
- 통합 기준: CIK가 있으면 CIK, 없으면 명확히 일치하는 기업명을 사용한다.
- 핵심 키: `_company_key`.
- 주의: 결측 CIK는 10-K 수집 전에 보완해야 하며 ticker만으로 기업을
  장기간 연결하지 않는다.

### `sp500_securities.csv`

- 목적: 동일 기업의 복수 주식 종류와 당시 ticker를 보존하는 감사표다.
- 행 단위: 연구연도별 하나의 상장 종목이다.
- 핵심 키: `sample_year`과 `symbol`의 조합.
- 주의: 이 파일의 행 수는 기업 수와 같지 않을 수 있으며 직접적인 기업 수
  집계에는 사용하지 않는다.

두 CSV의 열은 다음 의미를 공유한다.

| 열 | 의미 |
| --- | --- |
| `sample_year` | 연구에 배정된 연도 |
| `snapshot_date` | 구성기업 확정 기준일 |
| `symbol` | 해당 표본에서 사용하는 ticker |
| `security` | 기업 또는 종목 명칭 |
| `gics_sector` | GICS 섹터 |
| `gics_sub_industry` | GICS 하위 산업 |
| `headquarters` | 본사 소재지 |
| `date_added` | 확보 가능한 S&P 500 편입일 |
| `cik` | 10자리 zero-padded SEC CIK |
| `founded` | 설립연도 또는 설립 정보 |
| `metadata_status` | 메타데이터 확보·보완 상태 |
| `source_url` | 행 메타데이터의 출처 URL |

`sp500_companies.csv`에만 있는 `_company_key`는 `cik:<10자리 CIK>` 또는
CIK 결측 시 정규화된 기업명 기반 키로 기업을 통합하기 위한 내부 식별자다.

## 생성 및 검증 관계

```text
data/raw/*
    -> scripts/build_annual_constituents.py
    -> 2020-2025/*.csv + data/processed/annual_constituents_manifest.json
    -> scripts/validate_annual_constituents.py
```

- `data/raw/` 파일은 새 수집일 스냅숏을 추가하는 방식으로 보존하며 기존
  스냅숏을 조용히 덮어쓰지 않는다.
- 연도별 CSV와 manifest는 생성 스크립트의 산출물이므로 수동 수정 대신
  생성 로직 또는 식별자 보완 자료를 수정한 뒤 재생성한다.
- `validate_annual_constituents.py`는 산출물을 변경하지 않는다.
- 아직 10-K 원문, filing metadata, 본문 추출물 및 분석 결과 폴더는 없다.
  해당 구조는 수집 기준을 확정한 뒤 별도 버전에서 추가한다.
