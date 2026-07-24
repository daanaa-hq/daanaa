# QA Checklist — Search Performance Fix & Monitoring Infrastructure
**Date:** 2026-07-24  
**Test Scope:** FTS index rebuild, health checks, monitoring, search + events pages

---

## Section 1: Search Functionality (Core Fix Verification)

### 1.1 Basic Search Queries
- [ ] **Single word search** — `curl http://127.0.0.1:5000/api/search?q=health`
  - Expected: 20 results in <500ms
  - Check: HTTP 200, `total` field present, results array non-empty
  - Log response time and first 3 org names

- [ ] **Multi-word search** — `curl http://127.0.0.1:5000/api/search?q=food+bank`
  - Expected: Results in <500ms
  - Check: Results are food bank related, not random matches
  - Verify: Exact phrases work (FTS should handle multi-word)

- [ ] **Non-existent search** — `curl http://127.0.0.1:5000/api/search?q=xyz123notreal`
  - Expected: HTTP 200, `total: 0`, empty results array
  - Check: No crash, graceful empty result
  - Verify: Query still completes in <100ms

- [ ] **Hyphenated org search** — `curl http://127.0.0.1:5000/api/search?q=4-H`
  - Expected: Results for "4-H" organizations
  - Check: No SQL errors, returns 4-H foundations
  - Log: Confirm this worked (was failing in 2026-07-18)

- [ ] **Zip code search** — `curl http://127.0.0.1:5000/api/search?q=97701`
  - Expected: Organizations in/near that zip code
  - Check: Results show city name substitution in response
  - Verify: "zip_resolved" banner data present

- [ ] **Mixed query** — `curl http://127.0.0.1:5000/api/search?q=food+bank+97701`
  - Expected: Food banks near that zip code
  - Check: Results are both food-related AND near zip
  - Verify: All results have state/city fields populated

### 1.2 Search Performance Benchmarks
- [ ] **Latency p50 (median)** — Run 10 searches with different queries
  - Expected: All <400ms
  - Log: Average response time
  - Alert if any >1s

- [ ] **Latency p95 (tail)** — Run 20 diverse searches
  - Expected: p95 <800ms
  - Log: slowest query and its time
  - Alert if any >2s

- [ ] **Concurrent search** — Run 5 simultaneous searches
  - Expected: All complete within 1s, no 503/504 errors
  - Check: No timeout cascades
  - Tool: `for i in {1..5}; do curl -s http://127.0.0.1:5000/api/search?q=health & done; wait`

- [ ] **Empty query handling** — `curl http://127.0.0.1:5000/api/search?q=`
  - Expected: HTTP 400 with "q param required" error
  - Check: No crash, no timeout
  - Verify: Error message is clear

### 1.3 Search Result Quality
- [ ] **Result relevance** — Search "food bank", verify top 5 results are actually food banks
  - Check: `cause_tags` include "food" or "bank"
  - Check: mission field mentions food/hunger
  - Log: First 3 org names and their missions

- [ ] **Result sorting** — Search "health"
  - Expected: Results sorted by relevance (BM25 score)
  - Check: Most relevant results first
  - Verify: Name-order fallback for ties works

- [ ] **Pagination** — `curl http://127.0.0.1:5000/api/search?q=health&per_page=50&page=2`
  - Expected: Results 51-100
  - Check: Total count accurate
  - Verify: No duplicate results across pages

---

## Section 2: Events/Volunteer Page Performance

### 2.1 Volunteer Page Load
- [ ] **Page loads on first visit** — Navigate to `https://daanaa.org/volunteer` (or localhost equivalent)
  - Expected: Page renders in <3s
  - Check: "10 nationwide events" display without user clicking search
  - Verify: Events load and render correctly

- [ ] **Page responsiveness** — Check page load time with browser DevTools
  - Expected: Largest contentful paint <2s
  - Check: No layout shift while events load
  - Verify: Search box is interactive immediately

