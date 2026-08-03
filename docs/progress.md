# Project Progress and Session Handoff

## 2026-08-03 - historical branch push 및 workflow 입력 blocker

- 배포: `8ff545f35d5bbd7c9b0a802333fafde43f76715c`를 `origin/codex/historical-backfill-continuous`에 push했다. main에는 push·merge하지 않았다. (codex)
- 보류: continuous workflow는 실행하지 않았다. 현재 저장소에 필요한 `2019/sample_503/sample/final_analysis_sample_503.csv`가 없어 workflow input manifest가 불명확하며, partial 입력으로 실행하지 않았다. (codex)
- 다음 정확한 작업: 기존 artifact 또는 constituent manifest에서 2019 collection-ready sample manifest를 복구한 뒤, cache preflight가 동일 SEC source를 재사용하는 것을 확인하고 workflow를 1회 실행한다. (codex)

## 2026-08-03 - SEC metadata cache-first 복구 및 2019 constituent 검증

- 상태: 작업 시작 HEAD는 `296bea6`; 원격 runner HEAD는 `38a3f1086ac1cbb3dea8cc83244b360db24522dc`, 원격 historical branch HEAD는 `0b997b601e48234b565452c2951cb21512fdbb95`, 원격 main HEAD는 `cc162b21719fb1bf12c0dfaeab1818ad1d2c1d41`이다. `git fetch --all --prune`은 Codespaces의 `.git/FETCH_HEAD` 읽기 전용 제약으로 실행되지 않았다. 종료 당시 미커밋 4개 파일은 모두 복구되었고, 원격 historical branch 구현과 비교해 끝 개행 외 차이가 없었다. (codex)
- 변경: `build_annual_constituents.py`와 `build_full_historical_constituents.py`가 SEC ticker JSON을 cache-first로 선택하고 JSON 필수 필드를 검증한다. 유효 cache는 SHA 중복을 하나로 처리하며, cache가 없을 때만 `SEC_USER_AGENT`로 단일 요청한다. HTTP 403은 retryable false로 기록한다. (codex)
- 변경: continuous workflow가 SEC cache preflight를 수행하고, chain state에 source path·SHA-256·origin·network 여부·retrieved timestamp를 전달한다. candidate web generator가 입력 panel의 실제 source path/hash를 기록하도록 보완했다. (codex)
- 실행: `python scripts/build_full_historical_constituents.py --source-date 2026-07-24 --start-year 2019 --end-year 2019`를 실제 저장소 cache·raw source로 1회 실행했다. 2019 snapshot은 505 securities·501 company rows이며 SEC network request는 0회였다. (codex)
- 검증: 관련 pytest 10 passed, Python compile, workflow YAML parse 및 `git diff --check`가 통과했다. continuous GitHub Actions는 실행하지 않았고 R2·Google Drive write, main merge/push, 기존 2020–2025 panel/dashboard 변경은 0이다. (codex)
- 다음: `.git` 쓰기 권한이 있는 환경에서 변경을 기능 단위 commit하고 `codex/historical-backfill-continuous`에 push한 뒤, 동일 workflow를 1회 dry-run/승인 실행한다. (codex)

## 2026-08-02 - 503개 표본·6개 batch runner 일반화

- 변경: `scripts/run_yearly_10k_batch.py`에 `MAX_SAMPLE_SIZE=503`, `BATCH_SIZE=100`, `MAX_BATCH_COUNT=6`을 적용하고 전체 manifest의 중복·결측·Form·보고연도와 상한을 시작 시 검증한다. (codex)
- 변경: 503개 행을 100·100·100·100·100·3으로 원래 manifest 순서대로 분할하며 batch 6을 허용하고 batch 7·0·음수와 504개·0개 manifest를 거부한다. (codex)
- 변경: `extract_10k_analysis_text.py`와 `run_language_full_sample.py`가 runner가 전달하는 연도·sample namespace 경로를 사용할 수 있도록 선택적 경로 인수를 추가했다. 기존 2025 기본 경로는 유지한다. (codex)
- 변경: `merge_yearly_10k_batches.py`가 최대 6개 batch summary의 범위 겹침과 manifest 행 수를 검증하고 batch 순서를 보존한다. (codex)
- 검증: 503개 fixture·batch 6·batch coverage·runner summary·merge summary 테스트 16건 및 기존 HTML/extraction/download/pilot 관련 테스트 33건이 통과했다. `py_compile`과 `git diff --check`도 통과했다. (codex)
- 제한: `.git/refs`가 읽기 전용으로 마운트되어 별도 branch 생성, commit 및 push는 이 환경에서 수행하지 못했다. 실제 SEC/R2/Google Drive 쓰기와 historical backfill은 수행하지 않았다. (codex)

## 2026-08-02 - 논문용 Figure 웹 통합

- 감사: `analysis/descriptive_2020_2025/figures/`의 기존 PNG·SVG·집계 CSV를 확인하고 본문·부록·표 전용 사용 결정을 `web/docs/figure-audit.md`에 기록했다. (codex)
- 구현: 기존 figure 집계값을 수정하지 않고 `figure-data.json`·`figure-manifest.json`과 source CSV 다운로드를 생성하며, React SVG Figure 7종을 연구보고서의 결과 절에 통합했다. (codex)
- 검증: Figure source·manifest 테스트 2건을 포함한 관련 pytest 14건, generator `py_compile`, Vite build 및 local Playwright desktop/mobile(pageerror·console error·failed request 0, Figure SVG·caption·source·download 확인)를 실행했다. (codex)
- 배포: 커밋 `6d6f68c` push 후 production root가 새 Vite asset을 제공하는 것을 확인했다. production 브라우저 테스트는 현재 환경의 `sandbox_host_linux.cc` 종료 오류로 실행되지 않았고, local preview desktop/mobile 검증은 통과했다. Chromium PDF 생성도 같은 sandbox 제약으로 보류했다. (codex)

최신 기록을 위쪽에 추가하고 기존 기록을 삭제하지 않는다.

## 2026-08-02 - production blank screen 원인 확인 및 브라우저 검증

