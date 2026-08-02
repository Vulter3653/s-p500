# 분석 방법

## 표본과 filing

기업 식별은 SEC CIK와 `company_id`를 우선하며, 정확한 `reportDate` 연도의 Form `10-K` primary document를 사용한다. amended filing과 부적격 form은 기존 표본 규칙에 따라 제외한다.

## 텍스트 측정

AI 문장은 저장소의 정규식·phrase matching 규칙으로 식별한다. Brysbaert concreteness는 SMART stopword 처리와 Porter stemming 기반 매칭을 사용한다. Loughran–McDonald 변수는 사전 일치 token을 적격 token으로 나누어 비율을 계산한다. tense와 passive voice는 spaCy POS/dependency 결과를 사용하며, Fog Index는 실제 readability 구현의 sentence·word·complex-word 규칙을 따른다.

## 통계

전체 및 연도별 기술통계, AI 공시·미공시 단순 비교, 연속 연도 동일 기업 변화, Pearson·Spearman 상관 및 VIF를 기존 CSV 산출물에서 읽는다. 유효 분모가 없는 AI 수준 변수는 구조적 결측으로 보존한다.