- [ ] **Mobile view** — Test `/volunteer` on mobile device or mobile viewport
  - Expected: <3s load, events stack vertically
  - Check: Touch targets (buttons) are ≥44px
  - Verify: Scroll is smooth, no janky reflows

### 2.2 Event Display & Filtering
- [ ] **Initial event load** — Page loads with 10 events shown (auto-load)
  - Expected: 10 events visible without user interaction
  - Check: Event title, date, location visible for each
  - Log: First 3 event titles

- [ ] **Search by keyword** — Type "food" in search box
  - Expected: Events filtered to show food-related only, <1s
  - Check: No timeout
  - Verify: Result count updates

- [ ] **Search by location** — Type "New York" 
  - Expected: Events in NY show, <1s
  - Check: City/state matches
  - Verify: Out-of-state events disappear

- [ ] **Search by date** — Filter for events "This Week"
  - Expected: Only events within 7 days show
  - Check: Date logic correct (today's date boundaries)
  - Verify: Count decreases appropriately

- [ ] **No results state** — Search "xyz123notreal"
  - Expected: "No events found" message (not blank page)
  - Check: Message is visible and helpful
  - Verify: Search box still editable

### 2.3 Event Detail & Interest Capture
- [ ] **Event detail page loads** — Click on an event
  - Expected: Event detail renders in <1s
  - Check: Full event description, time, location visible
  - Verify: Org name and "Interested in volunteering?" button present

- [ ] **Interest modal opens** — Click "Interested in volunteering?" button
  - Expected: Modal pops up with email form
  - Check: Email input field is focused
  - Verify: Modal is keyboard-accessible (can Tab through)

- [ ] **Email validation** — Try submitting without email
  - Expected: Submit button disabled or error message
  - Check: "Please enter a valid email" error
  - Verify: No API call made

- [ ] **Valid submission** — Enter valid email, click submit
  - Expected: Modal closes, success message appears
  - Check: HTTP 200 response
  - Verify: Email address captured (check backend logs)

- [ ] **Error handling** — Simulate API error (block network tab in DevTools)
  - Expected: Error message in modal, not a crash
  - Check: "Something went wrong" message
  - Verify: Can close modal and retry

---

## Section 3: Health Check Infrastructure

### 3.1 Manual Health Check Script
- [ ] **Script runs without errors** — `bash scripts/health_check.sh`
  - Expected: Script completes, no crashes
  - Check: Exit code 0 or clear error message
  - Log: Full output to console

- [ ] **Homepage check** — Output shows `Homepage: 200`
  - Expected: Homepage is reachable and responds quickly
  - Check: Response time <3s
  - Verify: Status code is 200

- [ ] **Directory check** — Output shows `Directory: 200`
  - Expected: Directory page accessible
  - Check: Response time <3s
  - Verify: Status code is 200

- [ ] **Volunteer page check** — Output shows `Volunteer: 200`
  - Expected: Volunteer page accessible
  - Check: Response time <3s
  - Verify: Status code is 200

- [ ] **API health check** — Output shows `Health endpoint: 200`
  - Expected: API health endpoint returns 200
  - Check: Local API at 127.0.0.1:5000 is reachable
  - Verify: No timeouts

- [ ] **Performance thresholds** — Output shows performance results
  - Expected: All endpoints <3000ms
  - Check: No slow endpoints flagged
  - Log: Response times for each endpoint

- [ ] **Log file created** — Check `logs/health_check.log` exists
  - Expected: Log file populated with timestamps
  - Check: Timestamps are from recent run
  - Verify: All checks logged

### 3.2 Continuous Monitoring Script
- [ ] **Monitor starts** — `bash scripts/monitor_site_health.sh &`
  - Expected: Script runs in background
  - Check: Logs appear in `logs/monitor.log`
  - Log: First 5 lines of logs

- [ ] **Monitoring interval** — Let monitor run for 15 minutes
  - Expected: Multiple check cycles (3-4 checks per 5 min interval)
  - Check: Log shows timestamps ~5 minutes apart
  - Verify: No duplicate checks within 1 minute

- [ ] **Alert on failure** — Simulate failure by stopping API: `pkill -f "gunicorn"`
  - Expected: Alert written to `logs/alerts.log` within 5 minutes
  - Check: Alert message is clear ("API unhealthy")
  - Verify: Monitor attempts recovery (restart command)

- [ ] **Recovery after restart** — Restart API: `python3 daanaa_api.py &`
  - Expected: Next health check passes
  - Check: `logs/monitor.log` shows "✓ Site healthy" again
  - Verify: Alert clears (recovery logged)

- [ ] **Graceful stop** — `pkill -f "monitor_site_health.sh"`
  - Expected: Monitor exits cleanly
  - Check: No zombie processes
  - Verify: Log files are properly closed

### 3.3 Diagnostics Script
- [ ] **Diagnostics complete** — `python3 scripts/diagnose_search_perf.py`
  - Expected: Script runs to completion, exits with status 0 or 1
  - Check: All 4 diagnostic sections run
  - Log: Full output

- [ ] **Database diagnostics** — Output shows database health
  - Expected: "✓ org_fts FTS table exists"
  - Check: "✓ Total organizations: 2,056,834"
  - Verify: "✓ FTS index entries: 2,056,834" (in sync)
  - Alert if counts don't match (drift detected)

- [ ] **FTS query performance** — Output shows FTS tests
  - Expected: "health" query <10ms
  - Check: "food bank" query <10ms
  - Verify: "xyz123notreal" query <5ms

- [ ] **Full search simulation** — Output shows end-to-end test
  - Expected: "✓ Search performance OK: XXXms"
  - Check: Duration <500ms
  - Alert if >1000ms (slow search path)

- [ ] **API endpoint test** — Output shows live API test
  - Expected: "GET /api/search?q=health: 200 in XXXms"
  - Check: Status code 200
  - Verify: Response time <500ms

---

## Section 4: FTS Index Health

### 4.1 Index Sync Verification
- [ ] **FTS and registry counts match**
  ```bash
  sqlite3 /home/akbar/meritgiving/data/merit_registry.db \
    "SELECT (SELECT COUNT(*) FROM registry_enriched) as registry, \
            (SELECT COUNT(*) FROM org_fts) as fts"
  ```
  - Expected: Both counts are 2,056,834
  - Alert if difference >1%
  - Log: Both counts

- [ ] **FTS triggers exist** — Check database schema
  ```bash
  sqlite3 /home/akbar/meritgiving/data/merit_registry.db \
    "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='registry_enriched'"
  ```
  - Expected: 3 triggers: org_ai, org_ad, org_au
  - Verify: All present

- [ ] **FTS table integrity** — Run quick integrity check
  ```bash
  sqlite3 /home/akbar/meritgiving/data/merit_registry.db \
    "SELECT COUNT(*) FROM org_fts WHERE organization_name IS NULL OR ein IS NULL"
  ```
  - Expected: 0 (no nulls in indexed columns)
  - Alert if >0

### 4.2 Index Coverage by NTEE
- [ ] **Health (E) coverage** — Count health org results
  ```bash
  curl "http://127.0.0.1:5000/api/organizations?ntee=E&per_page=1" | jq '.total'
  ```
  - Expected: >100,000 (large category)
  - Log: Exact count

- [ ] **Small category coverage** — Count a small category
  ```bash
  curl "http://127.0.0.1:5000/api/organizations?ntee=Y&per_page=1" | jq '.total'
  ```
  - Expected: >1,000 (even small cats indexed)
  - Log: Exact count

- [ ] **Search results match browse counts** — Compare API results
  - Search: `curl http://127.0.0.1:5000/api/search?q=health&per_page=1` → check `total`
  - Browse: `curl http://127.0.0.1:5000/api/organizations?ntee=E&per_page=1` → check `total`
  - Verify: Search results ≤ Browse results (search is subset)

---

## Section 5: Integration Testing

### 5.1 Post-Deployment Flow
- [ ] **Deploy triggers health check** — Simulate deployment
  1. Note current time
  2. Run: `bash scripts/safe_deploy_droplet.sh --code-only` (or `--frontend-only` if no backend changes)
  3. Expected: Deployment completes, health check runs at end
  4. Check: `logs/safe_deploy.log` shows "POST-DEPLOYMENT HEALTH CHECK" section
  5. Verify: All health checks passed

- [ ] **Rollback on health check failure** — (Skip in prod; test in dev only)
  1. Simulate deploy that breaks homepage: rename `index.html` before build
  2. Run deploy
  3. Expected: Health check fails, deploy rolls back
  4. Check: Homepage still works after rollback
  5. Restore file, clean up

### 5.2 Full User Journey (Donor)
- [ ] **Find + Save + Volunteer Flow**
  1. Navigate to `/directory`
  2. Search for "food bank" → <1s results
  3. Click first result → org detail loads <1s
  4. Add to wallet (if wallet feature available)
  5. Click "Interested in volunteering?" → modal → enter email → submit
  6. Expected: All steps <1s each, success message
  7. Check: No errors in browser console

### 5.3 Error Cases
- [ ] **API timeout handling** — Manually introduce a delay
  1. In `daanaa_api.py`, add `import time; time.sleep(2)` to search endpoint (temporarily)
  2. Run: `curl http://127.0.0.1:5000/api/search?q=health`
  3. Expected: Request completes in ~2s (not stuck)
  4. Remove delay before committing

- [ ] **Database locked** — Simulate heavy load
  1. Run 10 concurrent searches: `for i in {1..10}; do curl -s http://127.0.0.1:5000/api/search?q=health & done; wait`
  2. Expected: All complete, no 503 errors
  3. Check: Response times are still <1s
  4. Verify: No "database is locked" errors in logs

- [ ] **Missing FTS data** — Check graceful degradation (should not occur post-fix)
  1. Temporarily drop one org from FTS: `sqlite3 data/merit_registry.db "DELETE FROM org_fts LIMIT 1"`
  2. Run: `python3 scripts/diagnose_search_perf.py`
  3. Expected: Diagnostics flag the mismatch ("FTS out of sync")
  4. Restore: `bash scripts/rebuild_fts_index_quick.sh`

---

## Section 6: Regression Testing (Confirm Prior Bugs Don't Return)

### 6.1 Known Previous Issues (2026-07-18 fixes)
- [ ] **Hyphen handling** — `curl http://127.0.0.1:5000/api/search?q=4-H`
  - Expected: NO SQL errors, returns 4-H orgs
  - Alert if error appears in logs

- [ ] **AND/OR/NOT literal** — `curl http://127.0.0.1:5000/api/search?q=AND+OR+NOT`
  - Expected: Results for those literal terms, not boolean operators
  - Check: No SQL errors
  - Verify: Results are actual org names/missions

- [ ] **Apostrophe handling** — `curl http://127.0.0.1:5000/api/search?q=L%27Anse`
  - Expected: Results for "L'Anse" area orgs
  - Check: No SQL errors
  - Verify: Results mention L'Anse or similar

### 6.2 Known Previous Issues (2026-06 fixes)
- [ ] **Revoked orgs excluded** — `curl http://127.0.0.1:5000/api/organizations?per_page=100`
  - Expected: No revoked orgs in results
  - Check: All orgs have `irs_revoked=false` or NULL
  - Verify: `org_status` is "active" for all

- [ ] **Zero-result fallback** — Search something obscure
  - Expected: If FTS returns 0, API logs to `analytics_zero_result_queries`
  - Check: Log entry appears after search
  - Verify: User sees "no results" message (not error)

---

## Section 7: Performance Benchmarking

### 7.1 Baseline Measurements
- [ ] **Record search latencies** — Run 50 searches, record times
  ```bash
  for q in health food bank volunteer donate nonprofit; do
    time curl -s "http://127.0.0.1:5000/api/search?q=$q" | jq '.total'
  done
  ```
  - Expected: All <500ms
  - Log: Average, min, max times
  - Store for regression comparison

- [ ] **Record page load times** — Use browser DevTools Network tab
  - Homepage: Expected <1s
  - Directory: Expected <2s
  - Volunteer: Expected <2s
  - Log: LCP (Largest Contentful Paint) for each

- [ ] **Database query times** — Check slow query log
  ```bash
  grep "SELECT" logs/gunicorn_access.log | tail -20 | awk '{print $NF}' | sort -n
  ```
  - Expected: 90% of queries <200ms
  - Alert if any >1000ms
  - Log: Top 5 slowest queries

### 7.2 Concurrent Load Test
- [ ] **10 concurrent searches** — Run and measure response times
  ```bash
  ab -n 100 -c 10 "http://127.0.0.1:5000/api/search?q=health"
  ```
  - Expected: All requests complete
  - Check: 0 failed requests
  - Log: Requests/sec, mean latency
  - Alert if mean >500ms under load

- [ ] **Sustained monitoring** — Let monitor run for 1 hour
  - Expected: No alerts, all checks pass
  - Check: Log file shows consistent check pattern
  - Verify: No memory leaks (monitor process size stable)

---

## Section 8: Cleanup & Final Verification

### 8.1 Test Artifacts
- [ ] **Temporary files removed**
  - Remove any test data added during testing
  - Clean up any modified code (revert time.sleep() tests, etc.)
  - Verify: `git status` is clean

- [ ] **Logs are readable**
  - Check `logs/health_check.log` — all checks visible
  - Check `logs/monitor.log` — at least 3 cycles logged
  - Check `logs/fts_rebuild.log` — rebuild success logged
  - Verify: No truncated or corrupted log lines

### 8.2 Final Sign-Off
- [ ] **All tests passed** — Review entire checklist
  - Count total tests: _____ passed, _____ failed
  - List any failures and root causes

- [ ] **No new issues introduced** — Check for new errors
  - Browser console: No errors
  - Server logs: No new ERROR/WARN lines
  - Verify: No 4xx/5xx responses in access log

- [ ] **Documentation updated** — Check if any docs need updating
  - If monitoring behavior differs from docs, note it
  - If new edge cases found, file a follow-up issue
  - Verify: DECISIONS.md entry makes sense post-testing

- [ ] **Ready for production** — Sign off
  - QA name: _____________________
  - Date: _____________________
  - Result: ✅ PASSED / ❌ FAILED
  - Notes: ___________________________________________________________

---

## Appendix: Quick Command Reference

**Local Testing:**
```bash
# Test search
curl "http://127.0.0.1:5000/api/search?q=health&per_page=5"

# Test health check
bash scripts/health_check.sh

# Run diagnostics
python3 scripts/diagnose_search_perf.py

# Check FTS sync
sqlite3 data/merit_registry.db \
  "SELECT 'registry' as t, COUNT(*) as c FROM registry_enriched 
   UNION ALL 
   SELECT 'fts' as t, COUNT(*) as c FROM org_fts"

# Monitor in background
bash scripts/monitor_site_health.sh &

# Stop monitoring
pkill -f "monitor_site_health.sh"

# Check latest health logs
tail -30 logs/health_check.log
tail -30 logs/monitor.log
```

**Browser Testing:**
- Homepage: `https://daanaa.org/` (or `http://localhost:5173/`)
- Directory: `https://daanaa.org/directory`
- Volunteer: `https://daanaa.org/volunteer`
- Org detail: `https://daanaa.org/org/264837170` (example EIN)

**DevTools Tips:**
- Network tab: Sort by Time to find slow requests
- Performance tab: Record page load, check LCP metric
- Console: Search for "error" or "warn" after each page load
