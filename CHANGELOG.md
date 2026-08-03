# Changelog

## 2026-08-03

- Fixed: historical dashboard generation now installs the PyYAML dependency required by `generate_web_analysis_data.py`. (codex)

## 2026-08-03

- Fixed: yearly batch runner가 package import와 direct script 실행 모두에서 관련 `scripts` 모듈을 로드하도록 import fallback을 보정했다. (codex)

## 2026-08-03

- Added: 기존 2019 constituent universe를 사용해 SEC filing metadata만 수집하는 collection-ready manifest adapter를 추가하고, continuous workflow가 manifest를 생성·artifact로 matrix job에 전달하도록 연결했다. (codex)

## 2026-08-03

- Fixed: SEC ticker metadata를 현재 branch의 `data/raw`와 복구 cache에서 먼저 검증·재사용하고, 유효 cache가 있으면 네트워크 요청을 0회로 유지하도록 constituent reconstruction을 수정했다. cache SHA-256·source path·origin·network 여부·timestamp를 manifest와 chain state에 기록한다. (codex)
- Added: 손상 cache 거부, 결정론적 cache 선택, SEC 요청 최대 1회, HTTP 403 non-retryable 기록 및 `SEC_USER_AGENT` 환경변수 검증을 위한 직접 테스트를 추가했다. (codex)
- Added: source-supported historical constituent builder와 continuous workflow의 cache preflight를 연결했다. 2020–2025 production panel/dashboard, R2 및 Google Drive는 변경하지 않았다. (codex)

## 2026-08-02

- Changed: yearly 10-K runner가 firm-level manifest를 최대 503개까지 검증하고 100개 단위 최대 6개 batch로 순서 보존 분할하도록 일반화했다. 기존 R2 overwrite 방지와 2025 경로 호환성은 유지한다. (codex)
- Changed: batch runner의 임시 HTML·텍스트·언어 경로를 `report_year/sample_namespace` 기준으로 계산하고, extraction·language 단계가 해당 동적 경로를 사용하도록 연결했다. (codex)
- Added: six-batch summary range 검증과 503개 fixture 기반 batch coverage 테스트를 추가했다. 실제 SEC·R2·Google Drive 쓰기는 수행하지 않았다. (codex)

## 2026-08-02

- Added: 기존 분석 figure CSV를 source로 사용하는 논문용 반응형 SVG Figure 7종, Figure manifest, source CSV 다운로드 및 웹 Figure 감사 문서를 추가했다. (codex)
- Changed: 연구보고서의 분석 결과 절에 AI 공시 확산·강도·구체성·시제·Loughran–McDonald·효과크기·동일 기업 변화 Figure를 통합했다. (codex)
- Tested: Figure source 검증, Python 관련 테스트, Vite build 및 local preview Playwright desktop/mobile 검증을 실행했다. production HTTP asset 반영은 확인했으나 원격 Chromium sandbox 오류로 DOM 검증은 보류했다. (codex)

## Unreleased

- Fixed: production blank screen의 실제 원인은 `docs` 객체가 설정되기 전에 `docs.limitations`를 읽은 React 런타임 예외였으며, 선택 데이터 로딩을 `Promise.allSettled()`로 분리하고 기본값·section error를 추가했다. (codex)
- Added: `ErrorBoundary`, Playwright production/local smoke test, desktop·mobile screenshot 생성 및 `test:browser` script를 추가했다. (codex)
- Fixed: 모바일 source note와 표가 body 폭을 밀어내던 overflow를 수정했다. (codex)

- Changed: 루트 Cloudflare Pages 화면을 발표형 카드 대시보드에서 논문 보고서형 통합 문서로 재구성하고, 표·수식·source note·변수 정의 부록을 실제 분석 JSON과 연결했다. (codex)
- Added: production preview에서 제공할 감사된 방법론·결과·한계·재현성 Markdown 사본과 A4 인쇄용 stylesheet를 생성한다. (codex)

- Changed: 웹 화면과 생성 문서의 표시용 `LM` 축약을 `Loughran–McDonald`로 통일하고, `lm_` 데이터 열 이름만 호환성을 위해 유지했다. (codex)

- Expanded: 전체 연도 평균을 source 전체 평균으로 연결하고, 실제 source 경로 검증·결과/재현성/한계 페이지·추가 JSON/CSV 산출물을 연구 대시보드에 추가했다. (codex)

