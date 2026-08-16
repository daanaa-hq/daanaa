# API Integration Plan — v4.0 Scores

**Status:** Ready for implementation (v4 scores validated and in database)

## Overview

v4 scores are now in `v4_scores` table. API integration adds new fields to org responses without breaking v3 functionality.

## Changes Required

### 1. Org Response Structure

**Add these fields to all org responses (search, detail, similar):**

```json
{
  // existing fields (unchanged)
  "merit_score": 42.5,
  "merit_tier": "Growing",
  
  // NEW: v4.0 scores
  "financial_health": "Stable",              // Strong / Stable / Inspiring
  "operating_model": "Direct_Service",       // 8 models
  "revenue_band": 3,                         // 0-7
  "peer_cell_size": 2865,
  "v4_metrics": {...}                        // optional: detailed metrics for transparency
}
```

### 2. SQL Queries to Update

All org-returning queries need LEFT JOIN to v4_scores:

```sql
SELECT 
  -- existing columns...
  r.merit_score, r.merit_tier, r.merit_band,
  
  -- NEW: v4 columns
  v4.merit_score as v4_score,
  v4.financial_health,
  v4.operating_model,
  v4.revenue_band,
  v4.peer_cell_size,
  v4.metrics_json

FROM registry_enriched r
LEFT JOIN v4_scores v4 ON r.EIN = v4.EIN
```

### 3. Environment Variables

**Add to `.env`:**
```bash
ENABLE_V4_SCORES=true          # Toggle v4 on/off (default: true)
ENABLE_V4_METRICS=false        # Include detailed metrics (default: false)
```

**Usage:**
```python
ENABLE_V4 = os.getenv('ENABLE_V4_SCORES', 'true').lower() == 'true'
ENABLE_V4_DETAIL = os.getenv('ENABLE_V4_METRICS', 'false').lower() == 'true'
```

### 4. Response Builder Helper

Add to `merit_api.py`:

```python
def _attach_v4_scores(org: dict, v4_row: sqlite3.Row | None, include_metrics: bool = False) -> dict:
    """Attach v4 scores to org response."""
    if not ENABLE_V4 or not v4_row:
        return org
    
    org['financial_health'] = v4_row['financial_health']
    org['operating_model'] = v4_row['operating_model']
    org['revenue_band'] = v4_row['revenue_band']
    org['peer_cell_size'] = v4_row['peer_cell_size']
    
    if include_metrics and v4_row['metrics_json']:
        org['v4_metrics'] = json.loads(v4_row['metrics_json'])
    
    return org
```

### 5. Endpoints to Update

| Endpoint | Location | Change |
|----------|----------|--------|
| `GET /api/orgs` | list_organizations() | Add v4 join, call _attach_v4_scores() |
| `GET /api/orgs/<EIN>` | get_organization() | Add v4 join |
| `POST /api/search` | fused_search() | Add v4 join |
| `GET /api/similar/<EIN>` | get_similar_organizations() | Add v4 join |

### 6. Backward Compatibility

- v3 scores (merit_score, merit_tier, merit_band) remain unchanged
- v4 fields are optional (graceful degradation if v4_scores is empty)
- ENABLE_V4_SCORES=false → v4 fields not returned

### 7. Caching

- Update cache keys to include v4 version
- TTL unchanged (1800s for org detail, 1800s for search)
- Example: `_ckey_v4 = _ck('org', ein, 'v4', 1)`

### 8. Testing Checklist

Before deploy:
- [ ] GET /api/orgs returns v4 fields (if ENABLE_V4=true)
- [ ] GET /api/orgs/<EIN> includes financial_health
- [ ] POST /api/search results include operating_model
- [ ] v4 fields null/absent if ENABLE_V4=false
- [ ] Search still works if v4_scores lookup slow (timeout handling)
- [ ] Load test: 100 req/s with v4 joins (measure latency impact)

## Implementation Steps

1. **Phase A — Code Changes (30 min)**
   - Add ENABLE_V4 env vars
   - Add _attach_v4_scores() helper
   - Update list_organizations() SQL
   - Update get_organization() SQL
   - Update fused_search() SQL

2. **Phase B — Testing (20 min)**
   - Restart API locally
   - Verify /api/orgs returns v4 fields
   - Verify search latency still <200ms
   - Test with ENABLE_V4=false

3. **Phase C — Deployment (10 min)**
   - Deploy to production
   - Monitor response times
   - Verify metrics flowing to Plausible

## Rollback Plan

If v4 integration causes issues:
1. Set `ENABLE_V4_SCORES=false` in .env
2. Restart API
3. v4 fields will not be returned, v3 scores still work
4. Investigate root cause, fix, re-test, deploy

## Risk Level

**LOW**: v4 is in separate table, v3 untouched, can be disabled at runtime.

---

*Ready for implementation. Expect <5% latency impact due to LEFT JOIN.*
