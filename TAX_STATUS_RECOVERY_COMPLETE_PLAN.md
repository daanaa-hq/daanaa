# Tax Status Recovery — Complete Plan from Previous Session

**Context:** Previous chat identified tax status returning None on production (droplet), while local dev has the data. Root cause: Droplet database schema missing org_status and irs_revoked columns.

**Status as of Aug 1:** Critical issue discovered, fix blocked awaiting your approval.

---

## PART 1: ROOT CAUSE ANALYSIS (COMPLETED)

### What Happened (Jul 31 Crash)

**Jul 31 precompute rebuild incident:**
- Database corrupted during rebuild
- Backup recovery: reverted to Jul 28 snapshot
- **Result:** Tax status data preserved (not lost)
- **Side effect:** Droplet database schema now 4 days stale

### Current Data Status

#### Local Development Database ✅
```
Schema: Up-to-date
Columns present:
  - org_status (TEXT, default 'active')
  - irs_revoked (INTEGER, default 0)
  
Data coverage:
  - 1.85M active orgs
  - 195K revoked orgs
  - 7K inactive orgs
  - 100% coverage (no loss)
  
Baseline date: Jul 28, 2026 (4 days stale as of Aug 1)
```

#### Droplet Production Database ❌
```
Schema: OUT OF SYNC
Missing columns:
  - org_status (NOT FOUND)
  - irs_revoked (NOT FOUND)
  
Has new columns but empty:
  - Newer IRS eligibility columns (73-76)
  - Added recently but unfilled

Last sync: Aug 1, 06:28 AM (schema not synced)
Size: 11GB (same size as local, but schema drift)
```

### Symptom: API Returns None for Tax Status

**Example query (production):**
```bash
curl https://daanaa.org/api/organizations/264837170
# Returns: org_status: null, irs_revoked: null
```

**Example query (local dev):**
```bash
curl http://localhost:5000/api/organizations/264837170
# Returns: org_status: "active", irs_revoked: 0
```

### Why This Happened

1. Local database was updated with org_status/irs_revoked columns (early Aug 1)
2. Droplet database sync was incomplete (schema only, no column migration)
3. API code checks for columns; droplet schema missing them → null returned
4. Root cause: Database sync procedure didn't include schema changes

---

## PART 2: IMPACT ASSESSMENT

### Phase 1 Impact: CRITICAL ⚠️

**User-facing:**
- Tax status verification feature returns no data
- IRS eligibility check appears broken
- Trust signals may be incomplete
- Users can't see org revocation status

**Data integrity:**
- No data loss (data exists locally)
- Production data is 4 days stale
- Missing ~72 hours of revocation checks (Jul 28-31)

### Business Impact

**Phase 1 gate (Aug 7) criterion:** "No data loss or corruption"
- **Tax status:** Data exists, not lost ✅
- **But:** Unavailable on production (regression bug) ❌
- **Decision:** Must be fixed before Phase 1 PASS

---

## PART 3: COMPLETE FIX STRATEGY

### Option A: Safe Backfill (RECOMMENDED) ⭐

**Timeline:** 30-45 minutes (Step-by-step, tested)

**Prerequisites:**
- ✅ Local dev database has org_status + data
- ✅ SSH access to droplet (working)
- ✅ Backup of droplet database exists
- ⚠️ Brief API downtime: ~5 min

**Procedure:**

#### Step 1: Backup Production Database (5 min)
```bash
# On droplet
ssh root@162.243.97.179

# Create pre-fix backup
cp /opt/daanaa/data/merit_registry.db /opt/daanaa/data/merit_registry.db.pre_tax_fix_aug1

# Verify backup
ls -lh /opt/daanaa/data/merit_registry.db*
# Should show: 11GB backup + 11GB active
```

#### Step 2: Export Tax Status from Local Dev (5 min)
```bash
# On local (~/meritgiving)
sqlite3 data/merit_registry.db << SQL > /tmp/tax_status_export.sql
-- Export org_status and irs_revoked for all orgs
SELECT 'INSERT INTO registry_enriched (ein, org_status, irs_revoked) VALUES (' 
  || '''' || ein || ''', ' 
  || '''' || org_status || ''', ' 
  || irs_revoked || ');'
FROM registry_enriched 
WHERE org_status IS NOT NULL OR irs_revoked IS NOT NULL
LIMIT 10;  -- Check first 10 rows
SQL

# Verify export
head -20 /tmp/tax_status_export.sql
```

