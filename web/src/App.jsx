import { useEffect, useMemo, useState } from "react";
import { EffectSizeFigure, FigureShell, GroupMeanFigure, LineFigure, PanelABFigure, WithinChangeFigure } from "./Figures";

const CORE_FILES = {
  summary: "analysis-summary.json",
  definitions: "variable-definitions.json",
  sourceManifest: "source-manifest.json",
};

const SUPPLEMENTAL_FILES = {
  yearly: "yearly-statistics.json",
  descriptive: "descriptive-statistics.json",
  comparison: "disclosure-comparison.json",
  within: "within-firm-changes.json",
  changes: "year-over-year-changes.json",
  pearson: "pearson-correlations.json",
  spearman: "spearman-correlations.json",
  vif: "vif.json",
  sampleAudit: "sample-audit.json",
  quality: "quality-control.json",
  buildMetadata: "build-metadata.json",
  figureData: "figure-data.json",
  figureManifest: "figure-manifest.json",
  coreDescriptive: "core-descriptive-statistics.json",
  pearsonCore: "pearson-core.json",
  modelFree: "model-free-comparison.json",
};

const DOCUMENTS = [
  ["methodology", "research-dashboard-methodology.md"],
  ["results", "research-dashboard-results.md"],
  ["limitations", "research-dashboard-limitations.md"],
  ["reproducibility", "research-dashboard-reproducibility.md"],
];

const formatNumber = (value, digits = 2) => {
  if (value === null || value === undefined || value === "" || Number.isNaN(Number(value))) return "-";
  return Number(value).toLocaleString("ko-KR", { maximumFractionDigits: digits });
};
const formatInteger = (value) => value === null || value === undefined ? "-" : Math.round(Number(value)).toLocaleString("ko-KR");
const formatPercent = (value, digits = 1) => value === null || value === undefined || Number.isNaN(Number(value)) ? "-" : `${(Number(value) * 100).toFixed(digits)}%`;
const formatP = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  const n = Number(value);
  return n < 0.001 ? "p < .001" : `p = ${n.toFixed(4).replace(/^0\./, ".")}`;
};
const display = (value) => Array.isArray(value) ? value.join(", ") : (value || "-");
const safeRows = (value) => Array.isArray(value) ? value : [];
const dataUrl = (path) => `${import.meta.env.BASE_URL}${path.replace(/^\//, "")}`;

async function loadJson(filename) {
  const response = await fetch(dataUrl(`data/${filename}`));
  if (!response.ok) throw new Error(`${filename}: ${response.status}`);
  return response.json();
}

function MarkdownLite({ value }) {
  if (!value) return <p className="muted">문서를 불러오는 중입니다.</p>;
  return <div className="source-document">{value.split(/\r?\n/).map((line, index) => {
    if (line.startsWith("# ")) return <h3 key={index}>{line.slice(2)}</h3>;
    if (line.startsWith("## ")) return <h4 key={index}>{line.slice(3)}</h4>;
    if (line.startsWith("### ")) return <h5 key={index}>{line.slice(4)}</h5>;
    if (line.startsWith("- ")) return <p key={index}>• {line.slice(2)}</p>;
    if (line.startsWith("```")) return null;
    if (!line.trim()) return <div className="md-space" key={index} />;
    return <p key={index}>{line}</p>;
  })}</div>;
}

function SourceNote({ source, generatedBy = "scripts/generate_web_analysis_data.py", n, condition }) {
  return <details className="source-note"><summary>기술 재현성 정보</summary><p><strong>자료원:</strong> <code>{source || "web/public/data/"}</code> · <strong>생성:</strong> <code>{generatedBy}</code>{n !== undefined && <> · <strong>N:</strong> {formatInteger(n)}</>}{condition && <> · <strong>조건:</strong> {condition}</>}</p></details>;
}

function SupplementalError({ source }) {
  return <details className="section-error"><summary>자료를 불러오지 못했습니다.</summary><p>기술 재현성 정보에서 요청된 자료의 상세 경로를 확인할 수 있습니다.</p><code>{source}</code></details>;
}

