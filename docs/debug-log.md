# Debug Log

## 2026-08-02 - 연구보고서 Figure 통합 검증

- 관찰: 기존 figure 산출물은 `analysis/descriptive_2020_2025/figures/`에 존재했지만 웹 결과 절에는 표만 표시되었다. (codex)
- 원인: figure 집계 CSV가 생성되었어도 frontend 데이터 로더와 Figure 컴포넌트가 연결되어 있지 않았다. (codex)
- 조치: `scripts/generate_web_analysis_data.py`가 기존 figure 집계·집단·within-firm CSV와 분석표를 읽어 `figure-data.json`, `figure-manifest.json`, 다운로드 CSV를 생성하도록 추가하고, React에 방어적인 SVG Figure 컴포넌트를 통합했다. (codex)
- 검증: source SHA·열·생성 script가 manifest에 존재하고, local production preview에서 desktop/mobile pageerror·console error·failed request가 모두 0이며 7개 Figure의 SVG·figcaption·source details·CSV download가 DOM에 표시된다. (codex)
- 남은 위험: 커밋 `6d6f68c` push 후 production root의 새 asset 반영은 HTTP로 확인했지만, 원격 Playwright는 `sandbox_host_linux.cc` 종료 오류로 실행되지 않았다. local preview 브라우저 검증은 통과했으며, 현재 Codespaces Chromium은 `page.pdf`도 같은 이유로 생성하지 못했다. (codex)

## 2026-08-02 - production blank screen의 첫 pageerror 확인

- 재현 명령: `cd web && npx playwright test tests/production-smoke.spec.js --reporter=line`를 production base URL로 실행했다.
- 관찰: HTTP 200, console error 0, failed request 0이었지만 `pageerror`는 다음과 같았다: `TypeError: Cannot read properties of undefined (reading 'limitations')` at `b0 (https://s-p500.pages.dev/assets/index-wyBcecrj.js:49:57861)`.
- 원인: `Report` 함수에서 `docs.limitations`와 `docs.reproducibility`를 읽었으나 production 데이터 조합 객체에 `docs`가 존재하지 않았다. React root 전체가 예외로 중단되어 흰 화면이 되었다.
- 수정: `docs = {}` 기본값을 추가하고, core data와 supplemental data를 분리했다. supplemental JSON/Markdown은 `Promise.allSettled()`로 로드하고 실패 시 해당 section에 Expected source 오류를 표시한다. `ErrorBoundary`가 남은 렌더 오류를 사용자에게 보여준다.
- 추가 원인: mobile viewport에서 긴 source path가 `scrollWidth=706`(viewport 390)을 만들었다. source note 줄바꿈과 `min-width:0`·table containment로 수정했다.
- 재검증: local production preview에서 desktop/mobile 모두 `pageerror=[]`, `consoleErrors=[]`, `failedRequests=[]`, 필수 heading 표시, appendix 204개, horizontal overflow false로 통과했다.
- 상태: local 수정 해결. production은 새 commit push 및 재배포 후 동일 테스트를 수행한다.

## 2026-08-02 - 수정 후 production 브라우저 검증 통과

- 배포: `e4a74fd` push 후 production HTML이 `index-DfcvgHXl.js`를 제공했다.
- 실행: `cd web && npx playwright test tests/production-smoke.spec.js --reporter=line`.
- 결과: desktop·mobile 모두 `httpStatus=200`, `consoleErrors=[]`, `pageErrors=[]`, `failedRequests=[]`; 필수 연구 절 heading과 `#appendix [data-variable-definition]` 204개가 표시됐다.
- 모바일: `document.documentElement.scrollWidth > window.innerWidth + 1`가 false로 확인되어 body-level horizontal overflow가 제거됐다. 표 내부 가로 스크롤은 유지된다.
- 정적 검증: JSON 8개와 Markdown 4개 endpoint가 HTTP 200이고 JSON parse가 성공했다. content-type과 파일 크기도 확인했다.
- 상태: production blank screen 해결됨. 실제 desktop/mobile screenshot은 Playwright test-results에 생성되며 test output 디렉터리는 `.gitignore`로 제외한다.

## 2026-08-02 - 루트 화면이 논문 보고서형으로 보이지 않던 문제

- 증상: `/`가 hero·요약 카드·간단 그래프 중심의 발표용 개요를 유지하고 상세 방법론·결과·변수 수식이 hash 페이지에만 노출됐다.
- 원인: `web/src/App.jsx`의 기본 분기에서 overview를 먼저 렌더링하고, `methods`·`results`·`variables`를 별도 페이지로 반환했다. 방법론 Markdown도 웹 본문과 직접 연결되지 않았다.
- 조치: 기본 렌더링을 통합 연구보고서로 교체하고, 실제 generated JSON에서 204개 변수 정의·연도별 표·집단 비교·상관·VIF를 읽어 표와 상세 블록으로 표시했다. 감사된 Markdown은 `web/public/docs/`에 generator가 복사해 `MarkdownLite`로 화면에 렌더링한다. A4 print stylesheet와 모바일 레이아웃도 추가했다.
- 검증: `python scripts/generate_web_analysis_data.py`, `python -m py_compile scripts/generate_web_analysis_data.py`, `cd web && npm run build`, Vite preview HTTP smoke test를 통과했다. 로컬 환경에 Chromium/Playwright가 없어 실제 screenshot 브라우저 테스트는 보류했다.
- 상태: 코드 수준의 루트 재구성은 해결됨. production 배포와 브라우저 screenshot은 push 이후 별도 확인이 필요하다.

## 2026-08-02 - production asset 반영과 브라우저 검증 환경 제한

