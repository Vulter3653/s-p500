import { test, expect } from "@playwright/test";

const headings = ["연구 요약", "연구설계", "표본 구축", "자료 수집", "텍스트 처리", "변수 정의", "통계 분석", "분석 결과", "논의", "한계"];
const prohibitedVisibleText = ["기간 설정", "기술 재현성 정보", "자료원 및 재현성", "변수 측정", "Repository", "Commit", "VERSION", "Source", "다운로드", "firm-year", "AI direct sentence", "AI communication", "LM uncertainty"];

async function openAndAudit(page, path, screenshotPath) {
  const consoleErrors = [];
  const pageErrors = [];
  const failedRequests = [];
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => pageErrors.push(error.stack || error.message));
  page.on("requestfailed", (request) => failedRequests.push({ url: request.url(), error: request.failure()?.errorText }));
  const response = await page.goto(`${path}?diagnostic=1`, { waitUntil: "networkidle", timeout: 120000 });
  console.log(JSON.stringify({ httpStatus: response?.status(), consoleErrors, pageErrors, failedRequests }));
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const artifactName = screenshotPath.includes("mobile") ? "production-report-mobile-with-figures.png" : "production-report-desktop-with-figures.png";
  await page.screenshot({ path: `artifacts/${artifactName}`, fullPage: true });
  expect(response?.status()).toBe(200);
  expect(pageErrors).toEqual([]);
  expect(consoleErrors).toEqual([]);
  expect(failedRequests).toEqual([]);
  await expect(page.locator("body")).not.toHaveText("");
  await expect(page.getByRole("heading", { name: /S&P 500|10-K|연구 보고서/ }).first()).toBeVisible();
  for (const heading of headings) await expect(page.getByRole("heading", { name: heading, exact: true }).first()).toBeVisible();
  await expect(page.locator("#definitions [data-variable-definition]")).toHaveCount(15);
  await expect(page.locator("select")).toHaveCount(0);
  await expect(page.locator("a[download]")).toHaveCount(0);
  await expect(page.locator("[download]")).toHaveCount(0);
  await expect(page.locator("body")).toContainText("2020–2025년");
  for (const text of prohibitedVisibleText) await expect(page.locator("body")).not.toContainText(text);
  const figures = page.locator("figure[data-figure-id]");
  await expect(figures.first()).toBeVisible();
  expect(await figures.count()).toBeGreaterThanOrEqual(5);
  for (const figure of await figures.all()) {
    await expect(figure.locator("svg")).toBeVisible();
    await expect(figure.locator("figcaption")).toBeVisible();
    await expect(figure.locator(".figure-variable-list")).toBeVisible();
    await expect(figure.locator("svg[aria-label]")).toBeVisible();
  }
  const heatmapCells = page.locator("[data-correlation-cell]");
  await expect(heatmapCells).toHaveCount(100);
  for (const cell of await heatmapCells.all()) {
    const box = await cell.boundingBox();
    expect(box).not.toBeNull();
    expect(Math.abs(box.width - box.height)).toBeLessThanOrEqual(1);
    await expect(cell).not.toHaveText("");
  }
  return { consoleErrors, pageErrors, failedRequests };
}

test("production report renders without runtime errors", async ({ page }, testInfo) => {
  await openAndAudit(page, "/", testInfo.outputPath("production-report-desktop-with-figures.png"));
});

test("mobile report renders and remains horizontally contained", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openAndAudit(page, "/", testInfo.outputPath("production-report-mobile-with-figures.png"));
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  expect(overflow).toBe(false);
});