- Fixed: 실제 descriptive statistics 열 이름과 화면 renderer의 별칭 불일치로 발생한 초기 렌더링 예외를 수정하고, 변수 정의 페이지의 문자열·목록 metadata를 모두 안전하게 표시하도록 보완했다. (codex)

- Fixed: 초기 데이터 로딩 중 조기 반환으로 React Hook 호출 순서가 달라져 화면이 멈출 수 있던 문제를 수정하고, 정적 분석 JSON 요청 실패 메시지와 재시도 UI를 추가했다. (codex)

- Added: 실제 분석 CSV·패널에서 웹 JSON을 생성하고 논문 부록 수준의 변수 정의, source metadata, `/variables`·`/methods` 페이지를 제공한다. (codex)

- Changed: Google Drive 평탄화 후 raw HTML 파일명을 `0_기업명_SYMBOL_CIK.html` 형식으로 변경하는 별도 수동 workflow를 추가했다. 파일 내용과 Drive file ID는 유지하고, manifest와 일치하지 않는 파일은 덮어쓰지 않는다. (codex)

- Changed: Google Drive raw HTML 폴더를 연도 바로 아래 leaf 폴더로 평탄화하는 수동 workflow와 실행기를 추가했다. 파일 내용과 파일명은 변경하지 않고, 중복 목적지는 덮어쓰지 않는다. (codex)

이 저장소의 모든 주요 변경 사항을 기록한다. 버전 형식은 Semantic Versioning을 따른다.

## [Unreleased]

- Reverted: 대시보드에서 Table 2 결정요인 분석 설계표를 제거하고 Table 1 기술통계표만 유지했다. (codex)
- Reverted: `문헌정리.pdf`를 문헌 배경으로 표시한 대시보드 영역을 제거하고, 해당 자료는 수식·측정 형식 확인에만 사용하도록 정정했다. (codex)
- Added: 논문 표 형식에 맞춘 `Table 1 · Descriptive statistics` 요약표와, 계수를 임의로 채우지 않는 `Table 2 · Determinants design` 분석 설계표를 대시보드에 추가했다. (codex)
- Added: `문헌정리.pdf`를 검토해 AI 공시, 금융 텍스트 사전, 10-K 가독성·복잡성, 미래지향·구체성 문헌과 본 연구의 측정 위치를 대시보드에 추가했다. (codex)
- Changed: 2020–2025 확장 패널의 연도별 AI 공시, AI 직접 문장 수, 구체성, 시제, LM uncertainty, Fog Index 및 주요 상관관계를 대시보드에 반영했다. (codex)
- Added: 대시보드에 SEC·CIK·Form 10-K 수집 방법, 변수 정의, 기술통계·변화·상관·VIF 분석 방법과 핵심 결과를 펼쳐 볼 수 있는 연구 맥락 섹션을 추가했다. (codex)
- Added: 대시보드 연구 맥락에 `ai_disclosure`, 시제·수동태·LM·Fog·구체성의 분자·분모·수식·결측 처리 및 측정 한계를 추가했다. (codex)
- Changed: Cloudflare Pages 대시보드를 데스크탑 발표 화면에 가까운 sidebar·headline·KPI·차트·표 구조로 재배치하고, 검색해 확인한 UI 원칙에 맞춰 여백·위계·대비·일관성을 정리했다. (codex)
- Added: Cloudflare Pages 루트 빌드 설정과 호환되는 `web/` React + Vite dashboard scaffold를 추가했다. 루트 `npm run build`는 `web`을 빌드해 `dist/`를 생성하며, 비밀정보와 raw HTML은 포함하지 않는다. (codex)
- Docs: 루트·연도별 README, 인수인계, repository structure, sample definition 및 constituent method 문서를 현재 2020–2025 완료 상태와 2019–2017 역사 확장 계획에 맞게 정리했다. `VERSION`은 `0.12.0`으로 유지했다. (codex)
- Docs: 기존 2020–2025 실행기의 2025 pilot 경로·1–5 batch 하드코딩을 감사하고, historical 처리는 기존 pipeline을 깨뜨리지 않는 전용 runner/workflow로 분리해야 함을 기록했다. (codex)
- Changed: Google Drive 신규 migration의 기본 저장 형식을 `연도/번호_연도_기업명_SYMBOL_CIK.html`로 고정하고, 기존 중첩 폴더 형식은 `legacy_nested` 호환 옵션으로만 유지한다. (codex)
- Docs: 기술통계 Markdown 보고서와 논문용 표를 한글 표시용 열 제목, 정수·백분율·p-value 형식, 구조적 결측 기호, 4개 연도별 패널 및 2023년 구조 변화 해석으로 보완했다. (codex)
- Analysis: 2020–2025년 2,829 firm-year 패널에 기존 측정값을 보존한 확장 패널, 시제·수동태·AI Fog 및 텍스트 통제변수, 기술통계·상관관계·VIF·한글 보고서와 그래프를 추가했다. (codex)
- Added: 2020–2025 firm-year 패널에 공개 spaCy POS/dependency 기반 시제·수동태와 AI Fog·텍스트 통제를 추가하는 연도별 병렬 측정 workflow 및 확장 패널 builder를 추가했다. (codex)
- Fixed: R2 multi-delete의 quiet 응답만으로 성공을 추정하지 않고 bucket 목록과 migration manifest를 대조해 실제 잔존 객체 수를 확인하는 읽기 전용 검증 mode를 추가했다. (codex)
- Added: Google Drive 이전이 검증된 manifest의 R2 raw HTML key만 최대 1,000개 단위로 삭제하고 API 오류를 감사하는 수동 실행기와 GitHub Actions workflow를 추가했다. (codex)
- Added: R2 manifest에 고정된 2020–2025 raw 10-K HTML을 overwrite 없이 Google Drive로 이전하고 size·SHA metadata를 검증하는 전용 실행기와 GitHub Actions workflow를 추가했다. (codex)
- Analysis: SnowballC 0.7.0과 NLTK 3.10.0 ORIGINAL_ALGORITHM의 소규모 Porter fixture 36개를 직접 비교해 모두 동일함을 확인했으며, 기존 구체성 결과는 변경하지 않았다. (codex)
- Added: Ubuntu R 4.3.3 환경과 CRAN archive의 SnowballC 0.7.0을 프로젝트 전용 library에 고정하는 설치·검증 스크립트를 추가했다. (codex)
- Docs: SnowballC archive SHA-256, R session 정보, 설치 경로 및 재현 명령을 기록했으며 기존 구체성 측정은 변경하지 않았다. (codex)

