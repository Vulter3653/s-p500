# 연구 청사진: 10-K 언어와 주주 반응

Updated: 2026-08-19

이 문서는 현재 확정된 연구 방향과 아직 결정되지 않은 설계를 구분한다. 현재 웹 보고서의 기술통계·상관관계·단변량 비교는 완료된 기존 분석이며, 아래의 주주 반응 연구는 향후 실증분석 청사진이다.

## 상태 표기

- **확정**: 현재 연구 방향 또는 저장소에서 검증된 상태
- **보류**: 연구질문은 유지하지만 현재 우선순위에서 제외
- **예정**: 향후 자료 결합·검증·분석 후보이며 아직 실행하지 않음
- **임시**: 기존 탐색 결과로 보존하지만 최종 측정이나 최종 specification이 아님

## 최상위 Research Questions

### RQ1 — Tense

> 10-K report의 시제(past tense vs. future tense)의 차이가 주주들에게 어떻게 반응시키는가?

- 상태: **보류**
- 기존 spaCy 측정은 최종 측정이 아니라 `spaCy 기반 임시 tense 분석`이다.
- 현재 단계에서는 tense 알고리즘 수정, LIWC 재현 또는 새로운 tense 계산을 수행하지 않는다.

### RQ2 — Concreteness

> 10-K report의 구체성(concreteness)의 차이가 주주들에게 어떻게 반응시키는가?

- 상태: **현재 우선 진행**
- 핵심 관계: `10-K Concreteness → Shareholder Reaction`
- 주주 반응 자료와의 결합 및 회귀 specification은 아직 실행 전이다.

## 현재 데이터 상태

### 2020–2025 핵심 패널 — 확정

- 분석단위: 기업-연도
- 관측치: 2,829개 기업-연도
- 고유 기업: 545개
- AI 관련 공시: 1,660개
- AI 관련 문장: 19,577개
- 현재 공개 웹 보고서는 이 패널의 기존 기술통계·상관관계·단변량 비교만 표시한다.

### Historical candidate panel — 확정

- 기간: 2006–2025
- 관측치: 4,897개 기업-연도
- 고유 기업: 584개
- 2020–2025 기존 패널: 2,829개
- 2006–2019 historical additions: 2,068개
- historical backfill: 2019년부터 2006년까지 완료
- chain status: `completed`
- validation: `PASS`

이 패널은 매년 완전한 S&P 500 전체 패널이 아니다. 정확한 성격은 **원천과 적격 filing이 확인된 historical candidate panel**이다.

## Concreteness 측정 방향

### 핵심 정의 — 확정

Concreteness는 Brysbaert et al. (2014)의 concreteness lexicon에 기반한다.

```text
Concreteness =
Brysbaert dictionary에 매칭되는 단어들의 concreteness score 평균
```

측정 방향은 Baek, Ihm, and Kang의 mission concreteness 연구와 동일하게 유지한다.

### 전처리 동등성 — 부분 검증 완료

2026-08-19 중간 검증의 판정은 **READY WITH DOCUMENTED LIMITATIONS**이다. 상세 근거는 [`analysis/concreteness_validation/concreteness_validation_report.md`](../analysis/concreteness_validation/concreteness_validation_report.md)에 기록했다.

- SMART stopword loader는 tidytext 0.3.1의 실제 SMART 571행·570고유 항목을 정확히 사용한다. 논문의 `SMART 1,149` 표현은 tidytext 전체 행 수와 충돌하며, 원문 실행 목록은 현재 저장소 근거만으로 확정할 수 없다.
- NLTK 3.10.0 Porter와 R SnowballC 0.7.0은 Brysbaert 단일어 37,058개와 기존 2025 pilot 100건의 고유 실제 token 32,009개에서 stem 차이 0건이었다.
- 기존 pilot 100건에서 전체 tidytext stopword 대안의 canonical 대비 Spearman 상관은 0.990843이었다.
- exact-only 및 ambiguous-stem 평균 대안의 Spearman 상관은 각각 0.978938, 0.983102으로 높지만 완전 동등하지 않았다. canonical의 ambiguous-stem 제외 규칙과 후속 민감도 분석 필요성을 유지한다.
- 2020–2025 전체 2,829건의 report coverage 평균은 0.744653이고 최솟값은 0.685484다.
- 2025 pilot warning artifact가 sample_500 QC flag merge에서 제외돼 flag가 stale하지만, 저장된 score와 status의 계산 오류는 확인되지 않았다.

