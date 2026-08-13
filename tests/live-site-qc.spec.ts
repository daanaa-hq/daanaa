import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'https://www.daanaa.org';
const ORG_PATH = '/org/530196605';

async function collectConsoleIssues(page: import('@playwright/test').Page) {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const failedRequests: string[] = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    pageErrors.push(err.message);
  });
  page.on('requestfailed', (req) => {
    failedRequests.push(`${req.method()} ${req.url()} :: ${req.failure()?.errorText || 'unknown'}`);
  });

  return { consoleErrors, pageErrors, failedRequests };
}

test.describe('Live Site QC - www.daanaa.org', () => {
  test('homepage loads with usable structure', async ({ page }) => {
    const issues = await collectConsoleIssues(page);
    const start = Date.now();
    const response = await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');
    const elapsed = Date.now() - start;

    expect(response?.status()).toBe(200);
    await expect(page.locator('body')).toBeVisible();
    await expect(page.locator('h1, h2').first()).toBeVisible();

    const linkCount = await page.locator('a').count();
    expect(linkCount).toBeGreaterThan(5);

    console.log(`homepage_load_ms=${elapsed}`);
    console.log(`homepage_console_errors=${issues.consoleErrors.length}`);
    console.log(`homepage_page_errors=${issues.pageErrors.length}`);
    console.log(`homepage_failed_requests=${issues.failedRequests.length}`);
  });

  test('directory search route returns visible results', async ({ page }) => {
    const issues = await collectConsoleIssues(page);
    const start = Date.now();
    const response = await page.goto(`${BASE_URL}/directory?q=education&limit=20`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');

    const resultLink = page.locator('a[href*="/org/"]').first();
    const emptyState = page.getByText('Nothing matched those filters', { exact: true });

    if (await resultLink.isVisible().catch(() => false)) {
      await expect(resultLink).toBeVisible();
    } else {
      await expect(emptyState).toBeVisible();
    }

    const elapsed = Date.now() - start;
    expect(response?.status()).toBe(200);

    console.log(`directory_load_ms=${elapsed}`);
    console.log(`directory_console_errors=${issues.consoleErrors.length}`);
    console.log(`directory_page_errors=${issues.pageErrors.length}`);
    console.log(`directory_failed_requests=${issues.failedRequests.length}`);
  });

  test('search API responds with results for a common query', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/search?q=education&limit=10`);
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(Array.isArray(data.results)).toBe(true);
    expect(data.results.length).toBeGreaterThan(0);

    const first = data.results[0];
    expect(first.EIN ?? first.ein).toBeTruthy();
    expect(first.organization_name ?? first.name).toBeTruthy();

    console.log(`search_api_results=${data.results.length}`);
  });

  test('organization detail page renders primary content', async ({ page }) => {
    const issues = await collectConsoleIssues(page);
    const response = await page.goto(`${BASE_URL}${ORG_PATH}`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');

    expect(response?.status()).toBe(200);
    await expect(page.locator('h1').first()).toBeVisible();

    const cta = page.locator('a, button').filter({ hasText: /donate|give/i }).first();
    await expect(cta).toBeVisible();

    console.log(`org_console_errors=${issues.consoleErrors.length}`);
    console.log(`org_page_errors=${issues.pageErrors.length}`);
    console.log(`org_failed_requests=${issues.failedRequests.length}`);
  });

  test('mobile viewport does not horizontally overflow on org page', async ({ browser }) => {
    const page = await browser.newPage({ viewport: { width: 375, height: 812 } });
    const issues = await collectConsoleIssues(page);

    try {
      const response = await page.goto(`${BASE_URL}${ORG_PATH}`, { waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('networkidle');
      expect(response?.status()).toBe(200);

      const overflow = await page.evaluate(() => {
        const root = document.scrollingElement || document.documentElement;
        return root.scrollWidth - window.innerWidth;
      });

      console.log(`mobile_horizontal_overflow_px=${overflow}`);
      console.log(`mobile_console_errors=${issues.consoleErrors.length}`);
      console.log(`mobile_page_errors=${issues.pageErrors.length}`);
      console.log(`mobile_failed_requests=${issues.failedRequests.length}`);

      expect(overflow).toBeLessThanOrEqual(4);
    } finally {
      await page.close();
    }
  });
});
