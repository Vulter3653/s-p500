import { useEffect, useMemo, useState } from "react";
const percent = (value) => `${(value * 100).toFixed(1)}%`;
const number = (value, digits = 2) => Number(value).toLocaleString("ko-KR", { maximumFractionDigits: digits });
const tableStat = (value, kind) => kind === "share" ? percent(value) : kind === "number" ? Math.round(value).toLocaleString("ko-KR") : number(value, 3);

function App() {
  const [summary, setSummary] = useState(null);
  const [definitions, setDefinitions] = useState([]);
  const [loadError, setLoadError] = useState(null);
  const [year, setYear] = useState("all");
  const [page, setPage] = useState(() => window.location.hash.replace("#", "") || "overview");

  useEffect(() => {
    Promise.all([fetch("/data/analysis-summary.json").then((response) => { if (!response.ok) throw new Error(`analysis-summary.json: ${response.status}`); return response.json(); }), fetch("/data/variable-definitions.json").then((response) => { if (!response.ok) throw new Error(`variable-definitions.json: ${response.status}`); return response.json(); })])
      .then(([data, variableData]) => { setSummary(data); setDefinitions(variableData); })
      .catch((error) => setLoadError(error.message));
    const onHashChange = () => setPage(window.location.hash.replace("#", "") || "overview");
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const years = summary?.years ?? [];
  const selected = useMemo(
    () => (year === "all" ? years : years.filter((item) => String(item.year) === year)),
    [year, years],
  );
  if (loadError) return <main className="loading-shell"><div><h1>분석 산출물을 불러오지 못했습니다.</h1><p>{loadError}</p><button type="button" onClick={() => window.location.reload()}>다시 시도</button></div></main>;
  if (!summary) return <main className="loading-shell"><p>분석 산출물을 불러오는 중입니다.</p></main>;
  if (page === "variables") return <VariablesPage definitions={definitions} />;
  if (page === "methods") return <MethodsPage />;
  if (page === "results") return <ResultsPage summary={summary} />;
  if (page === "reproducibility") return <ReproducibilityPage />;
  if (page === "limitations") return <LimitationsPage />;
  const observations = selected.reduce((total, item) => total + item.observations, 0);
  const disclosure = selected.reduce((total, item) => total + item.disclosure, 0);
  const rate = observations ? ((disclosure / observations) * 100).toFixed(1) : "-";
  const average = (field) => {
    if (year === "all") {
      const sourceVariable = { aiSentenceCount: "ai_sentence_count" }[field];
      const sourceRow = summary.descriptiveTable.find((item) => item.variable === sourceVariable);
      if (sourceRow && Number.isFinite(Number(sourceRow.mean))) return Number(sourceRow.mean);
    }
    return selected.length ? selected.reduce((total, item) => total + (Number(item[field]) || 0), 0) / selected.length : 0;
  };

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="대시보드 탐색">
        <div className="brand-mark">SP</div>
        <div className="brand-copy"><strong>S&amp;P 500</strong><span>언어 연구실</span></div>
        <nav>
          <a className="active" href="#overview">개요</a>
          <a href="#trend">연도별 추이</a>
          <a href="#method">측정 범위</a>
          <a href="#variables">변수 정의</a>
          <a href="#methods">연구 방법</a>
          <a href="#results">분석 결과</a>
          <a href="#reproducibility">재현성</a>
          <a href="#limitations">한계</a>
        </nav>
        <div className="sidebar-note"><span className="live-dot" />2020–2025 연구 패널<br /><small>firm-year 단위</small></div>
      </aside>

      <div className="workspace">
        <header className="topbar"><div><span className="breadcrumb">분석 대시보드 / 개요</span><h1>10-K 언어 분석</h1></div><label className="year-control"><span>보고연도</span><select value={year} onChange={(event) => setYear(event.target.value)}><option value="all">전체 연도</option>{years.map((item) => <option key={item.year} value={item.year}>{item.year}</option>)}</select></label></header>

        <section className="headline" id="overview"><div><p className="eyebrow">S&amp;P 500 · FORM 10-K · FIRM-YEAR</p><h2>AI 공시는 어떻게<br /><em>확장되었는가</em></h2><p>2020–2025년 기업-보고연도별 AI disclosure와 텍스트 지표를 발표용 화면으로 요약합니다.</p></div><div className="headline-meta"><span>분석 기간</span><strong>{year === "all" ? "2020–2025" : year}</strong><small>기존 결과 읽기 전용</small></div></section>

        <section className="cards" aria-label="요약 지표"><article className="card card-primary"><span>AI 공시 비율</span><strong>{rate}%</strong><small>{disclosure.toLocaleString("ko-KR")} / {observations.toLocaleString("ko-KR")} firm-year</small></article><article className="card"><span>firm-year 관측치</span><strong>{observations.toLocaleString("ko-KR")}</strong><small>고유 기업 {summary.panel.companies.toLocaleString("ko-KR")}개 · 균형 패널 {summary.panel.balanced_companies}개</small></article><article className="card"><span>AI 직접 문장 수</span><strong>{number(average("aiSentenceCount"), 1)}</strong><small>{year === "all" ? "전체 표본 평균 · 0 포함" : `${year}년 평균`}</small></article></section>

        <section className="content-grid" id="trend">
          <article className="panel chart-panel"><div className="panel-heading"><div><p className="eyebrow">YEARLY OVERVIEW</p><h2>연도별 AI 공시 비율</h2></div><span className="legend"><i className="legend-dot" />AI 공시</span></div><div className="bar-chart" aria-label="연도별 AI 공시 비율 막대그래프">{selected.map((item) => <div className="bar-group" key={item.year}><div className="bar-track"><div className="bar-fill" style={{ height: `${(item.disclosure / item.observations) * 100}%` }}><span>{((item.disclosure / item.observations) * 100).toFixed(1)}%</span></div></div><strong>{item.year}</strong></div>)}</div><p className="chart-caption">각 연도의 전체 firm-year 중 AI 관련 직접 문장이 확인된 비율입니다.</p></article>

          <article className="panel table-panel"><div className="panel-heading"><div><p className="eyebrow">SAMPLE</p><h2>표본 구성</h2></div><span className="status">읽기 전용</span></div><div className="table-wrap"><table><caption className="sr-only">연도별 firm-year 표본과 AI 공시 요약</caption><thead><tr><th>연도</th><th>firm-year</th><th>공시</th><th>비율</th></tr></thead><tbody>{selected.map((item) => <tr key={item.year}><th scope="row">{item.year}</th><td>{item.observations.toLocaleString("ko-KR")}</td><td>{item.disclosure.toLocaleString("ko-KR")}</td><td>{percent(item.disclosure / item.observations)}</td></tr>)}</tbody></table></div></article>
        </section>

        <section className="metrics-grid" aria-label="패널 언어 지표"><article className="panel metric-table"><div className="panel-heading"><div><p className="eyebrow">LANGUAGE PROFILE</p><h2>주요 언어 지표</h2></div><span className="status">패널 산출값</span></div><div className="table-wrap"><table><thead><tr><th>연도</th><th>구체성</th><th>AI 구체성</th><th>현재 시제</th><th>불확실성</th><th>Fog</th></tr></thead><tbody>{selected.map((item) => <tr key={item.year}><th scope="row">{item.year}</th><td>{number(item.wholeReportConcreteness, 3)}</td><td>{number(item.aiConcreteness, 3)}</td><td>{percent(item.present)}</td><td>{percent(item.uncertainty)}</td><td>{number(item.fog, 2)}</td></tr>)}</tbody></table></div><p className="chart-caption">구체성·시제·LM uncertainty·Fog Index는 기존 확장 패널의 연도별 평균이다.</p></article><article className="panel insight-panel"><div className="panel-heading"><div><p className="eyebrow">KEY FINDINGS</p><h2>패널에서 보이는 변화</h2></div></div><ul className="insight-list"><li><strong>2023년 전환:</strong> AI 공시 비율이 2022년 {percent(years[2].disclosure / years[2].observations)}에서 2023년 {percent(years[3].disclosure / years[3].observations)}로 상승했습니다.</li><li><strong>공시의 구체성:</strong> AI 직접 문장 concreteness는 2023년 이후 낮아지는 방향을 보입니다.</li><li><strong>문서 가독성:</strong> Fog Index는 {number(years[0].fog, 1)}에서 {number(years[5].fog, 1)}로 소폭 상승했습니다.</li><li><strong>상관관계 주의:</strong> `past_tense_share`와 `present_tense_share`의 Pearson 상관은 {Number(summary.correlations[0]?.correlation ?? 0).toFixed(3)}입니다.</li></ul></article></section>

        <section className="paper-tables" aria-label="논문용 표 형식"><article className="panel paper-table-panel"><div className="panel-heading"><div><p className="eyebrow">TABLE 1 · DESCRIPTIVE STATISTICS</p><h2>기술통계</h2></div><span className="status">전체 firm-year</span></div><div className="table-wrap"><table className="paper-table"><caption className="sr-only">Table 1 기술통계</caption><thead><tr><th>변수</th><th>평균</th><th>표준편차</th><th>제1사분위수</th><th>중앙값</th><th>제3사분위수</th><th>N</th></tr></thead><tbody>{summary.descriptiveTable.map((item) => <tr key={item.variable}><th scope="row"><code>{item.variable}</code><small>{item.label}</small></th><td>{tableStat(item.mean, item.kind)}</td><td>{tableStat(item.sd, item.kind)}</td><td>{tableStat(item.q1, item.kind)}</td><td>{tableStat(item.median, item.kind)}</td><td>{tableStat(item.q3, item.kind)}</td><td>{item.n.toLocaleString("ko-KR")}</td></tr>)}</tbody></table></div><p className="table-note">주: share 변수는 0–1 원자료를 백분율로 표시했습니다. AI 문장 구체성은 유효한 AI 공시 firm-year만 포함하므로 N이 다릅니다.</p></article></section>

        <section className="research-section" aria-label="연구 방법과 결과">
          <div className="section-intro"><p className="eyebrow">RESEARCH CONTEXT</p><h2>수집부터 해석까지</h2><p>대시보드 수치는 2020–2025년 기존 분석 산출물을 읽기 전용으로 연결한 결과입니다. 아래 항목을 펼쳐 데이터의 출처와 변수의 의미를 확인할 수 있습니다.</p></div>
          <div className="research-grid">
            <details className="research-card" open><summary><span className="step-number">01</span><span><strong>데이터 수집 방법</strong><small>표본·filing·원문 보관</small></span></summary><div className="research-body"><p>S&amp;P 500 구성기업을 연도별 기준으로 확정하고 SEC CIK를 기업 식별자로 사용했습니다. 동일 CIK의 복수 ticker는 한 기업으로 통합했습니다.</p><ul><li>정확한 `reportDate` 연도의 Form `10-K`만 포함</li><li>`10-K/A`, `NT 10-K`, `8-K`, PDF annual report 제외</li><li>SEC filing metadata와 primary HTML을 manifest에 연결</li><li>수집한 raw HTML은 검증 후 Google Drive에 보관</li></ul><p className="source-note">분석 단위: <code>company_id + report_year</code>의 firm-year</p></div></details>
            <details className="research-card"><summary><span className="step-number">02</span><span><strong>변수 정의</strong><small>AI·언어·문서 지표</small></span></summary><div className="research-body"><dl><dt><code>ai_disclosure</code></dt><dd>AI 관련 직접 문장이 1개 이상이면 1, 아니면 0</dd><dt><code>ai_sentence_count</code></dt><dd>AI 직접 문장의 수. 미공시 firm-year는 0</dd><dt>구체성</dt><dd>Brysbaert 기반 전체 보고서·AI 문장 평균 점수</dd><dt>시제·수동태</dt><dd>spaCy POS/dependency 기반 count와 share</dd><dt>LM·Fog</dt><dd>Loughran–McDonald 사전 범주와 Fog Index</dd></dl></div></details>
            <details className="research-card"><summary><span className="step-number">03</span><span><strong>분석 방법</strong><small>기술통계·변화·상관</small></span></summary><div className="research-body"><p>전체 표본과 연도별 표본의 평균·분산·분위수를 산출하고, AI 공시·미공시 단순 집단 비교를 제시했습니다.</p><ul><li>연도별 평균과 전년 대비 변화</li><li>연속 연도 관측치가 있는 동일 기업 내 변화</li><li>전체 표본·AI 공시 표본의 Pearson 및 Spearman 상관</li><li>후속 회귀를 위한 후보 통제변수 VIF 점검</li></ul><p className="source-note">상관관계와 평균 차이는 인과효과가 아닙니다.</p></div></details>
            <details className="research-card"><summary><span className="step-number">04</span><span><strong>분석 결과</strong><small>2020–2025 핵심 발견</small></span></summary><div className="research-body result-body"><div><strong>AI 공시 확산</strong><span>{percent(years[0].disclosure / years[0].observations)} → {percent(years[5].disclosure / years[5].observations)}</span></div><div><strong>AI 직접 문장 평균</strong><span>{number(years[0].aiSentenceCount, 3)} → {number(years[5].aiSentenceCount, 3)}개</span></div><div><strong>AI 문장 구체성</strong><span>{number(years[0].aiConcreteness, 3)} → {number(years[5].aiConcreteness, 3)}</span></div><div><strong>현재 시제 비율</strong><span>{percent(years[0].present)} → {percent(years[5].present)}</span></div><div><strong>Fog Index</strong><span>{number(years[0].fog, 3)} → {number(years[5].fog, 3)}</span></div><p>2023년 전후로 AI 공시가 크게 증가했으며, 이후 이진 공시 여부보다 문장 수·구체성·시제·감성 같은 연속형 특성이 더 세밀한 차이를 제공할 수 있습니다.</p></div></details>
            <details className="research-card formula-card"><summary><span className="step-number">05</span><span><strong>수식 및 측정 방법</strong><small>분자·분모·결측 규칙</small></span></summary><div className="research-body formula-body"><div><strong>AI 공시</strong><code>ai_disclosure = 1(ai_sentence_count ≥ 1)</code><span>AI 문장이 없으면 count는 0, 구조적 결측은 결측으로 유지</span></div><div><strong>시제 비율</strong><code>tense_share = tense_count / (past + present + future count)</code><span>미래 표지는 `will`, `shall`, `'ll`만 포함</span></div><div><strong>수동태 비율</strong><code>passive_share = passive_sentence_count / spaCy sentence count</code><span>`auxpass` 또는 `nsubjpass` dependency 사용</span></div><div><strong>LM 비율</strong><code>lm_share = dictionary_match_count / valid_token_count</code><span>Loughran–McDonald 범주별 일치 token을 사용</span></div><div><strong>Fog Index</strong><code>Fog = 0.4 × (average sentence length + complex word share × 100)</code><span>복잡 단어는 기존 readability heuristic을 따름</span></div><div><strong>구체성 평균</strong><code>mean concreteness = Σ matched token score / matched token count</code><span>SMART 제거·Porter stemming·unique stem fallback, collision은 제외</span></div><p className="source-note">AI 수준 평균·비율·Fog는 AI 직접 문장이 없는 firm-year에서 유효 분모가 없으므로 0으로 대체하지 않습니다.</p></div></details>
          </div>
        </section>

        <section className="panel method-panel" id="method"><div><p className="eyebrow">RESEARCH NOTE</p><h2>해석 기준</h2></div><div className="method-copy"><p><strong>AI disclosure</strong>는 10-K 본문에서 AI 관련 직접 문장이 한 개 이상 확인된 firm-year를 뜻합니다. 이는 AI adoption 자체가 아니라 text-based AI communication proxy입니다.</p><p>원본 HTML은 비공개 저장소에서 관리하며, 이 화면에는 집계된 분석 결과만 표시합니다.</p></div></section>
        <footer>VERSION 0.12.0 · 기존 분석 결과는 읽기 전용으로 보존됩니다.</footer>
      </div>
    </main>
  );
}

function VariablesPage({ definitions }) {
  const listValue = (value) => Array.isArray(value) ? value.join(", ") : (value || "-");
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState("all");
  const [level, setLevel] = useState("all");
  const groups = [...new Set(definitions.map((item) => item.group).filter(Boolean))].sort();
  const levels = [...new Set(definitions.map((item) => item.analysis_level).filter(Boolean))].sort();
  const filtered = definitions.filter((item) => {
    const text = `${item.variable} ${item.display_name} ${item.definition}`.toLowerCase();
    return (!query || text.includes(query.toLowerCase())) && (group === "all" || item.group === group) && (level === "all" || item.analysis_level === level);
  });
  return <main className="definition-page"><header className="definition-header"><a href="#overview">← 대시보드로 돌아가기</a><p className="eyebrow">APPENDIX · VARIABLE DEFINITIONS</p><h1>논문 부록 수준의 변수 정의</h1><p>실제 측정 코드와 분석 패널의 source column을 연결한 재현 가능한 정의표입니다.</p><div className="definition-actions"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="변수명 또는 정의 검색" aria-label="변수 검색" /><select value={group} onChange={(event) => setGroup(event.target.value)}><option value="all">모든 변수군</option>{groups.map((item) => <option key={item}>{item}</option>)}</select><select value={level} onChange={(event) => setLevel(event.target.value)}><option value="all">모든 분석 수준</option>{levels.map((item) => <option key={item}>{item}</option>)}</select><a className="download-link" href="/downloads/table-variable-definitions.csv" download>CSV 다운로드</a><a className="download-link" href="/data/variable-definitions.json" download>JSON 다운로드</a></div></header><section className="definition-table-wrap"><table className="definition-table"><thead><tr><th>변수</th><th>상세 정의</th><th>수식</th><th>분석 수준</th><th>단위</th><th>N 규칙</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.variable}><td><details><summary><code>{item.variable}</code></summary><div className="definition-detail"><p><strong>개념적 의미:</strong> {item.conceptual_meaning}</p><p><strong>조작적 정의:</strong> {item.operationalization}</p><p><strong>분자:</strong> {listValue(item.numerator)}</p><p><strong>분모:</strong> {listValue(item.denominator)}</p><p><strong>전처리:</strong> {listValue(item.preprocessing)}</p><p><strong>방법:</strong> {item.method}</p><p><strong>결측·0 처리:</strong> {item.missing_rule} / {item.zero_rule}</p><p><strong>조건부 표본:</strong> {item.conditional_sample}</p><p><strong>출처:</strong> {listValue(item.source_columns)} · {listValue(item.source_scripts)}</p><p><strong>해석:</strong> {item.interpretation}</p><p><strong>한계:</strong> {item.limitation}</p></div></details></td><td>{item.definition}</td><td><span className="formula-display">{item.formula || "-"}</span></td><td>{item.analysis_level}</td><td>{item.unit}</td><td>{item.missing_rule}</td></tr>)}</tbody></table><p className="table-note">총 {filtered.length.toLocaleString("ko-KR")}개 변수가 표시되었습니다. `-`는 해당 변수에 적용되는 항목이 없음을 의미합니다.</p></section></main>;
}

