import { formatVariableValue, labelFor, unitFor } from "./variableLabels";

const COLORS = ["#167c80", "#c58935", "#3d6388", "#9b5365", "#546b55"];
const DASHES = [undefined, "8 4", "3 4", "10 3 2 3", "5 3"];

const finite = (value) => Number.isFinite(Number(value)) ? Number(value) : null;
const extent = (rows, keys, includeZero = false) => {
  const values = rows.flatMap((row) => keys.map((key) => finite(row[key]))).filter((value) => value !== null);
  if (includeZero) values.push(0);
  if (!values.length) return [0, 1];
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) return [min - 1, max + 1];
  const pad = (max - min) * 0.12;
  return [min - pad, max + pad];
};
const yearDomain = (rows, yearKey = "report_year") => {
  const years = rows.map((row) => finite(row[yearKey])).filter((value) => value !== null);
  if (!years.length) return [0, 1];
  const min = Math.min(...years);
  const max = Math.max(...years);
  return [min, max === min ? min + 1 : max];
};
const yearTicks = (minYear, maxYear, maxTicks = 8) => {
  const step = Math.max(1, Math.ceil((maxYear - minYear) / Math.max(maxTicks - 1, 1)));
  const ticks = [];
  for (let year = minYear; year <= maxYear; year += step) ticks.push(year);
  if (ticks[ticks.length - 1] !== maxYear) ticks.push(maxYear);
  return ticks;
};
const axisValue = (value, key) => {
  const unit = unitFor(key);
  if (unit === "%") return `${(value * 100).toFixed(1)}%`;
  return value.toLocaleString("ko-KR", { maximumFractionDigits: unit === "단어" ? 0 : 2 });
};

export function FigureShell({ id, number, title, introduction, caption, condition, variables = [], legendItems = [], children }) {
  const items = variables.map((item, index) => typeof item === "string" ? {
    key: item,
    label: labelFor(item),
    unit: unitFor(item),
    color: COLORS[index % COLORS.length],
    dash: DASHES[index % DASHES.length],
  } : item);
  return <figure className="paper-figure" data-figure-id={id}>
    <div className="figure-number">{number}</div>
    <h3>{title}</h3>
    <p className="figure-introduction">{introduction}</p>
    {!!items.length && <div className="figure-variable-list" aria-label={`${number} 분석 변수`}>
      {items.map((item, index) => <span key={item.key || item.label} className="figure-variable-item"><i style={{ borderColor: item.color || COLORS[index % COLORS.length], borderStyle: item.dash ? "dashed" : "solid" }} /> <strong>{item.label || labelFor(item.key)}</strong><small>{item.unit || unitFor(item.key)}</small></span>)}
    </div>}
    {!!legendItems.length && <div className="figure-group-legend" aria-label={`${number} 집단 범례`}>
      {legendItems.map((item) => <span key={item.label}><i style={{ borderColor: item.color, borderStyle: item.dash ? "dashed" : "solid" }} />{item.label}</span>)}
    </div>}
    <div className="figure-plot">{children}</div>
    <figcaption><strong>주:</strong> {caption}{condition && <> 표본: {condition}.</>}</figcaption>
  </figure>;
}

