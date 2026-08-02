# 부록 A. 변수 정의

각 변수의 정의는 실제 패널 열, 측정 script 및 검증 규칙에 연결된다.

## 패널 A. 식별 변수

### `company_id` — 기업 안정 식별자

**상세 정의:** CIK 기반으로 연도별 firm-year를 연결하는 안정 기업 식별자이다. 회사명과 ticker가 변해도 패널 결합의 우선 키로 사용한다.

**분석 수준:** Firm-year identifier
**수식:** `company_id = stable identifier assigned from CIK`
**분자:** Not applicable
**분모:** Not applicable
**단위:** String identifier
**토큰 규칙:** Not applicable
**문장 규칙:** Not applicable
**사전/NLP:** SEC CIK identity mapping
**전처리:** String-preserved; no numeric arithmetic
**결측:** Missing identifier is a quality failure, not zero.
**0 처리:** Not applicable
**조건부 표본:** All firm-year observations
**Source column:** `company_id`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_2020_2025_language_panel.py`
**검증:** company_id + report_year duplicate count = 0
**해석:** Longitudinal firm key.
**한계:** Corporate succession or legal issuer changes may require manual identity review.

### `report_year` — 보고연도

**상세 정의:** 10-K의 reportDate 연도이며 filing year와 구분되는 연구 시간축이다.

**분석 수준:** Firm-year identifier
**수식:** `report_year = year(report_date)`
**분자:** Not applicable
**분모:** Not applicable
**단위:** Calendar year
**토큰 규칙:** Not applicable
**문장 규칙:** Not applicable
**사전/NLP:** SEC filing metadata
**전처리:** Integer cast after date validation
**결측:** Missing report year is invalid.
**0 처리:** Zero is invalid.
**조건부 표본:** All firm-year observations
**Source column:** `report_year`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_2020_2025_language_panel.py`
**검증:** Values must be in 2020–2025.
**해석:** Research year.
**한계:** It is not necessarily the SEC filing submission year.

## 패널 B. AI 커뮤니케이션 변수

### `ai_sentence_count` — AI 직접 문장 수

**상세 정의:** 기존 AI matcher가 추출한 비중복 AI 관련 문장의 firm-year별 개수이다. 전체 표본 평균은 미공시 firm-year의 0을 포함한다.

**분석 수준:** Firm-year and AI direct sentences
**수식:** `AI Sentence Countᵢₜ = Σₛ 1(sentence s contains a non-overlapping AI match)`
**분자:** Count of matched AI direct sentences
**분모:** 해당 없음
**단위:** Sentences
**토큰 규칙:** Existing AI dictionary and word-boundary matcher
**문장 규칙:** Existing sentence segmentation; each qualifying sentence counted once regardless of multiple matches.
**사전/NLP:** scripts/run_language_full_sample.py
**전처리:** Cleaned analysis text; overlapping term matches are resolved by existing matcher.
**결측:** Source missing remains missing.
**0 처리:** No qualifying sentence = 0.
**조건부 표본:** All firm-year observations
**Source column:** `ai_sentence_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/language_measurement_common.py, scripts/run_language_full_sample.py`
**검증:** Non-negative integer; sum agrees with AI sentence detail files where available.
**해석:** Textual AI communication intensity, not adoption.
**한계:** Counts depend on dictionary coverage, sentence extraction and reporting style.

### `ai_sentence_ratio` — AI 문장 비율

**상세 정의:** AI 직접 문장 수를 전체 유효 분석 문장 수로 나눈 비율이다.

**분석 수준:** Firm-year
**수식:** `AI Sentence Ratioᵢₜ = AI Direct Sentence Countᵢₜ / Total Eligible Sentence Countᵢₜ`
**분자:** ai_sentence_count
**분모:** total_analysis_sentence_count
**단위:** Proportion
**토큰 규칙:** Not applicable beyond source sentence count
**문장 규칙:** Eligible analysis sentences from existing extraction pipeline
**사전/NLP:** Existing full-sample language pipeline
**전처리:** No remeasurement; source ratio copied
**결측:** Missing when source denominator is unavailable.
**0 처리:** Zero AI sentences yield zero when denominator is positive.
**조건부 표본:** All firm-year observations
**Source column:** `ai_sentence_ratio, ai_sentence_count, total_analysis_sentence_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/run_language_full_sample.py`
**검증:** Non-negative and within [0, 1] when non-missing.
**해석:** Relative AI sentence intensity.
**한계:** Sensitive to section extraction and total sentence denominator.

### `ai_disclosure` — AI 공시 여부

**상세 정의:** 10-K 분석 본문에서 AI 관련 직접 문장이 한 개 이상 확인된 firm-year를 1로 표시하는 이진 변수이다. AI adoption 자체가 아니라 text-based AI communication proxy이다.

**분석 수준:** Firm-year
**수식:** `AI Disclosureᵢₜ = 1(ai_sentence_countᵢₜ ≥ 1)`
**분자:** AI direct sentence count ≥ 1
**분모:** 해당 없음
**단위:** Binary indicator
**토큰 규칙:** AI dictionary boundary matching in cleaned analysis text
**문장 규칙:** A sentence is direct AI-related when the existing AI matcher finds a non-overlapping dictionary match.
**사전/NLP:** Existing AI matcher and full-sample language pipeline
**전처리:** Existing cleaned sentence text and case-insensitive boundary matching
**결측:** Source missing remains missing.
**0 처리:** No AI direct sentence = 0.
**조건부 표본:** All firm-year observations; AI-level measures are conditional on ai_disclosure = 1.
**Source column:** `ai_disclosure, ai_disclosure_flag, ai_sentence_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/language_measurement_common.py, scripts/run_language_full_sample.py, scripts/build_extended_language_panel.py`
**검증:** ai_disclosure equals 1 exactly when ai_sentence_count >= 1, subject to source missing.
**해석:** Presence of AI-related communication in the filing.
**한계:** Keyword matching does not establish actual AI implementation or adoption.