- 재현: Playwright Chromium으로 `https://s-p500.pages.dev/?diagnostic=1`을 실행한 결과 `TypeError: Cannot read properties of undefined (reading 'limitations')`가 첫 `pageerror`로 발생했다. HTTP status는 200이었고 failed request·console error는 0이었다. (codex)
- 원인: production bundle의 `Report`가 `data.docs.limitations`를 읽었지만 optional 문서 로딩 결과를 `docs` 객체로 묶기 전에 렌더링했다. (codex)
- 조치: `ErrorBoundary`를 root에 적용하고, core JSON과 supplemental JSON/Markdown을 분리해 optional 자료를 `Promise.allSettled()`로 로드하며 `docs = {}` 기본값과 section-level 오류 안내를 추가했다. (codex)
- 추가 수정: 모바일에서 긴 source 경로가 body `scrollWidth`를 확장하던 문제를 `overflow-wrap`, `min-width: 0`, table containment으로 수정했다. (codex)
- 검증: local production preview Playwright desktop/mobile 2개 테스트가 pageerror·console error·failed request 0, 필수 heading 표시, appendix 204개 DOM, mobile horizontal overflow 없음으로 통과했다. (codex)
- 상태: 수정 후 production 재배포 및 동일 Playwright test 재실행이 필요하다. (codex)

## 2026-08-02 - production 브라우저 검증 완료

- 배포: `e4a74fd`를 `origin/main`에 push한 뒤 production asset이 `index-DfcvgHXl.js`와 `index-Mdlp60ng.css`로 갱신되었다. (codex)
- production Playwright: desktop·mobile 2개 테스트가 모두 통과했으며 HTTP 200, `pageerror=0`, console error 0, failed request 0, 필수 heading 표시, appendix 204개 DOM, 모바일 horizontal overflow 없음이 확인됐다. (codex)
- 산출물: 실제 production desktop/mobile screenshot을 `web/test-results/`에서 생성하고 로컬 보관용 `web/artifacts/`로 복사했다. 해당 디렉터리는 Git에서 제외한다. (codex)
- API 검증: production JSON parse 성공, JSON·Markdown endpoint 12개 HTTP 200, 파일 크기 0 초과와 content-type을 확인했다. (codex)
- 상태: production 화면 정상 렌더링으로 전환되었으며, 최신 검증 문서 기록을 별도 commit으로 남긴다. (codex)

## 2026-08-02 - 루트 연구보고서형 대시보드 재구성

- 변경: `web/src/App.jsx`의 루트 화면을 표지·초록·연구설계·표본 구축·자료 수집·텍스트 처리·변수 측정·통계 분석·결과·논의·한계·재현성·부록 순서의 통합 보고서로 전면 재구성했다. (codex)
- 연결: 실제 `analysis/descriptive_2020_2025/`에서 생성된 JSON, 204개 변수 정의, 연도별 표, Welch 비교, 상관 및 VIF를 화면에 표시하고 각 표에 N·조건·source note를 추가했다. (codex)
- 디자인: sticky 목차, 학술 표, 수식 블록, 표 가로 스크롤, 모바일 반응형 및 A4 print stylesheet를 추가했다. (codex)
- 검증: generator·py_compile·Vite production build·preview HTTP smoke test와 생성 파일 응답 200을 확인했다. 브라우저 엔진과 Playwright가 Codespaces에 없어 screenshot 기반 검증은 아직 수행하지 못했다. (codex)
- 상태: 기존 패널·언어 결과·원본 HTML은 수정하지 않았으며, 다음 단계는 커밋 후 Cloudflare Pages production 배포와 실제 브라우저 screenshot 확인이다. (codex)

## 2026-08-02 - 연구보고서형 화면 production 반영 확인

- 배포: `5595ff3`을 `origin/main`에 push했고 `https://s-p500.pages.dev/`가 HTTP 200을 반환했다. 최신 asset에서 연구 요약·표본 구축·변수 측정·분석 결과·Fog Index 수식·Loughran–McDonald 표기를 확인했다. (codex)
- 검증: production의 분석 JSON·변수 정의 JSON·source manifest·감사 Markdown endpoint가 모두 HTTP 200이며 print CSS가 포함되어 있다. (codex)
- 제한: Codespaces에 Chromium·Firefox·Playwright가 없어 desktop/mobile screenshot과 실제 브라우저 상호작용 검증은 수행하지 못했다. (codex)

## 2026-08-02 - Loughran–McDonald 표기 통일

- 변경: UI, 변수 정의 metadata 및 생성 Markdown에서 표시용 `LM`을 `Loughran–McDonald`로 변경했다. (codex)
- 호환: 실제 데이터 열의 `lm_` 접두사는 column 호환성을 위해 변경하지 않았다. (codex)
- 검증: standalone `LM` 표시 0건, 관련 테스트 9건 및 frontend build 통과. (codex)

## 2026-08-02 - 논문 보고용 대시보드 설명 및 결과 페이지 확장

- 수정: 전체 연도 `ai_sentence_count` 카드를 연도별 단순평균이 아닌 전체 descriptive statistics 평균과 연결했다. (codex)
- 검증: 모든 variable definition의 source dataset·source script 존재를 생성 단계에서 확인하고 잘못된 concreteness script 경로를 수정했다. (codex)
- 추가: `#results`, `#reproducibility`, `#limitations` 페이지와 연도 변화·상관·VIF·품질 JSON 및 다운로드 CSV를 추가했다. (codex)
- 검증: 관련 테스트 8건, generator, frontend build, `git diff --check`를 실행했다. (codex)

## 2026-08-02 - 배포 화면 런타임 예외 수정

- 원인: 배포된 `analysis-summary.json`은 `N`, `standard_deviation`, `p25`, `p75`를 제공했지만 화면은 다른 키를 참조했다. (codex)
- 수정: 생성기에서 실제 CSV 열을 화면용 별칭으로 자동 정규화하고, correlation 키와 변수 정의 metadata 타입도 실제 JSON 구조에 맞췄다. (codex)
- 확인: 배포 URL의 HTML·`/data/analysis-summary.json` 모두 HTTP 200이며 새 build와 관련 테스트가 통과했다. (codex)

## 2026-08-02 - 대시보드 초기 로딩 오류 수정

