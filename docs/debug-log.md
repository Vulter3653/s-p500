# Debug Log

최신 기록을 위쪽에 추가하고 기존 기록을 삭제하지 않는다.

## 2026-07-31 - R2 raw HTML 삭제 범위 고정

- 문제 요약: Google Drive 이전을 완료한 뒤 R2 비용을 중단하려면 bucket 또는 prefix가 아니라 검증 완료 manifest의 정확한 2,829개 object key만 삭제해야 한다. (codex)
- 확인: run `30544560261` artifact에서 manifest 2,829행, 고유 key 2,829개, 빈·중복 key 0개, 성공 상태 2,829개 및 failure CSV 데이터 행 0개를 확인했다. (codex)
- 조치: 기본 비삭제, `--execute` 명시, 기대 행 수·상태·중복·빈 key fail-closed, 최대 1,000개 batch 및 응답 `Errors` 기록을 구현했다. workflow execute에는 `DELETE_R2_RAW_HTML_2829` 확인 문자열과 단일 concurrency group을 적용했다. (codex)
- 검증: 실제 artifact dry run에서 2,829개가 모두 eligible이며 delete API 미호출을 확인했고, count 불일치·중복·빈 key·manifest 외 key 방지·API error 기록 mock test 6개가 통과했다. (codex)
- 상태: 실제 R2 삭제는 workflow 코드를 원격 main에 반영한 뒤 단 한 번 실행하고 결과 artifact를 확인해야 한다. (codex)

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
