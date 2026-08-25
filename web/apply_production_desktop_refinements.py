#!/usr/bin/env python3
"""Final production-only layout and figure-series consistency refinements."""
from __future__ import annotations

import re
from pathlib import Path

OUT = Path(__file__).resolve().parent / "index.html"


def main() -> None:
    document = OUT.read_text(encoding="utf-8")

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
  .chart-x-tick{font-size:10px!important}
  .chart-value-label{font-size:8.5px!important}
}
</style>
'''
    if 'id="production-desktop-fit"' not in document:
        document = document.replace("</head>", css + "</head>", 1)

    # Rebuild each polyline from its own series dots, sorted by report year.
    # This removes any line/dot mismatch caused by prior legend-index recoloring or row order.
    script = r'''
<script id="production-line-dot-sync">
(() => {
  document.querySelectorAll('svg.figure-svg').forEach((svg) => {
    svg.querySelectorAll('polyline[data-series]').forEach((line) => {
      const series = line.dataset.series || '';
      const points = Array.from(svg.querySelectorAll('circle.chart-point[data-series]'))
        .filter((point) => (point.dataset.series || '') === series)
        .sort((a, b) => Number(a.dataset.year || 0) - Number(b.dataset.year || 0));
      if (!points.length) return;
      line.setAttribute('points', points.map((point) => `${point.getAttribute('cx')},${point.getAttribute('cy')}`).join(' '));
      const pointColor = points[0].getAttribute('fill');
      if (pointColor) line.setAttribute('stroke', pointColor);
      if (series === '전체') line.setAttribute('stroke-dasharray', '8 5');
    });
  });
})();
</script>
'''
    if 'id="production-line-dot-sync"' not in document:
        document = document.replace("</body>", script + "</body>", 1)

    # Raw p-values only: adjusted/FDR/multiplicity-adjusted p-value fields or wording are prohibited.
    forbidden_adjusted = [
        "adjusted_p", "adjusted_pvalue", "adjusted p", "adjusted-p",
        "fdr_p", "q_value", "bonferroni", "holm", "보정된 p", "보정 p", "보정하지 않은",
    ]
    found = [token for token in forbidden_adjusted if token.lower() in document.lower()]
    if found:
        raise RuntimeError(f"Adjusted p-value wording/source leaked into production HTML: {found}")

    forbidden_callout = [
        "Item 1C Cybersecurity</strong> — 최근 3개 연도 중심",
        "Item 8 Financial Statements and Supplementary Data</strong> — 표·주석 중심",
    ]
    found_callout = [token for token in forbidden_callout if token in document]
    if found_callout:
        raise RuntimeError(f"Exploratory Section callout remains: {found_callout}")

    required = [
        'id="production-desktop-fit"',
        'id="production-line-dot-sync"',
        'p&lt;0.001***',
        '2005',
        '2025',
    ]
    missing = [token for token in required if token not in document]
    if missing:
        raise RuntimeError(f"Production refinement missing: {missing}")

    OUT.write_text(document, encoding="utf-8")
    print("Applied production desktop-fit, raw-p, Section-callout, and line-dot refinements.")


if __name__ == "__main__":
    main()