- 원인: `summary`가 준비되기 전에는 반환하고 준비된 뒤에만 `useMemo`를 호출하여 React Hook 순서가 렌더 사이에서 바뀌었다. (codex)
- 수정: `useMemo`를 모든 렌더에서 동일하게 호출하도록 이동하고, 분석 JSON 요청의 HTTP 오류 검사를 추가했다. (codex)
- 검증: `npm run build`, `git diff --check` 통과. (codex)

## 2026-08-02 - 연구 보고용 웹 데이터·변수 정의 자동화

- 추가: `scripts/generate_web_analysis_data.py`가 기존 분석 산출물에서 웹 JSON·CSV와 상세 변수 정의 문서를 생성한다. (codex)
- 추가: `/variables`와 `/methods` hash 페이지, source SHA-256 metadata 및 Cloudflare `_redirects`를 구성했다. (codex)
- 보호: 기존 패널·언어 결과·원본 HTML은 수정하지 않았으며 실제 통계값은 frontend에 하드코딩하지 않는다. (codex)

## 2026-08-02 - 2019–2017년 역사적 표본 확장 계획 기록

- 계획: 현재 최저 분석연도 2020년의 직전 3개 연도인 2019, 2018, 2017을 역순으로 처리한다. (codex)
- 표본: 역사적 S&P 500 503 securities를 기준으로 하되, SEC의 유일한 적격 Form 10-K 조건을 충족하는 행만 포함하고 제외 사유를 보존한다. (codex)
- 실행: 연도별로 manifest 생성, SEC 수집, R2 저장, 추출·언어 측정, Google Drive 이전을 순차 수행한다. 한 연도 검증 전 다음 연도를 시작하지 않는다. (codex)
- Free Tier 보호: workflow 동시 실행을 막고 `max-parallel: 1`, checkpoint·resume, rate-limit 지연, 최소 artifact와 수동 실행을 사용한다. 503개는 100·100·100·100·100·3의 6개 batch로 나눈다. (codex)
- 상태: 계획만 기록했으며 2019–2017년 workflow 실행, SEC 수집, R2·Google Drive 변경은 아직 수행하지 않았다. (codex)
- 감사: 기존 2020–2025 실행기는 `2025/pilot_100` 경로와 1–5 batch를 하드코딩하고 있어 historical 6개 batch를 직접 처리할 수 없다. 기존 검증 pipeline을 깨뜨리지 않도록 전용 historical runner/workflow가 필요하다. (codex)

## 2026-08-02 - 저장소 문서·버전·인수인계 상태 전수조사

- 감사: 루트 `README.md`, 연도별 README, `2025/pilot_100/README.md`, `docs/current_project_handover.md`, `docs/repository-structure.md`, `docs/sample-definition.md`, `docs/constituent-data-method.md`의 과거 상태 설명을 현재 2020–2025 완료 및 2019–2017 계획과 일치하도록 정리했다. (codex)
- 버전: `VERSION`은 실제 릴리스 변경이 없으므로 `0.12.0`으로 유지하고, 임의의 `0.13.0` 변경은 반영하지 않았다. (codex)
- 보호: 기존 분석 결과·Google Drive 파일·R2 객체를 변경하지 않았으며, 역사 workflow도 실행하지 않았다. (codex)

## 2026-08-02 - Cloudflare Pages React dashboard scaffold 추가

- 추가: 저장소 루트의 Cloudflare Pages 설정을 유지하면서 `web/`에 React + Vite 반응형 dashboard 구조를 만들고, 루트 `npm run build`가 `web/dist/`를 생성하도록 연결했다. (codex)
- 화면: 연도 선택, firm-year 수, AI 공시 수·비율, 연도별 요약표와 `/api/summary` 연결 준비 상태를 추가했다. 현재 fallback 수치는 기존 확정 표본 요약만 사용한다. (codex)
- 안전: R2·Google OAuth secret, raw HTML, 기존 패널과 분석 결과는 frontend bundle에 포함하지 않았다. (codex)
- 검증: `npm install --prefix web --no-audit --no-fund`와 루트 `npm run build`가 성공했고, Vite가 루트 `dist/`를 생성했다. `git diff --check`도 통과했다. (codex)

## 2026-07-31 - 기술통계 Markdown 보고서 표시·해석 보완

- 변경: `write_descriptive_reports.py`가 기존 통계 CSV를 수정하지 않고 한글 열 제목, 정수 연도·관측치 수, 백분율, p-value 및 `-` 구조적 결측 표시로 Markdown을 재생성하도록 개선했다. (codex)
- 구성: 연도별 표를 표본·AI 공시, 구체성·시제, 불확실성·수동태·가독성, AI 감성의 4개 패널로 분리했다. (codex)
- 해석: AI 공시 포화, 연도 구성 효과, 2023년 전후 구조 변화, 제한적인 미래 조동사 측정, 상관·VIF 해석 주의사항을 보고서에 추가했다. (codex)
- 검증: raw `nan`·소수점 연도·`p = 0.0000`·영문 원자료 열 제목 0개, 관련 테스트 7개 통과, 기존 확장 패널과 통계 CSV 변경 0건을 확인했다. (codex)

## 2026-08-02 - Google Drive 신규 저장 형식 기본값 고정

- 변경: 향후 Google Drive migration의 기본 `drive_layout`을 `year_flat`으로 설정했다. 파일은 각 연도 폴더 바로 아래 `번호_연도_기업명_SYMBOL_CIK.html` 형식으로 저장된다. (codex)
- 호환: 기존 `legacy_nested` 형식은 명시적 옵션으로만 유지하며, 기존 Drive 파일·패널·R2 객체는 변경하지 않았다. (codex)
- 검증: migration 실행기 `py_compile`, workflow YAML 파싱 및 `git diff --check`를 통과했다. 실제 migration은 실행하지 않았다. (codex)

## 2026-07-31 - Google Drive raw HTML 폴더 평탄화 준비

