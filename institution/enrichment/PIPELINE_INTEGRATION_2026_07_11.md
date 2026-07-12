# Enrichment Pipeline Integration — 2026-07-11

**Authority:** Founder Ruling 2026-07-11 (Operational Decisions, Item 2: AI Memory Migration)  
**Status:** ACTIVE (integrated into overnight_pipeline.py within 8pm–8am automation window)  
**Effective:** 2026-07-12 (next automation cycle)  

---

## AUTOMATION WINDOW: 8pm–8am (20:00–08:00)

**Master orchestration:**
```
21:00 (9pm) —— gpu_night.sh start
              Launch GPU services (llama-server Qwen3-30B, embed server)
              
22:00-02:00 —— Autonomous background tasks
              reembed_watchdog.py (embedding maintenance, 30-min intervals)
              email_agent (email triage, 2-hour intervals)
              
02:00 (2am) —— enrichment_loop_8pm_8am.sh START
              Continuous enrichment batches (enrich_batch.py) until 8am
              All Priority 1-3 enrichment items run in loop
              
02:30 (2:30am) — overnight_pipeline.py START
              [NEW] run_enrichment_pipeline() integrated here
              Donation link extraction Phase 1 (200 orgs)
              Scoring, backups, quality gates
              
02:30 (2:30am) — daanaa_backup.sh START (coordinated)
              Critical tables dump + offsite push
              Runs concurrently, no DB locks
              
03:00 (3am) —— monitor_backups.sh START
              Backup health check + revocation sync
              
08:00 (8am) —— enrichment_loop_8pm_8am.sh STOP
              Cutoff: no new batches after 8am
              
09:00 (9am) —— gpu_night.sh stop
              Deactivate GPU, cool down (house thermal constraint)
```

---

## SCOPE: Priority 1-5 Enrichment

**What enriches during 8pm-8am window:**

| Priority | Component | Orchestrator | Status | Details |
|----------|-----------|---------------|--------|---------|
| P1 | Website Discovery | enrichment_loop | ✅ Autonomous | crawl + verify, mark 'beta' |
| P2 | Website Validation | enrichment_loop | ✅ Concurrent | HTTP verify, HTTPS→HTTP |
| P3 | Mission Generation | gpu_night.sh + enrichment_loop | ✅ GPU batch | 900+/night, Qwen3-30B |
| P4 | Donation Link Extract | overnight_pipeline (NEW) | ✅ at 02:30 | 200 orgs/run, conf≥90 |
| P5 | Contact/Actions | enrichment_loop | ⏳ Future | Phase 6-10 queued |

---

## OVERNIGHT_PIPELINE INTEGRATION (02:30)

**Where donation_link_pipeline fits:**
```
overnight_pipeline.py 02:30 START
  ...
  6.5–6.7: Concurrent fetch + enrichment (missions, tags)
  [NEW] 6.8: run_enrichment_pipeline()
       └─ run_donation_link_pipeline()
          Donation links Phase 1 (200 orgs)
  ...
  Scoring, quality gates, publish
  ~04:30 END
```

**Why 02:30, not earlier:** Allows enrichment_loop (starting 02:00) to populate cache + website data before donation extraction runs.

---

## BACKUP & MONITORING COORDINATION

**Parallel execution (no conflicts):**
- 02:30 — overnight_pipeline.py (scoring + enrichment)
- 02:30 — daanaa_backup.sh (DB dump, SQLite read-only)
- 03:00 — monitor_backups.sh (health check)

**Design:** SQLite allows read-only dumps concurrently with writes; backup uses strict shell flags (set -Eeuo pipefail, ERR trap).

**Robustness:** Backup script fixed (commit d86d422) to fail loudly; enrichment includes non-fatal error handling (logged, continues).

**Monitoring:** All logs go to `/logs/overnight.log` + `/logs/backup.log` + `/logs/generate_missions_32b.log`.

---

## CODE CHANGES

**File:** `/home/akbar/meritgiving/scripts/overnight_pipeline.py`

**Added functions:**
```python
def run_donation_link_pipeline():
    """Run donation link discovery Phase 1 — 200 orgs, 600s timeout, non-fatal errors."""

def run_enrichment_pipeline():
    """Coordinate Priority 1-5 enrichment (websites + missions + donations + contacts)."""
```

**Integrated into main():**
```python
# Step 6.8: Enrichment pipeline orchestration
run_enrichment_pipeline()  # Added after concurrent fetch+enrichment
```

**Logging:** All stages logged to `/home/akbar/meritgiving/logs/overnight.log` with timestamps.

---

## DATA QUALITY EXPECTATIONS

**Nightly output (starting 2026-07-12 02:30):**

| Component | Metrics |
|-----------|---------|
| Websites fetched | ~86K+ verified (live crawl) |
| Websites cached | page_cache populated for missions + donations |
| Missions generated | ~900–1000/night (Qwen3-30B) |
| Donation links extracted | 200–400 links (Phase 1, 200 orgs) |
| Donations published | ~50–100 (confidence ≥90 only) |
| Database status | registry_enriched updated with verify links + confidence scores |

---

## ERROR HANDLING

**Non-fatal errors** (pipeline continues):
- Mission generation batch errors (logged, counted, reported)
- Donation link extraction timeouts (org skipped, retry next night)
- Website verification failures (marked 'beta_unverified', retried)
- Fetch errors (logged, cache partially populated)

**Fatal errors** (pipeline stops):
- Database locked (indicates concurrent writes)
- Out of disk space
- Python subprocess crash (non-zero exit, logged)

---

## MONITORING & ALERTS

**Log locations:**
- Main: `/home/akbar/meritgiving/logs/overnight.log` (comprehensive)
- Backups: `/home/akbar/meritgiving/logs/backup.log` + `.backup_errors`
- Missions: `/home/akbar/meritgiving/logs/generate_missions_32b.log`
- Donations: `[stdout redirected to overnight.log]`

**Health check:**
```bash
# Check nightly stats (run after 04:30)
tail -20 /home/akbar/meritgiving/logs/overnight.log
grep "enrichment\|donation\|mission" /home/akbar/meritgiving/logs/overnight.log | tail -10
```

---

## GOVERNANCE & AUTHORITY

**Authority:** Founder Ruling 2026-07-11, Operational Decisions, Item 2.

**Enrichment principles (per Founder Ruling):**
1. All website-discovered data marked 'beta' (heuristic, not verified)
2. Donation links require confidence ≥90 (fail-closed)
3. AI-generated missions labeled as AI-assisted in API
4. Contact extraction must respect GDPR/privacy boundaries
5. All enrichment is opt-in (orgs can claim to move to 'verified')

---

## NEXT STEPS (Future Phases)

**Phase 6-10 enrichment** (queued for future integration):
- P6: GitHub repository discovery (supplemental source)
- P7: Advanced contact extraction (board members, staff)
- P8: Volunteer opportunity mining
- P9: Similar-org recommendations
- P10: Readiness assessment (capacity signals)

**Timeline:** Phases 6-10 queued after P1-5 stabilize (2 weeks of clean nightly runs).

---

**The enrichment pipeline is now part of the institutional rhythm. Every night, 86K+ organizations are enriched with websites, missions, and donation links — all marked transparently, all auditable, all reversible through the org claim flow.**

**Status: ACTIVE as of 2026-07-12 02:30 UTC.**
