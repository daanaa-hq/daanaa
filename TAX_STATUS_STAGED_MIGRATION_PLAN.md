# Tax Status Staged Migration — Production-Grade Recovery Plan

**Approach:** Staged migration with deterministic reconciliation (smaller data movement, auditable changes, tested rollback)

**Status:** Ready for review and execution

---

## Overview

Rather than exporting millions of SQL statements or replacing an 11GB database, this plan:

1. **Phase 1:** Build a validated recovery artifact (SQLite sidecar) locally
2. **Phase 2:** Test on a production copy first
3. **Phase 3:** Verify row-level parity with checksums
4. **Phase 4:** Production cutover with documented rollback

---

## Phase 1: Build Recovery Artifact Locally

### Step 1.1: Generate Recovery Database

```bash
cd ~/meritgiving
python3 scripts/build_tax_status_recovery.py
```

**What it does:**
- Reads from local `data/merit_registry.db`
- Creates `data/tax_status_recovery.db` (sidecar database)
- Validates:
  - No duplicate EINs
  - No malformed EINs (non-9-digit)
  - `irs_revoked` ∈ {0, 1} only
  - Required fields not unexpectedly null
  - Row counts match baseline expectations
- Calculates SHA256 checksums for row-level parity verification
- Outputs `tax_status_recovery_manifest.json` with metadata

**Expected output:**
```
✅ Recovery artifact created successfully!
   Database: /home/akbar/meritgiving/data/tax_status_recovery.db
   Manifest: /home/akbar/meritgiving/data/tax_status_recovery_manifest.json

Summary:
   Total records: ~2,056,834
   Active: ~1,860,834
   Revoked: ~195,000
   Status breakdown: {"active": ..., "revoked": ..., "inactive": ...}
   Validation: PASSED
```

### Step 1.2: Review Recovery Manifest

```bash
cat ~/meritgiving/data/tax_status_recovery_manifest.json
```

**Verify:**
- `validation_passed: true`
- `total_records > 2,000,000`
- `revoked_organizations` matches expected baseline (~195K)
- `status_breakdown` has reasonable distribution
- No validation errors
- `source_integrity_check: "ok"`

---

## Phase 2: Validate Against Production Copy

### Step 2.1: Obtain Production Copy

**Option A: SSH snapshot (if droplet accessible)**
```bash
ssh root@162.243.97.179 << 'SNAPSHOT'
cp /opt/daanaa/data/merit_registry.db /opt/daanaa/data/merit_registry_backup_$(date +%s).db
SNAPSHOT
# Then download to local for testing
```

**Option B: Assume current local dev DB matches production (use with caution)**
- Current local DB has production snapshot from Aug 1 restoration
- Safe if you're certain no schema drift occurred since

### Step 2.2: Dry Run on Production Copy

```bash
# Create test copy
cp ~/meritgiving/data/merit_registry.db ~/meritgiving/data/merit_registry_test.db

# Run dry run (no changes)
python3 ~/meritgiving/scripts/apply_tax_status_recovery.py \
  --prod-db ~/meritgiving/data/merit_registry_test.db \
  --recovery-db ~/meritgiving/data/tax_status_recovery.db
```

**Expected output:**
```
[1/4] Validating production database...
  ✅ Valid. Rows: 2056834, columns: 76

[2/4] Loading recovery artifact...
  ✅ Loaded 2056834 recovery records

[3/4] Dry run (reporting intended changes)...
   will_add_org_status_column: True
   will_add_irs_revoked_column: True
   recovery_records: 2056834
   expected_matched: 2056834
   production_org_count: 2056834
   changes_summary: Add columns: org_status irs_revoked; Update 2056834 rows

Dry run complete. Use --apply to execute migration.
```

### Step 2.3: Verify on Test Copy

If running with `--apply`, verify parity:

```bash
sqlite3 ~/meritgiving/data/merit_registry_test.db << SQL
-- Row counts
SELECT 'Total orgs' as metric, COUNT(*) as value FROM registry_enriched
UNION ALL
SELECT 'With org_status', COUNT(*) FROM registry_enriched WHERE org_status IS NOT NULL
UNION ALL
SELECT 'Active (irs_revoked=0)', COUNT(*) FROM registry_enriched WHERE irs_revoked = 0
UNION ALL
SELECT 'Revoked (irs_revoked=1)', COUNT(*) FROM registry_enriched WHERE irs_revoked = 1
UNION ALL
SELECT 'Null irs_revoked', COUNT(*) FROM registry_enriched WHERE irs_revoked IS NULL;

-- Spot check: active org
SELECT ein, org_status, irs_revoked FROM registry_enriched WHERE ein = '264837170';

-- Spot check: revoked org (find one)
SELECT ein, org_status, irs_revoked FROM registry_enriched 
WHERE irs_revoked = 1 LIMIT 1;

-- Integrity
PRAGMA integrity_check;
SQL
```