- 확인: 기존 Google Drive migration 실행기는 `연도/sample_500/html/raw/<CIK>/<accession>.html` 구조를 사용하며 leaf 폴더 이름은 CIK이다. (codex)
- 구현: leaf 폴더를 해당 연도 바로 아래로 이동하고 빈 `sample_500`·`html`·`raw` wrapper만 선택적으로 제거하는 수동 workflow와 실행기를 추가했다. (codex)
- 안전: 파일 내용·파일명·Drive 파일 ID는 변경하지 않으며, 동일 이름 목적지나 중복 폴더는 덮어쓰지 않고 실패로 기록한다. (codex)
- 검증: 실행기 `py_compile`, workflow YAML parsing 및 `git diff --check`를 통과했다. Drive 실제 변경은 workflow dry-run 확인 후 execute에서만 수행한다. (codex)

## 2026-07-31 - Google Drive raw HTML 파일명 변경 준비

- 요구: 평탄화가 완료된 뒤 각 연도 leaf 폴더의 HTML 이름을 `0_기업명_SYMBOL_CIK.html` 형식으로 변경한다. 숫자는 해당 연도 manifest의 `sample_order - 1`이다. (codex)
- 구현: `rename_google_drive_raw_html.py`와 별도 수동 workflow를 추가했다. 연도별 manifest의 기업명·ticker·CIK를 사용하며 파일 내용·file ID는 변경하지 않는다. (codex)
- 안전: accession이 manifest와 일치하지 않거나 목적지 파일명이 충돌하면 해당 파일을 변경하지 않고 실패로 기록한다. (codex)

## 2026-07-31 - 2020–2025 기술통계·상관분석 산출

- 실행: Actions run `30620803314`의 6개 연도 측정 job이 모두 성공했고 연도별 feature artifact를 확보했다. (codex)
- 결과: 기존 2,829행·147개 열은 변경 없이 유지했으며 204개 열의 확장 패널, 기술통계표, Pearson·Spearman 상관표, VIF표, 연도별·동일 기업 변화표를 생성했다. (codex)
- 표본: 연도별 행 수는 446, 462, 471, 479, 487, 484개이며 AI disclosure firm-year는 1,660개다. (codex)
- 신규 측정: spaCy 3.8.7·en_core_web_sm 3.8.0 기반 시제·수동태와 기존 readability heuristic 기반 AI Fog를 사용했다. 원본 HTML 재수집·R2·Google Drive 변경은 없었다. (codex)
- 검증: 기존 값 변경 셀 0, company-year·CIK-year·accession 중복 0, 신규 count 음수 0, share 범위 위반 0, infinity 0, AI 0문장 수준 구조적 결측 위반 0을 확인했다. 관련 테스트 4개와 `py_compile`, `git diff --check`를 실행했다. (codex)
- 산출물: `analysis/descriptive_2020_2025/` 아래 확장 패널, variable dictionary, measurement audit/design, 품질 요약, CSV 표, PNG/SVG 그림 및 한글 Markdown 보고서를 생성했다. (codex)

## 2026-07-31 - 2020–2025 기술통계용 확장 언어 변수 준비

- 감사: 기존 2,829행·147열 패널에서 AI 공시, LM 7범주, report/AI concreteness, report Fog, 길이 및 숫자 비율을 확인해 재측정 대상에서 제외했다. (codex)
- 입력: 연도별 기존 Actions artifact와 2025 pilot/recovery extraction에서 accession 고유 정제 텍스트 2,829개를 확보했으며 Google Drive raw HTML과 R2는 읽거나 변경하지 않았다. (codex)
- 신규 방법: spaCy 3.8.7·en_core_web_sm 3.8.0 POS/dependency로 whole-report/AI 시제와 수동태를 측정하고 기존 deterministic heuristic으로 AI Fog를 생성한다. (codex)
- smoke test: 연도별 AI 공시·미공시·문서 길이 차이를 포함한 18개 firm-year를 전체 파싱했다. 4 worker는 메모리로 종료되어 1 worker로 고정했으며, 최초 AI 연결 오류는 안정 company_id가 아닌 고유 accession으로 연결해 수정했다. (codex)
- 다음 단계: 6개 연도 matrix job의 신규 측정 완료 후 기존 값 불변 2,829행 확장 패널, 기술통계, 상관관계, VIF, 한글 표·그래프·보고서를 생성한다. (codex)

## 2026-07-31 - Google Drive 이전 완료 R2 raw HTML 삭제 준비

- 후속 확인: 최초 run의 `Errors=0`은 quiet 응답에 근거한 API 접수 결과일 뿐 실제 객체 부재 검증이 아니므로, manifest key의 R2 잔존 여부를 bucket 목록에서 읽기 전용으로 확인하는 `verify_absence` mode를 추가했다. (codex)
- 최종 검증: run `30619115601`의 R2 API 목록 결과는 manifest 잔존 0개, 버킷 전체 0개, 총 0바이트, manifest 외 객체 0개다. Cloudflare 화면에 사용량이 남아 있다면 현재 객체가 아니라 대시보드 집계 갱신 문제다. (codex)
- 기준: migration run `30544560261` artifact의 2,829행은 고유 object key 2,829개, `uploaded` 2,828개, `skipped_existing_match` 1개, size·SHA 검증 2,829개이며 실패·중복·빈 key가 없다. (codex)
- 구현: prefix 또는 bucket 전체 삭제 없이 manifest key만 최대 1,000개씩 삭제하고 `--execute`에서만 R2 delete API를 호출하는 실행기와 confirmation이 필요한 수동 workflow를 추가했다. (codex)
- 검증: 관련 mock test 6개, Python compile, workflow YAML parse, 실제 artifact dry run 및 `git diff --check`가 통과했다. dry run의 delete API 호출은 0회이며 전체 테스트는 실행하지 않았다. (codex)
- 안전: Google Drive, 기존 패널·분석 결과, R2 credential·bucket 설정은 변경하지 않으며 실제 삭제 결과는 별도 Actions artifact로 보존한다. (codex)
- 실행: Actions run `30618552630`에서 manifest key 2,829개를 3개 batch로 삭제 요청했고 API 오류 없이 2,829개가 성공 처리됐다. bucket 자체와 manifest 외 객체는 삭제 대상으로 삼지 않았다. (codex)

## 2026-07-30 - R2 raw HTML의 Google Drive 이전 준비

