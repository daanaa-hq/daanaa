# Phase 5 Launch Ready — Final Checklist

**Date:** 2026-06-21  
**Status:** Ready to launch when Phase 4 completes  
**Estimated runtime:** 30-40 hours for 15-25K orgs on GPU 1  
**Launch command:** `bash ~/meritgiving/scripts/launch_phase5_bg.sh`

## Pre-Launch Validation

### Database State
- [x] mission column exists in registry_enriched
- [x] cause_tags column exists in registry_enriched
- [x] Phase 4 will populate website_status='beta' for verified orgs
- [x] No schema changes needed for Phase 5

### GPU Resources
- [x] mxbai-embed-large ready on port 11436 (used by Phase 4)
- [x] Qwen2.5-32B ready on port 11437 (for Phase 5 mission generation)
- [x] GPU 0 → Phase 4 (semantic verification)
- [x] GPU 1 → Phase 5 (mission backfill)
- [x] Can run in parallel once Phase 4 produces first batch

### Scripts Verified
- [x] phase5_mission_backfill.py — 380 lines, Qwen2.5 integration, checkpointing every 100 orgs
- [x] cause_taxonomy.py — 168 lines, 15-cause taxonomy, 120+ keyword patterns
- [x] phase5_monitor.py — 247 lines, real-time progress tracking, alerts
- [x] launch_phase5_bg.sh — 328 lines, launcher with health checks, auto-restart (up to 5x)

### Health Checks (Run on Launch)
```bash
# Verify databases
sqlite3 ~/meritgiving/data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE website_status='beta' LIMIT 1;"

# Verify GPU
curl -s http://localhost:11437/health | jq .

# Verify Phase 4 output format
sqlite3 ~/meritgiving/data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE website_status='beta' LIMIT 1;"
```

## Launch Sequence

### 1. Wait for Phase 4 Completion
- Monitor: `ps aux | grep phase4_semantic`
- When count of `website_status='beta'` orgs > 0, Phase 4 has found first match
- Phase 4 completes when count stabilizes (all 100/50K candidates processed)

### 2. Pre-Launch Checks (2 min)
```bash
# Run these before launching Phase 5
bash ~/meritgiving/scripts/phase5_monitor.py --check-only
# Should output: ✓ Database healthy, ✓ GPU responsive, ✓ 15K+ orgs to process
```

### 3. Launch Phase 5 (one command)
```bash
bash ~/meritgiving/scripts/launch_phase5_bg.sh
```
- Starts mission generation on GPU 1
- Checkpoints every 100 orgs (resumable)
- Logs to /tmp/phase5_progress.log
- Runs for 30-40 hours

### 4. Monitor Progress
```bash
# Watch in real-time
tail -f /tmp/phase5_progress.log

# Or query database periodically
watch -n 10 "sqlite3 ~/meritgiving/data/merit_registry.db \
  \"SELECT COUNT(*) as total, COUNT(CASE WHEN mission IS NOT NULL THEN 1 END) as with_missions FROM registry_enriched WHERE website_status='beta';\""
```

## Rollback / Resume

**If interrupted:** Phase 5 checkpoints every 100 orgs. To resume:
```bash
bash ~/meritgiving/scripts/launch_phase5_bg.sh --resume
```

**If GPU fails:** Auto-restart up to 5 times with exponential backoff (5s, 10s, 20s, 40s, 80s).

**If database locks:** Retry logic with exponential backoff (2s, 4s, 8s).

## Success Criteria

Phase 5 succeeds when:
- ✓ Mission text generated for 15K+ orgs
- ✓ Cause tags extracted for 15K+ orgs
- ✓ No unrecoverable errors (GPU failures recoverable)
- ✓ Database remains consistent
- ✓ Can query: `SELECT * FROM registry_enriched WHERE website_status='beta' AND mission IS NOT NULL LIMIT 5`

## Timeline

| Phase | Duration | GPU | Status |
|-------|----------|-----|--------|
| Phase 4 (Semantic Verification) | 10-15 hours | GPU 0 | Running (100-org test) |
| Phase 5 (Mission Generation) | 30-40 hours | GPU 1 | Ready to launch |
| **Total** | **40-55 hours** | Both | Parallel after Phase 4 starts producing |

## Monitoring Dashboards

While Phase 5 runs:
```bash
# Terminal 1: Watch progress
tail -f /tmp/phase5_progress.log

# Terminal 2: Track database
sqlite3 ~/meritgiving/data/merit_registry.db \
  "SELECT COUNT(*) FROM registry_enriched WHERE website_status='beta' AND mission IS NOT NULL;" \
  && echo "orgs with missions"

# Terminal 3: GPU health
watch -n 5 "curl -s http://localhost:11437/health | jq ."
```

---

**Next action:** When Phase 4 completes (produces website_status='beta' orgs), execute:
```
bash ~/meritgiving/scripts/launch_phase5_bg.sh
```
