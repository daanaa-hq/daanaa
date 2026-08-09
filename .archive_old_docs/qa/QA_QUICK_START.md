# QA Quick Start — Search Performance Fix (2026-07-24)

## What Changed

Search was timing out (60+ seconds). **Root cause:** FTS index was missing 298K orgs. **Fixed in 11 seconds.**

## What to Test (Priority Order)

### 🔴 Critical Path (Must Pass)
1. **Search works** — `curl http://127.0.0.1:5000/api/search?q=health`
   - ✅ Expected: 20 results in <500ms
   
2. **Volunteer page loads** — Navigate to `/volunteer`
   - ✅ Expected: Events load without clicking search, <2s page render

3. **Health check passes** — `bash scripts/health_check.sh`
   - ✅ Expected: All checks green (homepage, directory, volunteer, API)

### 🟡 Important (Should Pass)
4. **Events work end-to-end**
   - Search events by keyword/location
   - Click event → detail loads
   - Click "Interested" → email modal → submit

5. **Performance benchmarks**
   - 5 concurrent searches all complete in <1s
   - No 503/504 errors under load

6. **Monitoring starts** — `bash scripts/monitor_site_health.sh &`
   - Expected: Logs appear in `logs/monitor.log` every 5 minutes
   - Expected: Detects failures and attempts recovery

### 🟢 Nice-to-Have (Regression Tests)
7. **Hyphenated searches work** — `curl http://127.0.0.1:5000/api/search?q=4-H`
   - ✅ Expected: Returns 4-H orgs (was broken in 2026-07-18)

8. **No revoked orgs in results** — Browse directory
   - ✅ Expected: All orgs active/deductible

---

## Test Environment

**API:** `http://127.0.0.1:5000` (local dev)  
**Frontend:** `http://localhost:5173` (Vite dev) or deployed droplet  
**Database:** `/home/akbar/meritgiving/data/merit_registry.db`  
**Logs:** `/home/akbar/meritgiving/logs/`

---

## Success Criteria

| Metric | Before Fix | After Fix | Pass? |
|--------|-----------|-----------|-------|
| Search latency (p50) | 60s+ timeout | <400ms | ✅ |
| Search latency (p95) | N/A | <800ms | ✅ |
| Volunteer page load | N/A | <2s | ✅ |
| FTS index sync | 298K missing | 2.056M ✓ | ✅ |
| Health check status | N/A | All green | ✅ |
| Concurrent searches (10x) | N/A | All complete | ✅ |
| Hyphen handling | Broken | Works | ✅ |

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `scripts/rebuild_fts_index_quick.sh` | Rebuilds FTS index if needed |
| `scripts/health_check.sh` | Verifies site health post-deployment |
| `scripts/monitor_site_health.sh` | Continuous monitoring (5-min checks) |
| `scripts/diagnose_search_perf.py` | Full diagnostics if search is slow |
| `logs/health_check.log` | Health check results |
| `logs/monitor.log` | Continuous monitoring log |
| `logs/fts_rebuild.log` | FTS rebuild log |

---

## Quick Sanity Checks

```bash
# 1. Is search fast?
time curl -s "http://127.0.0.1:5000/api/search?q=health" | jq '.total'
# Expected: <500ms, returns number like 165199

# 2. Is FTS in sync?
sqlite3 /home/akbar/meritgiving/data/merit_registry.db \
  "SELECT (SELECT COUNT(*) FROM registry_enriched) as registry, (SELECT COUNT(*) FROM org_fts) as fts"
# Expected: 2056834 | 2056834

# 3. Is health check green?
bash scripts/health_check.sh 2>&1 | grep -E "(ERROR|✓)"
# Expected: All ✓ checks, no ERROR lines

# 4. Does monitoring log?
tail logs/monitor.log | head -5
# Expected: Recent timestamps (~5 min apart)
```

---

## If Search is Still Slow

Run the full diagnostics:
```bash
python3 scripts/diagnose_search_perf.py
```

Expected output:
```
✓ Database Health
✓ FTS Query Performance
✓ Full Search Simulation
✓ API Endpoint
```

If any check fails, that's the bottleneck.

---

## If Tests Fail

1. **Search returns 0 results** → Run `rebuild_fts_index_quick.sh`
2. **Health check fails** → Check API is running (`ps aux | grep gunicorn`)
3. **Monitoring won't start** → Check `logs/` directory is writable
4. **Events page blank** → Check browser console for JS errors
5. **Email modal won't submit** → Check API is reachable from frontend

---

## Sign-Off Template

```
QA Tester: ___________________
Date: ___________________
Environment: [dev/prod/staging]

Critical Path: ✅ PASS / ❌ FAIL
Important: ✅ PASS / ❌ FAIL (failures: _______________________)
Regression Tests: ✅ PASS / ❌ FAIL (failures: _______________________)

Overall Result: ✅ READY FOR PRODUCTION / ❌ NEEDS FIXES
```

---

## Full Checklist

See `QA_CHECKLIST_2026_07_24.md` for detailed test cases (8 sections, 50+ test cases).

**Estimated time to test:** 45-60 minutes  
**Can be parallelized:** Yes (search + monitoring tests can run concurrently)
