# Figure 산출물 감사

기존 `analysis/descriptive_2020_2025/figures/`의 산출물을 읽기 전용으로
확인하고, 본문 Figure와 부록·표 전용 산출물을 구분했다. 수치는 기존
집계 CSV에서 다시 계산하지 않으며, 웹 Figure는 생성된 JSON을 사용한다.

| Figure file | 내용 | Source data | Generator | 현재 상태 | 웹 사용 | 결정 |
| --- | --- | --- | --- | --- | --- | --- |
| `01_ai_disclosure_rate_by_year.svg` | 연도별 AI 공시 비율 | `figures/figure_aggregate_data.csv` | `scripts/create_descriptive_figures.py` | 최신 집계 | Figure 1 다운로드 원본 | `main_text` |
| `02_mean_ai_sentence_count_by_year.svg` | 전체 표본 AI 직접 문장 수 | `figures/figure_aggregate_data.csv` | `scripts/create_descriptive_figures.py` | 최신 집계 | Figure 2 다운로드 원본 | `main_text` |
| `03_whole_report_concreteness_by_year.svg`, `04_ai_concreteness_by_year.svg` | 보고서·AI 문장 구체성 | `figures/figure_aggregate_data.csv` | `scripts/create_descriptive_figures.py` | 최신 집계 | Figure 3에 통합 | `main_text` |
| `05_tense_shares_by_year.svg` | 과거·현재·미래 시제 비율 | `figures/figure_aggregate_data.csv` | `scripts/create_descriptive_figures.py` | 최신 집계 | Figure 4 | `main_text` |
| `09_ai_sentiment_by_year.svg` | AI 직접 문장 Loughran–McDonald 범주 | `figures/figure_aggregate_data.csv` | `scripts/create_descriptive_figures.py` | 최신 집계 | Figure 5 | `main_text` |
| `appendix_ai_group_*.svg` | 공시·미공시 연도별 집단 평균 | `figures/figure_ai_group_data.csv` | `scripts/create_descriptive_figures.py` | 세부 비교 | 표와 중복 | `appendix` |
| `change_*.svg` | 동일 기업 내 전년 변화 | `figures/figure_within_firm_change_data.csv` | `scripts/create_descriptive_figures.py` | 세부 비교 | Figure 7 데이터 | `main_text` |
| `06_uncertainty_by_year.svg`, `07_passive_voice_by_year.svg`, `08_fog_index_by_year.svg`, `10_report_length_by_year.svg` | 단일 계열 연도 추이 | `figures/figure_aggregate_data.csv` | `scripts/create_descriptive_figures.py` | 최신 집계 | 표와 중복 | `table_only` |
| `figure_aggregate_data.csv` | 본문 연도별 집계 원자료 | 기존 확장 패널 | `scripts/create_descriptive_figures.py` | 검증 완료 | Figure JSON source | `main_text` |
| `figure_ai_group_data.csv` | AI 공시 집단별 집계 원자료 | 기존 확장 패널 | `scripts/create_descriptive_figures.py` | 검증 완료 | 부록 source | `appendix` |
| `figure_within_firm_change_data.csv` | 연속연도 기업 내 변화 원자료 | table 07 | `scripts/create_descriptive_figures.py` | 검증 완료 | Figure 7 source | `main_text` |

모든 기존 PNG·SVG는 원자료와 생성 script가 연결되어 있다. 웹 본문은
가독성과 반응형 표시를 위해 동일 source에서 SVG를 직접 렌더링하고,
기존 SVG는 다운로드용으로만 제공한다. VIF와 전체 상관행렬은 정확한
수치와 pairwise N이 중요한 진단이므로 표·다운로드를 우선하며, 이후
부록 Figure로 확장할 수 있다.
