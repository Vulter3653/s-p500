# WRDS Data Acquisition Contract

Updated: 2026-08-19

Status: **SPECIFICATION PREPARED / NOT YET EXECUTED**

## 1. Scope

이 문서는 RQ2 `10-K Concreteness → Shareholder Reaction` 분석에 필요한 외부 자료를 한 번의 계획된 수집으로 확보하기 위한 계약이다. 실제 WRDS·SEC 요청, identifier linkage, CAR·BHAR 계산 및 회귀분석은 아직 수행하지 않았다. RQ1 Tense는 보류 상태이며 이 계약의 수집 범위를 늘리지 않는다.

계약은 다음 여섯 부분을 정의한다.

- A. Empirical sample contract
- B. Event-date contract
- C. `CIK → GVKEY → CCM → PERMNO` linkage contract
- D. Compustat acquisition contract
- E. CRSP acquisition contract
- F. Earnings/confounding-event data contract

현재 CRSP는 legacy SIZ가 아니라 CIZ(Flat File Format 2.0)를 최신 형식으로 사용한다. 따라서 아래에서 **검증됨**으로 표시한 필드만 자동 query 대상으로 삼고, `VERIFY IN WRDS BEFORE RUN` 항목은 실제 계정의 data dictionary와 table columns를 확인하기 전에는 query에 넣지 않는다. 공식 근거는 [WRDS CRSP CIZ 전환 안내](https://wrds-www.wharton.upenn.edu/pages/data-announcements/changes-to-crsp-data/), [WRDS CIZ-to-SIZ macro](https://wrds-www.wharton.upenn.edu/pages/wrds-research/macros/crsp-ciztosiz-macro/), [CRSP/Compustat Merged Data Guide](https://wrds-www.wharton.upenn.edu/documents/402/CRSP-Compustat_Merged_Database_Data_Guide_9efDcmD.pdf)를 우선한다.

## 2. Primary empirical sample

### Primary sample — 확정 후보

- source: `analysis/descriptive_2020_2025/firm_year_language_extended.parquet`
- period: 2020–2025 report year
- unit: 기업-연도
- observations: 2,829
- unique companies/CIKs: 545
- accession numbers: 2,829 unique
- duplicate CIK–report year: 0

첫 WRDS empirical acquisition은 이 **2020–2025 core 2,829건**만 대상으로 한다. 이 패널은 현재 canonical·validated sample이고 연도별 구성, filing identity 및 언어 측정의 검증 수준이 historical candidate보다 높다. 표본 완전성과 identifier 품질을 우선하고 불필요한 historical query 비용과 선택편향 위험을 줄이기 위한 결정이다.

### Historical candidate — 향후 robustness/extension

- period: 2006–2025
- observations: 4,897
- historical additions: 2,068
- status: 원천과 적격 filing이 확인된 candidate panel

Historical candidate는 과거로 갈수록 관측치가 감소하고 매년 완전한 S&P 500 전체 패널이 아니므로 첫 query에 포함하지 않는다. 향후 별도 승인 후 robustness 또는 확장 표본으로 수집한다. 이는 연구가설 변경이 아니라 acquisition scope의 단계 구분이다.

### Main IV와의 관계

Whole-report concreteness, AI-related concreteness 및 difference score 중 최종 main IV는 미확정이다. 세 후보 모두 동일 firm-event의 financial/market data를 사용하므로 WRDS query 범위에는 영향을 주지 않는다. Whole-report measure의 현재 상태는 `READY WITH DOCUMENTED LIMITATIONS`이다.

## 3. Event date

### 보존할 세 날짜

다음 값을 각각 별도 필드로 보존한다. 하나를 다른 값으로 덮어쓰지 않는다.

| Field | Definition | Current availability |
| --- | --- | --- |
| `sec_filing_date` | SEC의 공식 calendar filing date | core 2,829/2,829 |
| `sec_acceptance_datetime_raw` | SEC가 제공한 원문 timestamp | canonical panel에는 없음 |
| `sec_acceptance_datetime_et` | timezone-aware timestamp를 `America/New_York`으로 변환한 값 | 향후 enrichment |
| `market_event_date` | CRSP trading calendar와 acceptance time으로 정렬한 event trading date | 향후 derived |

Canonical panel의 filing-date 범위는 **2020-02-18~2026-03-02**이고 주말 filing은 0건이다. 기존 2025 pilot metadata에서는 적격 100건 중 99건에 `acceptance_datetime`이 있으며, replacement ITW 1건은 비어 있다. 따라서 전체 2,829건의 acceptance timestamp는 향후 SEC metadata enrichment requirement다.

### Market-event-date 기본 규칙

1. SEC timestamp 원문과 timezone 표기를 그대로 보존하고 timezone-aware 값으로 파싱한다.
2. `America/New_York`으로 변환한다.
3. 해당 날짜가 CRSP trading day이고 acceptance가 그 날의 정규 session close **이전**이면 같은 trading day를 후보 event date로 둔다.
4. session close 이후 또는 정확히 close 시각이면 다음 CRSP trading day로 이동한다.
5. 주말·휴장일이면 다음 CRSP trading day로 이동한다.
6. timestamp가 없으면 `event_date_alignment_status=missing_acceptance_timestamp`로 남기며 calendar filing date로 조용히 대체하지 않는다. Filing-date-only sensitivity를 사용할지는 별도 승인 사항이다.

정규 close를 일괄 `16:00`으로 하드코딩하지 않는다. 조기 폐장 등을 반영한 실제 거래일 session schedule과 event-study 문헌을 implementation 단계에서 검증한다. CRSP market daily date를 canonical trading calendar로 사용한다.

### SEC metadata enrichment와 WRDS의 분리

```text
SEC metadata enrichment
CIK + accession_number
→ acceptanceDateTime
→ timezone normalization
→ market-event-day alignment

WRDS acquisition
CIK → GVKEY → CCM → PERMNO
→ fundamentals + market returns
```

기존 `scripts/collect_sec_filing_metadata.py`는 이미 SEC `acceptanceDateTime`을 `acceptance_datetime`으로 보존한다. 새 collector를 만들지 않고, 실제 enrichment 단계에서 이 canonical 처리 경로를 core panel에 최소 확장한다. 이번 계약 작성에서는 SEC 요청을 실행하지 않았다.

## 4. Identifier linkage

### Canonical path

```text
10-K CIK
→ Compustat GVKEY
→ CRSP/Compustat Merged link history
→ PERMNO / PERMCO
```

회사명과 ticker는 검토·감사용 보조값이며 primary linkage key가 아니다.

### CIK normalization

- 동일성 판정: 숫자값 기준
- canonical audit representation: 10자리 zero-padded string
- 예: `320193 → 0000320193`
- 입력 원문 CIK와 normalized CIK를 모두 보존
- 숫자가 아니거나 10자리를 초과하는 값은 자동 수정하지 않고 invalid 상태로 분류

현재 core panel의 CIK는 이미 10자리 문자열이며 545개가 모두 존재한다.

### CIK → GVKEY

Compustat에서 최소 `gvkey`, `cik`, `tic`, `conm`, `cusip`, `datadate`, `fyear`를 확보한다. CIK는 current identifier일 수 있으므로 날짜가 있는 annual records와 company identifier records를 함께 보존한다.

필수 audit status:

- `exact_1_to_1`
- `one_cik_multiple_gvkey`
- `unmatched_cik`
- `duplicate_candidate`
- `manual_review`

One-to-many와 unmatched를 자동 drop하지 않는다. 후보의 `gvkey`, company name, ticker, CUSIP, available date range 및 fiscal records를 모두 남긴다.

### GVKEY → PERMNO via CCM

Raw CCM link history는 matched GVKEY의 모든 후보를 보존한다.

필수 필드:

- `gvkey`
- `liid`
- `lpermno`
- `lpermco`
- `linkdt`
- `linkenddt`
- `linktype`
- `linkprim`

유효일 기본 조건:

```text
linkdt ≤ market_event_date ≤ linkenddt
```

Missing/open-ended `linkenddt`는 active link 후보로 처리하되 원래 결측을 보존한다. 공식 CCM guide는 `LINKPRIM`의 P/C를 primary marker로, `LINKTYPE`의 LC/LU/LS 등을 링크 성격으로 정의한다. WRDS의 현재 CIZ macro는 `LC`, `LU`, `LS`와 `P`, `C`를 사용하므로 이를 **derived selection의 우선 후보**로 둔다. 실제 계정 schema와 분포를 확인하기 전 raw query에서 다른 link type을 버리지 않는다.

### Multiple PERMNO

한 event에 여러 security candidate가 있으면 first row를 선택하지 않는다.

선택 순서:

1. event date에 유효한 CCM link
2. 승인된 `linktype`
3. `linkprim ∈ {P, C}`
4. CRSP security history상 common equity·primary trading security
5. event 전 estimation history와 event 후 return availability
6. 위 조건 후 후보가 하나일 때만 자동 선택
7. 둘 이상이면 manual review; 모든 후보 보존

최종 derived map은 `one event → one primary PERMNO`를 목표로 한다. Value-weighted multi-security aggregation은 robustness 후보이며 기본값이 아니다.

## 5. Compustat Annual

### Dataset A: annual fundamentals + identifiers

Primary sample의 matched GVKEY만 대상으로 한다. `datadate` acquisition range는 **2018-01-01~2025-12-31**로 두어 report fiscal year와 t−1/pre-event specification을 한 번의 수집으로 구성할 수 있게 한다.

| Category | Raw fields |
| --- | --- |
| Identity/date | `gvkey`, `cik`, `conm`, `tic`, `cusip`, `datadate`, `fyear`, `fyr` |
| Classification/audit | `sic`, `naics`, `fic`, `curcd`, `indfmt`, `datafmt`, `popsrc`, `consol` |
| Fundamentals | `at`, `dltt`, `dlc`, `prcc_f`, `csho`, `ceq`, `seq`, `ni`, `ib`, `intan`, `spi` |

현재 계획한 파생 후보와 보존할 raw components:

| Concept | Candidate formula | Status |
| --- | --- | --- |
| Firm Size | `ln(at)` | primary control candidate |
| Leverage | `(dltt + dlc) / at` | primary control candidate |
| MTB | `(prcc_f × csho) / ceq` | formula and denominator treatment pending |
| Loss | `ni < 0` | primary control candidate |
| Intangibles | `intan / at` | optional control candidate |
| Special Items | `spi / at` | optional control candidate |

파생변수만 내려받지 않고 raw components를 보존한다. `seq`, `ib`는 equity·income alternative 및 결측 audit용으로 유지한다. Age는 company-history/IPO source, BusSeg·ForSeg는 segment source, BigN은 auditor source가 추가로 필요할 수 있으므로 첫 annual minimum query에 이름만 추정해 넣지 않는다. 이 세 후보는 `VERIFY IN WRDS BEFORE RUN` 및 별도 승인 항목이다.

### Format filters

공개 WRDS 예제의 표준 후보는 다음과 같다.

```text
consol = 'C'
indfmt = 'INDL'
datafmt = 'STD'
popsrc = 'D'
```

다만 첫 수집의 목적은 matched firms를 잃지 않는 것이므로 raw acquisition에서는 `indfmt`, `datafmt`, `popsrc`, `consol` 값을 함께 보존하고, canonical filter 적용 전 unmatched/duplicate 분포를 audit한다. 특히 비표준 산업·금융 형식 때문에 core firm이 사라지는지 확인한다. 국가를 `fic='USA'`로 사전 제한하지 않는다. 공식 예제: [WRDS Market-to-Book macro](https://wrds-www.wharton.upenn.edu/pages/wrds-research/macros/wrds-macros-market-book-ratios/).

### SEC report date ↔ Compustat datadate

`report_year == fyear`만으로 연결하지 않는다.

1. SEC `report_date`와 Compustat `datadate` exact match를 우선한다.
2. exact가 없으면 모든 nearby candidate와 date difference를 보존한다.
3. 허용 tolerance는 실제 distribution을 본 뒤 승인한다.
4. `fyear`는 validation field로 사용한다.
5. no match와 multiple candidate를 명시적 status로 남긴다.

### Control timing

- Specification 1 후보: 해당 10-K fiscal-year fundamentals
- Specification 2 후보: t−1 또는 filing 이전 latest public fundamentals

Same-report fiscal values가 earnings announcement에서 먼저 공개됐을 수 있으므로 두 timing specification을 모두 구성할 수 있게 raw annual history를 받는다. 어떤 것을 primary control로 사용할지는 회귀 specification 단계에서 확정한다.

## 6. Compustat Quarterly RDQ

### Dataset B: earnings announcement dates

최소 필드:

- `gvkey`
- `datadate`
- `fyearq`
- `fqtr`
- `rdq`

Matched GVKEY에 대해 `datadate` **2019-01-01~2025-12-31**을 수집하고, 해당 fiscal quarter의 `rdq`가 2026년에 속해도 보존한다. `rdq`의 실제 availability와 datatype은 WRDS data dictionary에서 실행 직전 확인한다.

목적은 다음 값을 계산할 수 있게 하는 것이다.

```text
earnings_event_gap_calendar_days = market_event_date - rdq
earnings_event_gap_trading_days  = trading-day distance(market_event_date, rdq)
```

Event overlap threshold, exclusion rule 및 near-event indicator는 아직 미확정이다. Raw RDQ를 먼저 보존해 exclusion과 robustness를 모두 가능하게 한다.

## 7. CCM

### Dataset C1: link history

Matched GVKEY의 모든 CCM link records를 별도 raw artifact로 저장한다. 최소한 core event range와 CRSP acquisition range에 겹치는 link를 포함하되, 작은 link table은 matched GVKEY의 전체 link history를 받는 것을 우선한다. Link candidate를 Compustat annual이나 CRSP return과 대규모 join query로 즉시 합치지 않는다.

실행 직전 확인:

- 현재 WRDS schema/table name
- `lpermno`, `lpermco`, `liid`, `linkdt`, `linkenddt`, `linktype`, `linkprim` 존재
- open-ended `linkenddt` coding
- 승인할 linktype/linkprim 조합

## 8. CRSP Daily

### Dataset C2: security returns

CRSP의 최신 CIZ daily stock source를 사용한다. 공식 WRDS macro 기준 table 후보는 `crsp.dsf_v2`이고 다음 CIZ 필드는 공개 문서에서 확인됐다.

| Requirement | Verified CIZ field | Legacy-compatible name |
| --- | --- | --- |
| Security ID | `permno` | `PERMNO` |
| Trading date | `dlycaldt` | `DATE` |
| Total return | `dlyret` | `RET` |
| Ex-dividend return | `dlyretx` | `RETX` |
| Price | `dlyprc` | `PRC` |
| Volume | `dlyvol` | `VOL` |
| Market capitalization | `dlycap` | derived market cap |
| Price adjustment | `dlycumfacpr` | `CFACPR` |
| Share adjustment | `dlycumfacshr` | `CFACSHR` |

Security-history requirement:

- `permco`
- `cusip`/historical CUSIP
- ticker/trading symbol
- security-information effective dates
- primary exchange
- security/share/issuer type
- trading status and conditional type

CRSP CIZ security-history field names는 `stkSecurityInfoHist` 및 공식 CIZ-to-SIZ macro의 `secInfoStartDt`, `secInfoEndDt`, `PrimaryExch`, `SecurityType`, `SecuritySubType`, `ShareType`, `USIncFlg`, `IssuerType`, `TradingStatusFlg`, `ConditionalType`를 기준으로 하되 대소문자와 실제 table columns를 실행 전 확인한다.

### Delisting requirement — 필수

BHAR와 survivorship-bias 통제를 위해 delisting return과 delisting code는 optional이 아니다. Legacy schema의 검증된 이름은 `DLRET`, `DLSTCD`이며 CRSP 공식 문서는 delisting event를 별도 history로 정의한다. CIZ는 delisting convention과 table 구조가 legacy와 달라졌으므로 다음을 **VERIFY IN WRDS BEFORE RUN**으로 둔다.

- CIZ `dlyret`에 delisting return이 반영되는 정확한 규칙
- 별도 CIZ delisting return/code field 또는 event table 이름
- daily return과 delisting return을 중복 결합하지 않는 방법
- missing delisting return codes의 보존 방법

이 mapping을 확인하지 않은 상태에서는 BHAR용 CRSP query를 실행하지 않는다. Legacy 이름을 CIZ query에 추정해 넣지 않는다.

### Shares outstanding

`SHROUT`은 legacy에서 검증된 필드다. CIZ의 정확한 shares-outstanding field/table은 `VERIFY IN WRDS BEFORE RUN`으로 표시한다. `dlycap`이 있어도 raw shares requirement를 임의로 제거하지 않는다.

### Abnormal volume

Volume은 `collect now / analyze later`로 분류한다. Main DV는 아니지만 daily extraction의 추가 비용이 작고 후속 다운로드를 줄이므로 `dlyvol`을 보존한다. Abnormal-volume 분석 규칙은 이번 계약 범위 밖이다.

## 9. Market and factor data

### Dataset C3: CRSP market daily

WRDS의 CIZ macro가 사용하는 table 후보는 `crsp.wrds_dailyindexret_query`다.

- `dlycaldt`
- `vwretd`
- `ewretd`

Value-weighted와 equal-weighted market return을 모두 받는다. Primary benchmark는 아직 미확정이지만 두 series의 추가 비용은 작고 Market Model robustness를 재다운로드 없이 지원한다.

### Dataset D: Fama–French–Carhart daily factors — 별도 source

이 자료는 CRSP daily security table과 같은 source가 아니다. WRDS Fama-French factor dataset 또는 Kenneth French Data Library의 별도 daily files로 취급한다.

- `date`
- `mktrf` / `MKT-RF`
- `smb` / `SMB`
- `hml` / `HML`
- `umd` 또는 `mom` / momentum
- `rf` / `RF`

WRDS 공개 macro는 `ff.factors_daily`와 `mktrf`, `smb`, `hml`, `umd`, `rf`를 사용한다. 실제 subscription schema를 확인하고 원천·release를 기록한다. Kenneth French Data Library를 사용할 경우 [공식 Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)의 daily 3-factor 및 daily momentum files를 별도 raw artifact로 저장한다.

## 10. Query date ranges

### Observed event range

- earliest filing date: **2020-02-18**
- latest filing date: **2026-03-02**

### CRSP one-acquisition target range

```text
2018-08-01 through 2027-04-30
```

근거:

- 시작일: earliest event보다 18개월 전 월초. 255 trading observations가 event 46 trading days 전에 끝나는 candidate estimation design과 holiday/missing-return buffer를 포괄한다.
- 종료일: latest event보다 13개월 후 월말. 최대 12개월 BHAR와 event-date alignment/delisting buffer를 포괄한다.

CRSP query는 가능한 경우 selected/candidate PERMNO로 제한하고 전체 CRSP universe를 내려받지 않는다. 다만 2027-04-30은 현재 시점보다 미래이므로 **최신 2025 report-year events의 완전한 12개월 BHAR를 지금 한 번에 받을 수 없다**. 실제 실행 전에 다음 중 하나를 승인해야 한다.

1. 완전한 one-shot acquisition을 위해 2027-04-30 자료가 제공될 때까지 기다린다.
2. 지금 2018-08-01부터 latest available date까지 immutable snapshot을 받고, 2027-04-30 이후 동일 contract로 append-only refresh를 한 번 수행한다.
3. 12개월 horizon을 제외한다. 단, 이는 BHAR specification 변경이므로 별도 연구 승인 사항이다.

### Estimation and event windows

- Primary estimation candidate: 255 trading observations ending 46 trading days before event (`[-300-ish, -46]`의 calendar-independent trading-observation 개념)
- Planned CAR: `[-1,+1]`, `[-2,+2]`, `[-3,+3]`
- Robustness candidate: `[-1,+2]`, `[-2,0]`, `[0,+2]`
- BHAR candidate: 1, 3, 6, 필요시 12개월

모든 event window는 calendar day가 아니라 CRSP trading day로 구현한다. Estimation model, minimum observations, BHAR start day 및 benchmark는 아직 미확정이지만 위 raw date range는 합리적인 후보를 재다운로드 없이 지원한다.

## 11. Raw artifact retention

새 디렉터리는 이번 작업에서 만들지 않았다. 실제 수집 시 기존 적절한 구조가 없으면 다음 개념을 사용한다.

```text
data/wrds/raw/
  compustat_annual.*
  compustat_quarterly_rdq.*
  ccm_links.*
  crsp_daily.*
  crsp_market_daily.*
  factor_daily.*

data/wrds/derived/
  identifier_crosswalk.*
  event_security_map.*
  event_return_panel.*
```

Raw artifact는 final panel에 즉시 merge하거나 덮어쓰지 않는다. 각 파일과 함께 다음을 보존한다.

- query text 또는 WRDS form specification
- schema/table 및 field list
- query date range
- extraction timestamp와 database update/release 정보
- row count, file size, SHA-256
- missing-value encoding과 timezone
- source snapshot/version

## 12. Audit fields

Derived linkage에는 최소 다음 필드를 보존한다.

- `cik_original`
- `cik_normalized`
- `gvkey_match_status`
- `gvkey_candidate_count`
- `gvkey_selection_reason`
- `ccm_candidate_count`
- `selected_permno`
- `selected_permco`
- `permno_selection_reason`
- `linktype`
- `linkprim`
- `linkdt`
- `linkenddt`
- `sec_filing_date`
- `sec_acceptance_datetime_raw`
- `sec_acceptance_datetime_et`
- `market_event_date`
- `event_date_alignment_reason`
- `event_date_alignment_status`

Regression dataset에서 일부를 제외하더라도 intermediate audit dataset에는 유지한다.

## 13. Sample attrition

다음 sample-flow contract를 사용한다.

```text
Initial core 10-K sample: 2,829
→ valid event metadata
→ CIK–GVKEY matched
→ valid-date CCM link
→ primary PERMNO selected
→ sufficient CRSP estimation history
→ Compustat annual matched
→ RDQ/confounding-event status available
→ final CAR sample
→ sufficient long-horizon return / delisting information
→ final BHAR sample
```

각 단계에서 `starting_n`, `passed_n`, `excluded_n`, `exclusion_reason`을 남긴다. 탈락 원인을 합쳐서 `unmatched` 하나로 기록하지 않는다.

## 14. Items requiring final approval

WRDS 실행 전에 다음을 확정하거나 확인해야 한다.

1. **CRSP snapshot strategy**: 지금 partial snapshot + 2027 append refresh인지, 완전한 12개월 BHAR maturity까지 기다릴지.
2. **CRSP CIZ schema**: `dsf_v2`, market index, shares outstanding 및 delisting fields/table의 실제 이름과 semantics.
3. **CCM derived filter**: 허용 `linktype`/`linkprim`과 multiple-PERMNO tie resolution.
4. **Acceptance timestamp fallback**: timestamp가 끝내 없는 event의 filing-date-only sensitivity 포함 여부.
5. **Market-close convention**: exchange session schedule, exact-close boundary 및 early-close 처리.
6. **Compustat optional sources**: Age, BusSeg, ForSeg, BigN을 첫 acquisition에 포함할지.
7. **Compustat date tolerance**: `report_date ↔ datadate`의 exact-match 실패 분포를 본 뒤 결정.
8. **Control timing**: same-report fiscal values와 lagged/pre-event values 중 primary specification.
9. **Earnings confound rule**: RDQ 거리의 exclusion/indicator threshold.
10. **Return models**: primary market benchmark, factor robustness, minimum estimation observations.
11. **BHAR specification**: start day, horizon, benchmark, missing/delisting treatment.

1~6과 실제 schema 확인은 acquisition execution 전 승인 대상이다. 7~11은 raw acquisition 범위를 바꾸지 않는 한 다운로드 후 확정할 수 있다.

## 15. Actual WRDS execution checklist

- [ ] Primary sample을 core 2,829건으로 고정
- [ ] 545 CIK를 10자리 문자열로 정규화하고 원문 보존
- [ ] SEC acceptance timestamp enrichment 계획 승인
- [ ] Compustat Annual table/fields와 2018-01-01~2025-12-31 범위 확인
- [ ] Compustat Quarterly `rdq` table/fields와 범위 확인
- [ ] CCM table, fields, open-ended link coding 확인
- [ ] CRSP CIZ daily table과 verified field list 확인
- [ ] CIZ delisting return/code 및 shares-outstanding mapping 확인
- [ ] CRSP market daily `vwretd`, `ewretd` 확인
- [ ] Factor source와 daily field names 확인
- [ ] CRSP snapshot/maturity strategy 승인
- [ ] Raw path, query manifest, hash 및 append-only policy 승인
- [ ] Sample attrition 및 linkage audit schema 승인
- [ ] Query preview의 예상 row count와 date boundaries 검토
- [ ] 실제 WRDS 실행을 별도 승인