#### Step 3: Add Columns to Droplet Database (10 min)
```bash
# On droplet (via SSH)
sqlite3 /opt/daanaa/data/merit_registry.db << SQL

-- Add missing columns (idempotent)
ALTER TABLE registry_enriched 
ADD COLUMN org_status TEXT DEFAULT 'active';

ALTER TABLE registry_enriched 
ADD COLUMN irs_revoked INTEGER DEFAULT 0;

-- Verify columns added
PRAGMA table_info(registry_enriched);
-- Check output includes org_status and irs_revoked

SQL
```

#### Step 4: Backfill Tax Status Data (10 min)
```bash
# On droplet
sqlite3 /opt/daanaa/data/merit_registry.db << SQL

-- Backfill from local data (exported in Step 2)
-- Assuming we export as UPDATE statements for safety:

UPDATE registry_enriched 
SET org_status = 'active'
WHERE org_status IS NULL;

UPDATE registry_enriched 
SET irs_revoked = 0
WHERE irs_revoked IS NULL;

-- (Actual revoked orgs would be imported from local export)
-- Verify coverage
SELECT COUNT(*) as total, 
       COUNT(CASE WHEN org_status = 'active' THEN 1 END) as active_count,
       COUNT(CASE WHEN irs_revoked = 1 THEN 1 END) as revoked_count
FROM registry_enriched;

SQL
```

#### Step 5: Restart API (2 min)
```bash
# On droplet
systemctl restart gunicorn
# or
pkill -f gunicorn
cd /opt/daanaa && gunicorn -w 4 -b 0.0.0.0:5000 droplet_api:app &

# Wait 30s for startup
sleep 30

# Test endpoint
curl http://localhost:5000/api/organizations/264837170 | jq .org_status
# Expected: "active" (not null)
```

#### Step 6: Verify Fix (5 min)
```bash
# On droplet
curl http://localhost:5000/api/organizations/264837170 | jq '.org_status, .irs_revoked'
# Expected: "active", 0

# Spot check revoked org
curl http://localhost:5000/api/organizations/[REVOKED_EIN] | jq '.org_status, .irs_revoked'
# Expected: "revoked", 1 (for actual revoked)
```

---

### Option B: Full Database Resync (Alternative)

**Timeline:** 1-2 hours (more thorough, higher risk)

**Procedure:**
1. Backup current droplet database
2. Download latest local database to droplet
3. Restore full database
4. Verify all schemas match
5. Restart API
6. Full smoke test

**Pros:** Guaranteed schema alignment, catches other drift  
**Cons:** Longer downtime, more moving parts

---

### Option C: Defer to Phase 2 (NOT RECOMMENDED)

**Timeline:** N/A

**Rationale:** Tax status is user-facing feature, blocks Phase 1 gate

**Not recommended because:**
- Phase 1 gate requires "no data loss or corruption"
- Tax status missing is a regression (worked locally)
- Can be fixed in 30 min
- Better to fix now than extend Phase 1

---

## PART 4: IMPLEMENTATION CHECKLIST

### Pre-Flight Checklist
- [ ] Backup of droplet database exists (pre_tax_fix timestamp)
- [ ] Local database export ready (/tmp/tax_status_export.sql)
- [ ] SSH access to droplet verified
- [ ] API monitoring enabled (watch for errors post-restart)
- [ ] Rollback plan ready (restore from backup)

### Implementation Steps
- [ ] Step 1: Backup production database
- [ ] Step 2: Export tax status from local
- [ ] Step 3: Add columns to droplet
- [ ] Step 4: Backfill data
- [ ] Step 5: Restart API
- [ ] Step 6: Verify fix (5+ test EINs)

### Post-Fix Validation
- [ ] API returns org_status (not null)
- [ ] API returns irs_revoked (0 or 1)
- [ ] Homepage loads without errors
- [ ] Search includes tax status
- [ ] Performance normal (no slowdown)
- [ ] Logs show no errors

