# S&P 500 Annual Sample Definition

Updated: 2026-07-20

## 확정 원칙

연구연도 `t`의 S&P 500 표본은 다음 해 1월 1일 현재 S&P 500 구성기업으로 정의한다.

```text
sample_year = t
snapshot_date = (t + 1)-01-01
```

따라서 2025년 S&P 500 표본의 확정 기준일은 2026년 1월 1일이다.

## 연구연도와 기준일

| sample_year | snapshot_date |
| ---: | --- |
| 2020 | 2021-01-01 |
| 2021 | 2022-01-01 |
| 2022 | 2023-01-01 |
| 2023 | 2024-01-01 |
| 2024 | 2025-01-01 |
| 2025 | 2026-01-01 |

## 변경 이력 적용 규칙

Wikipedia의 `Selected changes to the list of S&P 500 components` 표에 기록된 `Effective Date`를 기준으로 구성기업 변경을 적용한다.

- `Effective Date <= snapshot_date`: 해당 변경을 연구연도 표본에 반영한다.
- `Effective Date > snapshot_date`: 해당 변경을 연구연도 표본에 반영하지 않는다.
- 현재 구성기업 목록에서 과거 표본을 복원할 때는 변경 이력을 최신순에서 과거순으로 역적용한다.
- 역적용 시 편입 기업은 제거하고 제외 기업은 복원한다.
- ticker 또는 기업명만 변경된 사건은 기업의 편입·제외가 아니라 동일 기업의 식별자 변경으로 관리한다.
- 합병, 분할 및 주식 종류 변경은 CIK와 변경 사유를 함께 확인한다.

## 기업 단위 처리

S&P 500은 복수 주식 종류로 인해 500개 기업보다 많은 종목을 포함할 수 있다. 10-K 수집의 기본 단위는 종목이 아니라 SEC CIK 기반 기업이다.

- 동일 CIK의 복수 ticker는 하나의 기업으로 통합한다.
- ticker는 시점별 보조 식별자로 보존한다.
- 동일 기업의 복수 주식 종류로 인해 같은 10-K를 중복 수집하지 않는다.

## 자료 출처와 검증

- 1차 표본 구축 기준: Wikipedia의 현재 S&P 500 구성기업 표와 Selected changes 표
- 구성기업 변경 기준 필드: `Effective Date`, `Added`, `Removed`, `Reason`
- 기업 식별 검증: SEC CIK 및 SEC EDGAR 제출자료
- 주요 변경 사건 검증: 표에 연결된 S&P Dow Jones Indices 발표자료

Wikipedia 페이지는 계속 변경되므로 실제 표본 생성 시 원본 수집일, 원본 파일 또는 스냅숏, 파싱 코드 및 변경 이력 원자료를 함께 보존한다.

