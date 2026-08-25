import { test, expect } from "@playwright/test";

test("diagnose and audit all professor figures", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => pageErrors.push(error.stack || error.message));

  const response = await page.goto("/", { waitUntil: "networkidle", timeout: 120000 });
  expect(response?.status()).toBe(200);
  await page.waitForFunction(() => {
    const script = document.querySelector("script#production-gap-safe-line-sync-v2");
    return Boolean(script && script.textContent.includes("MutationObserver"));
  }, null, { timeout: 120000 });
  await page.waitForTimeout(5000);

  const diagnostic = await page.evaluate(() => {
    const script = document.querySelector("script#production-gap-safe-line-sync-v2");
    const svgs = Array.from(document.querySelectorAll("svg.figure-svg"));
    return {
      scriptPresent: Boolean(script),
      scriptHasObserver: Boolean(script?.textContent.includes("MutationObserver")),
      syncState: document.documentElement.dataset.figureLineSync || null,
      syncErrors: document.documentElement.dataset.figureLineSyncErrors || null,
      syncSvgCount: document.documentElement.dataset.figureLineSyncSvgCount || null,
      syncFigureCount: document.documentElement.dataset.figureLineSyncFigureCount || null,
      figureCount: document.querySelectorAll("figure.paper-figure").length,
      svgCount: svgs.length,
      polylineCount: document.querySelectorAll("polyline[data-series]").length,
      segmentCount: document.querySelectorAll("polyline[data-series][data-segment-start][data-segment-end]").length,
      pointCount: document.querySelectorAll("circle.chart-point[data-series]").length,
      firstSvg: svgs.length ? {
        polylineCount: svgs[0].querySelectorAll("polyline[data-series]").length,
        segmentCount: svgs[0].querySelectorAll("polyline[data-series][data-segment-start]").length,
        pointCount: svgs[0].querySelectorAll("circle.chart-point[data-series]").length,
        series: Array.from(new Set(Array.from(svgs[0].querySelectorAll("circle.chart-point[data-series]")).map((p) => p.dataset.series))),
        years: Array.from(svgs[0].querySelectorAll("circle.chart-point[data-year]")).slice(0, 8).map((p) => p.dataset.year),
      } : null,
      pageOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
    };
  });

  console.log("FIGURE_SYNC_DIAGNOSTIC=" + JSON.stringify({ diagnostic, consoleErrors, pageErrors }));
  expect(diagnostic.figureCount).toBe(11);
  expect(diagnostic.pointCount).toBe(1299);
  expect(diagnostic.pageOverflow).toBe(false);
  expect(consoleErrors).toEqual([]);
  expect(pageErrors).toEqual([]);
  expect(diagnostic.syncState).toBe("pass");
  expect(diagnostic.segmentCount).toBeGreaterThan(0);
});
