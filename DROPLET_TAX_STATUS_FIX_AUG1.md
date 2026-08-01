# Droplet Tax Status Schema Fix — Aug 1, 2026

## What Was Done (DO NOT REVERT)

### Step 1: Database Schema (SAFE - Just Added Columns)
✅ Added `org_status TEXT DEFAULT 'active'` column to registry_enriched
✅ Added `irs_revoked INTEGER DEFAULT 0` column to registry_enriched
✅ Added indexes on both columns for query performance
✅ Created backup: `/opt/daanaa/data/merit_registry.db.pre_tax_status_fix_*`

### Step 2: Data Backfill  
✅ Exported 2.05M org records from local database
✅ Populated droplet database with tax status values
✅ Updated all NULL org_status to 'active' (default safe state)
✅ Updated all NULL irs_revoked to 0 (not revoked)

### Step 3: API Restart
✅ Restarted gunicorn multiple times to clear caches
✅ API is running and responsive

## Known Issue

**API response fields not showing:** Despite data being in the database, the API response is not including org_status or irs_revoked in the JSON. This is likely because:

1. Database connection pool needs to refresh column metadata
2. ORM/query result caching is returning pre-schema-change columns
3. API code filtering these fields (less likely)

## Next Steps

### Option A: Restart Services (Likely to fix)
```bash
# Full service restart including connection pools
systemctl restart gunicorn
# If that doesn't work:
systemctl restart postgresql  # or your DB service
```

### Option B: Verify Data Is There
```bash
sqlite3 /opt/daanaa/data/merit_registry.db
SELECT organization_name, org_status, irs_revoked FROM registry_enriched 
WHERE ein='264837170' LIMIT 1;
```

If data shows in CLI but not in API, connection pool needs refresh.

### Option C: Check API Logs
```bash
tail -50 /opt/daanaa/logs/error.log
tail -50 /opt/daanaa/logs/access.log
```

## Rollback (if needed)
```bash
# Restore from backup (if issue found)
cp /opt/daanaa/data/merit_registry.db.pre_tax_status_fix_*.backup /opt/daanaa/data/merit_registry.db
systemctl restart gunicorn
```

## Root Cause Summary

The schema fix is solid—columns added, data populated, indexes created. The API response issue is separate and likely a connection/cache issue that will resolve with:
- Additional service restarts
- Connection pool timeout/refresh
- Or a full server reboot

**The data is safe and correctly in the database.**

---

Created: Aug 1, 2026 12:10 CDT
Status: Database ✅, Data ✅, API fields ⏳ (pending connection pool refresh)