## 패널 C. 구체성 변수

### `whole_report_concreteness` — 전체 보고서 구체성

**상세 정의:** SMART stopword 제거 후 Brysbaert concreteness lexicon에 유효하게 매칭된 전체 보고서 token의 평균 점수이다. exact match를 우선하고 unique Porter stem fallback을 사용하며 ambiguous collision은 제외한다.

**분석 수준:** Whole 10-K report
**수식:** `Concretenessᵢₜ = Σⱼ Ratingⱼ / Matched Eligible Token Countᵢₜ`
**분자:** Matched token concreteness ratings summed over valid matches
**분모:** report_concreteness_matched_token_count
**단위:** Brysbaert rating score
**토큰 규칙:** Alphabetic eligible tokens after SMART stopword removal
**문장 규칙:** All included analysis sentences
**사전/NLP:** Brysbaert lexicon; Porter stemming; exact then unique-stem fallback
**전처리:** Lowercase, SMART removal, Porter stemming; collision stems excluded
**결측:** Missing when no valid matched token denominator exists.
**0 처리:** No valid matched token is structural missing, not zero score.
**조건부 표본:** All firm-year observations with valid report matches
**Source column:** `whole_report_concreteness, report_concreteness_mean, report_concreteness_matched_token_count, report_concreteness_coverage`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/measure_linguistic_concreteness.py, scripts/build_extended_language_panel.py`
**검증:** Coverage is within [0, 1]; collision counts retained.
**해석:** Higher score indicates more concrete matched vocabulary under the lexicon.
**한계:** Lexicon coverage and contextual meaning may not capture document-level abstraction.

### `ai_concreteness` — AI 직접 문장 구체성

**상세 정의:** AI 직접 문장에 포함된 유효 token 중 Brysbaert 점수가 매칭된 token의 평균이다. AI 문장이 없는 firm-year에는 유효한 AI 분모가 없으므로 결측이다.

**분석 수준:** AI direct sentences
**수식:** `AI Concretenessᵢₜ = Σⱼ AI Matched Ratingⱼ / AI Matched Token Countᵢₜ`
**분자:** AI matched token ratings
**분모:** ai_concreteness_matched_token_count
**단위:** Brysbaert rating score
**토큰 규칙:** AI sentence eligible alphabetic tokens after SMART removal
**문장 규칙:** Existing AI direct sentence rows only
**사전/NLP:** Brysbaert lexicon with exact and unique-stem fallback
**전처리:** Same as whole-report concreteness; collision excluded
**결측:** AI sentence count zero or valid denominator zero => missing.
**0 처리:** No AI sentence is not treated as zero concreteness.
**조건부 표본:** AI disclosure firm-years only
**Source column:** `ai_concreteness, ai_concreteness_mean, ai_concreteness_matched_token_count, ai_concreteness_coverage`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/measure_linguistic_concreteness.py`
**검증:** AI coverage within [0, 1]; N reflects valid AI-level observations.
**해석:** Higher score indicates more concrete matched AI vocabulary.
**한계:** Conditional sample and sparse AI text can make the mean unstable.

## 패널 D. Loughran–McDonald 변수

### `lm_uncertainty_share` — LM uncertainty 비율

**상세 정의:** Loughran–McDonald financial dictionary의 Uncertainty 범주에 일치한 유효 token 수를 전체 유효 LM token 수로 나눈 상대 비중이다. 심리 상태가 아니라 금융공시 어휘의 비중이다.

**분석 수준:** Whole 10-K report
**수식:** `LM Uncertainty Shareᵢₜ = Uncertainty Token Countᵢₜ / Eligible LM Token Countᵢₜ`
**분자:** report_uncertainty_count
**분모:** report_total_eligible_word_count
**단위:** Proportion
**토큰 규칙:** Existing LM eligible tokenization and normalization
**문장 규칙:** All included report sentences
**사전/NLP:** Loughran–McDonald Master Dictionary
**전처리:** Existing lowercase/token normalization; category active rules
**결측:** Source missing or denominator zero remains missing.
**0 처리:** Zero category matches with positive denominator = 0.
**조건부 표본:** All valid report-level observations
**Source column:** `lm_uncertainty_share, report_uncertainty_ratio, report_uncertainty_count, report_total_eligible_word_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/run_language_full_sample.py, scripts/build_extended_language_panel.py`
**검증:** Non-missing proportion within [0, 1].
**해석:** Relative use of LM uncertainty vocabulary.
**한계:** Dictionary matching ignores local syntax, negation and polysemy.

## 패널 E. 시제 변수

### `past_tense_share` — 과거 시제 비율

**상세 정의:** spaCy POS 결과에서 VBD로 분류된 동사 수를 past, present, future 시제 count 합으로 나눈 비율이다.

**분석 수준:** Whole 10-K report
**수식:** `Past Shareᵢₜ = Past Countᵢₜ / (Past + Present + Future Count)ᵢₜ`
**분자:** past_tense_count (VBD)
**분모:** finite_verb_count
**단위:** Proportion
**토큰 규칙:** spaCy token/POS output
**문장 규칙:** spaCy sentence segmentation over analysis text
**사전/NLP:** spaCy 3.8.7 with en_core_web_sm 3.8.0
**전처리:** Existing cleaned text, chunked NLP processing
**결측:** Denominator zero => missing.
**0 처리:** Zero count retained when denominator is positive.
**조건부 표본:** All firm-year observations with finite-verb denominator
**Source column:** `past_tense_share, past_tense_count, finite_verb_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/measure_extended_language_features.py`
**검증:** Share within [0, 1]; tense counts non-negative.
**해석:** Relative past-tense marker share, not narrative temporality in full.
**한계:** POS tagging and finite-verb rules can misclassify complex constructions.

