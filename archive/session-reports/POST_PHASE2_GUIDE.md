# Post-Phase-2 Workflow Guide

## Overview

After Phase 2 (ProPublica financial enrichment) completes, we need to:
1. Score all 1.97M orgs with v4.0 scorer
2. Rebuild search indexes (FTS)
3. Export research snapshot with fresh data
4. Deploy to the droplet

This guide documents the updated, tested process.

---

## Files Updated/Created (June 9, 2026)

| File | Change | Status |
|------|--------|--------|
| `scripts/build_fts_index.py` | ⭐ **UPDATED** | Now indexes 1.97M visible orgs, adds cause_tags + category fields, filters by deductibility=1 & org_status='active', batched insert for speed |
| `scripts/overnight_pipeline.py` | ⭐ **UPDATED** | Now calls merit_scorer_v4_0 nightly (non-blocking) |
| `scripts/post_phase2_workflow.sh` | ✅ **CREATED** | Complete post-Phase-2 orchestration: score → load → FTS rebuild → snapshot → deploy |
| `scripts/watch_phase2_and_deploy.sh` | ✅ **CREATED** | Auto-trigger: monitors Phase 2 log, runs post_phase2_workflow.sh on completion |

---

## How to Trigger

### Option 1: Manual (Recommended for first run)

When Phase 2 completes, run:

```bash
cd ~/meritgiving
source venv/bin/activate
bash scripts/post_phase2_workflow.sh
```

**Time estimate**: ~3-4 hours total
- Scoring: ~2-3 hours
- FTS rebuild: ~10 min
- Snapshot export: ~2 min
- Deploy: ~20 min

### Option 2: Automatic (Background)

To monitor Phase 2 and auto-trigger when done:

```bash
bash scripts/watch_phase2_and_deploy.sh &
```

This will:
1. Poll every 30 seconds for Phase 2 completion
2. Auto-trigger `post_phase2_workflow.sh` when detected
3. Run the full workflow in the background
4. Exit when complete

**Best for**: Overnight/unattended runs

### Option 3: Dry Run (Test the plan)

To see what will run without executing:

```bash
bash scripts/post_phase2_workflow.sh --dry-run
```

### Option 4: Skip Final Deploy

To score/index without deploying to droplet:

```bash
bash scripts/post_phase2_workflow.sh --skip-deploy
```

---

## Workflow Stages

### Stage 1: Score all orgs (merit_scorer_v4_0)

```bash
python3 scripts/merit_scorer_v4_0.py --output scores_v4_0_YYYYMMDD_HHMMSS.json
```

**What it does:**
- Scores 1,968,365 tax-deductible, active orgs
- Uses 9 operating models (financial archetypes)
- Produces 0-100 peer financial context scores
- Outputs JSON file

**Time**: ~2-3 hours
**Resumable**: Yes — if scores file already exists, skips this stage

### Stage 2: Load scores into DB

```bash
python3 scripts/load_v4_scores.py scores_v4_0_YYYYMMDD_HHMMSS.json
```

**What it does:**
- Reads JSON scores file
- Updates `registry_enriched.merit_score`, `merit_tier`, `merit_band`
- Records scorer version and timestamp

**Time**: ~5 min

### Stage 3: Rebuild FTS search index

```bash
python3 scripts/build_fts_index.py --rebuild
```

**What it does:**
- Drops existing `org_fts` table
- Recreates with expanded fields: org_name, mission, city, state, category (NTEECC), cause_tags
- Inserts 1.97M visible orgs (deductibility=1, org_status='active') in batches
- Optimizes the index

**Changes from May 26 version:**
- ✅ Now filters by deductibility=1 and org_status='active' (only visible orgs)
- ✅ Adds NTEECC category and cause_tags to searchable fields
- ✅ Batched insert for 2M-scale performance
- ✅ Progress logging with ETA

**Time**: ~5-10 min

### Stage 4: Export research snapshot

```bash
MERIT_DB_PATH=data/merit_registry.db python3 scripts/export_research_snapshot.py
```

**What it does:**
- Reads fresh scores from `registry_enriched`
- Generates sector health tables (all 26 NTEE categories)
- Outputs `frontend/public/research-snapshot.json` for the research page
- ~50-100 KB

**Time**: ~2 min

### Stage 5: Deploy to droplet

```bash
bash scripts/safe_deploy_droplet.sh
```

**What it does:**
- Snapshots live DB (never locks :5000)
- Integrity checks snapshot DB
- Precomputes all static files in sandbox:
  - Browse results (category × state)
  - Org detail pages with FAISS similar-orgs (1.97M files)
  - FAISS semantic index (quantized to 129 MB)
  - Research/methodology pages
- Validates all donate/website links against snapshot
- Deploys to droplet atomically (v0→v1 swap, v2→v0 backup for rollback)

**Time**: ~20 min

---

## Monitoring & Logs

**Post-Phase-2 workflow log:**
```bash
tail -f logs/post_phase2.log
```

**Individual stages:**
- Scorer: Built-in logging (appears in `post_phase2.log`)
- FTS: Progress every 50K orgs
- Snapshot: `export_research_snapshot.py` output
- Deploy: `safe_deploy_droplet.sh` progress + final status

---

## Rollback

If something fails mid-deploy, the droplet is safe:

1. **Check droplet status:**
   ```bash
   curl https://daanaa.org/api/stats
   ```

2. **If deploy failed (v1 is bad):**
   ```bash
   ssh user@daanaa_droplet
   # Manually swap back: v0 (backup) → current
   ```

3. **To re-run deploy only:**
   ```bash
   bash scripts/post_phase2_workflow.sh --skip-scorer --skip-fts  # (not yet, but you can just re-run safe_deploy_droplet.sh)
   ```

---

## Verification After Completion

**Local (:5000):**
```bash
curl http://localhost:5000/api/stats
# Should show: 1,968,365 visible orgs, updated merit_score counts
```

**Droplet (daanaa.org):**
```bash
curl https://daanaa.org/api/stats
# Should match local
```

**Site verification:**
- Browse to https://daanaa.org/directory
- Check an org detail page — should show new merit scores
- Research page: https://daanaa.org/research (should show updated sector health)

---

## Nightly Scorer Integration

The `overnight_pipeline.py` now calls `merit_scorer_v4_0` at the end of its nightly run (after enrichment completes). This keeps scores fresh without manual intervention.

**Current cron schedule:**
```
30 2 * * * cd ~/meritgiving && source venv/bin/activate && python3 scripts/overnight_pipeline.py >> logs/overnight.log 2>&1
```

The scorer is non-blocking — if it errors, the pipeline continues. Check `overnight.log` for scorer status.

---

## Summary of Changes

| Component | Before | After |
|-----------|--------|-------|
| **Scorer in pipeline** | Manual only | Nightly + post-Phase-2 |
| **FTS index** | May 26 (pre-2M) | June 9 (2M-optimized, deductibility filter, more fields) |
| **Post-Phase-2 process** | Manual multi-step | Automated, resumable, logged |
| **Safe deploy** | New in June 9 | Now uses post_phase2_workflow.sh |
| **Auto-trigger** | N/A | watch_phase2_and_deploy.sh monitors Phase 2 |

---

## Questions?

- Scorer details: See `scripts/merit_scorer_v4_0.py` header
- Deploy safety: See `scripts/safe_deploy_droplet.sh` comments
- FTS improvements: See `scripts/build_fts_index.py` docstring
