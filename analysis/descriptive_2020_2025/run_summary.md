# 실행 결과 요약

## 실행 상태

실행 상태: `SUCCESS`(성공)

## 입력 데이터

입력 패널: `analysis/descriptive_2020_2025/firm_year_language_extended.parquet`
분석 기간: 2020–2025년

## 분석 표본

전체 firm-year: 2,829행, 고유 기업: 545개
연도별 행 수: [{'report_year': 2020, 'firm_year_count': 446}, {'report_year': 2021, 'firm_year_count': 462}, {'report_year': 2022, 'firm_year_count': 471}, {'report_year': 2023, 'firm_year_count': 479}, {'report_year': 2024, 'firm_year_count': 487}, {'report_year': 2025, 'firm_year_count': 484}]
AI 공시 firm-year: 1,660개, AI 미공시 firm-year: 1,169개

## 확장 패널 결과

기존 열은 변경하지 않고 신규 측정 변수만 결합했다. 상세 품질 수치는 `measurement_quality_summary.csv`에 기록했다.

## 기술통계 및 상관분석

기술통계표, 연도별 변화표, Pearson·Spearman 상관표 및 VIF표를 `tables/`에 생성했다.

## 그래프

연도별 핵심 변수와 AI disclosure 그룹별 그림을 `figures/`에 생성했다.

## 결측 및 warning

AI 문장 0개에 대한 AI 수준 평균·비율과 전년 부재 lag는 결측으로 유지했다. 기존 warning은 관측치 삭제 없이 보존했다.

## 원본 보존

기존 패널·연도별 결과·Google Drive 원본 HTML·R2 객체는 수정하지 않았다. SEC 재수집과 기존 정상 firm-year 재처리는 수행하지 않았다.
