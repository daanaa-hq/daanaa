# V6 QA — Blocking Issues Found

**Date:** 2026-07-27  
**Status:** ❌ BLOCKING — Data foundation issues must be resolved before staging activation  
**Severity:** CRITICAL

---

## Summary

Staging validation discovered critical data quality issues in the current v6 candidate run (`v6_foundation_candidate_20260727_corrected`). These issues prevent public activation and require remediation.

---

## Blocking Issues

### Issue 1: Revoked Organizations in Active Tiers ❌

**Severity:** CRITICAL (Stewardship Principle #1 — Trust signals must be evidence-based)

**Finding:**
- 120,887 revoked 501(c)(3) organizations are assigned to numeric tiers (Tier 1-4)
- Expected: 0 revoked organizations in active tiers

**Impact:**
- Peer comparisons include defunct organizations
- Violates IRS revocation data integrity
- Gives users false peer context

**Root Cause:** 
Candidate run was generated before IRS revocation synchronization was fully implemented

**Remediation:**
```bash
# 1. Identify which revoked orgs are in active tiers
sqlite3 data/merit_registry.db "
  SELECT COUNT(DISTINCT a.ein)
  FROM v6_peer_context_assignments a
  WHERE a.run_id='v6_foundation_candidate_20260727_corrected'
  AND a.selected_tier IN ('1_direct','2_regional_conditional','3_broader_regional','4_national')
  AND a.ein IN (SELECT EIN FROM registry_enriched WHERE irs_revoked=1);
"

# 2. Move these to Tier 5 (archetype-only) with null peer metrics
# 3. Regenerate candidate run after revocation sync

# 4. Verify fix:
sqlite3 data/merit_registry.db "
  SELECT COUNT(*)
  FROM v6_peer_context_assignments a
  WHERE a.run_id='<NEW_RUN_ID>'
  AND a.selected_tier IN ('1_direct','2_regional_conditional','3_broader_regional','4_national')
  AND a.ein IN (SELECT EIN FROM registry_enriched WHERE irs_revoked=1);
" # Should return: 0
```

---

### Issue 2: Tier 2 Missing State Scope ❌

**Severity:** CRITICAL (Data integrity — required field null)

**Finding:**
- ALL 893,721 Tier 2 Regional Conditional assignments have `geography_scope IS NULL`
- Expected: ALL should have `geography_scope = 'state'`

**Impact:**
- Cannot determine which state's peers to use
- Peer comparison is meaningless without geography
- Violates v6 Tier 2 specification

**Root Cause:**
Candidate generation did not populate geography_scope for regional tiers

**Remediation:**
```bash
# Check actual schema
sqlite3 data/merit_registry.db "
  SELECT DISTINCT geography_scope, COUNT(*)
  FROM v6_peer_context_assignments
  WHERE run_id='v6_foundation_candidate_20260727_corrected'
  AND selected_tier='2_regional_conditional'
  GROUP BY geography_scope;
"

# Verify geography_value is also null
sqlite3 data/merit_registry.db "
  SELECT COUNT(*)
  FROM v6_peer_context_assignments
  WHERE run_id='v6_foundation_candidate_20260727_corrected'
  AND selected_tier='2_regional_conditional'
  AND geography_value IS NULL;
"

# Regenerate candidate with proper geography mapping
```

---

### Issue 3: Sample Organizations Not in Candidate Run ⚠️

**Severity:** HIGH (Cannot validate Tier assignments)

**Finding:**
- Test organizations not found in candidate run:
  - EIN 010000109 (expected Tier 1)
  - EIN 330520220 (expected Tier 2)
  - EIN 800421341 (expected Tier 3)
  - EIN 920970635 (expected Tier 4)
  - EIN 461200595 (expected Tier 5)

**Possible causes:**
1. Sample EINs are not in registry_enriched (not active 501c3)
2. Sample EINs are revoked
3. Sample EINs have invalid NTEE codes
4. Candidate run is only partial (incomplete assignments)

**Remediation:**
Verify sample organizations exist and what their current status is
```bash
sqlite3 data/merit_registry.db "
  SELECT EIN, organization_name, irs_revoked, NTEE1
  FROM registry_enriched
  WHERE EIN IN ('010000109', '330520220', '800421341', '920970635', '461200595');
"
```

---

## Data Quality Dashboard

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Total assignments | 1,910,561 | 1,910,561 | ✅ (if checking correct run) |
| Tier 1 Direct | ~330K | 336,735 | ✅ |
| Tier 2 Regional | ~890K | 893,721 | ✅ |
| Tier 3 Broader | ~48K | 48,401 | ✅ |
| Tier 4 National | ~10K | 10,547 | ✅ |
| Tier 5 Archetype | ~620K | 621,157 | ✅ |
| **Revoked in active** | **0** | **120,887** | ❌ CRITICAL |
| **Tier 2 with state scope** | **893,721** | **0** | ❌ CRITICAL |
| **Test org coverage** | **5/5** | **0/5** | ⚠️ NEEDS INVESTIGATION |

---

## Blocking Gates

**CANNOT PROCEED TO PRODUCTION STAGING until:**

1. ✅ All revoked organizations removed from Tier 1-4
2. ✅ All Tier 2 assignments have geography_scope = 'state' AND valid geography_value
3. ✅ Sample test organizations verified in candidate run
4. ✅ Validation script passes with 0 errors
5. ✅ Privacy check passes (8/8 gates)
6. ✅ New candidate report generated after fixes

---

## Recommendation

**Do NOT activate v6 in production with current candidate run.**

**Instead:**
1. Investigate root cause of revocation and geography issues
2. Implement pre-generation validation in scorer
3. Generate new candidate with fixes applied
4. Re-run full validation suite
5. Proceed to staging only after all 5 blocking gates pass

---

## Next Steps

1. **Immediately:** Investigate scorer implementation (scripts/v6_candidate_run_from_foundation.py)
2. **Run:** Remediation queries above to understand scope
3. **Fix:** Update scorer to populate required fields
4. **Regenerate:** Create fresh candidate with corrections
5. **Validate:** Re-run checklist with new candidate
6. **Report:** Update this document with remediation results

---

**This candidate run is NOT staging-ready. Remediation required.**
