# WRDS Data Acquisition Contract

Updated: 2026-08-19

Status: **PHASE 1 CAR SPECIFICATION PREPARED / NOT YET EXECUTED**

## 1. Scope and phase order

이 문서는 RQ2 `10-K Concreteness → Shareholder Reaction` 중 **PHASE 1 단기 주주반응(CAR)**에 필요한 raw data acquisition 계약이다. 실제 WRDS·SEC 요청, identifier linkage, CAR 계산 및 회귀분석은 아직 수행하지 않았다. RQ1 Tense는 보류 상태다.

- **PHASE 1 — 현재 우선:** Short-term shareholder reaction, CAR
- **PHASE 2 — 후속:** Long-term shareholder reaction, BHAR

PHASE 1은 Compustat Annual, Compustat Quarterly RDQ, CCM link history, CRSP CIZ daily security returns, CRSP daily market returns 및 선택적 factor data를 대상으로 한다. BHAR horizon·benchmark·장기 보유수익률·장기 delisting 처리·미래 snapshot 전략은 PHASE 2에서 별도 설계하며 CAR 수집의 blocker가 아니다.

현재 CRSP는 legacy SIZ가 아니라 CIZ(Flat File Format 2.0)를 최신 형식으로 사용한다. 공식 공개 문서에서 확인된 필드만 아래 계약에 확정하고, 계정별 library·table·column availability가 필요한 항목은 `VERIFY IN WRDS UI BEFORE QUERY`로 표시한다. 공식 근거는 [WRDS CRSP CIZ 전환 안내](https://wrds-www.wharton.upenn.edu/pages/data-announcements/changes-to-crsp-data/), [WRDS CIZ-to-SIZ macro](https://wrds-www.wharton.upenn.edu/pages/wrds-research/macros/crsp-ciztosiz-macro/), [WRDS CIZ event-study macro](https://wrds-www.wharton.upenn.edu/pages/wrds-research/macros/run-an-event-study-ciz-format-macro/), [CRSP CIZ Database Guide](https://www.crsp.org/wp-content/uploads/guides/CRSP_US_Stock_%26_Indexes_Database_Guide_Flat_File_Format_2.0.pdf), [CRSP/Compustat Merged Data Guide](https://wrds-www.wharton.upenn.edu/documents/402/CRSP-Compustat_Merged_Database_Data_Guide_9efDcmD.pdf)를 우선한다.

## 2. Primary empirical sample

### PHASE 1 primary sample

- source: `analysis/descriptive_2020_2025/firm_year_language_extended.parquet`
- period: 2020–2025 report year
- unit: 기업-연도
- observations: 2,829
- unique companies/CIKs: 545
- accession numbers: 2,829 unique
- duplicate CIK–report year: 0

첫 CAR acquisition은 검증된 **2020–2025 core 2,829건**만 대상으로 한다. Historical candidate 4,897건은 과거로 갈수록 관측치가 감소하며 완전한 historical S&P 500 panel이 아니므로 future robustness/extension으로 분리한다.

Whole-report concreteness, AI-related concreteness 및 difference score 중 최종 main IV는 미확정이다. 모두 동일 firm-event market data를 사용하므로 PHASE 1 raw acquisition 범위에는 영향을 주지 않는다. Whole-report Concreteness는 `READY WITH DOCUMENTED LIMITATIONS` 상태다.

## 3. Event-date contract

### 별도 보존할 날짜

| Field | Definition | Current availability |
| --- | --- | --- |
| `sec_filing_date` | SEC calendar filing date | core 2,829/2,829 |
| `sec_acceptance_datetime_raw` | SEC 원문 acceptance timestamp | canonical panel에는 없음 |
| `sec_acceptance_datetime_et` | `America/New_York` timezone-aware 값 | 향후 enrichment |
| `market_event_date` | CRSP trading calendar와 acceptance time으로 정렬한 event date | 향후 derived |

Canonical filing range는 **2020-02-18~2026-03-02**이고 주말 filing은 0건이다. 기존 2025 pilot은 적격 100건 중 99건에 유효 timestamp가 있다. `scripts/collect_sec_filing_metadata.py`는 이미 SEC `acceptanceDateTime`을 `acceptance_datetime`으로 보존하므로 새 collector를 만들지 않는다.

### Market-event-date 후보 규칙

1. SEC 원문 timestamp와 timezone을 보존한다.
2. timestamp를 `America/New_York`으로 변환한다.
3. 정규 거래일의 실제 session close 이전 acceptance는 당일 trading day를 사용한다.
4. close 이후 또는 정확히 close 시각인 acceptance는 다음 CRSP trading day로 이동한다.
5. 주말·휴장일은 다음 CRSP trading day로 이동한다.
6. 조기 폐장은 공식 trading calendar의 실제 close를 적용한다.
7. timestamp가 없으면 명시적 missing status로 남기고 filing date로 조용히 대체하지 않는다.

정규 close를 모든 날짜에 일괄 하드코딩하지 않는다. Exact-close boundary와 early-close schedule source는 구현 시 공식 trading calendar로 검증한다.

Acceptance timestamp enrichment는 **최종 CAR event-date construction에는 필요하지만 CRSP raw acquisition의 blocker는 아니다.** 두 pipeline을 분리한다.

```text
SEC metadata enrichment
CIK + accession_number → acceptance datetime → market event date

WRDS acquisition
CIK → GVKEY → CCM → PERMNO → fundamentals + daily returns
```

## 4. Identifier linkage contract

Canonical path는 다음과 같다.

```text
10-K CIK → Compustat GVKEY → CCM link history → PERMNO / PERMCO
```

회사명과 ticker는 검토·감사용 보조값이며 primary linkage key가 아니다.

### CIK normalization and CIK → GVKEY

- 숫자 identity를 확인하고 audit representation은 10자리 zero-padded string으로 저장한다.
- 예: `320193 → 0000320193`
- source CIK와 normalized CIK를 모두 보존한다.
- Compustat identifier/date fields: `gvkey`, `cik`, `tic`, `conm`, `cusip`, `datadate`, `fyear`, `fyr`, `sic`
- `exact_1_to_1`, `one_cik_multiple_gvkey`, `unmatched_cik`, `duplicate_candidate`, `manual_review`를 구분한다.
- One-to-many와 unmatched를 silent drop하지 않는다.

### GVKEY → PERMNO via CCM

공식 WRDS macro에서 사용하는 canonical table 후보는 `crsp.ccmxpf_lnkhist`다. Raw link history에 최소 다음 필드를 보존한다.

- `gvkey`
- `liid`
- `lpermno`
- `lpermco`
- `linkdt`
- `linkenddt`
- `linktype`
- `linkprim`

Event-date 유효 조건은 다음과 같다.

```text
linkdt ≤ market_event_date ≤ linkenddt
```

Missing/open-ended `linkenddt`는 active 후보로 처리하되 원래 coding을 보존하고 WRDS UI에서 확인한다. 공식 CCM guide에 따른 코드 의미는 다음과 같다.

- `LC`: research complete, standard link
- `LU`: unresearched CUSIP link
- `LS`: 해당 security에 한정된 유효 link
- `P`: Compustat가 지정한 primary issue
- `C`: overlapping 또는 missing primary marker를 해결하기 위해 CRSP가 지정한 primary issue

WRDS 공식 CIZ macro의 후보 필터 `linktype in ('LC','LU','LS')` 및 `linkprim in ('P','C')`를 derived selection의 출발점으로 사용한다. Raw query에서는 실제 분포를 확인하기 전에 다른 후보를 조용히 버리지 않는다.

### Multiple PERMNO

First row를 선택하지 않는다. Deterministic hierarchy 후보는 다음과 같다.

1. market event date에 active link
2. 승인된 linktype
3. linkprim priority
4. common equity·primary trading security
5. CAR estimation history와 event-window return availability
6. 여전히 복수이면 manual review

모든 candidate를 intermediate audit에 보존한다. 실제 tie 빈도를 보기 전 추가 tie-break를 확정하지 않는다.

## 5. Compustat Annual — Dataset A

Matched GVKEY에 대해 identifier와 CAR 회귀의 최소 control raw components를 수집한다.

| Category | Raw fields |
| --- | --- |
| Identity/date | `gvkey`, `cik`, `conm`, `tic`, `cusip`, `datadate`, `fyear`, `fyr` |
| Classification/audit | `sic`, `naics`, `fic`, `curcd`, `indfmt`, `datafmt`, `popsrc`, `consol` |
| Fundamentals | `at`, `dltt`, `dlc`, `prcc_f`, `csho`, `ceq`, `seq`, `ni`, `ib`, `intan`, `spi` |

Acquisition range 후보는 `datadate` **2018-01-01~2025-12-31**이다. 이는 해당 10-K fiscal year와 t−1/pre-event specification을 모두 구성하기 위한 범위다. Derived formulas는 regression 단계에서 확정하고 raw components를 보존한다.

표준 filter 후보는 `consol='C'`, `indfmt='INDL'`, `datafmt='STD'`, `popsrc='D'`다. 실제 query 전 공식 Compustat schema와 entitlement에서 필드·코드를 확인한다. `report_year == fyear`만으로 연결하지 않고 SEC `report_date ↔ datadate` exact match를 우선하며, tolerance는 실제 linkage distribution을 본 뒤 정한다.

Age, BusSeg, ForSeg, BigN처럼 별도 history/table 비용이 큰 후보는 최초 CAR acquisition의 blocker가 아니다.

## 6. Compustat Quarterly RDQ — Dataset B

Earnings announcement confounding을 확인하기 위해 최소 다음 필드를 수집한다.

- `gvkey`
- `datadate`
- `fyearq`
- `fqtr`
- `rdq`

RDQ와 `market_event_date` 간 calendar/trading-day 거리를 계산할 수 있게 원자료를 보존한다. Overlap indicator, exclusion, control 또는 robustness 중 사용할 방식과 threshold는 분석 단계에서 결정한다. 실제 quarterly table과 `rdq` availability/type은 `VERIFY IN WRDS UI BEFORE QUERY`다.

## 7. CCM — Dataset C

Matched GVKEY의 link history를 별도 raw artifact로 받는다. Compustat annual 또는 CRSP return과 대규모 one-shot join을 하지 않는다. 실행 직전 다음을 확인한다.

- `crsp.ccmxpf_lnkhist` 접근 가능 여부
- 계약 필드 존재와 datatype
- open-ended `linkenddt` coding
- `LC/LU/LS`, `P/C` 분포

## 8. CRSP CIZ Daily — Dataset D

### Canonical table and fields

공식 WRDS CIZ macro가 사용하는 security-level daily table은 **`crsp.dsf_v2`**다.

| Requirement | Canonical CIZ field | Status |
| --- | --- | --- |
| Security ID | `permno` | 공식 macro 확인 |
| Trading date | `dlycaldt` | 공식 macro/guide 확인 |
| Total daily return | `dlyret` | 공식 macro/guide 확인 |
| Ex-dividend return | `dlyretx` | 공식 macro/guide 확인 |
| Price | `dlyprc` | 공식 macro/guide 확인 |
| Volume | `dlyvol` | 공식 macro/guide 확인 |
| Market capitalization | `dlycap` | 공식 macro/guide 확인 |
| Price adjustment factor | `dlycumfacpr` | 공식 macro 확인 |
| Share adjustment factor | `dlycumfacshr` | 공식 macro 확인 |
| Delisting-return indicator | `dlydelflg` | 공식 CIZ guide 확인; UI column 확인 필요 |
| Return-missing indicator | `dlyretmissflg` | 공식 CIZ guide 확인; UI column 확인 필요 |
| Distribution-return indicator | `dlydistretflg` | 공식 CIZ guide 확인; UI column 확인 필요 |

CAR의 canonical return은 `dlyret`이다. 공식 CIZ guide는 `DlyRet`을 daily total return으로 정의하며 `DlyDelFlg='Y'`는 해당 daily row에 delisting return이 존재함을 나타낸다. 따라서 short event/estimation window의 delisting occurrence는 CIZ total-return row와 audit flags로 확인한다. Legacy `RET`, `DLRET`, `DLSTCD`를 CIZ query에 임의 적용하지 않는다.

Security-history table·fields는 `stkSecurityInfoHist`, `secInfoStartDt`, `secInfoEndDt`, `PrimaryExch`, `SecurityType`, `SecuritySubType`, `ShareType`, `USIncFlg`, `IssuerType`, `TradingStatusFlg`, `ConditionalType` 후보를 실행 전 UI에서 확인한다. Shares-outstanding equivalent는 CAR 계산의 필수값이 아니므로 확인이 늦어져도 acquisition blocker가 아니다. `dlycap`과 `dlyvol`은 저비용 control/후속 분석을 위해 보존한다.

## 9. CRSP Market and factor data

### Dataset E: CRSP Daily Market Returns

공식 WRDS CIZ macro의 table 후보는 **`crsp.wrds_dailyindexret_query`**다.

- `dlycaldt`
- `vwretd`
- `ewretd`

Value-weighted와 equal-weighted market return을 모두 받는다. Baseline Market Model의 primary benchmark 선택은 분석 단계에서 확정한다. Table/fields의 현재 계정 availability는 WRDS UI에서 확인한다.

### Dataset F: Factor Daily — optional robustness

FF4 robustness 후보는 유지하되 initial CRSP acquisition의 blocker가 아니다.

- `date`
- `mktrf` / `MKT-RF`
- `smb` / `SMB`
- `hml` / `HML`
- `umd` 또는 `mom`
- `rf` / `RF`

WRDS 공개 macro의 후보 source는 `ff.factors_daily`다. 실제 entitlement/schema를 확인하고 별도 raw artifact로 보존한다.

## 10. CAR estimation and event windows

- Primary estimation candidate: event 전 약 `[-300,-46]` trading-day 영역에서 255 trading observations
- Planned CAR windows: `[-1,+1]`, `[-2,+2]`, `[-3,+3]`
- Robustness candidates: `[-1,+2]`, `[-2,0]`, `[0,+2]`

모든 index는 **CRSP trading day** 기준이다. Calendar-day subtraction으로 estimation window를 만들지 않는다. Minimum estimation observations와 exact expected-return model은 raw acquisition 후 specification 단계에서 확정할 수 있다.

## 11. CAR-only CRSP query date range

Observed canonical filing range:

- earliest: **2020-02-18**
- latest: **2026-03-02**

PHASE 1 security·market·factor daily acquisition 범위:

```text
2018-08-01 through 2026-03-31
```

- Start: earliest event보다 18개월 앞선 월초로, 255 observations ending 46 trading days before event와 휴장·missing-return buffer를 포괄한다.
- End: latest event의 최대 short window `+3 trading days`보다 충분히 뒤인 월말 buffer다.
- 실제 trading-day coverage는 CRSP calendar에서 확인한다.
- 현재 2026-08 기준 latest event의 short CAR는 이미 성숙했으므로 future append나 2027 자료가 필요하지 않다.

가능하면 linkage audit 후 selected/candidate PERMNO universe로 제한한다. **CAR는 one current acquisition sufficient**이며, PHASE 2 BHAR의 future snapshot 전략과 분리한다.

## 12. Raw artifact retention

이번 작업에서는 디렉터리를 만들지 않았다. 실제 수집 시 기존 적절한 구조를 우선 재사용하고, 없을 때 다음 개념을 사용한다.

```text
data/wrds/raw/
  compustat_annual.*
  compustat_quarterly_rdq.*
  ccm_links.*
  crsp_daily_car.*
  crsp_market_daily_car.*
  factor_daily_car.*

data/wrds/derived/
  identifier_crosswalk.*
  car_event_security_map.*
  car_event_return_panel.*
```

Raw artifact를 final panel에 즉시 merge하거나 덮어쓰지 않는다. Query text, schema/table/fields, date range, extraction timestamp, release 정보, row count, file size, SHA-256, missing encoding 및 timezone을 함께 보존한다.

## 13. CAR linkage and audit fields

최소 다음을 intermediate audit dataset에 보존한다.

- source/normalized CIK
- GVKEY, match status, candidate count, selection reason
- CCM candidate count와 모든 PERMNO candidates
- selected PERMNO/PERMCO와 selection reason
- `linktype`, `linkprim`, `linkdt`, `linkenddt`
- `sec_filing_date`, raw/ET acceptance datetime
- `market_event_date`, alignment reason/status
- estimation-window observation count
- market-return availability
- event-window availability
- RDQ/confounding status
- CAR availability status

## 14. CAR sample attrition

```text
Initial core 10-K sample: 2,829
→ CIK valid
→ CIK–GVKEY matched
→ valid-date CCM link
→ primary PERMNO selected
→ sufficient CRSP estimation observations
→ market return available
→ event window available
→ RDQ/confounding status available
→ final CAR sample
```

각 단계에서 `starting_n`, `passed_n`, `excluded_n`, `exclusion_reason`을 남기고 unmatched를 silent drop하지 않는다. BHAR sample flow는 PHASE 2에서 별도 정의한다.

## 15. Readiness priorities

### P0 — WRDS query 직전 UI 확인 필수

- Compustat Annual·Quarterly table names, 계약 fields 및 datatype
- Quarterly `rdq` availability
- `crsp.ccmxpf_lnkhist`와 CCM fields/open-end coding
- `crsp.dsf_v2` 접근 및 `permno`, `dlycaldt`, `dlyret` 포함 계약 fields
- `dlydelflg` 등 audit flags의 실제 column spelling/casing
- `crsp.wrds_dailyindexret_query`, `vwretd`, `ewretd`
- CRSP 자료가 2026-03-31까지 이용 가능한지
- CAR-only query range `2018-08-01~2026-03-31`

### P1 — query 후 linkage/event construction에서 결정 가능

- 실제 multiple-PERMNO tie resolution
- 전체 2,829건 acceptance timestamp enrichment
- exact-close boundary와 early-close schedule source
- RDQ confounding threshold
- report date–datadate tolerance

### P2 — regression specification에서 결정 가능

- exact main IV
- primary Market Model benchmark와 minimum estimation observations
- primary/robustness CAR window designation
- FF4 specification
- standard-error and clustering specification
- same-report versus lagged control timing

## 16. PHASE 2 — BHAR deferred

다음은 삭제하지 않되 **DEFERRED TO PHASE 2 — BHAR**로 분리한다.

- BHAR start day
- 1/3/6/12-month horizon
- benchmark와 long-term compounding
- long-term delisting treatment
- missing/suspended return handling
- next 10-K overlap와 long-horizon confounding
- maturity·snapshot·append-only refresh strategy
- PHASE 2 전용 query end date와 sample attrition

이 항목들 때문에 PHASE 1 CAR raw acquisition을 지연시키지 않는다.

## 17. Actual CAR acquisition order

1. Compustat Annual
2. Compustat Quarterly RDQ
3. CCM Link Table
4. CIK → GVKEY → PERMNO linkage audit
5. 확정 PERMNO universe 기반 CRSP Daily CAR range
6. CRSP Market Daily 동일 range
7. 필요 시 Factor Daily
8. SEC acceptance timestamp enrichment
9. Market event date construction
10. CAR calculation

BHAR는 이 sequence에 포함하지 않는다.

## 18. Actual WRDS execution checklist — CAR

- [ ] Current branch와 clean working tree 확인
- [ ] Core panel 2,829 rows와 source SHA 확인
- [ ] CIK normalization rule 확인
- [ ] Compustat Annual table/schema와 fields 확인
- [ ] Compustat Quarterly table과 RDQ 확인
- [ ] CCM table/schema·fields·open-end coding 확인
- [ ] CIZ `crsp.dsf_v2`와 total return `dlyret` 확인
- [ ] CIZ return audit flags 확인
- [ ] CRSP Market Daily table과 `vwretd`·`ewretd` 확인
- [ ] Earliest/latest filing date 확인
- [ ] CAR-only range `2018-08-01~2026-03-31` 확인
- [ ] Query text 저장
- [ ] Raw artifact overwrite 방지
- [ ] Row count·file size·SHA-256 기록
- [ ] Unmatched linkage silent drop 금지
- [ ] 실제 WRDS 실행 별도 승인

## 19. Final readiness verdict

**READY FOR CAR WRDS ACQUISITION EXCEPT FOR FIELDS TO VERIFY IN WRDS UI**

공식 공개 자료로 CIZ canonical table·daily total return·market-return source와 CCM 후보 schema를 확인했다. 실제 계정의 entitlement, table/column availability, casing, RDQ 및 latest CRSP date는 query 실행 직전 UI에서 확인해야 한다. Acceptance timestamp enrichment와 분석 specification의 P1/P2 결정은 raw acquisition을 막지 않는다. 실제 WRDS query는 아직 실행하지 않았다.
