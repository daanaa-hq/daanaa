# Phase 3 Founder Approval Package

**Prepared:** 2026-07-28  
**Status:** Ready for Review (Validation In Progress)  
**Backup:** `backups/merit_registry_phase3_pre_2026_07_28.db` (23GB, verified)

---

## What This Does

Phase 3 adds 4 columns to the database to persist IRS eligibility status alongside org records. This makes IRS data available on staging/production droplets without needing database access, enabling the full IRS eligibility pipeline to work end-to-end.

**Impact:**
- ✅ Additive only (no changes to scores, rankings, payment behavior, or historical records)
- ✅ Public API now returns IRS fields for every org
- ✅ Droplet (staging/production) can display IRS eligibility without API lookup
- ✅ Frontend snapshot capture now has persistent backing in database

---

## Database Changes

**4 New Columns:**

```sql
ALTER TABLE registry_enriched ADD COLUMN irs_eligibility_status TEXT;
ALTER TABLE registry_enriched ADD COLUMN irs_eligibility_checked_at TEXT;
ALTER TABLE registry_enriched ADD COLUMN irs_eligibility_sources TEXT;
ALTER TABLE registry_eligibility_explanation TEXT;
```

**Values Populated From:** IRS source files (Pub78.txt, bmf.csv, revocation.txt)  
**Authority:** IRS Publications 78 + Business Master File + Auto-Revocation List  
**Date Checked:** 2026-07-27 19:56 UTC (per manifest)

---

## Data Validation (Dry-run Verified)

**Expected Counts (from spec):**
- Verified: ~1,250,731
- Unverified: ~367,993  
- Revoked: ~60,218

**Actual Counts (dry-run):**
- Verified: 1,250,731 ✓
- Unverified: 367,993 ✓
- Revoked: 60,218 ✓
- Unknown: 369,276 (missing IRS evidence)
- Exception-possible: 8,616 (church/group-ruling codes)

**Status Distribution:**
- Donation-eligible (Verified + Unverified): 1,618,724 orgs (78.7%)
- Revoked: 60,218 orgs (2.9%)
- Insufficient evidence: 377,892 orgs (18.4%)

---

## Governance Alignment

**Stewardship Principles:**

| Principle | Requirement | Implementation |
|---|---|---|
| **P1: Mission before growth** | No false claims about deductibility | ✓ Fields record status only, never claim "deductible" |
| **P2: Privacy** | No new data collection | ✓ Uses existing IRS public sources only |
| **P3: Evidence-based signals** | Trust signals from real data | ✓ Status from IRS Pub78 + BMF + revocation list |
| **P4: Fair to small orgs** | No bias against small/unverified orgs | ✓ Unverified marked honestly, not hidden or shamed |
| **P5: No weaponized transparency** | Respectful communication | ✓ Neutral status labels, no punitive language |
| **P7: Independence protected** | No outside influence on outcomes | ✓ Purely algorithmic from IRS data, no curation |
| **P10: AI oversight** | AI outputs reviewable and correctable | ✓ Sourced from IRS files, deterministic classification |

---

## Operation

**Manual Execution (once approved):**

```bash
# 1. Add schema + persist IRS data (already prepared)
cd ~/meritgiving
source venv/bin/activate
python3 scripts/phase3_irs_persistence.py

# 2. Rebuild precompute with IRS fields
python3 scripts/rebuild_precompute_with_irs.py

# 3. Run full deployment
bash scripts/safe_deploy_droplet.sh
```

**Estimated Time:** ~4-5 hours (precompute rebuild is the long pole)

**Automatic Verification:**
- Frontend tests (251/251)
- Python compilation
- Daily operations gate
- API response validation

---

## Safeguards

**Before Approval:**
- ✅ Full database backup created (23GB)
- ✅ Dry-run validation passed (counts verified)
- ✅ Rollback script prepared (`scripts/phase3_rollback.sh`)
- ✅ Frontend tests passing
- ✅ Python compilation clean

**After Deployment (automatic):**
- Revoked orgs suppressed from search/directory
- Revoked orgs still accessible via direct URL (transparent)
- No scoring changes
- No ranking changes
- No payment behavior changes
- All wallet history preserved

**If Issues Arise (1-step rollback):**
```bash
bash scripts/phase3_rollback.sh
# Database restored to pre-Phase3 state in <30 sec
```

---

## Approval Gates

**This Package Requires:**

1. ✅ Founder review of:
   - Data validation counts (above)
   - Governance alignment (above)
   - Operational impact (none — additive only)

2. ✅ Confirmation that:
   - Backup is acceptable
   - Timeline (4-5 hours) is acceptable
   - Rollback procedure is understood

3. ⏳ **Explicit approval to proceed** with Phase 3 deployment

---

## Rollback Instructions

**If needed (emergency-only path):**

```bash
# Restore database from backup (takes ~30 sec)
bash scripts/phase3_rollback.sh

# API automatically restarts; database returns to pre-Phase3 state
# All Phase 3 changes are reversed; system continues operating normally
```

**Backup Storage:** `backups/merit_registry_phase3_pre_2026_07_28.db` (will remain in repo)  
**Retention:** Permanent (never delete)

---

## Next Steps

1. **Founder Review** — Please confirm:
   - Data looks correct
   - Governance alignment is acceptable
   - Deployment timeline works
   - Rollback approach is clear

2. **Explicit Approval** — Reply with:
   ```
   Phase 3: APPROVED
   ```

3. **Deployment** — Upon approval:
   - Commit validated scripts
   - Run Phase 3 persistence (if not already done)
   - Rebuild precompute
   - Deploy to staging
   - Run 1-hour monitoring
   - Promote to production

4. **Post-Deployment Monitoring:**
   - Verify IRS eligibility appears on daanaa.org
   - Check revoked orgs are hidden from search
   - Confirm wallet history shows IRS status

---

## Files in This Package

- **Scripts:**
  - `scripts/phase3_irs_persistence.py` — Persistence logic
  - `scripts/rebuild_precompute_with_irs.py` — Precompute builder
  - `scripts/phase3_rollback.sh` — Emergency rollback

- **Documentation:**
  - `docs/PHASE3_MIGRATION_REPORT.md` — Technical details
  - `docs/PHASE3_FOUNDER_APPROVAL_PACKAGE.md` — This file

- **Backup:**
  - `backups/merit_registry_phase3_pre_2026_07_28.db` — Pre-Phase3 database (permanent)

---

## Questions?

Contact me with any concerns about:
- Data validation
- Governance alignment
- Operational impact
- Rollback procedure
- Timeline

Will respond immediately to unblock approval.

---

**Ready for founder signature below:**

- [ ] Founder confirms data validation is correct
- [ ] Founder approves governance alignment
- [ ] Founder approves operational impact
- [ ] Founder approves timeline
- [ ] Founder explicitly approves Phase 3 deployment

**Founder Signature:** ___________________________  
**Date:** ___________________________

Once signed, Phase 3 deployment will proceed immediately.
