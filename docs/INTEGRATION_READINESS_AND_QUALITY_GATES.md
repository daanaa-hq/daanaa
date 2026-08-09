# Integration Readiness & Quality Gates — Preventing Incomplete Utilization

**Problem Statement:** Historically, spike work has not translated to full production utilization. Code is built and validated locally, but either:
1. Not fully integrated into the pipeline (partial deployment)
2. Integrated but not activated (feature flag stays off, data not displayed)
3. Displayed but not used (enriched data fields go unused in API/UI)
4. Silent failures in production (monitoring doesn't catch breakage until manual review)

**This document establishes gates to ensure everything built is end-to-end validated and actually used before calling it "done".**

---

## Integration Readiness Checklist (Before Orchestrator Is Built)

### Level 1: Code-to-Database Integration
**Gate:** Website verifier output exists in database and is queryable.

```bash
# Verify Phase 1 data is present and accessible
SELECT COUNT(*) FROM website_verification_results WHERE verification_status = 'verified';
SELECT COUNT(*) FROM website_verification_results WHERE http_status = 200;
# Expected: >0 in both
```

**Gate:** ProPublica financial data exists in database with multiple years per org.

```bash
SELECT COUNT(DISTINCT EIN) FROM propublica_financial_history;
SELECT AVG(years_per_org) FROM (
  SELECT EIN, COUNT(*) as years_per_org FROM propublica_financial_history GROUP BY EIN
);
# Expected: >100K orgs, average >5 years each
```

**Gate:** LLM-extracted metadata is stored and parseable.

```bash
SELECT COUNT(*) FROM extracted_metadata WHERE founded_year IS NOT NULL;
SELECT COUNT(*) FROM extracted_metadata WHERE confidence >= 0.7;
# Expected: >0 in both
```

### Level 2: API Integration (Droplet)
**Gate:** Website verifier data is served by the API.

```bash
# Query an org that was website-verified
curl -s http://daanaa.org/api/organizations/{verified-ein} | jq '.website_verified_domain'
# Expected: Returns the verified domain, not null
```

**Gate:** ProPublica financial history is available via the API.

```bash
curl -s http://daanaa.org/api/organizations/{ein}/financial-history | jq '.years_available'
# Expected: Returns array of fiscal years [2023, 2022, 2021, ...], not null or []
```

**Gate:** LLM metadata appears in org detail endpoints.

```bash
curl -s http://daanaa.org/api/organizations/{ein} | jq '.extracted_metadata'
# Expected: founded_year, service_area_states, mission_summary all present (where applicable)
```

### Level 3: UI/UX Integration (Frontend)
**Gate:** Website verifier data is displayed on the org detail page.

```
Visual check: Org page shows "Website: [domain]" with verification status badge
Expected: Green checkmark for verified, yellow warning for dead_link, grey for unverified
```

**Gate:** Financial history chart renders on org detail page.

```
Visual check: Org page shows "5-Year Financial Trend" or similar
Expected: Line chart of revenue/expenses from ProPublica data (if available)
```

**Gate:** Metadata is used in search and discovery.

```
Visual check: Org directory filter by "Founded in last 5 years" works
Expected: Search results filter by extracted founded_year from metadata
```

### Level 4: Quality & Monitoring
**Gate:** Error tracking is live and visible.

```bash
# Dashboard query: enrichment_metrics table shows no phase with >5% error rate
SELECT phase, AVG(error_rate) FROM enrichment_metrics GROUP BY phase;
# Expected: All error_rates < 0.05 (5%)
```

**Gate:** Checkpoint/resume actually works in production.

```bash
# Simulate mid-phase failure: kill orchestrator at 50% completion
# Restart orchestrator
# Verify it resumes from checkpoint, not from start
SELECT record_count FROM enrichment_checkpoints WHERE phase = 'website_verify' AND run_date = date('now');
# Expected: count increases, not reset to 0
```

**Gate:** Silent failures are impossible (all errors logged, counted, alerted).

```bash
# Check logs for "except: pass" or bare except blocks
grep -r "except:" scripts/enrichment/ | grep -v "except [A-Za-z]"
# Expected: 0 results
```

---

## Efficiency Gates (Spike → Production Validation)

### Gateway: Throughput Hold-True
**Before scheduling into nightly cron, validate that spike throughput holds at production scale.**

| Module | Spike Measured | Production Gate | Validation Method |
|--------|---|---|---|
| Website Verifier | 13.5K/hour | Must sustain 12K+/hour on 10K sample | Run on 10K orgs, measure timing |
| ProPublica Sync | 42K/hour (rate-limited) | Must sustain 40K+/hour on 10K sample | Run on 10K orgs, measure timing |
| LLM Extraction | 0.06s/page | Must sustain <0.1s/page on 1000 pages | Run on 1K pages, measure latency p95 |

**If any module regresses >10% from spike measurements, INVESTIGATE BEFORE SCHEDULING.**

### Gateway: Cost Validation
**Nightly enrichment has infrastructure costs. Before enabling, log actual resource usage.**

```bash
# GPU hours (Qwen3 on port 11437)
# Expected: <2 GPU-hours per nightly run (machine has 2 GPUs, can run 2x)

# Network bandwidth (ProPublica API, website crawl)
# Expected: <100 MB outbound per nightly run

# Storage growth (new database rows)
# Expected: <500 MB added to merit_registry.db per nightly run
```

**Cost check:** If any exceeds projection by >50%, recalibrate batch size / worker count.

---

## Usage Gates (Data → Product Impact)

### Gateway: Enriched Data Is Actually Used
**Before marking Phase 1 complete, verify that the data we're enriching actually appears in**:

1. **Public API responses** (test 20 random orgs)
   ```bash
   for ein in $(sqlite3 data/merit_registry.db "SELECT EIN FROM registry_enriched WHERE website_verified_domain IS NOT NULL LIMIT 20"); do
     curl -s http://localhost:5000/api/organizations/$ein | jq -e '.website_verified_domain' > /dev/null || echo "MISSING: $ein"
   done
   # Expected: 0 missing
   ```

2. **Search results** (test 10 queries)
   ```bash
   curl -s "http://localhost:5000/api/search?q=founded+1990" | jq '.organizations[0].founded_year'
   # Expected: Field present and used in ranking
   ```

3. **Org detail pages** (visual inspection on 5 orgs)
   - Website verification badge visible?
   - Financial history chart present (if ProPublica data)?
   - Metadata (founded year, service area) displayed?

4. **Donor-facing features** (if applicable)
   - Can users filter by "Founded after 2020"?
   - Can users see "5-year trend" on org pages?
   - Does the wallet show enriched metadata when bookmarking?

**If data exists in DB but not used anywhere → ESCALATE as incomplete integration.**

### Gateway: Monitoring Is Live
**Before marking "done", verify that every enrichment phase has:**

1. ✅ **Real-time metrics dashboard**
   - Throughput (orgs/hour)
   - Error rate (%)
   - Last-run timestamp
   - Next-run ETA

2. ✅ **Alerting configured**
   - Alert if phase takes >2 hours (vs. projected 30 min)
   - Alert if error rate >5%
   - Alert if checkpoint not advancing (stalled)
   - Alert if database not growing

3. ✅ **Rollback capability verified**
   - `.prev` snapshot exists before write phase
   - Rollback script tested on dry-run

---

## Quality Gates (Per-Module Acceptance)

### Website Verifier Module
**Before shipping Phase 1 (nightly scheduler):**

- [ ] **Correctness**
  - [ ] 50-org spike: 100% of verified URLs (status=200) are actually reachable
  - [ ] 50-org spike: redirects (status=301/302) resolve correctly
  - [ ] robots.txt is respected (no "robots_disallowed" errors indicate bugs)

- [ ] **Robustness**
  - [ ] Timeout handling: URLs that timeout are retried once, then marked timeout (not error)
  - [ ] DNS failures logged distinctly from HTTP errors
  - [ ] No thread leaks: run for 2 hours, thread count stays <20

- [ ] **Completeness**
  - [ ] Checkpoint tested: kill at 25%, resume from checkpoint, verify no duplicates
  - [ ] Dry-run produces no database writes
  - [ ] Production run writes all results to website_verification_results table

- [ ] **Integration**
  - [ ] API endpoint /api/organizations/{ein} includes website_verified_domain
  - [ ] Org detail page displays verification status badge
  - [ ] Search can filter by "website_verified" flag

### ProPublica Sync Module
**Before shipping Phase 1.5 (nightly scheduler):**

- [ ] **Correctness**
  - [ ] 500-org sample: 100% of revenue figures match IRS Form 990s (spot-check 10)
  - [ ] Fiscal years are stored correctly (no 2099 or year=0)
  - [ ] Multi-year rows per org are accurate (average >5 years observed)

- [ ] **Robustness**
  - [ ] Rate-limit backoff works: 429 responses trigger 5s pause (not failure)
  - [ ] Network failures are retried with exponential backoff
  - [ ] "Not in ProPublica" (404) responses don't crash the batch

- [ ] **Completeness**
  - [ ] Checkpoint tested: kill at 50%, resume from checkpoint, no duplicates
  - [ ] Dry-run produces no database writes
  - [ ] Production run writes all propublica_financial_history rows

- [ ] **Integration**
  - [ ] API endpoint /api/organizations/{ein}/financial-history returns years
  - [ ] Org detail page displays 5-year financial chart
  - [ ] Financial data actually shows up when available (not null)

### LLM Extraction Module
**Before shipping Phase 2 (orchestrator):**

- [ ] **Correctness**
  - [ ] Smoke test on 10 real pages: extracted revenue within 10% of actual figures
  - [ ] Smoke test on 10 real pages: founded_year matches org website text
  - [ ] Confidence scores are honest (no >0.9 on ambiguous text)

- [ ] **Robustness**
  - [ ] Malformed LLM responses (invalid JSON) don't crash the batch
  - [ ] Inference server timeout (>30s) is handled gracefully (mark as error, not crash)
  - [ ] No hallucination: LLM never invents fields not in the source text

- [ ] **Completeness**
  - [ ] Run on 100 real /financials pages: 100% return structured JSON (success or explicit null)
  - [ ] Dry-run produces no database writes
  - [ ] Production run writes all extracted_metadata rows

- [ ] **Integration**
  - [ ] API includes extracted metadata in org responses
  - [ ] Org detail page displays extracted data with source attribution
  - [ ] Search can filter by founded_year if present

---

## Success Metrics (First 30 Days Post-Deploy)

**Week 1: Operational**
- [ ] All enrichment phases run to completion nightly with 0 manual intervention
- [ ] Checkpoint/resume tested successfully (intentional kill + restart)
- [ ] Error rate <5% across all phases
- [ ] No alerts for stalled phases or missing data

**Week 2: Integration**
- [ ] Website verification data visible on 100% of checked org detail pages
- [ ] ProPublica financial data visible on 78% of orgs (coverage measured in spike)
- [ ] LLM metadata visible where available (founded_year, service area)
- [ ] Search works with new filters (e.g., "founded after 2010")

**Week 3: Impact**
- [ ] User CTR on org cards increases (hypothesis: richer metadata helps discoverability)
- [ ] Wallet bookmarks include verified website (if available)
- [ ] No customer-reported data accuracy issues on newly-enriched fields

**Week 4: Sustainability**
- [ ] Throughput trending (spike measured 2.5h/run; actual avg < 3h)
- [ ] Cost stable (GPU hours, bandwidth, storage all on projection)
- [ ] Rollback not needed (0 production incidents)

**If any metric misses → INVESTIGATE before expanding to Phase 2.**

---

## The Enforcement Pattern

**Do not mark a component "done" until ALL gates pass.**

For each module:
1. **Code review** (check) → Spike testing (measure) → **Integration gate** (verify data in DB + API) → **UI gate** (verify users see it) → **Monitoring gate** (verify we can see it failed) → **Usage gate** (verify it's actually used).

**If any gate fails:**
- Do NOT proceed to the next phase.
- Do NOT schedule nightly (even "just for now").
- Investigate the gap, fix it, re-run the gate.
- Log the issue in LESSONS.md so it doesn't repeat.

This is how we ensure historical "built but not used" gaps don't happen again.

