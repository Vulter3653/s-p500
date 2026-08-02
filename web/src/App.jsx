import { useEffect, useMemo, useState } from "react";
import { analysisSummary } from "./data/analysisSummary.js";

const fallbackYears = analysisSummary.years;
const percent = (value) => `${(value * 100).toFixed(1)}%`;
const number = (value, digits = 2) => Number(value).toLocaleString("ko-KR", { maximumFractionDigits: digits });

function App() {
  const [summary, setSummary] = useState(null);
  const [year, setYear] = useState("all");

  useEffect(() => {
    fetch("/api/summary")
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => data && setSummary(data))
      .catch(() => undefined);
  }, []);

  const years = summary?.years?.map((item) => ({ ...fallbackYears.find((base) => base.year === item.year), ...item })) ?? fallbackYears;
  const selected = useMemo(
    () => (year === "all" ? years : years.filter((item) => String(item.year) === year)),
    [year, years],
  );
  const observations = selected.reduce((total, item) => total + item.observations, 0);
  const disclosure = selected.reduce((total, item) => total + item.disclosure, 0);
  const rate = observations ? ((disclosure / observations) * 100).toFixed(1) : "-";
  const average = (field) => selected.length ? selected.reduce((total, item) => total + item[field], 0) / selected.length : 0;

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="대시보드 탐색">
        <div className="brand-mark">SP</div>
        <div className="brand-copy"><strong>S&amp;P 500</strong><span>언어 연구실</span></div>
        <nav>
          <a className="active" href="#overview">개요</a>
          <a href="#trend">연도별 추이</a>
          <a href="#method">측정 범위</a>
        </nav>
        <div className="sidebar-note"><span className="live-dot" />2020–2025 연구 패널<br /><small>firm-year 단위</small></div>
      </aside>

      <div className="workspace">
        <header className="topbar"><div><span className="breadcrumb">분석 대시보드 / 개요</span><h1>10-K 언어 분석</h1></div><label className="year-control"><span>보고연도</span><select value={year} onChange={(event) => setYear(event.target.value)}><option value="all">전체 연도</option>{years.map((item) => <option key={item.year} value={item.year}>{item.year}</option>)}</select></label></header>

        <section className="headline" id="overview"><div><p className="eyebrow">S&amp;P 500 · FORM 10-K · FIRM-YEAR</p><h2>AI 공시는 어떻게<br /><em>확장되었는가</em></h2><p>2020–2025년 기업-보고연도별 AI disclosure와 텍스트 지표를 발표용 화면으로 요약합니다.</p></div><div className="headline-meta"><span>분석 기간</span><strong>{year === "all" ? "2020–2025" : year}</strong><small>기존 결과 읽기 전용</small></div></section>

        <section className="cards" aria-label="요약 지표"><article className="card card-primary"><span>AI 공시 비율</span><strong>{rate}%</strong><small>{disclosure.toLocaleString("ko-KR")} / {observations.toLocaleString("ko-KR")} firm-year</small></article><article className="card"><span>firm-year 관측치</span><strong>{observations.toLocaleString("ko-KR")}</strong><small>고유 기업 {analysisSummary.panel.companies.toLocaleString("ko-KR")}개 · 균형 패널 {analysisSummary.panel.balancedCompanies}개</small></article><article className="card"><span>AI 직접 문장 수</span><strong>{number(average("aiSentenceCount"), 1)}</strong><small>{year === "all" ? "전체 표본 평균 · 0 포함" : `${year}년 평균`}</small></article></section>

        <section className="content-grid" id="trend">
          <article className="panel chart-panel"><div className="panel-heading"><div><p className="eyebrow">YEARLY OVERVIEW</p><h2>연도별 AI 공시 비율</h2></div><span className="legend"><i className="legend-dot" />AI 공시</span></div><div className="bar-chart" aria-label="연도별 AI 공시 비율 막대그래프">{selected.map((item) => <div className="bar-group" key={item.year}><div className="bar-track"><div className="bar-fill" style={{ height: `${(item.disclosure / item.observations) * 100}%` }}><span>{((item.disclosure / item.observations) * 100).toFixed(1)}%</span></div></div><strong>{item.year}</strong></div>)}</div><p className="chart-caption">각 연도의 전체 firm-year 중 AI 관련 직접 문장이 확인된 비율입니다.</p></article>

          <article className="panel table-panel"><div className="panel-heading"><div><p className="eyebrow">SAMPLE</p><h2>표본 구성</h2></div><span className="status">읽기 전용</span></div><div className="table-wrap"><table><caption className="sr-only">연도별 firm-year 표본과 AI 공시 요약</caption><thead><tr><th>연도</th><th>firm-year</th><th>공시</th><th>비율</th></tr></thead><tbody>{selected.map((item) => <tr key={item.year}><th scope="row">{item.year}</th><td>{item.observations.toLocaleString("ko-KR")}</td><td>{item.disclosure.toLocaleString("ko-KR")}</td><td>{percent(item.disclosure / item.observations)}</td></tr>)}</tbody></table></div></article>
        </section>

        <section className="metrics-grid" aria-label="패널 언어 지표"><article className="panel metric-table"><div className="panel-heading"><div><p className="eyebrow">LANGUAGE PROFILE</p><h2>주요 언어 지표</h2></div><span className="status">패널 산출값</span></div><div className="table-wrap"><table><thead><tr><th>연도</th><th>구체성</th><th>AI 구체성</th><th>현재 시제</th><th>불확실성</th><th>Fog</th></tr></thead><tbody>{selected.map((item) => <tr key={item.year}><th scope="row">{item.year}</th><td>{number(item.wholeReportConcreteness, 3)}</td><td>{number(item.aiConcreteness, 3)}</td><td>{percent(item.present)}</td><td>{percent(item.uncertainty)}</td><td>{number(item.fog, 2)}</td></tr>)}</tbody></table></div><p className="chart-caption">구체성·시제·LM uncertainty·Fog Index는 기존 확장 패널의 연도별 평균이다.</p></article><article className="panel insight-panel"><div className="panel-heading"><div><p className="eyebrow">KEY FINDINGS</p><h2>패널에서 보이는 변화</h2></div></div><ul className="insight-list"><li><strong>2023년 전환:</strong> AI 공시 비율이 2022년 {percent(analysisSummary.years[2].disclosure / analysisSummary.years[2].observations)}에서 2023년 {percent(analysisSummary.years[3].disclosure / analysisSummary.years[3].observations)}로 상승했습니다.</li><li><strong>공시의 구체성:</strong> AI 직접 문장 concreteness는 2023년 이후 낮아지는 방향을 보입니다.</li><li><strong>문서 가독성:</strong> Fog Index는 {number(analysisSummary.years[0].fog, 1)}에서 {number(analysisSummary.years[5].fog, 1)}로 소폭 상승했습니다.</li><li><strong>상관관계 주의:</strong> `past_tense_share`와 `present_tense_share`의 Pearson 상관은 {analysisSummary.correlations[0].value.toFixed(3)}입니다.</li></ul></article></section>

        <section className="research-section" aria-label="연구 방법과 결과">
          <div className="section-intro"><p className="eyebrow">RESEARCH CONTEXT</p><h2>수집부터 해석까지</h2><p>대시보드 수치는 2020–2025년 기존 분석 산출물을 읽기 전용으로 연결한 결과입니다. 아래 항목을 펼쳐 데이터의 출처와 변수의 의미를 확인할 수 있습니다.</p></div>
          <div className="research-grid">
            <details className="research-card" open><summary><span className="step-number">01</span><span><strong>데이터 수집 방법</strong><small>표본·filing·원문 보관</small></span></summary><div className="research-body"><p>S&amp;P 500 구성기업을 연도별 기준으로 확정하고 SEC CIK를 기업 식별자로 사용했습니다. 동일 CIK의 복수 ticker는 한 기업으로 통합했습니다.</p><ul><li>정확한 `reportDate` 연도의 Form `10-K`만 포함</li><li>`10-K/A`, `NT 10-K`, `8-K`, PDF annual report 제외</li><li>SEC filing metadata와 primary HTML을 manifest에 연결</li><li>수집한 raw HTML은 검증 후 Google Drive에 보관</li></ul><p className="source-note">분석 단위: <code>company_id + report_year</code>의 firm-year</p></div></details>
            <details className="research-card"><summary><span className="step-number">02</span><span><strong>변수 정의</strong><small>AI·언어·문서 지표</small></span></summary><div className="research-body"><dl><dt><code>ai_disclosure</code></dt><dd>AI 관련 직접 문장이 1개 이상이면 1, 아니면 0</dd><dt><code>ai_sentence_count</code></dt><dd>AI 직접 문장의 수. 미공시 firm-year는 0</dd><dt>구체성</dt><dd>Brysbaert 기반 전체 보고서·AI 문장 평균 점수</dd><dt>시제·수동태</dt><dd>spaCy POS/dependency 기반 count와 share</dd><dt>LM·Fog</dt><dd>Loughran–McDonald 사전 범주와 Fog Index</dd></dl></div></details>
            <details className="research-card"><summary><span className="step-number">03</span><span><strong>분석 방법</strong><small>기술통계·변화·상관</small></span></summary><div className="research-body"><p>전체 표본과 연도별 표본의 평균·분산·분위수를 산출하고, AI 공시·미공시 단순 집단 비교를 제시했습니다.</p><ul><li>연도별 평균과 전년 대비 변화</li><li>연속 연도 관측치가 있는 동일 기업 내 변화</li><li>전체 표본·AI 공시 표본의 Pearson 및 Spearman 상관</li><li>후속 회귀를 위한 후보 통제변수 VIF 점검</li></ul><p className="source-note">상관관계와 평균 차이는 인과효과가 아닙니다.</p></div></details>
            <details className="research-card"><summary><span className="step-number">04</span><span><strong>분석 결과</strong><small>2020–2025 핵심 발견</small></span></summary><div className="research-body result-body"><div><strong>AI 공시 확산</strong><span>27.58% → 96.69%</span></div><div><strong>AI 직접 문장 평균</strong><span>1.379 → 17.893개</span></div><div><strong>AI 문장 구체성</strong><span>2.994 → 2.736</span></div><div><strong>현재 시제 비율</strong><span>71.81% → 75.34%</span></div><div><strong>Fog Index</strong><span>20.637 → 20.883</span></div><p>2023년 전후로 AI 공시가 크게 증가했으며, 이후 이진 공시 여부보다 문장 수·구체성·시제·감성 같은 연속형 특성이 더 세밀한 차이를 제공할 수 있습니다.</p></div></details>
            <details className="research-card formula-card"><summary><span className="step-number">05</span><span><strong>수식 및 측정 방법</strong><small>분자·분모·결측 규칙</small></span></summary><div className="research-body formula-body"><div><strong>AI 공시</strong><code>ai_disclosure = 1(ai_sentence_count ≥ 1)</code><span>AI 문장이 없으면 count는 0, 구조적 결측은 결측으로 유지</span></div><div><strong>시제 비율</strong><code>tense_share = tense_count / (past + present + future count)</code><span>미래 표지는 `will`, `shall`, `'ll`만 포함</span></div><div><strong>수동태 비율</strong><code>passive_share = passive_sentence_count / spaCy sentence count</code><span>`auxpass` 또는 `nsubjpass` dependency 사용</span></div><div><strong>LM 비율</strong><code>lm_share = dictionary_match_count / valid_token_count</code><span>Loughran–McDonald 범주별 일치 token을 사용</span></div><div><strong>Fog Index</strong><code>Fog = 0.4 × (average sentence length + complex word share × 100)</code><span>복잡 단어는 기존 readability heuristic을 따름</span></div><div><strong>구체성 평균</strong><code>mean concreteness = Σ matched token score / matched token count</code><span>SMART 제거·Porter stemming·unique stem fallback, collision은 제외</span></div><p className="source-note">AI 수준 평균·비율·Fog는 AI 직접 문장이 없는 firm-year에서 유효 분모가 없으므로 0으로 대체하지 않습니다.</p></div></details>
          </div>
        </section>

        <section className="panel method-panel" id="method"><div><p className="eyebrow">RESEARCH NOTE</p><h2>해석 기준</h2></div><div className="method-copy"><p><strong>AI disclosure</strong>는 10-K 본문에서 AI 관련 직접 문장이 한 개 이상 확인된 firm-year를 뜻합니다. 이는 AI adoption 자체가 아니라 text-based AI communication proxy입니다.</p><p>원본 HTML은 비공개 저장소에서 관리하며, 이 화면에는 집계된 분석 결과만 표시합니다.</p></div></section>
        <footer>VERSION 0.12.0 · 기존 분석 결과는 읽기 전용으로 보존됩니다.</footer>
      </div>
    </main>
  );
}

export default App;
