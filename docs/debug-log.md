# Debug Log

최신 기록을 위쪽에 추가하고 기존 기록을 삭제하지 않는다.

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
