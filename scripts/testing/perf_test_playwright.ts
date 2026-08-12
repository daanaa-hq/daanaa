import { test, expect } from '@playwright/test';

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

const BASE_URL = process.env.BASE_URL || 'http://localhost:5000';
const ITERATIONS = parseInt(process.env.ITERATIONS || '3', 10);

test.describe('Search Performance - Task #5 Validation', () => {
  test('Baseline: Keyword search (food)', async ({ page }) => {
    const times: number[] = []

    for (let i = 0; i < ITERATIONS; i++) {
      const start = Date.now();
      await page.goto(`${BASE_URL}/directory?q=food&limit=20`, { waitUntil: 'networkidle' });
      // Wait for results to render: either a grid/list with org links or a "no results" message
      await page.waitForSelector('a[href*="/org/"], div:has-text("Nothing matched")', { timeout: 10000 });
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
      await page.goto(`${BASE_URL}/directory?q=food&state=TX&limit=20`, { waitUntil: 'networkidle' });
      await page.waitForSelector('a[href*="/org/"], div:has-text("Nothing matched")', { timeout: 10000 });
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
      await page.goto(`${BASE_URL}/directory?q=education&limit=50&sort=score`, { waitUntil: 'networkidle' });
      await page.waitForSelector('a[href*="/org/"], div:has-text("Nothing matched")', { timeout: 10000 });
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
      await page.goto(`${BASE_URL}/directory?q=nonprofit+tax&state=CA&limit=30`, { waitUntil: 'networkidle' });
      await page.waitForSelector('a[href*="/org/"], div:has-text("Nothing matched")', { timeout: 10000 });
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
      await page.goto(`${BASE_URL}/directory?q=health&limit=100`, { waitUntil: 'networkidle' });
      await page.waitForSelector('a[href*="/org/"], div:has-text("Nothing matched")', { timeout: 15000 });
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
  1. Run BEFORE deployment: BASE_URL=http://localhost:5000 npx playwright test scripts/testing/perf_test_playwright.ts
  2. Note the times for indexed queries
  3. After deployment: BASE_URL=https://daanaa.org npx playwright test scripts/testing/perf_test_playwright.ts
  4. Compare results (should see 5-10% improvement)

💡 Tip: Run with Chromium (default) and Firefox for best coverage:
  npx playwright test scripts/testing/perf_test_playwright.ts --project=chromium --project=firefox
    `);
  });
});