**Expected results:**
- Total orgs: 2,056,834
- With org_status: 2,056,834 (or very close)
- Active: ~1,860,834
- Revoked: ~195,000
- Null irs_revoked: 0
- Sample org has org_status and irs_revoked values
- Integrity check: "ok"

---

## Phase 3: Verify Parity with Checksums

### Step 3.1: Calculate Checksums

**Locally (expected state):**
```bash
sqlite3 ~/meritgiving/data/tax_status_recovery.db << SQL > /tmp/recovery_checksums.txt
SELECT ein, source_checksum FROM tax_status_recovery 
ORDER BY ein;
SQL
```

**On test copy (actual state):**
```bash
# This would require updating the test to calculate matching checksums
# For now, verify data integrity manually (spot checks above)
```

### Step 3.2: Manual Spot Checks

Test at least:
- [ ] One active organization (org_status='active', irs_revoked=0)
- [ ] One revoked organization (org_status='revoked', irs_revoked=1)
- [ ] One inactive organization (org_status='inactive', irs_revoked=0)
- [ ] One unknown EIN (not in original database)
- [ ] One organization with unusual status

---

## Phase 4: Production Cutover

### Step 4.1: Pre-Flight Checklist

**Database & Service:**
- [ ] Confirm production database path: `/opt/daanaa/data/merit_registry.db`
- [ ] Confirm systemd service: `systemctl status gunicorn` (or documented service name)
- [ ] Confirm available disk space on droplet: `df -h /opt/daanaa/data/`
- [ ] Expect ~11GB for database, backup, and recovery artifact

**Access & Backup:**
- [ ] SSH access to droplet verified
- [ ] Backup mechanism documented and tested
- [ ] Rollback plan reviewed

**Artifact Transfer:**
- [ ] Recovery artifact uploaded to droplet: `/opt/daanaa/data/tax_status_recovery.db`
- [ ] Manifest uploaded: `/opt/daanaa/data/tax_status_recovery_manifest.json`
- [ ] Migration script uploaded: `/opt/daanaa/scripts/apply_tax_status_recovery.py`

### Step 4.2: Create Verified Backup

```bash
ssh root@162.243.97.179 << 'BACKUP'
set -e

PROD_DB="/opt/daanaa/data/merit_registry.db"
BACKUP_DIR="/opt/daanaa/data/backups"

# Create backup with timestamp
BACKUP_FILE="$BACKUP_DIR/merit_registry_pre_tax_status_fix_$(date +%Y%m%d_%H%M%S).db"
mkdir -p "$BACKUP_DIR"

# Create clean backup
cp "$PROD_DB" "$BACKUP_FILE"
chmod 600 "$BACKUP_FILE"

# Verify backup integrity
sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check" | grep -q "ok" && \
  echo "✅ Backup created and verified: $BACKUP_FILE" || \
  (echo "❌ Backup integrity check failed" && exit 1)

# Record backup checksum
sha256sum "$BACKUP_FILE" > "$BACKUP_FILE.sha256"

BACKUP
```

### Step 4.3: Dry Run on Production

```bash
ssh root@162.243.97.179 << 'DRYRUN'
cd /opt/daanaa

# Run dry run (no changes)
python3 scripts/apply_tax_status_recovery.py \
  --prod-db /opt/daanaa/data/merit_registry.db \
  --recovery-db /opt/daanaa/data/tax_status_recovery.db

# Review output carefully before proceeding
DRYRUN
```

### Step 4.4: Stop API Service

```bash
ssh root@162.243.97.179 << 'STOP'
# Use documented service manager, not pkill
systemctl stop gunicorn

# Verify stopped
sleep 2
systemctl status gunicorn || echo "Service stopped successfully"
STOP
```

### Step 4.5: Apply Migration

```bash
ssh root@162.243.97.179 << 'MIGRATE'
cd /opt/daanaa

# Apply changes (transactional)
python3 scripts/apply_tax_status_recovery.py \
  --prod-db /opt/daanaa/data/merit_registry.db \
  --recovery-db /opt/daanaa/data/tax_status_recovery.db \
  --apply

# Check exit code
if [ $? -eq 0 ]; then
  echo "✅ Migration applied successfully"
else
  echo "❌ Migration failed — rollback will be performed"
  exit 1
fi
MIGRATE
```

### Step 4.6: Verify Post-Migration

```bash
ssh root@162.243.97.179 << 'VERIFY'
sqlite3 /opt/daanaa/data/merit_registry.db << SQL
-- Integrity check
PRAGMA integrity_check;

-- Row counts
SELECT 'Total orgs' as metric, COUNT(*) as value FROM registry_enriched
UNION ALL
SELECT 'With org_status', COUNT(*) FROM registry_enriched WHERE org_status IS NOT NULL
UNION ALL
SELECT 'Revoked', COUNT(*) FROM registry_enriched WHERE irs_revoked = 1;

-- Sample query
SELECT ein, org_status, irs_revoked 
FROM registry_enriched 
WHERE ein IN ('264837170', '942345678') 
LIMIT 2;
SQL
VERIFY
```

