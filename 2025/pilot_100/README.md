# 2025년 100개 기업 파일럿

이 폴더는 2025년 초기 100개 파일럿의 표본·SEC metadata·원문 추출 결과를 보존한다. 이후 2025년 300개·500개 확장 결과와 통합 패널은 각각의 `sample_300`·`sample_500` 및 `panel_2020_2025`에 저장한다.

## 현재 상태

- 파일럿 표본: 100개
- SEC primary HTML 수집: 완료
- 본문·문단·문장 추출: 완료
- 언어 측정: 기존 300개·500개 통합 결과에 포함
- 원본 HTML: Google Drive에 보관
- 이 폴더의 기존 파일: 읽기 전용

## 주요 경로

- `sample/final_analysis_sample_100.csv`: 파일럿 filing의 기준 입력
- `metadata/`: filing metadata와 소규모 감사 manifest
- `html/`: 과거 수집 결과와 SHA manifest
- `text/`: 본문·표·문단·문장 추출 결과
- `language_smoke_test/`: 초기 smoke test와 warning 기록

기존 smoke test 결과는 역사적 기록이며, 전체 2025년 분석 결과를 대표하는 표본으로 재해석하지 않는다.

## 보존 규칙

기존 파일럿 HTML, 추출 결과, 언어 결과 및 manifest를 삭제하거나 재생성하지 않는다. 새로운 historical 연도 처리는 이 폴더가 아닌 해당 연도 전용 manifest와 결과 디렉터리를 사용한다.
