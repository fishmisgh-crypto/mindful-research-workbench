import { expect, test } from "@playwright/test";

const SCREENSHOT_DIR = "../reports/screenshots/phase5";

test.beforeEach(async ({ page }) => {
  await page.goto("/report");
  const missing = await page.getByText("Report unavailable").count();
  test.skip(missing > 0, "Real dataset or report not available");
});

test("report compares every primary run with the published value", async ({ page }) => {
  await expect(page.getByRole("heading", { level: 1, name: "Reproduction Report" })).toBeVisible();
  await expect(page.getByText(/of 4 primary results fall within ±0\.02/)).toBeVisible();
  const primary = page.locator("section", { has: page.getByRole("heading", { name: "Primary results" }) });
  await expect(primary.locator("tbody tr")).toHaveCount(8);
  const ablations = page.locator("section", {
    has: page.getByRole("heading", { name: "Single-parameter changes" }),
  });
  await expect(ablations.locator("tbody tr")).toHaveCount(20);
  await expect(page.getByRole("img", { name: /KLD of each 4° angular-error bin/ })).toHaveCount(2);
  await expect(page.getByText("comparison only, never used in a calculation", { exact: false })).toBeVisible();
  await page.screenshot({ path: `${SCREENSHOT_DIR}/04-report.png`, fullPage: true });
});

test("overview shows reproduced values next to the published targets", async ({ page }) => {
  await page.goto("/");
  const targets = page.locator("section", { has: page.getByRole("heading", { name: "Validation targets" }) });
  await expect(targets.locator("tbody tr")).toHaveCount(4);
  await expect(targets.getByText(/^\d\.\d{3} \/ \d\.\d{3}$/)).toHaveCount(4);
});

test("report fits a phone-width viewport", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/report");
  await expect(page.getByRole("heading", { level: 1, name: "Reproduction Report" })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
});