- 대상: 연도별 R2 manifest의 2020–2025 raw HTML 2,829개, 14,167,004,308바이트를 source of truth로 고정했다. 중복 object key와 accession은 0개다. (codex)
- 구현: OAuth refresh, Drive root 권한·quota, R2 연결, 한 객체 upload·동일 객체 skip, 전체 이전·checkpoint·size/SHA 검증을 수행하는 전용 workflow와 실행기를 추가했다. (codex)
- 안전: R2 삭제·overwrite, SEC 재수집, 기존 언어 결과·2,829행 패널 수정 및 raw HTML Git 추적은 수행하지 않는다. 실제 이전은 연결 시험 성공 후에만 실행한다. (codex)
- 검증: Python compile, workflow YAML parse, `git diff --check`를 최소 검증으로 사용하며 전체 68개 테스트는 실행하지 않는다. (codex)
- 실행: Actions run `30543859858`은 실제 secret 주입 확인에서 client ID와 client secret이 빈 값으로 확인되어 38초 후 중단됐다. refresh token, root folder ID 및 R2 네 변수는 주입됐으며 OAuth 요청·Drive/R2 객체 접근·이전은 수행되지 않았다. (codex)

## 2026-07-30 - SnowballC와 NLTK Porter 소규모 fixture 비교

- 비교: 일반형·활용형·다단계 접미사·연구 관련 단어·Porter 경계 사례 36개를 SnowballC 0.7.0 `wordStem()`과 NLTK 3.10.0 `ORIGINAL_ALGORITHM`에 동일하게 입력했다. (codex)
- 결과: 36개 stem이 모두 동일했고 차이는 0개였다. 이는 소규모 fixture 범위의 결과이며 전체 구현 동등성을 의미하지 않는다. (codex)
- 범위: 기존 5개 기업 구체성 결과 재측정, Brysbaert 37,058개 단어 전수 비교 및 전체 테스트는 수행하지 않았다. (codex)

## 2026-07-29 - R 및 SnowballC 0.7.0 환경 고정

- 환경: Ubuntu package manager로 R 4.3.3과 개발 도구를 설치하고 CRAN archive의 SnowballC 0.7.0을 프로젝트 전용 library에 source build했다. (codex)
- 무결성: SnowballC archive 405,463바이트와 SHA-256 `b10fee9d322f567a22c580b49b5d4ba1c86eae40a71794ca92552c726b3895f3`를 기록했다. (codex)
- 검증: packageVersion 0.7.0과 6개 단어의 wordStem 실행·길이·NA·빈 출력 조건을 확인했다. (codex)
- 범위: NLTK 비교, 전체 Brysbaert stem 비교, 5개 기업 재측정 및 기존 PARTIAL 판정 변경은 수행하지 않았다. (codex)

## 2026-07-29 - Brysbaert textual concreteness 5개 기업 측정

- 출처: Springer 공식 supplementary XLSX 39,954행(37,058 single, 2,896 bigram), 8열, 점수 1.04–5.00, SHA-256 `1673ead761e28833a40e82c0d20f10782955ced9366d600eafeefee0f2254545`를 검증했다. (codex)
- 전처리: Baek et al. (2023) Appendix A에 따라 SMART stopword 제거와 NLTK Porter original algorithm을 적용했다. tidytext 0.3.1 실제 SMART subset은 571행·570고유 항목이며 canonical SHA는 `220f9e4fde204eb4d4a216f4b5024633b61e41555809f95d9b12f0773be0a3f3`다. (codex)
- 매칭: 원형 exact를 우선하고 exact가 없을 때 unique stem만 사용했다. 6,956개 dictionary collision stem은 평균하지 않고 unmatched 처리했다. (codex)
- 결과: NVDA·HPE·WAT·NSC AI 평균은 각각 2.994·2.876·2.555·2.701이며 TECH AI는 분모 0, 보고서 평균은 2.868이다. 보고서 coverage는 0.734–0.765다. (codex)
- 검증: 논문 physics/science 예제 3.10/2.96, AI 문장 273, LM 결과 불변, 5개 기업, score·coverage 범위와 idempotent skip을 확인했다. (codex)
- 범위: LIWC2015 time focusing, 수동태, 인간 라벨, 100개 확장, R2는 수행하지 않았다. (codex)

## 2026-07-29 - 공식 LM 금융사전 5개 기업 적용

- 출처: 공식 Notre Dame 페이지가 직접 연결한 1993–2025 CSV를 확보해 9,093,460바이트, 86,553행, 17열 및 SHA-256 `e2d1328682bab7d2187684fb9f5420bb730401c9eefc00daf835edd203f4859d`를 확인했다. (codex)
- 규칙: 범주 값이 양수인 단어만 활성화하고 0과 음수 제거 표지는 제외했으며 다중 범주 소속은 독립적으로 유지했다. (codex)
- 측정: 기존 NVDA·HPE·TECH·WAT·NSC 및 AI 문장 273개를 유지하면서 AI 문장과 전체 보고서의 7개 LM 범주, 비율, 순감성 및 coverage를 생성했다. (codex)
- 결측: AI 문장이 없는 TECH의 AI 수준 분모 변수는 missing으로 두고 보고서 수준 LM 변수는 계산했다. NSC 단일 AI 문장 warning을 유지했다. (codex)
- 배포: 학술 연구 사용은 허용되지만 공개 재배포 문구가 없어 원본과 전체 파생 사전은 Git에서 제외하고 공식 설치·SHA 검증 절차만 추적한다. (codex)
- 범위: Brysbaert 구체성, dependency 시제·수동태, 인간 truth label, 100개 확장, R2 및 외부 재무자료는 수행하지 않았다. (codex)

## 2026-07-29 - 5개 기업 언어 변수 smoke test