- 확인: `5595ff3` push 후 `https://s-p500.pages.dev/`가 HTTP 200을 반환했고, 초기 캐시 응답 이후 최신 `index-wyBcecrj.js`와 `index-DXe8XX9p.css` asset으로 갱신되었다.
- 확인 내용: 최신 JavaScript asset에 `연구 요약`, `표본 구축`, `변수 측정`, `분석 결과`, `Fog Index 구현식`, `Loughran–McDonald`가 포함되고 CSS에 `@media print`가 포함된다.
- 제한: 실행 환경에 브라우저 실행 파일과 Playwright가 모두 없어 실제 DOM screenshot·mobile viewport·navigation click 검증은 재현할 수 없었다. HTTP endpoint와 정적 asset 검증으로 대체했으며, 이는 사용자 지정 PASS 조건의 브라우저 검증을 충족하지 않는다.

## 2026-08-02 - Loughran–McDonald 축약 표기 제거

- 문제: 웹 설명과 자동 생성 변수 정의에 `LM` 축약이 남아 있어 공식 명칭 표기가 일관되지 않았다.
- 조치: 사용자 표시 문구와 수식을 `Loughran–McDonald`로 통일하고 generic variable display name도 `lm` token을 공식 명칭으로 확장했다.
- 검증: UI·config·웹 Markdown에서 standalone `LM` 검색 0건, pytest 9건과 frontend build 통과. 데이터 열 이름은 변경하지 않았다.

## 2026-08-02 - 전체 평균 및 연구 설명 확장

- 문제: 전체 연도 카드가 연도별 평균의 단순평균을 사용했고, 방법론·결과·재현성·한계 설명이 별도 문서에만 축약되어 있었다.
- 조치: `summary.descriptiveTable`의 source 전체 평균을 사용하도록 수정하고, 실제 source 경로 검증 및 상세 연구 페이지를 추가했다.
- 검증: source dataset·script 204개 정의 검증, 관련 pytest 8건, frontend build, `git diff --check` 통과.

## 2026-08-02 - 배포 JSON 열 이름 불일치로 인한 빈 화면

- 관찰: `https://s-p500.pages.dev/`와 `/data/analysis-summary.json`은 HTTP 200으로 응답했으므로 정적 파일 경로는 정상이었다.
- 원인: `summary.descriptiveTable`의 원자료 행에는 `N`, `standard_deviation`, `p25`, `p75`가 있었으나 React가 `item.n`, `item.sd`, `item.q1`, `item.q3`를 호출했다. `undefined.toLocaleString()`으로 첫 화면 렌더링이 중단될 수 있었다. 변수 정의 페이지의 문자열 metadata에 `.join()`을 호출하는 추가 오류도 확인했다.
- 수정: 생성기에서 `n`, `sd`, `q1`, `q3`, `kind`, `label` 별칭을 자동 생성하고, React에서 문자열·목록을 모두 처리하도록 수정했다. correlation 필드도 실제 `correlation` 열을 사용한다.
- 검증: 생성기, `py_compile`, 관련 pytest 5건, `npm run build`, `git diff --check` 통과. 원자료와 패널은 변경하지 않았다.

## 2026-08-02 - 웹 대시보드 로딩 중단 원인 및 수정

- 증상: Cloudflare Pages 화면이 로딩되지 않거나 로딩 상태에서 멈춤.
- 재현 근거: `App`가 `summary`가 없을 때 조기 반환한 뒤 데이터 수신 후에만 `useMemo`를 실행하여 Hook 호출 순서가 달라지는 코드 구조를 확인했다. React는 이 경우 Hook 순서 오류를 발생시킬 수 있다.
- 수정: `years`와 `selected` 계산을 조기 반환보다 앞에 배치해 모든 렌더에서 Hook 순서를 고정했다. `fetch` 응답 상태도 확인하고 실패 시 오류 원문과 재시도 버튼을 표시한다.
- 검증: `npm run build` 성공, `git diff --check` 성공. 기존 분석 데이터와 패널은 변경하지 않았다.

## 2026-08-02 - 연구 대시보드 자동 데이터 연결 검증

- 원인: 이전 화면이 수동 JavaScript 요약값을 사용해 원자료와의 자동 동기화가 보장되지 않았다. (codex)
- 조치: 분석 CSV와 확장 패널을 읽는 생성기를 추가하고 frontend를 정적 JSON fetch 방식으로 전환했다. (codex)
- 검증: source column, 기간, 행 수, 중복 key, 비율 범위 및 Infinity를 생성 단계에서 검사하도록 했다. (codex)

## 2026-08-02 - 2019–2017년 역사적 확장 작업의 실행 전 조건 기록

- 요청: 2019년부터 2017년까지 역순으로 역사적 S&P 500 표본을 복구하고, R2 저장·분석·Google Drive 이전을 반복한다. (codex)
- 확인: 현재 저장소의 기준 연도는 2020–2025년이며, R2는 이전 삭제 검증에서 빈 상태로 기록되어 있다. 역사적 구성종목 원천자료와 PR #2는 별도 검토가 필요하다. (codex)
- 안전 계획: 여러 연도 동시 실행을 금지하고, 연도별 `max-parallel: 1`, rate-limit 지연, checkpoint·resume, 수동 workflow를 사용한다. (codex)
- 표본 주의: 503 securities는 기존 5개 100행 batch만으로 처리할 수 없으므로 100·100·100·100·100·3의 6개 batch로 분할한다. (codex)
- 상태: 아직 workflow를 실행하지 않았고 SEC, R2, Google Drive 또는 기존 분석 결과를 변경하지 않았다. (codex)
- 감사 결과: `process-10k-yearly-batches.yml`, `run_yearly_10k_batch.py`, 추출기 및 language runner에 2025 pilot 경로와 1–5 batch 전제가 남아 있다. 이 전제를 전역 수정하지 않고 historical 전용 실행기로 분리하는 것이 안전하다. (codex)

## 2026-08-02 - 문서·버전 상태 전수조사

