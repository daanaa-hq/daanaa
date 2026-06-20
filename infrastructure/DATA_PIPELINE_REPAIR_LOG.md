# Data Pipeline Repair Session — 2026-06-20

## Background Operations (Running in Parallel)

**Start Time:** 2026-06-20 16:55 UTC  
**Estimated Completion:** 2026-06-20 17:30 UTC (35 min)

### Operation 1: FTS5 Index Rebuild
```bash
python3 scripts/build_fts_index.py --rebuild
```
- **Status:** Running (PID 589829)
- **Purpose:** Sync FTS5 index with registry
- **Current state:** 1,858,452 indexed vs 2,064,613 source (206,161 missing, 10%)
- **Expected outcome:** 2,064,613 indexed (100% coverage)

### Operation 2: Merit Scorer v4.0
```bash
python3 scripts/merit_scorer_v4_0.py --output /tmp/scores.json
```
- **Status:** Running (PID 589834)
- **Purpose:** Compute peer financial context scores (v4) for all orgs
- **Current state:** 537,920 scored (26% coverage)
- **Expected outcome:** ~1.9M scored (92%+ coverage, limited by financial data availability)
- **Output:** `/tmp/scores.json` (to be imported to database)

## Pre-Repair State

| Metric | Count | % |
|--------|-------|---|
| Total orgs in registry | 2,064,613 | 100% |
| FTS5 indexed | 1,858,452 | 90% |
| **FTS5 gap** | **206,161** | **10%** |
| Scored (v4) | 537,920 | 26% |
| Scored (v5) | 447,557 | 21.7% |

## Next Steps (After Completion)

1. **Verify FTS5 rebuild:** Count should reach 2,064,613
2. **Import scorer output:** Load `/tmp/scores.json` into database
3. **Rebuild embeddings:** Update org_embeddings table for new orgs
4. **Run health check:** `python3 infrastructure/pipeline/pipeline_health.py`
5. **Verify API:** Test directory, search, org detail endpoints
6. **Backup post-repair:** Run daily_backup.sh to capture new state
7. **Monitor:** Watch metrics for search latency, scoring queries

## Post-Repair Goals

- [ ] FTS5: 2,064,613 indexed (100%)
- [ ] v4 scores: >1,800,000 (>85%)
- [ ] v5 scores: >1,600,000 (>75%)
- [ ] Embeddings: >500,000 computed
- [ ] Search latency: <100ms for most queries
- [ ] No "out of sync" warnings in health check

## Monitoring

Check progress:
```bash
# Monitor background jobs
jobs -l

# Check database state (mid-operation)
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM org_fts;"

# Check scorer progress (if verbose logging)
tail -f /tmp/scores.json | tail -1 | jq '.count'
```

## Rollback Plan

If repair fails:
1. Stop background jobs: `kill 589829 589834`
2. Restore from backup: `bash infrastructure/backup/test_restore.sh`
3. Re-diagnose with `python3 infrastructure/pipeline/pipeline_health.py`

---

**Session Owner:** Claude Code  
**Estimated Impact:** Improves search coverage 10%, scoring coverage 4x  
**Risk Level:** Low (operations are deterministic, can be repeated)
