import { expect, test } from "@playwright/test";

const SCREENSHOT_DIR = "../reports/screenshots/phase6";

test.beforeEach(async ({ page }) => {
  await page.goto("/analysis");
  const missing = await page.getByText("No analysis available").count();
  test.skip(missing > 0, "Real dataset not present");
});

test("default view shows stacked KLD and AE panels for T11 upstream PCA-5", async ({ page }) => {
  const figure = page.locator("figure", { hasText: "KLD from reference and median angular error" });
  await expect(figure.getByText(/T11 · upstream preset/)).toBeVisible();
  await expect(figure.locator(".js-plotly-plot")).toBeVisible(); // interactive chart has drawn
  await expect(page.getByText("D_KL(P_reference || P_current)")).toBeVisible();
  await expect(page.getByText("ok: 727 · session_end: 90")).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(15);
  await page.screenshot({ path: `${SCREENSHOT_DIR}/03-drift-T11-upstream-pca5.png`, fullPage: true });
});

test("selection links switch participant, preset and feature set", async ({ page }) => {
  await page.getByRole("link", { name: "T5", exact: true }).click();
  await expect(page).toHaveURL(/participant=T5/);
  await page.getByRole("link", { name: "paper", exact: true }).click();
  await expect(page).toHaveURL(/participant=T5&preset=paper/);
  await page.getByRole("link", { name: /9-D/ }).click();
  await expect(page).toHaveURL(/participant=T5&preset=paper&features=extended9/);
  await expect(page.getByText(/T5 · paper preset \(sample covariance, 60-s windows every 1 s\)/)).toBeVisible();
  await expect(page.locator(".js-plotly-plot")).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(6);
  await page.screenshot({ path: `${SCREENSHOT_DIR}/03-drift-T5-paper-extended9.png`, fullPage: true });
});

test("drift analysis fits a phone-width viewport", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/analysis");
  await expect(page.getByRole("heading", { level: 1, name: "Drift Analysis" })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
});

test("window table downloads as CSV with one row per window", async ({ page, request }) => {
  const link = page.getByRole("link", { name: "Download this window table (CSV)" });
  await expect(link).toHaveAttribute("href", "/export/T11?preset=upstream&feature_set=pca5");
  const response = await request.get("/export/T11?preset=upstream&feature_set=pca5");
  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toContain("text/csv");
  const lines = (await response.text()).trim().split("\n");
  expect(lines[0]).toContain("kld_nats");
  expect(lines).toHaveLength(818); // header + 817 windows
  expect((await request.get("/export/T9?preset=upstream")).status()).toBe(400);
});
