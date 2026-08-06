import { useEffect, useState } from "react";
import { EffectSizeFigure, FigureShell, GroupMeanFigure, LineFigure, PanelABFigure, WithinChangeFigure } from "./Figures";
import { PUBLIC_VARIABLE_DEFINITIONS, RESEARCH_VARIABLES, VARIABLE_LABELS, labelFor, unitFor } from "./variableLabels";

const DATA_FILES = {
  definitions: "variable-definitions.json",
  yearly: "yearly-statistics.json",
  figureData: "figure-data.json",
  coreDescriptive: "core-descriptive-statistics.json",
  pearsonCore: "pearson-core.json",
  modelFree: "model-free-comparison.json",
};

const PERIOD_START = 2020;
const PERIOD_END = 2025;
const PERIOD_LABEL = "2020–2025";

const safeRows = (value) => Array.isArray(value) ? value : [];
const dataUrl = (path) => `${import.meta.env.BASE_URL}${path.replace(/^\//, "")}`;
const formatInteger = (value) => value === null || value === undefined || Number.isNaN(Number(value)) ? "-" : Math.round(Number(value)).toLocaleString("ko-KR");
const formatNumber = (value, digits = 3) => value === null || value === undefined || Number.isNaN(Number(value)) ? "-" : Number(value).toLocaleString("ko-KR", { maximumFractionDigits: digits });
const formatPercent = (value, digits = 1) => value === null || value === undefined || Number.isNaN(Number(value)) ? "-" : `${(Number(value) * 100).toFixed(digits)}%`;
const formatP = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  const number = Number(value);
  return number < 0.001 ? "p < .001" : `p = ${number.toFixed(4).replace(/^0\./, ".")}`;
};
const formatStatistic = (variable, value, digits = 3) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  const unit = unitFor(variable);
  if (unit === "%") return formatPercent(value, 2);
  if (unit === "단어") return formatInteger(value);
  return formatNumber(value, digits);
};

async function loadJson(filename) {
  const response = await fetch(dataUrl(`data/${filename}`));
  if (!response.ok) throw new Error(`${filename}: ${response.status}`);
  return response.json();
}

function Section({ id, number, title, kicker, children }) {
  return <section className="report-section" id={id}><div className="section-heading"><span className="section-number">{number}</span><div><p className="kicker">{kicker}</p><h2>{title}</h2></div></div>{children}</section>;
}

