#!/usr/bin/env python3
"""Build the production professor report from the validated public preview.

The preview supplies the full validated report and data-bearing HTML. This script
applies only the user-requested presentation/text refinements for production.
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path


SOURCE_URL = "https://professor-report-2005-2025.s-p500.pages.dev/"
OUT = Path(__file__).resolve().parent / "index.html"


def main() -> None:
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "s-p500-production-report-builder/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        document = response.read().decode("utf-8")

    if "5,355" not in document or "Whole 10-K" not in document or "Concreteness" not in document:
        raise RuntimeError("Unexpected professor-report source content")

    # Variable Definitions: retain definitions themselves, remove redundant interpretation/introduction copy.
    document = document.replace(
        '<p class="caution"><strong>변수 해석:</strong> Concreteness가 핵심 비교 변수이다. 시제, 수동태, Loughran–McDonald 어휘, Fog Index와 보고서 길이는 추가적인 기술적 특성으로 제시한다. AI 관련 문장에서 측정되는 Concreteness와 어휘 변수는 AI 없음에서 정의되지 않아 NA이며, AI 관련 문장 수는 AI 없음에서 실제 관측값 0이다.</p>',
        "",
    )
    document = re.sub(r'<h3[^>]*>\s*추가 기술 변수\s*</h3>', "", document, count=1)
    document = document.replace("추가 기술 변수", "")
    document = document.replace(
        '<p>논문 독자가 핵심 변수의 의미와 계산 방식을 확인할 수 있도록 개념, 조작적 정의, 계산식, 분자·분모, 단위와 결측 처리를 제시한다.</p>',
        "",
    )
    document = document.replace(
        '<p>과거·현재 시제와 미래 조동사 표지는 spaCy의 문장분할, 토큰화, 품사 및 의존구문 분석 결과에 기존 코드의 규칙을 적용해 계산하였다.</p>',
        "",
    )

    # Korean-first statistical terminology and concise p-value wording.
    replacements = {
        "paired t-test": "대응표본 t-검정",
        "Welch t-test": "Welch t-검정",
        "Wilcoxon rank-sum test": "Wilcoxon 순위합 검정",
        ">Welch t<": ">Welch t값<",
        ">Wilcoxon p값<": ">Wilcoxon 순위합 p값<",
        "p-value": "p값",
        "보정하지 않은 ": "",
        "exploratory analysis": "탐색적 분석",
    }
    for old, new in replacements.items():
        document = document.replace(old, new)

    # Strengthen Discussion and remove the entire Limitations block requested by the user.
    discussion = (
        '<h3>6.11 결과 해석 (Discussion)</h3>'
        '<p>전체기간 대응표본 1,890개에서 AI 관련 문장의 평균 Concreteness는 2.83으로, 동일 기업-연도 Whole 10-K의 평균 2.89보다 0.06 낮게 나타났다(p&lt;0.001***). 이는 전체기간 평균에서 동일한 10-K 안에서도 AI 관련 문장이 보고서 전체보다 상대적으로 덜 구체적인 어휘로 작성되는 경향이 확인되었음을 보여준다.</p>'
        '<p>연도별 대응비교에서는 2017–2022년에 AI 관련 문장의 평균 Concreteness가 대응표본 Whole 10-K 평균보다 높았고, 2023–2025년에는 반대로 낮게 나타났다. 따라서 전체기간 평균만으로는 연도별 방향 차이를 충분히 설명하기 어렵고, AI 관련 언어의 구체성은 시기에 따라 서로 다른 패턴을 보였다.</p>'
        '<p>Section 분석에서도 서술 맥락에 따른 차이가 나타났다. Item 1 Business와 Item 1A Risk Factors에서는 AI 관련 문장의 평균 Concreteness가 대응표본 Section 전체보다 각각 약 0.05점과 0.06점 낮았으며, Item 7 MD&amp;A에서는 약 0.03점 높았다. 즉 AI 관련 언어의 구체성은 10-K의 모든 부분에서 동일한 방향으로 나타나지 않았으며, 사업 설명·위험 공시·경영진의 성과 및 전망 설명과 같은 Section의 서술 맥락에 따라 차이를 보였다.</p>'
        '<p>보고서 단위의 전체·AI 존재·AI 없음 비교와 동일 보고서 내부의 대응비교는 서로 다른 비교 단위를 사용한다. 전자는 AI 관련 문장의 존재 여부에 따른 기업-연도 평균을 보여주며, 후자는 동일한 10-K 안에서 AI 관련 문장과 Whole 10-K 사이의 언어적 차이를 보여준다. 따라서 Concreteness의 핵심 결과는 동일 기업-연도 대응비교를 중심으로 읽고, 보고서 단위 및 Section 단위 결과를 함께 확인하면 AI 관련 공시 언어가 나타나는 위치와 서술 맥락에 따른 차이를 구분할 수 있다.</p>'
    )
    pattern = r'<h3>6\.11 결과 해석 \(Discussion\)</h3>.*?<h3>6\.12 해석 시 유의사항 \(Limitations\)</h3><ul class="limitations-list">.*?</ul>'
    document, count = re.subn(pattern, discussion, document, count=1, flags=re.S)
    if count != 1 and discussion not in document:
        raise RuntimeError("Could not replace Discussion/Limitations block")

    # Improve axes and distinguish the full-sample reference visually without changing any data values.
    visual_css = '''
<style id="production-figure-refinement">
.chart-y-tick,.chart-x-tick{font-size:12px!important;font-weight:600;fill:#42525a!important}
.chart-axis-title{font-size:12px!important;font-weight:800;fill:#31444d!important}
.figure-variable-item i,.figure-group-legend i{border-top-width:3px!important}
</style>
'''
    document = document.replace("</head>", visual_css + "</head>", 1)

    visual_script = r'''
<script id="production-figure-series-refinement">
(() => {
  const palette = {
    overall: '#5f6368',
    present: '#0072B2',
    absent: '#E69F00',
    ai: '#CC79A7',
    whole: '#0072B2'
  };
  const seriesStyle = (label) => {
    const value = (label || '').trim();
    if (value === '전체') return {color: palette.overall, dash: '8 5'};
    if (value.startsWith('AI 존재')) return {color: palette.present, dash: ''};
    if (value.startsWith('AI 없음')) return {color: palette.absent, dash: ''};
    if (value === 'AI 관련 문장') return {color: palette.ai, dash: ''};
    if (value === 'Whole 10-K') return {color: palette.whole, dash: ''};
    if (value === 'AI 관련 공시 여부') return {color: palette.present, dash: ''};
    return null;
  };

  document.querySelectorAll('.paper-figure').forEach((figure) => {
    figure.querySelectorAll('.figure-variable-list, .figure-group-legend').forEach((legend) => {
      const panel = legend.parentElement;
      const svg = panel ? panel.querySelector('.figure-plot svg') : null;
      const items = Array.from(legend.querySelectorAll('span'));
      const polylines = svg ? Array.from(svg.querySelectorAll('polyline')) : [];
      items.forEach((item, index) => {
        const label = item.textContent.trim();
        const style = seriesStyle(label);
        if (!style) return;
        item.dataset.seriesColor = style.color;
        const indicator = item.querySelector('i');
        if (indicator) {
          indicator.style.borderColor = style.color;
          indicator.style.borderTopStyle = style.dash ? 'dashed' : 'solid';
        }
        if (polylines[index]) {
          polylines[index].setAttribute('stroke', style.color);
          if (style.dash) polylines[index].setAttribute('stroke-dasharray', style.dash);
          else polylines[index].removeAttribute('stroke-dasharray');
        }
      });
    });

    figure.querySelectorAll('circle.chart-point[data-series]').forEach((point) => {
      const style = seriesStyle(point.dataset.series);
      if (style) point.setAttribute('fill', style.color);
    });
  });

  document.querySelectorAll('text.chart-axis-title').forEach((label) => {
    const text = label.textContent.trim();
    if (text === '연도별 평균 Z-score') label.textContent = '평균 Z-score (0 = 전체기간 평균)';
    if (text === 'Concreteness 평균(1–5)') label.textContent = 'Concreteness 평균 (1–5점)';
    if (text === '표준화 평균 차이 (AI 존재 − AI 없음)') label.textContent = '표준화 평균차이 (AI 존재 − AI 없음, 0 = 차이 없음)';
  });
})();
</script>
'''
    document = document.replace("</body>", visual_script + "</body>", 1)

    axis_script = r'''
<script id="production-axis-range-refinement">
(() => {
  const svgNS = 'http://www.w3.org/2000/svg';

  const niceStep = (raw) => {
    const safe = Math.max(raw, 1e-9);
    const magnitude = Math.pow(10, Math.floor(Math.log10(safe)));
    const fraction = safe / magnitude;
    let niceFraction;
    if (fraction <= 1.5) niceFraction = 1;
    else if (fraction <= 2.25) niceFraction = 2;
    else if (fraction <= 3.5) niceFraction = 2.5;
    else if (fraction <= 7.5) niceFraction = 5;
    else niceFraction = 10;
    return niceFraction * magnitude;
  };

  const niceRange = (values, symmetric, minimumSpan) => {
    let low = Math.min(...values);
    let high = Math.max(...values);
    if (low === high) {
      const half = Math.max(Math.abs(low) * 0.08, 0.10);
      low -= half;
      high += half;
    }
    if (minimumSpan && high - low < minimumSpan) {
      const center = (low + high) / 2;
      low = center - minimumSpan / 2;
      high = center + minimumSpan / 2;
    }
    const pad = (high - low) * 0.08;
    low -= pad;
    high += pad;
    const targetIntervals = symmetric ? 6 : 4;
    if (symmetric) {
      const extent = Math.max(Math.abs(low), Math.abs(high));
      low = -extent;
      high = extent;
    }
    const step = niceStep((high - low) / targetIntervals);
    if (symmetric) {
      const bound = Math.ceil(Math.max(Math.abs(low), Math.abs(high)) / step) * step;
      low = -bound;
      high = bound;
    } else {
      low = Math.floor(low / step) * step;
      high = Math.ceil(high / step) * step;
    }
    const intervals = Math.round((high - low) / step);
    const ticks = Array.from({length: intervals + 1}, (_, index) => low + index * step);
    if (low <= 0 && high >= 0 && !ticks.some((value) => Math.abs(value) < 1e-12)) {
      ticks.push(0);
      ticks.sort((a, b) => a - b);
    }
    return {low, high, ticks};
  };

  document.querySelectorAll('.paper-figure svg.figure-svg').forEach((svg) => {
    const axisLines = Array.from(svg.querySelectorAll('line.chart-axis-line'));
    const verticalAxis = axisLines.find((line) => {
      const x1 = Number(line.getAttribute('x1'));
      const x2 = Number(line.getAttribute('x2'));
      const y1 = Number(line.getAttribute('y1'));
      const y2 = Number(line.getAttribute('y2'));
      return Number.isFinite(x1) && x1 === x2 && y1 !== y2;
    });
    if (!verticalAxis) return; // Figure 6 is horizontal and keeps its own symmetric x-axis.

    const points = Array.from(svg.querySelectorAll('circle.chart-point[data-point-value]'));
    if (!points.length) return;
    const values = points.map((point) => Number(point.dataset.pointValue)).filter(Number.isFinite);
    if (!values.length) return;

    const yTitle = Array.from(svg.querySelectorAll('text.chart-axis-title')).find((node) => (node.getAttribute('transform') || '').includes('rotate(-90)'));
    const axisLabel = yTitle ? yTitle.textContent.trim() : '';
    const symmetric = axisLabel.includes('Z-score') || axisLabel.includes('전년 대비');
    const minimumSpan = axisLabel.includes('Concreteness') ? 0.40 : null;
    const range = niceRange(values, symmetric, minimumSpan);

    const plotTop = Math.min(Number(verticalAxis.getAttribute('y1')), Number(verticalAxis.getAttribute('y2')));
    const plotBottom = Math.max(Number(verticalAxis.getAttribute('y1')), Number(verticalAxis.getAttribute('y2')));
    const axisX = Number(verticalAxis.getAttribute('x1'));
    const horizontalAxis = axisLines.find((line) => Number(line.getAttribute('y1')) === Number(line.getAttribute('y2')));
    const plotRight = horizontalAxis ? Math.max(Number(horizontalAxis.getAttribute('x1')), Number(horizontalAxis.getAttribute('x2'))) : Number(svg.getAttribute('viewBox').split(/\s+/)[2]) - 50;
    const y = (value) => plotBottom - (plotBottom - plotTop) * (value - range.low) / (range.high - range.low);

    const originalPositions = new Map();
    points.forEach((point) => {
      const key = `${point.dataset.series || ''}|${point.dataset.year || ''}`;
      originalPositions.set(key, Number(point.getAttribute('cy')));
    });
    const labelOffsets = new Map();
    svg.querySelectorAll('text.chart-value-label[data-label-value]').forEach((label) => {
      const key = `${label.dataset.series || ''}|${label.dataset.year || ''}`;
      const originalPointY = originalPositions.get(key);
      if (Number.isFinite(originalPointY)) labelOffsets.set(label, Number(label.getAttribute('y')) - originalPointY);
    });

    points.forEach((point) => {
      const value = Number(point.dataset.pointValue);
      point.setAttribute('cy', y(value).toFixed(1));
    });
    labelOffsets.forEach((offset, label) => {
      const value = Number(label.dataset.labelValue);
      label.setAttribute('y', (y(value) + offset).toFixed(1));
    });

    svg.querySelectorAll('polyline[data-series]').forEach((polyline) => {
      const series = polyline.dataset.series || '';
      const seriesPoints = points
        .filter((point) => (point.dataset.series || '') === series)
        .sort((a, b) => Number(a.dataset.year || 0) - Number(b.dataset.year || 0));
      if (seriesPoints.length) {
        polyline.setAttribute('points', seriesPoints.map((point) => `${point.getAttribute('cx')},${point.getAttribute('cy')}`).join(' '));
      }
    });

    svg.querySelectorAll('text.chart-y-tick').forEach((node) => node.remove());
    svg.querySelectorAll('line.chart-grid:not(.chart-axis-line)').forEach((node) => node.remove());
    const insertBefore = svg.querySelector('polyline, circle.chart-point');
    range.ticks.slice().reverse().forEach((tick) => {
      const yy = y(tick);
      const line = document.createElementNS(svgNS, 'line');
      line.setAttribute('class', 'chart-grid');
      line.setAttribute('x1', String(axisX));
      line.setAttribute('x2', String(plotRight));
      line.setAttribute('y1', yy.toFixed(1));
      line.setAttribute('y2', yy.toFixed(1));
      const text = document.createElementNS(svgNS, 'text');
      text.setAttribute('class', 'chart-axis chart-y-tick');
      text.setAttribute('x', String(axisX - 8));
      text.setAttribute('y', (yy + 4).toFixed(1));
      text.setAttribute('text-anchor', 'end');
      text.textContent = tick.toFixed(2);
      if (insertBefore) {
        svg.insertBefore(line, insertBefore);
        svg.insertBefore(text, insertBefore);
      } else {
        svg.appendChild(line);
        svg.appendChild(text);
      }
    });

    const zero = svg.querySelector('line.chart-zero');
    if (zero && range.low <= 0 && range.high >= 0) {
      const zeroY = y(0).toFixed(1);
      zero.setAttribute('y1', zeroY);
      zero.setAttribute('y2', zeroY);
    }
    svg.dataset.axisLow = range.low.toFixed(2);
    svg.dataset.axisHigh = range.high.toFixed(2);
  });
})();
</script>
'''
    document = document.replace("</body>", axis_script + "</body>", 1)

    # Production-facing validation.
    forbidden = [
        "변수 해석:",
        "추가 기술 변수",
        "논문 독자가 핵심 변수의 의미와 계산 방식을 확인할 수 있도록",
        "과거·현재 시제와 미래 조동사 표지는 spaCy의 문장분할",
        "보정하지 않은",
        "paired t-test",
        "Welch t-test",
        "Wilcoxon rank-sum test",
        "exploratory analysis",
        "6.12 해석 시 유의사항",
    ]
    remaining = [term for term in forbidden if term in document]
    if remaining:
        raise RuntimeError(f"Forbidden production wording remains: {remaining}")
    required = [
        "대응표본 t-검정",
        "Welch t-검정",
        "탐색적 분석",
        "6.11 결과 해석 (Discussion)",
        "production-figure-series-refinement",
        "production-axis-range-refinement",
        "0 = 전체기간 평균",
    ]
    missing = [term for term in required if term not in document]
    if missing:
        raise RuntimeError(f"Required production refinements missing: {missing}")

    OUT.write_text(document, encoding="utf-8")
    print(f"Wrote production professor report: {OUT} ({len(document):,} chars)")


if __name__ == "__main__":
    main()
