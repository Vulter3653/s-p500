import { useRef } from "react";

const COLORS = ["#167c80", "#c58935", "#3d6388", "#9b5365", "#546b55"];
const LABELS = {
  ai_disclosure_rate: "AI 공시 비율",
  mean_ai_sentence_count_all: "전체 평균 AI 직접 문장 수",
  mean_ai_sentence_count_disclosers: "공시기업 조건부 평균 AI 직접 문장 수",
  whole_report_concreteness: "전체 보고서 구체성",
  ai_concreteness: "AI 직접 문장 구체성",
  past_tense_share: "과거 시제",
  present_tense_share: "현재 시제",
  future_tense_share: "미래 시제 표지",
  ai_lm_positive_share: "AI 긍정",
  ai_lm_negative_share: "AI 부정",
  ai_lm_uncertainty_share: "AI 불확실성",
};
const VARIABLE_LABELS = {
  whole_report_concreteness: "전체 보고서 구체성",
  ai_sentence_count: "AI 직접 문장 수",
  ai_concreteness: "AI 직접 문장 구체성",
  past_tense_share: "과거 시제 비율",
  present_tense_share: "현재 시제 비율",
  lm_uncertainty_share: "Loughran–McDonald 불확실성",
  fog_index: "Fog Index",
};

const finite = (value) => Number.isFinite(Number(value)) ? Number(value) : null;
const extent = (rows, keys) => {
  const values = rows.flatMap((row) => keys.map((key) => finite(row[key]))).filter((value) => value !== null);
  if (!values.length) return [0, 1];
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) return [min - 1, max + 1];
  const pad = (max - min) * 0.1;
  return [min - pad, max + pad];
};
const percentKey = (key) => key.includes("share") || key.includes("rate");
const formatValue = (value, key) => {
  if (value === null) return "-";
  return percentKey(key) ? `${(value * 100).toFixed(1)}%` : value.toLocaleString("ko-KR", { maximumFractionDigits: 2 });
};

