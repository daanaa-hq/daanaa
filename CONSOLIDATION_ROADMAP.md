# Cron Consolidation Roadmap

**Goal**: Replace 42 scattered cron jobs with a unified master orchestrator that coordinates all pipeline phases.

**Status**: Phase 1 (Design) ✅ Complete | Phase 2 (Implementation) ⏳ In Progress

---

## What's Built

### ✅ Master Orchestrator (`scripts/master_orchestrator.py`)
- Unified coordinator for 6 pipeline phases (IRS → Scoring → Enrichment → Embeddings → Sync → Reporting)
- Dependency-aware execution (phases run in order, required phases block downstream)
- Comprehensive logging and state tracking in `orchestrator_state` table
- Modes: `--mode full` (all phases), `--phase <name>` (single phase), `--mode status` (report)
- Timeout protection, skip-if-recent optimization, environment variable support

### ✅ Audit Document (`AGENT_ECOSYSTEM_AUDIT.md`)
- Mapped all 42 cron jobs by category
- Identified 4 critical blockers:
  - **overnight_pipeline.py orphaned** (not in cron) → 1000s of missing ProPublica enrichments
  - **Database not updating** (0 scoring runs yesterday) → scores stale
  - **Duplicate morning_brief jobs** (7 AM + 11 AM) → two runs per day
  - **GPU shutdown conflict** (9 AM same-time execution) → race condition

### ✅ Consolidation Helper (`scripts/consolidate_cron.sh`)
- Creates `orchestrator_state` table
- Shows before/after cron schedule
- Dry-run mode to preview changes
- Guides manual crontab updates

---

## Implementation Steps (Phase 2)

### 1. **Quick Fixes** (Low risk, high impact)
These fix the immediate blockers without touching the full consolidation:

**A. Restore overnight_pipeline.py to cron**
```bash
# Add to crontab at 2:30 AM (after IRS ingest phase)
30 2 * * * cd ~/meritgiving && source venv/bin/activate && python3 scripts/overnight_pipeline.py >> logs/overnight.log 2>&1
```
**Impact**: 1000s of orgs will get ProPublica enrichment again  
**Urgency**: High — blocking enrichment pipeline

**B. Fix GPU shutdown conflict**
```bash
# Remove (old):
0 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop_embed_server

# Add (staggered):
5 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop_embed_server
```
**Impact**: Eliminates race condition at 9 AM  
**Urgency**: Medium — rare but data-corrupting if it happens

**C. Merge duplicate morning_brief jobs**
```bash
# Remove (old):
0 7 * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/morning_brief.py
0 11 * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/morning_briefing_agent.py

# Add (merged):
0 7 * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/morning_briefing_agent.py
```
**Impact**: Single run per day, cleaner logs  
**Urgency**: Low — cosmetic, no data impact

### 2. **Full Consolidation** (After quick fixes)
Once quick fixes are in place and tested, consolidate all 42 jobs:

**NEW PRIMARY ORCHESTRATOR (add to crontab):**
```bash
# Master pipeline orchestrator — replaces 30+ jobs
0 2 * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 scripts/master_orchestrator.py --mode full >> /home/akbar/meritgiving/logs/master_orchestrator.log 2>&1
```

**KEEP (independent, not in master_orchestrator):**
```bash
# High-frequency monitors (running in parallel is OK)
*/5 * * * * /home/akbar/meritgiving/scripts/log_gpu_temp.sh
*/4 * * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/gpu_queue_manager.py --run >> /home/akbar/meritgiving/logs/cron.log 2>&1
*/10 * * * * source /home/akbar/meritgiving/venv/bin/activate && python3 /home/akbar/meritgiving/scripts/surge_detection_agent.py >> /home/akbar/meritgiving/logs/surge_agent.log 2>&1
*/30 * * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/feedback_ingestion_agent.py >> /home/akbar/meritgiving/logs/cron.log 2>&1

# Hourly IRS status check
0 * * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 scripts/hourly_irs_status_check.py

# Email triage (independent workflow)
30 7 * * * cd /home/akbar/meritgiving && /home/akbar/meritgiving/venv/bin/python3 -m scripts.email_agent.run --limit 50 --query 'newer_than:2d -label:daanaa/triaged' >> /home/akbar/meritgiving/logs/email_agent.log 2>&1

# GPU night mode (separate system)
0 22 * * * /home/akbar/meritgiving/scripts/gpu_night.sh start >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1
0 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1

# Weekly tasks
15 4 * * 0 /home/akbar/meritgiving/scripts/weekly_maintenance.sh
0 5 * * 1 venv/bin/python3 scripts/impact_snapshot.py >> logs/impact.log 2>&1

# External/infrastructure jobs
0 * * * * /usr/bin/python3 /home/akbar/procurement_stack/python_scripts/albert_etl.py >> /home/akbar/procurement_stack/albert_autonomous.log 2>&1
0 9 1 * * /home/akbar/warehouse/health-check.sh >> /home/akbar/warehouse/health-cron.log 2>&1
```