export function LineFigure({ id, rows, keys, ariaLabel }) {
  const width = 760; const height = 320; const left = 72; const right = 34; const top = 34; const bottom = 48;
  const validRows = (Array.isArray(rows) ? rows : []).filter((row) => finite(row.report_year) !== null);
  const [min, max] = extent(validRows, keys);
  const [minYear, maxYear] = yearDomain(validRows);
  const x = (year) => left + ((year - minYear) / (maxYear - minYear)) * (width - left - right);
  const y = (value) => top + (max - value) / (max - min) * (height - top - bottom);
  const ticks = [min, min + (max - min) / 2, max];
  return <svg className="figure-svg" data-svg-id={id} viewBox={`0 0 ${width} ${height}`} role="img" aria-label={ariaLabel}>
    <title>{ariaLabel}</title><desc>2020년부터 2025년까지의 분석값을 변수별 선, 점, 수치로 표시한 그래프</desc>
    {ticks.map((tick) => <g key={tick}><line x1={left} x2={width - right} y1={y(tick)} y2={y(tick)} className="chart-grid" /><text x={left - 9} y={y(tick) + 4} textAnchor="end" className="chart-axis">{axisValue(tick, keys[0])}</text></g>)}
    {yearTicks(minYear, maxYear).map((year) => <text key={year} x={x(year)} y={height - 16} textAnchor="middle" className="chart-axis">{year}</text>)}
    {keys.map((key, index) => {
      const series = validRows.filter((row) => finite(row[key]) !== null);
      const points = series.map((row) => `${x(Number(row.report_year))},${y(finite(row[key]))}`).join(" ");
      const last = series[series.length - 1];
      return <g key={key}><polyline points={points} fill="none" stroke={COLORS[index % COLORS.length]} strokeWidth="3" strokeDasharray={DASHES[index % DASHES.length]} />{series.map((row) => { const value = finite(row[key]); const text = `${row.report_year}년 ${labelFor(key)} ${formatVariableValue(value, key)}`; return <circle key={`${key}-${row.report_year}`} cx={x(Number(row.report_year))} cy={y(value)} r="4.5" fill="#fff" stroke={COLORS[index % COLORS.length]} strokeWidth="3" aria-label={text}><title>{text}</title></circle>; })}{last && <text x={x(Number(last.report_year)) - 6} y={y(finite(last[key])) - 9 - index * 2} textAnchor="end" className="chart-value-label" fill={COLORS[index % COLORS.length]}>{formatVariableValue(finite(last[key]), key)}</text>}</g>;
    })}
  </svg>;
}

export function PanelABFigure({ id, rows, ariaLabel }) {
  const width = 760; const panelHeight = 184; const left = 74; const right = 28; const top = 34;
  const panels = [
    ["ai_disclosure_rate", "Panel A · AI 관련 공시 비율"],
    ["report_word_count", "Panel B · 평균 보고서 단어 수"],
  ];
  const valid = Array.isArray(rows) ? rows : [];
  return <svg className="figure-svg panel-ab-svg" data-svg-id={id} viewBox={`0 0 ${width} ${panelHeight * panels.length}`} role="img" aria-label={ariaLabel}>
    <title>{ariaLabel}</title><desc>2020–2025년 AI 관련 공시 비율과 평균 보고서 단어 수를 독립된 세로축으로 표시한다.</desc>
    {panels.map(([key, title], index) => {
      const panelRows = valid.filter((row) => finite(row[key]) !== null);
      const [min, max] = extent(panelRows, [key]);
      const [minYear, maxYear] = yearDomain(panelRows);
      const yBase = index * panelHeight;
      const x = (year) => left + ((year - minYear) / (maxYear - minYear)) * (width - left - right);
      const y = (value) => yBase + top + (max - value) / (max - min) * 102;
      const points = panelRows.map((row) => `${x(Number(row.report_year))},${y(finite(row[key]))}`).join(" ");
      return <g key={key}><text x={left} y={yBase + 18} className="chart-axis chart-label">{title} ({unitFor(key)})</text>{[min, min + (max - min) / 2, max].map((tick) => <g key={`${key}-${tick}`}><line x1={left} x2={width - right} y1={y(tick)} y2={y(tick)} className="chart-grid" /><text x={left - 9} y={y(tick) + 4} textAnchor="end" className="chart-axis">{axisValue(tick, key)}</text></g>)}<polyline points={points} fill="none" stroke={COLORS[0]} strokeWidth="3" />{panelRows.map((row) => { const value = finite(row[key]); const text = `${row.report_year}년 ${labelFor(key)} ${formatVariableValue(value, key)}`; return <g key={`${key}-${row.report_year}`}><circle cx={x(Number(row.report_year))} cy={y(value)} r="4.5" fill="#fff" stroke={COLORS[0]} strokeWidth="3" aria-label={text}><title>{text}</title></circle><text x={x(Number(row.report_year))} y={y(value) - 9} textAnchor="middle" className="chart-value-label">{formatVariableValue(value, key)}</text></g>; })}{yearTicks(minYear, maxYear, 6).map((year) => <text key={`${key}-year-${year}`} x={x(year)} y={yBase + 166} textAnchor="middle" className="chart-axis">{year}</text>)}</g>;
    })}
  </svg>;
}