- 문제: 루트 README, 연도별 README, 인수인계 문서와 구성종목 방법 문서에 초기 파일럿 단계와 현재 2020–2025 완료 상태가 혼재했다. (codex)
- 조치: 현재 완료 표본, Google Drive 보관, R2 빈 상태, 2019–2017 역순 계획, historical 실행기 분리 원칙을 문서에 반영했다. `VERSION`은 실제 코드 릴리스가 아니므로 변경하지 않았다. (codex)
- 검증: 수정 문서의 상태·연도·버전 검색과 `git diff --check`를 수행한다. 기존 데이터와 외부 저장소는 변경하지 않는다. (codex)

## 2026-08-02 - Cloudflare Pages 루트 설정과 React 앱 경로 정렬

- 문제: Cloudflare Pages 입력은 Root directory `/`, Build command `npm run build`, Output directory `dist`로 저장되어 있으나 저장소에 frontend `package.json`이 없었다. (codex)
- 조치: 루트 `package.json`을 build shim으로 추가하고 실제 React + Vite 앱을 `web/`에 배치했다. `web/vite.config.js`는 빌드 결과를 루트 `dist/`로 출력한다. (codex)
- 안전: frontend는 `/api/summary`가 없을 때 기존 확정 표본 요약을 fallback으로 표시하며, raw HTML·R2 credential·Google OAuth 값은 포함하지 않는다. (codex)
- 검증: `npm install --prefix web --no-audit --no-fund`와 `npm run build`가 성공했다. Cloudflare 실제 배포는 아직 실행하지 않았다. (codex)

## 2026-08-02 - Cloudflare Pages 출력 디렉터리 불일치 수정

- 증상: Pages가 `web/dist`를 검증했지만 기존 Vite 설정이 루트 `dist`를 생성해 `Output directory "web/dist" not found`가 발생했다. (codex)
- 원인: Cloudflare Pages의 저장된 출력 경로와 Vite `outDir`가 서로 달랐다. (codex)
- 조치: `web/vite.config.js`의 `outDir`를 `dist`로 변경해 루트 build shim 실행 시 `web/dist`가 생성되도록 맞췄다. (codex)

## 2026-08-02 - Google Drive 신규 저장 형식 기본값

- 요청: 이후 Google Drive raw HTML 저장의 기본 형식을 `연도/번호_연도_기업명_SYMBOL_CIK.html`로 유지한다. (codex)
- 확인: 기존 migration 실행기는 `연도/sample_500/html/raw/CIK/accession.html` 중첩 형식을 기본으로 사용하고 있었다. (codex)
- 조치: `--drive-layout` 선택지를 추가하고 기본값을 `year_flat`으로 변경했다. 연도별 sample manifest에서 `sample_order`, `company_name`, `symbol`을 읽어 파일명을 결정하며, `legacy_nested` 옵션은 호환용으로 남겼다. (codex)
- 검증: `python -m py_compile scripts/migrate_r2_html_to_google_drive.py`, workflow YAML 파싱 및 `git diff --check`가 통과했다. Google Drive/R2 실데이터에는 접근하거나 변경하지 않았다. (codex)

## 2026-07-31 - Google Drive raw HTML 폴더 구조 변경 준비

- 요청: `연도/sample_500/html/raw/<leaf>/<raw HTML>` 구조를 `연도/<leaf>/<raw HTML>`로 변경한다. (codex)
- 확인: 저장소의 기존 migration 코드가 leaf 폴더를 ticker가 아닌 CIK 값으로 생성한다. 따라서 이번 변경에서는 식별자 이름을 임의로 ticker로 바꾸지 않고 기존 leaf 폴더와 파일을 그대로 이동한다. (codex)
- 조치: `flatten_google_drive_raw_html.py`와 수동 실행 전용 workflow를 추가했다. 파일별 이동이 아니라 leaf 폴더의 parent만 변경하며, 중복 목적지·예상치 못한 폴더·비어 있지 않은 wrapper는 안전하게 중단한다. (codex)
- 검증: Python compile과 YAML parsing을 통과했다. 실제 Drive 접근·dry-run·execute는 커밋 후 workflow에서 수행한다. (codex)

## 2026-07-31 - Google Drive raw HTML 파일명 변경 준비

- 요청: 폴더 평탄화 완료 후 파일명을 `0_기업명_SYMBOL_CIK.html` 형식으로 바꾼다. (codex)
- 판단: 기존 Drive 파일은 accession 이름이고 migration 코드상 leaf 폴더는 CIK이므로, 연도별 sample manifest를 accession·CIK 연결의 source of truth로 사용한다. (codex)
- 조치: 파일명만 변경하는 dry-run/execute workflow를 추가했다. 기존 파일 ID와 내용은 유지하고 중복 목적지·manifest 불일치는 중단한다. (codex)

최신 기록을 위쪽에 추가하고 기존 기록을 삭제하지 않는다.

## 2026-07-31 - Markdown 표시용 표 재생성 오류 수정

- 문제: 보고서 재생성기에서 문자열로 변환하기 전 `variable_1`·`variable_2` 값을 수치로 변환하려 해 `ValueError`가 발생했고, 정수 포맷이 연도에도 천 단위 구분을 적용했다. (codex)
- 원인: 표시용 표의 변수·분석 표본·방법 열에 문자열 처리 규칙이 없었고 `report_year`가 일반 정수 열과 같은 포맷 경로를 사용했다. (codex)
- 조치: 변수명은 백틱, 분석 표본은 한글, 방법명은 `Pearson`·`Spearman` 원문으로 유지하고 연도는 천 단위 구분 없이 표시하도록 수정했다. share 계열 행은 백분율로 표시했다. (codex)
- 검증: Markdown 재생성, `raw nan`·소수점 연도·`p = 0.0000`·영문 원자료 열 제목 0개, 관련 테스트 7개 및 `git diff --check` 통과를 확인했다. 기존 CSV·Parquet는 읽기 전용으로 유지했다. (codex)

## 2026-07-31 - 기술통계 파이프라인 검증 보완