### `present_tense_share` — 현재 시제 비율

**상세 정의:** spaCy POS 결과에서 VBP 또는 VBZ로 분류된 동사 수를 세 시제 count 합으로 나눈 비율이다.

**분석 수준:** Whole 10-K report
**수식:** `Present Shareᵢₜ = Present Countᵢₜ / (Past + Present + Future Count)ᵢₜ`
**분자:** present_tense_count (VBP + VBZ)
**분모:** finite_verb_count
**단위:** Proportion
**토큰 규칙:** spaCy POS tokens
**문장 규칙:** spaCy sentence segmentation
**사전/NLP:** spaCy 3.8.7 en_core_web_sm 3.8.0
**전처리:** Existing cleaned text and chunk processing
**결측:** Denominator zero => missing.
**0 처리:** Zero count retained when denominator is positive.
**조건부 표본:** All firm-year observations with finite-verb denominator
**Source column:** `present_tense_share, present_tense_count, finite_verb_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/measure_extended_language_features.py`
**검증:** Share within [0, 1].
**해석:** Relative present-tense marker share.
**한계:** Not a comprehensive measure of present-oriented managerial language.

### `future_tense_share` — 미래 시제 비율

**상세 정의:** will, shall, 'll 미래 보조 표지 count를 세 시제 count 합으로 나눈 제한적 미래 시제 지표이다. plan to, intend to, expect to, aim to, anticipate, be going to는 포함하지 않는다.

