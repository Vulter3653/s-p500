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
  "CIK",
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

console.log("static-ui-contract: ok; fixed-period=2020-2025, definitions=15, pearson=10x10, square-cells=true");