- 문제: 초기 통계 quality check가 기존 `*_ratio` 열도 신규 0–1 share로 간주해 2,829건의 범위 위반을 보고했다. 기존 ratio 열은 역사적 단위를 유지해야 하므로 해당 검사는 잘못된 것이었다. (codex)
- 원인: 신규 proportion 검사 대상에 기존 ratio 열을 포함한 구현 오류였다. (codex)
- 조치: quality check를 신규 `*_share`와 `*_coverage` 열로 제한하고 기존 ratio 값은 변경하지 않았다. (codex)
- 추가 문제: correlation fixture에서 자기 자신과의 상관을 계산할 때 pandas 중복 열 이름으로 `Series`가 반환됐다. 대각선 pair를 단일 열 DataFrame으로 처리하도록 수정했다. (codex)
- 검증: `PYTHONPATH=. pytest -q tests/test_descriptive_analysis.py tests/test_extended_language_features.py` 결과 4 passed, 확장 패널 2,829행·204열, 기존 열 변경 셀 0, 중복·음수 count·share 위반·infinity 0을 확인했다. (codex)
- 상태: 해결됨. (codex)

## 2026-07-31 - 확장 언어 측정 smoke test

- 문제 1: spaCy dependency parser 4 worker가 긴 10-K를 동시에 처리하면서 `BrokenProcessPool`이 발생했다. 동일 18개 smoke 표본을 worker 1개로 재실행해 정상 완료했으며 전체 Actions도 연도별 job 내부 worker 1개로 고정했다. (codex)
- 문제 2: 최초 smoke 결과에서 AI 문장이 모두 0으로 연결됐다. 패널의 안정 `company_id`와 연도별 source ID가 다르기 때문이며, 고유 accession을 기준으로 AI 문장 상세를 연결하도록 수정했다. (codex)
- 입력 검증: 임시 extraction artifact와 저장소 pilot/recovery 텍스트를 합쳐 accession 2,829개가 패널 2,829행과 누락·중복 없이 일치한다. raw HTML 재다운로드·재추출은 수행하지 않는다. (codex)
- 상태: 관련 fixture는 통과했으며 accession 수정 후 18개 smoke 결과를 재확인하고 6개 연도 병렬 전체 측정을 진행한다. (codex)

## 2026-07-31 - R2 raw HTML 삭제 범위 고정

- 후속 문제: 사용자가 R2 데이터가 남아 있음을 확인했다. 최초 구현은 `DeleteObjects`의 `Quiet=True` 응답에서 `Errors`가 없으면 성공으로 계산했지만 실제 객체 부재를 확인하지 않아 성공 판정 근거가 불충분했다. (codex)
- 후속 조치: 전체 object 내용을 다운로드하거나 SHA를 재계산하지 않고, `ListObjectsV2` 결과와 manifest key 집합의 교집합만 계산하는 읽기 전용 `verify_absence` mode를 추가했다. 잔존 객체가 확인된 경우에만 해당 key 재삭제를 검토한다. (codex)
- 실제 확인: verify run `30618948813`에서 manifest 대상 2,829개 중 R2 잔존 key는 0개였다. 사용자가 확인한 잔존 데이터의 성격을 구분하기 위해 동일 목록 응답에서 버킷 전체 객체 수와 총 bytes도 민감정보 없이 집계하도록 보강했다. (codex)
- 최종 확인: verify run `30619115601`에서 R2 버킷 전체 목록은 객체 0개·0바이트였고 manifest 대상 및 manifest 외 잔존 객체도 각각 0개였다. 최초 성공 판정의 검증 공백은 해소됐으며 실제 bucket 데이터가 비어 있음을 API로 확인했다. (codex)
- 문제 요약: Google Drive 이전을 완료한 뒤 R2 비용을 중단하려면 bucket 또는 prefix가 아니라 검증 완료 manifest의 정확한 2,829개 object key만 삭제해야 한다. (codex)
- 확인: run `30544560261` artifact에서 manifest 2,829행, 고유 key 2,829개, 빈·중복 key 0개, 성공 상태 2,829개 및 failure CSV 데이터 행 0개를 확인했다. (codex)
- 조치: 기본 비삭제, `--execute` 명시, 기대 행 수·상태·중복·빈 key fail-closed, 최대 1,000개 batch 및 응답 `Errors` 기록을 구현했다. workflow execute에는 `DELETE_R2_RAW_HTML_2829` 확인 문자열과 단일 concurrency group을 적용했다. (codex)
- 검증: 실제 artifact dry run에서 2,829개가 모두 eligible이며 delete API 미호출을 확인했고, count 불일치·중복·빈 key·manifest 외 key 방지·API error 기록 mock test 6개가 통과했다. (codex)
- 실행 결과: workflow run `30618552630`은 2,829개 key를 1,000개 이하의 3개 batch로 delete 요청했고 응답 `Errors`는 0개였다. checkpoint 2,829행과 헤더만 있는 실패 CSV를 artifact로 확인했다. (codex)
- 상태: 해결됨. 객체별 HEAD·SHA 재검증이나 전체 다운로드는 반복하지 않았고, Google Drive·기존 패널·분석 결과는 수정하지 않았다. (codex)

## 2026-07-30 - Google Drive migration 연결 시험 분리

- 문제 요약: Codespaces에는 Google OAuth 값이 없고 repository secrets에만 설정되어 있어 로컬에서 Drive 연결과 실제 이전을 검증할 수 없다. (codex)
- 조치: secret 값을 출력하지 않는 GitHub Actions 전용 workflow를 만들고, 한 객체 시험과 전체 이전을 별도 dispatch mode로 분리했다. 시험은 OAuth refresh, root 접근·생성 권한, quota, R2 연결, upload 검증 및 재실행 skip을 모두 확인한다. (codex)
- 안전장치: Drive 기존 동일 파일의 size 또는 SHA가 다르면 conflict, 동명 파일·폴더가 복수이면 ambiguous로 중단하며 R2와 Drive 기존 파일을 overwrite하거나 삭제하지 않는다. (codex)
- 검증 결과: run `30543859858`에서 secret 이름 네 개는 repository metadata에 존재했지만 실제 job에는 `GOOGLE_DRIVE_CLIENT_ID`와 `GOOGLE_DRIVE_CLIENT_SECRET`이 빈 값으로 주입됐다. 나머지 Google 두 변수와 R2 네 변수는 set으로 확인됐다. (codex)
- 상태: OAuth 요청 전 안전하게 중단했으며 `test` mode가 성공해야만 `full` mode를 실행한다. 누락된 두 secret을 비어 있지 않은 값으로 다시 저장해야 한다. (codex)

