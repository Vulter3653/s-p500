#!/usr/bin/env python3
"""Final production-only layout, language, and figure consistency refinements."""
from __future__ import annotations

import re
from pathlib import Path

OUT = Path(__file__).resolve().parent / "index.html"


def main() -> None:
    document = OUT.read_text(encoding="utf-8")

    document = document.replace(
        '<p>논문 독자가 핵심 변수의 의미와 계산 방식을 확인할 수 있도록 개념, 조작적 정의, 계산식, 분자·분모, 단위와 결측 처리를 제시한다.</p>',
        "",
    )
    document = document.replace(
        '<p>과거·현재 시제와 미래 조동사 표지는 spaCy의 문장분할, 토큰화, 품사 및 의존구문 분석 결과에 기존 코드의 규칙을 적용해 계산하였다.</p>',
        "",
    )
    document = document.replace("추가 기술 변수", "")

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

    pattern = re.compile(
        r'(<div class="two-column"><div><h3>주요 분석</h3><p><strong>Item 1 Business</strong>.*?</p></div>)'
        r'<div><h3>탐색적 분석</h3><p><strong>Item 1C Cybersecurity</strong>.*?'
        r'<strong>Item 8 Financial Statements and Supplementary Data</strong>.*?</p></div></div>',
        re.S,
    )
    document = pattern.sub(r'\1</div>', document, count=1)

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

    script = r'''
<script id="production-dot-to-dot-line-sync-v3">
(() => {
  const seriesColor = (points) => {
    const first = points[0];
    return first ? (first.getAttribute('fill') || '#0072B2') : '#0072B2';
  };

  const rebuildSvgLinesFromDots = (svg) => {
    const points = Array.from(svg.querySelectorAll('circle.chart-point[data-series][data-year]'));
    if (!points.length) return {series: 0, segments: 0, errors: []};

    // Data lines are rebuilt exclusively from the rendered dots. Axis/grid elements are <line>, not <polyline>.
    svg.querySelectorAll('polyline').forEach((node) => node.remove());
    svg.querySelectorAll('line[data-dot-connector="true"]').forEach((node) => node.remove());

    const insertionPoint = svg.querySelector('circle.chart-point, text.chart-value-label');
    const names = Array.from(new Set(points.map((point) => point.dataset.series || '').filter(Boolean)));
    const errors = [];
    let segmentCount = 0;

    names.forEach((series) => {
      const seriesPoints = points
        .filter((point) => (point.dataset.series || '') === series)
        .sort((a, b) => Number(a.dataset.year) - Number(b.dataset.year));
      const color = seriesColor(seriesPoints);

      for (let index = 1; index < seriesPoints.length; index += 1) {
        const previous = seriesPoints[index - 1];
        const current = seriesPoints[index];
        const previousYear = Number(previous.dataset.year);
        const currentYear = Number(current.dataset.year);

        // If the immediately following report year has no dot, keep that interval blank.
        if (!Number.isFinite(previousYear) || !Number.isFinite(currentYear) || currentYear !== previousYear + 1) continue;

        const connector = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        connector.dataset.dotConnector = 'true';
        connector.dataset.series = series;
        connector.dataset.startYear = String(previousYear);
        connector.dataset.endYear = String(currentYear);
        connector.setAttribute('x1', previous.getAttribute('cx'));
        connector.setAttribute('y1', previous.getAttribute('cy'));
        connector.setAttribute('x2', current.getAttribute('cx'));
        connector.setAttribute('y2', current.getAttribute('cy'));
        connector.setAttribute('stroke', color);
        connector.setAttribute('stroke-width', '3');
        connector.setAttribute('fill', 'none');
        if (series === '전체') connector.setAttribute('stroke-dasharray', '8 5');
        if (insertionPoint) svg.insertBefore(connector, insertionPoint);
        else svg.appendChild(connector);
        segmentCount += 1;

        if (connector.getAttribute('x1') !== previous.getAttribute('cx') || connector.getAttribute('y1') !== previous.getAttribute('cy')) {
          errors.push(`${series} ${previousYear}: start connector/dot mismatch`);
        }
        if (connector.getAttribute('x2') !== current.getAttribute('cx') || connector.getAttribute('y2') !== current.getAttribute('cy')) {
          errors.push(`${series} ${currentYear}: end connector/dot mismatch`);
        }
      }
    });

    return {series: names.length, segments: segmentCount, errors};
  };

  const syncAll = () => {
    let svgCount = 0;
    let seriesCount = 0;
    let segmentCount = 0;
    const errors = [];

    document.querySelectorAll('svg.figure-svg').forEach((svg) => {
      const result = rebuildSvgLinesFromDots(svg);
      if (result.series > 0) svgCount += 1;
      seriesCount += result.series;
      segmentCount += result.segments;
      errors.push(...result.errors);
    });

    document.documentElement.dataset.dotLineSync = errors.length ? 'fail' : 'pass';
    document.documentElement.dataset.dotLineSyncErrors = String(errors.length);
    document.documentElement.dataset.dotLineSyncSvgCount = String(svgCount);
    document.documentElement.dataset.dotLineSyncSeriesCount = String(seriesCount);
    document.documentElement.dataset.dotLineSyncSegmentCount = String(segmentCount);
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', syncAll, {once: true});
  else syncAll();
  window.addEventListener('load', syncAll, {once: true});
  [100, 500, 1500, 3000].forEach((delay) => setTimeout(syncAll, delay));
})();
</script>
'''
    document = re.sub(r'<script id="production-line-dot-sync">.*?</script>', "", document, count=1, flags=re.S)
    document = re.sub(r'<script id="production-gap-safe-line-sync-v2">.*?</script>', "", document, count=1, flags=re.S)
    document = re.sub(r'<script id="production-dot-to-dot-line-sync-v3">.*?</script>', script.strip(), document, count=1, flags=re.S)
    if 'id="production-dot-to-dot-line-sync-v3"' not in document:
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
        'id="production-dot-to-dot-line-sync-v3"',
        'dataset.dotLineSync',
        'data-dot-connector',
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
    print("Applied final production professor-report refinements with direct dot-to-dot gap-safe connectors.")


if __name__ == "__main__":
    main()
