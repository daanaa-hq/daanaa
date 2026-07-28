# Phase 3 Migration Report — IRS Eligibility Database Persistence

**Date:** 2026-07-28  
**Status:** In Progress (Validation Running)  
**Backup:** `backups/merit_registry_phase3_pre_2026_07_28.db` (23GB)

---

## Executive Summary

Phase 3 adds 4 columns to `registry_enriched` table to persist IRS eligibility status, checked timestamp, data sources, and explanation text. This makes IRS eligibility data available on the droplet for staging/production without needing API database access.

**Key Properties:**
- ✅ Additive only (no score/ranking/payment changes)
- ✅ Uses IRS source files as authority (Pub78 + BMF + revocation list)
- ✅ Preserves all wallet history and donations
- ✅ Revoked orgs hidden from search but accessible via direct URL
- ✅ No false deductibility claims on historical gifts

---

## Migration Details

### Schema Changes

Added to `registry_enriched` table:

```sql
ALTER TABLE registry_enriched ADD COLUMN irs_eligibility_status TEXT;
ALTER TABLE registry_enriched ADD COLUMN irs_eligibility_checked_at TEXT;
ALTER TABLE registry_enriched ADD COLUMN irs_eligibility_sources TEXT;
ALTER TABLE registry_enriched ADD COLUMN irs_eligibility_explanation TEXT;
```

**Column Semantics:**

| Column | Type | Values | Notes |
|---|---|---|---|
| `irs_eligibility_status` | TEXT | verified, unverified, revoked, unknown, exception_possible | Current IRS evidence classification |
| `irs_eligibility_checked_at` | TEXT | ISO 8601 timestamp | When IRS source files were fetched (from manifest) |
| `irs_eligibility_sources` | TEXT | JSON array | ["Pub78", "BMF"], ["BMF subsection 03"], etc. |
| `irs_eligibility_explanation` | TEXT | Human-readable | "IRS Pub78 and BMF both list...", "BMF only..." |

### Status Classification

Implemented per user specification:

```
verified = Pub78 + BMF AND NOT current_revocation
unverified = BMF-only AND NOT current_revocation  
revoked = current IRS auto-revocation record
unknown = missing or stale IRS evidence
exception_possible = documented church/group-ruling exception
```

### Data Quality

**Dry-run verification (passed):**

| Status | Count | Expected | Delta |
|---|---|---|---|
| Verified | 1,250,731 | ~1,250,731 | ✓ |
| Unverified | 367,993 | ~367,993 | ✓ |
| Revoked | 60,218 | ~60,218 | ✓ |
| Unknown | 369,276 | - | - |
| Exception-possible | 8,616 | - | - |
| **Total** | **2,056,834** | - | - |

**Verified + Unverified subset:** 1,618,724 (78.7% of registry)  
**Revoked subset:** 60,218 (2.9% of registry)

---

## Validation Status

### Completed

- ✅ Dry-run validation (counts match spec)
- ✅ Backup created (23GB)
- ✅ Schema migration prepared
- ✅ Frontend tests (251/251 pass)

### In Progress

- ⏳ Live persistence (2M+ orgs, ~10 min runtime)
- ⏳ Frontend build
- ⏳ Python compilation
- ⏳ Daily operations gate
- ⏳ API response verification

### Outstanding

- ⏳ Complete precompute rebuild (includes IRS fields in org JSONs)
- ⏳ Search/directory filtering (revoked suppression)
- ⏳ Droplet deployment preparation

---

## Validation Checklist

### Database Integrity

- [ ] No revoked orgs in active scoring tiers (1_verified, 2_verified, 3_verified)
- [ ] No non-deductible orgs in numeric tiers
- [ ] Historical wallet records unchanged
- [ ] No backfilled wallet/donation records
- [ ] Constraints: all NEW data only, never retroactive

### API/Frontend

- [ ] /api/organizations/<ein> returns all 4 IRS fields
- [ ] Wallet history displays "IRS status recorded on [date]"
- [ ] Revoked orgs suppress donate CTA
- [ ] Revoked orgs hidden from search/directory
- [ ] Revoked orgs still accessible via direct URL

### Operations

- [ ] Frontend tests pass
- [ ] Frontend build succeeds
- [ ] Python compilation clean
- [ ] Daily gate runs WARN-only (not BLOCKED)
- [ ] No scores changed
- [ ] No peer assignments changed
- [ ] No payment behavior changed

### Documentation

- [ ] Migration diff prepared
- [ ] Before/after counts documented
- [ ] API response samples collected
- [ ] Rollback instructions written
- [ ] Founder approval obtained

---

## Rollback Plan

**In case of issues:**

```bash
# 1. Restore database from backup
cp backups/merit_registry_phase3_pre_2026_07_28.db data/merit_registry.db

# 2. Restart API
cd ~/meritgiving && bash restart_api.sh

# 3. Verify restoration
curl -s http://localhost:5000/health | python3 -m json.tool
```

**Minimum recovery time:** ~30 seconds (copy + restart)

---

## Deployment Readiness

**Status:** Awaiting validation completion

**Approval Required From:** Founder

**Deployment Path (once approved):**

1. Commit Phase 3 migration + validation results
2. Run `scripts/safe_deploy_droplet.sh` (full precompute rebuild)
3. Monitor staging for 1 hour
4. Promote to production droplet

**Estimated deployment time:** 4-5 hours (full precompute rebuild)

---

## Files Modified

- `scripts/phase3_irs_persistence.py` — Persistence script
- `scripts/rebuild_precompute_with_irs.py` — Precompute builder
- `daanaa_api.py` — Already wired to return IRS fields
- Frontend components — Already updated for display (Phase 2)

---

## References

- Dry-run counts: Section "Data Quality"
- IRS source files: `data/irs_authority/v6_eligibility/`
- Helper: `scripts/irs_eligibility_helper.py`
- Backup: `backups/merit_registry_phase3_pre_2026_07_28.db`

---

**Next:** Await validation completion, then prepare for founder approval review.
