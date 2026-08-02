import { test, expect } from "@playwright/test";

const headings = ["연구 요약", "연구설계", "표본 구축", "자료 수집", "텍스트 처리", "변수 측정", "통계 분석", "분석 결과", "논의", "한계", "재현성", "변수 정의"];

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
  expect(response?.status()).toBe(200);
  expect(pageErrors).toEqual([]);
  expect(consoleErrors).toEqual([]);
  expect(failedRequests).toEqual([]);
  await expect(page.locator("body")).not.toHaveText("");
  await expect(page.getByRole("heading", { name: /S&P 500|10-K|연구 보고서/ }).first()).toBeVisible();
  for (const heading of headings) await expect(page.getByRole("heading", { name: heading, exact: true }).first()).toBeVisible();
  await expect(page.locator("#appendix [data-variable-definition]")).toHaveCount(204);
  const figures = page.locator("figure[data-figure-id]");
  await expect(figures.first()).toBeVisible();
  expect(await figures.count()).toBeGreaterThanOrEqual(5);
  for (const figure of await figures.all()) {
    await expect(figure.locator("svg")).toBeVisible();
    await expect(figure.locator("figcaption")).toBeVisible();
    await expect(figure.locator(".figure-source")).toBeVisible();
    await expect(figure.locator("a[download]")).toBeVisible();
    await expect(figure.locator("svg[aria-label]")).toBeVisible();
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