Canonical measurement는 변경하지 않는다. 전체 2,829건 alternative score의 재계산은 이번 검증 범위에서 수행하지 않았으며, 회귀 단계에서 이 제한과 대안 민감도를 문서화한다.

## Whole 10-K와 AI-related sentences — 탐색적 분석

교수 피드백에 따라 `Whole 10-K vs. AI-related sentences` 비교는 유지한다. 이는 전체 10-K와 AI 관련 언어의 차이를 이해하기 위한 보조적·탐색적 분석이며 최상위 Research Question은 아니다.

다음 선택은 아직 **미확정**이다.

- AI-related concreteness를 main IV로 사용할지
- whole-report concreteness를 main IV로 사용할지
- 두 측정치의 difference score를 사용할지

RQ2의 기본 관계는 `10-K concreteness → shareholder reaction`이다.

## Section-level analysis — 탐색적 확장 후보

- 상태: **exploratory / not yet included in main specification**
- 후보 section: Risk Factors, MD&A 등
- section별 차이가 실제로 관찰되는지 먼저 확인해야 한다.
- 변수 수가 과도하게 늘어날 수 있으므로 현재 main specification에는 포함하지 않는다.

이번 문서 갱신에서는 section extraction이나 재분석을 수행하지 않았다.

## Tense — 보류 및 임시 결과

### spaCy 기반 임시 tense 분석

기존 임시 규칙은 다음과 같다.

- Past: `VBD`
- Present: `VBP`, `VBZ`
- Future: 품사가 `AUX`인 `will`, `shall`, `'ll`, `’ll`

기존 값은 삭제하지 않고 **spaCy 기반 임시 분석 결과**로만 보존한다.

| 분석 범위 | Past | Present | Future |
| --- | ---: | ---: | ---: |
| 전체 10-K | 22.88% | 73.85% | 3.27% |
| AI 관련 문장 | 9.15% | 86.52% | 4.33% |

이 값은 확정 결과가 아니며 현재 단계에서 재계산하지 않는다.

### LIWC2015 방법론 참고 — 예정

Baek & Ihm의 방법은 LIWC2015의 `focus past`, `focus present`, `focus future`를 사용하고 다음 형태로 Time focusing을 구성한다.

```text
Time focusing = Past - (Present + Future)
```

이는 현재 spaCy 기반 임시 방식과 동일하지 않다. LIWC 재현 및 최종 tense 측정 선택은 보류 상태다.

## Passive voice — control 후보

- 상태: **최종 control로 미확정**
- 현재 위치: control variable 후보
- 향후 passive voice의 이론적 의미와 기존 연구 근거를 확인해야 한다.
- 기존 spaCy 기반 passive rule과 결과는 보존하되 이번 작업에서는 재계산하지 않는다.

## 향후 데이터 결합 — 예정

현재는 WRDS 수집 실행 단계가 아니라 청사진 작성 단계다.

향후 데이터 구조:

```text
10-K linguistic panel
+ Compustat firm-year controls
+ CRSP market return data
```

- 기본 분석단위: Firm-Year
- event date: 10-K filing date
- 식별자 연결 청사진: `CIK → GVKEY → PERMNO`
- ticker 또는 firm name 문자열만으로 최종 매칭하는 방식은 지양한다.

이번 문서 갱신에서는 WRDS, Compustat 또는 CRSP에 접속하거나 자료를 내려받지 않았다.

## 단기 Event Study — 예정

### Event date와 CAR

