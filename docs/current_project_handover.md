# S&P 500 10-K AI Language Research
# Current Project Handover

## 1. 연구 목적

- S&P 500 기업의 10-K에서 AI 관련 언어 특성을 분석한다.
- 현재 primary language measure는 textual concreteness다.
- AI 관련 직접 문장 수준과 전체 보고서 수준을 분리한다.
- 현재는 2025년 pilot 100 중 5개 기업 smoke test를 완료한 상태다.

## 2. 현재 Git 상태

- VERSION: `0.12.0`
- HEAD: `d7c5738581b1248954470baf3f43e11d8fdc3b8c`
- branch: `main`
- `origin/main`과 일치
- working tree clean

## 3. 완료된 주요 단계

### 3.1 2025년 HTML 수집

- 대상 100개
- HTML 100/100 성공
- commit: `e675522e12ce012224ed7ff2356c2c3d86bfc277`
- VERSION `0.8.0`

### 3.2 10-K text extraction

- 100/100 처리
- success 59
- warning 41
- failed 0
- total words 6,172,973
- paragraphs 141,796
- sentences 298,250
- commit: `4a6995ca02e50df07a40364053782abd0d5ad0b0`
- VERSION `0.9.0`

### 3.3 5개 기업 language smoke test

기업:

- NVDA
- HPE
- TECH
- WAT
- NSC

AI 관련 직접 문장:

- NVDA 137
- HPE 119
- TECH 0
- WAT 16
- NSC 1
- 총 273개

- commit: `3678213701e21d4185f562de04803869fd272c24`
- VERSION `0.10.0`

### 3.4 Loughran-McDonald 측정

- 공식 1993-2025 사전 사용
- AI 수준과 보고서 수준 측정 완료
- TECH AI 수준 missing
- LM 결과 정상 생성
- commit: `c5b2399cd197dc00d88e60e81e0262966241402a`
- VERSION `0.11.0`

### 3.5 Brysbaert 구체성 측정

공식 사전:

- 39,954행
- single word 37,058
- bigram 2,896
- 점수 범위 1.04-5.00

전처리:

- tokenization
- lowercase
- SMART stopword 제거
- Porter stemming
- Brysbaert matching
- matched score 평균

SMART:

- tidytext 0.3.1 공식 자료
- 571행
- `would` 중복
- 570개 고유어

Matching:

1. 원형 exact match
2. exact 실패 시 unique Porter stem fallback
3. collision stem 제외
4. collision score 평균 금지

AI 수준 구체성:

- NVDA mean 2.9936, coverage 0.6505
- HPE mean 2.8757, coverage 0.6651
- TECH missing
- WAT mean 2.5553, coverage 0.7007
- NSC mean 2.7013, coverage 0.8421

보고서 수준 구체성:

- NVDA 2.8954
- HPE 2.8689
- TECH 2.8676
- WAT 2.9003
- NSC 2.9014

- commit: `4578c7c6a50b45f9c94fdf201672f46fbb44b5ea`
- VERSION `0.12.0`
- 현재 판정: `partial_with_documented_warnings`

경고:

- 논문 SMART 1,149개와 실제 SMART subset 570개 차이
- Porter stem collision
- R SnowballC와 NLTK 직접 비교 미완료

### 3.6 R 및 SnowballC 환경 고정

- R 4.3.3
- SnowballC 0.7.0
- Ubuntu 24.04.4 LTS
- SnowballC archive SHA-256:
  `b10fee9d322f567a22c580b49b5d4ba1c86eae40a71794ca92552c726b3895f3`
- 설치 및 smoke test PASS
- commit: `d7c5738581b1248954470baf3f43e11d8fdc3b8c`
- VERSION `0.12.0` 유지

## 4. 현재 변수 상태

- AI mention extraction: `success`
- Loughran-McDonald: `success`
- textual concreteness: `partial_with_documented_warnings`
- time focusing: `blocked_liwc2015_license_required`
- passive voice: `blocked_model_missing`
- human review: `pending`
- R2: `deferred`
- Colab: `deferred`

## 5. 주요 주의사항

- 구체성이 primary language measure다.
- AI 문장 수준과 보고서 수준을 분리한다.
- TECH AI-level은 denominator zero이므로 missing이다.
- NSC는 AI 문장 1개이므로 warning이다.
- collision stem 점수는 평균하지 않는다.
- 미매칭 token에 임의 점수를 부여하지 않는다.
- 공식 사전 값은 논문 예시에 맞추어 수정하지 않는다.
- 계산은 full precision을 유지하고 표에서만 반올림한다.
- 원본 및 전체 파생 사전은 Git에서 제외한다.
- 5개 기업 결과로 효과를 추론하지 않는다.

## 6. 다음 작업 순서

1. R SnowballC 0.7.0과 NLTK Porter 비교
2. 차이가 있으면 5개 기업 구체성 재측정
3. 구체성 결과 연구자 검토
4. 31개 AI 문장 인간 검토
5. TECH 및 NSC 확인
6. 이후 100개 확장 여부 결정

현재 보류:

- LIWC2015 time focusing
- passive voice
- R2
- Colab

## 7. 주요 경로

- `2025/pilot_100/`
- `2025/pilot_100/language_smoke_test/`
- `2025/pilot_100/language_smoke_test/ai_related_sentences/`
- `2025/pilot_100/language_smoke_test/textual_concreteness/`
- `2025/pilot_100/language_smoke_test/combined_language_results/`
- `2025/pilot_100/language_smoke_test/quality_check/`
- `2025/pilot_100/language_smoke_test/reproducibility/`
- `references/dictionaries/loughran_mcdonald_master_dictionary/`
- `references/dictionaries/brysbaert_concreteness/`
- `references/software/r_snowballc_environment/`
- `scripts/`
- `tests/`
