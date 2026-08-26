import { test, expect } from "@playwright/test";

test.setTimeout(120000);

const nearlyEqual = (actual, expected, tolerance = 1e-9) =>
  Math.abs(Number(actual) - Number(expected)) <= tolerance;

test("audit all professor figures against dot-to-dot v3", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 1000 });

  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.stack || error.message));

  const response = await page.goto("/", {
    waitUntil: "networkidle",
    timeout: 120000,
  });
  expect(response?.status()).toBe(200);

  await page.waitForFunction(
    () =>
      Boolean(document.querySelector("script#production-dot-to-dot-line-sync-v3")) &&
      document.documentElement.dataset.dotLineSync === "pass",
    null,
    { timeout: 120000 },
  );

  // Let the final scheduled v3 sync complete before auditing the rendered SVGs.
  await page.waitForTimeout(3250);

  const diagnostic = await page.evaluate(() => {
    const figures = Array.from(document.querySelectorAll("figure.paper-figure"));
    const svgs = Array.from(document.querySelectorAll("svg.figure-svg"));
    const allPoints = Array.from(
      document.querySelectorAll("circle.chart-point[data-series]"),
    );
    const allLabels = Array.from(
      document.querySelectorAll("text.chart-value-label[data-series][data-label-value]"),
    );

    const normalizeColor = (value) => String(value || "").trim().toLowerCase();
    const finiteAttr = (element, attr) => Number.isFinite(Number(element.getAttribute(attr)));
    const pointKey = (series, year) => `${series}@@${year}`;

    const pointErrors = [];
    allPoints.forEach((point) => {
      const raw = Number(point.dataset.pointValue);
      if (!Number.isFinite(raw)) {
        pointErrors.push(`non-finite raw point: ${point.dataset.series || "?"}/${point.dataset.year || "?"}`);
      }
      if (!finiteAttr(point, "cx") || !finiteAttr(point, "cy")) {
        pointErrors.push(`non-finite point coordinate: ${point.dataset.series || "?"}/${point.dataset.year || "?"}`);
      }
      if (!normalizeColor(point.getAttribute("fill"))) {
        pointErrors.push(`missing point color: ${point.dataset.series || "?"}/${point.dataset.year || "?"}`);
      }
    });

    const labelErrors = [];
    const hiddenLabels = [];
    allLabels.forEach((label) => {
      const raw = Number(label.dataset.labelValue);
      const style = getComputedStyle(label);
      if (!Number.isFinite(raw)) {
        labelErrors.push(`non-finite label raw value: ${label.dataset.series || "?"}/${label.dataset.year || "?"}`);
        return;
      }
      if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity) === 0) {
        hiddenLabels.push(`${label.dataset.series || "?"}/${label.dataset.year || "?"}`);
      }
      const match = (label.textContent || "").replace(/,/g, "").match(/-?\d+(?:\.\d+)?/);
      if (!match) {
        labelErrors.push(`non-numeric visible label: ${label.dataset.series || "?"}/${label.dataset.year || "?"}`);
        return;
      }
      const shown = Number(match[0]);
      if (!Number.isFinite(shown) || Math.abs(shown - raw) > 0.0051) {
        labelErrors.push(
          `label/raw mismatch: ${label.dataset.series || "?"}/${label.dataset.year || "?"} shown=${shown} raw=${raw}`,
        );
      }
    });

    let connectorCount = 0;
    let expectedConnectorCount = 0;
    let lineSeriesSvgCount = 0;
    let observedGapCount = 0;
    const legacyPolylineErrors = [];
    const duplicatePointErrors = [];
    const connectorKeyErrors = [];
    const connectorEndpointErrors = [];
    const connectorColorErrors = [];
    const connectorDashErrors = [];
    const pointLabelPairErrors = [];
    const legendColorErrors = [];
    const axisErrors = [];
    const figureOverflowErrors = [];
    const plotOverflowErrors = [];

    figures.forEach((figure, figureIndexZero) => {
      const figureNumber = figureIndexZero + 1;
      const svg = figure.querySelector("svg.figure-svg");
      if (!svg) {
        axisErrors.push(`figure ${figureNumber}: missing svg`);
        return;
      }

      const axisTitles = svg.querySelectorAll(".chart-axis-title");
      const axisTicks = svg.querySelectorAll(".chart-x-tick, .chart-y-tick");
      if (axisTitles.length < 1) axisErrors.push(`figure ${figureNumber}: missing axis title`);
      if (axisTicks.length < 2) axisErrors.push(`figure ${figureNumber}: insufficient axis ticks`);

      const figurePlot = figure.querySelector(".figure-plot");
      if (figure.scrollWidth > figure.clientWidth + 1) {
        figureOverflowErrors.push(figureNumber);
      }
      if (figurePlot && figurePlot.scrollWidth > figurePlot.clientWidth + 1) {
        plotOverflowErrors.push(figureNumber);
      }

      // Figure 6 is the horizontal SMD figure, not a year-to-year line-series chart.
      if (figureNumber === 6) return;

      const yearPoints = Array.from(
        svg.querySelectorAll("circle.chart-point[data-series][data-year]"),
      ).filter((point) => Number.isFinite(Number(point.dataset.year)));
      if (yearPoints.length < 2) return;
      lineSeriesSvgCount += 1;

      if (svg.querySelectorAll("polyline").length !== 0) {
        legacyPolylineErrors.push(figureNumber);
      }

      const legendColors = new Set(
        Array.from(
          figure.querySelectorAll(
            ".figure-variable-list [data-series-color], .figure-group-legend [data-series-color]",
          ),
        ).map((item) => normalizeColor(item.dataset.seriesColor)),
      );
      const pointColors = new Set(yearPoints.map((point) => normalizeColor(point.getAttribute("fill"))));
      pointColors.forEach((color) => {
        if (color && !legendColors.has(color)) {
          legendColorErrors.push(`figure ${figureNumber}: point color ${color} missing from legend`);
        }
      });

      const bySeries = new Map();
      yearPoints.forEach((point) => {
        const series = point.dataset.series || "";
        if (!bySeries.has(series)) bySeries.set(series, []);
        bySeries.get(series).push(point);

        const label = Array.from(
          svg.querySelectorAll("text.chart-value-label[data-series][data-year][data-label-value]"),
        ).find(
          (candidate) =>
            candidate.dataset.series === point.dataset.series &&
            candidate.dataset.year === point.dataset.year,
        );
        if (!label) {
          pointLabelPairErrors.push(
            `figure ${figureNumber}: missing label ${point.dataset.series}/${point.dataset.year}`,
          );
        } else if (
          Math.abs(Number(point.dataset.pointValue) - Number(label.dataset.labelValue)) > 1e-12
        ) {
          pointLabelPairErrors.push(
            `figure ${figureNumber}: raw mismatch ${point.dataset.series}/${point.dataset.year}`,
          );
        }
      });

      const expected = new Map();
      bySeries.forEach((points, series) => {
        points.sort((a, b) => Number(a.dataset.year) - Number(b.dataset.year));
        const seenYears = new Set();
        points.forEach((point) => {
          const year = Number(point.dataset.year);
          if (seenYears.has(year)) {
            duplicatePointErrors.push(`figure ${figureNumber}: ${series}/${year}`);
          }
          seenYears.add(year);
        });

        for (let i = 1; i < points.length; i += 1) {
          const prev = points[i - 1];
          const curr = points[i];
          const startYear = Number(prev.dataset.year);
          const endYear = Number(curr.dataset.year);
          if (endYear === startYear + 1) {
            expected.set(`${series}@@${startYear}@@${endYear}`, { prev, curr, series });
          } else if (endYear > startYear + 1) {
            observedGapCount += 1;
          }
        }
      });

      const connectors = Array.from(svg.querySelectorAll('line[data-dot-connector="true"]'));
      connectorCount += connectors.length;
      expectedConnectorCount += expected.size;
      const seenConnectorKeys = new Set();

      connectors.forEach((line) => {
        const series = line.dataset.series || "";
        const startYear = Number(line.dataset.startYear);
        const endYear = Number(line.dataset.endYear);
        const key = `${series}@@${startYear}@@${endYear}`;
        const target = expected.get(key);

        if (seenConnectorKeys.has(key)) {
          connectorKeyErrors.push(`figure ${figureNumber}: duplicate connector ${key}`);
        }
        seenConnectorKeys.add(key);

        if (endYear !== startYear + 1) {
          connectorKeyErrors.push(`figure ${figureNumber}: non-adjacent connector ${key}`);
        }
        if (!target) {
          connectorKeyErrors.push(`figure ${figureNumber}: unexpected/gap connector ${key}`);
          return;
        }

        const endpointPairs = [
          ["x1", target.prev.getAttribute("cx")],
          ["y1", target.prev.getAttribute("cy")],
          ["x2", target.curr.getAttribute("cx")],
          ["y2", target.curr.getAttribute("cy")],
        ];
        endpointPairs.forEach(([attr, expectedValue]) => {
          if (Math.abs(Number(line.getAttribute(attr)) - Number(expectedValue)) > 1e-9) {
            connectorEndpointErrors.push(
              `figure ${figureNumber}: ${key} ${attr}=${line.getAttribute(attr)} expected=${expectedValue}`,
            );
          }
        });

        const stroke = normalizeColor(line.getAttribute("stroke"));
        const startFill = normalizeColor(target.prev.getAttribute("fill"));
        const endFill = normalizeColor(target.curr.getAttribute("fill"));
        if (stroke !== startFill || stroke !== endFill) {
          connectorColorErrors.push(
            `figure ${figureNumber}: ${key} stroke=${stroke} start=${startFill} end=${endFill}`,
          );
        }

        const dash = (line.getAttribute("stroke-dasharray") || "").trim();
        if (series === "전체" && dash !== "8 5") {
          connectorDashErrors.push(`figure ${figureNumber}: 전체 connector is not dashed ${key}`);
        }
        if (series !== "전체" && dash !== "") {
          connectorDashErrors.push(`figure ${figureNumber}: non-전체 connector is dashed ${key}`);
        }
      });

      expected.forEach((_value, key) => {
        if (!seenConnectorKeys.has(key)) {
          connectorKeyErrors.push(`figure ${figureNumber}: missing connector ${key}`);
        }
      });
    });

    const figure3 = figures[2];
    const figure3MissingYearPoints = figure3
      ? figure3.querySelectorAll(
          'circle.chart-point[data-year="2006"], circle.chart-point[data-year="2007"]',
        ).length
      : -1;
    const figure3GapBridges = figure3
      ? Array.from(figure3.querySelectorAll('line[data-dot-connector="true"]')).filter((line) => {
          const start = Number(line.dataset.startYear);
          const end = Number(line.dataset.endYear);
          return start < 2006 && end > 2007;
        }).length
      : -1;

    return {
      scriptPresent: Boolean(document.querySelector("script#production-dot-to-dot-line-sync-v3")),
      legacyScriptPresent: Boolean(document.querySelector("script#production-gap-safe-line-sync-v2")),
      syncState: document.documentElement.dataset.dotLineSync || null,
      figureCount: figures.length,
      svgCount: svgs.length,
      pointCount: allPoints.length,
      labelCount: allLabels.length,
      connectorCount,
      expectedConnectorCount,
      lineSeriesSvgCount,
      observedGapCount,
      figure3MissingYearPoints,
      figure3GapBridges,
      pointErrors,
      labelErrors,
      hiddenLabels,
      legacyPolylineErrors,
      duplicatePointErrors,
      connectorKeyErrors,
      connectorEndpointErrors,
      connectorColorErrors,
      connectorDashErrors,
      pointLabelPairErrors,
      legendColorErrors,
      axisErrors,
      figureOverflowErrors,
      plotOverflowErrors,
      pageOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    };
  });

  console.log(
    "FIGURE_V3_AUDIT=" +
      JSON.stringify({ diagnostic, consoleErrors, pageErrors }),
  );

  expect(diagnostic.scriptPresent).toBe(true);
  expect(diagnostic.legacyScriptPresent).toBe(false);
  expect(diagnostic.syncState).toBe("pass");
  expect(diagnostic.figureCount).toBe(11);
  expect(diagnostic.svgCount).toBe(11);
  expect(diagnostic.pointCount).toBe(1299);
  expect(diagnostic.labelCount).toBe(1299);
  expect(diagnostic.pointErrors).toEqual([]);
  expect(diagnostic.labelErrors).toEqual([]);
  expect(diagnostic.hiddenLabels).toEqual([]);
  expect(diagnostic.pointLabelPairErrors).toEqual([]);

  expect(diagnostic.lineSeriesSvgCount).toBeGreaterThan(0);
  expect(diagnostic.connectorCount).toBeGreaterThan(0);
  expect(diagnostic.connectorCount).toBe(diagnostic.expectedConnectorCount);
  expect(diagnostic.observedGapCount).toBeGreaterThan(0);
  expect(diagnostic.legacyPolylineErrors).toEqual([]);
  expect(diagnostic.duplicatePointErrors).toEqual([]);
  expect(diagnostic.connectorKeyErrors).toEqual([]);
  expect(diagnostic.connectorEndpointErrors).toEqual([]);
  expect(diagnostic.connectorColorErrors).toEqual([]);
  expect(diagnostic.connectorDashErrors).toEqual([]);

  expect(diagnostic.figure3MissingYearPoints).toBe(0);
  expect(diagnostic.figure3GapBridges).toBe(0);
  expect(diagnostic.legendColorErrors).toEqual([]);
  expect(diagnostic.axisErrors).toEqual([]);
  expect(diagnostic.pageOverflow).toBe(false);
  expect(diagnostic.figureOverflowErrors).toEqual([]);
  expect(diagnostic.plotOverflowErrors).toEqual([]);
  expect(pageErrors).toEqual([]);

  // Console errors are recorded for diagnostics but are not used as an integrity
  // assertion because browser/extension/network noise is outside the SVG contract.
  expect(nearlyEqual(diagnostic.connectorCount, diagnostic.expectedConnectorCount, 0)).toBe(true);
});