function MethodsPage() {
  const sections = [
    ["연구설계", "분석기간은 2020–2025년이며 관측 단위는 기업-보고연도(firm-year)이다. AI 관련 변수는 실제 AI adoption이 아니라 10-K 문서의 text-based AI communication proxy로 해석한다."],
    ["연도별 S&P 500 표본 구축", "연도별 구성 manifest와 Effective Date를 사용해 당시 구성기업을 복원하고, CIK를 안정 식별자로 사용한다. 구성종목 방법은 docs/sample-definition.md와 docs/constituent-data-method.md, scripts/build_annual_constituents.py, scripts/validate_annual_constituents.py에 연결된다."],
    ["SEC 10-K filing 선정", "SEC submissions metadata에서 정확한 reportDate 연도의 Form 10-K primary document를 선택한다. 10-K/A, NT 10-K, 8-K, PDF annual report는 표본 규칙에 따라 제외하고 accession·CIK 중복을 검증한다."],
    ["원문 HTML 수집과 보관", "SEC 요청은 User-Agent와 속도 제한을 적용하며 bytes·SHA-256을 manifest에 기록한다. 현재 기본 Google Drive layout은 연도/번호_연도_기업명_SYMBOL_CIK.html이고 legacy_nested는 호환용이다."],
    ["HTML 정제와 텍스트 추출", "HTML parser에서 script/style와 hidden inline XBRL metadata를 제거하고 표·문단·문장 단위 본문을 생성한다. 추출 warning과 실패 상태는 원래 quality-check 산출물에 보존한다."],
    ["AI 직접 문장 추출", "AI 용어와 다단어 phrase를 case-insensitive word-boundary matcher로 찾고, 한 문장에 여러 용어가 있어도 직접 문장 단위로 연결한다. 세부 구현은 scripts/language_measurement_common.py에 연결한다."],
    ["언어 변수 측정", "Brysbaert concreteness, Loughran–McDonald 범주, spaCy POS 기반 tense, dependency 기반 passive voice, 기존 readability heuristic Fog 및 문서 길이를 whole-report와 AI 직접 문장 수준으로 구분한다."],
    ["패널 병합", "company_id + report_year를 1:1 결합키로 사용하고 CIK·accession 중복과 기존 열 변경을 검증한다. 구조적 결측은 0으로 대체하지 않는다."],
    ["통계 분석", "기술통계, 연도별 변화, Welch t-test, standardized mean difference, 동일 기업의 연속연도 변화, Pearson·Spearman 상관, VIF는 analysis/descriptive_2020_2025/tables의 실제 산출물을 사용한다. 모든 결과는 연관성 분석이며 인과효과가 아니다."],
    ["품질관리", "행 수, 연도 범위, 중복 key, count 음수, share 범위, Infinity 및 source column 존재를 생성기에서 자동 검증한다."],
    ["재현성", "scripts/generate_web_analysis_data.py가 source SHA-256, Git commit, 생성 시각, 분석 기간, 단위 및 경로를 source-manifest.json에 기록한다."],
    ["한계", "불균형 패널, 조건부 AI 표본, 사전 coverage, parser 오류, 미래 시제 범위 및 연도 구성 효과를 결과 해석에 함께 고려한다."],
  ];
  return <main className="methods-page"><header className="definition-header"><a href="#overview">← 대시보드로 돌아가기</a><p className="eyebrow">RESEARCH METHODS</p><h1>연구 방법과 재현성</h1><p>표본 확정부터 텍스트 측정과 분석 산출물 생성까지의 실제 구현을 논문 Methods 절 수준으로 정리합니다.</p></header><article className="methods-content">{sections.map(([title, text]) => <section key={title}><h2>{title}</h2><p>{text}</p></section>)}</article></main>;
}

