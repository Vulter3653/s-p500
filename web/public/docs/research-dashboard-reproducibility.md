# 재현성 안내

`scripts/generate_web_analysis_data.py`를 실행하면 기존 분석 CSV와 2020–2025 확장 패널을 읽어 웹 JSON·CSV와 변수 정의 문서를 다시 생성한다. 핵심 Table 2–4는 2,829개 기업-연도에 고정되며, 생성물에는 데이터 생성 commit과 source file SHA-256이 기록된다. 프런트엔드 배포 commit은 별도 검증이 없으면 표시하지 않는다.

```bash
python scripts/generate_web_analysis_data.py
cd web
npm run build
```

수치 변경은 분석 측정 단계에서 수행하지 않으며, 웹 단계에서는 원자료의 읽기·직렬화·검증만 수행한다.
