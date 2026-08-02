# Full Historical S&P 500 Constituent Reconstruction

Updated: 2026-08-02

## 목적

Wikipedia의 현재 구성기업 표와 SEC ticker 자료를 메타데이터 보조원으로 사용하고,
`fja05680/sp500`의 역사적 구성종목 CSV가 실제로 지원하는 가장 오래된 연구연도부터
가장 최근 연구연도까지 연도별 S&P 500 구성기업 표본을 재구성한다.

기존 `2020/`-`2025/` 산출물은 기본 실행에서 덮어쓰지 않는다. 이 기간을 다시 만들려면
`--overwrite-existing`을 명시해야 한다.

## 기준

연구연도 `t`의 표본은 `t+1-01-01` 이전 또는 당일의 역사적 구성종목 자료 중 가장
최근 행을 사용한다. 원천자료의 첫 유효 날짜 이전은 추정하거나 보간하지 않는다.
따라서 '가장 오래된 연도'는 코드에 고정하지 않고 매 실행 시 원천 CSV에서 자동 산정한다.

- 구성종목 여부: 역사적 구성종목 CSV
- 현재 기업명·산업·CIK 보조: Wikipedia 현재 표
- 현재 ticker-CIK 보조: SEC `company_tickers.json`
- 제한적 과거 ticker 보조: 저장소의 명시적 legacy map

과거 ticker가 현재 자료와 연결되지 않는 경우에도 구성종목 행은 삭제하지 않는다.
대신 `metadata_status=historical_membership_only`로 남기고 CIK와 산업분류를 결측으로 보존한다.
이는 현재 ticker를 과거 기업에 임의로 연결하는 오류를 방지하기 위한 조치다.

## 실행

```bash
python -m pip install 'pandas>=2.0,<3.0' 'lxml>=5.0,<7.0'
python scripts/build_full_historical_constituents.py --source-date 2026-08-02
```

특정 범위만 생성할 수 있다.

```bash
python scripts/build_full_historical_constituents.py \
  --source-date 2026-08-02 \
  --start-year 1990 \
  --end-year 2019
```

기존 연도 CSV를 의도적으로 재생성하는 경우에만 다음 옵션을 사용한다.

```bash
python scripts/build_full_historical_constituents.py \
  --source-date 2026-08-02 \
  --overwrite-existing
```

GitHub Actions의 `Build full historical S&P 500 constituents` workflow도 동일한 작업을
수동 실행하며 결과 전체를 30일 보존 artifact로 업로드한다. workflow는 저장소에 직접
commit하거나 기존 자료를 삭제하지 않는다.

## 산출물

각 생성 연도에 다음 파일을 만든다.

```text
YYYY/sp500_securities.csv
YYYY/sp500_companies.csv
```

전체 실행 감사정보는 다음 manifest에 기록한다.

```text
data/processed/full_historical_constituents_manifest.json
```

manifest에는 원천 SHA-256, 원천이 지원하는 최초·최종 연도, 기존 자료로 인해 건너뛴 연도,
각 연도의 실제 사용 역사 자료일, 행 수, CIK 결측 수와 출력 경로가 포함된다.

## 해석상 제한

1. 역사적 구성종목 CSV가 제공하지 않는 날짜 이전은 복원하지 않는다.
2. Wikipedia의 `Selected changes`는 완전한 장기 변경 이력이 아니므로 과거 membership의
   source of truth로 사용하지 않는다.
3. 현재 SEC ticker snapshot은 상장폐지·합병·ticker 변경 기업을 완전하게 포함하지 않는다.
4. 오래된 연도의 CIK·기업명·GICS 결측은 membership 오류가 아니라 metadata 미확정 상태일 수 있다.
5. 10-K 수집 전에는 각 과거 ticker를 SEC submissions와 accession 자료로 별도 검증해야 한다.