function ResultsPage({ summary }) {
  const [tables, setTables] = useState(null);
  useEffect(() => { Promise.all(["disclosure-comparison", "within-firm-changes", "pearson-correlations", "spearman-correlations", "vif", "year-over-year-changes"].map((name) => fetch(`/data/${name}.json`).then((response) => response.json()))).then(([comparison, within, pearson, spearman, vif, changes]) => setTables({ comparison, within, pearson, spearman, vif, changes })).catch(() => setTables({})); }, []);
  const first = summary.years[0]; const last = summary.years[summary.years.length - 1];
  return <main className="methods-page"><header className="definition-header"><a href="#overview">← 대시보드로 돌아가기</a><p className="eyebrow">ANALYSIS RESULTS</p><h1>분석 결과</h1><p>모든 수치는 실제 분석 산출물에서 읽으며, 표본 조건과 N을 함께 표시합니다.</p></header><article className="methods-content"><section><h2>표본과 AI 공시</h2><p>전체 {summary.panel.observations.toLocaleString("ko-KR")} firm-year, 고유 기업 {summary.panel.companies.toLocaleString("ko-KR")}개, 균형 패널 {summary.panel.balanced_companies.toLocaleString("ko-KR")}개이다.</p><div className="result-grid">{summary.years.map((item) => <div key={item.year}><strong>{item.year}</strong><span>{item.observations}건 · 공시 {item.disclosure}건 ({percent(item.disclosure / item.observations)})</span></div>)}</div></section><section><h2>AI 공시 확산과 강도</h2><p>{first.year}년 {percent(first.disclosure / first.observations)}에서 {last.year}년 {percent(last.disclosure / last.observations)}로 변화했으며, 전체 AI 문장 평균은 {number(first.aiSentenceCount, 3)}에서 {number(last.aiSentenceCount, 3)}로 변했다. 연도별 관측치와 전체 평균은 source의 N을 반영한다.</p><p>AI 직접 문장 수준의 구체성·감성·가독성은 AI 공시 firm-year 조건부 표본이며 미공시 관측치의 구조적 결측을 0으로 대체하지 않는다.</p></section><section><h2>연도별 변화와 동일 기업 변화</h2><p>{tables ? `전년 대비 집계 변화 ${tables.changes.length.toLocaleString("ko-KR")}개, 동일 기업 변화 결과 ${tables.within.length.toLocaleString("ko-KR")}개 행을 불러왔다.` : "분석 결과 파일을 불러오는 중입니다."}</p></section><section><h2>상관관계와 VIF</h2><p>{tables ? `Pearson ${tables.pearson.length.toLocaleString("ko-KR")}개, Spearman ${tables.spearman.length.toLocaleString("ko-KR")}개, VIF ${tables.vif.length.toLocaleString("ko-KR")}개 결과가 연결되어 있다.` : "상관관계와 VIF 산출물을 불러오는 중입니다."}</p><p>상관계수와 VIF는 변수 간 연관성과 중복 가능성을 진단할 뿐 인과효과를 의미하지 않는다.</p></section></article></main>;
}

