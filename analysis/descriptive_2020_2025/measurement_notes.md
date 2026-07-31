# 측정 방법 기록

## 기존 변수

기존 `ai_disclosure_flag`, Loughran–McDonald 범주, Brysbaert concreteness, `report_fog_index` 및 보고서 길이 변수는 기존 결과를 그대로 사용했다.

## 신규 시제 변수

`past_tense_count`, `present_tense_count`, `future_tense_count`는 spaCy POS tag를 기준으로 분류했다. 과거는 `VBD`, 현재는 `VBP`·`VBZ`, 미래는 `will`·`shall`·`'ll` 보조 표지를 사용했다. share의 분모는 분류 가능한 세 시제 count의 합이다.

## 신규 수동태 변수

`passive_voice_sentence_count`는 spaCy dependency의 `auxpass` 또는 `nsubjpass` 관계가 있는 문장을 세었다. share의 분모는 spaCy가 분리한 문장 수이다. 문장 구조가 복잡한 경우 오탐·누락 가능성이 있다.

## AI 수준 변수

`ai_` 접두사가 있는 변수는 AI 직접 문장만을 대상으로 한다. AI 문장이 없으면 count는 0이지만 평균·share·Fog Index와 같이 유효 분모가 필요한 값은 결측이다.

## 결측 및 0

실제 count 0과 구조적 결측을 구분했다. 전년 관측이 없거나 분모가 0인 변화량·비율은 0으로 대체하지 않았다.

## 재현성

측정 실행은 `scripts/measure_extended_language_features.py`와 연도별 GitHub Actions artifact를 사용했다. 원본 HTML을 다시 수집하거나 기존 언어 측정값을 재계산하지 않았다.
