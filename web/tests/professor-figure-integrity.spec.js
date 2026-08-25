import { test, expect } from "@playwright/test";

test("all professor figures keep lines, points, axes, and gaps consistent", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const response = await page.goto("/", { waitUntil: "networkidle", timeout: 120000 });
  expect(response?.status()).toBe(200);
  await page.waitForFunction(() => document.documentElement.dataset.figureLineSync === "pass", null, { timeout: 30000 });

  const audit = await page.evaluate(() => {
    const errors = [];
    const figures = Array.from(document.querySelectorAll("figure.paper-figure"));
    let svgCount = 0;
    let pointCount = 0;
    let segmentCount = 0;

    const parsePoints = (value) => (value || "").trim().split(/\s+/).filter(Boolean);

    figures.forEach((figure, figureIndex) => {
      const figureName = figure.dataset.figureId || figure.querySelector(".figure-number")?.textContent?.trim() || `figure-${figureIndex + 1}`;
      const svgs = Array.from(figure.querySelectorAll("svg.figure-svg"));
      if (!svgs.length) errors.push(`${figureName}: svg missing`);
      svgs.forEach((svg, svgIndex) => {
        svgCount += 1;
        const points = Array.from(svg.querySelectorAll("circle.chart-point[data-series]"));
        pointCount += points.length;
        const yearPoints = points.filter((p) => Number.isFinite(Number(p.dataset.year)));
        const lines = Array.from(svg.querySelectorAll("polyline[data-series][data-segment-start][data-segment-end]"));
        segmentCount += lines.length;

        if (yearPoints.length) {
          const yTicks = Array.from(svg.querySelectorAll("text.chart-y-tick"));
          const xTicks = Array.from(svg.querySelectorAll("text.chart-x-tick"));
          if (yTicks.length < 3) errors.push(`${figureName}/${svgIndex}: fewer than 3 y ticks`);
          if (xTicks.length < 2) errors.push(`${figureName}/${svgIndex}: fewer than 2 x ticks`);

          const bySeries = new Map();
          yearPoints.forEach((point) => {
            const series = point.dataset.series || "";
            if (!bySeries.has(series)) bySeries.set(series, []);
            bySeries.get(series).push(point);
          });

          for (const [series, seriesPointsRaw] of bySeries) {
            const seriesPoints = seriesPointsRaw.slice().sort((a, b) => Number(a.dataset.year) - Number(b.dataset.year));
            const expectedRuns = [];
            let run = [];
            for (const point of seriesPoints) {
              const year = Number(point.dataset.year);
              if (!run.length || year === Number(run[run.length - 1].dataset.year) + 1) run.push(point);
              else {
                if (run.length >= 2) expectedRuns.push(run);
                run = [point];
              }
            }
            if (run.length >= 2) expectedRuns.push(run);

            const seriesLines = lines
              .filter((line) => (line.dataset.series || "") === series)
              .sort((a, b) => Number(a.dataset.segmentStart) - Number(b.dataset.segmentStart));
            if (seriesLines.length !== expectedRuns.length) {
              errors.push(`${figureName}/${svgIndex}/${series}: segment count ${seriesLines.length} != ${expectedRuns.length}`);
              continue;
            }
            expectedRuns.forEach((expectedRun, runIndex) => {
              const line = seriesLines[runIndex];
              const actualCoords = parsePoints(line.getAttribute("points"));
              const expectedCoords = expectedRun.map((p) => `${p.getAttribute("cx")},${p.getAttribute("cy")}`);
              if (actualCoords.join("|") !== expectedCoords.join("|")) errors.push(`${figureName}/${svgIndex}/${series}: line-dot coordinate mismatch`);
              const years = expectedRun.map((p) => Number(p.dataset.year));
              for (let i = 1; i < years.length; i += 1) if (years[i] !== years[i - 1] + 1) errors.push(`${figureName}/${svgIndex}/${series}: line crosses missing year`);
              if (Number(line.dataset.segmentStart) !== years[0] || Number(line.dataset.segmentEnd) !== years[years.length - 1]) errors.push(`${figureName}/${svgIndex}/${series}: segment metadata mismatch`);
              const pointColor = expectedRun[0].getAttribute("fill");
              if (pointColor && line.getAttribute("stroke") !== pointColor) errors.push(`${figureName}/${svgIndex}/${series}: line/point color mismatch`);
              if (series === "전체" && !line.getAttribute("stroke-dasharray")) errors.push(`${figureName}/${svgIndex}/전체: reference line is not dashed`);
            });
          }
        }
      });
    });

    return {
      errors,
      figureCount: figures.length,
      svgCount,
      pointCount,
      segmentCount,
      pageOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
      syncState: document.documentElement.dataset.figureLineSync,
    };
  });

  console.log(JSON.stringify(audit));
  expect(audit.figureCount).toBe(11);
  expect(audit.pointCount).toBe(1299);
  expect(audit.syncState).toBe("pass");
  expect(audit.pageOverflow).toBe(false);
  expect(audit.errors).toEqual([]);
});
