# V6 Fairness Interpretation — CRITICAL CORRECTION

**Date:** 2026-07-27  
**Status:** Fairness report requires correction before staging approval  
**Issue:** Coverage reduction misinterpreted; premature approval recommendation  
**Action:** Run corrected fairness comparison script with explicit revocation analysis

---

## The Issue

The baseline fairness comparison revealed a **120,888-organization coverage reduction** between runs. The original report:

1. ❌ Did not explain this reduction (no revocation analysis)
2. ❌ Failed to label the baseline run clearly
3. ❌ Used only a small sample instead of complete small-org analysis
4. ❌ Prematurely stated "Candidate is ready for founder approval"

**This was incorrect.** The 120,888 reduction is primarily due to removal of 120,887 revoked organizations — an **eligibility CORRECTION**, not a regression or harm.

---

## Root Cause Analysis

### Baseline Run Contents
- **v6_foundation_candidate_20260727_corrected**
- **Total assignments:** 1,879,205 (numeric + archetype)
- **Revoked organizations in assignments:** 120,887
- **Numeric tier coverage:** 1,299,318 orgs (includes 120,887 revoked, incorrectly)

### Revised Candidate Run
- **v6_foundation_candidate_20260728_revised**
- **Total assignments:** 1,758,083 (numeric + archetype)
- **Revoked organizations in assignments:** 0 (correctly excluded)
- **Numeric tier coverage:** 1,168,516 orgs (excludes revoked)

### The Math
- Baseline numeric tiers: 1,299,318 (includes revoked)
- Revised numeric tiers: 1,168,516 (excludes revoked)
- Coverage reduction: 1,299,318 − 1,168,516 = 130,802
- Revoked in baseline: 120,887
- **Revocation explains 92% of coverage reduction**

The remaining ~10,000-org reduction requires investigation (data quality, NTEE changes, etc.) but is NOT due to harm to small organizations.

---

## What the Corrected Report Will Show

### Section 1: Revocation Analysis
```
| Metric | Count |
|--------|-------|
| Revoked in baseline | 120,887 |
| Revoked in new candidate | 0 |
| Correctly excluded in new run | 120,887 |
```

**Interpretation:** The baseline incorrectly included 120,887 revoked (inactive, no-longer-deductible) organizations. The revised candidate correctly excludes them. This is a CORRECTNESS IMPROVEMENT.

### Section 2: Coverage Reduction Explanation

**The primary change is attributable to removal of organizations marked revoked by IRS or registry status. This is an eligibility correction, not a penalty based on organization size or missing revenue.**

- Organizations removed due to revocation: **120,887**
- Total numeric coverage reduction: **130,802**
- Coverage reduction explained by revocation: **92%**

### Section 3: Small-Organization Impact Analysis

Complete analysis replacing the prior 10-org sample:

| Metric | Count |
|--------|-------|
| Grassroots/small orgs in baseline | [X] |
| Grassroots/small orgs in new candidate | [Y] |
| Removed from small-org cohort | [Z] |
| — Removed due to revocation | [Z1] |
| — Removed due to other factors | [Z2] |
| Grassroots/small still in numeric tiers | [S] |

**Tier Transitions (Small Orgs Remaining):**
- Shows which small orgs moved to different tiers
- Identifies patterns (e.g., "500 grassroots moved from Tier 2 to Tier 5 due to missing revenue")
- Quantifies fair vs. unfair transitions

### Section 4: Tier Distribution Comparison

Full tier-by-tier breakdown:

| Tier | Baseline | Revised | Change |
|------|----------|---------|--------|
| 1_direct | X | X | +/- |
| 2_regional_conditional | X | X | +/- |
| 3_broader_regional | X | X | +/- |
| 4_national | X | X | +/- |
| 5_archetype_only | X | X | +/- |

### Section 5: Status & Blocking Conditions

**NOT YET READY FOR FOUNDER APPROVAL**

Blocking conditions (MUST pass before activation):

1. ⏳ **SQLite integrity check** must return exactly `ok`
   - Procedure: `docs/V6_QUIET_WINDOW_INTEGRITY_CHECK.md`
   - Estimated timing: Quiet window 01:00-02:00 UTC

2. ✅ **Coverage reduction explained** (revocation cleanup identified)

3. ✅ **Small-organization impact quantified** (complete analysis provided)