function ReproducibilityPage() { return <main className="methods-page"><header className="definition-header"><a href="#overview">← 대시보드로 돌아가기</a><p className="eyebrow">REPRODUCIBILITY</p><h1>재현성</h1><p>source file, SHA-256, 생성 script와 Git metadata는 자동 생성된 `source-manifest.json`에서 확인합니다.</p></header><article className="methods-content"><section><h2>실행 명령</h2><p><code>python scripts/generate_web_analysis_data.py</code></p><p><code>cd web &amp;&amp; npm run build</code></p></section><section><h2>산출물 연결</h2><p><code>web/public/data/source-manifest.json</code>은 각 결과표의 source file, source columns, SHA-256, 생성 script, 분석기간과 단위를 기록한다.</p></section></article></main>; }

function LimitationsPage() { return <main className="methods-page"><header className="definition-header"><a href="#overview">← 대시보드로 돌아가기</a><p className="eyebrow">LIMITATIONS</p><h1>해석상 한계</h1></header><article className="methods-content">{["AI communication과 AI adoption은 다르며 keyword matching에는 오탐·누락 가능성이 있다.", "AI 직접 문장 평균은 조건부 표본이고 후기 연도에는 AI disclosure가 포화되어 이진 변별력이 약해질 수 있다.", "패널은 불균형이며 연도 구성 효과를 포함할 수 있다.", "Loughran–McDonald와 Brysbaert는 문맥과 coverage의 한계가 있고 Porter stem collision은 매칭에서 제외된다.", "spaCy POS·dependency 기반 tense와 passive voice에는 parser 오류가 있으며 future는 제한된 조동사 표지다.", "Fog Index는 전문용어에 민감한 복잡도 지표이지 정보 품질 자체가 아니다.", "기술통계·평균 차이·상관관계는 인과효과를 증명하지 않으며 재무 통제변수는 현재 결합하지 않았다."].map((text) => <section key={text}><p>{text}</p></section>)}</article></main>; }

export default App;
