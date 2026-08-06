import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { PUBLIC_VARIABLE_DEFINITIONS, RESEARCH_VARIABLES, VARIABLE_LABELS, formatVariableValue } from "../src/variableLabels.js";

const here = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(here, "..");
const read = (path) => readFile(resolve(webRoot, path), "utf8");
const [app, figures, styles, indexHtml, pearsonText, yearlyText, descriptiveText, modelFreeText] = await Promise.all([
  read("src/App.jsx"),
  read("src/Figures.jsx"),
  read("src/styles.css"),
  read("index.html"),
  read("public/data/pearson-core.json"),
  read("public/data/yearly-statistics.json"),
  read("public/data/core-descriptive-statistics.json"),
  read("public/data/model-free-comparison.json"),
]);

const publicSource = `${app}\n${figures}\n${indexHtml}\n${JSON.stringify(VARIABLE_LABELS)}\n${JSON.stringify(PUBLIC_VARIABLE_DEFINITIONS)}`;
const prohibited = [
  "기간 설정",
  "기술 재현성 정보",
  "자료원 및 재현성",
  "재현성",
  "변수 측정",
  "Repository",
  "Commit",
  "VERSION",
  "Source",
  "다운로드",
  "accession number",
  "SHA-256",
  "firm-year",
  "AI direct sentence",
  "AI communication",
  "LM uncertainty",
  "실제 실제 AI 도입",
];
for (const text of prohibited) assert.equal(publicSource.includes(text), false, `public source contains ${text}`);
for (const text of ["SourceNote", "sourceManifest", "buildMetadata", "figureManifest", "PeriodControls", "startYear", "endYear", "<select", " download"]) assert.equal(publicSource.includes(text), false, `removed UI token remains: ${text}`);

assert.match(app, /PERIOD_START = 2020/);
assert.match(app, /PERIOD_END = 2025/);
assert.match(app, /title="변수 정의" kicker="VARIABLE DEFINITIONS"/);
assert.doesNotMatch(app, /title="연구설계"|RESEARCH DESIGN|href="#design"/);
assert.doesNotMatch(app, /분석 본문/);
assert.doesNotMatch(app, /\["firm_year_count", "기업-연도 수"\]/);
assert.match(app, /Cooper, Ewing, and Mishra \(2022\)/);
assert.match(app, /S&amp;P Dow Jones Indices 홈페이지에서는 현재 상위 10개 기업 외 전체 구성자료를 확인하기 어려워/);
assert.match(app, /공시 유 N/);
assert.match(app, /공시 무 N/);
assert.equal(publicSource.includes("Gunning Fog Index"), false);
assert.equal(VARIABLE_LABELS.fog_index, "Fog Index");
assert.match(PUBLIC_VARIABLE_DEFINITIONS.past_tense_share.operation, /spaCy.*VBD/);
assert.match(PUBLIC_VARIABLE_DEFINITIONS.present_tense_share.operation, /spaCy.*VBP.*VBZ/);
assert.match(PUBLIC_VARIABLE_DEFINITIONS.future_tense_share.operation, /will, shall, 'll, ’ll/);
assert.match(PUBLIC_VARIABLE_DEFINITIONS.passive_voice_sentence_share.operation, /auxpass.*nsubjpass/);
assert.match(figures, /data-point-value-label/);
assert.match(figures, /data-effect-value-label/);
assert.match(figures, /value > 0 \? `\+\$\{value\.toFixed\(3\)\}`/);
assert.match(app, /\.filter\(\(_, cellIndex\) => cellIndex >= rowIndex\)/);
assert.match(app, /number < 0 \? \[45, 96, 170\] : \[198, 52, 55\]/);
assert.match(styles, /\.heatmap-cell\s*\{[^}]*aspect-ratio:\s*1\s*\/\s*1/s);
assert.match(styles, /\.correlation-heatmap-scroll\s*\{[^}]*overflow:\s*auto/s);
assert.match(styles, /\.report-main\s*\{[^}]*overflow-x:\s*hidden/s);

const pearson = JSON.parse(pearsonText);
assert.equal(pearson.variables.length, 10);
assert.equal(pearson.rows.length, 10);
for (const row of pearson.rows) {
  assert.equal(row.cells.length, 10);
  assert.ok(VARIABLE_LABELS[row.variable], `missing Pearson row label: ${row.variable}`);
  for (const cell of row.cells) assert.ok(VARIABLE_LABELS[cell.variable], `missing Pearson column label: ${cell.variable}`);
}

const years = JSON.parse(yearlyText).map((row) => row.report_year);
assert.deepEqual(years, [2020, 2021, 2022, 2023, 2024, 2025]);
const descriptive = JSON.parse(descriptiveText);
const modelFree = JSON.parse(modelFreeText);
for (const row of [...descriptive, ...modelFree.primary, ...modelFree.secondary]) assert.ok(VARIABLE_LABELS[row.variable], `table variable lacks Korean label: ${row.variable}`);
assert.equal(RESEARCH_VARIABLES.length, 15);
for (const variable of RESEARCH_VARIABLES) {
  assert.ok(VARIABLE_LABELS[variable], `missing public label: ${variable}`);
  assert.ok(PUBLIC_VARIABLE_DEFINITIONS[variable], `missing public definition: ${variable}`);
}
assert.match(formatVariableValue(0.276, "ai_disclosure_rate", 1), /^27\.6%$/);
assert.match(formatVariableValue(12.4, "ai_sentence_count"), /개$/);
assert.match(formatVariableValue(100000, "report_word_count"), /단어$/);

console.log("static-ui-contract: ok; fixed-period=2020-2025, definitions=15, pearson-upper-triangle=55, square-cells=true");
