# Phase 1: Performance-First Architecture Review

**Goal:** Understand current droplet performance constraints BEFORE adding 167 endpoints  
**Duration:** 2 hours (parallel audit workers)  
**Success Criteria:** We know exactly which endpoints can run native vs. which MUST proxy

---

## Performance Audit: 8 Parallel Workers

### Worker 1: Current Droplet Load Profile
**Task:** Measure real-world performance baseline
```bash
# Check current droplet capacity
- CPU usage (get baseline)
- Memory usage (get baseline)
- Disk I/O (get baseline)
- Response times for core endpoints (/api/search, /api/organizations)
- Cache hit rates (in-process dict)
```

**Output:** `droplet_baseline.json`

### Worker 2: Endpoint Classification by Compute Cost
**Task:** Analyze which endpoints are lightweight vs. expensive
```
LIGHTWEIGHT (< 10ms per req, native OK):
  ✓ /api/search (uses FTS5 index, cached)
  ✓ /api/organizations/<id> (simple lookup, cached)
  ✓ /api/volunteer-events (read-only catalog)
  ✓ /api/stats (precomputed)
  ✓ /api/health (trivial)

MEDIUM (10-100ms, conditional native):
  ? /api/sector-health (aggregation, possible caching)
  ? /api/guides (precomputed, small data)
  ? /api/methodology (static content)

EXPENSIVE (> 100ms, MUST proxy to home):
  ✗ /api/interest (database write + email trigger)
  ✗ /api/claim/* (EIN verification, Firebase auth)
  ✗ /api/volunteer/* (multi-table joins, business logic)
  ✗ /api/portal/* (complex org state)
  ✗ /api/email/* (external service call)
  ✗ /api/admin/* (complex queries)
```

**Output:** `endpoint_compute_cost.json`

### Worker 3: Database Query Performance Analysis
**Task:** Identify slow queries that must proxy
```bash
# For each endpoint in daanaa_api.py:
# - Extract SQL queries
# - Estimate execution time on droplet DB (search.db)
# - Identify n+1 queries or expensive joins
# - Mark as "native OK" or "proxy to home"

Query patterns to watch:
- Joins to v4_scores table (MUST proxy - doesn't exist on droplet)
- Joins to org_embeddings (MUST proxy - doesn't exist on droplet)
- Full-table scans (expensive on droplet)
- Subqueries without indexes (expensive)
```

**Output:** `query_performance.json`

### Worker 4: Caching Strategy Analysis
**Task:** Design cache layers to keep droplet fast
```
Current in-process cache (daanaa_api.py):
  - Per-namespace TTLs
  - No Redis (good - simpler)
  - TTLs: ntee=2h, org=10min, search=5min

Caching opportunities for new endpoints:
  - /api/interest counts: Cache per EIN (1h TTL)
  - /api/claim/my-orgs: Cache per user (5min TTL)
  - /api/volunteer-events: Cache list (10min TTL)
  - /api/portal/events: Cache per org (5min TTL)

Cache invalidation:
  - On write (claim, interest, volunteer hour)
  - On TTL expiry
  - On manual flush (admin action)
```

**Output:** `caching_strategy.json`

### Worker 5: Proxy Latency Analysis
**Task:** Measure home-to-droplet round-trip cost
```bash
# Test proxy latency on current endpoints:
curl -w "%{time_total}" https://daanaa.org/api/events/2

Typical results:
  - Local network (home → droplet): ~50-100ms
  - Cloudflare → droplet: ~150-300ms
  - Expected P95: <500ms

Acceptable proxy candidates:
  ✓ Write operations (interest, claim, volunteer hours)
  ✓ Complex reads (portal dashboards)
  ✓ External service calls (email)

Unacceptable proxy (would be too slow):
  ✗ /api/search (users expect <200ms)
  ✗ /api/organizations (catalog lookup, should be <100ms)
```

**Output:** `proxy_latency.json`

### Worker 6: Droplet Capacity Headroom Analysis
**Task:** Understand how much load droplet can handle before adding endpoints
```
Current droplet spec: 1 vCPU, 2GB RAM, 70GB NVMe
Current traffic: ~1K req/day to /api/search

Adding 167 endpoints will:
  - Increase binary size (~2-3MB more code, OK)
  - Increase RAM (if all in-memory caches hit): ~50-100MB more, OK
  - Increase CPU (if 10% more endpoints get native): ~10% more CPU, OK
  - Increase I/O (if native access to search.db): potential issue if concurrent

Breaking point analysis:
  - Droplet can handle 10-50K req/day before hitting limits
  - Current: ~1K req/day (plenty of headroom)
  - Growing to: ~5K-10K req/day (still fine with optimization)
```

**Output:** `capacity_headroom.json`

