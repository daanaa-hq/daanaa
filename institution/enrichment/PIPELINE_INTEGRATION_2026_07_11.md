# Enrichment Pipeline Integration — 2026-07-11

**Authority:** Founder Ruling 2026-07-11 (Operational Decisions, Item 2: AI Memory Migration)  
**Status:** ACTIVE (integrated into overnight_pipeline.py)  
**Effective:** 2026-07-12 (next nightly run at 02:30)  

---

## SCOPE: Priority 1-5 Enrichment

**What enriches every night (starting 02:30):**

| Priority | Component | Stage | Status | Details |
|----------|-----------|-------|--------|---------|
| P1 | Website Discovery | Fetch | ✅ Running autonomously | crawl + verify, mark 'beta' |
| P2 | Website Validation | Verify | ✅ Concurrent with scoring | HTTP HEAD/GET, HTTPS→HTTP |
| P3 | Mission Generation | GPU batch | ✅ Running (Qwen3-30B) | 900+ missions/night, 12K line log |
| P4 | Donation Link Extract | NEW INTEGRATION | 🔄 Phase 1 nightly | 200 orgs/run, confidence ≥90 |
| P5 | Contact/Actions | Queued | ⏳ Future (Phase 6-10) | Post-P4 completion |

---

## ORCHESTRATION: Nightly Pipeline (02:30 UTC)

**Execution sequence:**
```
02:30 START overnight_pipeline.py

  1. BMF sync (IRS classification)
  2. Revocation check
  3. Manual submissions
  4. ProPublica enrichment
  5. Nonprofit updates
  6. v5.0 scoring (SLOW)
  7. Cohort context rebuild
  
  8. [PARALLEL START]
     - Fetch websites (concurrent)
     - Parallel enrichment (missions + tags)
     - → both complete ~45 min
  
  9. [NEW] Enrichment pipeline orchestration (Step 6.8)
     - run_enrichment_pipeline()
     - Donation link extraction Phase 1
     - Coordinated logging
  
  10. Volunteer event expiry
  11. Data quality gate
  12. Export research snapshot
  13. Cleanup stale scores
  14. Purge stale wallets
  15. Publish + deploy to droplet
  
  ~04:30 END (approx 2 hours total)
```

---

## BACKUP COORDINATION

**Timing:**
- 02:30 — overnight_pipeline.py starts (scoring + enrichment)
- 02:30 — daanaa_backup.sh starts (critical tables dump)
- 03:00 — monitor_backups.sh starts (health check + revocation sync)

**Design:** Both pipelines run independently; backups do NOT lock the database (SQLite read-only mode for exports).

**Robustness:** Backup script fixed (commit d86d422) to fail loudly on any error; enrichment pipeline includes error handling for donations/missions.

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