```text
t = 0 = 10-K filing date
AR_it = R_it - E(R_it)
CAR[t1,t2] = Σ AR_it
```

우선 계획된 단기 CAR event window:

- `CAR[-1,+1]`
- `CAR[-2,+2]`
- `CAR[-3,+3]`

위 구간은 BHAR window가 아니라 단기 CAR event window다.

Robustness 후보이며 아직 최종 확정되지 않은 구간:

- `[-1,+2]`
- `[-2,0]`
- `[0,+2]`

Expected return benchmark 후보:

- Market Model
- Fama-French-Carhart four-factor model 등

참고한 *Journal of Marketing*의 “Hands Off My Brand!” 연구는 Market Model, FF4 robustness, 255 trading-day estimation period, event 46 trading days 전 종료 방식을 사용했다. 현재 연구의 정확한 estimation window와 benchmark model은 아직 확정하지 않는다.

## 장기 Shareholder Reaction — 예정

장기 주주 반응은 BHAR로 측정할 계획이다.

```text
BHAR =
기업 buy-and-hold return
- benchmark buy-and-hold return
```

후보 horizon:

- 1개월
- 3개월
- 6개월
- 필요시 12개월

정확한 장기 window와 benchmark는 미확정이다. 단기 CAR 최대 window와 장기 BHAR가 겹치지 않도록 설계한다. 예를 들어 `CAR[-3,+3]`을 사용하면 장기 window를 `+4` 이후 시작하는 방식을 검토할 수 있으나, 이는 최종 specification이 아니다.

## Compustat control 후보 — 예정

우선 검토 후보:

- LnAssets / Firm Size
- Leverage
- MTB
- Loss
- Age
- Intangibles
- BusSeg
- ForSeg
- BigN
- Special Items

시장자료 기반 후보:

- Return volatility / Risk

위 변수를 모두 최종 회귀에 포함하는 것으로 확정하지 않는다. 최종 control set은 concreteness 연구, 10-K textual analysis 연구, marketing event-study 연구를 대조한 뒤 최소한으로 선정한다.

## Textual control 후보 — 예정

- Word count
- Fog Index
- Boilerplate
- Redundancy
- Specificity
- Stickiness
- Hard information mix
- Passive voice

`Specificity`와 `Concreteness`는 동일한 변수가 아니다.

- Specificity: NER 기반 entity density
- Concreteness: Brysbaert 기반 lexical semantic concreteness

두 개를 서로 대체하거나 혼동하지 않는다.

## Event-study validity 필수 후속 검토

아직 분석하지 않은 필수 검토사항:

- earnings announcement와 10-K filing date의 근접성
- overlapping/confounding corporate events
- M&A
- CEO change
- major litigation
- dividend announcement
- major product announcement
- overlapping firm observations
- BHAR benchmark
- delisting return
- long-term holding-period definition

특히 earnings announcement가 10-K filing event window에 포함되면 10-K linguistic information effect와 earnings news effect를 분리하기 어렵다.

## Empirical architecture

```text
S&P 500 constituents
→ SEC 10-K HTML
→ 10-K narrative extraction
→ Brysbaert-based Concreteness
→ 10-K Filing Date
→ CIK-GVKEY-PERMNO linking
→ Compustat controls + CRSP returns
→ Short-term CAR [-1,+1], [-2,+2], [-3,+3]
→ Long-term BHAR
→ Concreteness and Shareholder Reaction regression
→ Robustness analysis
```

Tense는 현재 이 pipeline에서 **보류** 상태다.

## 현재 작업과 미래 분석의 경계

- 완료: 기존 구성종목·10-K·언어 패널, historical candidate panel, 기술통계·상관관계·단변량 비교, 웹 보고서
- 보류: 최종 tense 측정과 RQ1 실증분석
- 예정: WRDS/Compustat/CRSP 결합, CAR·BHAR 계산, shareholder reaction 회귀, robustness 분석
- 미실행: 가상의 CAR·BHAR·Compustat 값 생성 및 웹 표시