### Worker 7: Load Testing Plan
**Task:** Define SLAs and testing strategy before deployment
```
Service Level Objectives (SLOs):
  P50 (median): < 100ms
  P95: < 300ms
  P99: < 500ms
  Error rate: < 0.1%

Load test scenarios:
  1. Baseline (current load): verify no regression
  2. +10x search volume: verify search still fast
  3. +100 concurrent interest signals: verify proxy handles load
  4. +100 concurrent claim attempts: verify auth + proxy stable
  5. Mixed workload (all endpoint types): verify overall stability
```

**Output:** `load_testing_plan.json`

### Worker 8: Monitoring & Alerting Setup
**Task:** Design monitoring to catch performance regressions before production
```
Metrics to track:
  - Droplet CPU (alert if > 70%)
  - Droplet memory (alert if > 80%)
  - Response time P95 (alert if > 300ms)
  - Proxy latency P95 (alert if > 500ms)
  - Error rate (alert if > 0.1%)
  - Cache hit rate (alert if < 80% for cached endpoints)

Logging:
  - Every request: timestamp, endpoint, method, status, duration
  - Every error: full stack trace (no PII)
  - Every cache miss (to optimize TTLs)
  - Every proxy call (to track home-server load)

Dashboards:
  - Real-time health (CPU, memory, error rate)
  - Endpoint performance (latency per route)
  - Cache effectiveness (hit rates by endpoint)
  - Proxy load (calls/sec to home)
```

**Output:** `monitoring_plan.json`

---

## Phase 1 Output: Performance Specification

When all 8 workers complete, we'll have:

```yaml
# performance_spec.yaml
---
droplet_capacity:
  cpu_available: 85% (after new endpoints)
  memory_available: 70% (after new endpoints)
  disk_available: 95% (after new endpoints)
  headroom_safe: true
  can_handle_10x_growth: true

native_endpoints:
  count: ~30-40 (lightweight reads, cached)
  examples: [/api/search, /api/organizations, /api/stats]
  expected_latency_p95: < 100ms
  can_handle: 10K req/day per endpoint

proxy_endpoints:
  count: ~120-130 (writes, complex logic, external calls)
  examples: [/api/interest, /api/claim, /api/email, /api/volunteer]
  expected_latency_p95: < 300ms (local) / < 500ms (through Cloudflare)
  can_handle: 1K req/day per endpoint (good for pilot)

caching_strategy:
  in_process_cache: Keep (no Redis needed)
  new_cache_layers: 15+ (per endpoint)
  expected_hit_rate: 85%+
  memory_cost: +50MB (acceptable)

monitoring:
  dashboards: 4 (health, endpoints, cache, proxy)
  alerts: 8 (CPU, memory, latency, errors, cache, proxy)
  logging: Comprehensive, privacy-compliant
  
sla_confidence:
  P50: < 100ms (confident)
  P95: < 300ms (confident)
  P99: < 500ms (confident)
  Error rate: < 0.1% (confident)

deployment_risk: LOW
  - Droplet has headroom
  - No new hardware needed
  - Caching prevents slowdowns
  - Proxy pattern offloads heavy ops
  - Monitoring catches regressions early
```

---

## Decision Points After Phase 1

**IF everything checks out:**
→ Proceed immediately to Phase 2 (Code Organization)

**IF droplet is too tight:**
→ Option A: Reduce native endpoints (proxy more)
→ Option B: Upgrade droplet ($32-64/mo) and continue
→ Option C: Split workload (search on droplet, everything else on home)

**IF monitoring reveals blind spots:**
→ Add more instrumentation before proceeding

---

## Timeline

```
Phase 1a: Launch 8 parallel workers          (5 min)
Phase 1b: Wait for completion                (90 min)
Phase 1c: Analyze results + make decision    (25 min)
────────────────────────────────────────
Total: 2 hours

If decision = GO: Start Phase 2 immediately
If decision = ADJUST: Modify plan, re-run specific workers (30 min)
```

---

## What We're Protecting Against

✅ **Latency regression** - Monitoring catches if endpoints slow down  
✅ **Out-of-memory** - Capacity analysis shows we have room  
✅ **Cache thrashing** - TTL strategy prevents cascading misses  
✅ **Proxy overload** - Load test verifies home-server can handle scale  
✅ **Silent failures** - Logging captures every error  
✅ **Untraced regressions** - Dashboards show before/after metrics  

---

## Ready to Launch Phase 1?

This gives us:
- ✅ Confidence that platform won't slow down
- ✅ Clear data for every deployment decision
- ✅ Monitoring in place from day 1
- ✅ SLAs we can defend to users

**Proceeding with Phase 1 parallel audit in 5 minutes...**

