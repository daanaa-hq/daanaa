# QA Test Matrix — Search Fix Testing (2026-07-24)

**Purpose:** Quick reference showing what to test, how to test it, and expected results.  
**Format:** 3-column table (Test | Steps | Expected Result)

---

## Priority 1: Critical Path (⏱ 10 minutes)

Must pass all of these.

### 1.1 Search is Fast
| Test | Steps | Expected |
|------|-------|----------|
| Basic search | `curl http://127.0.0.1:5000/api/search?q=health` | HTTP 200, ~20 results, <500ms |
| Multi-word search | `curl http://127.0.0.1:5000/api/search?q=food+bank` | HTTP 200, results in <500ms |
| Search with no results | `curl http://127.0.0.1:5000/api/search?q=xyz123notreal` | HTTP 200, `total: 0`, <100ms |

### 1.2 Volunteer Page Loads
| Test | Steps | Expected |
|------|-------|----------|
| Page loads | Navigate to `/volunteer` | Page renders <2s, events visible |
| Auto-load 10 events | Page loads with no user interaction | 10 events display in event list |
| Events are clickable | Click first event title | Event detail page loads <1s |

### 1.3 Health Check Passes
| Test | Steps | Expected |
|------|-------|----------|
| Run health check | `bash scripts/health_check.sh` | All checks green, exit code 0 |
| Homepage check | Review output | Shows `Homepage: 200` |
| Directory check | Review output | Shows `Directory: 200` |
| Volunteer check | Review output | Shows `Volunteer: 200` |
| API health check | Review output | Shows `Health endpoint: 200` |

---

## Priority 2: Important (⏱ 20 minutes)

Should pass all of these.

### 2.1 Events Full Flow
| Test | Steps | Expected |
|------|-------|----------|
| Search by keyword | On `/volunteer`, type "food" | Events filtered <1s, count decreases |
| Search by location | Type "New York" in location field | Only NY events show |
| Filter by date | Select "This Week" | Only events within 7 days |
| No results state | Search "xyz123notreal" | Shows "No events found" message |

### 2.2 Interest Capture
| Test | Steps | Expected |
|------|-------|----------|
| Modal opens | Click "Interested in volunteering?" | Modal appears with email form |
| Email validation | Click submit without email | Shows error or disables submit |
| Submit email | Enter valid email, click submit | Modal closes, success message |
| Error handling | Simulate network error | Shows error message, can retry |

### 2.3 Performance Under Load
| Test | Steps | Expected |
|------|-------|----------|
| 5 concurrent searches | `for i in {1..5}; do curl -s http://127.0.0.1:5000/api/search?q=health & done; wait` | All complete <1s, no 503/504 |
| 10 concurrent searches | Same but `{1..10}` | All complete <2s |
| Load test with ab | `ab -n 100 -c 10 http://127.0.0.1:5000/api/search?q=health` | 0 failed requests |

### 2.4 FTS Index Sync
| Test | Steps | Expected |
|------|-------|----------|
| Registry count | `sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched"` | Returns 2,056,834 |
| FTS count | `sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM org_fts"` | Returns 2,056,834 |
| Counts match | Compare both | Exactly equal (0% drift) |
| FTS triggers exist | `sqlite3 data/merit_registry.db "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='registry_enriched'"` | Shows org_ai, org_ad, org_au |

### 2.5 Monitoring Infrastructure
| Test | Steps | Expected |
|------|-------|----------|
| Monitor starts | `bash scripts/monitor_site_health.sh &` | Logs appear in `logs/monitor.log` |
| Check interval | Let run 15 min, count log lines | ~3-4 checks per 5-min cycle |
| Recovery attempt | Stop API, wait 5 min | Log shows alert, recovery attempt |
| Stop monitor | `pkill -f monitor_site_health.sh` | Process exits cleanly |

---

## Priority 3: Regression Tests (⏱ 15 minutes)

Should still work after the fix.

### 3.1 2026-07-18 Fixes (Search Quality)
| Test | Steps | Expected |
|------|-------|----------|
| Hyphen handling | `curl http://127.0.0.1:5000/api/search?q=4-H` | Returns 4-H orgs, no SQL error |
| AND/OR literal | `curl http://127.0.0.1:5000/api/search?q=AND+OR` | Results for literal terms, not boolean |
| Apostrophe handling | `curl http://127.0.0.1:5000/api/search?q=L%27Anse` | L'Anse orgs found, no error |

### 3.2 2026-06 Fixes (Data Quality)
| Test | Steps | Expected |
|------|-------|----------|
| Revoked orgs excluded | `curl http://127.0.0.1:5000/api/organizations?per_page=100` | No `irs_revoked=1` orgs in results |
| Deductible only | Review org_status field | All orgs have `org_status='active'` |
| Zero-result fallback | Search something very obscure | Shows "No results" message (not error) |

### 3.3 2026-07-05 Fixes (Droplet Architecture)
| Test | Steps | Expected |
|------|-------|----------|
| Droplet serves static | Deploy runs, check droplet | Data loads without proxying home API |
| No embeddings needed | Search works on droplet | Search doesn't hang (no embedding load) |
| Search on droplet | Hit live droplet endpoint | Returns results quickly |

---

## Priority 4: Edge Cases (⏱ 10 minutes)

Optional but good to verify.

### 4.1 Query Edge Cases
| Test | Steps | Expected |
|------|-------|----------|
| Empty query | `curl http://127.0.0.1:5000/api/search?q=` | HTTP 400, "q param required" |
| Very long query | `curl http://127.0.0.1:5000/api/search?q=...` (500 chars) | HTTP 200 or graceful error |
| Special characters | `curl http://127.0.0.1:5000/api/search?q=%40%23%24` | Handled safely, no SQL error |
| Unicode query | `curl http://127.0.0.1:5000/api/search?q=café` | Results if orgs match |

