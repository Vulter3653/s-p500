# 연구 대시보드 방법론

본 대시보드는 2020–2025년 S&P 500 기업의 Form `10-K` firm-year 분석 결과를 읽기 전용으로 제공한다. 표본, SEC filing 선정, 원문 수집, 텍스트 추출, 언어 측정 및 패널 병합은 저장소의 기존 script와 산출물을 따른다.

## 자료 흐름

연도별 manifest와 SEC metadata를 사용해 적격 primary HTML을 확정하고, 추출된 본문에서 AI 직접 문장, 구체성, Loughran–McDonald 범주, 시제, 수동태 및 가독성을 측정한다. 집계표와 확장 패널은 `scripts/generate_web_analysis_data.py`가 웹 정적 데이터로 변환한다.

## 해석 원칙

AI 관련 변수는 실제 AI adoption이 아니라 10-K 문서의 `text-based AI communication proxy`이다. 평균 차이와 상관관계는 기술통계 및 연관성 분석이며 인과효과를 의미하지 않는다.