**분석 수준:** Whole 10-K report
**수식:** `Future Shareᵢₜ = Future Marker Countᵢₜ / (Past + Present + Future Count)ᵢₜ`
**분자:** future_tense_count (will/shall/'ll markers)
**분모:** finite_verb_count
**단위:** Proportion
**토큰 규칙:** Lowercase/lemma rule implemented in measurement script
**문장 규칙:** spaCy sentence segmentation
**사전/NLP:** spaCy 3.8.7 en_core_web_sm 3.8.0
**전처리:** Existing cleaned text and marker matching
**결측:** Denominator zero => missing.
**0 처리:** Zero marker count retained when denominator is positive.
**조건부 표본:** All firm-year observations with finite-verb denominator
**Source column:** `future_tense_share, future_tense_count, finite_verb_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/measure_extended_language_features.py`
**검증:** Share within [0, 1].
**해석:** Limited future-modal marker usage, not all future orientation.
**한계:** Other future-oriented constructions are omitted.

## 패널 F. 수동태 변수

### `passive_voice_sentence_share` — 수동태 문장 비율

**상세 정의:** spaCy dependency parse에서 auxpass 또는 nsubjpass 관계가 하나 이상 있는 문장을 수동태로 표시하고 전체 spaCy 문장 수로 나눈다. 한 문장에 여러 관계가 있어도 한 문장으로 센다.

**분석 수준:** Whole 10-K report
**수식:** `Passive Shareᵢₜ = Passive Sentence Countᵢₜ / Parsed Sentence Countᵢₜ`
**분자:** passive_voice_sentence_count
**분모:** spacy_sentence_count
**단위:** Proportion
**토큰 규칙:** spaCy dependency tokens
**문장 규칙:** spaCy sentence boundaries
**사전/NLP:** spaCy dependency parser; auxpass/nsubjpass
**전처리:** Existing cleaned text and chunked processing
**결측:** Sentence denominator zero => missing.
**0 처리:** No passive relation with positive denominator = 0.
**조건부 표본:** All parsed report observations
**Source column:** `passive_voice_sentence_share, passive_voice_sentence_count, spacy_sentence_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/measure_extended_language_features.py`
**검증:** Share within [0, 1].
**해석:** Parser-defined passive sentence prevalence.
**한계:** Parser errors, reduced clauses and complex coordination can cause false negatives or positives.

## 패널 G. 가독성 변수

### `fog_index` — Gunning Fog Index

**상세 정의:** 정제된 분석 텍스트의 유효 단어·문장 수와 결정론적 음절 휴리스틱으로 복잡 단어 비율을 계산해 문장 길이와 결합한 가독성 지수이다.

**분석 수준:** Whole 10-K report
**수식:** `Fogᵢₜ = 0.4 × [(Wordsᵢₜ / Sentencesᵢₜ) + 100 × (ComplexWordsᵢₜ / Wordsᵢₜ)]`
**분자:** Eligible words; words with count_syllables(word) >= 3
**분모:** Eligible non-empty sentences; eligible words
**단위:** Index score
**토큰 규칙:** language_measurement_common.WORD_RE tokens containing alphabetic characters
**문장 규칙:** Non-empty extracted analysis sentences
**사전/NLP:** scripts/language_measurement_common.py readability()
**전처리:** HTML extraction output; punctuation excluded by WORD_RE; deterministic vowel-group syllable heuristic; terminal e rule
**결측:** Missing when sentence or word denominator is zero.
**0 처리:** Zero complex words with positive words = zero complex-word ratio.
**조건부 표본:** All firm-year observations with valid report text
**Source column:** `fog_index, report_fog_index`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/language_measurement_common.py, scripts/measure_report_level_controls.py`
**검증:** Finite numeric index; source status valid.
**해석:** Higher values indicate greater surface complexity under this heuristic.
**한계:** Does not directly measure information quality; financial/legal terminology can be treated as complex.

## 패널 H. 어휘 통제변수

### `numeric_token_share` — 숫자 token 비율

**상세 정의:** 정규식 token 중 integer, decimal, comma-number 또는 percentage 형태로 분류된 numeric token의 비율이다.

**분석 수준:** Whole 10-K report
**수식:** `Numeric Shareᵢₜ = Numeric Token Countᵢₜ / All Token Countᵢₜ`
**분자:** Tokens matching numeric pattern
**분모:** All WORD_RE tokens
**단위:** Proportion
**토큰 규칙:** WORD_RE with numeric pattern "\d+(?:[.,]\d+)*%?"
**문장 규칙:** All included analysis sentences
**사전/NLP:** language_measurement_common.numeric_token_ratio()
**전처리:** Existing cleaned text; no external numeric parser
**결측:** Zero total tokens => missing.
**0 처리:** No numeric token with positive total tokens = 0.
**조건부 표본:** All valid report observations
**Source column:** `numeric_token_share, report_numeric_token_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/measure_report_level_controls.py, scripts/language_measurement_common.py`
**검증:** Share within [0, 1].
**해석:** Relative prevalence of numeric token forms.
**한계:** Regex categories do not capture all dates, currencies or context.

## 패널 I. 패널 구조 및 파생 변수

### `source_company_id` — Source Company Id

**상세 정의:** source_company_id is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `source_company_id = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `source_company_id`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `sample_order` — Sample Order

**상세 정의:** sample_order is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `sample_order = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `sample_order`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `batch_id` — Batch Id

**상세 정의:** batch_id is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `batch_id = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `batch_id`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_date` — Report Date

**상세 정의:** report_date is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_date = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_date`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `form` — Form

**상세 정의:** form is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `form = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `form`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `r2_object_key` — R2 Object Key

**상세 정의:** r2_object_key is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `r2_object_key = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `r2_object_key`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `cik` — Cik

**상세 정의:** cik is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `cik = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `cik`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ticker` — Ticker

**상세 정의:** ticker is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ticker = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ticker`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `company_name` — Company Name

**상세 정의:** company_name is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `company_name = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `company_name`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `accession_number` — Accession Number

**상세 정의:** accession_number is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `accession_number = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `accession_number`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `filing_date` — Filing Date

**상세 정의:** filing_date is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `filing_date = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `filing_date`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `parser_version` — Parser Version

**상세 정의:** parser_version is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `parser_version = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `parser_version`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `language_measurement_version` — Language Measurement Version

**상세 정의:** language_measurement_version is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `language_measurement_version = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `language_measurement_version`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_disclosure_binary` — Ai Disclosure Binary

**상세 정의:** ai_disclosure_binary is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_disclosure_binary = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_disclosure_binary`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_term_count` — Ai Term Count

**상세 정의:** ai_term_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_term_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_term_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_terms_per_1000_words` — Ai Terms Per 1000 Words

**상세 정의:** ai_terms_per_1000_words is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_terms_per_1000_words = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_terms_per_1000_words`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `total_analysis_word_count` — Total Analysis Word Count

**상세 정의:** total_analysis_word_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `total_analysis_word_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `total_analysis_word_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `total_analysis_sentence_count` — Total Analysis Sentence Count

**상세 정의:** total_analysis_sentence_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `total_analysis_sentence_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `total_analysis_sentence_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_detection_status` — Ai Detection Status

**상세 정의:** ai_detection_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_detection_status = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_detection_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_uncertainty_count` — Ai Uncertainty Count

**상세 정의:** ai_uncertainty_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_uncertainty_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_uncertainty_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_uncertainty_ratio` — Ai Uncertainty Ratio

**상세 정의:** ai_uncertainty_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_uncertainty_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_uncertainty_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_litigious_count` — Ai Litigious Count

**상세 정의:** ai_litigious_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_litigious_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_litigious_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_litigious_ratio` — Ai Litigious Ratio

**상세 정의:** ai_litigious_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_litigious_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_litigious_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_weak_modal_count` — Ai Weak Modal Count

**상세 정의:** ai_weak_modal_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_weak_modal_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_weak_modal_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_weak_modal_ratio` — Ai Weak Modal Ratio

**상세 정의:** ai_weak_modal_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_weak_modal_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_weak_modal_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_strong_modal_count` — Ai Strong Modal Count

**상세 정의:** ai_strong_modal_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_strong_modal_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_strong_modal_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_strong_modal_ratio` — Ai Strong Modal Ratio

**상세 정의:** ai_strong_modal_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_strong_modal_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_strong_modal_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_constraining_count` — Ai Constraining Count

**상세 정의:** ai_constraining_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_constraining_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_constraining_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_constraining_ratio` — Ai Constraining Ratio

**상세 정의:** ai_constraining_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_constraining_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_constraining_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_total_eligible_word_count` — Ai Total Eligible Word Count

**상세 정의:** ai_total_eligible_word_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_total_eligible_word_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_total_eligible_word_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `uncertainty_status` — Uncertainty Status

**상세 정의:** uncertainty_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `uncertainty_status = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `uncertainty_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_positive_count` — Ai Positive Count

**상세 정의:** ai_positive_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_positive_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_positive_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_negative_count` — Ai Negative Count

**상세 정의:** ai_negative_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_negative_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_negative_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_positive_ratio` — Ai Positive Ratio

**상세 정의:** ai_positive_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_positive_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_positive_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_negative_ratio` — Ai Negative Ratio

**상세 정의:** ai_negative_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_negative_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_negative_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_net_tone` — Ai Net Tone

**상세 정의:** ai_net_tone is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_net_tone = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_net_tone`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_sentiment_word_coverage` — Ai Sentiment Word Coverage

**상세 정의:** ai_sentiment_word_coverage is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_sentiment_word_coverage = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_sentiment_word_coverage`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_net_tone_by_words` — Ai Net Tone By Words

**상세 정의:** ai_net_tone_by_words is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_net_tone_by_words = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_net_tone_by_words`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_total_lm_matched_word_count` — Ai Total Lm Matched Word Count

**상세 정의:** ai_total_lm_matched_word_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_total_lm_matched_word_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_total_lm_matched_word_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `sentiment_status` — Sentiment Status

**상세 정의:** sentiment_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `sentiment_status = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `sentiment_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_mean` — Ai Concreteness Mean

**상세 정의:** ai_concreteness_mean is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_mean = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_mean`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_median` — Ai Concreteness Median

**상세 정의:** ai_concreteness_median is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_median = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_median`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_standard_deviation` — Ai Concreteness Standard Deviation

**상세 정의:** ai_concreteness_standard_deviation is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_standard_deviation = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_standard_deviation`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_min` — Ai Concreteness Min

**상세 정의:** ai_concreteness_min is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_min = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_min`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_max` — Ai Concreteness Max

**상세 정의:** ai_concreteness_max is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_max = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_max`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_matched_token_count` — Ai Concreteness Matched Token Count

**상세 정의:** ai_concreteness_matched_token_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_matched_token_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_matched_token_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_eligible_token_count` — Ai Concreteness Eligible Token Count

**상세 정의:** ai_concreteness_eligible_token_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_eligible_token_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_eligible_token_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_unmatched_token_count` — Ai Concreteness Unmatched Token Count

**상세 정의:** ai_concreteness_unmatched_token_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_unmatched_token_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_unmatched_token_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_coverage` — Ai Concreteness Coverage

**상세 정의:** ai_concreteness_coverage is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_coverage = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_coverage`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_unique_dictionary_entries` — Ai Concreteness Unique Dictionary Entries

**상세 정의:** ai_concreteness_unique_dictionary_entries is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_unique_dictionary_entries = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_unique_dictionary_entries`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_stem_collision_count` — Ai Concreteness Stem Collision Count

**상세 정의:** ai_concreteness_stem_collision_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_stem_collision_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_stem_collision_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_status` — Ai Concreteness Status

**상세 정의:** ai_concreteness_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_status = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_mean` — Report Concreteness Mean

**상세 정의:** report_concreteness_mean is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_mean = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_mean`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_median` — Report Concreteness Median

**상세 정의:** report_concreteness_median is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_median = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_median`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_standard_deviation` — Report Concreteness Standard Deviation

**상세 정의:** report_concreteness_standard_deviation is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_standard_deviation = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_standard_deviation`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_min` — Report Concreteness Min

**상세 정의:** report_concreteness_min is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_min = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_min`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_max` — Report Concreteness Max

**상세 정의:** report_concreteness_max is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_max = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_max`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_matched_token_count` — Report Concreteness Matched Token Count

**상세 정의:** report_concreteness_matched_token_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_matched_token_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_matched_token_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_eligible_token_count` — Report Concreteness Eligible Token Count

**상세 정의:** report_concreteness_eligible_token_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_eligible_token_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_eligible_token_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_unmatched_token_count` — Report Concreteness Unmatched Token Count

**상세 정의:** report_concreteness_unmatched_token_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_unmatched_token_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_unmatched_token_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_coverage` — Report Concreteness Coverage

**상세 정의:** report_concreteness_coverage is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_coverage = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_coverage`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_unique_dictionary_entries` — Report Concreteness Unique Dictionary Entries

**상세 정의:** report_concreteness_unique_dictionary_entries is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_unique_dictionary_entries = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_unique_dictionary_entries`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_stem_collision_count` — Report Concreteness Stem Collision Count

**상세 정의:** report_concreteness_stem_collision_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_stem_collision_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_stem_collision_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_status` — Report Concreteness Status

**상세 정의:** report_concreteness_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_status = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `log_report_word_count` — Log Report Word Count

**상세 정의:** log_report_word_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `log_report_word_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `log_report_word_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_sentence_count` — Report Sentence Count

**상세 정의:** report_sentence_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_sentence_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_sentence_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_paragraph_count` — Report Paragraph Count

**상세 정의:** report_paragraph_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_paragraph_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_paragraph_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_mean_sentence_length` — Report Mean Sentence Length

**상세 정의:** report_mean_sentence_length is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_mean_sentence_length = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_mean_sentence_length`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_fog_index` — Report Fog Index

**상세 정의:** report_fog_index is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_fog_index = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_fog_index`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_numeric_token_ratio` — Report Numeric Token Ratio

**상세 정의:** report_numeric_token_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_numeric_token_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_numeric_token_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_ai_term_count` — Report Ai Term Count

**상세 정의:** report_ai_term_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_ai_term_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_ai_term_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_ai_terms_per_1000_words` — Report Ai Terms Per 1000 Words

**상세 정의:** report_ai_terms_per_1000_words is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_ai_terms_per_1000_words = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_ai_terms_per_1000_words`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_table_text_word_count` — Report Table Text Word Count

**상세 정의:** report_table_text_word_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_table_text_word_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_table_text_word_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_table_text_ratio` — Report Table Text Ratio

**상세 정의:** report_table_text_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_table_text_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_table_text_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `source_html_bytes` — Source Html Bytes

**상세 정의:** source_html_bytes is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `source_html_bytes = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `source_html_bytes`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `analysis_text_bytes` — Analysis Text Bytes

**상세 정의:** analysis_text_bytes is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `analysis_text_bytes = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `analysis_text_bytes`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `analysis_text_to_html_ratio` — Analysis Text To Html Ratio

**상세 정의:** analysis_text_to_html_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `analysis_text_to_html_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `analysis_text_to_html_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_control_status` — Report Control Status

**상세 정의:** report_control_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_control_status = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_control_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_positive_count` — Report Positive Count

**상세 정의:** report_positive_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_positive_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_positive_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_negative_count` — Report Negative Count

**상세 정의:** report_negative_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_negative_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_negative_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_net_tone` — Report Net Tone

**상세 정의:** report_net_tone is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_net_tone = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_net_tone`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_uncertainty_count` — Report Uncertainty Count

**상세 정의:** report_uncertainty_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_uncertainty_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_uncertainty_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_uncertainty_ratio` — Report Uncertainty Ratio

**상세 정의:** report_uncertainty_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_uncertainty_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_uncertainty_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_weak_modal_count` — Report Weak Modal Count

**상세 정의:** report_weak_modal_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_weak_modal_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_weak_modal_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_weak_modal_ratio` — Report Weak Modal Ratio

**상세 정의:** report_weak_modal_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_weak_modal_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_weak_modal_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_strong_modal_count` — Report Strong Modal Count

**상세 정의:** report_strong_modal_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_strong_modal_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_strong_modal_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_strong_modal_ratio` — Report Strong Modal Ratio

**상세 정의:** report_strong_modal_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_strong_modal_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_strong_modal_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_litigious_count` — Report Litigious Count

**상세 정의:** report_litigious_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_litigious_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_litigious_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_litigious_ratio` — Report Litigious Ratio

**상세 정의:** report_litigious_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_litigious_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_litigious_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_constraining_count` — Report Constraining Count

**상세 정의:** report_constraining_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_constraining_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_constraining_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_constraining_ratio` — Report Constraining Ratio

**상세 정의:** report_constraining_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_constraining_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_constraining_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_forward_looking_count` — Report Forward Looking Count

**상세 정의:** report_forward_looking_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_forward_looking_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_forward_looking_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_forward_looking_ratio` — Report Forward Looking Ratio

**상세 정의:** report_forward_looking_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_forward_looking_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_forward_looking_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_positive_ratio` — Report Positive Ratio

**상세 정의:** report_positive_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_positive_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_positive_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_negative_ratio` — Report Negative Ratio

**상세 정의:** report_negative_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_negative_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_negative_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_net_tone_by_words` — Report Net Tone By Words

**상세 정의:** report_net_tone_by_words is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_net_tone_by_words = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_net_tone_by_words`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_sentiment_word_coverage` — Report Sentiment Word Coverage

**상세 정의:** report_sentiment_word_coverage is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_sentiment_word_coverage = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_sentiment_word_coverage`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_total_lm_matched_word_count` — Report Total Lm Matched Word Count

**상세 정의:** report_total_lm_matched_word_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_total_lm_matched_word_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_total_lm_matched_word_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_total_eligible_word_count` — Report Total Eligible Word Count

**상세 정의:** report_total_eligible_word_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_total_eligible_word_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_total_eligible_word_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `concreteness_status` — Concreteness Status

**상세 정의:** concreteness_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `concreteness_status = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `concreteness_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `lm_ai_status` — Lm Ai Status

**상세 정의:** lm_ai_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `lm_ai_status = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `lm_ai_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `lm_report_status` — Lm Report Status

**상세 정의:** lm_report_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `lm_report_status = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `lm_report_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `matching_strategy_version` — Matching Strategy Version

**상세 정의:** matching_strategy_version is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `matching_strategy_version = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `matching_strategy_version`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `concreteness_preprocessing_version` — Concreteness Preprocessing Version

**상세 정의:** concreteness_preprocessing_version is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `concreteness_preprocessing_version = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `concreteness_preprocessing_version`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `warning_count` — Warning Count

**상세 정의:** warning_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `warning_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `warning_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `has_single_ai_sentence_warning` — Has Single Ai Sentence Warning

**상세 정의:** has_single_ai_sentence_warning is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `has_single_ai_sentence_warning = source-defined indicator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Binary indicator
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `has_single_ai_sentence_warning`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `has_stem_collision_warning` — Has Stem Collision Warning

**상세 정의:** has_stem_collision_warning is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `has_stem_collision_warning = source-defined indicator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Binary indicator
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `has_stem_collision_warning`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `has_denominator_zero_warning` — Has Denominator Zero Warning

**상세 정의:** has_denominator_zero_warning is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `has_denominator_zero_warning = source-defined indicator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Binary indicator
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `has_denominator_zero_warning`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `has_extraction_warning` — Has Extraction Warning

**상세 정의:** has_extraction_warning is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `has_extraction_warning = source-defined indicator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Binary indicator
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `has_extraction_warning`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `has_any_warning` — Has Any Warning

**상세 정의:** has_any_warning is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `has_any_warning = source-defined indicator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Binary indicator
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `has_any_warning`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `has_failed_status` — Has Failed Status

**상세 정의:** has_failed_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `has_failed_status = source-defined indicator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Binary indicator
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `has_failed_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_disclosure_flag` — Ai Disclosure Flag

**상세 정의:** ai_disclosure_flag is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_disclosure_flag = source-defined indicator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Binary indicator
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_disclosure_flag`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `panel_start_year` — Panel Start Year

**상세 정의:** panel_start_year is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `panel_start_year = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `panel_start_year`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `panel_end_year` — Panel End Year

**상세 정의:** panel_end_year is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `panel_end_year = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `panel_end_year`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `panel_year_count` — Panel Year Count

**상세 정의:** panel_year_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `panel_year_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `panel_year_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `is_balanced_2020_2025` — Is Balanced 2020 2025

**상세 정의:** is_balanced_2020_2025 is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `is_balanced_2020_2025 = source-defined indicator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Binary indicator
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `is_balanced_2020_2025`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `has_gap_within_observed_period` — Has Gap Within Observed Period

**상세 정의:** has_gap_within_observed_period is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `has_gap_within_observed_period = source-defined indicator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Binary indicator
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `has_gap_within_observed_period`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ticker_changed_within_panel` — Ticker Changed Within Panel

**상세 정의:** ticker_changed_within_panel is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ticker_changed_within_panel = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ticker_changed_within_panel`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `company_name_changed_within_panel` — Company Name Changed Within Panel

**상세 정의:** company_name_changed_within_panel is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `company_name_changed_within_panel = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `company_name_changed_within_panel`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `cik_changed_within_panel` — Cik Changed Within Panel

**상세 정의:** cik_changed_within_panel is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `cik_changed_within_panel = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `cik_changed_within_panel`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `first_observed_year` — First Observed Year

**상세 정의:** first_observed_year is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `first_observed_year = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `first_observed_year`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `last_observed_year` — Last Observed Year

**상세 정의:** last_observed_year is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `last_observed_year = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `last_observed_year`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_disclosure_flag_lag1` — Ai Disclosure Flag Lag1

**상세 정의:** ai_disclosure_flag_lag1 is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_disclosure_flag_lag1 = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_disclosure_flag_lag1`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_disclosure_flag_change` — Ai Disclosure Flag Change

**상세 정의:** ai_disclosure_flag_change is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_disclosure_flag_change = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_disclosure_flag_change`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_sentence_count_lag1` — Ai Sentence Count Lag1

**상세 정의:** ai_sentence_count_lag1 is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_sentence_count_lag1 = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_sentence_count_lag1`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_sentence_count_change` — Ai Sentence Count Change

**상세 정의:** ai_sentence_count_change is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_sentence_count_change = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_sentence_count_change`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_mean_lag1` — Ai Concreteness Mean Lag1

**상세 정의:** ai_concreteness_mean_lag1 is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_mean_lag1 = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_mean_lag1`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_concreteness_mean_change` — Ai Concreteness Mean Change

**상세 정의:** ai_concreteness_mean_change is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_concreteness_mean_change = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_concreteness_mean_change`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_mean_lag1` — Report Concreteness Mean Lag1

**상세 정의:** report_concreteness_mean_lag1 is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_mean_lag1 = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_mean_lag1`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_concreteness_mean_change` — Report Concreteness Mean Change

**상세 정의:** report_concreteness_mean_change is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_concreteness_mean_change = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_concreteness_mean_change`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_positive_count_lag1` — Ai Positive Count Lag1

**상세 정의:** ai_positive_count_lag1 is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_positive_count_lag1 = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_positive_count_lag1`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_positive_count_change` — Ai Positive Count Change

**상세 정의:** ai_positive_count_change is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_positive_count_change = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_positive_count_change`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_negative_count_lag1` — Ai Negative Count Lag1

**상세 정의:** ai_negative_count_lag1 is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_negative_count_lag1 = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_negative_count_lag1`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_negative_count_change` — Ai Negative Count Change

**상세 정의:** ai_negative_count_change is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_negative_count_change = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_negative_count_change`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_uncertainty_count_lag1` — Ai Uncertainty Count Lag1

**상세 정의:** ai_uncertainty_count_lag1 is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_uncertainty_count_lag1 = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_uncertainty_count_lag1`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_uncertainty_count_change` — Ai Uncertainty Count Change

**상세 정의:** ai_uncertainty_count_change is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_uncertainty_count_change = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_uncertainty_count_change`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_positive_count_lag1` — Report Positive Count Lag1

**상세 정의:** report_positive_count_lag1 is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_positive_count_lag1 = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_positive_count_lag1`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_positive_count_change` — Report Positive Count Change

**상세 정의:** report_positive_count_change is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_positive_count_change = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_positive_count_change`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_negative_count_lag1` — Report Negative Count Lag1

**상세 정의:** report_negative_count_lag1 is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_negative_count_lag1 = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_negative_count_lag1`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_negative_count_change` — Report Negative Count Change

**상세 정의:** report_negative_count_change is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_negative_count_change = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_negative_count_change`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_uncertainty_count_lag1` — Report Uncertainty Count Lag1

**상세 정의:** report_uncertainty_count_lag1 is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_uncertainty_count_lag1 = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_uncertainty_count_lag1`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_uncertainty_count_change` — Report Uncertainty Count Change

**상세 정의:** report_uncertainty_count_change is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_uncertainty_count_change = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_uncertainty_count_change`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `past_tense_count` — Past Tense Count

**상세 정의:** past_tense_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `past_tense_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `past_tense_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `present_tense_count` — Present Tense Count

**상세 정의:** present_tense_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `present_tense_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `present_tense_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `future_tense_count` — Future Tense Count

**상세 정의:** future_tense_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `future_tense_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `future_tense_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `finite_verb_count` — Finite Verb Count

**상세 정의:** finite_verb_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `finite_verb_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `finite_verb_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `passive_voice_sentence_count` — Passive Voice Sentence Count

**상세 정의:** passive_voice_sentence_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `passive_voice_sentence_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `passive_voice_sentence_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `spacy_sentence_count` — Spacy Sentence Count

**상세 정의:** spacy_sentence_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `spacy_sentence_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `spacy_sentence_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_past_tense_count` — Ai Past Tense Count

**상세 정의:** ai_past_tense_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_past_tense_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_past_tense_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_present_tense_count` — Ai Present Tense Count

**상세 정의:** ai_present_tense_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_present_tense_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_present_tense_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_future_tense_count` — Ai Future Tense Count

**상세 정의:** ai_future_tense_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_future_tense_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_future_tense_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_finite_verb_count` — Ai Finite Verb Count

**상세 정의:** ai_finite_verb_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_finite_verb_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_finite_verb_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_past_tense_share` — Ai Past Tense Share

**상세 정의:** ai_past_tense_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_past_tense_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_past_tense_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_present_tense_share` — Ai Present Tense Share

**상세 정의:** ai_present_tense_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_present_tense_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_present_tense_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_future_tense_share` — Ai Future Tense Share

**상세 정의:** ai_future_tense_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_future_tense_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_future_tense_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_passive_voice_sentence_count` — Ai Passive Voice Sentence Count

**상세 정의:** ai_passive_voice_sentence_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_passive_voice_sentence_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_passive_voice_sentence_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_passive_voice_sentence_share` — Ai Passive Voice Sentence Share

**상세 정의:** ai_passive_voice_sentence_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_passive_voice_sentence_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_passive_voice_sentence_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_spacy_sentence_count` — Ai Spacy Sentence Count

**상세 정의:** ai_spacy_sentence_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_spacy_sentence_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_spacy_sentence_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `report_character_count` — Report Character Count

**상세 정의:** report_character_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `report_character_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `report_character_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `average_word_length` — Average Word Length

**상세 정의:** average_word_length is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `average_word_length = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `average_word_length`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `lexical_density` — Lexical Density

**상세 정의:** lexical_density is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `lexical_density = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `lexical_density`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `root_type_token_ratio` — Root Type Token Ratio

**상세 정의:** root_type_token_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `root_type_token_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `root_type_token_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `type_token_ratio` — Type Token Ratio

**상세 정의:** type_token_ratio is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `type_token_ratio = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `type_token_ratio`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `percentage_expression_count` — Percentage Expression Count

**상세 정의:** percentage_expression_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `percentage_expression_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `percentage_expression_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `currency_expression_count` — Currency Expression Count

**상세 정의:** currency_expression_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `currency_expression_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `currency_expression_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_word_count` — Ai Word Count

**상세 정의:** ai_word_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_word_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_word_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `log_ai_word_count` — Log Ai Word Count

**상세 정의:** log_ai_word_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `log_ai_word_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `log_ai_word_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_fog_index` — Ai Fog Index

**상세 정의:** ai_fog_index is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_fog_index = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_fog_index`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_average_sentence_length` — Ai Average Sentence Length

**상세 정의:** ai_average_sentence_length is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_average_sentence_length = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_average_sentence_length`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_complex_word_share` — Ai Complex Word Share

**상세 정의:** ai_complex_word_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_complex_word_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_complex_word_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `tense_measurement_status` — Tense Measurement Status

**상세 정의:** tense_measurement_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `tense_measurement_status = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `tense_measurement_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `passive_voice_measurement_status` — Passive Voice Measurement Status

**상세 정의:** passive_voice_measurement_status is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `passive_voice_measurement_status = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `passive_voice_measurement_status`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `dependency_model` — Dependency Model

**상세 정의:** dependency_model is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `dependency_model = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `dependency_model`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `dependency_model_version` — Dependency Model Version

**상세 정의:** dependency_model_version is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `dependency_model_version = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `dependency_model_version`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `extended_measurement_version` — Extended Measurement Version

**상세 정의:** extended_measurement_version is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `extended_measurement_version = copied source value`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Source value
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `extended_measurement_version`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `log1p_ai_sentence_count` — Log1P Ai Sentence Count

**상세 정의:** log1p_ai_sentence_count is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `log1p_ai_sentence_count = source-defined eligible unit count`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Count
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `log1p_ai_sentence_count`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `lm_positive_share` — Lm Positive Share

**상세 정의:** lm_positive_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `lm_positive_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `lm_positive_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `lm_negative_share` — Lm Negative Share

**상세 정의:** lm_negative_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `lm_negative_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `lm_negative_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `lm_litigious_share` — Lm Litigious Share

**상세 정의:** lm_litigious_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `lm_litigious_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `lm_litigious_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `lm_strong_modal_share` — Lm Strong Modal Share

**상세 정의:** lm_strong_modal_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `lm_strong_modal_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `lm_strong_modal_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `lm_weak_modal_share` — Lm Weak Modal Share

**상세 정의:** lm_weak_modal_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `lm_weak_modal_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `lm_weak_modal_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `lm_constraining_share` — Lm Constraining Share

**상세 정의:** lm_constraining_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `lm_constraining_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `lm_constraining_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_lm_positive_share` — Ai Lm Positive Share

**상세 정의:** ai_lm_positive_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_lm_positive_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_lm_positive_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_lm_negative_share` — Ai Lm Negative Share

**상세 정의:** ai_lm_negative_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_lm_negative_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_lm_negative_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_lm_uncertainty_share` — Ai Lm Uncertainty Share

**상세 정의:** ai_lm_uncertainty_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_lm_uncertainty_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_lm_uncertainty_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_lm_litigious_share` — Ai Lm Litigious Share

**상세 정의:** ai_lm_litigious_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_lm_litigious_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_lm_litigious_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_lm_strong_modal_share` — Ai Lm Strong Modal Share

**상세 정의:** ai_lm_strong_modal_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_lm_strong_modal_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_lm_strong_modal_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_lm_weak_modal_share` — Ai Lm Weak Modal Share

**상세 정의:** ai_lm_weak_modal_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_lm_weak_modal_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_lm_weak_modal_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.

### `ai_lm_constraining_share` — Ai Lm Constraining Share

**상세 정의:** ai_lm_constraining_share is retained from the validated extended panel without remeasurement.

**분석 수준:** Firm-year
**수식:** `ai_lm_constraining_share = source-defined numerator / source-defined denominator`
**분자:** Source-defined or not applicable
**분모:** Source-defined or not applicable
**단위:** Proportion
**토큰 규칙:** Inherited from source measurement.
**문장 규칙:** Inherited from source measurement.
**사전/NLP:** Existing source measurement
**전처리:** No transformation beyond serialization.
**결측:** 원자료의 결측값은 결측으로 유지한다.
**0 처리:** 원자료의 0은 0으로 유지한다.
**조건부 표본:** Source-defined sample
**Source column:** `ai_lm_constraining_share`
**Source dataset:** `analysis/descriptive_2020_2025/firm_year_language_extended.csv`
**Measurement script:** `scripts/build_extended_language_panel.py`
**검증:** 원자료 열의 존재와 결측 의미를 검증한다.
**해석:** Interpret according to the source variable dictionary.
**한계:** This generated generic description must be supplemented before publication if the variable is used as a primary construct.