## 2026-07-30 - SnowballC와 NLTK Porter 직접 비교 확인

- 문제 요약: 기존 구체성 측정에는 SnowballC 0.7.0과 NLTK 3.10.0 ORIGINAL_ALGORITHM의 직접 비교가 남아 있었다. (codex)
- 조치: 활용형, 다단계 접미사 및 경계 사례를 포함한 고정 fixture 36개를 두 구현에 입력하고 token별 stem을 비교했다. (codex)
- 검증: 최초 CSV의 기본 CRLF가 `git diff --check`에서 trailing whitespace로 감지되어 생성기의 줄바꿈을 LF로 고정했다. 재생성 후 fixture 36개 모두 동일, 차이 0개, CSV 36행 및 `git diff --check` 통과를 확인했으며 전체 테스트는 실행하지 않았다. (codex)
- 상태: fixture 범위에서는 동일하다. 전체 동등성 검증이나 기존 구체성 결과 재측정은 수행하지 않았고, 향후 차이가 발견될 경우에만 확대 비교를 검토한다. (codex)

## 2026-07-29 - R runtime 부재와 SnowballC 버전 고정

- 문제 요약: 구체성 단계에서 R runtime이 없어 SnowballC 0.7.0을 직접 실행할 수 없었다. (codex)
- 원인: Codespaces 기본 환경에 `R`과 `Rscript` 실행 파일이 설치되어 있지 않았다. (codex)
- 조치: Ubuntu `r-base`·`r-base-dev`를 설치하고 CRAN archive의 정확한 SnowballC 0.7.0을 Git 제외된 프로젝트 library에 source build했다. (codex)
- 검증: R 4.3.3, packageVersion 0.7.0, package 경로 및 wordStem의 6개 입력·6개 비결측 출력 조건을 확인했다. 기존 구체성 산출물은 재생성하지 않았다. (codex)
- 상태: 환경 고정은 해결됨. NLTK와의 직접 stem 비교는 후속 범위로 남는다. (codex)

## 2026-07-29 - Baek Appendix A와 공식 source metadata 차이

- 문제 요약: Baek et al. Appendix A는 SMART stopword 1,149개라고 기술하지만 tidytext 0.3.1의 공식 문서는 1,149가 세 lexicon 전체 행 수라고 설명한다. 공식 RDA의 SMART는 571행이며 `would` 중복을 제거하면 570개다. 논문 예제의 `subject=3.13`도 공식 Brysbaert XLSX의 3.14와 다르다. (codex)
- 원인: Appendix의 lexicon별 행 수 표현과 예제 표시값이 공식 배포 파일의 실제 값과 일치하지 않는다. 참가자 원자료를 재집계하거나 값을 임의 수정하지 않았다. (codex)
- 조치: 공식 SMART subset 570고유 항목을 사용하고 차이를 metadata에 기록했다. 공식 subject 3.14를 사용한 raw 평균 3.105/2.965를 2자리로 반올림해 보고된 3.10/2.96 fixture를 재현했다. (codex)
- 추가 검토: dictionary Porter stem 6,956개가 다중 entry collision이었다. exact original을 우선하고 unique stem만 fallback으로 허용하며 collision은 unmatched 처리했다. (codex)
- 검증: loader, 예제, fixture, 5개 결과 및 품질검사는 통과했다. R SnowballC 0.7.0 runtime은 환경에 없어 NLTK 3.10.0 original Porter fixture로 고정했다. (codex)
- 상태: source 차이는 설명된 warning이며 구조 오류는 없다. (codex)

## 2026-07-29 - LM 재배포와 TECH 분모 0 처리

- 문제 요약: 공식 페이지는 학술 연구 무료 사용을 명시하지만 원본 또는 전체 파생 사전의 공개 Git 재배포 허용은 명시하지 않았다. 최초 LM 적용 품질검사는 TECH의 eligible word count가 0인 것을 missing으로 기대해 실패했다. (codex)
- 원인: 연구 사용과 재배포 권한은 별개이며, TECH는 AI 관련 문장이 없어 count와 ratio의 해석 가능한 분모가 없지만 eligible word count 자체는 0으로 기록된다. (codex)
- 조치: 원본·전체 파생 사전을 `.gitignore`로 제외하고 SHA와 설치 절차만 추적했다. TECH의 LM count·ratio·net tone은 missing, eligible word count는 0, 상태는 `warning_denominator_zero`로 명시했다. (codex)
- 검증: loader는 86,553행과 7개 필수 범주를 확인했고 음수 source value 19개가 활성화되지 않았다. 품질검사와 전체 53개 테스트가 통과했다. (codex)
- 상태: 해결됨. 사전 재배포 조건은 보수적으로 unclear로 유지한다. (codex)

## 2026-07-29 - 언어 smoke-test 모듈 import 경로

- 문제 요약: 최초 신규 테스트 실행에서 4개 test module이 `language_measurement_common`을 찾지 못해 import error로 실패했다. (codex)
- 원인: 신규 스크립트가 CLI 직접 실행 경로만 가정했고 기존 테스트의 `scripts.*` package import 경로를 지원하지 않았다. (codex)
- 조치: 관련 모듈에 package-relative import와 CLI fallback import를 함께 적용했다. 측정 산출물이나 검증 기준은 변경하지 않았다. (codex)
- 검증: 수정 후 기존 30개와 신규 15개를 합한 45개 테스트, `py_compile`, smoke-test 품질검사 및 `git diff --check`가 통과했다. (codex)
- 상태: 해결됨. 별도로 확인된 사전·dependency model 부재는 오류가 아니라 명시적 blocked dependency다. (codex)

