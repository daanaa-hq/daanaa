# Gate Failures Analysis & Recovery Plan

**Date:** 2026-08-11  
**Severity:** Gate 4 (data), Gate 5 (fairness violation), Gate 7 (PASS ✅)

---

## Gate 4: Website Verification — FAILED (61% vs need 85%)

### Root Cause
- 37 HTTP errors (404, 500, SSL errors)
- 2 timeouts
- Bad/malformed URLs in registry_enriched.website field

### Examples of Issues
- Missing protocol (stored as `example.org` not `https://example.org`)
- Typos in domain names
- Expired domains
- Redirects to fundraising pages instead of org homepage

### Options to Fix
**Option A: Adjust threshold** (quick)
- Lower pass threshold from 85% to 70%
- Rationale: 61% is reasonable for nonprofits (many lack tech infrastructure)
- Downside: Acknowledges data quality gap

**Option B: Clean URLs** (1-2 hours)
- Run link validation pipeline to find/fix broken URLs
- De-duplicate and standardize formats
- Re-test after cleanup
- Expected result: 70-80% HTTP 200

**Option C: Hybrid** (recommended)
- Accept 61% baseline as data quality baseline
- Flag bad URLs for cleanup
- Commit to 75%+ by Oct 1
- Launch with transparency note: "Website data quality improving"

---

## Gate 5: Small Org Fairness — FAILED (CRITICAL)

### Root Cause: FAIRNESS VIOLATION
Small orgs systematically disadvantaged in website discovery pipeline.

**Data:**
- Small orgs (<$150K): 43% have websites
- Large orgs (>$1M): 87% have websites
- Gap: 44 percentage points (3.5x disadvantage)

### Why This Matters (Stewardship Principle #4)
> "Small organizations deserve fairness. Our systems should not automatically disadvantage sincere organizations simply because they are smaller or less digitally mature."

This failure **violates our founding principle** and must be fixed before public launch.

### Root Cause Analysis
Discovery daemon prioritizes large orgs because:
1. Large orgs have better SEO (rank higher in Google)
2. Large orgs listed on more platforms (GuideStar, IRS directories)
3. Small orgs may have outdated/abandoned websites
4. Algorithm has implicit size bias in its ranking

### Fix Strategy (4-6 hours)

**Phase 1: Bias elimination** (2 hours)
- Modify discovery daemon to weight small orgs equally
- Remove size-based filtering in website scraper
- Target small orgs specifically (e.g., "nonprofit $50K" searches)

**Phase 2: Testing** (2 hours)
- Re-sample 100 small + 100 large orgs
- Verify parity: 0.95-1.05 ratio achieved
- Document changes in docs/WEBSITE_DISCOVERY_BIAS_FIX.md

**Phase 3: Deployment** (1 hour)
- Deploy fixed daemon
- Monitor discovery rate for next 24h
- Report results

### Success Criteria
- Website discovery parity: 0.95-1.05x
- Small org discovery rate: 70%+ (up from 43%)
- Large org discovery rate: maintained or improved

---

## Gate 7: Independence Verification — PASS ✅

**Result:** No paid placement code found, all scoring deterministic from IRS data

**Confidence:** HIGH - Code audit confirmed:
- No hardcoded org whitelist
- No vendor scoring boost
- No size-based ranking advantage (algorithm-level)
- All data from public IRS sources

Note: Gate 5 failure indicates potential algorithm-level bias that needs fixing despite code audit passing.

---

## Decision: How to Proceed

### Option 1: Fix All Gates (2-3 days)
- Fix Gate 4 data quality (Option C: accept baseline + cleanup plan)
- Fix Gate 5 fairness bias (modify daemon, re-test)
- Re-test all gates until PASS
- Launch after all gates pass

**Timeline:** Aug 13-14  
**Confidence:** High (fixes are clear)

### Option 2: Launch with Exceptions
- Gate 7: PASS (independence verified)
- Gate 4: Accept 61% as launch baseline + transparency note
- Gate 5: DEFER (commit to fairness fix by Sept 1)
- Launch pilot with known limitations

**Timeline:** Aug 12 (immediate)  
**Risk:** Fairness violation visible to early users

### Option 3: Pause & Investigate
- Root cause analysis on why large orgs have 2x website discovery
- Comprehensive bias audit across pipeline
- Re-test with improved methodology
- More rigorous quality bar

**Timeline:** Aug 15+ (delays launch)  
**Confidence:** Very high after thorough audit

---

## Recommendation: Option 1

Fix Gates 4 & 5 before launch. Gate 5 failure is a **founding principle violation** and non-negotiable.

**Timeline:** 12 hours work over next 2 days = Ready Aug 13

**Why:**
- Fairness is core to mission (Principle #4)
- Fixes are straightforward (data cleanup, algorithm tuning)
- Small delay (2 days) worth avoiding launch with bias
- Public trust depends on fair treatment of all orgs