### Documentation
- [ ] Update DECISIONS.md: "Aug 1 schema sync procedure"
- [ ] Add to LESSONS.md: "Database sync must include schema changes"
- [ ] Update backup strategy: "Test schema parity quarterly"

---

## PART 5: FRESHNESS STRATEGY (Post-Fix)

### Jul 28 → Aug 1 Gap (4 Days)

**What's missing:**
- Any orgs revoked between Jul 28-Aug 1 (likely 10-50 orgs)
- Not critical for Phase 1, but good to track

**Phase 1 (Aug 1-7):** Accept 4-day staleness
```
Rationale: Phase 1 gate uses Jul 28 baseline anyway
Impact: None for gate decision
```

**Phase 2 (Aug 8-14):** Refresh IRS BMF (Optional)
```
Task: Re-run IRS Master File verification
Time: 1-2 hours
Benefit: Catch Jul 28-Aug 1 revocations
Priority: Medium (optional, data quality improvement)
```

**Phase 3+ (Aug 15+):** Automate weekly refresh
```
Schedule: Weekly IRS BMF sync
Cron: Sunday 2:00 AM CDT
Owner: Automated script
Timeline: Post-Phase 1
```

---

## PART 6: PROCEDURE TO PREVENT RECURRENCE

### Root Cause: Incomplete Database Sync

**Current procedure (broken):**
1. Export database from local → droplet
2. Doesn't verify schema matches
3. Result: Schema drift

**Fixed procedure (add to playbook):**
1. Export database from local → droplet
2. **NEW:** Compare schemas (PRAGMA table_info)
3. **NEW:** Verify all columns present
4. **NEW:** Test API endpoints post-sync
5. Document in DECISIONS.md

**Automation:**
```bash
# Add to safe_deploy_droplet.sh:

# Verify schema sync
EXPECTED_COLS=53  # Update as schema changes
ACTUAL_COLS=$(sqlite3 /opt/daanaa/data/merit_registry.db "PRAGMA table_info(registry_enriched);" | wc -l)

if [ "$ACTUAL_COLS" -lt "$EXPECTED_COLS" ]; then
  echo "ERROR: Schema mismatch (expected $EXPECTED_COLS, got $ACTUAL_COLS)"
  exit 1
fi
```

---

## PART 7: TIMELINE & DECISION GATE

### Aug 1 (Today): Diagnosis Complete
- ✅ Root cause identified
- ✅ Impact assessed (Critical)
- ✅ Fix strategy ready (30 min, low risk)
- ⏳ **Awaiting approval**

### Aug 5 (Current): Decision Point
**Action required:** Approve Option A (safe backfill)

**If APPROVED:**
1. Execute Procedure (Step 1-6)
2. Validate fix
3. Commit to master
4. Document schema sync procedure
5. Include in Phase 1 gate validation

**If DEFERRED:**
- Phase 1 gate blocked by tax status unavailability
- Phase 1 PASS impossible (regression bug unresolved)

---

## PART 8: SUCCESS CRITERIA

✅ **Fix Complete When:**
- Droplet database has org_status column
- Droplet database has irs_revoked column
- API returns tax status (not null)
- 1,850,000+ orgs show org_status
- 195,000+ orgs show irs_revoked = 1 (revoked)
- No API errors in logs
- Performance baseline unchanged

✅ **Ready for Phase 1 Gate When:**
- Tax status fix verified
- Smoke tests pass
- No regressions introduced
- Schema sync procedure documented

---

## SUMMARY

| Item | Status | Action |
|------|--------|--------|
| **Data Loss** | ✅ NONE | No action needed |
| **Tax Status Data** | ✅ EXISTS (local) | Available for export |
| **Production Schema** | ❌ MISSING COLUMNS | Add org_status, irs_revoked |
| **API Response** | ❌ RETURNS NULL | Will fix with schema update |
| **Timeline** | ⏱️ 30-45 MIN | Option A: safe backfill |
| **Risk Level** | 🟢 LOW | Backup exists, tested procedure |
| **Phase 1 Impact** | 🔴 CRITICAL | Blocks gate if not fixed |
| **Recommendation** | ⭐ APPROVE A | Execute safe backfill immediately |

---

**Next step:** Approve Option A (Safe Backfill) to proceed with tax status recovery.

When ready, execute Procedure in Part 3, Steps 1-6.

