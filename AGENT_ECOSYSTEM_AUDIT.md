# Agent Ecosystem Audit (2026-06-09)

## Executive Summary
- **Total cron jobs**: 42 (with duplicates)
- **Active log files** (last 24h): 20+
- **Orphaned scripts**: overnight_pipeline.py (not in cron)
- **Duplicates**: morning_briefing agents (multiple entries), multiple GPU/embedding tasks
- **Health**: Database not updating (0 scoring runs yesterday) despite 20+ agents running

---

## Cron Jobs by Category

### 1. **IRS Ingestion & Monitoring** (7 jobs)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 0 * * * * | hourly_irs_status_check.py | Check IRS feed for new filings | ✅ Active |
| 0 21 * * * | daily_irs_check.py | Daily IRS refresh | ✅ Active |
| 0 1 1 * * | download_irs_soi.sh | Monthly SOI extract download | ⏳ Monthly |
| 0 1 * * 0 | aws s3 gt990_index | Weekly gt990 index sync from S3 | ⏳ Weekly |
| 0 */2 * * * | auto_ingest.py | Bimodal IRS ingest (every 2h) | ✅ Active |
| 30 1 3 * * | sync_irs_revocations.py | Monthly revocation sync | ⏳ Monthly |
| 0 2 * * * | db_sync_from_droplet.sh | Sync database from droplet | ✅ Active |

### 2. **Scoring & Enrichment** (5 jobs, 2 ORPHANED)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 0 6 1 * * | monthly_rescore_agent.py | Monthly full rescore | ⏳ Monthly |
| 0 3 * * * | agent_nightly_audit.md | Nightly audit loop (OpenClaw) | ⏰ 3 AM daily |
| 15 3 * * * | agent_outcome_analyzer.py | Analyze previous runs | ⏰ 3:15 AM |
| **[ORPHANED]** | overnight_pipeline.py | ProPublica enrichment + revocation check | ❌ Not in cron |
| **[ORPHANED]** | merit_daemon.sh | Unknown (Sunday 3 AM) | ⏰ May be stuck |

### 3. **ML & Embeddings** (5 jobs, 1 DUPLICATE)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 0 22 * * * | gpu_night.sh start | Start GPU for ML at 10 PM | ✅ Active |
| 0 9 * * * | gpu_night.sh stop | Stop GPU at 9 AM | ✅ Active |
| 0 9 * * * | gpu_night.sh stop_embed_server | Stop embed server (DUPLICATE TIME!) | ⚠️ Conflict |
| */4 * * * * | gpu_queue_manager.py | Manage GPU queue every 4 min | ✅ Active |
| */5 * * * * | log_gpu_temp.sh | Log GPU temp every 5 min | ✅ Active |

### 4. **Search & Embeddings** (2 jobs)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 0 23 * * * | nightly_web_discovery_orchestrator.py | Nightly web discovery Phase 1-3 | ✅ Active (heavy) |
| 0 2 1 * * | precompute_similar_orgs.py | Monthly recompute org similarity | ⏳ Monthly |

### 5. **Agents: Quality, Tagging, Health** (7 jobs)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 15 2 * * * | run_agents.py --agent quality | Daily quality checks (2:15 AM) | ✅ Active |
| 35 2 * * * | run_agents.py --agent cause_tags | Daily cause tag generation (2:35 AM) | ✅ Active |
| 0 4 * * 0 | run_agents.py --agent link_health | Weekly link health check | ⏳ Weekly |
| 0 6 1 * * | run_agents.py --agent enrichment | Monthly enrichment agent | ⏳ Monthly |
| 0 * * * * | phase4_completion_monitor.py | Monitor Phase 4 every hour | ✅ Active (high freq) |
| */30 * * * * | feedback_ingestion_agent.py | Ingest feedback every 30 min | ✅ Active |
| */10 * * * * | surge_detection_agent.py | Surge detection every 10 min | ✅ Active |

### 6. **Backfill & Phase Work** (2 jobs)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 50 2 * * 0 | backfill_stubs.py --phase 1 | Phase 1 backfill (Sunday) | ⏳ Weekly |
| 0 3 * * 1-6 | backfill_stubs.py --phase 2 --limit 300 | Phase 2 backfill (daily M-Sat) | ✅ Active |

### 7. **Email & Comms** (1 job)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 30 7 * * * | email_agent.py run --limit 50 | Triage & draft incoming emails | ✅ Active (7:30 AM) |

### 8. **Reporting & Maintenance** (6 jobs, 1 DUPLICATE)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 0 7 * * * | morning_brief.py | Morning briefing #1 | ⚠️ Duplicate? |
| 0 11 * * * | morning_briefing_agent.py | Morning briefing #2 | ⚠️ Duplicate (both active!) |
| 0 6 * * 1 | weekly_summary_agent.py | Weekly summary (Monday 6 AM) | ⏳ Weekly |
| 15 4 * * 0 | weekly_maintenance.sh | Weekly maintenance | ⏳ Weekly |
| 0 4 * * * | night_batch_launcher.sh | Nightly batch jobs (4 AM) | ✅ Active |
| 0 5 * * 1 | impact_snapshot.py | Weekly impact time-series | ⏳ Weekly |

### 9. **Cause Spotlights** (1 job)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 30 5 * * * | generate_cause_spotlights.py | Daily cause spotlight generation | ✅ Active |