export function EffectSizeFigure({ id, rows, ariaLabel }) {
  const width = 760; const rowHeight = 34; const left = 285; const right = 52; const top = 26;
  const items = (Array.isArray(rows) ? rows : []).filter((row) => finite(row.standardized_mean_difference) !== null);
  const [min, max] = extent(items, ["standardized_mean_difference"], true);
  const x = (value) => left + (value - min) / (max - min) * (width - left - right);
  return <svg className="figure-svg effect-svg" data-svg-id={id} viewBox={`0 0 ${width} ${Math.max(170, top + items.length * rowHeight + 28)}`} role="img" aria-label={ariaLabel}>
    <title>{ariaLabel}</title><desc>AI 관련 공시 기업과 미공시 기업의 표준화 평균 차이를 변수별로 표시한다.</desc>
    <line x1={x(0)} x2={x(0)} y1={top - 8} y2={top + items.length * rowHeight} className="chart-zero" />
    {items.map((row, index) => { const y = top + index * rowHeight + 12; const value = finite(row.standardized_mean_difference); const color = value < 0 ? COLORS[3] : COLORS[0]; const text = `${labelFor(row.variable)} 표준화 평균 차이 ${value.toFixed(3)}`; return <g key={row.variable}><text x={left - 12} y={y + 4} textAnchor="end" className="chart-axis">{labelFor(row.variable)}</text><line x1={x(0)} x2={x(value)} y1={y} y2={y} stroke={color} strokeWidth="3" /><circle cx={x(value)} cy={y} r="5" fill={color} aria-label={text}><title>{text}</title></circle><text x={x(value) + (value < 0 ? -9 : 9)} y={y + 4} textAnchor={value < 0 ? "end" : "start"} className="chart-value-label">{value.toFixed(3)}</text></g>; })}
  </svg>;
}

export function GroupMeanFigure({ id, rows, ariaLabel }) {
  const variables = ["whole_report_concreteness", "lm_uncertainty_share", "fog_index", "report_word_count"];
  const width = 760; const panelHeight = 154; const left = 76; const right = 28; const top = 31;
  const valid = Array.isArray(rows) ? rows : [];
  const colors = { 0: COLORS[1], 1: COLORS[0] };
  const labels = { 0: "AI 관련 공시 없음", 1: "AI 관련 공시 있음" };
  return <svg className="figure-svg group-mean-svg" data-svg-id={id} viewBox={`0 0 ${width} ${panelHeight * variables.length}`} role="img" aria-label={ariaLabel}>
    <title>{ariaLabel}</title><desc>AI 관련 공시 여부에 따른 기업-연도 평균을 네 변수의 독립된 패널로 비교한다.</desc>
    {variables.map((variable, panelIndex) => {
      const panelRows = valid.filter((row) => finite(row.report_year) !== null && finite(row[variable]) !== null);
      const [min, max] = extent(panelRows, [variable]);
      const yBase = panelIndex * panelHeight;
      const [minYear, maxYear] = yearDomain(panelRows);
      const x = (year) => left + ((year - minYear) / (maxYear - minYear)) * (width - left - right);
      const y = (value) => yBase + top + (max - value) / (max - min) * 86;
      return <g key={variable}><text x={left} y={yBase + 17} className="chart-axis chart-label">{labelFor(variable)} ({unitFor(variable)})</text>{[min, min + (max - min) / 2, max].map((tick) => <g key={`${variable}-${tick}`}><line x1={left} x2={width - right} y1={y(tick)} y2={y(tick)} className="chart-grid" /><text x={left - 9} y={y(tick) + 4} textAnchor="end" className="chart-axis">{axisValue(tick, variable)}</text></g>)}{[0, 1].map((group) => { const subset = panelRows.filter((row) => Number(row.ai_disclosure) === group); const points = subset.map((row) => `${x(Number(row.report_year))},${y(finite(row[variable]))}`).join(" "); const last = subset[subset.length - 1]; return <g key={`${variable}-${group}`}><polyline points={points} fill="none" stroke={colors[group]} strokeWidth="3" strokeDasharray={group === 0 ? DASHES[1] : undefined} />{subset.map((row) => { const value = finite(row[variable]); const text = `${row.report_year}년 ${labels[group]} ${labelFor(variable)} ${formatVariableValue(value, variable)}`; return <circle key={`${variable}-${group}-${row.report_year}`} cx={x(Number(row.report_year))} cy={y(value)} r="4" fill="#fff" stroke={colors[group]} strokeWidth="3" aria-label={text}><title>{text}</title></circle>; })}{last && <text x={x(Number(last.report_year)) - 5} y={y(finite(last[variable])) - 7 - group * 2} textAnchor="end" className="chart-value-label" fill={colors[group]}>{formatVariableValue(finite(last[variable]), variable)}</text>}</g>; })}{yearTicks(minYear, maxYear, 6).map((year) => <text key={`${variable}-year-${year}`} x={x(year)} y={yBase + 141} textAnchor="middle" className="chart-axis">{year}</text>)}</g>;
    })}
  </svg>;
}

