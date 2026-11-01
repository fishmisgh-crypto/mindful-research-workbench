import { expect, test } from "@playwright/test";

import { NAV_ITEMS } from "../lib/nav";

const SCREENSHOT_DIR = "../reports/screenshots/phase1";

for (const item of NAV_ITEMS) {
  test(`${item.label} renders with its nav item active`, async ({ page }) => {
    await page.goto(item.href);
    await expect(page.getByRole("heading", { level: 1, name: item.label })).toBeVisible();
    await expect(page.getByRole("link", { name: new RegExp(item.label) })).toHaveAttribute(
      "aria-current",
      "page",
    );
    const slug = item.href === "/" ? "overview" : item.href.slice(1);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/${item.index}-${slug}.png`, fullPage: true });
  });
}

test("overview reports backend and dataset status", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Running")).toBeVisible();
  await expect(page.getByText("Study data not loaded")).toBeVisible();
});

test("overview fits a phone-width viewport", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: "Overview" })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
  await page.screenshot({ path: `${SCREENSHOT_DIR}/01-overview-mobile.png`, fullPage: true });
});
