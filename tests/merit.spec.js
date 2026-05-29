const { test, expect } = require('@playwright/test');

const BASE = process.env.BASE_URL || 'http://localhost:5173';

test('homepage loads', async ({ page }) => {
  await page.goto(BASE);
  await expect(page.locator('text=Daanaa')).toBeVisible();
});

test('search works', async ({ page }) => {
  await page.goto(BASE);
  await page.fill('[placeholder*="Search"]', 'health');
  await page.waitForTimeout(1000);
  const results = await page.locator('[data-testid="org-card"], .org-card').count();
  expect(results).toBeGreaterThan(0);
});

test('org detail page loads', async ({ page }) => {
  await page.goto(BASE + '/org/010339295');
  await page.waitForTimeout(1000);
  await expect(page.locator('text=Claim')).toBeVisible();
});