export function WithinChangeFigure({ id, rows, ariaLabel }) {
  const variables = ["whole_report_concreteness", "ai_sentence_count", "past_tense_share", "lm_uncertainty_share", "fog_index"];
  const width = 760; const rowHeight = 112; const left = 255; const right = 36; const top = 10;
  const groups = variables.map((variable) => ({ variable, rows: (Array.isArray(rows) ? rows : []).filter((row) => row.variable === variable && finite(row.report_year) !== null) })).filter((item) => item.rows.length);
  return <svg className="figure-svg change-svg" data-svg-id={id} viewBox={`0 0 ${width} ${Math.max(180, top + groups.length * rowHeight)}`} role="img" aria-label={ariaLabel}>
    <title>{ariaLabel}</title><desc>2020–2025년 중 연속된 두 연도에 관찰된 동일 기업의 평균 변화를 표시한다.</desc>
    {groups.map(({ variable, rows: subset }, index) => { const yBase = top + index * rowHeight; const [min, max] = extent(subset, ["mean_within_firm_change"], true); const [minYear, maxYear] = yearDomain(subset); const x = (year) => left + ((year - minYear) / (maxYear - minYear)) * (width - left - right); const y = (value) => yBase + 28 + (max - value) / (max - min) * 58; const points = subset.map((row) => `${x(Number(row.report_year))},${y(finite(row.mean_within_firm_change))}`).join(" "); const last = subset[subset.length - 1]; return <g key={variable}><text x={0} y={yBase + 19} className="chart-axis chart-label">{labelFor(variable)} ({unitFor(variable)})</text><line x1={left} x2={width - right} y1={y(0)} y2={y(0)} className="chart-zero" />{yearTicks(minYear, maxYear, 6).map((year) => <text key={year} x={x(year)} y={yBase + 103} textAnchor="middle" className="chart-axis">{year}</text>)}<polyline points={points} fill="none" stroke={COLORS[index % COLORS.length]} strokeWidth="3" strokeDasharray={DASHES[index % DASHES.length]} />{subset.map((row) => { const value = finite(row.mean_within_firm_change); const text = `${row.report_year}년 ${labelFor(variable)} 평균 변화 ${formatVariableValue(value, variable)}`; return <circle key={`${variable}-${row.report_year}`} cx={x(Number(row.report_year))} cy={y(value)} r="4" fill="#fff" stroke={COLORS[index % COLORS.length]} strokeWidth="3" aria-label={text}><title>{text}</title></circle>; })}{last && <text x={x(Number(last.report_year)) - 5} y={y(finite(last.mean_within_firm_change)) - 8} textAnchor="end" className="chart-value-label">{formatVariableValue(finite(last.mean_within_firm_change), variable)}</text>}</g>; })}
  </svg>;
}
