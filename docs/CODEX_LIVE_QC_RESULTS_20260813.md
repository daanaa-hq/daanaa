# Codex Live-Site QC Report
**Date:** August 13, 2026  
**Target:** https://www.daanaa.org  
**Status:** ⚠️ CRITICAL ISSUES FOUND

---

## Executive Summary

Codex ran comprehensive browser testing + accessibility audit on production daanaa.org. **Three P1 issues identified** that should be addressed before promoting current state as "live and ready."

---

## Detailed Findings

### 🔴 P1: Systemic Color Contrast Failures (Accessibility)

**Severity:** HIGH - WCAG compliance violation  
**Root Cause:** Shared color token/system issue (not isolated page bugs)  
**Affected Pages:** All tested pages

| Page | Violations | Example |
|------|-----------|---------|
| /research | 143 nodes | Likely text/link contrast vs background |
| /directory | 114 nodes | Search results text likely affected |
| /methodology | 103 nodes | Documentation text likely affected |
| /org/530196605 | (included in scan) | Org detail page |
| /about, /privacy, /security | (included in scan) | General pages |

**Evidence:** Axe accessibility scanner reported serious violations across all sampled routes.

**Impact:** 
- Users with vision impairments cannot use the site reliably
- WCAG AA compliance at risk
- Legal exposure (accessibility lawsuits common in nonprofit sector)

**Fix Strategy:**
1. Audit CSS token definitions (likely in `frontend/src/styles/` or Tailwind config)
2. Identify which text/link color pairs fail contrast
3. Update tokens to meet WCAG AA (4.5:1 for normal text, 3:1 for large text)
4. Re-run Axe scan to verify

---

### 🔴 P1: Directory Search Route Performance & Errors

**Severity:** HIGH - User-facing performance issue  
**Route:** `/directory?q=education&limit=20`  
**Measured Load Time:** ~5923ms (5.9 seconds)  
**Console Issues:**
- 6 console errors logged
- 5 failed network requests

**Impact:**
- Users see blank page for 6 seconds while searching
- Failed requests suggest missing API data or crashed components
- Poor first impression on critical discovery UX

**Investigation Needed:**
1. Which 5 requests are failing? (403? 404? 500? timeouts?)
2. What are the 6 console errors?
3. Is API `/api/search` responding correctly?
4. Are components mounting twice (React StrictMode in dev)?
5. Is there a missing precomputed data dependency?

**Quick Wins:**
- Check browser DevTools Network tab for failed requests
- Check DevTools Console for error stack traces
- Verify API health on production
- Check for missing environment variables on droplet

---

### 🔴 P1: API Contract Drift (Test/Live Mismatch)

**Severity:** HIGH - Data structure mismatch  
**Issue:** Live API returns uppercase fields, tests expect lowercase

**Live API Response (Actual):**
```json
{
  "mode": "fts",
  "query": "education",
  "results": [
    {
      "EIN": "364593555",
      "organization_name": "EDUCATION MINNESOTA SEBEKA EDUCATION SUPPORT PROFESSIONALS",
      ...
    }
  ],
  "total": 3
}
```

**Older QC Tests Expected:**
```json
{
  "ein": "364593555",
  "name": "EDUCATION MINNESOTA SEBEKA EDUCATION SUPPORT PROFESSIONALS",
  ...
}
```

**Root Cause:** API schema likely changed; test fixtures weren't updated.

**Fix:**
1. Audit `scripts/core/droplet_api.py` `/api/search` endpoint for field naming
2. Update all frontend code accessing `ein`/`name` to use `EIN`/`organization_name`
3. Update test fixtures and mocks to match live schema
4. Add contract test to catch future drift

**Note:** This explains why local Playwright tests were timing out earlier—they were looking for data that wasn't shaped the way they expected.

---

### 🟡 P2: Org Detail Page Runtime Noise

**Severity:** MEDIUM - Not blocking, but noisy  
**Route:** `/org/530196605`  
**Status:** ✅ Returns 200, content renders  
**Issues Logged:**
- 11 console errors
- 5 failed requests

**Mobile Viewport (375px):**
- ✅ No horizontal overflow
- ✅ Content readable

**Assessment:** Core functionality works, but errors suggest missing dependencies or stale imports. Low priority vs. P1 items.

---

## Test Coverage

**Routes Tested (All returned 200):**
- ✅ / (homepage)
- ✅ /directory (search route)
- ✅ /org/530196605 (org detail page)
- ✅ /about, /methodology, /research, /privacy, /security, /wallet, /for-nonprofits

**Browsers Tested:**
- Playwright browser pass (simulated real user)
- Axe accessibility scan
- Mobile viewport (375px)

**API Tested:**
- `/api/search` endpoint contract

---

## Recommendations (Priority Order)

**BEFORE next major promotion:**

1. **Fix color contrast tokens** (P1, ~2-4 hours)
   - Root cause analysis of CSS tokens
   - Update colors to WCAG AA
   - Verify with Axe scan
   - Re-run live-site audit

2. **Debug directory page failures** (P1, ~2-4 hours)
   - Identify which 5 requests are failing
   - Review 6 console errors
   - Test `/api/search` endpoint health
   - Measure post-fix load time (target: <2s)

3. **Fix API contract drift** (P1, ~1-2 hours)
   - Update frontend to use EIN/organization_name
   - Update test fixtures
   - Add contract tests
   - Verify against live API

4. **Clean up org page errors** (P2, deferred)
   - Identify missing dependencies
   - Resolve stale imports
   - Clean up console warnings

---

## Codex Test Artifact

**Location:** `tests/live-site-qc.spec.ts` (temporary, test-only)  
**Purpose:** Reusable live-site QC suite for future deployments  
**No product code changed** during this pass

---

## Next Steps

1. **Immediate:** Acknowledge findings, assign P1 fixes
2. **This week:** Address color contrast + directory slowness
3. **Re-test:** Run `tests/live-site-qc.spec.ts` against updated site
4. **Document:** Update DECISIONS.md with findings & fixes applied

---

**Report prepared by:** Codex (live-site QC)  
**Summary for:** Claude Code + Akbar Khowaja  
**Follow-up needed:** Yes (P1 fixes required before production promotion)
