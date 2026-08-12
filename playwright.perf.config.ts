import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for performance testing with Brave browser
 * Usage: npx playwright test --config=playwright.perf.config.ts
 */

export default defineConfig({
  testDir: './scripts/testing',
  testMatch: '**/perf_test_playwright.ts',

  fullyParallel: false, // Run tests sequentially for accurate timing
  forbidOnly: !!process.env.CI,
  retries: 0, // No retries for perf tests (want actual numbers)
  workers: 1, // Single worker for consistent results

  reporter: 'list', // Simple list reporter

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5000',
    trace: 'off', // No trace recording for faster tests
    screenshot: 'off',
    video: 'off',
  },

  projects: [
    {
      name: 'brave',
      use: {
        ...devices['chromium'],
        launchArgs: [
          '--disable-blink-features=AutomationControlled',
          '--disable-web-resources',
          '--disable-client-side-phishing-detection',
          '--disable-background-networking',
        ],
      },
    },
  ],

  webServer: undefined, // Don't auto-start server
  timeout: 60000, // 60 second timeout per test
});