## 2026-07-29 - 10-K section 후보 및 표 표식 오탐

- 문제 요약: 최초 parser가 Item 7을 6개 기업에서만 탐지하고 분석 본문 61개에 내부 표 제거 표식을 남겼다. (codex)
- 원인: `Item 1` 정규식이 `Item 15/16`까지 허용해 문서 끝 후보를 선택했고, 중첩 block이 하위 표 표식을 다시 포함했다. (codex)
- 조치: Item 번호 경계를 엄격히 하고, 실제 본문 heading 점수 임계값과 순서를 적용했으며 상위 block의 표 표식을 제거했다. optional section 경고와 핵심 회사 경고도 분리했다. (codex)
- 검증: Item 7 탐지는 84개로 개선됐고 표 표식·HTML·script/style·XBRL 오염은 모두 0이다. 탐지되지 않은 16개와 경계가 짧은 핵심 section은 warning으로 보존했다. (codex)
- 상태: 추출 pipeline은 완료됐으나 WFC 등 table-layout 및 multi-registrant section 경계는 다음 parser 개선 대상으로 남는다. (codex)

## 2026-07-29 - 대용량 문장 CSV

- 문제 요약: 비압축 `sentences.csv`가 103,370,905바이트로 GitHub 단일 파일 제한 위험이 있었다. (codex)
- 조치: 문단·문장 상세표를 gzip CSV로 직접 생성·검증하도록 변경하고 소규모 요약 CSV와 `sections.csv`는 유지했다. (codex)
- 검증: 압축 후 문단 파일 약 15MB, 문장 파일 약 18MB이며 품질검사에서 원래 141,796행과 298,250행을 모두 읽었다. (codex)
- 상태: 해결됨. (codex)

## 2026-07-29 - HTML 다운로드 요약 HTTP 상태 타입 오류

- 문제 요약: 100개 요청과 파일 저장은 모두 성공했지만 최초 실행 summary가 `http_failures=100`을 출력하고 종료 코드 1을 반환했다. (codex)
- 원인: manifest 생성 중 HTTP 상태는 정수 `200`이었으나 요약 코드가 문자열 `"200"`과 직접 비교했다. (codex)
- 조치: 비교 전에 HTTP 상태를 문자열로 정규화했다. 파일·manifest·로그는 실제 성공 결과와 일치해 재다운로드하지 않았다. (codex)
- 검증: 재실행에서 기존 100개 파일이 모두 SHA 일치로 skip되었고 `http_failures=0`, 실패 0, 고유 SHA 100을 확인했다. (codex)
- 상태: 해결됨. (codex)

## 2026-07-29 - 교체 스크립트 반복 실행 상태 검증

- 문제 요약: 최초 교체 적용 후 같은 명령을 다시 실행하면 TXT manifest가 이미 `excluded_after_filing_validation` 상태여서 초기 `no_eligible_2025_10k` 전제 검사가 실패했다. (codex)
- 원인: 입력 audit 상태가 첫 실행 결과로 정상 전환되는 점과 기존 생성 ITW 행을 고려하지 않아 반복 실행 가능성이 부족했다. (codex)
- 조치: 두 TXT audit 상태를 모두 엄격한 accession 결측 조건과 함께 허용하고, 생성된 ITW·review·summary·exclusion 행을 ID로 제거한 뒤 재생성하도록 했다. (codex)
- 검증: 교체 스크립트를 연속 두 번 실행해 두 실행 모두 최종 100개, eligible 100개, 고유 CIK·accession 100개 및 Industrials 16개를 출력했고 unit test 13개가 통과했다. (codex)
- 상태: 해결됨. 네트워크 integration은 코드 변경에 필요하지 않아 재실행하지 않았다. (codex)

## 2026-07-29 - TXT 2025 reportDate 10-K 부재 조사

- 문제 요약: TXT에는 정확한 Form 10-K가 있지만 reportDate 2025 조건을 충족하는 filing이 없었다. (codex)
- 확인: SEC recent와 historical fragment 전체를 확인했으며 2025-02-06 filing은 reportDate 2024-12-28, 2026-02-11 filing은 reportDate 2026-01-03이다. fiscal year end metadata는 `0102`다. (codex)
- 결론: filingDate 기준으로 대체하지 않고 `no_eligible_2025_10k`를 유지한다. 결정론적 Industrials 예비 1순위 ITW를 교체 후보로만 제안했다. (codex)
- 상태: 원인 확인 및 교체 근거 생성 완료. 실제 교체는 사용자 결정 대기 중이다. (codex)

## 2026-07-29 - historical submissions 과다 순회 및 일시적 연결 오류

- 문제 요약: 최초 전체 실행이 오래된 historical fragment를 모두 순회하여 시간 한도에 도달했고, 중첩 실행 중 2개 기업에서 일시적 `URLError`가 기록됐다. (codex)
- 원인: fragment의 `filingFrom`·`filingTo` 범위를 적용하지 않은 과도한 조회와 일시적 네트워크 연결 실패였다. (codex)
- 조치: 2025-01-01부터 cutoff 2026-07-29와 겹치는 fragment만 조회하고 URL cache를 사용해 전체 산출물을 재생성했다. 기존 요청 로그는 감사 목적으로 보존했다. (codex)
- 검증: 최종 100개 metadata 응답 성공, 99개 eligible, 1개 no eligible, accession 중복 0 및 eligible primary document 결측 0을 확인했다. (codex)
- 상태: 수집 오류는 해결됨. manual review 3건은 후속 판단 대상으로 남았다. (codex)

## 2026-07-29 - integration smoke test import 경로

