# Quick Fix Log — 2026-06-09

## Problem

**IRS data pipeline was broken for 8 days** (last update: June 1)

- `registry_enriched` table not updating despite cron jobs
- `auto_ingest.py` running every 2 hours but failing silently
- Real IRS scripts (`overnight_sync.py`, `overnight_pipeline.py`) not scheduled

## Root Cause Analysis

### Issue #1: auto_ingest.py Database Path Mismatch
```python
# WRONG (what it was):
DB_PATH = BASE / "data" / "db" / "merit.db"  # 11M, abandoned database

# CORRECT:
DB_PATH = BASE / "data" / "merit_registry.db"  # 9.4G, active database
```

**Impact**: auto_ingest.py was running every 2 hours but writing to the wrong database (which nobody was reading).

### Issue #2: Orphaned IRS Pipeline Scripts
- `overnight_sync.py` (IRS 990 merge & dedupe) — **not in cron**
- `overnight_pipeline.py` (ProPublica enrichment) — **not in cron**
- These are the actual IRS data pipeline but were never wired to the scheduler

### Issue #3: GPU Shutdown Race Condition
```bash
# BEFORE (race condition at 9 AM):
0 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop
0 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop_embed_server

# AFTER (staggered):
0 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop
5 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop_embed_server
```

## Fixes Applied

### ✅ Fix #1: Correct auto_ingest.py Database Path
**File**: `scripts/auto_ingest.py` line 7
```diff
- DB_PATH = BASE / "data" / "db" / "merit.db"
+ DB_PATH = BASE / "data" / "merit_registry.db"  # Fixed: was pointing to abandoned /data/db/merit.db
```

**Status**: Applied ✅

### ✅ Fix #2: Restore IRS Pipeline to Cron
**Crontab Changes**:

**Removed**:
```bash
0 */2 * * * cd ~/meritgiving && source venv/bin/activate && INGEST_BATCH=100 REBALANCE_THRESHOLD=10000 python3 scripts/auto_ingest.py >> ~/meritgiving/logs/auto_ingest.log 2>&1
```

**Added**:
```bash
# Core IRS pipeline (2:00-2:30 AM daily)
0 2 * * * cd ~/meritgiving && source venv/bin/activate && python3 scripts/overnight_sync.py >> logs/overnight_sync.log 2>&1
30 2 * * * cd ~/meritgiving && source venv/bin/activate && python3 scripts/overnight_pipeline.py >> logs/overnight.log 2>&1
```

**Status**: Applied ✅

### ✅ Fix #3: Fix GPU Shutdown Conflict
**Crontab Changes**:

**Changed from**:
```bash
0 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop_embed_server
```

**Changed to**:
```bash
5 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop_embed_server >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1
```

**Status**: Applied ✅

## Verification

```bash
# Check crontab has been updated
$ crontab -l | grep -E "overnight_sync|overnight_pipeline"
0 2 * * * cd ~/meritgiving && source venv/bin/activate && python3 scripts/overnight_sync.py >> logs/overnight_sync.log 2>&1
30 2 * * * cd ~/meritgiving && source venv/bin/activate && python3 scripts/overnight_pipeline.py >> logs/overnight.log 2>&1

# Both scripts pass syntax check
$ python3 -m py_compile scripts/overnight_sync.py
$ python3 -m py_compile scripts/overnight_pipeline.py
✅ Both OK
```

## Expected Behavior (Starting 2026-06-10)

**Daily at 2:00 AM**:
1. `overnight_sync.py` runs
   - Dedupes `registry_enriched` by highest revenue per EIN
   - Merges new 990 XML filings from IRS
   - Recalculates peer percentiles
   - Expected duration: 30-60 min

2. At 2:30 AM, `overnight_pipeline.py` runs
   - Enriches new orgs with ProPublica data
   - Checks for IRS revocations
   - Ingests manual link submissions
   - Expected duration: 60-120 min

**Expected Result**:
- `registry_enriched.updated_at` will have new timestamps (daily)
- Database will be current within 24 hours of new IRS filings

## Monitoring

### Watch the logs
```bash
tail -f logs/overnight_sync.log logs/overnight.log
```

### Check database updates
```bash
sqlite3 data/merit_registry.db "SELECT MAX(updated_at) FROM registry_enriched;"
```

### Check for errors
```bash
grep -i error logs/overnight_sync.log logs/overnight.log
```

## Rollback

If issues arise:
```bash
crontab /tmp/crontab_before.txt  # Restore previous crontab
```

## Related Work

- **Full consolidation** (Option B): See `CONSOLIDATION_ROADMAP.md`
- **Ecosystem audit**: See `AGENT_ECOSYSTEM_AUDIT.md`
- **Master orchestrator**: See `scripts/master_orchestrator.py` (for future consolidation)

## Timeline

| Time | Event |
|------|-------|
| 2026-06-01 19:59 | Last registry_enriched update before fix |
| 2026-06-01 → 06-09 | Registry stale (8 days), auto_ingest silently failing |
| 2026-06-09 03:45 | Quick fixes applied |
| 2026-06-10 02:00 | First run of restored IRS pipeline |
| 2026-06-10 03:30 | Expected: registry_enriched updated with 9 days of new data |