## [0.12.0] - 2026-07-29

- Added: Springer 공식 Brysbaert et al. (2014) 집계 XLSX와 CRAN tidytext 0.3.1 SMART 자료의 SHA·구조·점수 범위를 검증하는 loader를 추가했다. (codex)
- Analysis: Baek, Ihm, and Kang (2023)의 SMART 제거→Porter stemming→Brysbaert 평균 절차를 5개 기업의 AI 직접 문장과 전체 10-K에 적용했다. (codex)
- Analysis: 원형 exact match를 우선하고 unique Porter stem만 fallback으로 허용했으며 ambiguous stem은 평균 결합 없이 unmatched warning으로 보존했다. (codex)
- Data: AI·보고서 구체성 평균, 중앙값, 표준편차, 범위, coverage, collision, AI token 상세 및 미매칭 진단을 생성했다. (codex)
- Docs: 논문의 SMART 1,149개 표기와 tidytext 실제 SMART 571행·570고유 항목 차이, 공식 `subject` 점수 3.14와 본문 3.13 차이 및 예제 재현을 기록했다. (codex)
- Security: 공개 재배포가 명확하지 않은 전체 사전·파생 word-score 목록·SMART 목록은 Git에서 제외했다. (codex)

## [0.11.0] - 2026-07-29

- Added: 공식 Notre Dame 1993–2025 Loughran-McDonald Master Dictionary의 SHA-256·열 구조·활성/제거 규칙을 검증하는 loader와 재현성 metadata를 추가했다. (codex)
- Analysis: 5개 smoke-test 기업의 AI 직접 관련 문장과 전체 10-K에 Positive, Negative, Uncertainty, Litigious, Strong Modal, Weak Modal, Constraining 변수를 계산했다. (codex)
- Data: TECH의 AI 문장 분모 0은 missing으로 유지하고 보고서 수준 값은 계산했으며, NSC 단일 AI 문장 warning과 273개 기존 AI 문장 집합을 보존했다. (codex)
- Security: 공개 재배포 허용이 명확하지 않은 원본 및 전체 파생 사전을 Git에서 제외하고 공식 다운로드 절차·파일명·SHA만 기록했다. (codex)
- Docs: Brysbaert 구체성 및 dependency 기반 시제·수동태는 계속 blocked이며 100개 확장과 R2 작업을 수행하지 않았음을 명시했다. (codex)

