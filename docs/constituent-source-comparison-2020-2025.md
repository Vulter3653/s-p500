# 2020–2025 S&P 500 구성종목 외부 원천 비교 감사

- 감사 기준일(UTC): 2026-08-06
- 대상 저장소: `Vulter3653/s-p500`
- 대상 범위: 연구연도 2020–2025의 현재 수집 CSV와 collection-ready sample manifest
- 비교 외부 원천:
  1. [datasets/s-and-p-500-companies](https://github.com/datasets/s-and-p-500-companies)
  2. [hanshof/sp500_constituents](https://github.com/hanshof/sp500_constituents)
- 판정 원칙: 외부 저장소의 현재 스냅샷은 과거 연도 구성종목의 정답으로 대체하지 않는다. 프로젝트의 연도별 snapshot과 historical reconstruction을 주 원천으로 유지하고, 외부 저장소는 독립적인 교차검증 참고원으로만 사용한다.

## 1. 감사 질문과 비교 단위

이번 감사는 다음을 확인한다.

1. 프로젝트의 2020–2025 CSV가 연도별 500개 행을 갖는가.
2. CSV의 스냅샷 날짜와 연구연도의 관계가 문서화되어 있는가.
3. CIK·ticker·기업 식별자가 중복 없이 collection-ready manifest로 정제되었는가.
4. 외부 현재 목록과 비교할 때 차이가 실제 오류인지, 시점·share class·기업 식별 규칙 차이인지 구분되는가.
5. 외부 historical 파일을 과거 연도 정답으로 오용하지 않는가.

주 식별자는 CIK를 사용한다. CIK가 없는 경우에만 정규화한 ticker를 보조적으로 사용한다. 단순 ticker 문자열 일치만으로 동일 기업을 판정하지 않는다.

## 2. 프로젝트 내부 원천

### 2.1 연도별 구성종목 CSV

경로는 다음과 같다.

```text
2020/sp500_companies.csv
2021/sp500_companies.csv
2022/sp500_companies.csv
2023/sp500_companies.csv
2024/sp500_companies.csv
2025/sp500_companies.csv
```

공통 열:

```text
_company_key, sample_year, snapshot_date, symbol, security,
gics_sector, gics_sub_industry, headquarters, date_added, cik,
founded, metadata_status
```

검사 결과:

| 연구연도 | CSV 행 수 | snapshot_date | CIK 중복 초과 행 | 판정 |
|---:|---:|---|---:|---|
| 2020 | 500 | 2021-01-01 | 40 | 행 수 PASS; share class/기업 집계 규칙 별도 확인 |
| 2021 | 500 | 2022-01-01 | 34 | 행 수 PASS; share class/기업 집계 규칙 별도 확인 |
| 2022 | 500 | 2023-01-01 | 21 | 행 수 PASS; share class/기업 집계 규칙 별도 확인 |
| 2023 | 500 | 2024-01-01 | 14 | 행 수 PASS; share class/기업 집계 규칙 별도 확인 |
| 2024 | 500 | 2025-01-01 | 9 | 행 수 PASS; share class/기업 집계 규칙 별도 확인 |
| 2025 | 500 | 2026-01-01 | 2 | 행 수 PASS; share class/기업 집계 규칙 별도 확인 |

여기서 “CIK 중복 초과 행”은 `count(CIK)-1`의 합이다. 이는 CSV가 security/listing 수준을 포함할 수 있음을 의미하며, 즉시 오류로 판정하지 않는다. historical collection-ready manifest에서는 company-level identity와 filing 고유성을 다시 검증해야 한다.

### 2.2 collection-ready sample manifest

현재 확인된 유효 행 수는 다음과 같다.

| 연구연도 | manifest 유효 firm-year 행 수 | batch/수집 상태 |
|---:|---:|---|
| 2020 | 446 | 기존 완료 산출물 |
| 2021 | 462 | 기존 완료 산출물 |
| 2022 | 471 | 기존 완료 산출물 |
| 2023 | 479 | 기존 완료 산출물 |
| 2024 | 487 | 기존 완료 산출물 |
| 2025 | 484 | 기존 완료 산출물 |

CSV의 500개 구성종목과 manifest의 유효 행 수가 다른 이유는 filing 부재, identity 정제, 중복 제거 및 collection eligibility 규칙 때문이다. 이 차이를 임의 보간하거나 500개로 맞추지 않는다.

### 2.3 프로젝트 historical reference

프로젝트가 보관한 historical components 파일:

```text
data/raw/sp500_historical_components_2026-07-24.csv
```

확인된 총 행 수는 2,718개이며 열은 `date,tickers`다. 이 파일은 연도별 membership reconstruction의 프로젝트 내부 원천으로 남기며, 외부 현재 snapshot으로 덮어쓰지 않는다.

## 3. 외부 원천의 성격

### 3.1 datasets/s-and-p-500-companies

저장소 README는 이 자료를 S&P 500 companies 데이터셋으로 설명하고, 최신 공개 목록은 Wikipedia를 참조한다고 명시한다. 현재 파일은 현재 시점의 구성 목록에 가깝고, README의 source/licence 정보도 함께 확인해야 한다.

- 저장소: [datasets/s-and-p-500-companies](https://github.com/datasets/s-and-p-500-companies)
- 비교 파일: `data/constituents.csv`
- 감사 시점 외부 행 수: 502
- 외부 파일은 현재 스냅샷이므로 2020, 2021, …, 2025의 특정 snapshot과 시간 정렬되어 있지 않다.
- 실제 내용에는 2026년 유효일이 포함된 신규 구성종목이 보인다. 따라서 이 파일을 과거 2020–2025의 historical truth로 사용할 수 없다.

### 3.2 hanshof/sp500_constituents

README는 1996년 이후 historical constituents를 제공한다고 설명하며, 현재 구성 파일과 별도의 `sp_500_historical_components.csv`를 구분한다.

- 저장소: [hanshof/sp500_constituents](https://github.com/hanshof/sp500_constituents)
- 현재 구성 파일: `sp500_constituents.csv`
- historical 파일: `sp_500_historical_components.csv`
- 이 감사 환경에서는 historical raw CSV가 4MB 응답 제한을 초과하여 전체 내용을 기계적으로 내려받아 행 단위 대조하지 못했다.
- 따라서 hanshof historical 파일에 대해 “2020–2025 전체 행 일치”라고 주장하지 않는다. 저장소의 파일 구분과 제공 범위만 독립 참고로 기록하고, 실제 정량 대조는 파일을 별도로 확보한 후 재현해야 한다.

## 4. 정량 비교: 2025 프로젝트 CSV 대 datasets 현재 파일

비교 대상:

- 프로젝트: `2025/sp500_companies.csv`, 500행
- 외부: `datasets/s-and-p-500-companies/data/constituents.csv`, 502행
- 키: CIK 정규화 후 교집합·차집합

결과:

| 비교 항목 | 수 |
|---|---:|
| 프로젝트 CSV 행 수 | 500 |
| datasets 외부 행 수 | 502 |
| CIK 교집합 | 488 |
| 프로젝트에만 존재하는 CIK | 9 |
| 외부에만 존재하는 CIK | 11 |

프로젝트에만 존재하는 대표 종목:

```text
CPB Campbell's
CAG Conagra Brands
EPAM EPAM Systems
EA Electronic Arts
LW Lamb Weston
MTCH Match Group
MOH Molina Healthcare
PAYC Paycom
POOL Pool Corporation
```

외부에만 존재하는 대표 종목:

```text
CASY, CIEN, COHR, ECHO, FDXF, FLEX,
HONA, LITE, MRVL, VEEV, VRT
```

외부 차집합에는 2025–2026 유효일 또는 현재 구성 변화가 관찰되므로, 이 차이는 우선적으로 “2025 historical CSV의 오류”가 아니라 **서로 다른 기준일과 구성 변화**로 해석해야 한다. CIK 교집합 488/500은 현재 snapshot과 프로젝트 2025 CSV 사이의 높은 식별자 중첩을 보여주지만, historical 정확성이나 filing completeness를 증명하지는 않는다.

## 5. 비교 결과의 해석 규칙

### PASS로 기록하는 항목

- 2020–2025 각 CSV가 500행을 가짐.
- 각 CSV에 `sample_year`, `snapshot_date`, `cik`가 존재함.
- collection-ready manifest의 유효 행 수가 별도로 기록됨.
- 2025 대 datasets 비교에서 CIK 키를 사용한 결과와 차집합을 재현 가능하게 기록함.
- 외부 current snapshot을 historical 연도 정답으로 사용하지 않음.
- hanshof historical raw 전체 대조 불가를 명시하고 과장된 일치 판정을 하지 않음.

### 추가 확인이 필요한 항목

- CSV의 CIK 중복을 company-level로 집계할 때 적용할 기존 프로젝트 규칙.
- 각 연구연도의 정확한 historical membership effective date와 외부 historical 파일의 이벤트 시점 정렬.
- hanshof `sp_500_historical_components.csv` 전체를 확보한 뒤 2020–2025 각 날짜의 membership 집합 대조.
- CIK가 없는 행의 ticker 정규화와 기업명 변경 이력.
- 구성종목 일치와 SEC 10-K filing 존재는 별개이므로, manifest의 accession·report_date 검증을 별도로 수행.

## 6. 재현 명령

프로젝트 CSV 행 수·snapshot·CIK 중복:

```bash
python - <<'PY'
import csv, collections, pathlib
for year in range(2020, 2026):
    path = pathlib.Path(str(year)) / "sp500_companies.csv"
    rows = list(csv.DictReader(path.open()))
    ciks = [row["cik"].strip() for row in rows if row.get("cik")]
    duplicate_extra = sum(n - 1 for n in collections.Counter(ciks).values() if n > 1)
    print(year, len(rows), sorted({row["snapshot_date"] for row in rows}),
          duplicate_extra)
PY
```

프로젝트 historical reference 행 수:

```bash
python - <<'PY'
import csv
path = "data/raw/sp500_historical_components_2026-07-24.csv"
print(sum(1 for _ in csv.DictReader(open(path))))
PY
```

2025 외부 비교는 datasets 파일을 확보한 뒤 다음 키 규칙을 사용한다.

```text
normalize_cik(value) = digits only, left-zero padding removed
intersection = local_cik ∩ external_cik
local_only = local_cik - external_cik
external_only = external_cik - local_cik
```

## 7. 보호 및 결론

이번 감사에서는 다음 파일을 수정하지 않았다.

```text
panel_2020_2025/
analysis/descriptive_2020_2025/
기존 Figure
기존 원본 HTML
R2 객체
Google Drive 객체
```

결론:

1. 프로젝트 2020–2025 구성종목 CSV는 연도별 500행과 명시적 snapshot date를 갖는다.
2. collection-ready manifest 행 수는 filing/identity 검증 후 446–487행으로 별도 관리된다.
3. datasets 현재 파일과의 2025 CIK 비교는 488개 교집합, 9개 local-only, 11개 external-only로 재현된다.
4. 외부 current snapshot의 기준일이 프로젝트 historical 연구연도와 다르므로, 차집합을 오류로 자동 판정하지 않는다.
5. hanshof는 historical 검증에 적합한 참고 원천이지만, 이번 환경에서는 대용량 raw 파일 전체를 내려받지 못했으므로 정량 일치 판정을 보류한다.
6. 프로젝트의 historical reconstruction과 collection-ready manifest가 분석·수집의 source of truth이며, 외부 저장소는 독립 교차검증 자료다.

감사 판정: **조건부 PASS — 프로젝트 CSV 구조·행 수·2025 외부 CIK 비교는 확인되었고, hanshof historical 전체 정량 대조는 파일 확보 후 후속 작업이 필요하다.**


## 8. 누락·미확인 항목 점검 결과

이번 재점검에서 “비교를 수행했다”고 오해할 수 있는 누락을 별도로 구분했다.

| 항목 | 현재 문서 상태 | 판정 및 후속 조치 |
|---|---|---|
| 외부 저장소 조회일 | 2026-08-06 UTC로 기록 | PASS |
| 외부 저장소 URL | 두 저장소의 repository URL과 파일명이 기록됨 | PASS |
| 외부 저장소 commit SHA/tag | 현재 문서에 고정되지 않음 | **미확인**. 외부 데이터는 mutable하므로 후속 정량 감사에서는 raw 파일 commit SHA를 함께 기록해야 함 |
| datasets 외부 파일 전체 열 목록 | 파일 경로와 행 수만 기록 | **보완 필요**. 현재 비교에 사용한 CIK 열과 실제 header를 별도 수집해 기록해야 함 |
| hanshof 현재 구성 파일 정량 비교 | 수행하지 않음 | **미실시**. 현재 파일은 historical 연구연도와 직접 정렬되지 않아 정답 판정에 사용하지 않음 |
| hanshof historical 2020–2025 행 단위 비교 | 대용량 응답 제한으로 수행하지 못함 | **미확인**. 원본 파일 확보 후 날짜별 membership 집합 비교 필요 |
| datasets 2020·2021·2022·2023·2024별 비교 | 수행하지 않음 | **미실시**. datasets 파일이 현재 snapshot이므로 해당 연도 비교 근거가 없음 |
| 2025 CIK 전체 차집합 | 대표명이 아니라 9개·11개 전체 목록을 기록 | PASS |
| ticker-only 매칭 | CIK를 우선하고 실제 ticker-only 결과는 산출하지 않음 | **미실시**. CIK 결측 행이 있을 때 별도 보조 분석 필요 |
| 외부 source license | datasets README의 PDDL 설명을 확인했으나 원문 license 파일 SHA는 기록하지 않음 | **미확인**. 법적 재배포 판단의 근거로 사용하지 않음 |
| SEC filing 일치 | 구성종목 비교와 별개로 취급 | PASS. accession·report_date는 collection manifest 검증에서 별도 확인 |

따라서 현재 문서의 비교 범위는 **프로젝트 내부 2020–2025 구조 감사 + 2025 대 datasets 현재 snapshot의 CIK 비교**로 한정된다. 위 표의 “미실시/미확인” 항목은 결측값을 0이나 일치로 대체하지 않는다.

### 8.1 외부 원천 버전 고정에 대한 재현성 요구

후속 외부 비교를 PASS로 판정하려면 다음을 추가 기록해야 한다.

1. 외부 repository의 조회 commit SHA 또는 tag.
2. raw 파일 URL과 HTTP retrieval timestamp.
3. raw 파일 SHA-256.
4. 실제 header와 식별자 정규화 함수.
5. 기준일이 같은 연도별 historical membership 입력.
6. 비교 대상의 전체 차집합 CSV 또는 JSON artifact.

현재 감사에서는 이 요건을 충족하지 못한 외부 원천에 대해 역사적 일치 판정을 내리지 않았다.

### 8.2 내부 데이터 보호 재확인

누락 점검 과정에서도 다음은 변경하지 않았다.

- `panel_2020_2025/`
- `analysis/descriptive_2020_2025/`
- 기존 Figure 및 원본 HTML
- R2 object와 Google Drive object
- 기존 dashboard generated data

감사 결과: **문서 기록은 보완 완료. 외부 historical 2020–2025 전체 정량 대조는 여전히 후속 작업으로 남아 있음.**