function SvgDownload({ svgId }) {
  const download = () => {
    const node = document.querySelector(`[data-svg-id="${svgId}"]`);
    if (!node) return;
    const source = new XMLSerializer().serializeToString(node);
    const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${svgId}.svg`;
    anchor.click();
    URL.revokeObjectURL(url);
  };
  return <button type="button" className="figure-download" onClick={download}>SVG 다운로드</button>;
}

export function FigureShell({ id, number, title, introduction, caption, source, sourceCsv, condition, children, svgId = id }) {
  return <figure className="paper-figure" data-figure-id={id}>
    <div className="figure-number">{number}</div>
    <h3>{title}</h3>
    <p className="figure-introduction">{introduction}</p>
    <div className="figure-plot">{children}</div>
    <figcaption><strong>주:</strong> {caption}{condition && <> 조건부 표본: {condition}.</>}</figcaption>
    <details className="figure-source"><summary>자료원 및 재현성</summary><p><strong>Source:</strong> <code>{source}</code><br /><strong>생성:</strong> <code>scripts/generate_web_analysis_data.py</code><br /><strong>단위:</strong> firm-year 또는 유효한 연속연도 기업 pair</p></details>
    <nav className="figure-downloads" aria-label={`${number} 다운로드`}><a href={sourceCsv} download>Source CSV 다운로드</a><SvgDownload svgId={svgId} /></nav>
  </figure>;
}

export function LineFigure({ id, rows, keys, labels = keys.map((key) => LABELS[key] || key), percent = false, ariaLabel }) {
  const width = 760; const height = 300; const left = 62; const right = 22; const top = 28; const bottom = 44;
  const validRows = (Array.isArray(rows) ? rows : []).filter((row) => finite(row.report_year) !== null);
  const [min, max] = extent(validRows, keys);
  const x = (year) => left + ((year - 2020) / 5) * (width - left - right);
  const y = (value) => top + (max - value) / (max - min) * (height - top - bottom);
  const ticks = [min, min + (max - min) / 2, max];
  return <svg className="figure-svg" data-svg-id={id} viewBox={`0 0 ${width} ${height}`} role="img" aria-label={ariaLabel}>
    <title>{ariaLabel}</title><desc>연도별 분석값을 선과 점으로 표시한 그래프</desc>
    {ticks.map((tick) => <g key={tick}><line x1={left} x2={width - right} y1={y(tick)} y2={y(tick)} className="chart-grid" /><text x={left - 8} y={y(tick) + 4} textAnchor="end" className="chart-axis">{percent ? `${(tick * 100).toFixed(0)}%` : tick.toLocaleString("ko-KR", { maximumFractionDigits: 1 })}</text></g>)}
    {validRows.map((row) => <text key={row.report_year} x={x(Number(row.report_year))} y={height - 16} textAnchor="middle" className="chart-axis">{row.report_year}</text>)}
    {keys.map((key, index) => {
      const points = validRows.map((row) => { const value = finite(row[key]); return value === null ? null : `${x(Number(row.report_year))},${y(value)}`; }).filter(Boolean).join(" ");
      return <g key={key}><polyline points={points} fill="none" stroke={COLORS[index % COLORS.length]} strokeWidth="3" /><text x={width - right} y={top + index * 18} textAnchor="end" className="chart-legend" fill={COLORS[index % COLORS.length]}>{labels[index]}</text>{validRows.map((row) => finite(row[key]) === null ? null : <circle key={`${key}-${row.report_year}`} cx={x(Number(row.report_year))} cy={y(finite(row[key]))} r="4" fill={COLORS[index % COLORS.length]}><title>{`${row.report_year}: ${formatValue(finite(row[key]), key)}`}</title></circle>)}</g>;
    })}
  </svg>;
}

export function EffectSizeFigure({ id, rows, ariaLabel }) {
  const width = 760; const rowHeight = 30; const left = 255; const right = 30; const top = 26;
  const items = (Array.isArray(rows) ? rows : []).filter((row) => finite(row.standardized_mean_difference) !== null);
  const [min, max] = extent(items, ["standardized_mean_difference"]);
  const x = (value) => left + (value - min) / (max - min) * (width - left - right);
  return <svg className="figure-svg effect-svg" data-svg-id={id} viewBox={`0 0 ${width} ${Math.max(170, top + items.length * rowHeight + 24)}`} role="img" aria-label={ariaLabel}>
    <title>{ariaLabel}</title><desc>AI 공시와 미공시 집단의 표준화 평균 차이</desc>
    <line x1={x(0)} x2={x(0)} y1={top - 8} y2={top + items.length * rowHeight} className="chart-zero" />
    {[-0.8, -0.5, -0.2, 0.2, 0.5, 0.8].map((value) => value > min && value < max ? <line key={value} x1={x(value)} x2={x(value)} y1={top - 8} y2={top + items.length * rowHeight} className="chart-reference" /> : null)}
    {items.map((row, index) => { const y = top + index * rowHeight + 12; const value = finite(row.standardized_mean_difference); return <g key={row.variable}><text x={left - 10} y={y + 4} textAnchor="end" className="chart-axis">{VARIABLE_LABELS[row.variable] || row.variable}</text><line x1={x(0)} x2={x(value)} y1={y} y2={y} stroke={value < 0 ? COLORS[3] : COLORS[0]} strokeWidth="3" /><circle cx={x(value)} cy={y} r="5" fill={value < 0 ? COLORS[3] : COLORS[0]}><title>{`${row.variable}: ${value.toFixed(3)}`}</title></circle></g>; })}
    <text x={x(0)} y={top + items.length * rowHeight + 18} textAnchor="middle" className="chart-axis">0</text>
  </svg>;
}

export function WithinChangeFigure({ id, rows, ariaLabel }) {
  const variables = ["whole_report_concreteness", "ai_sentence_count", "past_tense_share", "lm_uncertainty_share", "fog_index"];
  const width = 760; const rowHeight = 108; const left = 210; const right = 30; const top = 10;
  const groups = variables.map((variable) => ({ variable, rows: (Array.isArray(rows) ? rows : []).filter((row) => row.variable === variable) })).filter((item) => item.rows.length);
  return <svg className="figure-svg change-svg" data-svg-id={id} viewBox={`0 0 ${width} ${Math.max(180, top + groups.length * rowHeight)}`} role="img" aria-label={ariaLabel}>
    <title>{ariaLabel}</title><desc>연속된 연도 관측치가 있는 동일 기업의 평균 변화</desc>
    {groups.map(({ variable, rows: subset }, index) => { const yBase = top + index * rowHeight; const [min, max] = extent(subset, ["mean_within_firm_change"]); const x = (year) => left + ((year - 2021) / 4) * (width - left - right); const y = (value) => yBase + 25 + (max - value) / (max - min) * 55; const zero = min <= 0 && max >= 0 ? y(0) : null; const points = subset.map((row) => `${x(Number(row.report_year))},${y(finite(row.mean_within_firm_change))}`).join(" "); return <g key={variable}><text x={0} y={yBase + 18} className="chart-axis chart-label">{VARIABLE_LABELS[variable] || variable}</text>{zero !== null && <line x1={left} x2={width - right} y1={zero} y2={zero} className="chart-zero" />}{[2021, 2022, 2023, 2024, 2025].map((year) => <text key={year} x={x(year)} y={yBase + 96} textAnchor="middle" className="chart-axis">{year}</text>)}<polyline points={points} fill="none" stroke={COLORS[index % COLORS.length]} strokeWidth="3" />{subset.map((row) => <circle key={`${variable}-${row.report_year}`} cx={x(Number(row.report_year))} cy={y(finite(row.mean_within_firm_change))} r="4" fill={COLORS[index % COLORS.length]}><title>{`${row.report_year}: ${finite(row.mean_within_firm_change).toFixed(4)}`}</title></circle>)}</g>; })}
  </svg>;
}
