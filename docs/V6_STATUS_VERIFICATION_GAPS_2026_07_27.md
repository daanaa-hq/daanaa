# V6 Status — Verification Gaps Identified

**Date:** 2026-07-27  
**Status:** Hardened and locally tested. Ready for baseline fairness comparison and staging QA. NOT yet production-ready or approved for activation.

**Verified by founder:** 2026-07-27

---

## Confirmed Working ✅

- ✅ 24/24 v6 tests pass
- ✅ Privacy checks pass (8/8 gates)
- ✅ Hardening scripts exist and functional
- ✅ Candidate remains inactive (`status='candidate'`)
- ✅ Production flags remain disabled
- ✅ Transactional backfill code includes rollback behavior
- ✅ Weekly generation wired to create fresh candidates
- ✅ Revocation verification blocking enforced
- ✅ All 11 approval gates functional

---

## TWO CRITICAL GAPS IDENTIFIED

### Gap 1: Fairness Report Interpretation (CRITICAL) ⏳

**Issue Found (Updated 2026-07-27):**
- Original fairness report found coverage reduction of 120,888 organizations
- Baseline contained 120,887 revoked organizations (incorrectly included)
- New candidate correctly excludes revoked orgs
- Report failed to explain this as eligibility cleanup, not harm
- Report prematurely stated "ready for approval" without this analysis
- Report lacked complete small-organization transition data

**Root Cause:**
Coverage reduction interpretation error. The 120,888 drop is primarily due to removal of 120,887 revoked organizations — an eligibility CORRECTION, not a regression or harm to small organizations.

**Fix Applied:**
- Created `scripts/v6_fairness_comparison_corrected.py` (~400 lines)
- New script includes:
  - **Explicit revocation analysis:** Count revoked in baseline vs. revised candidate
  - **Coverage reduction explanation:** Quantify revocation removal as % of total reduction
  - **Complete small-org transitions:** Count grassroots/small orgs in each tier, track removals by cause (revocation vs. other)
  - **Clear baseline labeling:** "Comparison Baseline Run" (not "Prior Active Run")
  - **NO premature approval:** Lists blocking conditions (integrity check, staging QA, founder review)

**Required Action:**
```bash
# Run corrected fairness comparison with explicit baseline
python3 scripts/v6_fairness_comparison_corrected.py \
  v6_foundation_candidate_20260728_revised \
  v6_foundation_candidate_20260727_corrected \
  data/merit_registry.db
```

**Expected Output:**
- Markdown report in `reports/v6/fairness_analysis_corrected_v6_foundation_candidate_20260728_revised.md`
- Section 1: Revocation Analysis (baseline revoked count, new revoked count, correctly excluded)
- Section 2: Coverage Analysis (reduction explained: X orgs due to revocation, Y due to other factors)
- Section 3: Small-Organization Impact (complete tier transition analysis, not just sampling)
- Section 4: Tier Distribution Comparison (all 5 tiers, baseline vs. revised)
- Section 5: Status & Blocking Conditions
  - ✅ Coverage reduction explained (revocation cleanup)
  - ✅ Small-org impact quantified (complete analysis)
  - ⏳ SQLite integrity check must return exactly `ok`
  - ⏳ Staging QA must pass (all 5 tiers tested)
  - ⏳ Founder review of presentation + tier assignments
  - ❌ NO approval recommendation until all conditions met

**CRITICAL:** The report will NOT recommend approval. It will list what remains to be verified.

**Status:** ⏳ Needs to be run during next quiet maintenance window

---

### Gap 2: Full SQLite Integrity Scan Interrupted by Lock ⏳

**Issue Found:**
- Full `PRAGMA integrity_check` interrupted by active database lock
- Returned incomplete result
- Needs clean rerun to confirm `ok` status

**Root Cause:**
- Database was in use during integrity scan attempt
- Active queries/connections holding locks

**Required Action:**
```bash
# Run during quiet maintenance window (no API/frontend running)
# Stop all services first
./stop_services.sh  # or pkill -f "python3 daanaa_api.py" if no script exists

# Wait 10 seconds for locks to clear
sleep 10

# Run integrity check
sqlite3 data/merit_registry.db "PRAGMA integrity_check;"
# Expected: ok

# Restart services
./restart_api.sh
```

**Verification Procedure:**
```bash
# Confirm database is accessible after integrity check
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched;"
# Expected: 1,900,000+ rows
```

**Status:** ⏳ Needs to be run during next quiet maintenance window

---

