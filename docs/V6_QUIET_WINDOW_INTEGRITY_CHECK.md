# V6 SQLite Integrity Check — Quiet Window Procedure

**Purpose:** Complete full `PRAGMA integrity_check` without database lock interruptions  
**Duration:** 20–30 minutes (total, including pre/post verification)  
**Requirements:** No competing database access (API, frontend, scripts all stopped)  
**Date Created:** 2026-07-27

---

## Background

The V6 candidate run requires verification of complete database integrity. A prior attempt to run `PRAGMA integrity_check` was interrupted by active database locks, preventing completion of the full scan.

This procedure ensures a clean, uninterrupted integrity check during a documented quiet maintenance window.

---

## Pre-Check (5 minutes)

Verify that it's safe to stop services:

```bash
# 1. Confirm no other processes hold database locks
lsof data/merit_registry.db 2>/dev/null || echo "No open file handles"

# 2. Check for running API processes
pgrep -f "python3 daanaa_api.py" || echo "API not running"

# 3. Confirm no frontend dev servers
pgrep -f "npm run dev" || echo "Frontend not running"

# 4. Check for active background jobs
jobs || echo "No background jobs"
```

**All checks should return NOT FOUND or empty. If any process is found, verify it's safe to stop, then proceed to Stop Services.**

---

## Stop Services (5 minutes)

Gracefully stop all database-accessing services:

```bash
# 1. Stop the Flask API (if running)
pkill -f "python3 daanaa_api.py"

# 2. Stop Gunicorn (if running in production mode)
pkill -f gunicorn || echo "Gunicorn not running"

# 3. Stop frontend dev server (if running)
pkill -f "npm run dev" || echo "Frontend dev not running"

# 4. Wait for locks to clear (important: don't rush this)
sleep 10

# 5. Verify services stopped
pgrep -f "python3 daanaa_api.py" && echo "WARNING: API still running" || echo "API confirmed stopped"
pgrep -f gunicorn && echo "WARNING: Gunicorn still running" || echo "Gunicorn confirmed stopped"
```

---

## Run Integrity Check (10–15 minutes)

Execute the full integrity check:

```bash
# Run PRAGMA integrity_check
echo "Starting integrity check at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
INTEGRITY_RESULT=$(sqlite3 data/merit_registry.db "PRAGMA integrity_check;")
echo "Integrity check completed at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""
echo "Result:"
echo "$INTEGRITY_RESULT"
```

**Expected output:** A single line containing exactly:
```
ok
```

**If result is NOT `ok`:**
- The output will list specific corruption errors (e.g., `wrong # of entries in index X`)
- DO NOT proceed with staging or production
- Document the exact error and escalate to founder
- May require database restore from backup

**Save the exact result for the record:**
```bash
# Capture to file for documentation
sqlite3 data/merit_registry.db "PRAGMA integrity_check;" > /tmp/v6_integrity_check_$(date -u +%Y%m%dT%H%M%SZ).txt
cat /tmp/v6_integrity_check_*.txt
```

---

## Verify Database Access (2 minutes)

Confirm database is accessible and has expected data:

```bash
# 1. Count registry records
REGISTRY_COUNT=$(sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched;")
echo "Registry enriched records: $REGISTRY_COUNT"
# Expected: ~1,900,000

# 2. Count v6 assignments in candidate run
V6_COUNT=$(sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM v6_peer_context_assignments WHERE run_id='v6_foundation_candidate_20260728_revised';")
echo "V6 candidate assignments: $V6_COUNT"
# Expected: 1,758,083

# 3. Check candidate status
V6_STATUS=$(sqlite3 data/merit_registry.db "SELECT status FROM v6_scoring_runs WHERE run_id='v6_foundation_candidate_20260728_revised';")
echo "V6 candidate status: $V6_STATUS"
# Expected: 'candidate'
```

**All counts should match expectations. If any differ significantly, note the discrepancy.**

---

## Restart Services (5 minutes)

Restore normal operation:

