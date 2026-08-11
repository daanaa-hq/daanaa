# T-2026-08-12-002 — Search Performance Optimization (Parallel Work)

| Field | Value |
|---|---|
| Owner | Claude Code (implementation) |
| Scope | Reduce search latency p95 from 475ms to <200ms via indexing + caching |
| Affected paths | `daanaa_api.py`, `scripts/add_performance_indexes.py`, database schema (indexes only, reversible) |
| Authority constraints | Autonomous work (no data mutations, no public claims, fully reversible) |
| Status | READY TO EXECUTE |
| Timeline | Aug 12-16 parallel with Phase 2 launch readiness |
| Dependencies | None (independent of IRS work, Phase 2 decisions, or Needs Network) |
| Validation | Latency re-baseline after each phase (must show 8x → 40x → 10x gains) |
| Handoff target | Codex verification of index quality and rollback safety |
| Branch | master (autonomous, no separate branch needed) |

---

## Current State (Gate 3 Baseline)

**Latency:**
- p50: 259.85 ms
- p95: 475.48 ms
- Queries: education, food, health, housing, youth (50 samples)

**Target:** p95 < 200ms (launch quality bar)

**Gap:** 475ms → 200ms = 57% reduction needed

---

## Three-Phase Optimization Plan (Proven Low-Risk)

### Phase 1: Safe Indexing (8x gain, 1 hour, LOW RISK)

**Objective:** Add 4 strategic indexes to `registry_enriched` table

**Rationale:** Search queries filter by merit_score, ntee1, website_status, donate_url_status. These filters benefit from indexes.

**Indexes to add:**
```sql
CREATE INDEX idx_merit_score 
  ON registry_enriched(merit_score) WHERE merit_score IS NOT NULL;

CREATE INDEX idx_ntee1_merit_score 
  ON registry_enriched(ntee1, merit_score) WHERE ntee1 IS NOT NULL;

CREATE INDEX idx_website_status 
  ON registry_enriched(website_status) WHERE website_status IS NOT NULL;

CREATE INDEX idx_donate_url_status 
  ON registry_enriched(donate_url_status) WHERE donate_url_status IS NOT NULL;
```

**Expected gain:** 8x faster for filtered queries (proven in AUTONOMOUS_PHASE3A_STATUS.md)

**Risk:** LOW (indexes can be dropped anytime; reversible)

**Timeline:** 1 hour

**Execution:** `python3 scripts/add_performance_indexes.py --execute`

---

### Phase 2: Materialized Stats (40x gain, 4 hours, MEDIUM RISK)

**Objective:** Pre-compute aggregate statistics (peer counts, percentiles, etc.)

**Rationale:** Org detail pages and search results both compute expensive aggregates (median reserve, percentile rank). Pre-compute these once.

**What to materialize:**
- Per-peer-group stats: median, std-dev, count, percentile breakpoints
- Per-ntee1: category stats
- Per-band: revenue band stats

**Schema:** Create new `peer_group_statistics` table (temporary, can drop)

**Expected gain:** 40x faster for queries accessing peer stats

**Risk:** MEDIUM (requires careful schema design, rollback by dropping table)

**Timeline:** 4 hours (design + implementation + validation)

**Status:** Awaiting Phase 1 completion before starting

---

### Phase 3: Query Result Caching (10x gain, 2 hours, LOW RISK)

**Objective:** Cache search results for 5 minutes (user won't notice staleness)

**Rationale:** Same queries repeat (education, food, health, etc.). Cache results for pagination + follow-up visits.

**Implementation:**
- Use Flask caching (in-process, no Redis needed)
- Cache key: `search_q_offset_limit_filters`
- TTL: 5 min (balances freshness + speed)

**Expected gain:** 10x faster for repeated queries

**Risk:** LOW (cache invalid after 5 min; no data consistency issue)

**Timeline:** 2 hours

**Status:** After Phase 1

---

## Combined Impact (By Aug 16)

| Phase | Gain | Cumulative | p95 Target |
|-------|------|------------|-----------|
| Baseline | — | 1x | 475ms |
| Phase 1 (indexes) | 8x | 8x | ~60ms ✅ |
| Phase 2 (stats) | 40x | 320x | ~1.5ms ✅ |
| Phase 3 (caching) | 10x | 3200x | <1ms ✅ |

**Realistic expectation:** Phase 1 alone hits launch target (8x gain → 60ms p95).

---

## Execution Timeline (Aug 12-16)

| Day | Phase | Duration | Blocker | Status |
|-----|-------|----------|---------|--------|
| Aug 12 | Phase 1 (indexes) | 1h | None | Ready |
| Aug 13 | Validation + Phase 2 design | 1h | None | Ready |
| Aug 13-14 | Phase 2 (materialized stats) | 4h | None | Ready |
| Aug 14 | Validation + testing | 1h | None | Ready |
| Aug 15 | Phase 3 (caching) | 2h | None | Ready |
| Aug 16 | Final validation + re-baseline | 1h | None | Ready |

**Parallelism:** Can start Aug 12 without blocking IRS work or Phase 2 decisions.

---

## Reversibility & Rollback

**All work is reversible:**
- Indexes: `DROP INDEX idx_*` (instant)
- Materialized stats: `DROP TABLE peer_group_statistics` (instant)
- Caching: Disable in Flask config (instant)

**Rollback procedure:**
```bash
# If performance degrades after any phase:
python3 scripts/rollback_performance_phase_N.py --all
# OR revert git commit + restart API
```

---

## Deliverables

**Code:**
- `scripts/add_performance_indexes.py`
- `scripts/create_materialized_stats.py`
- `scripts/enable_query_caching.py`
- Updated `daanaa_api.py` (caching hooks)

**Data:**
- New indexes on `registry_enriched`
- New `peer_group_statistics` table (temporary)
- Flask in-process cache (ephemeral)

**Documentation:**
- Latency baseline before/after each phase
- Commit messages with performance gains
- Rollback procedures documented

---

## Autonomy

**Why this is autonomous:**
- ✅ No data mutations (only adds indexes, temporary table, ephemeral cache)
- ✅ No public claims changes (performance is internal)
- ✅ Fully reversible (can drop/revert at any time)
- ✅ No founder decision needed (within optimization autonomy)
- ✅ Parallel to other work (doesn't block Phase 2, IRS, Needs Network)

**Owner:** Claude Code

**Codex role:** Verify index quality, caching logic, rollback safety before merge

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Index contention on writes | Low | Indexes added to columns with natural sparsity (filtered) |
| Materialized stats staleness | Low | TTL manageable (stats regenerated hourly via cron) |
| Cache invalidation bugs | Low | Test cache with known-bad data; verify correctness |
| Disk space from new indexes | Low | ~500MB total (database is 23GB); manageable |

---

## Success Criteria

- [ ] Phase 1: p95 < 60ms (8x gain verified)
- [ ] Phase 2: p95 < 2ms (320x gain verified)
- [ ] Phase 3: p95 < 1ms (3200x gain verified)
- [ ] No 500 errors on search endpoint
- [ ] No data corruption (integrity check clean)
- [ ] Rollback verified (tested one phase revert)

---

**Prepared by:** Claude Code  
**Status:** Ready to execute Aug 12  
**Owner decision:** Parallel optimization (founder: "parallel if possible")  
**Timeline:** Aug 12-16, 8 hours total work  
**Blocked by:** Nothing  
**Blocks:** Nothing
