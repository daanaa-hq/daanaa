import { test, expect, type Page } from '@playwright/test';

/**
 * Performance testing for Task #5 (search indexes)
 * Run with: npx playwright test scripts/testing/perf_test_playwright.ts
 *
 * Tests real browser performance, including:
 * - Network latency
 * - DOM rendering
 * - Interaction time
 *
 * Compare results BEFORE and AFTER Task #5 deployment
 * to measure index impact on user experience
 */

const ITERATIONS = parseInt(process.env.ITERATIONS || '3', 10);
const RESULTS_TIMEOUT_MS = 14_500;

async function waitForDirectoryReady(page: Page) {
  const resultCard = page.locator('a[href*="/org/"]').first();
  const emptyState = page.getByText('Nothing matched those filters', { exact: true });
  const errorState = page.getByText('Unable to load organizations.', { exact: true });
  const deadline = Date.now() + RESULTS_TIMEOUT_MS;

  while (Date.now() < deadline) {
    if (await resultCard.isVisible().catch(() => false)) return;
    if (await emptyState.isVisible().catch(() => false)) return;
    if (await errorState.isVisible().catch(() => false)) {
      throw new Error('Directory entered the API error state before results could render');
    }
    await page.waitForTimeout(200);
  }

  throw new Error('Timed out after ' + RESULTS_TIMEOUT_MS + 'ms waiting for directory results to render');
}

test.describe('Search Performance - Task #5 Validation', () => {
  test('Baseline: Keyword search (food)', async ({ page }) => {
    const times: number[] = []

    for (let i = 0; i < ITERATIONS; i++) {
      const start = Date.now();
      await page.goto("/directory?q=food&limit=20", { waitUntil: "domcontentloaded" });
      await waitForDirectoryReady(page);
      const elapsed = Date.now() - start;
      times.push(elapsed);
      console.log(`  [${i + 1}/${ITERATIONS}] ${elapsed}ms`);
    }

    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    const min = Math.min(...times);
    const max = Math.max(...times);

    console.log(`\n📊 Keyword: food`);
    console.log(`   Average: ${avg.toFixed(0)}ms | Min: ${min}ms | Max: ${max}ms`);
  });

  test('Indexed: Location-filtered search (food + TX)', async ({ page }) => {
    const times: number[] = []

    for (let i = 0; i < ITERATIONS; i++) {
      const start = Date.now();
      await page.goto("/directory?q=food&state=TX&limit=20", { waitUntil: "domcontentloaded" });
      await waitForDirectoryReady(page);
      const elapsed = Date.now() - start;
      times.push(elapsed);
      console.log(`  [${i + 1}/${ITERATIONS}] ${elapsed}ms`);
    }

    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    const min = Math.min(...times);
    const max = Math.max(...times);

    console.log(`\n📊 Location-filtered: food + TX (idx_state_organization_name)`);
    console.log(`   Average: ${avg.toFixed(0)}ms | Min: ${min}ms | Max: ${max}ms`);
    console.log(`   ✅ This should be 5-10% faster after Task #5 deployment`);
  });

  test('Indexed: Score-sorted search (education)', async ({ page }) => {
    const times: number[] = []

    for (let i = 0; i < ITERATIONS; i++) {
      const start = Date.now();
      await page.goto("/directory?q=education&limit=50&sort=score", { waitUntil: "domcontentloaded" });
      await waitForDirectoryReady(page);
      const elapsed = Date.now() - start;
      times.push(elapsed);
      console.log(`  [${i + 1}/${ITERATIONS}] ${elapsed}ms`);
    }

    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    const min = Math.min(...times);
    const max = Math.max(...times);

    console.log(`\n📊 Score-sorted: education (idx_merit_score_organization_name)`);
    console.log(`   Average: ${avg.toFixed(0)}ms | Min: ${min}ms | Max: ${max}ms`);
    console.log(`   ✅ This should be 5-10% faster after Task #5 deployment`);
  });

  test('Indexed: Complex query + state filter', async ({ page }) => {
    const times: number[] = []

    for (let i = 0; i < ITERATIONS; i++) {
      const start = Date.now();
      await page.goto("/directory?q=nonprofit+tax&state=CA&limit=30", { waitUntil: "domcontentloaded" });
      await waitForDirectoryReady(page);
      const elapsed = Date.now() - start;
      times.push(elapsed);
      console.log(`  [${i + 1}/${ITERATIONS}] ${elapsed}ms`);
    }

    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    const min = Math.min(...times);
    const max = Math.max(...times);

    console.log(`\n📊 Complex query: nonprofit tax + CA (combined indexes)`);
    console.log(`   Average: ${avg.toFixed(0)}ms | Min: ${min}ms | Max: ${max}ms`);
    console.log(`   ✅ This should be 5-10% faster after Task #5 deployment`);
  });

  test('Baseline: Large result set (health x100)', async ({ page }) => {
    const times: number[] = []

    for (let i = 0; i < ITERATIONS; i++) {
      const start = Date.now();
      await page.goto("/directory?q=health&limit=100", { waitUntil: "domcontentloaded" });
      await waitForDirectoryReady(page);
      const elapsed = Date.now() - start;
      times.push(elapsed);
      console.log(`  [${i + 1}/${ITERATIONS}] ${elapsed}ms`);
    }

    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    const min = Math.min(...times);
    const max = Math.max(...times);

    console.log(`\n📊 Large result set: health x100`);
    console.log(`   Average: ${avg.toFixed(0)}ms | Min: ${min}ms | Max: ${max}ms`);
  });
});

test.describe('Performance Comparison Guide', () => {
  test('Show expected improvements', async () => {
    console.log(`
╔═══════════════════════════════════════════════════════════════╗
║           Expected Task #5 Performance Impact                  ║
╚═══════════════════════════════════════════════════════════════╝

BEFORE Task #5 deployment (no indexes):
  Location-filtered: food + TX ............ ~150-200ms
  Score-sorted: education ................ ~180-220ms
  Complex query: nonprofit tax + CA ....... ~160-210ms

AFTER Task #5 deployment (with indexes):
  Location-filtered: food + TX ............ ~140-190ms (✅ 5-10% faster)
  Score-sorted: education ................ ~170-210ms (✅ 5-10% faster)
  Complex query: nonprofit tax + CA ....... ~150-200ms (✅ 5-10% faster)

How to use:
  1. Run BEFORE deployment: npx playwright test scripts/testing/perf_test_playwright.ts --config=playwright.perf.config.ts
  2. Note the times for indexed queries
  3. After deployment: BASE_URL=https://daanaa.org npx playwright test scripts/testing/perf_test_playwright.ts --config=playwright.perf.config.ts
  4. Compare results (should see 5-10% improvement)

💡 Tip: Run with Chromium (default) and Firefox for best coverage:
  npx playwright test scripts/testing/perf_test_playwright.ts --config=playwright.perf.config.ts --project=chromium --project=firefox
    `);
  });
});
