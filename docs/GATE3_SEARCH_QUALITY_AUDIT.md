# GATE 3: SEARCH QUALITY AUDIT — LIVE EXECUTION

**Status:** IN PROGRESS (Starts Aug 11)  
**Timeline:** 72 hours intensive (Aug 11-14)  
**Priority:** CRITICAL (Google indexing, real users arriving)  
**Authority:** "Option A" — confidence mode  

---

## METHODOLOGY

### Phase 1: Real-World Query Benchmark (24 hours)

**100 Common Nonprofit Searches:**
1. Category searches: "health nonprofit", "climate nonprofits", "education charity"
2. Geography searches: "nonprofits in San Francisco", "nonprofits near me"
3. Specific searches: "American Red Cross", "EIN 364123456"
4. Intent searches: "nonprofits that help homeless", "environmental nonprofits"
5. Typo searches: "Red Croos" (typo tolerance test)

**For each query, measure:**
- Time to first result: <500ms target
- Top-5 precision: >90% (relevant results first)
- Recall: Were all matching orgs found?
- Rank position: Small vs large org visibility equal?
- Website links: Working? (200 status)

**Tools:**
- `curl -w %{time_total}` for latency
- Manual relevance scoring (0-10)
- Automated link checking
- Gender/geography bias detection

---

### Phase 2: Edge Cases & Bias Detection (24 hours)

**Edge cases:**
- Empty results (orgs with no website)
- Duplicate results (FTS5 sync issues)
- Stale data (outdated website links)
- Confidence scoring (does system show uncertainty?)

**Bias detection:**
```
Cohort A: 50 small orgs (<$150K budget)
Cohort B: 50 large orgs (>$1M budget)

For each cohort:
  - Search by name → does it find the org? (recall)
  - Search by EIN → instant match? (exact match quality)
  - Search by category → appears in top 5? (visibility)
  - Search by mission keywords → ranked fairly? (semantic quality)
  
PASS: No significant difference in recall/ranking between cohorts
FAIL: Small orgs systematically ranked lower (P4 violation)
```

---

### Phase 3: Real Google Traffic Simulation (24 hours)

**Simulate live load:**
- 100 concurrent searches (parallel requests)
- Repeated queries (cache effectiveness)
- Mixed query types (realistic distribution)
- Measure degradation under load

**Metrics:**
- p95 latency: <1s (acceptable degradation)
- p99 latency: <3s (hard limit)
- Error rate: <0.1% (search must be reliable)
- Search cache hit rate: >70%

---

## GATE PASS CRITERIA

✅ **PASS if ALL true:**
- Precision >90% (top-5 results relevant)
- Recall >95% (find what we should find)
- Latency p95 <1s (fast enough)
- Bias audit: No systematic small-org disadvantage
- Error rate <0.1% (stable)

❌ **FAIL if ANY true:**
- Precision <85% (wrong results)
- Recall <90% (missing orgs)
- Latency p95 >2s (too slow for public)
- Detected bias against small orgs
- Error rate >0.5% (unreliable)

---

## EXECUTION SCHEDULE

**Saturday Aug 11 (12 hours):**
- [ ] Prepare 100 query benchmark
- [ ] Set up measurement tools
- [ ] Baseline latency measurements

**Sunday Aug 12 (24 hours):**
- [ ] Execute Phase 1: Real-world benchmarks
- [ ] Measure precision, recall, latency
- [ ] Log all results

**Monday Aug 13 (24 hours):**
- [ ] Execute Phase 2: Bias detection
- [ ] Cohort analysis (small vs large orgs)
- [ ] Edge case testing

**Tuesday Aug 14 (16 hours):**
- [ ] Execute Phase 3: Load testing
- [ ] Concurrent query stress test
- [ ] Cache effectiveness measurement

**Wednesday Aug 15 (8 hours):**
- [ ] Analyze all data
- [ ] Determine pass/fail
- [ ] Report findings

---

## DECISION TREE

```
GATE 3 PASSES (Precision >90%, Recall >95%, No Bias)?
  ├─ YES → Proceed to Gate 4 (Website Verification)
  │        Optimize for Google ranking immediately
  │        Scale public traffic with confidence
  │
  └─ NO → Identify failure cause:
           ├─ Precision issue? Fix FTS5 ranking
           ├─ Recall issue? Check index sync
           ├─ Latency issue? Optimize queries
           ├─ Bias issue? Fix peer group bias
           └─ Re-test (24h turnaround)
```

---

## DELIVERABLES (By Aug 15, 5 PM)

**Report: GATE3_SEARCH_QUALITY_RESULTS.md**
- Executive summary (pass/fail)
- Precision scores (by query type)
- Recall scores (by query type)
- Bias audit results
- Latency benchmarks (p50/p95/p99)
- Recommendations (if failing)

**Data: GATE3_BENCHMARK_DATA.json**
- All 100 queries + results
- Manual relevance scores
- Latency measurements
- Cohort analysis results

**Git commit:**
```bash
git commit -m "gate-3: SEARCH QUALITY AUDIT — [PASS|FAIL]

Evidence: 100 queries, precision/recall/bias measured
Results: [Summary of key metrics]
Decision: [Proceed to Gate 4 OR Fix [issue] and re-test]"
```

---

## WHAT IF GATE 3 FAILS?

**Common failure causes:**

**Precision <90%:**
- FTS5 ranking is off (typos rank high, names low)
- Solution: Boost name/EIN match weight, reduce typo boost
- Re-test: 24 hours

**Recall <95%:**
- Missing orgs in index (FTS5 sync issue)
- Solution: Rebuild FTS5 from registry_enriched
- Re-test: 24 hours

**Latency >1s p95:**
- Too many large result sets (search "nonprofit")
- Solution: Add filtering, limit result processing
- Re-test: 12 hours

**Bias detected (small orgs ranked lower):**
- Peer group ranking advantage to large orgs
- Solution: Implement size-blind ranking
- Re-test: 24 hours

**Error rate >0.5%:**
- Crashes or timeouts under load
- Solution: Debug errors in search handler
- Re-test: 12 hours

---

## PARALLEL WITH GATE 0 MONITORING

**While running Gate 3 audit:**
- Emergency fixes deployed Fri 8/15
- Monitor: ImportError/day, uptime, watchdog accuracy
- Gate 0 monitoring continues (independent stream)

**By Aug 15:**
- Gate 0 status: Operational stability confirmed
- Gate 3 status: Search quality determined
- Both gates inform next phase decision

---

## SUCCESS DEFINITION

**Gate 3 Passes:**
- Search quality proven robust
- Small orgs not disadvantaged
- Public traffic can scale safely
- Google ranking confidence high

**Gate 3 Fails:**
- Identified specific issue
- Fix plan clear (12-24h)
- Re-test scheduled
- No ambiguity

**Either way:** By Aug 15, you'll know exactly what search quality looks like and whether it's ready for public scale.

---

**STARTING TOMORROW.** Parallel with emergency fix monitoring and P6 Phase 2 work.

Let's see what real-world search quality actually is.

