# 연구 대시보드 방법론

## 1. 연구설계

분석기간은 2020–2025년이며 관측 단위는 기업-보고연도(`firm-year`)이다. 각 행은 하나의 기업과 하나의 회계연도 `10-K` 보고서를 나타낸다. AI 변수는 실제 AI adoption이 아니라 보고서에 나타난 `text-based AI communication proxy`이다.

## 2. 연도별 S&P 500 표본 구축

연도별 구성 manifest와 유효일자를 사용해 연구 시점의 S&P 500 구성기업을 복원한다. 현재 구성목록을 과거 시점으로 역복원할 때 구성종목의 변경일과 CIK 매핑을 보존하며, 동일 CIK의 ticker 표기는 기업 수준에서 연결한다. 원천자료와 SHA-256은 연도별 manifest와 `data/processed/annual_constituents_manifest.json`에 기록한다. 관련 파일은 `docs/sample-definition.md`, `docs/constituent-data-method.md`, `scripts/build_annual_constituents.py`, `scripts/validate_annual_constituents.py`이다.

## 3. SEC 10-K filing 선정

SEC submissions metadata에서 정확한 `reportDate` 연도의 Form `10-K` primary document를 선택한다. `10-K/A`, `NT 10-K`, `8-K`, PDF annual report는 제외하며, CIK·accession 중복과 복수 적격 filing은 quality-check에 기록한다. filing date와 accession은 manifest의 재현성 필드로 보존한다.

## 4. 원문 HTML 수집과 보관

SEC 요청은 User-Agent와 속도 제한을 적용하고, response bytes·파일 크기·SHA-256을 manifest에 기록한다. 현재 Google Drive 기본 layout은 `<root>/<연도>/<번호>_<연도>_<기업명>_<SYMBOL>_<CIK>.html`이며 `legacy_nested`는 호환용이다. 원문은 Git에 포함하지 않고 웹에는 집계 결과만 제공한다.

## 5. HTML 정제와 텍스트 추출

`scripts/extract_10k_analysis_text.py`는 HTML parser를 통해 script/style와 hidden inline XBRL metadata를 제거하고 표·문단·문장을 분리한다. whitespace normalization과 section warning을 유지하며, 분석 본문과 표 텍스트의 처리 상태를 quality-check 파일에 연결한다.

## 6. AI 직접 문장 식별

`scripts/language_measurement_common.py`의 AI term list와 case-insensitive word-boundary matcher를 사용한다. 단일어와 phrase는 비중첩 방식으로 검색하며, AI 용어가 한 문장에 여러 번 나타나더라도 직접 문장 수는 문장 단위로 계산한다. accession 연결 상세는 AI sentence 산출물에 보존한다.

## 7. 언어 측정

구체성은 `scripts/measure_linguistic_concreteness.py`의 Brysbaert 사전, SMART stopword 제거, Porter stemming과 unique-stem fallback을 따른다. LM 범주는 Loughran–McDonald 사전의 유효 token 비율로 계산한다. tense와 passive voice는 `spaCy` POS·dependency 규칙을 사용하며, Fog와 문서 길이는 `scripts/measure_readability.py` 및 기존 확장 측정 script를 따른다. 모든 변수의 상세 수식은 `research-dashboard-variable-definitions.md`와 `config/variable_definitions.yaml`에 있다.

## 8. 패널 구성

`company_id + report_year`를 기본 1:1 merge key로 사용하고 CIK·accession 중복을 검증한다. 기존 열 hash와 행 수가 유지되는지 확인하며, AI 문장 수 0은 실제 0으로 유지하고 유효 분모가 없는 AI 수준 평균·비율은 구조적 결측으로 남긴다.

## 9. 통계 분석

전체·연도별 기술통계, AI 공시·미공시 Welch 비교, 표준화 평균 차이, 연도별 절대·상대 변화, 연속 연도 동일 기업 변화, Pearson·Spearman 상관 및 VIF를 `analysis/descriptive_2020_2025/tables/`에서 읽는다. 모든 결과는 기술통계 및 연관성 분석이며 인과효과를 의미하지 않는다.

## 10. 품질관리

생성기는 기간, 행 수, unique key, count 비음수, share 범위, Infinity, source column, source dataset 및 measurement script 존재를 자동 검증한다. 실패하면 JSON 생성을 중단한다.

## 11. 재현성

`scripts/generate_web_analysis_data.py`는 source file 경로·열·SHA-256, 생성 script, Git commit, VERSION, 생성 시각, 분석기간과 단위를 `web/public/data/source-manifest.json`에 기록한다.

## 12. 한계

불균형 패널, 연도 구성 효과, AI 공시 포화, 사전 coverage, stem collision, spaCy parser 오류, 제한된 미래 시제 표지와 Fog의 전문용어 민감성을 결과 해석에 반영해야 한다.
