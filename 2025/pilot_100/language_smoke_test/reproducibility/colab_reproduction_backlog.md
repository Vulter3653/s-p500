# Colab reproduction backlog

- Step 4C에서도 notebook을 만들거나 실행하지 않았다.
- LM 1993-2025 CSV를 공식 Notre Dame 페이지에서 내려받아 repository의 예상 경로에 두고 SHA-256을 검증한다.
- 원본 및 전체 파생 LM 사전은 재배포 조건이 불명확하여 Git에 포함하지 않는다.
- Brysbaert 2014 XLSX는 공식 Springer supplement에서 내려받고 SHA-256을 검증한다.
- tidytext 0.3.1 CRAN source의 stop_words.rda에서 SMART subset을 추출한다.
- Brysbaert 원본·전체 파생 사전과 SMART 전체 목록은 재배포 조건을 보수적으로 처리해 Git에 포함하지 않는다.
- dependency parser와 모델 버전을 고정한 뒤 설치 셀을 문서화한다.
- R 4.3.3과 SnowballC 0.7.0은 Codespaces에서 고정·검증했으며, Colab에서는 `scripts/install_snowballc_0_7_0.R`을 실행한다.
- SnowballC와 NLTK stem 직접 비교 및 5개 기업 재측정은 아직 수행하지 않았다.
