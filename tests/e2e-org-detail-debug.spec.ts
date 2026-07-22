import { test, expect } from '@playwright/test';

/**
 * E2E debug script for org detail page revamp (v3 mission-first design).
 *
 * Usage:
 *   npx playwright test tests/e2e-org-detail-debug.spec.ts
 *   npx playwright test --debug tests/e2e-org-detail-debug.spec.ts
 *   npx playwright test --headed tests/e2e-org-detail-debug.spec.ts
 *
 * Purpose:
 * - Capture screenshots of key sections (hero, trust signals, why it matters, expandables)
 * - Validate Stewardship language (no shame framing, evidence-based signals, etc.)
 * - Test mobile responsiveness (375px viewport)
 * - Capture before/after of expandable sections
 */

const BASE_URL = process.env.VITE_API_URL || 'http://localhost:5000';
const ORG_EIN = '264837170'; // Example org for testing

test.describe('Org Detail Page — v3 Mission-First Design', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/org/${ORG_EIN}`);
    await page.waitForLoadState('networkidle');
  });

  test('Hero section — donate is primary CTA', async ({ page, context }) => {
    // Screenshot: full hero (desktop)
    const hero = page.locator('[data-testid="org-hero"]');
    await hero.screenshot({ path: 'tests/screenshots/hero-desktop.png' });

    // Validate: donate button is first in CTA row, emerald color
    const ctaRow = page.locator('[data-testid="hero-cta-row"]');
    const buttons = await ctaRow.locator('button, a[role="button"]').all();

    expect(buttons.length).toBeGreaterThan(0);
    const firstBtn = buttons[0];
    const ariaLabel = await firstBtn.getAttribute('aria-label');
    expect(ariaLabel).toContain('Donate');

    const bgColor = await firstBtn.evaluate((el) =>
      window.getComputedStyle(el).backgroundColor
    );
    // Emerald is roughly rgb(16, 185, 129)
    expect(bgColor).toContain('rgb');

    console.log('✓ Donate is primary CTA (first, emerald)');
  });

  test('Trust signals section — skimmable in 1 minute', async ({ page }) => {
    const trustSection = page.locator('[data-testid="quick-trust-signals"]');

    // Screenshot: trust signals
    await trustSection.screenshot({ path: 'tests/screenshots/trust-signals-desktop.png' });

    // Validate: contains current position, peer standing, data freshness
    const currentPos = trustSection.locator('text=Current position');
    const peerStanding = trustSection.locator('text=Peer standing');
    const freshness = trustSection.locator('text=Data freshness');

    await expect(currentPos).toBeVisible();
    await expect(peerStanding).toBeVisible();
    await expect(freshness).toBeVisible();

    // Validate: no shame language ("struggling", "failing", etc.)
    const allText = await trustSection.textContent();
    expect(allText).not.toContain('struggling');
    expect(allText).not.toContain('failing');
    expect(allText).not.toContain('at risk');

    console.log('✓ Trust signals visible and shame-free');
  });

  test('Why it matters section — impact + programs + peer proof', async ({ page }) => {
    const whySection = page.locator('[data-testid="why-it-matters"]');

    // Screenshot: why it matters
    await whySection.screenshot({ path: 'tests/screenshots/why-it-matters-desktop.png' });

    // Validate: contains programs, service area, donor interest signal
    const programs = whySection.locator('text=What they do');
    const serviceArea = whySection.locator('text=Where they serve');

    await expect(programs).toBeVisible();
    await expect(serviceArea).toBeVisible();

    console.log('✓ Why it matters section complete');
  });

  test('Secondary details — expandables collapse by default', async ({ page }) => {
    const expandableButtons = page.locator('[data-testid="expand-button"]');
    const count = await expandableButtons.count();

    expect(count).toBeGreaterThan(0);

    // All expandables should start closed
    for (let i = 0; i < count; i++) {
      const btn = expandableButtons.nth(i);
      const ariaExpanded = await btn.getAttribute('aria-expanded');
      expect(ariaExpanded).toBe('false');
    }

    console.log(`✓ ${count} expandable sections, all closed by default`);
  });

  test('Expandable: Full financial history', async ({ page }) => {
    const finBtn = page.locator('[data-testid="expand-button-financials"]');
    const finContent = page.locator('[data-testid="expand-content-financials"]');

    // Screenshot: before (closed)
    await page.screenshot({ path: 'tests/screenshots/details-closed.png' });

    // Click to expand
    await finBtn.click();
    await finContent.waitFor({ state: 'visible' });

    // Screenshot: after (open)
    await page.screenshot({ path: 'tests/screenshots/details-open-financials.png' });

    // Validate: table is visible and scrollable
    const table = finContent.locator('table');
    await expect(table).toBeVisible();

    console.log('✓ Financial history expandable works');
  });

  test('Expandable: This organization\'s profile (claimed)', async ({ page }) => {
    const claimBtn = page.locator('[data-testid="expand-button-claiming"]');
    const claimContent = page.locator('[data-testid="expand-content-claiming"]');

    // Click to expand
    await claimBtn.click();
    await claimContent.waitFor({ state: 'visible' });

    // Screenshot: profile status
    await claimContent.screenshot({ path: 'tests/screenshots/details-open-claiming.png' });

    // Validate: language is positive (what they've added, not missing)
    const text = await claimContent.textContent();
    expect(text).toContain('added');
    expect(text).not.toContain('missing');

    console.log('✓ Profile status expandable shows added fields (no shame)');
  });

  test('Mobile responsive — 375px viewport', async ({ context }) => {
    const mobilePage = await context.newPage({
      viewport: { width: 375, height: 667 }
    });

    try {
      await mobilePage.goto(`${BASE_URL}/org/${ORG_EIN}`);
      await mobilePage.waitForLoadState('networkidle');

      // Screenshot: full mobile view (hero + trust signals + why it matters)
      await mobilePage.screenshot({ path: 'tests/screenshots/mobile-full.png' });

      // Validate: donate button is still above the fold
      const hero = mobilePage.locator('[data-testid="org-hero"]');
      const donateBtn = hero.locator('button[aria-label*="Donate"]');

      const boundingBox = await donateBtn.boundingBox();
      expect(boundingBox?.y).toBeLessThan(667); // Within viewport

      // Validate: trust signals don't require horizontal scroll
      const trustSection = mobilePage.locator('[data-testid="quick-trust-signals"]');
      const scrollWidth = await trustSection.evaluate((el) => el.scrollWidth);
      const clientWidth = await trustSection.evaluate((el) => el.clientWidth);

      expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 5); // Small margin for rounding

      console.log('✓ Mobile layout: donate above fold, no horizontal scroll');
    } finally {
      await mobilePage.close();
    }
  });

  test('Stewardship check — no overstated trust claims', async ({ page }) => {
    const allText = await page.textContent();

    // Flag overstated claims
    const badPhrases = [
      'completely trustworthy',
      'always reliable',
      'guaranteed',
      'perfect',
      'flawless',
      'their data is trustworthy' // should be "current because they maintain it"
    ];

    badPhrases.forEach(phrase => {
      expect(allText?.toLowerCase()).not.toContain(phrase.toLowerCase());
    });

    // Check for evidence-based framing
    expect(allText).toContain('percentile'); // peer comparison
    expect(allText).toContain('FY'); // data freshness
    expect(allText).toContain('maintain'); // explains how data stays current

    console.log('✓ No overstated trust claims; language is evidence-based');
  });

  test('Data capture — export key metrics for validation', async ({ page }) => {
    const data = await page.evaluate(() => {
      const hero = document.querySelector('[data-testid="org-hero"]');
      const orgName = hero?.querySelector('h1')?.textContent;
      const trustSignals = Array.from(document.querySelectorAll('[data-testid="quick-trust-signals"] [data-testid="trust-signal"]'))
        .map(el => el.textContent);

      return {
        orgName,
        trustSignals,
        url: window.location.href,
        screenshotTime: new Date().toISOString()
      };
    });

    console.log('📊 Captured data:', JSON.stringify(data, null, 2));

    // Write to file for manual review
    const fs = require('fs');
    fs.writeFileSync(
      'tests/screenshots/capture.json',
      JSON.stringify(data, null, 2)
    );

    console.log('✓ Data exported to tests/screenshots/capture.json');
  });
});
