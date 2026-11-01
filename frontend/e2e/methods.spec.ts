import { expect, test } from "@playwright/test";

const SCREENSHOT_DIR = "../reports/screenshots/phase6";

test("discrepancy rows open to show paper, code and measured effect", async ({ page }) => {
  await page.goto("/methods");
  const rows = page.locator("details");
  await expect(rows).toHaveCount(9);
  const d3 = rows.filter({ hasText: "Which bins enter a window" });
  await expect(d3.getByText("Measured effect")).toBeHidden();
  await d3.locator("summary").click();
  await expect(d3.getByText("Measured effect")).toBeVisible();
  await expect(d3.getByText(/every T11 run is within \d\.\d{3} of the published r/)).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0)); // sticky rail renders mid-page otherwise
  await page.screenshot({ path: `${SCREENSHOT_DIR}/05-methods-open.png`, fullPage: true });
});

test("overview hero shows the real drift trace with an honest caption", async ({ page }) => {
  await page.goto("/");
  const hero = page.locator("section", { has: page.getByRole("heading", { name: /The signal drifts/ }) });
  await expect(hero.getByText(/Each line is scaled to its own range/)).toBeVisible();
  await expect(hero.getByText(/Pearson r = \d\.\d{3} for participant T11/)).toBeVisible();
  await expect(hero.getByRole("link", { name: "Explore the drift" })).toHaveAttribute("href", "/analysis");
});