### 10. **Database & Sync** (3 jobs)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 0 7 * * * | sync_db.sh | Daily database sync | ✅ Active |
| 0 23 * * * | sync_db_to_droplet.sh | Nightly push to droplet | ✅ Active |
| 0 3 2 * * | deploy_similar_orgs.sh | Monthly deploy similar orgs | ⏳ Monthly |

### 11. **Deployment & Monitoring** (3 jobs)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 0 3 2 * * | deploy_browse.sh | Monthly deploy browse data | ⏳ Monthly |
| 0 9 1 * * | health-check.sh | Monthly warehouse health check | ⏳ Monthly |
| 0 4 * * 0 | check_link_health.py | Weekly link revalidation | ⏳ Weekly |

### 12. **Other Services** (1 job)
| Schedule | Script | Purpose | Status |
|----------|--------|---------|--------|
| 0 * * * * | albert_etl.py | Procurement stack ETL (hourly) | ✅ Active |

---

## Critical Findings

### 🔴 **BLOCKING ISSUES**

1. **Database Not Updating Yesterday** (0 scoring runs in last 24h)
   - Despite 20+ agents running, registry_enriched not updated
   - monthly_rescore_agent runs only on 1st of month (next: July 1)
   - No daily scoring pipeline active
   - **Impact**: Scores are stale

2. **Orphaned overnight_pipeline.py**
   - Handles ProPublica enrichment + revocation checks
   - **Not scheduled in cron** — work is dropped
   - **Impact**: 1000s of orgs missing ProPublica data
   - **Fix**: Add back to schedule or merge into consolidated pipeline

3. **Duplicate morning_brief Jobs**
   - `morning_brief.py` at 7:00 AM
   - `morning_briefing_agent.py` at 11:00 AM
   - Both logs show recent activity (same day)
   - **Fix**: Consolidate to one job

4. **GPU Shutdown Conflict** (9 AM same-time execution)
   - `gpu_night.sh stop`
   - `gpu_night.sh stop_embed_server`
   - Both run at 0 9 * * * — will race
   - **Fix**: Stagger by 5 min

### ⚠️ **MEDIUM ISSUES**

5. **Phase 4 Monitor Running Every Hour** (not every minute)
   - `*/10 * * * * phase4_completion_monitor.py`
   - Running 6× per hour but unclear impact
   - **Risk**: CPU noise if redundant

6. **High-Frequency Jobs** (every 4-10 minutes)
   - surge_detection_agent.py (10 min)
   - feedback_ingestion_agent.py (30 min)
   - gpu_queue_manager.py (4 min)
   - **Risk**: Database lock contention during heavy phases

7. **No Consolidated Dependency Management**
   - 42 independent jobs with implicit ordering
   - If web_discovery fails, embeddings still run stale data
   - No transactional atomicity (DB might be mid-update when sync fires)
   - **Risk**: Data inconsistency

---

## Logs Health Check (Last 24h)

### ✅ **Recently active** (last 24h)
- web_finder_*.log (12M+, heavy activity)
- embed_server.log (embeddings)
- reembed_watchdog.log (GPU reembedding)
- agent_quality.log, agent_cause_tags.log
- backfill_p2.log
- feedback_ingestion.log, cron.log
- sync logs, gpu_temp.log

### ⏸️ **Stale or missing**
- overnight.log (missing entirely)
- phase4_launch.log (Jun 7)
- agent_cron.log (last 3 AM entry Jun 9)
- link_health.log (Jun 4, no recent runs)

---

## Recommended Consolidation Strategy

### Phase 1: Fix Immediate Blockers
1. **Restore overnight_pipeline.py** to schedule (daily, 2:30 AM before quality check)
2. **Merge duplicate morning briefings** → single job at 7 AM
3. **Stagger GPU shutdown** → 9:05 AM for stop_embed_server
4. **Fix monthly_rescore** → add weekly option or enable scoring in auto_ingest

### Phase 2: Design Unified Orchestrator
Create `master_orchestrator.py` that owns all phases:
```
PHASE 1: IRS Ingest (hourly + daily)
  ↓
PHASE 2: Scoring (weekly or daily)
  ↓
PHASE 3: Enrichment (ProPublica, websites, donations)
  ↓
PHASE 4: Embeddings & Search
  ↓
PHASE 5: Sync to Droplet
  ↓
PHASE 6: Reporting (morning brief, snapshots)
```

**Benefits:**
- Single cron entry: `0 2 * * * master_orchestrator.py`
- Dependency-aware execution (Phase 2 waits for Phase 1)
- Transactional: all or nothing per day
- One log file, unified observability
- Easy to pause/resume phases

### Phase 3: Retire Scattered Jobs
- Migrate legacy cron jobs into master_orchestrator phases
- Keep high-frequency monitors (gpu_queue_manager, email_agent) as satellite jobs
- Archive old scripts

---

## Next Steps (Priority Order)

1. ✅ **Map ecosystem** (this doc) — DONE
2. ⏳ **Identify orphans & duplicates** — SEE ABOVE
3. ⏳ **Design master orchestrator** — Draft skeleton
4. ⏳ **Consolidate jobs** — Implement phases
5. ⏳ **Test & verify** — Run a full cycle

