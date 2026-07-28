# Phase 3 Deployment Log

**Started:** 2026-07-28 00:50 UTC  
**Approval:** ✅ Founder approved  
**Status:** Deployment in progress

---

## Deployment Steps

### Step 1: Precompute Rebuild with IRS Fields

**Status:** ⏳ Running  
**Expected:** <30 min (2.05M org JSONs)  
**Started:** 00:50 UTC

**What this does:**
- Loads IRS eligibility data from database
- Rebuilds org detail JSON files in `precompute_output/orgs/`
- Each file includes the 4 IRS fields:
  - irs_eligibility_status
  - irs_eligibility_checked_at
  - irs_eligibility_sources
  - irs_eligibility_explanation

### Step 2: Full Droplet Deployment (Safe Deploy)

**Expected:** ~4-5 hours total  
**Will:** Build SPA + sync database snapshot + deploy precompute to staging

```bash
bash scripts/safe_deploy_droplet.sh
```

### Step 3: Staging Smoke Tests

**Tests:**
- Homepage loads (200)
- /directory works (200)
- /api/organizations/<ein> returns IRS fields (200)
- Revoked orgs hidden from search (✓)
- Revoked orgs accessible via direct URL (✓)
- Wallet history displays IRS status (visual QA)

### Step 4: Production Promotion

**Gate:** 1-hour staging monitoring  
**Decision:** Promote to production if no issues

---

## Checkpoints

- [ ] Precompute rebuild completes
- [ ] Safe deploy script runs
- [ ] Staging homepage loads
- [ ] IRS fields in API responses
- [ ] Revoked suppression working
- [ ] 1-hour monitoring complete
- [ ] Promoted to production

---

## Rollback Plan

**If needed at any point:**

```bash
bash scripts/phase3_rollback.sh
# Database restored in <30 sec
```

**Backup location:** `backups/merit_registry_phase3_pre_2026_07_28.db`

---

**Next notification:** Precompute rebuild completion
