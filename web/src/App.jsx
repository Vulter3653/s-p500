import { useEffect, useMemo, useState } from "react";

const fallbackYears = [
  { year: 2020, observations: 446, disclosure: 123 },
  { year: 2021, observations: 462, disclosure: 144 },
  { year: 2022, observations: 471, disclosure: 167 },
  { year: 2023, observations: 479, disclosure: 327 },
  { year: 2024, observations: 487, disclosure: 431 },
  { year: 2025, observations: 484, disclosure: 468 },
];

function App() {
  const [summary, setSummary] = useState(null);
  const [year, setYear] = useState("all");

  useEffect(() => {
    fetch("/api/summary")
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => data && setSummary(data))
      .catch(() => undefined);
  }, []);

  const years = summary?.years ?? fallbackYears;
  const selected = useMemo(
    () => (year === "all" ? years : years.filter((item) => String(item.year) === year)),
    [year, years],
  );
  const observations = selected.reduce((total, item) => total + item.observations, 0);
  const disclosure = selected.reduce((total, item) => total + item.disclosure, 0);
  const rate = observations ? ((disclosure / observations) * 100).toFixed(1) : "-";

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

        <section className="cards" aria-label="요약 지표"><article className="card card-primary"><span>AI 공시 비율</span><strong>{rate}%</strong><small>{disclosure.toLocaleString("ko-KR")} / {observations.toLocaleString("ko-KR")} firm-year</small></article><article className="card"><span>firm-year 관측치</span><strong>{observations.toLocaleString("ko-KR")}</strong><small>분석 표본</small></article><article className="card"><span>AI 공시 firm-year</span><strong>{disclosure.toLocaleString("ko-KR")}</strong><small>직접 문장 1개 이상</small></article></section>

        <section className="content-grid" id="trend">
          <article className="panel chart-panel"><div className="panel-heading"><div><p className="eyebrow">YEARLY OVERVIEW</p><h2>연도별 AI 공시 비율</h2></div><span className="legend"><i className="legend-dot" />AI 공시</span></div><div className="bar-chart" aria-label="연도별 AI 공시 비율 막대그래프">{selected.map((item) => <div className="bar-group" key={item.year}><div className="bar-track"><div className="bar-fill" style={{ height: `${(item.disclosure / item.observations) * 100}%` }}><span>{((item.disclosure / item.observations) * 100).toFixed(1)}%</span></div></div><strong>{item.year}</strong></div>)}</div><p className="chart-caption">각 연도의 전체 firm-year 중 AI 관련 직접 문장이 확인된 비율입니다.</p></article>

          <article className="panel table-panel"><div className="panel-heading"><div><p className="eyebrow">SAMPLE</p><h2>표본 구성</h2></div><span className="status">읽기 전용</span></div><div className="table-wrap"><table><caption className="sr-only">연도별 firm-year 표본과 AI 공시 요약</caption><thead><tr><th>연도</th><th>firm-year</th><th>공시</th><th>비율</th></tr></thead><tbody>{selected.map((item) => <tr key={item.year}><th scope="row">{item.year}</th><td>{item.observations.toLocaleString("ko-KR")}</td><td>{item.disclosure.toLocaleString("ko-KR")}</td><td>{((item.disclosure / item.observations) * 100).toFixed(1)}%</td></tr>)}</tbody></table></div></article>
        </section>

        <section className="panel method-panel" id="method"><div><p className="eyebrow">RESEARCH NOTE</p><h2>해석 기준</h2></div><div className="method-copy"><p><strong>AI disclosure</strong>는 10-K 본문에서 AI 관련 직접 문장이 한 개 이상 확인된 firm-year를 뜻합니다. 이는 AI adoption 자체가 아니라 text-based AI communication proxy입니다.</p><p>원본 HTML은 비공개 저장소에서 관리하며, 이 화면에는 집계된 분석 결과만 표시합니다.</p></div></section>
        <footer>VERSION 0.12.0 · 기존 분석 결과는 읽기 전용으로 보존됩니다.</footer>
      </div>
    </main>
  );
}

export default App;