### Step 4.7: Restart API Service

```bash
ssh root@162.243.97.179 << 'RESTART'
systemctl start gunicorn

# Wait for startup
sleep 5

# Verify running
systemctl status gunicorn || (echo "Service failed to start"; exit 1)

# Test health endpoint
curl -s http://localhost:5000/health | jq . || echo "Health check failed"
RESTART
```

### Step 4.8: Smoke Tests

```bash
# Test tax status endpoint (local proxy to droplet, or direct if accessible)
curl -s https://daanaa.org/api/organizations/264837170 | jq '.org_status, .irs_revoked'
# Expected: "active", 0

# Test search includes tax status
curl -s 'https://daanaa.org/api/search?q=health' | jq '.[0] | .org_status, .irs_revoked' 
# Expected: should include org_status and irs_revoked

# Monitor logs
ssh root@162.243.97.179 "tail -50 /var/log/gunicorn.log"
# Should be clean, no errors
```

### Step 4.9: Monitor (30+ minutes)

```bash
# Every 5 minutes for first 30 minutes:
watch -n 5 'curl -s http://localhost:5000/health && echo OK || echo FAILED'

# Check response times
curl -w "Time: %{time_total}s\n" -s https://daanaa.org/ > /dev/null
# Should be <2s
```

---

## Rollback Procedure

### If Validation Fails (Pre-Cutover)

```bash
# 1. Preserve failed database
ssh root@162.243.97.179 \
  cp /opt/daanaa/data/merit_registry.db \
     /opt/daanaa/data/merit_registry_FAILED_$(date +%s).db

# 2. Stop service
ssh root@162.243.97.179 systemctl stop gunicorn

# 3. Restore backup
ssh root@162.243.97.179 << 'RESTORE'
BACKUP_FILE=$(ls -1t /opt/daanaa/data/backups/merit_registry_pre_tax_status_fix_*.db | head -1)
cp "$BACKUP_FILE" /opt/daanaa/data/merit_registry.db
chmod 644 /opt/daanaa/data/merit_registry.db

# 4. Verify restored backup
sqlite3 /opt/daanaa/data/merit_registry.db "PRAGMA integrity_check"
RESTORE

# 5. Restart service
ssh root@162.243.97.179 systemctl start gunicorn

# 6. Re-run smoke tests
curl -s http://localhost:5000/health | jq .

# 7. Document incident
echo "Rollback completed. Failed DB preserved for investigation."
```

---

## Prevention Measures

### Schema Version Tracking

Add to `DECISIONS.md`:
```
2026-08-05: Database schema versioning introduced.
  - Migration files: database/migrations/028_tax_status_recovery.sql
  - Migration runner: scripts/apply_tax_status_recovery.py
  - Schema manifest: database/schema_manifest.json (schema version, column count, checksum)
  - Pre-deploy validation required
```

### Deployment Contract Check

Add to deployment script:
```bash
# Before syncing database to droplet:
python3 scripts/validate_schema_parity.py \
  --local-db ~/meritgiving/data/merit_registry.db \
  --remote-db /opt/daanaa/data/merit_registry.db

# Exit non-zero if schemas don't match
```

### Post-Deploy Smoke Test

```bash
# After restarting API, required:
curl -s https://daanaa.org/api/organizations/264837170 \
  | jq -e '.org_status and .irs_revoked' || exit 1
```

---

## Acceptance Criteria

✅ **Ready for review when:**

- [ ] Recovery artifact runs successfully on local database
- [ ] Dry run on test copy produces expected changes (no errors)
- [ ] Integrity checks pass before and after migration
- [ ] Spot checks show correct values (active, revoked, inactive orgs)
- [ ] Manifest validation passes
- [ ] Rollback procedure tested
- [ ] Exact production command documented
- [ ] Service name and database path confirmed
- [ ] Backup location and checksum procedure documented

✅ **Ready for production cutover when:**

- [ ] All review criteria passed
- [ ] Founder approval obtained
- [ ] Pre-flight checklist completed
- [ ] All communication sent (monitoring team, etc.)

---

## Decision Gate (Aug 5-7)

**Status:** Staged migration plan complete and ready for execution

**Your decision:**
- [ ] **Proceed with staged migration** (this plan)
- [ ] **Revert to safe backfill** (Option A from previous plan)
- [ ] **Request changes** (specify below)
- [ ] **Defer** (explain blocker)

---

**Next step:** Review this plan, verify it meets your standards, and approve for execution.

**Timeline once approved:** ~2 hours (1h local testing + dry run, 1h production cutover + monitoring)

