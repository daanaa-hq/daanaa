# Overlay Brand Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align the static growth pages with Daanaa's main visual system without adding React or backend dependencies.

**Architecture:** Extend `build_growth_pages.py` with one branded static shell and one optional directory-filter helper. Every generated page remains complete HTML; JavaScript only enhances index filtering.

**Tech Stack:** Python 3, static HTML/CSS/JavaScript, `unittest`, Playwright, axe-core.

---

### Task 1: Brand shell

**Files:**
- Create: `visibility/tests/test_growth_page_theme.py`
- Modify: `visibility/scripts/build_growth_pages.py`

- [ ] Add a failing test asserting that `page_shell()` emits main-site font families, exact brand tokens, labeled navigation and breadcrumbs, a 1200px container, accessible link color, and a complete footer.
- [ ] Run `python3 -m unittest visibility.tests.test_growth_page_theme -v` and confirm the expected failure.
- [ ] Replace the legacy inline shell with the minimal static branded shell.
- [ ] Re-run the focused test and confirm it passes.

### Task 2: Progressive directory filter

**Files:**
- Modify: `visibility/tests/test_growth_page_theme.py`
- Modify: `visibility/scripts/build_growth_pages.py`

- [ ] Add a failing test for `directory_filter()` requiring a label, search input, controlled list ID, result status, and enhancement hook.
- [ ] Implement `directory_filter()` and a small shell script that filters `li` elements while preserving initial HTML.
- [ ] Add filter controls and stable list IDs to state, category, and guide index pages.
- [ ] Run both growth-page and existing visibility tests.

### Task 3: Build and browser verification

**Files:**
- Generated: `visibility/public/nonprofits/**`
- Generated: `visibility/public/guides/**`
- Generated: `visibility/cloudflare-public/**`

- [ ] Rebuild the overlay, run stewardship checks, and prepare Cloudflare assets.
- [ ] Verify clean canonical URLs remain intact.
- [ ] Run Playwright screenshots and axe checks at 1440px and 390px.
- [ ] Deploy the static Pages project after all checks pass, then verify live routes and submit IndexNow.