- 선정: warning 없는 성공 기업 중 NVDA·HPE(사전 탐색 AI 빈도 상위), TECH(최저), WAT(단어 수 중앙값 인접), NSC(seed `20250729` 무작위)를 중복 없이 선정했다. (codex)
- 측정: AI 공시 4개, AI 비공시 1개, 직접 AI 문장 273개를 확인하고 AI 문장 Fog와 전체 보고서 길이·Fog·숫자·AI·표 비율 통제변수를 생성했다. (codex)
- 의존성: 로컬에 출처·라이선스가 확인된 Brysbaert·Loughran-McDonald 사전과 dependency model이 없어 구체성·불확실성·감성·시제·수동태를 blocked dependency로 보존했다. (codex)
- 품질: 입력 SHA 5/5, 통합 결과 5행, ratio·음수·무한대·구조 오류 0이며 수동검토 후보 31개는 인간 판정 없이 `needs_manual_review`로 남겼다. (codex)
- 검증: 기존 30개를 포함한 총 45개 테스트, `py_compile`, 품질검사, `git diff --check`가 통과했고 재실행에서 5개를 모두 skip했다. (codex)
- 범위: 100개 전체 적용, R2, SEC 네트워크, 외부 통제변수 수집은 수행하지 않았다. 다음 단계 전 사전·dependency model 출처와 버전을 확정해야 한다. (codex)

## 2026-07-29 - 2025 파일럿 분석용 텍스트 생성

- 추출: SEC 원본 HTML 100개의 SHA를 재검증하고 Cooper et al. (2022)을 참고한 inline XBRL parser로 언어 분석용 본문, 원문 구조 보존 텍스트, 표 텍스트 및 주요 Item 파일을 생성했다. (codex)
- 규모: 분석 단어 6,172,973개, 문단 141,796행, 문장 298,250행이며 100개 기업 연결과 모든 출력 SHA가 일치한다. (codex)
- 품질: 빈 본문·HTML 태그·script/style·XBRL namespace·깨진 문자·3회 실패는 0이다. 핵심 section 경계 warning은 41개 기업에 보존했다. (codex)
- 수동검토: 크기·단어 수 극단값과 고정 seed 표본 5개를 검토해 NVR·CPRT는 pass, WFC·D·ETR은 layout 또는 Item 7 경계 warning으로 기록했다. (codex)
- 재실행: parser `1.0.3` 산출물의 SHA 일치 재실행에서 100개 모두 skip했다. (codex)
- 범위: AI 여부, AI 문장, 구체성, 시제, 불확실성, 수동태, Fog, 감성 및 통제변수는 계산하지 않았다. 다음 단계는 3-5개 기업 언어 변수 smoke test다. (codex)

## 2026-07-29 - 2025 파일럿 SEC 10-K HTML 수집 완료

- 수집: 유일한 입력 `final_analysis_sample_100.csv`의 100개 accession과 primary document를 SEC Archives에서 최대 초당 1회로 다운로드했다. (codex)
- 무결성: HTML 100개, manifest 100행, 고유 accession·SHA-256 100개, 빈 파일·HTTP 실패·reportDate 불일치 0개를 확인했다. 총 크기는 448,173,188바이트다. (codex)
- 재실행: 두 번째 실행에서 100개 모두 기존 SHA-256 일치로 네트워크 요청 없이 skip되어 idempotency를 확인했다. 최초 요청 로그는 HTTP 200 100행, retry 0행이다. (codex)
- 범위: HTML collection completed 단계이며 본문 parsing, 텍스트 추출, NLP 및 언어 분석은 수행하지 않았다. (codex)
- 검증: unit/artifact test 19개, `py_compile`, 전체 파일 SHA 재계산 및 `git diff --check`가 통과했다. (codex)

## 2026-07-29 - 2025 파일럿 최종 분석 표본 및 filing metadata 확정

- 교체 적용: 최초 100개 추출 표본은 보존하고, 2025 reportDate Form 10-K가 없는 TXT(`P2025-059`)를 제외한 뒤 동일 Industrials의 deterministic reserve 1순위 ITW에 `P2025-R001`을 부여했다. seed `20250729`를 유지했고 새 추출이나 AI 정보는 사용하지 않았다. (codex)
- 최종 상태: `final_analysis_sample_100.csv`는 100개 기업, 100개 고유 CIK, 100개 고유 accession, Industrials 16개이며 모든 filing은 reportDate 2025의 정확한 Form 10-K다. (codex)
- audit: TXT의 원 filing 검토와 제외 사유를 유지하고 FOXA/FOX, GE, TXT, ITW 검토를 모두 resolved 처리했다. 기존 요청 로그 769행은 변경하지 않았다. (codex)
- 검증: 연도별 원본 SHA-256 검증, 비네트워크 unit test 13개, `py_compile`, 반복 교체 실행 및 `git diff --check`가 통과했다. integration smoke test와 원문 HTML 다운로드는 수행하지 않았다. (codex)
- 다음 단계: 원문 다운로드 승인을 받으면 `final_analysis_sample_100.csv`만 입력으로 사용하며, 현재 단계에서는 텍스트 추출과 언어변수 측정을 수행하지 않는다. (codex)

## 2026-07-29 - 수동검토 해결 및 TXT 교체 후보 제안

- identity 검토: FOXA/FOX는 동일 CIK의 두 주식종류로, GE는 SEC 법적 명칭과 표본 설명명 차이로 확인하여 둘 다 CIK·ticker 기반 resolved 처리했다. (codex)
- TXT 검토: fiscal year end `0102`로 인해 2025 제출 10-K의 reportDate는 2024-12-28, 2026 제출 10-K의 reportDate는 2026-01-03이므로 기존 no eligible 판정을 유지했다. (codex)
- 교체 제안: Industrials 결정론적 예비 1순위 ITW가 2025 reportDate 10-K 기준을 충족했으며, 실제 표본 교체는 적용하지 않았다. (codex)
- 범위: 기존 표본·metadata manifest를 변경하지 않았고 원문 HTML도 다운로드하지 않았다. (codex)

## 2026-07-29 - 100개 파일럿 SEC metadata 및 filing 선정

- 현재 상태: 100개 기업의 SEC submissions metadata 상태를 모두 기록하고, reportDate 2025 기준으로 99개 eligible Form 10-K와 1개 미확인 사례를 판정했다. (codex)
- 수정신고서: 관련 10-K/A 보유 기업 2개를 원 10-K와 reportDate로 연결했으며 주 filing으로 대체하지 않았다. (codex)
- 검증: accession 중복과 eligible primary document 결측은 없고, manual review 3개 기업을 남겼다. (codex)
- 범위: 원문 HTML, 텍스트 추출, 언어변수 및 분석은 수행하지 않았다. (codex)

## 2026-07-29 - 2025년 100개 기업 파일럿 표본 고정