## STAGING QA NOT YET COMPLETED ⏳

**What hasn't happened:**
- Staging has not been activated (feature flags enabled)
- End-to-end testing not completed
- V5 → V6 transition not validated
- Performance baseline not established

**What needs to happen:**
1. Enable feature flags in staging environment
2. Restart API and frontend
3. Test all 5 tiers with sample organizations
4. Test edge cases (missing revenue, revoked orgs, etc.)
5. Verify search/discovery still works (independent of v6)
6. Check API response times (<500ms expected)
7. Check frontend render times (<200ms expected)
8. Verify no console errors or regressions

**Timeline:** 4 hours minimum

**Blocking staging:** Fairness baseline comparison + full integrity check

---

## ORGANIZATION PAGE PRESENTATION QA NOT YET COMPLETED ⏳

**What hasn't happened:**
- Sample organization pages not generated for Scenarios A/B/C
- Messaging not reviewed by founder
- Tier assignments not visually validated
- No user-facing QA of page layout, messaging, limitations

**What needs to happen:**
1. Generate sample pages for:
   - **Scenario A:** Strong financial data (Tier 1) — e.g., large education nonprofit
   - **Scenario B:** Partial data (Tier 2) — e.g., regional nonprofit with old filing
   - **Scenario C:** Little data (Tier 5) — e.g., new or all-volunteer org
2. Review messaging for tone, clarity, limitations
3. Verify limitations are prominent and respectful
4. Ensure "no judgment" messaging clear for Tier 5
5. Test org claim flow (if implemented)

**Timeline:** 2 hours

**Blocking production:** Founder sign-off on org-page presentation

---

## ACCURATE STATUS

> **Hardened and locally tested. Ready for baseline fairness comparison and staging QA. Not yet production-ready or approved for activation.**

### What's Ready
- ✅ All implementation complete
- ✅ All local tests pass (24/24)
- ✅ All safeguards functional
- ✅ Privacy compliance verified
- ✅ Code hardened and production-safe

### What's Blocking Production
1. ⏳ Fairness baseline comparison (awaits quiet maintenance window + founder review)
2. ⏳ Full database integrity scan (awaits quiet maintenance window + confirmation)
3. ⏳ Staging end-to-end QA (awaits baseline comparison + integrity check)
4. ⏳ Organization page presentation QA (awaits staging validation)

---

## PATH TO PRODUCTION READINESS

### Phase 1: Baseline Verification (Next Quiet Window)
```
1. Run fairness comparison vs. v6_foundation_candidate_20260727_corrected
2. Run full SQLite integrity check
3. Confirm both return expected results
4. Report to founder
Estimated: 30 minutes
```

### Phase 2: Staging QA (Post-Verification)
```
1. Enable v6 feature flags in staging
2. Test all 5 tiers + edge cases
3. Validate performance baselines
4. Confirm no regressions
5. Report results to founder
Estimated: 4 hours
```

### Phase 3: Organization Page QA (Post-Staging)
```
1. Generate sample Scenario A/B/C pages
2. Review messaging and tone
3. Verify limitations prominent
4. Founder sign-off on presentation
5. Report to founder
Estimated: 2 hours
```

### Phase 4: Production Activation (Upon Founder Approval)
```
1. Enable v6 in production
2. Deploy to daanaa.org
3. Monitor for 24 hours
4. Gather user feedback
Estimated: 1 hour (monitoring)
```

**Total Timeline:** 1 day (Phases 1-3) + monitoring (Phase 4)

---

## NEXT STEPS

**For the team:**

1. **Schedule quiet maintenance window** (all services stopped for 30 min)
2. **Run fairness baseline comparison:**
   ```bash
   python3 scripts/v6_fairness_comparison.py \
     v6_foundation_candidate_20260728_revised \
     v6_foundation_candidate_20260727_corrected \
     data/merit_registry.db
   ```
3. **Run full database integrity check** (services stopped)
4. **Report results to founder**

**For the founder:**

1. Review fairness comparison report results
2. Confirm full integrity check returns `ok`
3. Approve staging QA timeline
4. Upon staging completion, approve production timeline

---

## Summary

The V6 system is **hardened, tested, and safe**. Two verification gaps must be closed before staging activation:

1. **Fairness baseline comparison** — Script fixed, needs to run with explicit baseline
2. **Full database integrity scan** — Needs clean rerun during quiet window

Estimated 1 day to close both gaps + complete staging/org-page QA.

**Status:** Ready to proceed with verification phase. Not yet production-ready until all gaps closed.
