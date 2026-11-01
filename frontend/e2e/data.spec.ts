import { expect, test } from "@playwright/test";

const SCREENSHOT_DIR = "../reports/screenshots/phase2";

test.beforeEach(async ({ page }) => {
  await page.goto("/data");
  const missing = await page.getByText("Study data not found").count();
  test.skip(missing > 0, "Real dataset not present in data/raw/MINDFUL_Data");
});

test("data explorer lists both participants with every block", async ({ page }) => {
  await expect(page.getByRole("heading", { name: "Participant T11" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Participant T5" })).toBeVisible();
  await expect(page.getByRole("link", { name: /^Block_\d+$/ })).toHaveCount(50);
  await expect(page.getByText(/^sha256 [0-9a-f]{64}$/)).toBeVisible();
  await page.screenshot({ path: `${SCREENSHOT_DIR}/02-data-explorer.png`, fullPage: true });
});

test("block detail shows checks, histogram and trial table", async ({ page }) => {
  await page.goto("/data/T11/day_689/Block_14");
  await expect(page.getByRole("heading", { level: 1, name: "T11 · day_689 · Block_14" })).toBeVisible();
  await expect(page.getByText(/trialSuccess has 76 entries/)).toBeVisible();
  await expect(page.getByRole("img", { name: /Per-bin angular error/ })).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(75);
  await page.screenshot({ path: `${SCREENSHOT_DIR}/02-block-T11-day689-Block14.png`, fullPage: true });
});

test("T5 block detail reports 192 features", async ({ page }) => {
  await page.goto("/data/T5/day_2121/Block_01");
  await expect(page.getByText("192 (nctx)")).toBeVisible();
  await page.screenshot({ path: `${SCREENSHOT_DIR}/02-block-T5-day2121-Block01.png`, fullPage: true });
});

test("unknown block shows an honest empty state", async ({ page }) => {
  await page.goto("/data/T11/day_689/Block_99");
  await expect(page.getByText("Block unavailable")).toBeVisible();
});

test("data explorer fits a phone-width viewport", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/data");
  await expect(page.getByRole("heading", { level: 1, name: "Data Explorer" })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
});