## [0.10.0] - 2026-07-29

- Added: 고정 seed와 명시적 선정 기준으로 warning 없는 5개 기업을 선택하고 AI 공시·직접 관련 문장·Fog 및 사전 비의존 보고서 통제변수를 측정하는 smoke-test pipeline을 추가했다. (codex)
- Data: NVDA, HPE, TECH, WAT, NSC의 기업 결과, AI match 상세, 수동검토 후보, 분모 0, warning, reproducibility inventory 및 출력 SHA를 기록했다. (codex)
- Analysis: 로컬에 없는 Brysbaert·Loughran-McDonald 사전과 dependency model을 가짜 값으로 대체하지 않고 관련 구체성·불확실성·감성·시제·수동태 상태를 blocked dependency로 보존했다. (codex)
- Added: AI 경계·문장 문맥·표 제외·분모 0·Fog·blocked dependency·최대 3회·ID/SHA 품질을 검증하는 비네트워크 테스트를 추가했다. (codex)
- Docs: 5개 smoke test가 부분 검증 단계이며 100개 확장, R2, SEC 재수집 및 외부 재무자료 수집은 수행하지 않았음을 기록했다. (codex)

## [0.9.0] - 2026-07-29

- Added: Cooper, Ewing, and Mishra (2022)를 참고해 inline XBRL HTML에서 언어 분석용 본문, 원문 구조 보존 텍스트, 표 텍스트 및 주요 Item별 텍스트를 생성했다. (codex)
- Data: 100개 기업의 텍스트 3종, 주요 section 파일, 문단 141,796행, 문장 298,250행, 기업별 추출 결과와 품질검사 자료를 추가했다. (codex)
- Added: 숨김·script·style·XBRL metadata 제거, 표 분리, Unicode 정규화, 문장 분리, section 탐지, SHA·ID·오염 검사를 위한 비네트워크 테스트를 추가했다. (codex)
- Changed: GitHub 단일 파일 제한을 피하도록 대용량 문단·문장 CSV를 gzip으로 저장하고 소규모 결과·품질 CSV는 그대로 유지했다. (codex)
- Docs: 텍스트 추출 완료 범위, 5개 수동검토 결과, section 경계 warning 및 아직 계산하지 않은 AI·언어 변수를 기록했다. (codex)

## [0.8.0] - 2026-07-29

- Added: 최종 분석 표본 CSV만 입력으로 사용해 SEC Archives의 지정 10-K primary HTML 100개를 초당 최대 1회 정책으로 수집하는 반복 실행 가능 downloader를 추가했다. (codex)
- Data: 기업별 원문 HTML, SHA-256·크기·HTTP 상태 manifest, 다운로드 요약 및 User-Agent 값을 포함하지 않는 요청 로그를 추가했다. (codex)
- Added: 입력 계약, URL 생성, 비식별 로그, manifest-파일 대응, SHA-256, 파일 크기 및 accession 고유성을 검증하는 비네트워크·artifact 테스트를 추가했다. (codex)
- Docs: HTML collection completed 상태와 본문 추출·NLP·언어 분석이 아직 수행되지 않았음을 기록했다. (codex)

## [0.7.0] - 2026-07-29

- Added: 승인된 TXT→ITW 교체를 deterministic reserve 순서와 계보 검증을 거쳐 반복 실행 가능하게 적용하고 최종 분석 표본 100개를 생성했다. (codex)
- Data: 최초 추출 표본은 보존하면서 TXT를 audit 전용으로 유지하고 `P2025-R001` ITW 및 eligible Form 10-K 100개를 최종 표본·metadata에 연결했다. (codex)
- Added: 최종 표본의 ID·CIK·accession 고유성, 산업 할당, filing 기준, 수동검토 해결을 검증하는 비네트워크 테스트를 추가했다. (codex)
- Docs: 최종 원문 다운로드의 유일한 입력, 표본 교체 근거, 검증 결과와 아직 수행하지 않은 HTML·텍스트·언어 측정 범위를 문서화했다. (codex)

