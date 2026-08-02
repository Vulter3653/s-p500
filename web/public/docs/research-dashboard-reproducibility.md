# 재현성 안내

`scripts/generate_web_analysis_data.py`를 실행하면 기존 분석 CSV와 확장 패널을 읽어 웹 JSON·CSV와 변수 정의 문서를 다시 생성한다. 생성물에는 분석 기간, firm-year 단위, source file SHA-256, Git commit, 생성 시각 및 버전이 포함된다.

```bash
python scripts/generate_web_analysis_data.py
cd web
npm run build
```

수치 변경은 분석 측정 단계에서 수행하지 않으며, 웹 단계에서는 원자료의 읽기·직렬화·검증만 수행한다.
