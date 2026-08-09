# Performance Baseline — Aug 9, 2026

**Purpose:** Establish Phase 2 launch readiness metrics
**Timestamp:** 2026-08-09 15:15:08
**Environment:** Local API (`http://localhost:5000`)

---

## Search Latency (p95 target: <200ms)

```
p50:  1.0ms
p95:  329.99ms ← TARGET
p99:  491.33ms
min:  0.47ms
max:  491.33ms
samples: 50
status: FAIL
```

**Interpretation:**
- **PASS (<200ms):** Search is performant for production
- **FAIL (>200ms):** Need to optimize queries or add caching

---

## Org Detail Page Latency (p95 target: <300ms)

```
p50:  N/Ams
p95:  N/Ams ← TARGET
p99:  N/Ams
min:  N/Ams
max:  N/Ams
samples: 0
status: UNKNOWN
```

**Interpretation:**
- **PASS (<300ms):** Org detail pages render quickly
- **FAIL (>300ms):** Need lazy-load or API optimization

---

## Database Query Performance

```
Trivial query: 0.0ms
Count all orgs: 5.27ms
Fetch 100 orgs: 0.69ms
Filter by NTEE1: 706.86ms

```

---

## Phase 2 Launch Readiness

| Check | Status | Notes |
|-------|--------|-------|
| Search <200ms p95 | ❌ NEEDS WORK | 329.99ms |
| Org detail <300ms p95 | ❌ NEEDS WORK | N/A |
| Database responsive | ✅ PASS | Queries <100ms |
| WCAG AA compliance | ⏳ TODO | Needs manual audit |
| Mobile responsive | ⏳ TODO | Needs manual audit |

---

## Recommendations

### If All Passes ✅
- Phase 2 is performance-ready for Oct 1 launch
- No blocking optimizations needed

### If Search Fails (<200ms)
- Add query caching (Redis or in-process)
- Consider FTS5 index optimization
- Profile slow queries with EXPLAIN PLAN

### If Org Detail Fails (<300ms)
- Implement lazy-load for below-fold sections
- Use API field selectors (return only needed fields)
- Consider HTTP compression

---

## Next Steps

1. Run this audit after each major change
2. Re-check before launch week (Sept 25)
3. Monitor live metrics after deployment (Plausible/Firebase)
4. Alert if p95 degrades >10% from baseline
