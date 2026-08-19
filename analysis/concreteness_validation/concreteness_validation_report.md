# Brysbaert Concreteness 전처리 강건성 검증

검증일: 2026-08-19

판정: **READY WITH DOCUMENTED LIMITATIONS**

## 검증 범위

이 검증은 기존 canonical 패널을 변경하지 않고 다음 자료와 구현을 재사용했다.

- canonical 실행 경로: `scripts/run_yearly_10k_batch_core.py` → `scripts/run_language_full_sample.py`
- Concreteness 공통 규칙: `scripts/measure_linguistic_concreteness.py`
- SMART loader: `scripts/load_smart_stopwords.py`
- Brysbaert loader: `scripts/load_brysbaert_concreteness_dictionary.py`
- 사전: Brysbaert et al. (2014) 공식 supplementary XLSX에서 검증한 39,954개 항목(단일어 37,058개, 두 단어 표현 2,896개)
- 측정 버전: language `0.3.0`, preprocessing `baek-smart-porter-1.0.0`, matching `exact-then-unique-porter-1.0.0`
- 민감도 표본: 2025 S&P 500에서 sector-proportional fixed-seed 방식으로 선정한 기존 `pilot_100` 정제 본문 100건

민감도 계산은 이미 정제된 41,311,739바이트의 분석 본문에 canonical 정규식 tokenization만 적용했다. raw HTML 추출, 문장분할, 2,829건 전체 NLP 및 canonical 산출물 재생성은 수행하지 않았다. 표본 100건의 canonical 점수는 저장된 결과와 최대 절대차 `1.11e-14`, coverage는 최대 절대차 `0`으로 재현됐다.

## Table A. Method equivalence

| Component | Current Python | Reference method | Match status |
|---|---|---|---|
| Dictionary | 공식 Brysbaert XLSX를 검증한 39,954개 항목 | Brysbaert et al. (2014) lexicon | 일치 |
| Stopwords | tidytext 0.3.1의 SMART 571행, 570고유 항목 | Baek, Ihm, and Kang Appendix는 SMART 1,149개로 기술 | **부분 일치·원문 구현 미확정** |
| Stemming | NLTK 3.10.0 `PorterStemmer(ORIGINAL_ALGORITHM)` | R SnowballC 0.7.0 `wordStem(language="porter")` | 검증 범위에서 완전 일치 |
| Matching | 원형 exact 우선 → unique stem fallback → ambiguous stem unmatched | stopword 제거·Porter stemming·Brysbaert matching; collision 세부 규칙은 저장소 근거로 확정 불가 | **부분 일치** |
| Denominator | 매칭된 token score의 산술평균 | 매칭된 단어의 concreteness score 평균 | 일치 |

### SMART 1,149 해석

고정된 tidytext 0.3.1 RDA에는 총 1,149행이 있지만 구성은 SMART 571행, onix 404행, snowball 174행이다. SMART의 `would` 중복을 제거하면 570고유 항목이고, 세 lexicon을 합치면 728고유 항목이다. 따라서 현재 loader가 SMART 부분집합을 잘못 읽는 오류는 없다.

다만 저장소에 보존된 논문 설명만으로는 저자가 실제 코드에서 (A) 전체 1,149행, (B) SMART 부분집합, 또는 (C) 별도 SMART 목록 중 무엇을 사용했는지 확정할 수 없다. 판정은 **D: 현재 저장소 근거만으로 원문 구현 확정 불가**이다. 현재 구현은 검증 가능한 tidytext SMART 부분집합을 선택하며, 논문의 “SMART 1,149” 표현과 동일하다고 주장하지 않는다.

## Stopword sensitivity — 기존 2025 pilot 100건

S0와 S2는 모두 실제 SMART 570고유 항목이므로 동일하다. S1은 tidytext 세 lexicon의 전체 1,149행을 합친 728고유 항목이며, canonical보다 158고유 항목이 많다.

| Metric | S0/S2: SMART 570 | S1: 전체 728 |
|---|---:|---:|
| Valid N | 100 | 100 |
| Mean | 2.894817 | 2.898645 |
| SD | 0.046293 | 0.047853 |
| Mean coverage | 0.745253 | 0.740776 |
| Pearson vs. canonical | 1.000000 | 0.994175 |
| Spearman vs. canonical | 1.000000 | 0.990843 |
| Mean absolute difference | 0 | 0.005006 |
| Maximum absolute difference | 0 | 0.017576 |
| Bottom-decile retention | 100% | 80% |
| Top-decile retention | 100% | 90% |
| Quartile movement rate | 0% | 12% |

Stopword 해석 차이는 평균 수준에는 작고 순위 상관은 높지만, 극단 decile 구성까지 완전히 동일하지는 않다.

## Table B. Stemming equivalence

| Metric | Result |
|---|---:|
| Brysbaert 전체 entries | 39,954 |
| Stem 대상 단일어 entries | 37,058 |
| Same stem | 37,058 |
| Different stem | 0 |
| Difference % | 0.000% |

추가로 pilot 100건의 SMART 제거 후 고유 실제 token 32,009개도 두 구현의 stem이 모두 일치했고, dictionary matching outcome이 달라진 token은 0개였다. 두 stem index 모두 24,502개 stem, 17,546개 unique stem, 6,956개 collision stem을 생성했다.

## Table C. Concreteness sensitivity — 기존 2025 pilot 100건

C0는 canonical, C1은 stem fallback을 전혀 사용하지 않는 exact-only, C2는 canonical의 exact·unique fallback을 유지하되 ambiguous stem에 속한 dictionary entry score 평균을 부여한 비canonical 민감도 분석이다. C2는 대체 측정치의 채택을 의미하지 않는다.

