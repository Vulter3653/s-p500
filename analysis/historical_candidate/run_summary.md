# 실행 결과 요약

## 실행 상태

실행 상태: `SUCCESS`(성공)

## 입력 데이터

입력 패널: `panel_historical_candidate/firm_year_language_panel_full_candidate.parquet`
분석 기간: 2006–2025년
패널 성격: 원천과 적격 filing이 확인된 historical candidate panel

## 분석 표본

전체 관측치: 4,897 firm-year
고유 기업: 584개
균형 패널: 27개 기업
불균형 패널: 557개 기업
AI 공시 firm-year: 1,880개
AI 미공시 firm-year: 3,017개

|   보고연도 |   firm-year 수 |
|-------:|--------------:|
|   2006 |            12 |
|   2007 |            20 |
|   2008 |            35 |
|   2009 |            39 |
|   2010 |            46 |
|   2011 |            51 |
|   2012 |            69 |
|   2013 |            96 |
|   2014 |           136 |
|   2015 |           180 |
|   2016 |           248 |
|   2017 |           311 |
|   2018 |           384 |
|   2019 |           441 |
|   2020 |           446 |
|   2021 |           462 |
|   2022 |           471 |
|   2023 |           479 |
|   2024 |           487 |
|   2025 |           484 |

## 기존 변수 감사 결과

기존 패널 열과 측정값은 수정하지 않았다. 기존 열 변경 셀은 0개이다.

## 신규 변수

spaCy 기반 시제·수동태, AI Fog 및 텍스트 통제변수를 확장 패널에 결합했다. 재무·기업 통제변수는 이번 단계에서 수집하지 않았다.

## 품질관리 결과

`automation/historical_backfill/chain-state.json` 기준 candidate rows는 4,897개, chain status는 `completed`, validation은 `PASS`이다.

이 패널은 매년 완전한 S&P 500 전체 패널이 아니다. 2,829개 행에 대한 기존 품질통계는 2020–2025 핵심 패널의 결과이므로 이 historical summary에 적용하지 않는다.

## 생성 파일

기술통계표 15개, 핵심 그래프 10개(PNG·SVG) 및 보조 그래프·보고서를 생성했다.

## 원본 보존

기존 CSV·Parquet, Google Drive raw HTML, R2 객체와 기존 언어 측정 결과를 수정하지 않았다. 이번 문서 정정에서도 데이터와 분석값을 재계산하지 않았다.