- 문제 요약: `python tests/integration_sec_smoke.py` 실행 시 저장소 루트가 모듈 경로에 없어 `scripts` import가 실패했다. (codex)
- 조치: 테스트가 계산한 저장소 루트를 `sys.path`에 명시적으로 추가했다. (codex)
- 상태: 수정 후 2개 기업 smoke test를 다시 실행하여 확인한다. (codex)

## 2026-07-29 - SEC User-Agent 미설정

- 문제 요약: SEC submissions와 Archives 수집에 필요한 `SEC_USER_AGENT` 환경변수가 설정되지 않았다. (codex)
- 관찰 결과: 사전 점검에서 `SEC_USER_AGENT_SET=no`를 확인했다. (codex)
- 조치: SEC 네트워크 요청을 수행하지 않고 비네트워크 표본 추출과 unit test까지만 완료했다. (codex)
- 상태: 미해결. 식별 가능한 실제 연구자 User-Agent 설정 후 integration 수집을 재개해야 한다. (codex)

## 2026-07-24 - 구조 설명 및 데이터 검증 공백 점검

- 문제 요약: 루트 README가 연도별 폴더만 설명해 전체 경로와 파일별 역할을 한눈에 확인하기 어려웠고, 기존 검증은 schema·key·원본 hash 손상을 탐지하지 못했다. (codex)
- 원인: 연도별 목록 최초 구축 시 행 수와 ticker 고유성 중심으로 최소 검증을 구현했으며 전체 구조 명세와 열 수준 검증은 포함하지 않았다. (codex)
- 조치: 주석형 전체 트리와 상세 파일 가이드를 추가하고 필수 열, 기업 키, CIK 형식, manifest 경로 및 원본 SHA-256 검증을 구현했다. (codex)
- 검증: `python scripts/validate_annual_constituents.py`, `python -m py_compile scripts/*.py`, `git diff --check`가 모두 통과했다. (codex)
- 상태: 해결됨. (codex)

## 2026-07-24 - GitHub 대용량 원본 blob 전송 잘림

- 문제 요약: 일반 `git push`가 HTTPS 자격 증명 부재로 실패한 뒤 GitHub Git Data API로 반영했으나, 원본 스냅숏 3개가 전송 중 약 786KB로 잘렸다. (codex)
- 관찰 결과: SEC JSON, 역사 구성종목 CSV, Wikipedia HTML의 원격 크기가 각각 786443-786445바이트였고 로컬 원본 크기 797926, 5526653, 1508704바이트와 달랐다. (codex)
- 원인: 로컬 파일을 base64로 읽는 중간 명령 출력에 단일 호출 크기 한도가 적용되어 전체 payload가 blob 생성 전에 잘렸다. (codex)
- 조치: 원본을 3의 배수 크기인 570000바이트 단위로 읽어 base64 조각을 결합한 뒤 각 전체 blob을 다시 생성했다. 일반 HTTPS 인증 실패는 자격 증명을 저장하지 않고 연결된 GitHub 권한을 사용해 처리했다. (codex)
- 검증: 원격 파일 크기, manifest SHA-256, 전체 Git tree SHA를 로컬과 대조한다. (codex)
- 상태: 원격 교체 및 최종 대조 후 해결로 확정한다. (codex)

## 2026-07-24 - Wikipedia 변경 이력만 사용한 역산의 행 수 불일치

- 문제 요약: Wikipedia 현재 구성표에서 `Selected changes`를 역적용한 초기 결과가 연도별 기대 종목 수보다 1개 이상 많았다. (codex)
- 관찰 결과: 초기 기업 단위 행 수는 2020-2021년 502개, 2022-2025년 501개였으며 정확한 500개 기업 표본이 되지 않았다. (codex)
- 원인: Wikipedia 표가 전체 변경이 아닌 `Selected changes`이고, 분사·ticker 변경·비대칭 추가 및 제외 사건이 있어 그 표만으로 정확한 과거 집합을 복원할 수 없다. (codex)
- 조치: Wikipedia 역산을 메타데이터의 기본으로 유지하되 일자별 역사 구성종목 자료로 기준일 ticker 집합을 교차검증하고, SEC ticker 자료로 CIK를 보완했다. 보정 ticker는 manifest에 연도별로 기록했다. (codex)
- 검증: 기업 목록 6개가 각각 500행이며 종목 목록이 기대 행 수와 일치하고 ticker가 고유한지 자동 검사했다. (codex)
- 상태: 구성종목 집합의 행 수 불일치는 해결했으며 과거 편출기업의 일부 CIK·GICS 결측은 후속 보완 대상으로 남겼다. (codex)

## 2026-07-24 - Wikipedia 표 헤더 파싱 오류

- 문제 요약: 최초 실행에서 변경 표 탐색의 `StopIteration`과 날짜 열의 `KeyError`가 순차적으로 발생했다. (codex)
- 원인: 변경 표가 중복된 다중 헤더를 사용하고 실제 날짜 열 이름이 `Effective Date`인데 초기 코드가 평탄화된 단일 `Date` 헤더를 가정했다. (codex)
- 조치: 구성기업 표와 변경 표 파서를 분리하고 다중 헤더 `('Effective Date', 'Effective Date')`를 명시적으로 사용했다. (codex)
- 검증: 동일 원본 스냅숏을 사용한 생성 스크립트가 정상 완료되고 6개 연도 검증이 통과했다. (codex)
- 상태: 해결됨. (codex)

## 2026-07-24 - 연도별 폴더 Git 추적 검증

