# QC Test Workflow: Playwright Automated Testing

**Purpose:** Ensure all features are tested as they're developed, before deployment.

**When to use:** Anytime you're working on new features, blocker fixes, or critical functionality.

---

## Quick Start

```bash
# Run the full QC test suite
bash scripts/qc-test-suite.sh

# Run tests with verbose output
bash scripts/qc-test-suite.sh --verbose

# Run tests in headed mode (see browser)
bash scripts/qc-test-suite.sh --headed

# Run specific test file
npx playwright test tests/qc-blocker-fixes.spec.ts
```

---

## Workflow: Develop → Test → Deploy

### Step 1: Develop Feature
```bash
cd frontend
npm run dev
# Make your changes in src/
```

### Step 2: Run QC Tests Locally
```bash
bash scripts/qc-test-suite.sh
```

**What it does:**
- ✅ Builds frontend if needed
- ✅ Starts dev server on port 5173
- ✅ Runs Playwright test suite
- ✅ Reports results (PASS/FAIL)
- ✅ Cleans up

### Step 3: Review Test Output

**If tests PASS:**
```
✅ ALL QC TESTS PASSED

Summary:
  ✓ Firebase Analytics removed (P2 compliance)
  ✓ IRS status bug fixed (P3 trust signal)
  ✓ Donation flow consistent
  ✓ Core functionality working
  ✓ No console errors
  ✓ Performance baseline met

Site is ready for deployment.
```

**If tests FAIL:**
```
❌ QC TESTS FAILED

Some tests failed. Review the output above and fix issues before deploying.
```

### Step 4: Commit & Deploy

Once tests pass:
```bash
git add .
git commit -m "feat: [feature name]

Tests: QC suite passing
- [what was tested]"

# Then use /daanaa-deploy for production
```

---

## Test Coverage: Phase 1 (Complete)

### 1. Firebase Analytics Removal (P2)
- ✅ Page HTML does NOT contain Firebase initialization
- ✅ Plausible analytics is loaded
- ✅ No analytics errors in console

### 2. IRS Status Bug Fix (P3)
- ✅ IRS eligibility section renders on org detail pages
- ✅ Status handling distinguishes revoked vs unknown
- ✅ Donation flow shows correct IRS status

### 3. Donation Flow Consistency
- ✅ Give options appear on org detail
- ✅ Router receives correct IRS status
- ✅ No navigation errors

### 4. Core Functionality Baseline
- ✅ Homepage loads (HTTP 200)
- ✅ Search functionality responds
- ✅ Org detail pages load
- ✅ No console errors (critical)
- ✅ Performance meets baseline (<3s for detail, <1s for search)

### 5. Live Search API Regression (Codex Finding 2026-08-11)
- ✅ Search returns results for common queries (education, food, health)
- ✅ Pagination works correctly (offset/limit don't overlap)
- ✅ Empty results handled gracefully (returns empty array, not error)

**Total Tests:** 17 test cases across 8 test groups

### Phase 2 (Planned, Future)
- Accessibility (WCAG AA) — keyboard navigation, screen reader compat
- Mobile responsiveness — viewport tests for mobile/tablet
- SEO meta tags — canonical tags, og:* tags, structured data
- Wallet functionality — bookmark persistence, sync across devices

---

## Adding Tests for New Features

### Pattern: Copy & Modify

1. **Open** `tests/qc-blocker-fixes.spec.ts`
2. **Add test block:**

```typescript
test.describe('Your Feature Name', () => {
  test('should do something specific', async ({ page }) => {
    await page.goto('http://localhost:5173/your-page');
    
    // Assert behavior
    const element = page.locator('[class*="YourFeature"]');
    await expect(element).toBeVisible();
    
    // Interact
    await element.click();
    
    // Verify result
    const result = page.locator('[data-testid="result"]');
    await expect(result).toContainText('Expected text');
  });
});
```

3. **Run tests:**
```bash
bash scripts/qc-test-suite.sh --verbose
```

4. **Commit with test evidence:**
```bash
git commit -m "feat: Your Feature

Tests: QC passing
- Your feature test [passing]"
```

---

## Playwright Basics

### Selectors

```typescript
// CSS
page.locator('.className')
page.locator('[data-testid="id"]')
page.locator('button:has-text("Click me")')

// Xpath
page.locator('//button[text()="Click"]')

// Role
page.locator('role=button[name="Click me"]')
```

### Wait & Interact

```typescript
// Wait for element
await page.waitForSelector('.element');

// Type text
await input.fill('search term');

// Click
await button.click();

// Check visibility
await expect(element).toBeVisible();

// Check content
await expect(element).toContainText('text');

// Network idle
await page.goto('url', { waitUntil: 'networkidle' });
```

### Assertions

```typescript
// Visibility
await expect(element).toBeVisible();
await expect(element).toBeHidden();

// Content
await expect(page).toHaveTitle('Title');
await expect(element).toContainText('text');

// HTTP Status
const response = await page.goto('url');
expect(response?.status()).toBe(200);

// Count
const count = await elements.count();
expect(count).toBeGreaterThan(0);
```

---

## Debugging Failed Tests

### Option 1: Run in headed mode
```bash
bash scripts/qc-test-suite.sh --headed
# Browser opens; you can watch tests run
```

### Option 2: Run specific test group (e.g., search regression)
```bash
npx playwright test tests/qc-blocker-fixes.spec.ts -g "Search API" --reporter=verbose

# Or run only search regression tests
npx playwright test tests/qc-blocker-fixes.spec.ts -g "Search" --headed
```

### Option 3: Debug in code
```typescript
// Add breakpoint
await page.pause();

// Debug output
console.log('Current URL:', page.url());
console.log('Element text:', await element.textContent());
```

### Troubleshooting Search Tests
If search tests fail:
```bash
# 1. Verify API is responding
curl http://localhost:5173/api/search?q=education

# 2. Check if dev server is running
lsof -Pi :5173 -sTCP:LISTEN

# 3. Run search tests with verbose output
npx playwright test tests/qc-blocker-fixes.spec.ts -g "Search API" --reporter=verbose

# 4. Run in headed mode to see browser interaction
bash scripts/qc-test-suite.sh --headed
```

---

## Integration with Deployment

**Before every deploy:**
```bash
# Run QC tests
bash scripts/qc-test-suite.sh

# If tests pass, proceed with /daanaa-deploy
# If tests fail, fix and re-run
```

**Codex's role:**
1. Reviews code changes
2. Checks test coverage
3. Verifies all tests pass
4. Approves deployment only if tests pass

---

## Performance Baseline

Current targets (can be adjusted):
- **Org detail page:** <3 seconds (networkidle)
- **Search response:** <1 second
- **Homepage load:** immediate (interactive)

If tests fail on performance, profile with Chrome DevTools or Playwright Inspector.

---

## Next Steps

1. **Add more test coverage** as features ship
2. **Integrate with CI/CD** (GitHub Actions, etc.) to auto-run on PRs
3. **Expand to include** accessibility (WCAG), SEO, mobile responsiveness
4. **Monitor performance** trends over time

---

**Remember:** A test that fails during development is better than a bug that reaches production.
