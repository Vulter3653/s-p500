# 2019–2017년 역사적 S&P 500 복구·분석 계획

## 목적

현재 2020–2025년 분석 결과를 보존하면서 더 오래된 연도의 역사적 S&P 500 구성종목을 복구하고 SEC Form 10-K 언어 분석을 확장한다. 연도별 raw HTML은 먼저 Cloudflare R2에 저장하고, 해당 연도의 수집·추출·언어 측정과 품질검사가 끝난 뒤 Google Drive로 이전한다.

## 처리 순서

연도는 다음 역순으로 한 번에 하나씩 처리한다.

```text
2019 → 2018 → 2017
```

이번 계획은 현재 최저 분석연도 2020년의 직전 3개 연도라는 해석을 사용한다.

## 표본과 batch

- 역사적 구성종목 원천자료를 membership의 기준으로 사용한다.
- 목표는 연도별 503 securities이며, 실제 원천자료와 SEC 적격 filing 조건을 충족하는 행만 포함한다.
- CIK 결측, 유일한 적격 Form 10-K 부재, 복수 적격 filing은 임의 보정이나 선택 없이 제외 목록에 기록한다.
- 503개를 100·100·100·100·100·3의 6개 batch로 분할한다.

## Free Tier 보호 원칙

- 여러 연도 workflow를 동시에 실행하지 않는다.
- 한 연도의 batch도 기본 `max-parallel: 1`로 실행한다.
- SEC 요청 사이에 기존 rate-limit 지연을 적용한다.
- 기업 단위 checkpoint와 artifact를 처리 직후 기록한다.
- 중단 후 `resume`으로 완료 기업을 재처리하지 않는다.
- 동일 연도 workflow의 중복 실행을 `concurrency`로 막는다.
- 자동 schedule과 cron은 추가하지 않는다.
- 로그·artifact·보존 기간은 필요한 최소 범위로 유지한다.
- API 오류와 quota 제한이 발생하면 재시도 간격을 늘리고 worker 수를 줄인다.

## 연도별 처리 흐름

1. 역사적 구성종목 manifest와 제외 목록 생성
2. 정확한 `reportDate` 연도의 Form `10-K` filing metadata 확인
3. SEC primary HTML 수집
4. R2 업로드 및 SHA·크기 검증
5. 본문 추출과 기존 언어 측정 pipeline 실행
6. 연도별 결과와 품질검사 생성
7. R2 manifest를 source of truth로 Google Drive 이전
8. Drive 파일 ID, 크기, SHA metadata 검증
9. 연도별 요약과 checkpoint 보존
10. 검증 완료 후 다음 연도로 이동

## 저장소와 기존 결과 보호

- 기존 2020–2025년 manifest, 언어 결과, 패널 및 Google Drive 파일은 읽기 전용으로 취급한다.
- R2 객체는 Drive 이전과 검증 전까지 삭제하지 않는다.
- 원본 HTML을 Git에 추가하지 않는다.
- 신규 연도 결과만 별도 디렉터리에 생성한다.
- 기존 측정식과 column 정의는 변경하지 않는다.

## 실행 전 규칙 감사 결과

현재 저장소의 기존 `process-10k-yearly-batches.yml`와 `run_yearly_10k_batch.py`는 2020–2025년 기존 표본을 위해 다음과 같은 legacy 전제를 가진다.

- batch 입력 선택지는 1–5로 제한되어 있다.
- 실행기 내부에 `2025/pilot_100` 경로가 하드코딩되어 있다.
- 추출기와 language runner도 2025 pilot 경로를 기본 입력으로 사용한다.
- 현재 workflow는 R2 저장을 기본 처리하며 historical 6번째 batch와 Google Drive 후속 이전을 직접 제공하지 않는다.

따라서 이 전제를 무리하게 전역 수정하면 이미 검증된 2020–2025년 pipeline을 깨뜨릴 수 있다. 역사 연도 처리는 기존 실행기를 먼저 복사해 덮어쓰는 방식이 아니라, 연도·namespace·6개 batch·checkpoint·R2→Drive 단계를 명시적으로 받는 전용 실행기와 workflow로 확장해야 한다. 기존 연도 workflow와 결과는 변경하지 않는다.

현재 확인된 보호 상태는 다음과 같다.

- PR #2의 역사적 구성종목 생성 workflow는 아직 `main`에 병합되지 않았다.
- R2는 이전 삭제 검증에서 빈 상태이며, 신규 historical 작업에서만 새 객체를 생성한다.
- Google Drive 신규 저장 기본 형식은 `year_flat`이다.
- 이번 문서화 단계에서는 workflow 실행, SEC 수집, R2 업로드, Google Drive 변경을 수행하지 않았다.

## 현재 상태

이 문서는 실행 계획을 기록한 것이다. 2019–2017년 workflow 실행, SEC 재수집, R2 업로드, Google Drive 변경은 아직 수행하지 않았다.