### 4.2 Pagination
| Test | Steps | Expected |
|------|-------|----------|
| Page 1 | `curl http://127.0.0.1:5000/api/search?q=health&page=1&per_page=10` | First 10 results |
| Page 2 | `curl http://127.0.0.1:5000/api/search?q=health&page=2&per_page=10` | Results 11-20 |
| Page bounds | Request page 9999 | HTTP 200, empty results array |
| Per-page limits | `per_page=100` | Returns 100 results (or max allowed) |

### 4.3 Browser Console Health
| Test | Steps | Expected |
|------|-------|----------|
| Homepage errors | Open `/`, check console | No red error messages |
| Directory errors | Open `/directory`, check console | No errors |
| Volunteer errors | Open `/volunteer`, check console | No errors |
| Search errors | Do a search, check console | No errors |

---

## Quick Test Commands (Copy-Paste Ready)

### Search Performance
```bash
# Single search
time curl -s "http://127.0.0.1:5000/api/search?q=health" | jq '.total'

# Multiple searches (log times)
for q in health food bank volunteer donate; do
  echo "Query: $q"
  time curl -s "http://127.0.0.1:5000/api/search?q=$q" > /dev/null
done

# Concurrent (10 parallel)
ab -n 100 -c 10 "http://127.0.0.1:5000/api/search?q=health"
```

### FTS Index Health
```bash
# Check sync status
sqlite3 /home/akbar/meritgiving/data/merit_registry.db \
  "SELECT 'Registry: ' || COUNT(*) FROM registry_enriched UNION ALL SELECT 'FTS: ' || COUNT(*) FROM org_fts"

# Check triggers
sqlite3 /home/akbar/meritgiving/data/merit_registry.db \
  "SELECT name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='registry_enriched'"

# Quick coverage check
sqlite3 /home/akbar/meritgiving/data/merit_registry.db \
  "SELECT COUNT(*) as 'Health orgs' FROM org_fts WHERE org_fts MATCH 'health'"
```

### Monitoring Health
```bash
# Check if monitoring is running
ps aux | grep monitor_site_health

# View recent checks
tail -20 logs/monitor.log

# Check for alerts
tail logs/alerts.log

# Check health check results
tail -30 logs/health_check.log
```

### Browser Testing
```bash
# Navigate to key pages
# Homepage: http://127.0.0.1:5173/
# Directory: http://127.0.0.1:5173/directory
# Volunteer: http://127.0.0.1:5173/volunteer
# Org detail: http://127.0.0.1:5173/org/264837170

# DevTools Network tab:
# 1. Reload page
# 2. Look for XHR requests
# 3. Check response time for /api/search calls
# 4. All should be <1s
```

---

## Test Status Tracker

Print this and check off as you go:

```
PRIORITY 1 (Critical Path)
  [ ] 1.1 Search is fast (3 tests)
  [ ] 1.2 Volunteer page loads (3 tests)
  [ ] 1.3 Health check passes (5 tests)
  Subtotal: [ ] 0/11 passing

PRIORITY 2 (Important)
  [ ] 2.1 Events full flow (4 tests)
  [ ] 2.2 Interest capture (4 tests)
  [ ] 2.3 Performance under load (3 tests)
  [ ] 2.4 FTS index sync (4 tests)
  [ ] 2.5 Monitoring infrastructure (4 tests)
  Subtotal: [ ] 0/19 passing

PRIORITY 3 (Regression)
  [ ] 3.1 2026-07-18 fixes (3 tests)
  [ ] 3.2 2026-06 fixes (3 tests)
  [ ] 3.3 2026-07-05 fixes (3 tests)
  Subtotal: [ ] 0/9 passing

PRIORITY 4 (Edge Cases)
  [ ] 4.1 Query edge cases (4 tests)
  [ ] 4.2 Pagination (4 tests)
  [ ] 4.3 Browser console (4 tests)
  Subtotal: [ ] 0/12 passing

TOTAL: [ ] 0/51 passing

OVERALL: [ ] READY FOR PRODUCTION / [ ] NEEDS FIXES
```

---

## Failure Triage

If a test fails, use this table to diagnose:

| Failing Test | Likely Cause | Diagnostic Command |
|--------------|--------------|-------------------|
| Search slow | API hanging or FTS out of sync | `python3 scripts/diagnose_search_perf.py` |
| Events won't load | Volunteer API broken | `curl http://127.0.0.1:5000/api/volunteer-events` |
| Health check fails | API not running | `ps aux \| grep gunicorn` |
| Modal won't submit | Interest endpoint broken | Check `daanaa_api.py` logs for errors |
| Concurrent searches timeout | Database locked | Check `PRAGMA busy_timeout` |
| Hyphen search broken | FTS wasn't rebuilt | `bash scripts/rebuild_fts_index_quick.sh` |
| Monitor won't start | Logs directory not writable | `ls -la logs/` |

---

## Test Execution Tips

1. **Parallelization:** Priority 2 and 4 tests can run while monitoring runs
2. **Log everything:** Save curl output, timing, errors
3. **Use timestamps:** Start log with date, end with date to measure total time
4. **Screenshot on fail:** If UI test fails, screenshot the state
5. **Clean between tests:** Stop API, restart, between major test sections

---

**Estimated total test time:** 45-60 minutes  
**Can be parallelized:** Yes (start monitoring while testing search)  
**Minimum to pass:** All Priority 1 + Priority 2 (P3 regression is nice-to-have)
