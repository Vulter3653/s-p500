# Changelog

이 저장소의 모든 주요 변경 사항을 기록한다. 버전 형식은 Semantic Versioning을 따른다.

## [Unreleased]

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