- Added: FOXA/FOX와 GE의 identity를 CIK·SEC ticker로 해결하고 TXT의 비달력 회계연도로 인한 2025 reportDate 10-K 부재 및 결정론적 Industrials 교체 후보를 기록했다. (codex)
- Added: 기존 요청 로그를 변경하지 않고 검토 실행 범위·cache·오류·입력파일 SHA-256을 `final_run_summary.csv`에 기록했다. (codex)
- Added: 고정된 100개 파일럿의 SEC submissions metadata를 rate limit·retry·cache·비식별 로그 정책으로 수집하고 2025 reportDate 기준 Form 10-K를 선정했다. (codex)
- Added: filing 선정, historical fragment, amendment 연결, cache 및 재시도 정책의 비네트워크 테스트와 metadata 검증 문서를 추가했다. (codex)
- Added: 2025년 CIK·GICS 확인 가능 모집단에서 seed `20250729`와 largest remainder 산업 비례할당으로 100개 파일럿 및 결정론적 예비 후보 순서를 생성했다. (codex)
- Added: 파일럿 표본의 재현성, 100개 행, 산업 할당 합계 및 기업·CIK 고유성을 검사하는 비네트워크 unit test를 추가했다. (codex)

## [0.6.0] - 2026-07-24

- Docs: `main`의 전체 주석형 트리와 각 폴더·파일·CSV 열의 역할 및 수정 원칙을 README와 구조 문서에 명시했다. (codex)
- Changed: 연도별 데이터 검증에 필수 열, 기업 키, sample year, CIK 형식, manifest 출력 경로 및 원본 SHA-256 검사를 추가했다. (codex)
- Docs: 현재 존재하지 않는 10-K 원문·filing metadata·추출물·분석 결과 구조는 수집 기준 확정 후 추가하도록 범위를 명시했다. (codex)

## [0.5.1] - 2026-07-24

- Fixed: GitHub 전송 출력 한도로 잘린 원본 스냅숏 3개를 분할 전송으로 교체하고 로컬 원본과 SHA-256을 재검증했다. (codex)
- Docs: 일반 HTTPS Git 인증 실패와 대용량 blob 전송 문제의 원인·조치·검증 결과를 디버그 로그에 기록했다. (codex)

## [0.5.0] - 2026-07-24

- Data: 2020-2025년 각 연도 폴더에 기준일별 500개 기업 목록과 복수 주식 종류를 유지한 종목 감사 목록을 추가했다. (codex)
- Added: Wikipedia 현재 구성표와 변경 이력을 역적용하고 역사 구성종목 및 SEC ticker 자료로 검증·보완하는 재현 스크립트를 추가했다. (codex)
- Added: 원본 HTML·CSV·JSON 스냅숏, SHA-256 해시, 연도별 행 수, CIK 결측 및 ticker 보정 내역을 보존하는 manifest를 추가했다. (codex)
- Added: 6개 연도의 기준일, 기업 수, 종목 수, ticker 고유성을 검사하는 검증 스크립트와 데이터 생성 방법 문서를 추가했다. (codex)

## [0.4.0] - 2026-07-24

- Added: 2020-2025년 연구 자료를 분리해 관리할 수 있도록 저장소 루트에 연도별 폴더와 안내 파일을 추가했다. (codex)
- Docs: 각 연도 폴더에 구성기업 확정 기준일, CIK 기반 중복 제거 원칙 및 표본 정의 문서 경로를 기록했다. (codex)

## [0.3.0] - 2026-07-20

- Changed: 연구연도 `t`의 S&P 500 표본을 다음 해 1월 1일 현재 구성기업으로 확정했다. (codex)
- Added: 2020-2025년 확정 기준일, 변경 이력 적용 및 CIK 기반 중복 제거 원칙을 설명하는 표본 정의 문서를 추가했다. (codex)

## [0.2.0] - 2026-07-20

- Changed: 저장소 목적을 2020-2025년 S&P 500 대상 기업의 10-K 수집 및 분석 프로젝트로 확정했다. (codex)
- Docs: 연구 범위, 분석 단위, 예정 작업 단계 및 데이터 수집 전에 확정해야 할 표본 기준을 문서화했다. (codex)

## [0.1.0] - 2026-07-20

- Added: 저장소 작업, 기록 보존, 검증 및 완료 보고 기준을 정의한 `AGENTS.md`를 추가했다. (codex)
- Added: 변경 이력, 진행 상황, 디버그 및 데이터 분석 기록 방식을 정의한 작성 규칙을 추가했다. (codex)
- Added: 버전, 진행 상황 및 디버그 기록을 위한 초기 관리 파일을 추가했다. (codex)
# Unreleased

- Added: runner branch 인수인계를 위한 fixture 전용 GitHub Actions와 Codespaces 재접속 문서를 추가했다. dashboard 및 실제 SEC/R2/Google Drive 실행과 분리했다. (codex)
