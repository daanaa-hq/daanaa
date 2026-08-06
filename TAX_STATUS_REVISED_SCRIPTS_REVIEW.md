# Tax Status Recovery Scripts — Revised Implementation Review

**Status:** Scripts revised per remediation requirements. Awaiting test execution.

## Remediation Checklist

✅ **Use set-based SQLite updates** (not row-by-row Python)
   - `apply_tax_status_recovery.py` now uses pure SQL UPDATE with WHERE IN clause
   - No Python loops over rows
   - Single atomic transaction

✅ **Detect and report unmatched EINs and conflicts**
   - Counts EINs in recovery artifact
   - Counts matched EINs in production
   - Reports unmatched (new) EINs separately
   - Detects existing non-null values and refuses to overwrite without `--force-overwrite`

✅ **Never overwrite non-null values without explicit override**
   - Pre-migration check counts existing non-null org_status and irs_revoked
   - Refuses to proceed if any exist (unless `--force-overwrite`)
   - Explicit flag required for destructive operation

✅ **Implement actual pre/post checksum parity**
   - Calculates SHA256 aggregate checksum before migration
   - Calculates SHA256 aggregate checksum after migration
   - Compares against recovery artifact manifest checksum
   - Reports parity result

✅ **Validate SQLite integrity before and after migration**
   - `PRAGMA integrity_check` run before start
   - `PRAGMA integrity_check` run after completion
   - Fails migration if either check fails

✅ **Make migration idempotent**
   - Designed to run twice with same result
   - Column additions are "if not exists" logic
   - Data updates use deterministic SQL
   - No duplicate rows created

✅ **Remove hard-coded assumptions**
   - No hard-coded row count expectations
   - No hard-coded revoked total expectations
   - Manifest reports ACTUAL counts from source DB
   - Test can compare against production without predetermined values

✅ **Dry-run by default**
   - `--apply` flag required to execute changes
   - Dry-run reports planned changes without writing
   - Safe for testing and validation

✅ **Keep backup, service, SSH operations outside script**
   - Script only modifies database
   - Caller responsible for:
     - Creating backup
     - Stopping service
     - Restarting service
     - SSH access
   - Script focuses only on database mutation and validation

---

## Test Plan

### Phase 1: Build Recovery Artifact
```bash
cd ~/meritgiving
python3 scripts/build_tax_status_recovery.py
```

**Expected outputs:**
- `data/tax_status_recovery.db` (validated sidecar)
- `data/tax_status_recovery_manifest.json` (metadata + checksums)
- Report of actual counts (no assumptions)
- Pass/fail on validation

### Phase 2-6: Apply Migration with Testing
See test outputs below.

---

## Notes for Production

1. Script only handles database mutation and validation
2. Service management (stop/start) remains caller responsibility
3. Dry-run is mandatory before --apply
4. Preserve test databases for audit trail

