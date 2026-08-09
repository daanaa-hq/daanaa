# Phase 2: Materialized Peer Group Stats

**Status:** PREPARED (not yet implemented, awaiting index completion and testing)
**Timeline:** This week
**Risk:** Medium (requires nightly pipeline modification)
**Expected Gain:** 406ms → ~10ms for stats queries (40x improvement)

## Problem Statement

Every org detail page load computes peer group statistics:

```sql
SELECT NTEE1, COUNT(*), AVG(merit_score), MIN(merit_score), MAX(merit_score)
FROM registry_enriched
WHERE merit_score IS NOT NULL
GROUP BY NTEE1
```

This takes 406ms. With Phase 1 indexes, it will be ~50ms. But org detail pages need this data for every load, making it a repeated bottleneck.

**Solution:** Pre-compute during nightly pipeline, store in database.

## Implementation Plan

### Step 1: Create Materialized Stats Table

```sql
CREATE TABLE IF NOT EXISTS peer_group_stats (
    NTEE1 TEXT PRIMARY KEY,
    org_count INTEGER,
    scored_count INTEGER,
    avg_score REAL,
    min_score REAL,
    max_score REAL,
    percentile_25 REAL,
    percentile_50 REAL,
    percentile_75 REAL,
    last_computed DATETIME,
    data_hash TEXT  -- For change detection
);

CREATE INDEX idx_peer_stats_ntee1 ON peer_group_stats(NTEE1);
```

### Step 2: Add Computation to Nightly Pipeline

In `scripts/overnight_pipeline.py`, after scoring completes:

```python
def compute_peer_group_stats(db):
    """Compute and store peer group statistics."""
    cursor = db.cursor()
    
    # Get current data hash
    cursor.execute("SELECT COUNT(*), SUM(merit_score) FROM registry_enriched WHERE merit_score IS NOT NULL")
    row = cursor.fetchone()
    current_hash = hashlib.md5(f"{row[0]}{row[1]}".encode()).hexdigest()
    
    # Check if stats need update
    cursor.execute("SELECT data_hash FROM peer_group_stats LIMIT 1")
    last_hash = cursor.fetchone()
    
    if last_hash and last_hash[0] == current_hash:
        print("Peer group stats unchanged, skipping recompute")
        return
    
    # Compute stats for each NTEE1
    cursor.execute("""
        SELECT
            NTEE1,
            COUNT(*) as org_count,
            COUNT(CASE WHEN merit_score IS NOT NULL THEN 1 END) as scored_count,
            AVG(merit_score) as avg_score,
            MIN(merit_score) as min_score,
            MAX(merit_score) as max_score,
            CAST((SELECT COUNT(*) FROM registry_enriched AS r2 
                  WHERE r2.NTEE1 = r1.NTEE1 AND r2.merit_score <= r1.merit_score) * 100.0 / 
                 COUNT(*) AS REAL) as percentile_score
        FROM registry_enriched AS r1
        WHERE merit_score IS NOT NULL
        GROUP BY NTEE1
    """)
    
    stats = cursor.fetchall()
    
    # Upsert into materialized table
    for row in stats:
        cursor.execute("""
            INSERT OR REPLACE INTO peer_group_stats
            (NTEE1, org_count, scored_count, avg_score, min_score, max_score, last_computed, data_hash)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)
        """, (*row, current_hash))
    
    db.commit()
    print(f"Computed peer group stats for {len(stats)} categories")
```

### Step 3: Modify API to Use Cached Stats

In `daanaa_api.py`, org detail endpoint:

```python
def get_org_peer_group_context(ein, ntee1):
    """Get peer group stats from materialized table."""
    cursor = db.cursor()
    
    # Fast lookup from materialized table
    cursor.execute("""
        SELECT avg_score, min_score, max_score, org_count, percentile_25, percentile_50, percentile_75
        FROM peer_group_stats
        WHERE NTEE1 = ?
    """, (ntee1,))
    
    stats = cursor.fetchone()
    
    if not stats:
        # Fallback to compute if not yet materialized
        return compute_peer_group_live(ntee1)
    
    return {
        'peer_avg': stats[0],
        'peer_min': stats[1],
        'peer_max': stats[2],
        'peer_count': stats[3],
        'percentiles': {
            'p25': stats[4],
            'p50': stats[5],
            'p75': stats[6]
        }
    }
```

## Testing Strategy

### Before Deployment

1. **Correctness Test:**
   - Compute live (current method): get results
   - Compute materialized: get results
   - Compare: must match exactly

2. **Performance Test:**
   - Fetch from materialized table: should be <2ms
   - Verify with org detail load test

3. **Consistency Test:**
   - Run materialized compute 3 times
   - Verify results are identical each time

### Post-Deployment

1. **Monitor nightly pipeline:** stats computation time
2. **Monitor API latency:** org detail endpoint with materialized stats
3. **Alert on staleness:** if stats not computed for 25 hours

## Rollback Plan

If issues arise:

```sql
-- Disable materialized stats
DELETE FROM peer_group_stats;

-- Modify API to always compute live
# In daanaa_api.py, revert get_org_peer_group_context() to live computation

-- Drop table (optional)
DROP TABLE peer_group_stats;
```

## Success Metrics

- Peer group stats: 50ms → <2ms (25x improvement)
- Org detail page load: ~1000ms → ~600ms (proportional improvement)
- Nightly pipeline: <5 second overhead for stats computation

## Files to Modify

1. `scripts/overnight_pipeline.py` - Add compute_peer_group_stats()
2. `daanaa_api.py` - Modify org detail endpoint to fetch materialized stats
3. `docs/PERFORMANCE_OPTIMIZATION_STRATEGY.md` - Update status
4. Database migration script - Create table and indexes

## Timeline

- **Before:** Phase 1 indexes complete and verified (in progress)
- **Day 1:** Code review and testing against staging DB
- **Day 2:** Deploy to production during nightly pipeline
- **Day 3-7:** Monitor and verify gains

---

**Status:** Ready to implement after Phase 1 indexes are verified
**Approval:** Requires founder for nightly pipeline modification