function MetricTable({ rows, columns, caption, note }) {
  return <div className="table-card"><div className="table-scroll"><table className="paper-table"><caption>{caption}</caption><thead><tr>{columns.map(([key, label]) => <th key={key} scope="col">{label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.variable || row.report_year || "row"}-${index}`}>{columns.map(([key], columnIndex) => columnIndex === 0 ? <th key={key} scope="row">{row[key] ?? "-"}</th> : <td key={key}>{row[key] ?? "-"}</td>)}</tr>)}</tbody></table></div>{note && <p className="table-note">{note}</p>}</div>;
}

function VariableBlock({ variable }) {
  const item = PUBLIC_VARIABLE_DEFINITIONS[variable];
  if (!item) return null;
  return <details className="variable-block" data-variable-definition={variable}><summary><strong>{labelFor(variable)}</strong><em>{item.unit}</em></summary><div className="variable-detail"><p><strong>개념적 정의</strong>{item.concept}</p><p><strong>조작적 정의</strong>{item.operation}</p><div className="formula-block"><h4>계산식</h4><div className="formula">{item.formula}</div></div><div className="definition-grid"><p><strong>분자</strong>{item.numerator}</p><p><strong>분모</strong>{item.denominator}</p><p><strong>단위</strong>{item.unit}</p><p><strong>조건부 표본</strong>{item.sample}</p><p className="definition-wide"><strong>결측 및 0 처리</strong>{item.missingZero}</p></div></div></details>;
}

const heatColor = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "#f1f3f2";
  const number = Math.max(-1, Math.min(1, Number(value)));
  const strength = Math.abs(number);
  const neutral = [247, 248, 246];
  const target = number < 0 ? [151, 70, 91] : [22, 124, 128];
  return `rgb(${neutral.map((channel, index) => Math.round(channel + (target[index] - channel) * strength)).join(", ")})`;
};

function CorrelationHeatmap({ data }) {
  const variables = safeRows(data?.variables).map((item) => item.variable);
  const rows = safeRows(data?.rows);
  return <div className="heatmap-card"><h3>표 3. Pearson 상관관계 히트맵</h3><p className="table-note">{PERIOD_LABEL}; N=2,829 기업-연도. 각 셀은 상관계수이며, 보조 설명에 유효 관측치 수와 p-value를 제공한다.</p><div className="correlation-heatmap-scroll" tabIndex="0" aria-label="Pearson 상관관계 히트맵 스크롤 영역"><div className="correlation-heatmap" role="grid" aria-label={`${PERIOD_LABEL} 핵심 연구변수 Pearson 상관계수`} style={{ gridTemplateColumns: `minmax(190px, 240px) repeat(${variables.length}, 72px)` }}><div className="heatmap-corner" aria-hidden="true" />{variables.map((variable) => <div key={`column-${variable}`} className="heatmap-column-label" role="columnheader"><span>{labelFor(variable)}</span></div>)}{rows.map((row) => <div className="heatmap-row" role="row" key={row.variable}><div className="heatmap-row-label" role="rowheader">{labelFor(row.variable)}</div>{safeRows(row.cells).map((cell) => { const value = cell.correlation; const coefficient = value === null || value === undefined ? "-" : Number(value).toFixed(3); const detail = `${labelFor(row.variable)}와 ${labelFor(cell.variable)}: 상관계수 ${coefficient}, 유효 관측치 ${formatInteger(cell.pairwise_N)}건, ${formatP(cell.pvalue)}`; return <div key={`${row.variable}-${cell.variable}`} className="heatmap-cell" role="gridcell" data-correlation-cell style={{ backgroundColor: heatColor(value), color: Math.abs(Number(value)) >= 0.58 ? "#fff" : "#23313b" }} aria-label={detail} title={detail}><span>{coefficient}</span></div>; })}</div>)}</div></div><div className="heatmap-scale" aria-label="상관계수 색상 범례"><span className="negative">−1 음의 상관</span><span className="neutral">0</span><span className="positive">+1 양의 상관</span></div></div>;
}

function Report({ data }) {
  const { definitions, yearly, figureData, coreDescriptive, pearsonCore, modelFree } = data;
  const years = safeRows(yearly).filter((row) => Number(row.report_year) >= PERIOD_START && Number(row.report_year) <= PERIOD_END);
  const aggregateFigures = safeRows(figureData?.aggregate).filter((row) => Number(row.report_year) >= PERIOD_START && Number(row.report_year) <= PERIOD_END);
  const groupFigures = safeRows(figureData?.ai_group).filter((row) => Number(row.report_year) >= PERIOD_START && Number(row.report_year) <= PERIOD_END);
  const withinFigures = safeRows(figureData?.within_change).filter((row) => Number(row.report_year) > PERIOD_START && Number(row.report_year) <= PERIOD_END);
  const first = years[0] || {};
  const last = years[years.length - 1] || {};
  const observations = years.reduce((sum, row) => sum + (Number(row.firm_year_count) || 0), 0);
  const disclosures = years.reduce((sum, row) => sum + (Number(row.ai_disclosure_count) || 0), 0);
  const disclosureRate = observations ? disclosures / observations : null;
  const availableDefinitions = new Set(safeRows(definitions).map((item) => item.variable));
  const researchDefinitions = RESEARCH_VARIABLES.filter((variable) => availableDefinitions.has(variable));
  const yearlyRows = years.map((row) => ({
    report_year: row.report_year,
    firm_year_count: `${formatInteger(row.firm_year_count)}건`,
    unique_company_count: `${formatInteger(row.unique_company_count)}개`,
    ai_disclosure_count: `${formatInteger(row.ai_disclosure_count)}건`,
    ai_disclosure_rate: formatPercent(row.ai_disclosure_rate),
    mean_report_word_count_all: `${formatInteger(row.mean_report_word_count_all)}단어`,
  }));
  const descriptiveRows = safeRows(coreDescriptive).map((row) => ({
    variable: labelFor(row.variable),
    N: `${formatInteger(row.N)}건`,
    mean: formatStatistic(row.variable, row.mean),
    sd: formatStatistic(row.variable, row.standard_deviation),
    q1: formatStatistic(row.variable, row.p25),
    median: formatStatistic(row.variable, row.median),
    q3: formatStatistic(row.variable, row.p75),
  }));
  const primaryRows = safeRows(modelFree?.primary).map((row) => ({
    variable: labelFor(row.variable),
    disclosure_N: `${formatInteger(row.disclosure_N)}건`,
    disclosure_mean: formatStatistic(row.variable, row.disclosure_mean),
    non_disclosure_N: `${formatInteger(row.non_disclosure_N)}건`,
    non_disclosure_mean: formatStatistic(row.variable, row.non_disclosure_mean),
    mean_difference: formatStatistic(row.variable, row.mean_difference),
    welch_t: formatNumber(row.welch_t),
    welch_pvalue: formatP(row.welch_pvalue),
  }));
  const secondaryRows = safeRows(modelFree?.secondary).map((row) => ({
    variable: labelFor(row.variable),
    q1_mean: formatStatistic(row.variable, row.q1_mean),
    q4_mean: formatStatistic(row.variable, row.q4_mean),
    mean_difference: formatStatistic(row.variable, row.mean_difference),
    welch_t: formatNumber(row.welch_t),
    welch_pvalue: formatP(row.welch_pvalue),
    wilcoxon_statistic: formatNumber(row.wilcoxon_statistic),
    wilcoxon_pvalue: formatP(row.wilcoxon_pvalue),
  }));
  const effectRows = safeRows(figureData?.comparison).filter((row) => VARIABLE_LABELS[row.variable]);
  const effectVariables = [...new Set(effectRows.map((row) => row.variable))];

  return <main className="report-app">
    <aside className="toc" aria-label="연구보고서 목차"><div className="toc-brand"><strong>S&amp;P 500</strong><span>10-K 언어 분석 보고서</span></div><nav><a href="#title">표지</a><a href="#abstract">연구 요약</a><a href="#design">1. 연구설계</a><a href="#sample">2. 표본 구축</a><a href="#collection">3. 자료 수집</a><a href="#processing">4. 텍스트 처리</a><a href="#definitions">5. 변수 정의</a><a href="#statistics">6. 통계 분석</a><a href="#results">7. 분석 결과</a><a href="#discussion">8. 논의</a><a href="#limitations">9. 한계</a></nav></aside>
    <div className="report-main">
      <section className="title-page" id="title"><p className="kicker">S&amp;P 500 · Form 10-K · 기업-연도 패널</p><h1>S&amp;P 500<br />2020–2025년 S&amp;P 500 기업<br /><em>10-K 언어적 특성 분석</em></h1><p className="subtitle">AI 관련 공시, 어휘적 구체성, Loughran–McDonald 금융사전 및 Gunning Fog Index의 기술통계·상관관계와 model-free evidence</p><dl className="title-meta"><div><dt>보고기간</dt><dd>2020–2025년</dd></div><div><dt>분석단위</dt><dd>기업-연도</dd></div><div><dt>관측치</dt><dd>{formatInteger(observations)}건</dd></div></dl></section>

      <Section id="abstract" number="요약" title="연구 요약" kicker="ABSTRACT"><div className="abstract-box"><p>이 보고서는 2020–2025년 S&amp;P 500 기업의 Form 10-K에서 관찰된 AI 관련 공시와 언어적 특성을 기술한다. 분석표본은 {formatInteger(observations)}개 기업-연도이며, AI 관련 공시가 확인된 관측치는 {formatInteger(disclosures)}건({formatPercent(disclosureRate)})이다.</p><p>핵심 변수는 AI 관련 공시 여부와 문장 수, 어휘적 구체성, 시제·수동태, Loughran–McDonald 금융 어휘, Gunning Fog Index와 보고서 길이이다.</p><p className="caution"><strong>해석 범위:</strong> AI 관련 공시는 실제 AI 도입을 직접 측정하지 않는다. 기술통계, 상관관계와 단순 집단 비교는 인과효과를 의미하지 않는다.</p></div></Section>

      <Section id="design" number="1" title="연구설계" kicker="RESEARCH DESIGN"><p>관측 단위는 기업과 보고연도의 조합인 기업-연도이다. 모든 본문 서술, 표와 Figure는 2020–2025년 표본을 사용한다.</p><div className="two-column"><div><h3>연구 질문</h3><p>AI 관련 공시는 2020–2025년 동안 어떻게 변화했으며, 공시 여부에 따라 보고서의 언어적 특성은 어떻게 다른가?</p></div><div><h3>분석 범위</h3><p>연도별 기술통계, Pearson 상관관계와 통제변수 없는 평균 비교를 제시한다. 실제 AI 도입이나 인과효과는 분석 대상이 아니다.</p></div></div></Section>

      <Section id="sample" number="2" title="표본 구축" kicker="SAMPLE CONSTRUCTION"><p>연도별 S&amp;P 500 구성기업을 확정하고 기업별 보고연도에 해당하는 Form 10-K를 연결했다. 수정신고서는 제외하고 동일 기업의 복수 주식종류는 기업 단위로 통합했다.</p><MetricTable caption="표 1. 2020–2025년 연도별 표본 구성" rows={yearlyRows} columns={[["report_year", "보고연도"], ["firm_year_count", "기업-연도 수"], ["unique_company_count", "고유 기업 수"], ["ai_disclosure_count", "AI 관련 공시 수"], ["ai_disclosure_rate", "AI 관련 공시 비율"], ["mean_report_word_count_all", "평균 보고서 단어 수"]]} note="2020–2025년 기업-연도 표본. 비율은 각 연도의 기업-연도 수를 분모로 계산한다." /><div className="audit-grid"><div><strong>전체 관측치</strong><span>{formatInteger(observations)}건</span></div><div><strong>AI 관련 공시</strong><span>{formatInteger(disclosures)}건</span></div><div><strong>AI 관련 공시 비율</strong><span>{formatPercent(disclosureRate)}</span></div><div><strong>최종 보고연도</strong><span>{last.report_year || "-"}년</span></div></div></Section>

      <Section id="collection" number="3" title="자료 수집" kicker="DATA COLLECTION"><div className="method-list"><p><strong>S&amp;P 500 구성기업.</strong> 현재 구성목록과 선택된 변경 이력을 역적용하고 역사 구성자료로 기준일별 기업 집합을 확인했다.</p><p><strong>Form 10-K.</strong> 연도별 구성기업에 해당하는 보고서를 SEC 공시자료에서 연결하고, 수정신고서는 분석에서 제외했다.</p><p><strong>분석 본문.</strong> 원문에서 언어 분석에 필요한 본문을 정제하되 원문과 정제 본문의 연결관계는 내부 자료에 보존했다.</p></div></Section>

      <Section id="processing" number="4" title="텍스트 처리" kicker="TEXT PROCESSING"><div className="two-column"><div><h3>본문 정제</h3><p>화면에 표시되지 않는 구조정보와 분석에서 제외할 영역을 제거한 뒤 문장과 단어 단위의 분석 본문을 구성했다.</p></div><div><h3>AI 관련 문장</h3><p>AI 관련 표현이 포함된 문장을 식별하고, 한 문장에 여러 관련 표현이 있어도 해당 문장은 한 번만 센다.</p></div></div><div className="flow"><span>Form 10-K</span><b>→</b><span>분석 본문</span><b>→</b><span>문장과 단어</span><b>→</b><span>기업-연도 변수</span></div></Section>

      <Section id="definitions" number="5" title="변수 정의" kicker="VARIABLE DEFINITIONS"><p>논문 독자가 핵심 변수의 의미와 계산 방식을 확인할 수 있도록 개념, 조작적 정의, 계산식, 분자·분모, 단위와 결측 처리를 제시한다.</p><div className="variable-feature-grid">{researchDefinitions.map((variable) => <VariableBlock key={variable} variable={variable} />)}</div></Section>

      <Section id="statistics" number="6" title="통계 분석" kicker="STATISTICAL ANALYSIS"><div className="analysis-methods"><div><h3>기술통계</h3><p>변수별 유효 관측치 수, 평균, 표준편차, 사분위수와 중앙값을 제시한다.</p></div><div><h3>Pearson 상관관계</h3><p>동일한 핵심 연구변수의 정사각형 상관행렬을 계산하고 변수 쌍별 유효 관측치 수와 p-value를 유지한다.</p></div><div><h3>AI 관련 공시 비교</h3><p>AI 관련 공시가 있는 기업-연도와 없는 기업-연도의 평균을 비교하고 Welch 검정 결과를 제시한다.</p></div><div><h3>보고서 길이 비교</h3><p>2020–2025년 전체 표본에서 로그 보고서 단어 수의 하위·상위 사분위를 한 번 분류해 비교한다.</p></div></div></Section>

      <Section id="results" number="7" title="분석 결과" kicker="RESULTS"><h3>7.1 주요 변수 기술통계</h3><MetricTable caption="표 2. 2020–2025년 주요 변수 기술통계" rows={descriptiveRows} columns={[["variable", "변수"], ["N", "유효 관측치"], ["mean", "평균"], ["sd", "표준편차"], ["q1", "제1사분위수"], ["median", "중앙값"], ["q3", "제3사분위수"]]} note="2020–2025년; 전체 표본 N=2,829 기업-연도. 조건부 변수는 변수별 유효 관측치 수가 다르다." />
      <h3>7.2 연도별 추이</h3><p>{first.report_year || "2020"}년 AI 관련 공시 비율은 {formatPercent(first.ai_disclosure_rate)}였고 {last.report_year || "2025"}년에는 {formatPercent(last.ai_disclosure_rate)}였다.</p><div className="figure-grid">
        <FigureShell id="figure-01" number="Figure 1" title="연도별 AI 관련 공시와 보고서 길이" introduction="AI 관련 공시 비율과 평균 보고서 단어 수를 서로 다른 세로축의 두 패널로 표시한다." caption="공통 시간추세를 인과관계로 해석하지 않는다." condition="2020–2025년 전체 기업-연도" variables={["ai_disclosure_rate", "report_word_count"]}><PanelABFigure id="figure-01-svg" rows={aggregateFigures} ariaLabel="2020–2025년 AI 관련 공시 비율과 평균 보고서 단어 수" /></FigureShell>
        <FigureShell id="figure-02" number="Figure 2" title="연도별 AI 관련 문장 수" introduction="전체 표본의 0 포함 평균과 AI 관련 공시 기업의 조건부 평균을 비교한다." caption="문서에서 관찰된 AI 관련 공시의 문장 수이며 실제 AI 도입을 뜻하지 않는다." condition="2020–2025년 기업-연도" variables={["mean_ai_sentence_count_all", "mean_ai_sentence_count_disclosers"]}><LineFigure id="figure-02-svg" rows={aggregateFigures} keys={["mean_ai_sentence_count_all", "mean_ai_sentence_count_disclosers"]} ariaLabel="2020–2025년 AI 관련 문장 수" /></FigureShell>
        <FigureShell id="figure-03" number="Figure 3" title="연도별 어휘적 구체성" introduction="전체 보고서와 AI 관련 문장의 평균 구체성을 비교한다." caption="AI 관련 문장 구체성은 해당 문장과 유효 매칭 단어가 있는 조건부 표본에서 정의된다." condition="2020–2025년 기업-연도" variables={["whole_report_concreteness", "ai_concreteness"]}><LineFigure id="figure-03-svg" rows={aggregateFigures} keys={["whole_report_concreteness", "ai_concreteness"]} ariaLabel="2020–2025년 전체 보고서와 AI 관련 문장 구체성" /></FigureShell>
        <FigureShell id="figure-04" number="Figure 4" title="연도별 시제 표지 비율" introduction="과거·현재 시제와 미래 조동사 표지의 상대 비율을 비교한다." caption="미래 조동사 표지는 미래지향 언어 전체를 의미하지 않는다." condition="2020–2025년 기업-연도" variables={["past_tense_share", "present_tense_share", "future_tense_share"]}><LineFigure id="figure-04-svg" rows={aggregateFigures} keys={["past_tense_share", "present_tense_share", "future_tense_share"]} ariaLabel="2020–2025년 시제 표지 비율" /></FigureShell>
        <FigureShell id="figure-05" number="Figure 5" title="AI 관련 문장의 금융 어휘 비율" introduction="AI 관련 문장에서 긍정·부정·불확실성 범주 어휘가 차지하는 비율을 비교한다." caption="Loughran–McDonald 금융사전에 일치한 어휘의 상대 비율이다." condition="2020–2025년 AI 관련 공시 기업-연도" variables={["ai_lm_positive_share", "ai_lm_negative_share", "ai_lm_uncertainty_share"]}><LineFigure id="figure-05-svg" rows={aggregateFigures} keys={["ai_lm_positive_share", "ai_lm_negative_share", "ai_lm_uncertainty_share"]} ariaLabel="2020–2025년 AI 관련 문장의 Loughran–McDonald 어휘 비율" /></FigureShell>
      </div>
      <h3>7.3 Pearson 상관관계</h3><CorrelationHeatmap data={pearsonCore} />
      <h3>7.4 Model-free 단변량 비교</h3><MetricTable caption="표 4A. AI 관련 공시 있음·없음 기업의 평균 비교" rows={primaryRows} columns={[["variable", "변수"], ["disclosure_N", "공시 있음 표본"], ["disclosure_mean", "공시 있음 평균"], ["non_disclosure_N", "공시 없음 표본"], ["non_disclosure_mean", "공시 없음 평균"], ["mean_difference", "평균 차이"], ["welch_t", "Welch t"], ["welch_pvalue", "p-value"]]} note="차이 방향은 공시 있음 − 공시 없음이다. 연도·산업·기업 규모를 통제하지 않은 평균 비교이다." /><MetricTable caption="표 4B. 보고서 길이 하위·상위 사분위 비교" rows={secondaryRows} columns={[["variable", "변수"], ["q1_mean", "하위 사분위 평균"], ["q4_mean", "상위 사분위 평균"], ["mean_difference", "하위 − 상위"], ["welch_t", "Welch t"], ["welch_pvalue", "Welch p"], ["wilcoxon_statistic", "Wilcoxon 통계량"], ["wilcoxon_pvalue", "Wilcoxon p"]]} note="2020–2025년 전체 표본에서 로그 보고서 단어 수를 기준으로 한 번 분류했다." /><div className="figure-grid">
        <FigureShell id="figure-06" number="Figure 6" title="AI 관련 공시 여부별 언어 특성 평균 추이" introduction="AI 관련 공시가 있는 기업과 없는 기업의 연도별 평균을 변수별 독립 패널로 비교한다." caption="연도·산업·기업 규모를 통제하지 않은 평균 비교이며 인과효과가 아니다." condition="2020–2025년 기업-연도" variables={["whole_report_concreteness", "lm_uncertainty_share", "fog_index", "report_word_count"]} legendItems={[{ label: "AI 관련 공시 있음", color: "#167c80" }, { label: "AI 관련 공시 없음", color: "#c58935", dash: true }]}><GroupMeanFigure id="figure-06-svg" rows={groupFigures} ariaLabel="2020–2025년 AI 관련 공시 있음과 없음 기업의 평균 언어 특성" /></FigureShell>
        <FigureShell id="figure-07" number="Figure 7" title="AI 관련 공시 여부별 표준화 평균 차이" introduction="AI 관련 공시 기업과 미공시 기업의 표준화 평균 차이를 변수별로 표시한다." caption="0은 집단 평균 차이가 없음을 뜻하며, 양수는 공시 기업 평균이 더 높음을 뜻한다." condition="2020–2025년 기업-연도" variables={effectVariables}><EffectSizeFigure id="figure-07-svg" rows={effectRows} ariaLabel="2020–2025년 AI 관련 공시 여부별 표준화 평균 차이" /></FigureShell>
        <FigureShell id="figure-08" number="Figure 8" title="동일 기업의 전년 대비 평균 변화" introduction="연속된 두 연도에 관찰된 동일 기업의 언어 특성 평균 변화를 표시한다." caption="각 변수의 원래 단위를 유지하며 0은 평균 변화가 없음을 뜻한다." condition="2020–2025년 중 유효한 연속연도 기업 쌍" variables={["whole_report_concreteness", "ai_sentence_count", "past_tense_share", "lm_uncertainty_share", "fog_index"]}><WithinChangeFigure id="figure-08-svg" rows={withinFigures} ariaLabel="2020–2025년 동일 기업의 전년 대비 언어 특성 평균 변화" /></FigureShell>
      </div></Section>

      <Section id="discussion" number="8" title="논의" kicker="DISCUSSION"><p>연도별 변화와 집단 간 평균 차이는 10-K에서 관찰된 언어적 패턴을 보여준다. 이러한 결과는 기업의 실제 AI 도입 여부나 도입 효과를 식별하지 않으며, 기업 구성과 보고서 특성의 차이가 함께 반영될 수 있다.</p></Section>

      <Section id="limitations" number="9" title="한계" kicker="LIMITATIONS"><ul className="limitations-list"><li>AI 관련 공시는 실제 AI 도입이 아니라 10-K에서 관찰된 공시 언어의 대리 측정치이다.</li><li>S&amp;P 500 구성기업 변경 이력의 누락, 기준일 차이, 기업명 변경과 합병·상장폐지 처리에서 측정오차가 발생할 수 있다.</li><li>연도별 표본 구성과 기업 특성 차이가 평균 추이에 영향을 줄 수 있다.</li><li>사전 기반 어휘 비율과 자동 언어 분류는 문맥과 복합적인 문장 구조를 완전히 반영하지 못한다.</li><li>기술통계, 상관관계와 단순 평균 비교만으로 인과관계를 판단할 수 없다.</li></ul></Section>
      <footer className="report-footer">2020–2025년 S&amp;P 500 기업 10-K 언어 분석 결과 보고서</footer>
    </div>
  </main>;
}

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    Promise.all(Object.entries(DATA_FILES).map(async ([key, filename]) => [key, await loadJson(filename)]))
      .then((entries) => setData(Object.fromEntries(entries)))
      .catch(() => setError(true));
  }, []);
  if (error) return <main className="loading-shell"><h1>분석 보고서를 불러오지 못했습니다.</h1><p>잠시 후 다시 시도해 주세요.</p><button type="button" onClick={() => window.location.reload()}>다시 시도</button></main>;
  if (!data) return <main className="loading-shell"><p>분석 결과를 불러오는 중입니다.</p></main>;
  return <Report data={data} />;
}
