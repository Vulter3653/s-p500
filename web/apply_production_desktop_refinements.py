#!/usr/bin/env python3
"""Final production-only layout, language, and figure consistency refinements."""
from __future__ import annotations

import re
from pathlib import Path

OUT = Path(__file__).resolve().parent / "index.html"


def main() -> None:
    document = OUT.read_text(encoding="utf-8")

    # Remove redundant professor-facing copy while preserving the actual variable definitions.
    document = document.replace(
        '<p>논문 독자가 핵심 변수의 의미와 계산 방식을 확인할 수 있도록 개념, 조작적 정의, 계산식, 분자·분모, 단위와 결측 처리를 제시한다.</p>',
        "",
    )
    document = document.replace(
        '<p>과거·현재 시제와 미래 조동사 표지는 spaCy의 문장분할, 토큰화, 품사 및 의존구문 분석 결과에 기존 코드의 규칙을 적용해 계산하였다.</p>',
        "",
    )
    document = document.replace("추가 기술 변수", "")

    # Korean-first statistical terminology and grammatical cleanup.
    replacements = {
        "paired t-test": "대응표본 t-검정",
        "Welch t-test": "Welch t-검정",
        "Wilcoxon rank-sum test": "Wilcoxon 순위합 검정",
        "대응표본 t-검정를": "대응표본 t-검정을",
        "대응표본 t-검정는": "대응표본 t-검정은",
        "Welch t-검정를": "Welch t-검정을",
        "Welch t-검정는": "Welch t-검정은",
        "Welch t-검정로": "Welch t-검정으로",
        "Wilcoxon 순위합 검정로": "Wilcoxon 순위합 검정으로",
        ">Welch p값<": ">Welch t-검정 p값<",
        ">Wilcoxon 순위합 p값<": ">Wilcoxon 순위합 검정 p값<",
        "보정하지 않은 ": "",
        "보정하지 않은": "",
    }
    for old, new in replacements.items():
        document = document.replace(old, new)

    document = document.replace(
        "전체 기업-연도 표본에서 Concreteness와 의 관측치 수, 중심경향 및 분산을 요약한다.",
        "전체 기업-연도 표본에서 Concreteness와 기타 기술 변수의 관측치 수, 중심경향 및 분산을 요약한다.",
    )

    # Use the final professor-facing interpretation and remove the Limitations block.
    discussion = (
        '<h3>6.11 결과 해석 (Discussion)</h3>'
        '<p>전체기간 대응표본 1,890개에서 AI 관련 문장의 평균 Concreteness는 2.83으로, 동일 기업-연도 Whole 10-K의 평균 2.89보다 0.06 낮았다(p&lt;0.001***). 즉 동일한 10-K 안에서 비교했을 때 AI 관련 문장은 보고서 전체보다 평균적으로 덜 구체적인 언어를 사용한 것으로 나타났다.</p>'
        '<p>연도별 대응비교에서는 2017–2022년에 AI 관련 문장의 평균 Concreteness가 대응표본 Whole 10-K 평균보다 높았고, 2023–2025년에는 반대로 낮았다. 전체기간 평균은 이러한 연도별 차이를 함께 포함하므로, AI 관련 언어의 Concreteness가 모든 연도에서 동일한 방향으로 나타난 것은 아니다.</p>'
        '<p>Section 분석에서는 Item 1 Business와 Item 1A Risk Factors의 AI 관련 문장 평균 Concreteness가 대응표본 Section 전체보다 각각 약 0.05점과 0.06점 낮았고, Item 7 MD&amp;A에서는 약 0.03점 높았다. 따라서 AI 관련 언어의 구체성은 10-K 내 위치에 따라 동일한 방향으로 나타나지 않았으며, 사업 설명·위험 공시·경영진의 성과 및 전망 설명에서 서로 다른 패턴을 보였다.</p>'
        '<p>보고서 단위의 ‘전체·AI 존재·AI 없음’ 비교와 동일 보고서 내부의 대응비교는 비교 단위가 다르다. 전자는 AI 관련 문장의 존재 여부에 따른 기업-연도 평균을 보여주고, 후자는 동일한 기업-연도 10-K 안에서 AI 관련 문장과 Whole 10-K의 차이를 보여준다. 따라서 Concreteness의 핵심 결과는 동일 기업-연도 대응비교를 중심으로 해석하고, 보고서 단위와 Section 단위 결과를 함께 보면 AI 관련 언어가 나타나는 위치와 문맥에 따른 차이를 구분할 수 있다.</p>'
    )
    document = re.sub(
        r'<h3>6\.11 결과 해석 \(Discussion\)</h3>.*?(?=<h3>6\.12 해석 시 유의사항 \(Limitations\)</h3>|</section>)',
        discussion,
        document,
        count=1,
        flags=re.S,
    )
    document = re.sub(
        r'<h3>6\.12 해석 시 유의사항 \(Limitations\)</h3>.*?(?=</section>)',
        "",
        document,
        count=1,
        flags=re.S,
    )

    # Remove the requested exploratory Section callout while retaining the full 23-Item table.
    pattern = re.compile(
        r'(<div class="two-column"><div><h3>주요 분석</h3><p><strong>Item 1 Business</strong>.*?</p></div>)'
        r'<div><h3>탐색적 분석</h3><p><strong>Item 1C Cybersecurity</strong>.*?'
        r'<strong>Item 8 Financial Statements and Supplementary Data</strong>.*?</p></div></div>',
        re.S,
    )
    document = pattern.sub(r'\1</div>', document, count=1)

    # Fit 2005–2025 into the visible desktop report width without page-level horizontal scrolling.
    css = r'''
<style id="production-desktop-fit">
@media (min-width:1200px){
  .report-main{width:calc(100vw - 235px)!important;max-width:none!important;padding-left:28px!important;padding-right:28px!important}
  .report-section{padding-left:20px!important;padding-right:20px!important}
  .paper-figure{padding:18px 14px 14px!important}
  .figure-plot,.table-scroll{overflow-x:visible!important}
  .figure-svg{width:100%!important;max-width:100%!important;min-width:0!important}
  .paper-table{width:100%!important;min-width:0!important;font-size:.66rem!important}
  .paper-table th,.paper-table td{padding:4px 4px!important}
  .paper-table thead th{white-space:normal!important;line-height:1.2!important}
  .paper-table th:first-child,.paper-table td:first-child{white-space:normal!important;min-width:88px!important}
  .table-note{padding:8px 10px 10px!important}
  .chart-x-tick{font-size:11px!important}
  .chart-value-label{font-size:8.5px!important}
}
.chart-y-tick,.chart-x-tick{font-size:12px!important;font-weight:700!important;fill:#263b45!important}
.chart-axis-title{font-size:12px!important;font-weight:800!important;fill:#263b45!important}
.chart-axis-line{stroke:#7a878d!important;stroke-width:1.4!important}
</style>
'''
    document = re.sub(r'<style id="production-desktop-fit">.*?</style>', css.strip(), document, count=1, flags=re.S)
    if 'id="production-desktop-fit"' not in document:
        document = document.replace("</head>", css + "</head>", 1)

    # Gap-safe line rendering: each line is rebuilt only from consecutive report years.
    # A missing year ends the segment, so no line is drawn through years without a dot.
    script = r'''
<script id="production-gap-safe-line-sync-v2">
(() => {
  const splitContiguousRuns = (points) => {
    const runs = [];
    let run = [];
    for (const point of points) {
      const year = Number(point.dataset.year);
      if (!Number.isFinite(year)) continue;
      if (!run.length || year === Number(run[run.length - 1].dataset.year) + 1) {
        run.push(point);
      } else {
        if (run.length >= 2) runs.push(run);
        run = [point];
      }
    }
    if (run.length >= 2) runs.push(run);
    return runs;
  };

  const syncSvg = (svg) => {
    const existingLines = Array.from(svg.querySelectorAll('polyline[data-series]'));
    if (!existingLines.length) return [];
    const allPoints = Array.from(svg.querySelectorAll('circle.chart-point[data-series][data-year]'));
    const errors = [];
    const seriesNames = Array.from(new Set(existingLines.map((line) => line.dataset.series || '')));

    for (const series of seriesNames) {
      const points = allPoints
        .filter((point) => (point.dataset.series || '') === series)
        .sort((a, b) => Number(a.dataset.year) - Number(b.dataset.year));
      const lines = existingLines.filter((line) => (line.dataset.series || '') === series);
      if (!lines.length) continue;
      const template = lines[0].cloneNode(false);
      lines.forEach((line) => line.remove());

      const runs = splitContiguousRuns(points);
      const insertionPoint = svg.querySelector('circle.chart-point, text.chart-value-label');
      runs.forEach((run, index) => {
        const line = template.cloneNode(false);
        const startYear = Number(run[0].dataset.year);
        const endYear = Number(run[run.length - 1].dataset.year);
        line.dataset.series = series;
        line.dataset.segmentIndex = String(index);
        line.dataset.segmentStart = String(startYear);
        line.dataset.segmentEnd = String(endYear);
        line.setAttribute('points', run.map((point) => `${point.getAttribute('cx')},${point.getAttribute('cy')}`).join(' '));
        const pointColor = run[0].getAttribute('fill');
        if (pointColor) line.setAttribute('stroke', pointColor);
        if (series === '전체') line.setAttribute('stroke-dasharray', '8 5');
        else line.removeAttribute('stroke-dasharray');
        if (insertionPoint) svg.insertBefore(line, insertionPoint);
        else svg.appendChild(line);
      });
    }

    const currentLines = Array.from(svg.querySelectorAll('polyline[data-series][data-segment-start][data-segment-end]'));
    for (const line of currentLines) {
      const series = line.dataset.series || '';
      const start = Number(line.dataset.segmentStart);
      const end = Number(line.dataset.segmentEnd);
      const points = allPoints
        .filter((point) => (point.dataset.series || '') === series)
        .filter((point) => Number(point.dataset.year) >= start && Number(point.dataset.year) <= end)
        .sort((a, b) => Number(a.dataset.year) - Number(b.dataset.year));
      const years = points.map((point) => Number(point.dataset.year));
      for (let index = 1; index < years.length; index += 1) {
        if (years[index] !== years[index - 1] + 1) errors.push(`${series}: line crosses missing year`);
      }
      const expected = points.map((point) => `${point.getAttribute('cx')},${point.getAttribute('cy')}`).join(' ');
      if ((line.getAttribute('points') || '') !== expected) errors.push(`${series}: line/dot coordinates differ`);
    }
    return errors;
  };

  const syncAll = () => {
    const errors = [];
    let auditedSvgCount = 0;
    document.querySelectorAll('svg.figure-svg').forEach((svg) => {
      if (svg.querySelector('polyline[data-series]')) auditedSvgCount += 1;
      errors.push(...syncSvg(svg));
    });
    document.documentElement.dataset.figureLineSync = errors.length ? 'fail' : 'pass';
    document.documentElement.dataset.figureLineSyncErrors = String(errors.length);
    document.documentElement.dataset.figureLineSyncSvgCount = String(auditedSvgCount);
  };

  syncAll();
  requestAnimationFrame(syncAll);
  window.addEventListener('load', syncAll, {once: true});
})();
</script>
'''
    document = re.sub(r'<script id="production-line-dot-sync">.*?</script>', "", document, count=1, flags=re.S)
    document = re.sub(r'<script id="production-gap-safe-line-sync-v2">.*?</script>', script.strip(), document, count=1, flags=re.S)
    if 'id="production-gap-safe-line-sync-v2"' not in document:
        document = document.replace("</body>", script + "</body>", 1)

    forbidden_adjusted = [
        "adjusted_p", "adjusted_pvalue", "adjusted p", "adjusted-p",
        "fdr_p", "q_value", "bonferroni", "holm", "보정된 p", "보정 p", "보정하지 않은",
    ]
    found = [token for token in forbidden_adjusted if token.lower() in document.lower()]
    if found:
        raise RuntimeError(f"Adjusted p-value wording/source leaked into production HTML: {found}")

    forbidden_text = [
        "추가 기술 변수",
        "6.12 해석 시 유의사항",
        "t-검정를",
        "t-검정는",
        "t-검정로",
        "검정로",
        "Item 1C Cybersecurity</strong> — 최근 3개 연도 중심",
        "Item 8 Financial Statements and Supplementary Data</strong> — 표·주석 중심",
    ]
    found_text = [token for token in forbidden_text if token in document]
    if found_text:
        raise RuntimeError(f"Professor-facing cleanup remains: {found_text}")

    required = [
        'id="production-desktop-fit"',
        'id="production-gap-safe-line-sync-v2"',
        'p&lt;0.001***',
        '6.11 결과 해석 (Discussion)',
        '대응표본 t-검정',
        'Welch t-검정',
        '2005',
        '2025',
    ]
    missing = [token for token in required if token not in document]
    if missing:
        raise RuntimeError(f"Production refinement missing: {missing}")

    OUT.write_text(document, encoding="utf-8")
    print("Applied final production professor-report refinements with gap-safe line rendering.")


if __name__ == "__main__":
    main()