- 현재 상태: `pilot/2025-10k-100`에서 CIK와 GICS sector가 확인된 487개 기업을 대상으로 산업 비례 100개 표본과 산업별 예비 순서를 생성했다. (codex)
- 표본 규칙: seed `20250729`, largest remainder, 기업 키·CIK 중복 금지이며 AI 텍스트 결과는 사용하지 않았다. (codex)
- 검증 결과: unit test, 기존 연도별 검증, `py_compile`, `git diff --check`가 통과했다. (codex)
- 제한: `SEC_USER_AGENT` 미설정으로 SEC metadata 및 원문 네트워크 수집은 수행하지 않았다. (codex)

## 2026-07-24 - 저장소 구조 명세 및 검증 보강

- 현재 상태: `main`의 전체 파일 트리와 각 경로의 역할·수정 원칙·생성 관계를 명시했다. (codex)
- 현재 버전: `0.6.0`. (codex)
- 보완 내용: 연도별 CSV의 행 단위와 열 의미를 문서화하고, 검증 스크립트에 schema·key·CIK·manifest·원본 hash 검사를 추가했다. (codex)
- 검증 범위: 모든 연도 표본의 500개 기업, 기대 종목 수, 기준일, 필수 열, 고유 키, CIK 형식 및 원본 3개의 SHA-256을 자동 검사한다. (codex)
- 다음 작업: 결측 CIK를 보완한 뒤 10-K filing metadata 및 원문 저장 구조를 확정한다. (codex)

## 2026-07-24 - 원본 스냅숏 원격 무결성 복구

- 현재 상태: GitHub 전송 과정에서 잘린 대용량 원본 3개를 분할 전송으로 다시 반영했다. (codex)
- 현재 버전: `0.5.1`. (codex)
- 검증 결과: 원격 `main`과 로컬 `main`의 전체 tree SHA, 원본 파일 크기 및 manifest에 기록된 SHA-256을 대조한다. (codex)
- 영향 범위: 연도별 기업·종목 목록과 생성 코드는 최초 반영부터 정상이며, 복구 대상은 `data/raw/`의 원본 스냅숏 3개다. (codex)

## 2026-07-24 - 연도별 S&P 500 기업 목록 구축

- 현재 상태: `2020/`-`2025/`에 기준일별 `sp500_companies.csv`와 종목 단위 `sp500_securities.csv`를 생성했다. (codex)
- 현재 버전: `0.5.0`. (codex)
- 표본 결과: 모든 연구연도 기업 목록은 500행이며, 종목 목록은 2020-2021년 505행, 2022-2025년 503행이다. (codex)
- 재현성: Wikipedia HTML, 역사 구성종목 CSV, SEC ticker JSON 원본과 SHA-256 해시를 보존하고 생성·검증 스크립트를 추가했다. (codex)
- 검증 결과: `python scripts/validate_annual_constituents.py`가 6개 연도 모두 통과했다. (codex)
- 알려진 제한: 현재 SEC ticker 파일에 없는 과거 편출기업은 CIK와 과거 GICS가 일부 결측이며 10-K 수집 전에 추가 보완이 필요하다. (codex)
- 다음 작업: 결측 CIK를 SEC EDGAR 역사 제출자료로 보완한 뒤 기업-보고연도 10-K filing 목록을 생성한다. (codex)

## 2026-07-24 - 2020-2025 연도별 폴더 생성

- 현재 상태: 저장소 루트에 `2020/`부터 `2025/`까지 연구연도별 폴더를 생성했다. (codex)
- 현재 버전: `0.4.0`. (codex)
- 폴더 추적: Git에서 빈 폴더를 추적할 수 있도록 각 연도 폴더에 `README.md`를 추가했다. (codex)
- 문서화: 각 폴더에 구성기업 확정 기준일, CIK 기반 기업 단위 및 공통 표본 정의 문서 경로를 기록했다. (codex)
- 검증 결과: `git diff --check`와 6개 연도별 `README.md` 존재 검사가 통과했다. (codex)
- 다음 작업: 연도별 S&P 500 구성기업 명단 생성 파이프라인과 연도 폴더 내부의 데이터 하위 구조를 확정한다. (codex)

## 2026-07-20 - 연도별 S&P 500 확정 기준 설정

- 현재 상태: 연구연도 `t`의 구성기업을 다음 해 1월 1일 현재 S&P 500 구성기업으로 정의했다. (codex)
- 현재 버전: `0.3.0`. (codex)
- 적용 예시: 2025년 표본은 2026년 1월 1일 현재 구성기업으로 확정한다. (codex)
- 변경 적용: Wikipedia 변경 표의 `Effective Date`가 확정 기준일 이하인 사건만 해당 연도에 반영한다. (codex)
- 기업 단위: 복수 주식 종류는 SEC CIK를 기준으로 하나의 기업으로 통합한다. (codex)
- 다음 작업: Wikipedia 원본 스냅숏을 보존하고 변경 이력을 역적용하는 연도별 표본 생성 파이프라인을 구현한다. (codex)

## 2026-07-20 - 프로젝트 목적 및 연구 범위 확정

- 현재 상태: 저장소 목적을 2020-2025년 S&P 500 대상 기업 전체의 10-K 보고서 수집 및 분석으로 확정했다. (codex)
- 현재 버전: `0.2.0`. (codex)
- 분석 단위: 기본적으로 기업-보고연도별 10-K filing으로 정의했다. (codex)
- 문서화: 대상 기간, 자료원, 수집·검증·분석 단계와 표본 정의 전 확정할 사항을 `README.md`에 기록했다. (codex)
- 미결정 사항: 10-K/A 처리, 기업 식별자 변경 처리, 보고연도와 filing year 기준을 확정해야 한다. (codex)
- 다음 작업: 표본 구축 원칙을 먼저 확정한 뒤 디렉터리 구조, 데이터 사전 및 SEC 수집 파이프라인을 설계한다. (codex)

## 2026-07-20 - 저장소 관리 체계 초기화

