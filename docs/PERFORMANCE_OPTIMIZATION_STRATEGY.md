# Daanaa V6 Performance Optimization Strategy

**Baseline Date:** August 9, 2026
**Baseline Database:** 2.056M orgs, 23.4 GB, SQLite

## Executive Summary

Audit identified peer group stats aggregation as the critical bottleneck (405ms). Scoring queries are moderately slow (238-271ms). FTS search has high variance (median 1.8ms, p95 60ms). Overall database performance is acceptable but can be improved 2-5x with strategic indexing.

## Current Baseline Performance

| Query | Mean | Median | P95 | Issue |
|-------|------|--------|-----|-------|
| count_all_orgs | 4.42ms | 4.26ms | — | Good |
| fetch_by_ein | 0.02ms | 0.01ms | — | Excellent (PK lookup) |
| fetch_100_orgs | 0.69ms | 0.64ms | — | Good |
| fts_search | 8.74-13ms | 1.8ms | 60ms | High variance |
| count_scored_orgs | 266ms | 265ms | — | SLOW: full scan |
| filter_by_ntee | 238ms | 238ms | — | SLOW: full scan |
| top_100_by_score | 271ms | 271ms | — | SLOW: full scan + sort |
| peer_group_stats | 406ms | 404ms | — | VERY SLOW: complex GROUP BY + aggregation |

## Root Causes

### 1. Peer Group Stats Query (406ms)
```sql
SELECT NTEE1, COUNT(*), AVG(merit_score), MIN(), MAX()
FROM registry_enriched
WHERE merit_score IS NOT NULL
GROUP BY NTEE1
```

**Problem:** No index on `(NTEE1, merit_score)`. Query scans all 2.056M rows, filters to 537K scored orgs, then aggregates.

**Impact:** This query runs on every org detail page load to compute peer percentiles.

### 2. Scoring Filter Queries (238-271ms)
```sql
SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL
SELECT * FROM registry_enriched WHERE NTEE1 = ? ORDER BY merit_score DESC
```

**Problem:** No index on `merit_score` or `(NTEE1, merit_score)`.

**Impact:** Every score-based sort or filter scans full table.

### 3. FTS Search Variance (1.8ms median, 60ms p95)
**Problem:** Some searches match very common words (health, nonprofit) that return many results. Variance suggests cache behavior.

**Impact:** Users see inconsistent search response times.

## Optimization Plan

### Phase 1: Strategic Indexing (Safe, Reversible)

**Indexes to Add:**
1. `idx_merit_score` on `merit_score` (improves score-based queries)
2. `idx_ntee1_merit_score` on `(NTEE1, merit_score)` (improves peer group queries)
3. `idx_website_donate_url` on `(website, donate_url)` (improves link discovery)

**Expected Impact:**
- Peer group stats: 406ms → ~50ms (8x improvement)
- Scoring filters: 238ms → ~30ms (8x improvement)
- Overall org detail load: proportional improvement

**Execution:** Safe to add; can drop if performance degrades.

### Phase 2: Materialized Peer Group Stats (Medium Risk)

**Approach:** Pre-compute peer group stats in nightly pipeline, store in new table or JSON column.

**Benefit:** Org detail pages fetch pre-computed stats instead of computing live.

**Risk:** Must keep in sync with registry_enriched changes.

**Mitigation:** Recompute every nightly pipeline run.

**Expected Impact:** Peer stats queries: ~50ms → ~1ms (40x improvement for clients)

### Phase 3: Query Result Caching (Low Risk)

**Approach:** In-process cache for deterministic queries (peer group stats, aggregations).

**Benefit:** Repeat queries return cached results within TTL.

**Risk:** Staleness if data changes mid-day (acceptable, recomputed nightly).

**Expected Impact:** Cached queries: 50ms → ~0.1ms for in-cache hits.

### Phase 4: FTS Optimization (If Needed)

**Options:**
- Add BM25 term weighting tuning
- Implement query normalization (remove very common words)
- Use semantic search (embeddings) for complex queries

**Status:** Defer unless FTS variance remains critical.

## Implementation Priority

| Priority | Phase | Effort | Risk | Gain | Timeline |
|----------|-------|--------|------|------|----------|
| 1 | Phase 1 Indexing | 1h | Low | 8x on scoring | Now |
| 2 | Phase 2 Materialization | 4h | Medium | 40x on peer stats | This week |
| 3 | Phase 3 Caching | 2h | Low | 10x on cached queries | This week |
| 4 | Phase 4 FTS | 4h | Medium | 2x variance reduction | If needed |

## Success Criteria

**Launch Ready (October 12):**
- Org detail page: <300ms p95 (current: varies, goal: <200ms)
- Search: <200ms p95 (current: depends on query)
- Peer group stats: <50ms (current: 406ms)

**Post-Launch Optimization:**
- Materialized stats: <10ms (20x improvement)
- Full-page load with caching: <500ms (from ~1000ms)

## Rollback Plan

All indexing is reversible:
```sql
DROP INDEX idx_merit_score;
DROP INDEX idx_ntee1_merit_score;
DROP INDEX idx_website_donate_url;
```

Materialized stats can be disabled by reverting nightly pipeline.

## Next Steps

1. **Immediate:** Add Phase 1 indexes (1h, safe)
2. **This week:** Implement Phase 2 materialization (4h, medium risk, high gain)
3. **This week:** Add Phase 3 caching (2h, low risk)
4. **Monitor:** Track p95 latencies post-deployment
5. **Review:** Audit again after Phase 2 to verify gains

## Files to Update

- `daanaa_api.py`: Add materialized stats query (Phase 2)
- `scripts/overnight_pipeline.py`: Compute stats at nightly run (Phase 2)
- `scripts/performance_audit_comprehensive.py`: Baseline established
- Database migrations: Add indexes (Phase 1)

---

**Status:** STRATEGY DOCUMENT
**Ready for:** Implementation (Phase 1 approved and safe to execute autonomously)
**Requires approval for:** Phase 2+ (changes nightly pipeline, medium risk)