function MetricTable({ rows, columns, caption, source, condition }) {
  return <div className="table-card"><div className="table-scroll"><table className="paper-table"><caption>{caption}</caption><thead><tr>{columns.map(([key, label]) => <th key={key}>{label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.variable || row.report_year || row.year || "row"}-${index}`}>{columns.map(([key]) => <td key={key}>{row[key] === null || row[key] === undefined ? "-" : row[key]}</td>)}</tr>)}</tbody></table></div><SourceNote source={source} condition={condition} /></div>;
}

function FormulaBlock({ title, formula, note }) {
  return <div className="formula-block"><h4>{title}</h4><div className="formula">{formula}</div>{note && <p>{note}</p>}</div>;
}

function VariableBlock({ item }) {
  return <details className="variable-block" data-variable-definition={item.variable}><summary><span><code>{item.variable}</code><strong>{item.display_name}</strong></span><em>{item.analysis_level}</em></summary><div className="variable-detail"><p><strong>개념적 정의</strong>{item.conceptual_meaning}</p><p><strong>조작적 정의</strong>{item.definition} {item.operationalization}</p><FormulaBlock title="수식" formula={item.formula} /><div className="definition-grid"><p><strong>분자</strong>{display(item.numerator)}</p><p><strong>분모</strong>{display(item.denominator)}</p><p><strong>단위</strong>{display(item.unit)}</p><p><strong>적격 토큰</strong>{display(item.token_rule)}</p><p><strong>적격 문장</strong>{display(item.sentence_rule)}</p><p><strong>사전/NLP</strong>{display(item.method)}</p><p><strong>전처리</strong>{display(item.preprocessing)}</p><p><strong>결측 처리</strong>{display(item.missing_rule)}</p><p><strong>0 처리</strong>{display(item.zero_rule)}</p><p><strong>조건부 표본</strong>{display(item.conditional_sample)}</p><p><strong>Source column</strong><code>{display(item.source_columns)}</code></p><p><strong>Source dataset</strong><code>{item.source_dataset}</code></p><p><strong>Source script</strong><code>{display(item.source_scripts)}</code></p><p><strong>검증 규칙</strong>{display(item.validation_rule)}</p><p><strong>해석</strong>{display(item.interpretation)}</p><p><strong>한계</strong>{display(item.limitation)}</p></div></div></details>;
}

function Section({ id, number, title, kicker, children }) {
  return <section className="report-section" id={id}><div className="section-heading"><span className="section-number">{number}</span><div><p className="kicker">{kicker}</p><h2>{title}</h2></div></div>{children}</section>;
}

function CoreTables({ coreDescriptive, pearsonCore, modelFree, figureData, buildPeriod }) {
  const descriptiveRows = safeRows(coreDescriptive).map((row) => ({
    variable: row.display_name || row.variable,
    N: formatInteger(row.N),
    mean: formatNumber(row.mean, 4),
    sd: formatNumber(row.standard_deviation, 4),
    q1: formatNumber(row.p25, 4),
    median: formatNumber(row.median, 4),
    q3: formatNumber(row.p75, 4),
  }));
  const primaryRows = safeRows(modelFree?.primary).map((row) => ({
    variable: row.display_name || row.variable,
    disclosure_N: formatInteger(row.disclosure_N),
    disclosure_mean: formatNumber(row.disclosure_mean, 4),
    non_disclosure_N: formatInteger(row.non_disclosure_N),
    non_disclosure_mean: formatNumber(row.non_disclosure_mean, 4),
    mean_difference: formatNumber(row.mean_difference, 4),
    welch_t: formatNumber(row.welch_t, 3),
    welch_pvalue: formatP(row.welch_pvalue),
  }));
  const secondaryRows = safeRows(modelFree?.secondary).map((row) => ({
    variable: row.display_name || row.variable,
    q1_mean: formatNumber(row.q1_mean, 4),
    q4_mean: formatNumber(row.q4_mean, 4),
    mean_difference: formatNumber(row.mean_difference, 4),
    welch_t: formatNumber(row.welch_t, 3),
    welch_pvalue: formatP(row.welch_pvalue),
    wilcoxon_statistic: formatNumber(row.wilcoxon_statistic, 3),
    wilcoxon_pvalue: formatP(row.wilcoxon_pvalue),
  }));
  const stars = (p) => p === null || p === undefined ? "" : Number(p) < 0.001 ? "***" : Number(p) < 0.01 ? "**" : Number(p) < 0.05 ? "*" : "";
  return <Section id="core-tables" number="7A" title="핵심 고정표와 Model-free 비교" kicker="CORE TABLES · 2020–2025">
    <p className="caution">아래 핵심표는 화면 선택기간과 무관하게 2020–2025년 패널 2,829개 기업-연도에 고정된다. 기술통계·상관관계·단순 집단 비교이며 인과효과나 실제 AI 도입을 측정하지 않는다.</p>
    <MetricTable caption="표 2. 2020–2025 주요 변수 기술통계 (N=2,829 기업-연도)" rows={descriptiveRows} columns={[["variable", "변수"], ["N", "N"], ["mean", "평균"], ["sd", "표준편차"], ["q1", "제1사분위수"], ["median", "중앙값"], ["q3", "제3사분위수"]]} source="/data/core-descriptive-statistics.json" condition="2020–2025; 변수별 유효 N" />
    <MetricTable caption="표 4A. AI 관련 공시 있음·없음 기업의 단순 평균 비교" rows={primaryRows} columns={[["variable", "변수"], ["disclosure_N", "공시 있음 N"], ["disclosure_mean", "공시 있음 평균"], ["non_disclosure_N", "공시 없음 N"], ["non_disclosure_mean", "공시 없음 평균"], ["mean_difference", "평균 차이"], ["welch_t", "Welch t"], ["welch_pvalue", "p-value"]]} source="/data/model-free-comparison.json" condition="공시 있음 − 공시 없음; 연도·산업·규모 통제 없음" />
    <MetricTable caption="표 4B. 보고서 길이 Q1·Q4 보조 비교 (차이 = Q1 − Q4)" rows={secondaryRows} columns={[["variable", "변수"], ["q1_mean", "Q1 평균"], ["q4_mean", "Q4 평균"], ["mean_difference", "Q1 − Q4"], ["welch_t", "Welch t"], ["welch_pvalue", "Welch p"], ["wilcoxon_statistic", "Wilcoxon 통계량"], ["wilcoxon_pvalue", "Wilcoxon p"]]} source="/data/model-free-comparison.json" condition="전체 2020–2025에서 log_report_word_count Q1/Q4 분류" />
    <p className="source-note">유의표시는 p &lt; .05(*), p &lt; .01(**), p &lt; .001(***) 기준으로 생성한다. 전체 구축기간은 {buildPeriod}이지만 본문 핵심표는 2020–2025로 고정한다.</p>
    <FigureShell id="figure-01-panel-ab" number="Figure 1A/B" title="연도별 AI 관련 공시와 보고서 길이" introduction="공통 연도축을 사용하되 서로 다른 단위의 두 결과를 Panel A와 Panel B로 분리한다." caption="연도별 기술적 추이이며 공통 시간추세를 인과관계로 해석하지 않는다." condition="선택기간과 별개로 2020–2025 고정 핵심패널" source="analysis/descriptive_2020_2025/figures/figure_aggregate_data.csv" sourceCsv={dataUrl("downloads/figure-aggregate-data.csv")}><PanelABFigure id="figure-01-panel-ab-svg" rows={figureData?.aggregate} ariaLabel="AI 관련 공시 비율과 평균 보고서 단어 수의 연도별 Panel A와 B" /></FigureShell>
    <FigureShell id="figure-07-group" number="Figure 7A" title="AI 관련 공시·미공시 기업의 평균 추이" introduction="AI 관련 공시가 있는 기업-연도와 없는 기업-연도의 평균 언어 특성을 연도별로 비교한다." caption="집단별 평균은 연도·산업·기업 규모를 통제하지 않은 model-free evidence이며 인과효과를 의미하지 않는다." condition="2020–2025; ai_disclosure=1과 0의 연도별 집단 평균" source="analysis/descriptive_2020_2025/figures/figure_ai_group_data.csv" sourceCsv={dataUrl("downloads/figure-ai-group-data.csv")}><GroupMeanFigure id="figure-07-group-svg" rows={figureData?.ai_group} ariaLabel="AI 관련 공시 있음과 없음 기업의 평균 언어 특성 추이" /></FigureShell>
    <div className="table-card"><div className="table-scroll"><table className="paper-table pearson-table"><caption>표 3. 2020–2025 핵심 변수 Pearson 상관행렬 (N=2,829 기업-연도)</caption><thead><tr><th>변수</th>{safeRows(pearsonCore?.variables).map((item) => <th key={item.variable} title={item.display_name}>{item.display_name}</th>)}</tr></thead><tbody>{safeRows(pearsonCore?.rows).map((row) => <tr key={row.variable}><th scope="row">{row.display_name}</th>{safeRows(row.cells).map((cell) => <td key={cell.variable} title={"pairwise N=" + formatInteger(cell.pairwise_N) + "; " + formatP(cell.pvalue)}>{cell.correlation === null || cell.correlation === undefined ? "-" : formatNumber(cell.correlation, 3)}{stars(cell.pvalue)}</td>)}</tr>)}</tbody></table></div><SourceNote source="/data/pearson-core.json" condition="Pearson; pairwise 유효 N과 p-value는 셀 title에 표시" /></div>
  </Section>;
}

function PeriodControls({ availableYears, startYear, endYear, onStartYear, onEndYear, onMainPeriod, onFullPeriod }) {
  return <section aria-label="분석기간 설정" style={{ border: "1px solid var(--rule, #d8d3c8)", padding: "1rem", margin: "1.5rem 0", background: "var(--paper-soft, #f7f5ef)" }}>
    <p className="kicker">DISPLAY PERIOD</p>
    <h2 style={{ marginTop: 0 }}>분석기간 설정</h2>
    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "end" }}>
      <label>시작연도<br /><select value={startYear} onChange={(event) => onStartYear(Number(event.target.value))}>{availableYears.filter((year) => year <= endYear).map((year) => <option key={year} value={year}>{year}</option>)}</select></label>
      <label>종료연도<br /><select value={endYear} onChange={(event) => onEndYear(Number(event.target.value))}>{availableYears.filter((year) => year >= startYear).map((year) => <option key={year} value={year}>{year}</option>)}</select></label>
      <button type="button" onClick={onMainPeriod}>메인 기간 2020–2025</button>
      <button type="button" onClick={onFullPeriod}>전체 기간</button>
    </div>
    <p className="caution"><strong>적용 범위:</strong> 선택 기간은 연도별 표, 표본 요약, 결과 서술 및 추세 Figure에 적용된다. 집단 비교·전체 기술통계·상관관계·VIF는 빌드 시 전체 구축기간으로 산출된 정적 통계이므로 재계산되지 않는다.</p>
  </section>;
}

function Report({ data }) {
  const { summary, definitions, yearly, descriptive, comparison, within, pearson, vif, sampleAudit, sourceManifest, buildMetadata, figureData, figureManifest, coreDescriptive, pearsonCore, modelFree, docs = {}, supplementalErrors = {} } = data;
  const allYears = useMemo(() => safeRows(yearly).map((row) => Number(row.report_year)).filter(Number.isFinite).sort((a, b) => a - b), [yearly]);
  const minAvailableYear = allYears[0];
  const maxAvailableYear = allYears[allYears.length - 1];
  const defaultStart = allYears.includes(2020) ? 2020 : minAvailableYear;
  const defaultEnd = allYears.includes(2025) ? 2025 : maxAvailableYear;
  const [startYear, setStartYear] = useState(defaultStart);
  const [endYear, setEndYear] = useState(defaultEnd);
  const periodLabel = `${startYear}–${endYear}`;
  const buildPeriod = buildMetadata?.analysis_period || summary?.analysis_period || `${minAvailableYear}–${maxAvailableYear}`;
  const years = safeRows(yearly).filter((row) => Number(row.report_year) >= startYear && Number(row.report_year) <= endYear);
  const first = years[0] || {};
  const last = years[years.length - 1] || {};
  const selectedObservations = years.reduce((sum, row) => sum + (Number(row.firm_year_count) || 0), 0);
  const selectedAiDisclosures = years.reduce((sum, row) => sum + (Number(row.ai_disclosure_count) || 0), 0);
  const selectedAiRate = selectedObservations ? selectedAiDisclosures / selectedObservations : null;
  const aggregateFigures = safeRows(figureData?.aggregate).filter((row) => Number(row.report_year) >= startYear && Number(row.report_year) <= endYear);
  const withinFigures = safeRows(figureData?.within_change).filter((row) => Number(row.report_year) > startYear && Number(row.report_year) <= endYear);
  const groups = useMemo(() => [...new Set(definitions.map((item) => item.group))], [definitions]);
  const coreVariables = ["ai_disclosure", "ai_sentence_count", "whole_report_concreteness", "ai_concreteness", "past_tense_share", "present_tense_share", "future_tense_share", "lm_uncertainty_share", "passive_voice_sentence_share", "fog_index", "report_word_count"];
  const coreDefinitions = coreVariables.map((name) => definitions.find((item) => item.variable === name)).filter(Boolean);
  const yearlyRows = years.map((row) => ({ report_year: row.report_year, firm_year_count: formatInteger(row.firm_year_count), unique_company_count: formatInteger(row.unique_company_count), ai_disclosure_count: formatInteger(row.ai_disclosure_count), ai_disclosure_rate: formatPercent(row.ai_disclosure_rate) }));
  const resultRows = years.map((row) => ({ report_year: row.report_year, ai_disclosure_rate: formatPercent(row.ai_disclosure_rate), mean_ai_sentence_count_all: formatNumber(row.mean_ai_sentence_count_all, 3), mean_ai_sentence_count_disclosers: formatNumber(row.mean_ai_sentence_count_disclosers, 3), mean_whole_report_concreteness_all: formatNumber(row.mean_whole_report_concreteness_all, 3), mean_ai_concreteness_disclosers: formatNumber(row.mean_ai_concreteness_disclosers, 3), mean_present_tense_share_all: formatPercent(row.mean_present_tense_share_all, 2), mean_future_tense_share_all: formatPercent(row.mean_future_tense_share_all, 2), mean_lm_uncertainty_share_all: formatPercent(row.mean_lm_uncertainty_share_all, 2), mean_passive_voice_sentence_share_all: formatPercent(row.mean_passive_voice_sentence_share_all, 2), mean_fog_index_all: formatNumber(row.mean_fog_index_all, 3), mean_report_word_count_all: formatInteger(row.mean_report_word_count_all) }));
  const descriptiveRows = safeRows(descriptive).slice(0, 16).map((row) => ({ variable: row.variable, N: formatInteger(row.N), mean: formatNumber(row.mean, 3), standard_deviation: formatNumber(row.standard_deviation, 3), p25: formatNumber(row.p25, 3), median: formatNumber(row.median, 3), p75: formatNumber(row.p75, 3) }));
  const comparisonRows = safeRows(comparison).map((row) => ({ variable: row.variable, disclosure_N: formatInteger(row.disclosure_N), disclosure_mean: formatNumber(row.disclosure_mean, 3), non_disclosure_N: formatInteger(row.non_disclosure_N), non_disclosure_mean: formatNumber(row.non_disclosure_mean, 3), mean_difference: formatNumber(row.mean_difference, 3), standardized_mean_difference: formatNumber(row.standardized_mean_difference, 3), welch_t: formatNumber(row.welch_t, 3), welch_pvalue: formatP(row.welch_pvalue) }));
  const corrRows = safeRows(pearson).slice(0, 12).map((row) => ({ variable: row.variable, ai_disclosure: formatNumber(row.ai_disclosure, 3), ai_sentence_count: formatNumber(row.ai_sentence_count, 3), whole_report_concreteness: formatNumber(row.whole_report_concreteness, 3), lm_uncertainty_share: formatNumber(row.lm_uncertainty_share, 3), fog_index: formatNumber(row.fog_index, 3), report_word_count: formatNumber(row.report_word_count, 3) }));
  const vifRows = safeRows(vif).map((row) => ({ variable: row.variable, N: formatInteger(row.N), VIF: formatNumber(row.VIF, 3) }));
  const figureMeta = (id) => safeRows(figureManifest).find((item) => item.figure_id === id) || {};
  const figureError = supplementalErrors.figureData || supplementalErrors.figureManifest;
  const mainPeriod = () => { setStartYear(allYears.includes(2020) ? 2020 : minAvailableYear); setEndYear(allYears.includes(2025) ? 2025 : maxAvailableYear); };
  const fullPeriod = () => { setStartYear(minAvailableYear); setEndYear(maxAvailableYear); };

  return <main className="report-app">
    <aside className="toc" aria-label="연구보고서 목차"><div className="toc-brand"><strong>S&amp;P 500</strong><span>연구보고서</span></div><nav><a href="#title">표지</a><a href="#period-settings">기간 설정</a><a href="#abstract">초록</a><a href="#design">1. 연구설계</a><a href="#sample">2. 표본 구축</a><a href="#collection">3. 자료 수집</a><a href="#processing">4. 텍스트 처리</a><a href="#methods">5. 변수 측정</a><a href="#statistics">6. 통계 분석</a><a href="#results">7. 결과</a><a href="#discussion">8. 논의</a><a href="#limitations">9. 한계</a><a href="#reproducibility">10. 재현성</a><a href="#variables">부록 A. 변수 정의</a></nav><div className="toc-meta"><small>firm-year · {periodLabel}</small><br /><small>전체 {buildPeriod}</small></div></aside>
    <div className="report-main">
      <section className="title-page" id="title"><p className="kicker">S&amp;P 500 · Form 10-K · 기업-연도 패널</p><h1>S&amp;P 500<br />{periodLabel}년 S&amp;P 500 기업<br /><em>10-K 언어적 특성 분석</em></h1><p className="subtitle">AI 관련 공시, 어휘적 구체성, Loughran–McDonald 금융사전 및 Gunning Fog Index의 기술통계·상관관계와 model-free evidence</p><dl className="title-meta"><div><dt>표시기간</dt><dd>{periodLabel}</dd></div><div><dt>전체 구축기간</dt><dd>{buildPeriod}</dd></div><div><dt>분석단위</dt><dd>기업-연도</dd></div><div><dt>선택 관측치</dt><dd>{formatInteger(selectedObservations)}</dd></div></dl></section>

      <div id="period-settings"><PeriodControls availableYears={allYears} startYear={startYear} endYear={endYear} onStartYear={setStartYear} onEndYear={setEndYear} onMainPeriod={mainPeriod} onFullPeriod={fullPeriod} /></div>

      <Section id="abstract" number="초록" title="연구 요약" kicker="ABSTRACT / EXECUTIVE SUMMARY"><div className="abstract-box"><p>본 화면은 전체 {buildPeriod} 패널 중 {periodLabel}년을 선택하여 S&amp;P 500 기업 Form 10-K의 AI 관련 공시와 문서 언어 특성의 연도별 분포를 기술한다. 선택기간 표본은 {formatInteger(selectedObservations)} firm-year이며 AI 관련 문장이 확인된 관측치는 {formatInteger(selectedAiDisclosures)}건({formatPercent(selectedAiRate)})이다.</p><p>핵심 측정치는 AI 관련 문장 여부와 개수, Brysbaert 구체성, spaCy 기반 시제·수동태, Loughran–McDonald 금융 어휘, Gunning Fog Index 및 보고서 길이다.</p><p className="caution"><strong>해석 범위:</strong> AI 관련 변수는 실제 실제 AI 도입이 아니라 10-K에 나타난 <code>문서에서 관찰된 AI 관련 공시의 대리 측정치</code>이다. 평균 차이와 상관관계는 인과효과를 의미하지 않는다.</p></div><SourceNote source="web/public/data/yearly-statistics.json" n={selectedObservations} condition={`${periodLabel} 선택기간`} /></Section>

      <Section id="design" number="1" title="연구설계" kicker="RESEARCH DESIGN"><p>관측 단위는 기업 식별자와 보고연도 조합인 <code>기업-연도</code>이다. 전체 구축 패널은 {buildPeriod}이며 화면의 기본 메인 기간은 2020–2025이다.</p><div className="two-column"><div><h3>연구 질문</h3><p>선택한 {periodLabel}년 동안 AI 관련 직접 공시가 얼마나 확산되었고, 언어 특성이 어떻게 변화했는지 기술한다.</p></div><div><h3>AI 관련 공시 대리변수</h3><p><code>ai_disclosure</code>는 기존 AI matcher가 추출한 직접 문장이 하나 이상일 때 1이며 실제 기술 도입을 직접 측정하지 않는다.</p></div></div></Section>

      <Section id="sample" number="2" title="표본 구축" kicker="SAMPLE CONSTRUCTION"><p>연도별 S&amp;P 500 구성 manifest와 SEC CIK를 사용해 대상 기업을 확정하고 정확한 <code>reportDate</code> 연도의 Form 10-K만 유지했다.</p><MetricTable caption={`표 1. ${periodLabel} 연도별 표본 구성`} rows={yearlyRows} columns={[["report_year", "보고연도"], ["firm_year_count", "firm-year 수"], ["unique_company_count", "고유 기업 수"], ["ai_disclosure_count", "AI 공시 수"], ["ai_disclosure_rate", "AI 공시 비율"]]} source="web/public/data/yearly-statistics.json" condition={`${periodLabel} 선택기간`} /><div className="audit-grid"><div><strong>선택기간 firm-year</strong><span>{formatInteger(selectedObservations)}건</span></div><div><strong>선택기간 AI 공시</strong><span>{formatInteger(selectedAiDisclosures)}건</span></div><div><strong>중복 company-year</strong><span>{formatInteger(sampleAudit?.duplicate_company_year)}건</span></div><div><strong>중복 accession</strong><span>{formatInteger(sampleAudit?.duplicate_accession)}건</span></div></div></Section>

      <Section id="collection" number="3" title="자료 수집" kicker="DATA COLLECTION"><div className="method-list"><p><strong>SEC filing 선정.</strong> 정확한 Form <code>10-K</code>, report date 연도, 유일 accession과 primary document를 확인했다.</p><p><strong>원문 보관.</strong> 파일 크기·SHA-256을 manifest에 기록하고 원본 HTML은 Google Drive에 보관한다.</p><p><strong>무결성.</strong> source manifest에는 원자료 경로, SHA-256, 생성 script, Git commit과 생성 시각이 연결되어 있다.</p></div><SourceNote source="web/public/data/source-manifest.json" /></Section>

      <Section id="processing" number="4" title="텍스트 처리" kicker="TEXT PROCESSING"><div className="two-column"><div><h3>HTML 정제</h3><p><code>scripts/extract_10k_analysis_text.py</code>가 script/style과 hidden inline XBRL metadata를 제거하고 분석 본문을 생성한다.</p></div><div><h3>AI 관련 문장</h3><p>기존 AI term list와 case-insensitive word-boundary matcher를 사용하며 여러 term이 한 문장에 있어도 문장은 한 번 센다.</p></div></div><div className="flow"><span>SEC metadata</span><b>→</b><span>primary HTML</span><b>→</b><span>정제 본문</span><b>→</b><span>문장</span><b>→</b><span>firm-year 변수</span></div></Section>

      <span id="methods" className="anchor-alias" aria-hidden="true" /><Section id="measurement" number="5" title="변수 측정" kicker="VARIABLE MEASUREMENT"><p>핵심 변수는 실제 <code>variable-definitions.json</code>에서 읽어 수식·분자·분모·결측·source metadata를 표시한다.</p><div className="measurement-index">{groups.map((group) => <span key={group}>{group} · {definitions.filter((item) => item.group === group).length}개</span>)}</div><div className="variable-feature-grid">{coreDefinitions.map((item) => <VariableBlock key={item.variable} item={item} />)}</div></Section>

      <Section id="statistics" number="6" title="통계 분석" kicker="STATISTICAL ANALYSIS"><div className="analysis-methods"><div><h3>선택기간 적용</h3><p>연도별 표, 표본 요약, 결과 서술과 추세 Figure는 {periodLabel}로 필터링한다.</p></div><div><h3>전체기간 고정</h3><p>전체 기술통계, AI 공시·미공시 비교, Pearson 상관과 VIF는 {buildPeriod} 빌드 산출물이다.</p></div><div><h3>변화</h3><p>동일 기업 변화 Figure는 선택기간 내부의 실제 연속연도 pair만 표시한다.</p></div><div><h3>해석</h3><p>정적 통계를 선택기간 통계로 오인하지 않도록 각 표의 조건에 구축기간을 표시한다.</p></div></div></Section>

      <Section id="results" number="7" title="분석 결과" kicker="RESULTS"><h3>7.1 선택기간 표본 특성 및 AI 공시 확산</h3><p>{first.report_year || "-"}년 AI 공시 비율은 {formatPercent(first.ai_disclosure_rate)}이고 {last.report_year || "-"}년에는 {formatPercent(last.ai_disclosure_rate)}이다.</p>{supplementalErrors.yearly ? <SupplementalError source="/data/yearly-statistics.json" /> : <MetricTable caption={`표 2. ${periodLabel} 연도별 핵심 기술통계`} rows={resultRows} columns={[["report_year", "보고연도"], ["ai_disclosure_rate", "AI 공시 비율"], ["mean_ai_sentence_count_all", "AI 문장 평균(전체)"], ["mean_ai_sentence_count_disclosers", "AI 문장 평균(공시)"], ["mean_whole_report_concreteness_all", "전체 보고서 구체성"], ["mean_ai_concreteness_disclosers", "AI 구체성(공시)"], ["mean_present_tense_share_all", "현재 시제"], ["mean_future_tense_share_all", "미래 표지"], ["mean_lm_uncertainty_share_all", "Loughran–McDonald 불확실성 어휘 비율"], ["mean_passive_voice_sentence_share_all", "수동태"], ["mean_fog_index_all", "Fog Index"], ["mean_report_word_count_all", "보고서 단어 수"]]} source="web/public/data/yearly-statistics.json" condition={`${periodLabel}; AI 수준 값은 공시 firm-year 조건부`} />}
      <h3>7.2 전체 구축기간 고정 통계</h3><p className="caution">아래 표와 효과크기 Figure는 {periodLabel}로 재산출된 값이 아니라 빌드 시점의 전체 {buildPeriod} 표본 통계이다.</p>{supplementalErrors.descriptive ? <SupplementalError source="/data/descriptive-statistics.json" /> : <MetricTable caption={`표 3. 전체 ${buildPeriod} 표본 기술통계`} rows={descriptiveRows} columns={[["variable", "변수"], ["N", "N"], ["mean", "평균"], ["standard_deviation", "표준편차"], ["p25", "제1사분위수"], ["median", "중앙값"], ["p75", "제3사분위수"]]} source="web/public/data/descriptive-statistics.json" condition={`전체 구축기간 ${buildPeriod}`} />}
      {supplementalErrors.comparison ? <SupplementalError source="/data/disclosure-comparison.json" /> : <MetricTable caption={`표 4. 전체 ${buildPeriod} AI 공시 여부별 단순 비교`} rows={comparisonRows} columns={[["variable", "변수"], ["disclosure_N", "공시 N"], ["disclosure_mean", "공시 평균"], ["non_disclosure_N", "미공시 N"], ["non_disclosure_mean", "미공시 평균"], ["mean_difference", "평균 차이"], ["standardized_mean_difference", "표준화 차이"], ["welch_t", "Welch t"], ["welch_pvalue", "p-value"]]} source="web/public/data/disclosure-comparison.json" condition={`전체 구축기간 ${buildPeriod}; 단순 집단 비교`} />}
      {supplementalErrors.pearson ? <SupplementalError source="/data/pearson-correlations.json" /> : <MetricTable caption={`표 5. 전체 ${buildPeriod} Pearson 상관관계 일부`} rows={corrRows} columns={[["variable", "행 변수"], ["ai_disclosure", "AI 공시"], ["ai_sentence_count", "AI 문장 수"], ["whole_report_concreteness", "전체 구체성"], ["lm_uncertainty_share", "Loughran–McDonald 불확실성 어휘 비율"], ["fog_index", "Fog Index"], ["report_word_count", "보고서 단어 수"]]} source="web/public/data/pearson-correlations.json" condition={`전체 구축기간 ${buildPeriod}; pairwise complete`} />}
      {supplementalErrors.vif ? <SupplementalError source="/data/vif.json" /> : <MetricTable caption={`표 6. 전체 ${buildPeriod} VIF 진단`} rows={vifRows} columns={[["variable", "변수"], ["N", "N"], ["VIF", "VIF"]]} source="web/public/data/vif.json" condition={`전체 구축기간 ${buildPeriod}`} />}
      {figureError ? <SupplementalError source="/data/figure-data.json" /> : <div className="figure-grid"><FigureShell id="figure-01" number="Figure 1" title={`${periodLabel} AI 공시 확산`} introduction="선택기간의 AI 관련 문장 존재 firm-year 비율을 보여준다." caption="전체 firm-year를 분모로 사용한다." condition={`${periodLabel} 전체 firm-year`} source={figureMeta("figure-01").source_file} sourceCsv={dataUrl("downloads/figure-aggregate-data.csv")}><LineFigure id="figure-01-svg" rows={aggregateFigures} keys={["ai_disclosure_rate"]} labels={["AI 공시 비율"]} percent ariaLabel={`${periodLabel} 연도별 AI 공시 비율`} /></FigureShell><FigureShell id="figure-02" number="Figure 2" title={`${periodLabel} AI 관련 문장 수`} introduction="전체 표본의 0 포함 평균과 AI 공시기업 조건부 평균을 분리한다." caption="실제 실제 AI 도입이 아니라 문서에서 관찰된 AI 관련 공시의 대리 측정치이다." condition={periodLabel} source={figureMeta("figure-02").source_file} sourceCsv={dataUrl("downloads/figure-aggregate-data.csv")}><LineFigure id="figure-02-svg" rows={aggregateFigures} keys={["mean_ai_sentence_count_all", "mean_ai_sentence_count_disclosers"]} labels={["전체 평균(0 포함)", "공시기업 평균"]} ariaLabel={`${periodLabel} AI 관련 문장 수`} /></FigureShell><FigureShell id="figure-03" number="Figure 3" title={`${periodLabel} 구체성 추이`} introduction="전체 보고서와 AI 관련 문장의 평균 구체성을 비교한다." caption="AI 구체성은 AI 공시 firm-year 조건부이다." condition={periodLabel} source={figureMeta("figure-03").source_file} sourceCsv={dataUrl("downloads/figure-aggregate-data.csv")}><LineFigure id="figure-03-svg" rows={aggregateFigures} keys={["whole_report_concreteness", "ai_concreteness"]} labels={["전체 보고서", "AI 관련 문장"]} ariaLabel={`${periodLabel} 구체성`} /></FigureShell><FigureShell id="figure-04" number="Figure 4" title={`${periodLabel} 시제 구성 변화`} introduction="과거·현재·미래 표지의 구성을 표시한다." caption="미래 표지는 will·shall·'ll/’ll이며 미래지향 언어 전체를 의미하지 않는다." condition={periodLabel} source={figureMeta("figure-04").source_file} sourceCsv={dataUrl("downloads/figure-aggregate-data.csv")}><LineFigure id="figure-04-svg" rows={aggregateFigures} keys={["past_tense_share", "present_tense_share", "future_tense_share"]} labels={["과거", "현재", "미래 표지"]} percent ariaLabel={`${periodLabel} 시제 비율`} /></FigureShell><FigureShell id="figure-05" number="Figure 5" title={`${periodLabel} AI 문장 LM 언어 추이`} introduction="AI 관련 문장에서 positive·negative·uncertainty 상대 빈도를 비교한다." caption="Loughran–McDonald 금융사전 기반이다." condition={`${periodLabel} AI 공시 firm-year`} source={figureMeta("figure-05").source_file} sourceCsv={dataUrl("downloads/figure-aggregate-data.csv")}><LineFigure id="figure-05-svg" rows={aggregateFigures} keys={["ai_lm_positive_share", "ai_lm_negative_share", "ai_lm_uncertainty_share"]} labels={["긍정", "부정", "불확실성"]} percent ariaLabel={`${periodLabel} AI 문장 LM 범주`} /></FigureShell><FigureShell id="figure-06" number="Figure 6" title={`전체 ${buildPeriod} AI 공시·미공시 표준화 평균 차이`} introduction="전체 구축기간의 표준화 평균 차이를 표시한다." caption="선택기간에 따라 재계산되지 않는 전체기간 단순 집단 비교이다." condition={`전체 ${buildPeriod}`} source={figureMeta("figure-06").source_file} sourceCsv={dataUrl("downloads/disclosure-comparison.csv")}><EffectSizeFigure id="figure-06-svg" rows={figureData?.comparison} ariaLabel={`전체 ${buildPeriod} AI 공시 미공시 표준화 평균 차이`} /></FigureShell><FigureShell id="figure-07" number="Figure 7" title={`${periodLabel} 동일 기업 내 전년 대비 변화`} introduction="선택기간 내부의 실제 연속연도 pair가 있는 기업 평균 변화를 표시한다." caption="각 변수의 원래 단위를 유지하며 0은 변화 없음이다." condition={`${periodLabel} 내부 연속연도 pair`} source={figureMeta("figure-07").source_file} sourceCsv={dataUrl("downloads/figure-within-firm-change-data.csv")}><WithinChangeFigure id="figure-07-svg" rows={withinFigures} ariaLabel={`${periodLabel} 동일 기업 내 전년 대비 평균 변화`} /></FigureShell></div>}</Section>

      <CoreTables coreDescriptive={coreDescriptive} pearsonCore={pearsonCore} modelFree={modelFree} figureData={figureData} buildPeriod={buildPeriod} />
      <Section id="discussion" number="8" title="논의" kicker="DISCUSSION"><p>기간 설정은 전체 historical 패널을 유지하면서 2020–2025를 메인 분석창으로 제공한다. 초기 연도와 후기 연도의 패턴을 동일한 화면에서 비교할 수 있지만 선택기간 변경 자체가 정적 통계의 재추정을 의미하지는 않는다.</p></Section>
      <Section id="limitations" number="9" title="한계" kicker="LIMITATIONS">{supplementalErrors.limitations ? <SupplementalError source="/docs/research-dashboard-limitations.md" /> : <MarkdownLite value={docs.limitations} />}<SourceNote source="web/docs/research-dashboard-limitations.md" /></Section>
      <Section id="reproducibility" number="10" title="재현성" kicker="REPRODUCIBILITY">{supplementalErrors.reproducibility ? <SupplementalError source="/docs/research-dashboard-reproducibility.md" /> : <MarkdownLite value={docs.reproducibility} />}<div className="download-grid"><a href={dataUrl("data/analysis-summary.json")} download>분석 요약 JSON</a><a href={dataUrl("data/variable-definitions.json")} download>변수 정의 JSON</a><a href={dataUrl("downloads/table-variable-definitions.csv")} download>변수 정의 CSV</a><a href={dataUrl("data/source-manifest.json")} download>Source manifest</a></div><SourceNote source="web/public/data/source-manifest.json" /></Section>
      <span id="variables" className="anchor-alias" aria-hidden="true" /><Section id="appendix" number="부록 A" title="변수 정의" kicker="APPENDIX A · VARIABLE DEFINITIONS"><p>총 {formatInteger(definitions.length)}개 변수의 상세 정의를 제공한다.</p><div className="appendix-tools"><input placeholder="변수명 검색" aria-label="변수명 검색" onChange={(event) => { const value = event.target.value.toLowerCase(); document.querySelectorAll(".variable-block").forEach((node) => { node.hidden = value && !node.textContent.toLowerCase().includes(value); }); }} /></div><div className="appendix-list">{definitions.map((item) => <VariableBlock key={item.variable} item={item} />)}</div><SourceNote source="web/public/data/variable-definitions.json" n={definitions.length} /></Section>
      <footer className="report-footer">기본 표시기간 {defaultStart}–{defaultEnd} · 전체 구축기간 {buildPeriod}</footer>
    </div>
  </main>;
}

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    const loadText = async (filename) => {
      const response = await fetch(dataUrl(`docs/${filename}`));
      if (!response.ok) throw new Error(`${filename}: ${response.status}`);
      return response.text();
    };
    Promise.all(Object.entries(CORE_FILES).map(async ([key, filename]) => [key, await loadJson(filename)]))
      .then(async (coreEntries) => {
        const optionalEntries = [...Object.entries(SUPPLEMENTAL_FILES).map(([key, filename]) => [key, loadJson(filename)]), ...DOCUMENTS.map(([key, filename]) => [key, loadText(filename)])];
        const settled = await Promise.allSettled(optionalEntries.map(([, promise]) => promise));
        const supplemental = {};
        const supplementalErrors = {};
        optionalEntries.forEach(([key], index) => {
          if (settled[index].status === "fulfilled") supplemental[key] = settled[index].value;
          else supplementalErrors[key] = settled[index].reason?.message || "request failed";
        });
        setData({ ...Object.fromEntries(coreEntries), ...supplemental, docs: { methodology: supplemental.methodology, results: supplemental.results, limitations: supplemental.limitations, reproducibility: supplemental.reproducibility }, supplementalErrors });
      })
      .catch((reason) => setError(reason.message));
  }, []);
  if (error) return <main className="loading-shell"><h1>분석 보고서를 불러오지 못했습니다.</h1><p>{error}</p><button type="button" onClick={() => window.location.reload()}>다시 시도</button></main>;
  if (!data) return <main className="loading-shell"><p>연구보고서와 분석 산출물을 불러오는 중입니다.</p></main>;
  return <Report data={data} />;
}