| Measure | Canonical C0 | Exact-only C1 | Collision-mean C2 |
|---|---:|---:|---:|
| Valid N | 100 | 100 | 100 |
| Mean | 2.894817 | 2.874592 | 2.841555 |
| SD | 0.046293 | 0.048812 | 0.042741 |
| Mean coverage | 0.745253 | 0.670858 | 0.927665 |
| Pearson vs canonical | 1.000000 | 0.978196 | 0.981953 |
| Spearman vs canonical | 1.000000 | 0.978938 | 0.983102 |
| MAE | 0 | 0.020368 | 0.053263 |
| Max diff | 0 | 0.055334 | 0.083458 |

### Rank stability

| Measure | Exact-only C1 | Collision-mean C2 |
|---|---:|---:|
| Bottom-decile retention | 80% | 90% |
| Top-decile retention | 90% | 90% |
| Quartile movement rate | 16% | 14% |

순위는 높은 상관을 유지하지만 `0.99` 이상의 거의 완전한 안정성에는 미달한다. 특히 collision score를 임의 평균하는 C2는 canonical보다 평균을 `0.053263` 낮추므로, collision policy는 단순한 무영향 warning이 아니다. 반면 canonical은 모호한 score를 임의 부여하지 않는 보수적 규칙이고, exact match가 성공한 token에는 collision이 적용되지 않는다.

## Table D. Collision audit — 2020–2025 canonical panel

| Metric | Whole report | AI sentences |
|---|---:|---:|
| Valid score N | 2,829 | 1,659 |
| Collision firm-year | 2,829 | 1,635 |
| Collision token count | 15,863,344 | 74,731 |
| Coverage mean | 0.744653 | 0.736696 |

AI coverage는 1,660건에서 정의되지만 그중 1건은 matched score가 없어 valid score N이 1,659다. Collision count는 unique type 수가 아니라 **token occurrence 수**다. 이는 exact original-form match가 실패하고 ambiguous dictionary stem에 도달한 경우만 센다. Whole-report 기준 collision은 전체 eligible token의 18.03%, unmatched token의 69.97%다. 해당 token은 canonical 평균의 분자와 분모에서 제외된다.

## Coverage audit — 2020–2025 canonical panel

| Statistic | Coverage |
|---|---:|
| N | 2,829 |
| Mean | 0.744653 |
| SD | 0.016980 |
| P1 | 0.695507 |
| P5 | 0.711693 |
| P10 | 0.720632 |
| P25 | 0.735714 |
| Median | 0.747832 |
| P75 | 0.756248 |
| P90 | 0.763180 |
| P95 | 0.768191 |
| P99 | 0.776280 |
| Minimum | 0.685484 |

최저 coverage는 Ameren 2023년(`0.685484`)이며, 하위 사례에는 Ameren, Occidental Petroleum, Evergy, Alliant Energy, Altria가 포함된다. Coverage와 보고서 단어 수의 상관은 Pearson `-0.299441`, Spearman `-0.320600`이다. Coverage가 보고서 길이와 무관하지 않으므로 회귀에서는 기존 계획대로 word count를 통제하고 coverage 민감도도 확인할 필요가 있다.

## Table E. QC consistency

| Warning | QC flag N | Actual condition N | Match? |
|---|---:|---:|---|
| Stem collision | 2,729 | 2,829 | No, −100 |
| AI denominator zero | 1,165 | 1,169 | No, −4 |
| Single AI sentence | 302 | 308 | No, −6 |

불일치는 모두 2025 `pilot_100`에서 발생한다. `2025/sample_500/quality_check/warning_cases.csv`에는 `S2025-*` 행만 있고, pilot의 별도 warning artifact에는 stem 100건, denominator zero 4건, single AI sentence 6건이 있다. `scripts/build_2020_2025_language_panel.py`는 sample_500 warning artifact에서 QC flag를 만들지만, score와 status는 pilot을 포함한 company result에서 가져온다. 따라서 이는 **stale QC flag merge 문제**이며 Concreteness 값 계산 오류는 아니다. 이 검증에서는 보호 원칙에 따라 flag나 panel을 수정하지 않았다.

## 최종 판정

**READY WITH DOCUMENTED LIMITATIONS**

- 공식 Brysbaert 사전, matched-token denominator 및 canonical score 재현에는 오류가 확인되지 않았다.
- NLTK와 SnowballC는 전체 Brysbaert 단일어와 pilot 실제 고유 token에서 완전히 일치했다.
- SMART 1,149 문제는 loader 오류가 아니라 논문 표현과 tidytext 실제 구조의 불일치이며, 원문 실행 목록은 저장소 증거만으로 확정할 수 없다.
- Stopword 대안은 높은 score/rank 안정성을 보였다.
- Collision 대안도 높은 상관을 유지했지만 순위와 수준이 완전히 동일하지 않으므로 collision exclusion을 명시하고 회귀 단계에서 대안 민감도를 보고해야 한다.
- 2,829건 전체의 alternative score는 저장된 report-level token detail이 없어 raw text 재처리 없이 계산할 수 없었다. 이번 판정은 전체 panel의 canonical coverage·collision audit과 기존 sector-proportional pilot 100건의 score sensitivity를 결합한 결과다.

따라서 현재 `whole_report_concreteness`를 RQ2 main IV 후보로 유지할 수 있다. Canonical 값을 교체하지 않으며, 실제 회귀 전에 stopword/collision 대안의 민감도 범위와 stale QC flag를 분석 문서에 명시해야 한다.

## 보호 및 미실행 범위

- canonical CSV·Parquet·연도별 language result 변경: 없음
- SEC·WRDS·CRSP·Compustat·R2·Google Drive 접근: 없음
- raw HTML 추출·전체 language pipeline·historical backfill·web generation: 미실행
- 영구 validation script 또는 대규모 CSV 신규 생성: 없음
