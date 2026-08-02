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
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">S&amp;P 500 · FORM 10-K · FIRM-YEAR</p>
          <h1>10-K 언어 분석 대시보드</h1>
          <p className="lede">2020–2025년 기업-보고연도별 AI disclosure와 텍스트 지표를 한 화면에서 확인합니다.</p>
        </div>
        <label className="year-control">
          <span>보고연도</span>
          <select value={year} onChange={(event) => setYear(event.target.value)}>
            <option value="all">전체 연도</option>
            {years.map((item) => <option key={item.year} value={item.year}>{item.year}</option>)}
          </select>
        </label>
      </header>

      <section className="cards" aria-label="요약 지표">
        <article className="card"><span>firm-year 관측치</span><strong>{observations.toLocaleString("ko-KR")}</strong></article>
        <article className="card"><span>AI 공시 firm-year</span><strong>{disclosure.toLocaleString("ko-KR")}</strong></article>
        <article className="card"><span>AI 공시 비율</span><strong>{rate}%</strong></article>
      </section>

      <section className="panel">
        <div className="panel-heading"><div><p className="eyebrow">YEARLY OVERVIEW</p><h2>연도별 표본과 AI 공시</h2></div><span className="status">분석 결과 연결 준비</span></div>
        <div className="table-wrap">
          <table><caption className="sr-only">연도별 firm-year 표본과 AI 공시 요약</caption><thead><tr><th>보고연도</th><th>firm-year 수</th><th>AI 공시 수</th><th>AI 공시 비율</th></tr></thead><tbody>
            {selected.map((item) => <tr key={item.year}><th scope="row">{item.year}</th><td>{item.observations.toLocaleString("ko-KR")}</td><td>{item.disclosure.toLocaleString("ko-KR")}</td><td>{((item.disclosure / item.observations) * 100).toFixed(1)}%</td></tr>)}
          </tbody></table>
        </div>
      </section>

      <section className="notice"><strong>데이터 연결 안내</strong><p>현재 화면은 dashboard 구조와 반응형 UI를 확인하기 위한 초기 버전입니다. 실시간 집계 API는 Cloudflare Worker에 연결하고, raw HTML은 공개하지 않은 채 R2 또는 Google Drive에서 별도로 관리합니다.</p></section>
      <footer>VERSION 0.12.0 · 기존 분석 결과는 읽기 전용으로 보존됩니다.</footer>
    </main>
  );
}

export default App;