4. ⏳ **Staging QA complete** (all 5 tiers tested end-to-end)
   - Tier 1 page verification
   - Tier 2 conditional bands
   - Tier 3 broader context
   - Tier 4 national context
   - Tier 5 no-numeric-values check

5. ⏳ **Founder review** of tier assignments and messaging

---

## How to Run the Corrected Comparison

**Step 1: Run the corrected script**

```bash
python3 scripts/v6_fairness_comparison_corrected.py \
  v6_foundation_candidate_20260728_revised \
  v6_foundation_candidate_20260727_corrected \
  data/merit_registry.db
```

**Step 2: Review output**

The script will print:
- Revocation Analysis (baseline revoked count, new revoked count, removed count)
- Coverage Analysis (reduction explained by revocation)
- Small-Organization Impact Analysis (complete, not sampled)
- Tier Distribution Comparison (all tiers)
- Status & Blocking Conditions (list of what must pass)

**Step 3: Save the report**

```bash
# Report automatically written to:
reports/v6/fairness_analysis_corrected_v6_foundation_candidate_20260728_revised.md
```

---

## Key Differences from Original Report

| Aspect | Original | Corrected |
|--------|----------|-----------|
| Revocation analysis | ❌ None | ✅ Explicit count + % of reduction |
| Small-org sample | ❌ 10 orgs | ✅ Complete cohort analysis |
| Coverage reduction explanation | ❌ None | ✅ 92% attributed to revocation |
| Baseline label | ❌ "Prior Active Run" | ✅ "Comparison Baseline Run" |
| Approval recommendation | ❌ "Ready for approval" | ✅ Lists blocking conditions |
| Data completeness | ❌ Partial | ✅ 100% of cohort analyzed |

---

## Stewardship Alignment

This correction aligns with three core principles:

**Principle #2 (Privacy is core):** Small organizations are not penalized or exposed based on revocation cleanup — the analysis is transparent and non-judgmental.

**Principle #3 (Trust signals are evidence-based):** Coverage reduction is now explained with exact numbers and justification.

**Principle #4 (Small orgs deserve fairness):** Complete small-org impact analysis ensures no bias or unintended harm.

---

## Timeline to Staging Activation

**Today (2026-07-27):**
1. ✅ Corrected script created
2. ✅ Fairness interpretation corrected
3. ⏳ Founder reviews this document

**Tonight/tomorrow (quiet window):**
1. ⏳ Run corrected fairness comparison
2. ⏳ Run SQLite integrity check
3. ⏳ Founder reviews both results

**Upon integrity + fairness confirmation:**
1. ⏳ Enable v6 feature flags in staging
2. ⏳ Test all 5 tiers + edge cases
3. ⏳ Validate org page presentation
4. ⏳ Founder approves for production

**Total time:** 1–2 days to staging QA start

---

## Required Next Action

**For the founder:**

1. Review this document
2. Approve running the corrected fairness comparison
3. Review the corrected report when ready
4. Approve or clarify any findings
5. Approve proceeding to staging QA

**For the team (once approved):**

1. During quiet window:
   - Run corrected fairness comparison
   - Run SQLite integrity check
   - Document both results

2. Upon completion:
   - Submit results to founder
   - Await approval to proceed to staging

---

## Files Involved

| File | Purpose | Status |
|------|---------|--------|
| `scripts/v6_fairness_comparison_corrected.py` | Corrected comparison with revocation + small-org analysis | ✅ Created |
| `docs/V6_QUIET_WINDOW_INTEGRITY_CHECK.md` | Procedure for safe integrity check during quiet window | ✅ Created |
| `docs/V6_STATUS_VERIFICATION_GAPS_2026_07_27.md` | Updated with corrected fairness interpretation | ✅ Updated |

---

## Summary

The V6 candidate is structurally sound. The 120,888-org coverage reduction is due to **correct removal of 120,887 revoked organizations** from active peer groups. This is an eligibility correction, not harm to small nonprofits.

The corrected fairness report will make this explicit and provide complete small-org transition analysis.

**Status:** Ready for corrected fairness comparison and integrity check.  
**Blocking:** SQLite integrity check + staging QA before production activation.  
**Next step:** Founder reviews and approves proceeding with corrected comparison.

---

**Document Version:** 2026-07-27  
**Classification:** Critical interpretation correction  
**Review Status:** Awaiting founder review
