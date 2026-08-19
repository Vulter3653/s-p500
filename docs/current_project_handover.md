# S&P 500 10-K 언어 분석 프로젝트 인수인계

Updated: 2026-08-19

## 현재 저장소 상태

- repository: `Vulter3653/s-p500`
- 작업 브랜치: `codex/web-research-report`
- 기준 commit: Concreteness validation `9859c749c1bbfec6d9a6da80a5e5b28b953819b1`
- 최신 HEAD는 고정값을 수동 복제하지 않고 `git rev-parse HEAD`로 확인한다.
- `origin/main`: `0bd911f7846abd3a96d853073e38fd470f2b3a36`
- VERSION: `0.14.0`

## 연구 우선순위

- RQ1 Tense: **보류**
- RQ2 Concreteness: **현재 우선 진행**
- 핵심 관계: `10-K Concreteness → Shareholder Reaction`
- 상세 확정·보류·예정 항목: [`docs/research-blueprint.md`](research-blueprint.md)

기존 tense 결과는 최종 측정이 아니라 `spaCy 기반 임시 tense 분석`이다. WRDS·Compustat·CRSP 결합, CAR·BHAR 및 주주 반응 회귀는 아직 실행하지 않은 향후 청사진이다.

## 확정된 데이터 상태

### 2020–2025 핵심 패널

- 2,829개 기업-연도
- 545개 고유 기업
- AI 관련 공시 1,660개
- AI 관련 문장 19,577개
- 연도별 관측치: 446 / 462 / 471 / 479 / 487 / 484

기존 연도별 manifest, extraction 결과, language 결과, 핵심 패널과 분석 산출물은 보존한다.

### Historical candidate panel

- 기간: 2006–2025
- 4,897개 기업-연도
- 584개 고유 기업
- 기존 2020–2025 패널 2,829개
- 2006–2019 historical additions 2,068개
- historical backfill: 2019 → 2006 완료
- chain status: `completed`
- validation: `PASS`

이는 매년 완전한 S&P 500 전체 패널이 아니라 **원천과 적격 filing이 확인된 historical candidate panel**이다.

## 완료·보류·예정 구분

### 완료

- 2020–2025 구성종목·Form 10-K·언어 패널 구축
- 2020–2025 기술통계·상관관계·단변량 비교
- 2006–2019 historical candidate backfill
- 기존 웹 데이터와 Figure 생성
- 웹 연구보고서 2차 피드백 브랜치 미리보기 배포
- Brysbaert Concreteness 전처리 중간 검증: `READY WITH DOCUMENTED LIMITATIONS`
- WRDS data acquisition·linkage contract 작성: specification prepared / not yet executed

### 보류

- RQ1 Tense
- 최종 tense 측정 방법 선택
- LIWC2015 재현 및 현재 spaCy 방식과의 비교

### 예정이며 미실행

- Concreteness stopword·collision 대안의 회귀 단계 robustness 문서화
- [`docs/wrds-data-acquisition-contract.md`](wrds-data-acquisition-contract.md)에 따른 primary core 2,829건의 실제 WRDS acquisition
- SEC acceptance timestamp enrichment 및 market-event-date 정렬
- CIK–GVKEY–CCM–PERMNO 연결
- Compustat controls 결합
- CRSP return 결합
- 단기 CAR 및 장기 BHAR
- Concreteness와 shareholder reaction 회귀
- event-study robustness 및 confounding-event 검토

## 현재 웹과 미래 연구의 경계

현재 공개 웹은 2020–2025 기존 descriptive analysis만 표시한다. 아직 존재하지 않는 WRDS, CAR, BHAR 또는 Compustat 결과를 완료된 분석처럼 표시하지 않는다. 현재 웹 브랜치는 main에 병합되지 않았고 production 배포도 수행하지 않았다.

## 보호 원칙

- 기존 CSV·JSON·HTML·패널·분석값을 재계산하거나 덮어쓰지 않는다.
- SEC·WRDS·R2·Google Drive 작업은 별도 승인과 명확한 실행 범위 없이 수행하지 않는다.
- historical candidate를 완전한 역사 S&P 500 패널로 표현하지 않는다.
- Tense 임시 결과를 확정 결과로 표현하지 않는다.
- 현재 작업 브랜치의 commit·push는 `AGENTS.md`의 기본 Git 완료 정책을 따르며, main 직접 변경·PR·merge·production deploy는 자동 수행하지 않는다.

## 다음 의사결정

1. CRSP current CIZ에서 delisting·shares fields와 CCM schema를 실행 직전 확인
2. 최신 2025 event의 12개월 BHAR가 성숙하기 전 partial snapshot을 받을지, 2027-04-30 이후 one-shot으로 받을지 결정
3. Acceptance timestamp가 없는 event의 fallback과 market-close alignment convention 승인
4. Age·segment·BigN optional source를 첫 acquisition에 포함할지 결정
5. RQ2에서 whole-report, AI-related 또는 difference score 중 main IV 선택
6. CAR benchmark·estimation window와 BHAR horizon·benchmark 확정
7. earnings announcement 및 confounding event 처리 규칙 확정
