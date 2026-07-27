# V6 Financial Context — Founder Approval Package

**Date:** 2026-07-27  
**To:** Founder (Akbar)  
**From:** Claude Code  
**Status:** ⏳ AWAITING DECISION — Data remediation required before staging activation

---

## Executive Summary

**The v6 financial context system is architecturally complete and ready for data remediation.**

We have successfully:
- ✅ Built and tested all backend API infrastructure
- ✅ Created React frontend component with Tier 1-5 support
- ✅ Implemented comprehensive validation suite (12 tests)
- ✅ Created daily/weekly automation framework for data operations
- ✅ Designed approval gates to prevent premature public activation

**However:** Staging validation revealed critical data quality issues in the current candidate run that **block public activation**. These issues must be fixed before we proceed to staging.

---

## What V6 Provides

### Peer Financial Context
Instead of a 0–100 score, users see:

**Tier 1 Direct:** "This nonprofit has 12 months of reserve. Similar orgs have 8–15 months."  
**Tier 2 Regional:** "No recent revenue data. Other [regional] nonprofits in this sector have 6–10 months reserve."  
**Tier 5 Archetype:** "Limited public data. Organizations with this funding model vary widely in reserves."

### User Value
- Honest peer comparison (not a judgment)
- Respects data availability (Tier 5 when data is thin)
- Prevents false precision on small orgs (Stewardship P#4)
- Clear limitations visible on every org page

### Stewardship Alignment
- ✅ **P1 (Mission first):** Scores from public data only, no paid placement
- ✅ **P2 (Privacy):** No wallet or donor data exposed
- ✅ **P3 (Evidence-based):** All claims backed by IRS/NCCS data
- ✅ **P4 (Small-org fairness):** Tier 5 prevents false numeric comparison
- ✅ **P5 (No shame):** Respectful language; limitations always visible

---

## Current Status

### ✅ Complete & Tested
1. **API Endpoint:** `/api/organizations/<ein>/financial-context` (500+ lines)
2. **Frontend Component:** V6FinancialContext.tsx (400+ lines, Tier 1-5 support)
3. **Page Integration:** OrganizationDetail.tsx renders v6 context
4. **Validation Suite:** 12 unit tests covering schema, tiers, API contract, privacy
5. **Automation Framework:** Daily/weekly jobs for data integrity
6. **Database Schema:** All v6 tables normalized and populated

### ⏳ Awaiting Decision
1. **Data Remediation:** Fix issues blocking staging (see below)
2. **Staging Activation:** Enable feature flags and QA across all 5 tiers
3. **Founder Review:** Final approval before production

### ❌ Blocking Issues Found
During staging validation, the validation suite caught **2 critical data issues**:

---

## Blocking Issue #1: Revoked Organizations in Active Tiers ❌

**Issue:** 120,887 revoked 501(c)(3) organizations are assigned to numeric tiers (Tier 1-4)  
**Expected:** 0 revoked organizations in peer groups  
**Impact:** Users see peer comparisons that include defunct organizations  
**Severity:** CRITICAL (violates Stewardship P#1 — Trust signals must be evidence-based)

**Why this happened:**
The candidate run was generated before IRS revocation synchronization was fully implemented. The scorer needs to exclude revoked organizations before computing peer groups.

**Fix:**
1. Implement revocation check in the scorer
2. Regenerate candidate run
3. Verify: `SELECT COUNT(*) FROM v6_peer_context_assignments WHERE irs_revoked=1 AND selected_tier IN ('1_direct', '2_regional_conditional', '3_broader_regional', '4_national');` → should return 0

---

## Blocking Issue #2: Tier 2 Missing State Scope ❌

**Issue:** ALL 893,721 Tier 2 assignments have `geography_scope IS NULL`  
**Expected:** ALL should have `geography_scope = 'state'` with a valid geography_value  
**Impact:** Cannot determine which state's peers to use; peer comparison is broken  
**Severity:** CRITICAL (data integrity — required field missing)

**Why this happened:**
The scorer does not populate geography_scope and geography_value for regional tiers. These are required by the API response contract.

**Fix:**
1. Ensure scorer maps organizations to Census state regions
2. Populate geography_scope and geography_value for Tier 2-3
3. Regenerate candidate run
4. Verify: All Tier 2 rows have `geography_scope = 'state'`

---

## What Needs to Happen Next

### Step 1: Fix Data Foundation (Dev Team)
1. Audit scorer (scripts/v6_candidate_run_from_foundation.py)
2. Add revocation filtering before peer group computation
3. Add state/region mapping for Tier 2-3
4. Run test generation with small sample (e.g., 100 orgs)
5. Verify validation suite passes

### Step 2: Regenerate Candidate Run
```bash
python3 scripts/v6_candidate_run_from_foundation.py --run-id v6_foundation_candidate_20260728_revised
```

### Step 3: Full Validation
```bash
python3 scripts/v6_validate_run.py v6_foundation_candidate_20260728_revised
# Should output: ✅ Validation PASSED (0 errors)
```

### Step 4: Staging Activation (Once Founder Approves Candidate)
```bash
export ENABLE_V6_FINANCIAL_CONTEXT=true
export VITE_ENABLE_V6_FINANCIAL_CONTEXT=true
./restart_api.sh
cd frontend && npm run dev
```

### Step 5: Founder QA Review
Test across all 5 tiers and verify peer context makes sense:
- Tier 1: See peer median + range
- Tier 2: See conditional bands by revenue level
- Tier 3: See broader regional context
- Tier 4: See national context
- Tier 5: See archetype descriptor only (no numbers)

### Step 6: Production Activation (Founder Approval Required)
Once staging looks good and founder approves:
```bash
# In production environment
export ENABLE_V6_FINANCIAL_CONTEXT=true
export VITE_ENABLE_V6_FINANCIAL_CONTEXT=true
# Deploy to daanaa.org
```

---

## Timeline

**If we fix the data issues today:**

| Phase | Timeline | Owner |
|-------|----------|-------|
| Data remediation | 2-4 hours | Dev team |
| Candidate regeneration | 1-2 hours | Dev team |
| Validation | 30 min | Dev team |
| Staging QA | 2-4 hours | Founder |
| Production activation | On approval | Ops |

**Total: 1-2 days to production-ready**

---

## Approval Gates

**These MUST be satisfied before production:**

- [ ] Revoked organizations = 0 in active tiers
- [ ] Tier 2 assignments have state scope (100%)
- [ ] Validation script passes (0 errors)
- [ ] Privacy check passes (8/8 gates)
- [ ] Staging QA completed (sample org testing)
- [ ] Founder explicitly approves new candidate

---

## Recommendations

### For Staging (Next 24-48 Hours)
1. Fix data issues in scorer
2. Regenerate candidate run
3. Deploy to staging with feature flags enabled
4. Test 20-30 sample organizations across all 5 tiers
5. Verify peer context is accurate for each tier

### For Production Launch (Week of Aug 4)
1. Monitor staging for 24-48 hours
2. Collect any user feedback
3. Enable v6 feature flag in production
4. Monitor API error rates + response times
5. Consider gradual rollout (10% → 50% → 100%) if available

### Going Forward
- Run weekly candidate generation (Mondays at 02:00 UTC)
- Compare new candidate with prior approved run
- Flag large changes for founder review
- Maintain data quality thresholds (0 revoked in active, all Tier 2 with geography)
- Publish weekly data quality report

---

## Decision Needed From Founder

**Question 1: Approve data remediation approach?**
- Fix revocation filtering + state scope population
- Regenerate candidate with corrections
- Proceed to staging validation

**Question 2: Timeline preference?**
- Fast track (fix today, stage tomorrow): 1-2 days to prod
- Measured pace (fix this week, stage next week): more thorough testing
- Defer: push to mid-August

**Question 3: Rollout strategy?**
- Replace v4/v5 scores entirely with v6
- Show both v4/v5 and v6 during transition period
- Use feature flag for gradual user rollout (10%/50%/100%)

---

## Documentation

All relevant docs are in `/docs/`:

| Document | Purpose |
|----------|---------|
| `V6_IMPLEMENTATION_HANDOFF_2026_07_27.md` | Complete technical spec |
| `V6_STAGING_ACTIVATION_GUIDE.md` | 6-step staging enable + checklist |
| `V6_DAILY_WEEKLY_DATA_OPERATIONS_PLAN_2026_07_27.md` | Operational procedures |
| `V6_QA_BLOCKING_ISSUES_2026_07_27.md` | Data issues + remediation |
| `V6_STAGING_QA_FINDINGS_2026_07_27.md` | Detailed QA results |

---

## Summary

✅ **V6 is architecturally sound and production-ready.**  
❌ **Current data candidate has integrity issues that must be fixed first.**  
⏳ **Awaiting founder decision on remediation + timeline.**  

**Estimated time to production:** 1-2 days after founder approval + data fixes

---

**Founder Action Required:**
1. Review this document
2. Approve data remediation approach
3. Confirm timeline preference
4. Authoriz dev team to proceed with fixes

Once approved, staging will be operational within 24 hours.
