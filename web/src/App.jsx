import { useEffect, useMemo, useState } from "react";

const DATA_FILES = {
  summary: "analysis-summary.json",
  definitions: "variable-definitions.json",
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
  sourceManifest: "source-manifest.json",
  buildMetadata: "build-metadata.json",
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

async function loadJson(filename) {
  const response = await fetch(`/data/${filename}`);
  if (!response.ok) throw new Error(`${filename}: ${response.status}`);
  return response.json();
}

function MarkdownLite({ value }) {
  if (!value) return <p className="muted">문서를 불러오는 중입니다.</p>;
  return <div className="source-document">{value.split(/\r?\n/).map((line, index) => {
    if (line.startsWith("# ")) return <h3 key={index}>{line.slice(2)}</h3>;
    if (line.startsWith("## ")) return <h4 key={index}>{line.slice(3)}</h4>;
    if (line.startsWith("### ")) return <h5 key={index}>{line.slice(4)}</h5>;
    if (line.startsWith("- ")) return <li key={index}>{line.slice(2)}</li>;
    if (line.startsWith("```")) return null;
    if (!line.trim()) return <div className="md-space" key={index} />;
    return <p key={index}>{line}</p>;
  })}</div>;
}

function SourceNote({ source, generatedBy = "scripts/generate_web_analysis_data.py", n, condition }) {
  return <div className="source-note"><strong>출처:</strong> <code>{source || "web/public/data/"}</code> · <strong>생성:</strong> <code>{generatedBy}</code>{n !== undefined && <> · <strong>N:</strong> {formatInteger(n)}</>}{condition && <> · <strong>조건:</strong> {condition}</>}</div>;
}

function MetricTable({ rows, columns, caption, source, condition }) {
  return <div className="table-card"><div className="table-scroll"><table className="paper-table"><caption>{caption}</caption><thead><tr>{columns.map(([key, label]) => <th key={key}>{label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.variable || row.report_year || row.year || "row"}-${index}`}>{columns.map(([key]) => <td key={key}>{row[key] === null || row[key] === undefined ? "-" : row[key]}</td>)}</tr>)}</tbody></table></div><SourceNote source={source} condition={condition} /></div>;
}

function FormulaBlock({ title, formula, note }) {
  return <div className="formula-block"><h4>{title}</h4><div className="formula">{formula}</div>{note && <p>{note}</p>}</div>;
}

function VariableBlock({ item }) {
  return <details className="variable-block"><summary><span><code>{item.variable}</code><strong>{item.display_name}</strong></span><em>{item.analysis_level}</em></summary><div className="variable-detail"><p><strong>개념적 정의</strong>{item.conceptual_meaning}</p><p><strong>조작적 정의</strong>{item.definition} {item.operationalization}</p><FormulaBlock title="수식" formula={item.formula} /><div className="definition-grid"><p><strong>분자</strong>{display(item.numerator)}</p><p><strong>분모</strong>{display(item.denominator)}</p><p><strong>단위</strong>{display(item.unit)}</p><p><strong>적격 토큰</strong>{display(item.token_rule)}</p><p><strong>적격 문장</strong>{display(item.sentence_rule)}</p><p><strong>사전/NLP</strong>{display(item.method)}</p><p><strong>전처리</strong>{display(item.preprocessing)}</p><p><strong>결측 처리</strong>{display(item.missing_rule)}</p><p><strong>0 처리</strong>{display(item.zero_rule)}</p><p><strong>조건부 표본</strong>{display(item.conditional_sample)}</p><p><strong>Source column</strong><code>{display(item.source_columns)}</code></p><p><strong>Source dataset</strong><code>{item.source_dataset}</code></p><p><strong>Source script</strong><code>{display(item.source_scripts)}</code></p><p><strong>검증 규칙</strong>{display(item.validation_rule)}</p><p><strong>해석</strong>{display(item.interpretation)}</p><p><strong>한계</strong>{display(item.limitation)}</p><p><strong>별칭</strong><code>{display(item.aliases)}</code></p></div></div></details>;
}

function Section({ id, number, title, kicker, children }) {
  return <section className="report-section" id={id}><div className="section-heading"><span className="section-number">{number}</span><div><p className="kicker">{kicker}</p><h2>{title}</h2></div></div>{children}</section>;
}

function Report({ data }) {
  const { summary, definitions, yearly, descriptive, comparison, within, changes, pearson, spearman, vif, sampleAudit, quality, sourceManifest, buildMetadata, docs } = data;
  const years = safeRows(yearly);
  const first = years[0] || {};
  const last = years[years.length - 1] || {};
  const groups = useMemo(() => [...new Set(definitions.map((item) => item.group))], [definitions]);
  const coreVariables = ["ai_disclosure", "ai_sentence_count", "whole_report_concreteness", "ai_concreteness", "past_tense_share", "present_tense_share", "future_tense_share", "lm_uncertainty_share", "passive_voice_sentence_share", "fog_index", "report_word_count"];
  const coreDefinitions = coreVariables.map((name) => definitions.find((item) => item.variable === name)).filter(Boolean);
  const yearlyRows = years.map((row) => ({ report_year: row.report_year, firm_year_count: formatInteger(row.firm_year_count), unique_company_count: formatInteger(row.unique_company_count), ai_disclosure_count: formatInteger(row.ai_disclosure_count), ai_disclosure_rate: formatPercent(row.ai_disclosure_rate) }));
  const resultRows = years.map((row) => ({ report_year: row.report_year, ai_disclosure_rate: formatPercent(row.ai_disclosure_rate), mean_ai_sentence_count_all: formatNumber(row.mean_ai_sentence_count_all, 3), mean_ai_sentence_count_disclosers: formatNumber(row.mean_ai_sentence_count_disclosers, 3), mean_whole_report_concreteness_all: formatNumber(row.mean_whole_report_concreteness_all, 3), mean_ai_concreteness_disclosers: formatNumber(row.mean_ai_concreteness_disclosers, 3), mean_present_tense_share_all: formatPercent(row.mean_present_tense_share_all, 2), mean_future_tense_share_all: formatPercent(row.mean_future_tense_share_all, 2), mean_lm_uncertainty_share_all: formatPercent(row.mean_lm_uncertainty_share_all, 2), mean_passive_voice_sentence_share_all: formatPercent(row.mean_passive_voice_sentence_share_all, 2), mean_fog_index_all: formatNumber(row.mean_fog_index_all, 3), mean_report_word_count_all: formatInteger(row.mean_report_word_count_all) }));
  const descriptiveRows = safeRows(descriptive).slice(0, 16).map((row) => ({ variable: row.variable, N: formatInteger(row.N), mean: formatNumber(row.mean, 3), standard_deviation: formatNumber(row.standard_deviation, 3), p25: formatNumber(row.p25, 3), median: formatNumber(row.median, 3), p75: formatNumber(row.p75, 3) }));
  const comparisonRows = safeRows(comparison).map((row) => ({ variable: row.variable, disclosure_N: formatInteger(row.disclosure_N), disclosure_mean: formatNumber(row.disclosure_mean, 3), non_disclosure_N: formatInteger(row.non_disclosure_N), non_disclosure_mean: formatNumber(row.non_disclosure_mean, 3), mean_difference: formatNumber(row.mean_difference, 3), standardized_mean_difference: formatNumber(row.standardized_mean_difference, 3), welch_t: formatNumber(row.welch_t, 3), welch_pvalue: formatP(row.welch_pvalue) }));
  const corrRows = safeRows(pearson).slice(0, 12).map((row) => ({ variable: row.variable, ai_disclosure: formatNumber(row.ai_disclosure, 3), ai_sentence_count: formatNumber(row.ai_sentence_count, 3), whole_report_concreteness: formatNumber(row.whole_report_concreteness, 3), lm_uncertainty_share: formatNumber(row.lm_uncertainty_share, 3), fog_index: formatNumber(row.fog_index, 3), report_word_count: formatNumber(row.report_word_count, 3) }));
  const vifRows = safeRows(vif).map((row) => ({ variable: row.variable, N: formatInteger(row.N), VIF: formatNumber(row.VIF, 3) }));
  const sourceCount = safeRows(sourceManifest?.sources).length;

  return <main className="report-app">
    <aside className="toc" aria-label="연구보고서 목차"><div className="toc-brand"><strong>S&amp;P 500</strong><span>연구보고서</span></div><nav><a href="#title">표지</a><a href="#abstract">초록</a><a href="#design">1. 연구설계</a><a href="#sample">2. 표본 구축</a><a href="#collection">3. 자료 수집</a><a href="#processing">4. 텍스트 처리</a><a href="#methods">5. 변수 측정</a><a href="#statistics">6. 통계 분석</a><a href="#results">7. 결과</a><a href="#discussion">8. 논의</a><a href="#limitations">9. 한계</a><a href="#reproducibility">10. 재현성</a><a href="#variables">부록 A. 변수 정의</a></nav><div className="toc-meta">VERSION {buildMetadata?.version || "0.12.0"}<br /><small>firm-year · 2020–2025</small></div></aside>
    <div className="report-main">
      <section className="title-page" id="title"><p className="kicker">S&amp;P 500 · FORM 10-K · FIRM-YEAR PANEL</p><h1>2020–2025년 S&amp;P 500 기업<br /><em>10-K 언어 특성 분석</em></h1><p className="subtitle">AI 공시, 구체성, 시제, Loughran–McDonald 어휘, 수동태와 가독성의 기술통계 및 연관성 분석</p><dl className="title-meta"><div><dt>분석기간</dt><dd>2020–2025</dd></div><div><dt>분석단위</dt><dd>firm-year</dd></div><div><dt>Repository</dt><dd>Vulter3653/s-p500</dd></div><div><dt>Commit</dt><dd><code>{buildMetadata?.git_commit || summary.git_commit}</code></dd></div><div><dt>VERSION</dt><dd>{buildMetadata?.version}</dd></div><div><dt>생성 시각</dt><dd>{buildMetadata?.generated_at || summary.generated_at}</dd></div></dl></section>

      <Section id="abstract" number="초록" title="연구 요약" kicker="ABSTRACT / EXECUTIVE SUMMARY"><div className="abstract-box"><p>본 연구는 2020–2025년 S&amp;P 500 기업의 Form 10-K를 firm-year 단위로 연결하여 AI 관련 공시 텍스트와 문서 언어 특성의 연도별 분포를 기술한다. 분석 표본은 {formatInteger(summary.panel.observations)} firm-year, {formatInteger(summary.panel.companies)}개 기업이며 {formatInteger(summary.panel.balanced_companies)}개 기업이 6개 연도를 모두 관측한 균형 패널이다.</p><p>핵심 측정치는 AI 직접 문장 여부와 개수, Brysbaert 구체성, spaCy 기반 시제·수동태, Loughran–McDonald 금융 어휘, Gunning Fog Index 및 보고서 길이다. 분석은 기술통계, 연도별 변화, Welch 집단 비교, 동일 기업 내 전년 변화, Pearson·Spearman 상관과 VIF 진단으로 구성한다.</p><p className="caution"><strong>해석 범위:</strong> AI 관련 변수는 실제 AI adoption이 아니라 10-K에 나타난 <code>text-based AI communication proxy</code>이다. 평균 차이와 상관관계는 통제되지 않은 기술적 연관성으로 인과효과를 의미하지 않는다.</p></div><SourceNote source="analysis/descriptive_2020_2025/tables/" n={summary.panel.observations} condition="전체 firm-year" /></Section>

      <Section id="design" number="1" title="연구설계" kicker="RESEARCH DESIGN"><p>관측 단위는 기업 식별자와 보고연도 조합인 <code>firm-year</code>이며, 각 행은 한 기업의 한 회계연도 Form 10-K 보고서를 의미한다. 패널은 연도별 적격 filing과 기업 CIK 연결 결과를 읽기 전용으로 결합한 불균형 패널이다.</p><div className="two-column"><div><h3>연구 질문</h3><p>AI 관련 직접 공시가 2020–2025년 동안 얼마나 확산되었고, AI 문장의 구체성·시제·감성·가독성이 어떻게 분포하는지 기술한다.</p></div><div><h3>AI communication proxy</h3><p><code>ai_disclosure</code>는 기존 AI matcher가 추출한 직접 문장이 하나 이상일 때 1이다. 이는 보고서에 나타난 언어적 공시이며 실제 기술 도입이나 기업 전략을 직접 측정하지 않는다.</p></div></div></Section>

      <Section id="sample" number="2" title="표본 구축" kicker="SAMPLE CONSTRUCTION"><p>연도별 S&amp;P 500 구성 manifest와 SEC CIK를 사용해 대상 기업을 확정하고, 정확한 <code>reportDate</code> 연도의 Form 10-K만 적격 filing으로 유지했다. 동일 CIK의 ticker 변경은 기업 식별 연결에 반영하되, 원자료의 시점별 ticker와 회사명은 보존했다.</p><MetricTable caption="표 1. 연도별 표본 구성" rows={yearlyRows} columns={[["report_year", "보고연도"], ["firm_year_count", "firm-year 수"], ["unique_company_count", "고유 기업 수"], ["ai_disclosure_count", "AI 공시 수"], ["ai_disclosure_rate", "AI 공시 비율"]]} source="analysis/descriptive_2020_2025/tables/table_01_sample_by_year.csv" /><div className="audit-grid"><div><strong>균형 패널</strong><span>{formatInteger(summary.panel.balanced_companies)}개 기업</span></div><div><strong>불균형 패널</strong><span>{formatInteger(summary.panel.unbalanced_companies)}개 기업</span></div><div><strong>중복 company-year</strong><span>{formatInteger(sampleAudit?.duplicate_company_year)}건</span></div><div><strong>중복 accession</strong><span>{formatInteger(sampleAudit?.duplicate_accession)}건</span></div></div></Section>

      <Section id="collection" number="3" title="자료 수집" kicker="DATA COLLECTION"><div className="method-list"><p><strong>SEC filing 선정.</strong> SEC submissions metadata에서 정확한 Form <code>10-K</code>, report date 연도, 유일 accession과 primary document를 확인했다. <code>10-K/A</code>, <code>NT 10-K</code>, <code>8-K</code> 및 annual report PDF는 제외했다.</p><p><strong>원문 보관.</strong> SEC response bytes와 파일 크기·SHA-256을 manifest에 기록하고, 원본 HTML은 Git에 넣지 않고 Google Drive에 보관한다. 기본 저장 형식은 <code>&lt;root&gt;/&lt;연도&gt;/&lt;번호&gt;_&lt;연도&gt;_&lt;기업명&gt;_&lt;SYMBOL&gt;_&lt;CIK&gt;.html</code>이다.</p><p><strong>무결성.</strong> source manifest와 생성 metadata에는 원자료 경로, SHA-256, 생성 script, Git commit과 생성 시각이 연결되어 있다.</p></div><SourceNote source="web/public/data/source-manifest.json" /></Section>

      <Section id="processing" number="4" title="텍스트 처리" kicker="TEXT PROCESSING"><div className="two-column"><div><h3>HTML 정제</h3><p><code>scripts/extract_10k_analysis_text.py</code>가 HTML parser로 script/style, hidden inline XBRL metadata를 제거하고 표·문단·문장과 section warning을 생성한다. 공백 정규화와 분석 본문 품질 상태는 extraction 결과에 보존된다.</p></div><div><h3>AI 직접 문장</h3><p>기존 AI term list와 case-insensitive word-boundary matcher를 사용한다. phrase match는 비중첩으로 처리하고, 여러 term이 한 문장에 있어도 직접 문장 count는 해당 문장을 한 번 센다.</p></div></div><div className="flow"><span>SEC metadata</span><b>→</b><span>primary HTML</span><b>→</b><span>정제 본문</span><b>→</b><span>문단·문장</span><b>→</b><span>firm-year 변수</span></div></Section>

      <span id="methods" className="anchor-alias" aria-hidden="true" /><Section id="measurement" number="5" title="변수 측정" kicker="VARIABLE MEASUREMENT"><p>아래 핵심 변수는 실제 <code>variable-definitions.json</code>에서 읽어 수식·분자·분모·결측·source metadata를 표시한다. 모든 204개 변수의 전체 정의는 부록에서 확인할 수 있다.</p><div className="measurement-index">{groups.map((group) => <span key={group}>{group} · {definitions.filter((item) => item.group === group).length}개</span>)}</div><div className="variable-feature-grid">{coreDefinitions.map((item) => <VariableBlock key={item.variable} item={item} />)}</div><FormulaBlock title="Fog Index 구현식" formula={"Fogᵢₜ = 0.4 × [ Eligible Wordsᵢₜ / Eligible Sentencesᵢₜ + 100 × (Complex Wordsᵢₜ / Eligible Wordsᵢₜ) ]"} note="복잡 단어 판정, eligible token과 non-empty sentence 규칙은 실제 readability 함수와 source metadata를 따른다. 이 지수는 정보 품질 자체가 아니라 표면적 복잡성을 측정한다." /></Section>

      <Section id="statistics" number="6" title="통계 분석" kicker="STATISTICAL ANALYSIS"><div className="analysis-methods"><div><h3>기술통계</h3><p>전체 및 연도별 firm-year에 대해 N, 결측 N, 평균, 표준편차, 사분위수와 최댓값을 산출한다. AI 직접 문장 수준 변수는 AI 공시 firm-year 조건부 N을 별도로 유지한다.</p></div><div><h3>집단 비교</h3><p>AI 공시·미공시 집단의 평균 차이, 표준화 평균 차이와 Welch t-test를 표시한다. 연도·산업·규모를 통제하지 않은 단순 비교이다.</p></div><div><h3>변화</h3><p>연도별 절대 변화와 전년 대비 변화율, 실제 연속연도 firm-year의 동일 기업 내 변화(ΔX<sub>i,t</sub> = X<sub>i,t</sub> − X<sub>i,t−1</sub>)를 구분한다.</p></div><div><h3>연관성·진단</h3><p>Pearson·Spearman 상관과 후보 통제변수 VIF를 산출한다. 구성적 관계와 기계적으로 파생된 변수쌍은 동일 모형 투입 시 주의한다.</p></div></div><SourceNote source="analysis/descriptive_2020_2025/tables/" generatedBy="scripts/run_descriptive_statistics.py; scripts/run_correlation_analysis.py" /></Section>

      <Section id="results" number="7" title="분석 결과" kicker="RESULTS"><h3>7.1 표본 특성 및 AI 공시 확산</h3><p>{first.report_year}년 AI 공시 비율은 {formatPercent(first.ai_disclosure_rate)}이고 {last.report_year}년에는 {formatPercent(last.ai_disclosure_rate)}이다. 연도별 관측치 수가 다르므로 전체 평균은 연도 평균의 단순평균이 아니라 원자료 전체 N을 기준으로 한다.</p><MetricTable caption="표 2. 연도별 핵심 기술통계" rows={resultRows} columns={[["report_year", "보고연도"], ["ai_disclosure_rate", "AI 공시 비율"], ["mean_ai_sentence_count_all", "AI 문장 평균(전체)"], ["mean_ai_sentence_count_disclosers", "AI 문장 평균(공시)"], ["mean_whole_report_concreteness_all", "전체 보고서 구체성"], ["mean_ai_concreteness_disclosers", "AI 구체성(공시)"], ["mean_present_tense_share_all", "현재 시제"], ["mean_future_tense_share_all", "미래 표지"], ["mean_lm_uncertainty_share_all", "Loughran–McDonald uncertainty"], ["mean_passive_voice_sentence_share_all", "수동태"], ["mean_fog_index_all", "Fog Index"], ["mean_report_word_count_all", "보고서 단어 수"]]} source="analysis/descriptive_2020_2025/tables/table_04_descriptive_statistics_by_year.csv" condition="AI 수준 값은 공시 firm-year 조건부" /><h3>7.2 전체 기술통계</h3><MetricTable caption="표 3. 전체 표본 기술통계" rows={descriptiveRows} columns={[["variable", "변수"], ["N", "N"], ["mean", "평균"], ["standard_deviation", "표준편차"], ["p25", "제1사분위수"], ["median", "중앙값"], ["p75", "제3사분위수"]]} source="analysis/descriptive_2020_2025/tables/table_02_overall_descriptive_statistics.csv" condition="전체 firm-year; AI 수준 변수는 유효 분모 조건부" /><h3>7.3 공시·미공시 비교</h3><MetricTable caption="표 4. AI 공시 여부별 단순 비교" rows={comparisonRows} columns={[["variable", "변수"], ["disclosure_N", "공시 N"], ["disclosure_mean", "공시 평균"], ["non_disclosure_N", "미공시 N"], ["non_disclosure_mean", "미공시 평균"], ["mean_difference", "평균 차이"], ["standardized_mean_difference", "표준화 차이"], ["welch_t", "Welch t"], ["welch_pvalue", "p-value"]]} source="analysis/descriptive_2020_2025/tables/table_05_ai_disclosure_group_comparison.csv" condition="연도·산업·규모 통제 없는 단순 집단 비교" /><h3>7.4 상관관계</h3><MetricTable caption="표 5. Pearson 상관관계 일부" rows={corrRows} columns={[["variable", "행 변수"], ["ai_disclosure", "AI 공시"], ["ai_sentence_count", "AI 문장 수"], ["whole_report_concreteness", "전체 구체성"], ["lm_uncertainty_share", "Loughran–McDonald uncertainty"], ["fog_index", "Fog Index"], ["report_word_count", "보고서 단어 수"]]} source="analysis/descriptive_2020_2025/tables/table_08_pearson_correlation_full_sample.csv" condition="pairwise complete observations" /><h3>7.5 동일 기업 변화와 VIF</h3><div className="two-column"><div><p>동일 기업 내 변화 산출물은 {formatInteger(within?.length)}개 변수·연도 조합이며, 실제 전년도 관측치가 있는 pair만 포함한다. 전체 변화표는 <code>year-over-year-changes.json</code>에서 연결한다.</p></div><MetricTable caption="표 6. VIF 진단" rows={vifRows} columns={[["variable", "변수"], ["N", "N"], ["VIF", "VIF"]]} source="analysis/descriptive_2020_2025/tables/table_15_vif_diagnostics.csv" condition="후보 텍스트 통제변수" /></div><p className="caution">상관계수와 VIF는 변수 간 연관성과 중복 가능성을 진단할 뿐 인과효과를 의미하지 않는다. 특히 count와 log count, count와 share, Fog와 평균 문장 길이, past·present·future share는 함께 투입할 때 구조적 중복을 검토해야 한다.</p></Section>

      <Section id="discussion" number="8" title="논의" kicker="DISCUSSION"><p>AI 공시 비율과 AI 직접 문장 수는 후기 연도로 갈수록 확대되지만, 이 변화는 보고 관행과 표본 구성의 변화가 함께 반영된 기술적 패턴이다. 2023년 전후의 큰 폭 변화는 year fixed effects 또는 명시적인 시기 구분을 고려할 필요성을 보여주지만, 이 화면은 원인이나 사건을 확정하지 않는다.</p><p>AI 공시 여부가 후기 연도에 포화되면 이진변수의 횡단면 변별력이 감소할 수 있다. 후속 분석에서는 AI 문장 수, 문장 비율, 구체성, 시제 및 Loughran–McDonald 범주와 같은 연속형 특성을 별도로 검토할 수 있다.</p></Section>

      <Section id="limitations" number="9" title="한계" kicker="LIMITATIONS"><MarkdownLite value={docs.limitations} /><SourceNote source="web/docs/research-dashboard-limitations.md" /></Section>

      <Section id="reproducibility" number="10" title="재현성" kicker="REPRODUCIBILITY"><MarkdownLite value={docs.reproducibility} /><div className="download-grid"><a href="/data/analysis-summary.json" download>분석 요약 JSON</a><a href="/data/variable-definitions.json" download>변수 정의 JSON</a><a href="/downloads/table-variable-definitions.csv" download>변수 정의 CSV</a><a href="/data/source-manifest.json" download>Source manifest</a></div><SourceNote source="web/public/data/source-manifest.json" /></Section>

      <span id="variables" className="anchor-alias" aria-hidden="true" /><Section id="appendix" number="부록 A" title="변수 정의" kicker="APPENDIX A · VARIABLE DEFINITIONS"><p>총 {formatInteger(definitions.length)}개 변수의 상세 정의를 패널별로 제공한다. 각 행을 펼치면 개념, 조작화, 수식, 분자·분모, 적격 단위, 전처리, 결측·0 처리, 조건부 표본, source와 한계를 확인할 수 있다.</p><div className="appendix-tools"><input placeholder="변수명 검색" aria-label="변수명 검색" onChange={(event) => { const value = event.target.value.toLowerCase(); document.querySelectorAll(".variable-block").forEach((node) => { node.hidden = value && !node.textContent.toLowerCase().includes(value); }); }} /></div><div className="appendix-list">{definitions.map((item) => <VariableBlock key={item.variable} item={item} />)}</div><SourceNote source="web/public/data/variable-definitions.json" n={definitions.length} /></Section>

      <footer className="report-footer">본 웹 보고서는 기존 분석 산출물을 읽기 전용으로 표시한다. 원본 HTML과 자격 증명은 공개하지 않는다. · VERSION {buildMetadata?.version || "0.12.0"} · commit <code>{buildMetadata?.git_commit || summary.git_commit}</code></footer>
    </div>
  </main>;
}

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    Promise.all(Object.entries(DATA_FILES).map(async ([key, filename]) => [key, await loadJson(filename)]).concat(DOCUMENTS.map(async ([key, filename]) => [key, await fetch(`/docs/${filename}`).then((response) => { if (!response.ok) throw new Error(`${filename}: ${response.status}`); return response.text(); })])))
      .then((entries) => setData(Object.fromEntries(entries)))
      .catch((reason) => setError(reason.message));
  }, []);
  if (error) return <main className="loading-shell"><h1>분석 보고서를 불러오지 못했습니다.</h1><p>{error}</p><button type="button" onClick={() => window.location.reload()}>다시 시도</button></main>;
  if (!data) return <main className="loading-shell"><p>연구보고서와 분석 산출물을 불러오는 중입니다.</p></main>;
  return <Report data={data} />;
}
