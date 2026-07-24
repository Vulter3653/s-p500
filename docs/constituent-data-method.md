# Annual Constituent Data Method

Updated: 2026-07-24

## 산출물

각 연구연도 폴더에는 두 종류의 목록을 둔다.

- `sp500_companies.csv`: SEC CIK와 동일 기업명 기준으로 복수 주식 종류를 통합한 500개 기업 목록
- `sp500_securities.csv`: 복수 주식 종류를 유지한 종목 단위 감사 목록

연도별 기준일은 `docs/sample-definition.md`에서 확정한 대로 연구연도 다음 해 1월 1일이다.

## 생성 방법

`scripts/build_annual_constituents.py`는 다음 순서로 자료를 생성한다.

1. 영어 Wikipedia의 현재 구성기업 표와 `Selected changes` 표를 HTML 스냅숏으로 저장한다.
2. 현재 구성종목에서 각 기준일 이후 변경을 역적용한다.
3. Wikipedia 변경 표가 전체 변경 이력이 아니라는 한계를 보완하기 위해 `fja05680/sp500`의 일자별 역사 구성종목으로 기준일별 ticker 집합을 검증한다.
4. 현재 SEC `company_tickers.json`과 확인된 과거 ticker-CIK 연결로 식별자를 보완한다.
5. 동일 CIK의 복수 주식 종류를 기업 단위로 통합한다. CIK가 없는 복수 종목은 동일 기업명이 명확히 일치할 때만 통합한다.
6. 원본 해시, 행 수, CIK 결측 수 및 검증 과정의 추가·제거 ticker를 manifest에 기록한다.

## 재현 명령

```bash
python -m pip install -r requirements.txt
python scripts/build_annual_constituents.py --source-date 2026-07-24
python scripts/validate_annual_constituents.py
```

## 알려진 제한

- Wikipedia의 변경 표는 `Selected changes`이므로 그 표만으로는 일부 과거 시점의 정확한 구성종목 수를 복원할 수 없다.
- 과거 편출 후 인수·상장폐지된 일부 기업은 현재 SEC ticker 파일에 존재하지 않아 CIK 또는 산업분류가 결측일 수 있다.
- `metadata_status`는 각 행의 메타데이터가 현재 표, SEC ticker 파일 또는 역사 구성종목 검증 중 어디에서 확보됐는지 나타낸다.
- 구성종목 여부는 완성했지만, 결측 CIK와 과거 시점 GICS는 10-K 수집 전에 SEC 제출자료 및 공식 변경 발표로 추가 검증해야 한다.
