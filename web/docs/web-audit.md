# 웹 분석 대시보드 감사

이 문서는 웹 화면이 기존 분석 산출물을 읽기 전용으로 사용하는지 점검한 기록이다. 수치는 `analysis/descriptive_2020_2025/tables/`와 `firm_year_language_extended.csv`에서 `scripts/generate_web_analysis_data.py`가 생성한다.

## 감사 결과

- 통계 수치: React 원본에 직접 입력하지 않고 `web/public/data/analysis-summary.json`에서 불러온다.
- API 의존성: 별도 `/api/summary` endpoint 없이 정적 JSON을 사용한다.
- 변수 정의: `config/variable_definitions.yaml`과 실제 패널 열을 생성 시 검증한다.
- 조건부 평균: AI 수준 변수는 유효한 AI 공시 firm-year의 분모 규칙을 보존한다.
- 결측과 0: JSON 직렬화에서 구조적 결측과 실제 count 0을 구분한다.
- 재현성: source SHA-256, 생성 시각, Git commit을 `source-manifest.json`과 `build-metadata.json`에 기록한다.
- 제한: 대시보드의 연관성은 인과효과가 아니며, 변수별 한계는 변수 정의와 방법 문서에 연결한다.