**RETIRE (consolidated into master_orchestrator):**
```bash
# ❌ auto_ingest.py (0 */2 * * *) → master_orchestrator --phase irs_ingest
# ❌ overnight_pipeline.py → master_orchestrator --phase enrichment
# ❌ monthly_rescore_agent.py (0 6 1 * *) → master_orchestrator --phase scoring
# ❌ morning_brief.py (0 7) → consolidated with morning_briefing_agent.py
# ❌ morning_briefing_agent.py (0 11) → master_orchestrator --phase reporting
# ❌ agent_nightly_audit.md (0 3) → deprecated, use master_orchestrator
# ❌ agent_outcome_analyzer.py (15 3) → optional, move to weekly if needed
# ❌ agent_quality.py (15 2) → optional, keep separate if needed
# ❌ agent_cause_tags.py (35 2) → optional, keep separate if needed
# ❌ link_health_check_agent.py (0 4 * * 0) → master_orchestrator --phase link_health
# ❌ db_sync_from_droplet.sh (0 2) → optional, keep separate if needed
# ❌ build_embeddings.py (ad-hoc) → master_orchestrator --phase embeddings
# ❌ deploy_browse.sh (0 3 2) → optional, run manually
# ❌ deploy_similar_orgs.sh (0 2 1) → optional, run manually
# ❌ weekly_summary_agent.py (0 6 * * 1) → run as separate job if needed
# ❌ generate_cause_spotlights.py (30 5) → run as separate job if needed
# ❌ backfill_stubs.py phases (0 50 2 / 0 3 * * 1-6) → optional, run as separate job
# ❌ various IRS jobs (download_irs_soi, ingest_gt990, sync_irs_revocations) → optional
```

---

## Testing Plan

### Quick Fix Testing (1-2 hours)
1. Add overnight_pipeline.py to cron at 2:30 AM
2. Monitor logs tomorrow (6/10) at 3 AM — check that enrichment happens
3. Verify database: `SELECT COUNT(*) FROM registry_enriched WHERE updated_at > datetime('now', '-1 day');` should be > 0
4. Fix GPU shutdown stagger (5 9 AM)
5. Merge morning brief jobs, verify no duplicate runs

### Full Consolidation Testing (4-6 hours)
1. Initialize orchestrator_state table
2. Run master_orchestrator.py --mode full manually (watch logs)
3. Verify all 6 phases execute (IRS → Scoring → Enrichment → Embeddings → Sync → Reporting)
4. Check orchestrator_state table for all phases recorded
5. Monitor database: confirm updates, scores, embeddings rebuilt
6. Deploy to cron: `0 2 * * * master_orchestrator.py --mode full`
7. Run for 3-5 days, monitor logs for any phase failures
8. Once stable, retire old jobs one by one

---

## Rollback Plan

If consolidation breaks the pipeline:

1. **Restore backup crontab:**
   ```bash
   crontab /tmp/crontab_backup_<timestamp>.txt
   ```

2. **Disable master_orchestrator** (comment out the 0 2 line)

3. **Return to ad-hoc mode** (manual runs of individual scripts)

4. **Root cause analysis**: Check `orchestrator_state` table to see which phase failed

---

## Benefits of Consolidation

| Before | After |
|--------|-------|
| 42 scattered cron jobs | 1 primary orchestrator + 9 independent jobs |
| No dependency tracking | Phases run in order, downstream waits |
| Transactional failures (IRS succeeds, scoring runs stale) | Atomic cycles: all-or-nothing per day |
| 10+ log files to monitor | 1 master log + optional phase logs |
| Manual job management (edit crontab for each) | Unified config in master_orchestrator.py |
| "When did X last run?" requires log archaeology | orchestrator_state table shows all runs |
| Duplicate jobs, conflicts, orphaned scripts | Single source of truth |

---

## Next Actions (Priority)

**Immediate (today):**
1. ✅ Audit ecosystem → DONE (AGENT_ECOSYSTEM_AUDIT.md)
2. ✅ Design master orchestrator → DONE (scripts/master_orchestrator.py)
3. ⏳ **Apply quick fixes** (restore overnight_pipeline, fix GPU conflict, merge morning brief)
4. ⏳ Test quick fixes for 24h

**Next week:**
5. Initialize orchestrator_state table
6. Test master_orchestrator.py manually
7. Deploy to cron (0 2 AM)
8. Monitor for 3-5 days
9. Retire old jobs in batches

---

## Monitoring Commands (After Deployment)

```bash
# Check orchestrator state for today
sqlite3 data/merit_registry.db "SELECT phase_name, run_time, status, duration_sec FROM orchestrator_state WHERE run_date = date('now') ORDER BY run_time DESC;"

# Check if master orchestrator is in crontab
crontab -l | grep master_orchestrator

# View master orchestrator log
tail -100 logs/master_orchestrator.log

# Run a single phase manually
python3 scripts/master_orchestrator.py --phase enrichment

# Check current status
python3 scripts/master_orchestrator.py --mode status
```