- 문제 요약: Git은 내용이 없는 디렉터리를 추적하지 않으므로 연도별 빈 폴더만 생성하면 원격 저장소에 반영되지 않는다. (codex)
- 재현 조건: 내용이 없는 `2020/`-`2025/` 디렉터리를 만들고 `git status --short`를 실행하면 신규 경로가 표시되지 않는다. (codex)
- 원인: Git의 추적 단위는 디렉터리가 아니라 파일이다. (codex)
- 조치: 각 연도 폴더에 표본 기준과 용도를 설명하는 `README.md`를 추가했다. (codex)
- 검증: `git diff --check`와 6개 연도별 `README.md` 존재 검사가 통과했으며, `git status --short`에서 의도한 연도 폴더와 문서 변경만 확인했다. (codex)
- 상태: 연도별 폴더가 파일을 포함하여 Git과 GitHub에서 추적 가능한 상태로 구성되었다. (codex)

## 2026-07-20 - 초기 상태 확인

- 문제 요약: 저장소가 커밋과 파일이 없는 빈 상태였다. (codex)
- 관찰 결과: `main` 브랜치에 커밋이 없었고 `origin/main` 원격 추적 브랜치도 아직 생성되지 않았다. (codex)
- 원인: 신규 GitHub 저장소에 초기 콘텐츠가 추가되지 않은 상태였다. (codex)
- 조치: 저장소 운영 규칙과 기록 파일을 최초 버전으로 구성했다. (codex)
- 검증: `git diff --check`가 오류 없이 통과했고, `git status --short`에서 의도한 초기 파일만 신규 파일로 확인했다. (codex)
- 상태: 저장소 관리 체계를 구성하여 해결했다. (codex)
## 2026-08-02 - 대시보드 발표형 레이아웃 보완

- 문제 요약: 기존 화면은 모바일형 카드와 단일 표 중심이라 데스크탑에서 발표 자료처럼 핵심 흐름을 빠르게 파악하기 어려웠다. (codex)
- 참고: UI 요소를 공간으로 그룹화하고, 시각적 위계를 분명히 하며, 색상·대비·타이포그래피를 목적에 맞게 제한하라는 공개 UI 지침을 확인했다. (codex)
- 조치: `web/src/App.jsx`에 탐색 영역, 핵심 메시지 headline, KPI, CSS 막대그래프, 표본 표와 연구 주석을 구성하고 `web/src/styles.css`에 데스크탑 우선 반응형 스타일을 적용했다. (codex)
- 안전: 디자인 이미지를 생성하지 않았고, 기존 집계 fallback 값과 API 경로를 유지했다. (codex)
- 검증: 빌드 및 diff 검증 후 Cloudflare Pages에서 최신 `main` 커밋을 재배포해야 한다. (codex)
## 2026-08-02 - 패널 분석값의 대시보드 표시 누락

- 문제 요약: 초기 대시보드는 연도별 관측치·AI 공시 수만 표시하여 확장 패널의 언어 지표와 구조적 요약을 충분히 노출하지 않았다. (codex)
- 원인: UI scaffold가 API fallback용 최소 연도 배열만 사용하고, `analysis/descriptive_2020_2025/figures/figure_aggregate_data.csv`의 확장 열을 연결하지 않았다. (codex)
- 조치: 패널 산출값에서 생성한 표시용 요약 모듈을 추가하고 연도별 언어 지표 표·핵심 변화·상관관계 주의사항을 대시보드에 연결했다. (codex)
- 검증: `npm run build` 성공, `git diff --check` 통과. (codex)
## 2026-08-02 - 대시보드 연구 맥락 정보 부족

- 문제 요약: 분석값은 표시했지만 데이터 수집 경로, 변수 정의, 통계 절차 및 결과 해석을 한 화면에서 확인하기 어려웠다. (codex)
- 조치: 네 단계 접이식 섹션을 추가해 수집 방법·변수·분석·결과를 기존 문서와 확장 패널 산출값에 맞춰 설명했다. (codex)
- 안전: 수치 재계산이나 패널 변경 없이 표시용 컴포넌트와 스타일만 확장했다. (codex)
- 검증: 빌드 및 diff 검증 후 Cloudflare Pages 최신 배포에서 확인한다. (codex)
## 2026-08-02 - 대시보드 수식 및 측정 정의 누락

- 문제 요약: 변수명과 결과값은 표시했지만 분석자가 분자·분모와 결측 처리 규칙을 화면에서 확인할 수 없었다. (codex)
- 조치: 수식·측정 방법 카드를 추가해 기존 `measurement_design.csv`, `measurement_notes.md`, 변수 사전의 규칙을 표시했다. (codex)
- 검증: 수치 재계산 없이 `npm run build`와 `git diff --check`를 수행한다. (codex)
## 2026-08-02 - 문헌 배경 표시 범위 정정

- 문제 요약: `문헌정리.pdf`의 목적이 문헌 근거 표시가 아니라 계산식과 측정 형식 확인이었는데, 대시보드에 문헌 카드가 추가되었다. (codex)
- 조치: 문헌 카드와 문헌 연구 배경 표현을 제거하고 수식·측정 방법 섹션은 보존했다. (codex)
- 검증: PDF 원문이나 내용은 저장소에 추가하지 않았으며 빌드와 diff 검증을 다시 수행한다. (codex)
## 2026-08-02 - 논문용 기술통계·결정요인 표 형식 보완

- 문제 요약: 대시보드 표가 화면용 요약에 치우쳐 논문용 `Mean`, `Std Dev.`, `Q1`, `Median`, `Q3`, `N` 형식을 직접 제공하지 않았다. (codex)
- 조치: 실제 기술통계 CSV에서 존재하는 변수만 Table 1로 표시하고, Table 2는 후속 회귀 설계 상태로 명시했다. (codex)
- 제한: 현재 분석 범위에는 재무 통제변수와 결정요인 회귀 결과가 없으므로 예시의 coefficient·t-stat·유의확률을 복제하지 않았다. (codex)
- 검증: `npm run build`, `git diff --check`를 수행한다. (codex)
## 2026-08-02 - Table 2 제거

- 조치: 회귀계수·t-stat을 포함하지 않는 설계표도 현재 화면에 불필요하다는 요청에 따라 제거했다. (codex)
- 상태: Table 1 기술통계표와 기존 측정 설명만 남겼다. (codex)
