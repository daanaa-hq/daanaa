# V6 Staging Readiness — Final Checklist

**Date:** 2026-07-27 19:45 UTC  
**Status:** ✅ ALL GATES PASS — Ready for staging activation  
**Approval Required:** Founder only

---

## Final Verification Results

| Check | Result | Evidence |
|-------|--------|----------|
| **Database Integrity** | ✅ ok | `PRAGMA integrity_check` = ok |
| **Unit Tests** | ✅ 12/12 pass | unittest output |
| **Privacy Gates** | ✅ 8/8 pass | privacy_check.sh |
| **Validator Candidate** | ✅ PASSED | v6_foundation_candidate_20260728_revised |
| **Revoked in Active** | ✅ 0 | Database query verified |
| **Tier 2 Geography** | ✅ Census regions | All use Northeast/Midwest/South/West |
| **Revenue Bands** | ✅ Canonical | All lowercase validated |
| **Tier 1 Revenue** | ✅ Verified | All have valid bands |
| **Minimum Peers** | ✅ All ≥5 | Tiers 1-4 meet thresholds |
| **Tier 5 Safety** | ✅ No numbers | peer_median/p25/p75 all NULL |

---

## Ready for Staging

**All blocking conditions cleared:**

✅ Candidate run validated and clean  
✅ Data quality gates all pass  
✅ Privacy compliance verified  
✅ Approval gates functional  
✅ Feature flags disabled (production safe)  
✅ No unauthorized changes  

---

## Exact Steps to Enable Staging

### Step 1: Founder Approves Candidate
```bash
sqlite3 data/merit_registry.db \
  "UPDATE v6_scoring_runs SET status='approved' WHERE run_id='v6_foundation_candidate_20260728_revised';"

# Verify:
sqlite3 data/merit_registry.db "SELECT run_id, status FROM v6_scoring_runs WHERE run_id='v6_foundation_candidate_20260728_revised';"
# Expected: v6_foundation_candidate_20260728_revised|approved
```

### Step 2: Enable V6 Feature Flags
```bash
export ENABLE_V6_FINANCIAL_CONTEXT=true
export VITE_ENABLE_V6_FINANCIAL_CONTEXT=true
```

### Step 3: Restart Services
```bash
./restart_api.sh
cd frontend && npm run dev
```

### Step 4: Test Endpoints
```bash
# Test Tier 1 Direct
curl http://localhost:5000/api/organizations/010000109/financial-context | jq .

# Test Tier 5 Archetype
curl http://localhost:5000/api/organizations/461200595/financial-context | jq .
```

### Step 5: Run QA Checklist
See: `V6_STAGING_ACTIVATION_GUIDE.md`

---

## Decision Gate for Founder

**Question:** Approve staging activation?

**If YES:**
1. Run Step 1 command above
2. Notify dev team
3. QA will proceed with Steps 2-5

**If NO / Concerns:**
1. Document feedback
2. Return to dev for fixes
3. Regenerate candidate

---

## Known Gaps (Will Not Block Staging)

| Gap | Impact | Timing |
|-----|--------|--------|
| Backfill ingestion | Daily ops dry-run only | Implement post-staging |
| Revocation repair | No automatic fixes | Manual intervention |
| Fairness report | Candidate generation only | Score comparison later |

All marked **NOT_CONFIGURED** in reports — transparent and non-blocking.

---

## Document Reference

- **Overview:** `V6_OPERATIONS_HARDENING_REPORT_2026_07_27.md`
- **Decision Package:** `V6_FOUNDER_APPROVAL_PACKAGE_2026_07_27.md`
- **Staging Enable:** `V6_STAGING_ACTIVATION_GUIDE.md`
- **Operations Plan:** `V6_DAILY_WEEKLY_DATA_OPERATIONS_PLAN_2026-07-27.md`

---

## Summary

✅ **V6 system is operationally sound**  
✅ **Candidate run validated and clean**  
✅ **All safety gates passed**  
✅ **Staging can proceed immediately**  
⏳ **Awaiting founder decision**  

**Timeline:** 5 minutes to enable staging (Step 1-3) + 2-4 hours for QA