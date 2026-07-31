# 측정 방법 기록

## 기존 변수

기존 `ai_disclosure_flag`, Loughran–McDonald 범주, Brysbaert concreteness, `report_fog_index` 및 보고서 길이 변수는 기존 결과를 그대로 사용했다.

## 신규 시제 변수

`past_tense_count`, `present_tense_count`, `future_tense_count`는 spaCy POS tag를 기준으로 분류했다. 과거는 `VBD`, 현재는 `VBP`·`VBZ`, 미래는 `will`·`shall`·`'ll` 보조 표지를 사용했다. share의 분모는 분류 가능한 세 시제 count의 합이다.

`future_tense_count`와 `future_tense_share`는 `will`, `shall`, `'ll`에 기반한 제한적 미래 조동사 측정값이다. `plan to`, `intend to`, `expect to`, `aim to`, `anticipate`, `be going to`와 같은 기타 미래 지향 표현은 포함하지 않는다. 따라서 본 변수는 미래 지향 언어 전체가 아니라 제한된 미래 시제 표지의 사용 빈도로 해석해야 한다.

## 신규 수동태 변수

`passive_voice_sentence_count`는 spaCy dependency의 `auxpass` 또는 `nsubjpass` 관계가 있는 문장을 세었다. share의 분모는 spaCy가 분리한 문장 수이다. 문장 구조가 복잡한 경우 오탐·누락 가능성이 있다.

수동태 변수는 `auxpass` 또는 `nsubjpass` 관계에 의존한다. 복잡한 문장, 축약 구조, parser 오류로 인해 일부 수동태가 누락되거나 능동문이 잘못 분류될 가능성이 있다.

## AI 수준 변수

`ai_` 접두사가 있는 변수는 AI 직접 문장만을 대상으로 한다. AI 문장이 없으면 count는 0이지만 평균·share·Fog Index와 같이 유효 분모가 필요한 값은 결측이다.

## 결측 및 0

실제 count 0과 구조적 결측을 구분했다. 전년 관측이 없거나 분모가 0인 변화량·비율은 0으로 대체하지 않았다.

## 재현성

측정 실행은 `scripts/measure_extended_language_features.py`와 연도별 GitHub Actions artifact를 사용했다. 원본 HTML을 다시 수집하거나 기존 언어 측정값을 재계산하지 않았다.