```bash
# 1. Restart API
source ~/meritgiving/venv/bin/activate
./restart_api.sh

# 2. Verify API started
sleep 3
curl -s http://localhost:5000/health || echo "API not responding yet"

# 3. Verify health endpoint returns 200
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
echo "Health check HTTP code: $HTTP_CODE"
# Expected: 200

# 4. Restart frontend (if needed)
cd frontend
npm run dev &
cd ..
echo "Frontend started in background"
```

**Confirm services are running:**
```bash
# Check API responds
curl -s http://localhost:5000/api/stats | python3 -c "import json, sys; print(json.load(sys.stdin).get('total_organizations', 'N/A'))"

# Check frontend loads (if dev server)
curl -s http://localhost:5173/ | head -1
```

---

## Documentation & Sign-Off

Record the integrity check result:

```bash
# Create documentation record
cat > /tmp/v6_integrity_check_record.txt << 'EOF'
Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Candidate Run: v6_foundation_candidate_20260728_revised
Database: data/merit_registry.db

Integrity Check Result:
$(sqlite3 data/merit_registry.db "PRAGMA integrity_check;")

Post-Check Verification:
- Registry records: $(sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched;")
- V6 assignments: $(sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM v6_peer_context_assignments WHERE run_id='v6_foundation_candidate_20260728_revised';")
- Candidate status: $(sqlite3 data/merit_registry.db "SELECT status FROM v6_scoring_runs WHERE run_id='v6_foundation_candidate_20260728_revised';")

Services Verified:
- API health: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
- Database accessible: YES

Performed by: [Your name/agent]
Approved by: [Founder]
EOF

# Display record
cat /tmp/v6_integrity_check_record.txt
```

---

## Blocking Conditions (MUST PASS before staging)

All three must be true:

| Condition | Status | Evidence |
|-----------|--------|----------|
| Integrity check = `ok` | ⏳ | `PRAGMA integrity_check` result |
| Registry count matches expected (~1.9M) | ⏳ | SELECT COUNT(*) query |
| Candidate status still = `candidate` | ✅ | SELECT status from v6_scoring_runs |

**Status:** All three must pass before proceeding to staging QA.

---

## If Integrity Check Fails

**Do NOT proceed with staging.**

**Steps:**
1. Document the exact error message
2. Note the date/time of check
3. Check for backup files: `ls -lh data/backups/v6/`
4. Contact founder with:
   - Exact error from `PRAGMA integrity_check`
   - Backup timestamp available
   - Recommendation: restore from backup or investigate error
5. Halt staging and production work until resolved

---

## Timeline

**Recommended quiet window:** 01:00–02:00 UTC (outside peak hours)

**Total duration:** 20–30 minutes from start to services-restored

**Expected order:**
- 01:00: Pre-check
- 01:05: Stop services
- 01:15: Run integrity check (10–15 min scan)
- 01:30: Verify database access
- 01:35: Restart services
- 01:45: Document + record result

---

## Next Steps After Integrity Check Passes

1. **Run corrected fairness comparison:**
   ```bash
   python3 scripts/v6_fairness_comparison_corrected.py \
     v6_foundation_candidate_20260728_revised \
     v6_foundation_candidate_20260727_corrected \
     data/merit_registry.db
   ```

2. **Review fairness report:**
   - Check revocation analysis
   - Verify small-org transitions
   - Confirm no premature approval recommendation

3. **Upon fairness report confirmation, proceed to staging QA**

---

## Checklist

- [ ] Pre-check completed — no database locks
- [ ] All services stopped gracefully
- [ ] Waited 10 seconds for lock release
- [ ] Integrity check run and result captured
- [ ] Result is exactly `ok` (if not, escalate)
- [ ] Post-check verification passed
- [ ] Services restarted and verified
- [ ] Record documented
- [ ] Founder notified of integrity check result
- [ ] Ready to proceed to staging QA

---

**Document Version:** 2026-07-27  
**Status:** Ready for execution during next quiet maintenance window