- 현재 상태: 빈 `s-p500` 저장소에 작업 규칙과 기록 체계를 구축했다. (codex)
- 현재 버전: `0.1.0`. (codex)
- 완료 항목: `AGENTS.md`, 작성 규칙, 변경 이력, 진행 기록, 디버그 로그 및 버전 파일을 추가했다. (codex)
- 검증 결과: `git diff --check`가 통과했고 `git status --short`에서 의도한 초기 파일만 확인했다. (codex)
- 알려진 제한: 아직 프로젝트 코드, 데이터, 분석 파이프라인 및 테스트가 없다. (codex)
- 다음 작업: 실제 프로젝트 목표와 데이터 구조가 정해지면 README, 디렉터리 구조 및 재현 명령을 추가한다. (codex)
## 2026-08-02 - 데스크탑 발표형 대시보드 UI 보완

- 변경: 기존 React 대시보드를 데스크탑 중심의 sidebar, headline, KPI 카드, 연도별 막대그래프 및 표 구성으로 재배치했다. (codex)
- 원칙: 참고한 UI 지침의 공간을 통한 그룹화, 명확한 시각적 위계, 목적 있는 색상, 단일 sans-serif, 좌측 정렬 및 충분한 행간을 적용했다. (codex)
- 범위: 분석값·raw HTML·기존 패널은 변경하지 않았으며 새 이미지나 외부 자산을 추가하지 않았다. (codex)
- 검증: `npm run build`, `git diff --check`를 실행한다. (codex)
## 2026-08-02 - 2020–2025 패널 분석값 대시보드 반영

- 변경: `analysis/descriptive_2020_2025/figures/figure_aggregate_data.csv`와 패널 품질 요약에 기반한 표시용 분석 요약을 `web/src/data/analysisSummary.js`로 추가했다. (codex)
- 화면: AI 공시 비율, firm-year 수, AI 직접 문장 평균, 균형·불균형 패널 수, 구체성·시제·uncertainty·Fog Index 및 상관관계 주의사항을 대시보드에 표시한다. (codex)
- 안전: 원본 패널·분석 CSV·raw HTML은 변경하지 않고, API 응답이 부분 요약만 제공해도 정적 패널값과 병합하도록 처리했다. (codex)
- 검증: `npm run build`, `git diff --check` 통과. (codex)
## 2026-08-02 - 대시보드 연구 방법·변수·결과 상세화

- 변경: 데이터 수집, 변수 정의, 분석 방법, 분석 결과를 데스크탑 대시보드의 접이식 연구 맥락 섹션으로 추가했다. (codex)
- 내용: SEC CIK·reportDate·Form 10-K 기준, Google Drive 원문 보관, AI·구체성·시제·수동태·LM·Fog 변수, 기술통계·연도 변화·within-firm·상관·VIF 절차를 설명한다. (codex)
- 결과: AI 공시 확산, AI 문장 수 증가, AI 구체성 하락, 현재 시제 증가, Fog Index 변화의 기존 산출값을 표시한다. (codex)
- 검증: `npm run build`, `git diff --check`를 실행한다. (codex)
## 2026-08-02 - 대시보드 수식 및 측정 방법 반영

- 변경: AI 공시, 시제 share, 수동태 share, LM share, Fog Index, concreteness 평균의 수식과 분자·분모를 접이식 연구 카드에 추가했다. (codex)
- 처리: AI 직접 문장이 없을 때의 count 0과 구조적 결측, 미래 시제 표지 범위, spaCy dependency, SMART·Porter·collision 규칙을 명시했다. (codex)
- 범위: 기존 산출값은 재계산하지 않았고 표시 설명만 보강했다. (codex)
- 검증: `npm run build`, `git diff --check`를 실행한다. (codex)
## 2026-08-02 - 문헌 자료 사용 범위 정정

- 정정: `문헌정리.pdf`의 문헌 근거·연구 배경 표시는 제거했다. 해당 파일은 수식·측정 방법·표현 형식을 확인하는 참고자료로만 사용한다. (codex)
- 유지: 대시보드의 수식, 분자·분모, 결측 처리 및 측정 절차 설명은 유지한다. (codex)
- 검증: 문헌 표시 제거 후 `npm run build`, `git diff --check`를 실행한다. (codex)
## 2026-08-02 - 논문용 Table 1·Table 2 형식 반영

- 변경: `table_02_overall_descriptive_statistics.csv`의 실제 산출값을 `Mean`, `Std Dev.`, `Q1`, `Median`, `Q3`, `N` 열로 표시하는 Table 1 형식 표를 추가했다. (codex)
- 추가: 텍스트 특성 결정요인 분석은 아직 실행하지 않았으므로, 종속변수·모형·설명변수·통제·상태를 보여주는 Table 2 설계표만 추가했다. 계수·t-stat·p-value는 생성하지 않았다. (codex)
- 안전: 제공된 예시의 재무변수나 회귀계수를 현재 패널에 임의로 이식하지 않았다. (codex)
- 검증: `npm run build`, `git diff --check`를 실행한다. (codex)
## 2026-08-02 - Table 2 표시 제거

- 변경: 사용자의 요청에 따라 대시보드 Table 2 결정요인 분석 설계표를 제거했다. (codex)
- 유지: 실제 산출값을 사용하는 Table 1 기술통계표, 수식·측정 방법 및 기존 패널 분석 결과는 유지한다. (codex)
# 2026-08-02 - 503개 runner 원격 인수인계 및 fixture CI

- 추가: `.github/workflows/test-yearly-runner-generalization.yml`이 runner 관련 파일 변경 시 fixture·mock 테스트와 Python compile만 실행하도록 구성했다. `contents: read`, runner 전용 concurrency, 14일 artifact 보존을 사용하며 SEC·R2·Google Drive secret을 주입하지 않는다. (codex)
- 추가: `docs/handoff-runner-503.md`에 원격 branch, 상수, dashboard와의 작업선 분리, 새 Codespaces 재접속 명령 및 historical 실행 전 조건을 기록했다. (codex)
- 상태: runner branch `24fb65d` 기반 작업을 PR로 보존하며 main에는 병합하지 않는다. 실제 historical 수집과 외부 저장소 쓰기는 실행하지 않는다. (codex)
- 후속: PR #3 첫 CI run `30741636264`는 pytest 미설치로 실패했으며, workflow에 pytest 설치를 추가해 재실행한다. (codex)
