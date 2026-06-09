# Automated Deployment System

## Overview

The system now automatically detects major data changes and re-deploys to the droplet without manual intervention. Three deployment paths:

1. **Immediate deployment** (now, for launch) — manual trigger
2. **Daily automated detection** — cron at 7 AM daily
3. **Phase 2 completion trigger** — watch_phase2_and_deploy.sh

---

## Deployment Process

All three paths use the same optimized workflow:

```
Stage 1: Score current data (merit_scorer_v4_0)      [2-3 hours, GPU]
  ↓
Stage 2: Load scores into DB                         [~5 min]
  ↓
Stage 3: PARALLEL
  ├─ Build FTS index (~10 min, CPU)
  └─ Export research snapshot (~2 min, light)
  ↓
Stage 4: Deploy to droplet (safe, sandboxed)         [~20 min]

Total: ~3.5 hours wall-clock
```

---

## Deployment Triggers

### 1. Manual Immediate Deployment (TODAY)

```bash
bash scripts/start_same_day_deploy.sh
```

**When**: Now, to launch daanaa.org tonight
**Time**: ~3.5 hours (starts 11 AM, done by ~2:30 PM)
**Log**: `logs/same_day_deploy_immediate.log`

### 2. Automated Daily Detection

**Cron**: 7 AM every morning
```
0 7 * * * source venv/bin/activate && bash scripts/detect_data_changes.sh
```

**What it checks**:
- New org count change (IRS BMF daily watch) — if +100 orgs detected
- New merit scores (rescoring completed)
- Phase 2 enrichment progress or completion
- Recent scoring runs

**If changes detected**: Automatically triggers `start_same_day_deploy.sh`

**Log**: `logs/data_changes.log` + `logs/detect_data_changes_cron.log`

### 3. Phase 2 Completion Trigger

```bash
bash scripts/watch_phase2_and_deploy.sh &
```

**When**: June 13, ~12:30 AM
**What**: Monitors Phase 2 log, auto-triggers `post_phase2_workflow.sh` on completion
**Result**: Droplet updated with enriched financial data by ~4 AM June 13

---

## State Tracking

The system maintains deployment state in `logs/deployment_state.json`:

```json
{
  "last_deploy": "2026-06-09T12:30:00Z",
  "last_org_count": 1968365,
  "last_score_update": "2026-06-09T12:30:00Z"
}
```

Used by `detect_data_changes.sh` to determine if re-deployment is needed. Updated automatically after each deployment.

---

## Monitoring & Logs

**Same-day deployment (immediate)**:
```bash
tail -f logs/same_day_deploy_immediate.log
```

**Daily change detection**:
```bash
tail -f logs/data_changes.log
```

**Scoring stage** (within deployment):
```bash
# Monitor progress at 20%/40%/60%/80%/100%
tail -f logs/post_phase2.log | grep "%"
```

**Phase 2 auto-trigger**:
```bash
tail -f logs/watch_phase2.log
```

---

## Timeline: Today (June 9)

| Time | Stage | Status |
|------|-------|--------|
| 11:10 AM | Deployment starts | ✅ Scoring in progress (GPU active) |
| 11:10 AM – 2:10 PM | Score 1.97M orgs | Monitor: 5 checkpoints |
| 2:10 PM – 2:20 PM | Load scores + FTS (parallel) | No monitoring |
| 2:20 PM – 2:40 PM | Deploy to droplet | Check: 20%, 100% |
| **~2:40 PM** | **Droplet LIVE** | 🚀 daanaa.org goes live |
| 2 PM | Leslie meeting | "Going live at 6 PM" (still accurate) |
| 6 PM | Full verification | Browse daanaa.org, confirm live |

---

## Timeline: June 13 (Phase 2 Completion)

| Time | Stage | Status |
|------|-------|--------|
| 12:30 AM | Phase 2 completes | Monitor detects completion |
| 12:30 AM | Auto-trigger deployment | post_phase2_workflow.sh starts |
| 12:30 AM – 3:30 AM | Re-score with enriched data | Monitor: 5 checkpoints |
| 3:30 AM – 4 AM | FTS + snapshot + deploy | Parallel stages |
| **~4 AM** | **Droplet updated** | ✨ Site now has enriched financial data |

---

## Resumability

Each stage checks for existing output and skips if already done:

**Scoring**: If `scores_v4_0_YYYYMMDD_HHMMSS.json` exists, skips re-scoring
**FTS**: If interrupted, re-run deployment script — picks up where it left off
**Deploy**: Safe sandbox — can retry safely without affecting :5000

---

## Error Handling

If deployment fails at any stage:

1. **Check log** for the stage that failed
2. **Fix the issue** (e.g., DB lock, disk space)
3. **Re-run** `start_same_day_deploy.sh` or `detect_data_changes.sh`
4. **Resumable**: Skips already-completed stages, retries from failure point

**Critical failures** (should not happen):
- DB corruption: `PRAGMA integrity_check` gates deployment
- Disk full: Deploy checks before precompute
- Deploy failure: Atomic swap prevents partial updates on droplet

---

## Manual Overrides

**Force re-deployment (skip change detection)**:
```bash
bash scripts/start_same_day_deploy.sh
```

**Force Phase 2 workflow only (if Phase 2 finishes during manual re-run)**:
```bash
bash scripts/post_phase2_workflow.sh
```

**Skip deploy, just score + index**:
```bash
bash scripts/post_phase2_workflow.sh --skip-deploy
```

---

## Summary: What Changed

| Before | After |
|--------|-------|
| Manual deployment needed | Automatic detection + deployment |
| One-time launch | Continuous improvement cycle |
| Static site after launch | Dynamic updates as data changes |
| 4-day wait for Phase 2 | Live today, enriched on June 13 |
| No feedback loop | Monitor data → detect change → redeploy → iterate |

Site now improves continuously as new data arrives, with **zero manual work**.
