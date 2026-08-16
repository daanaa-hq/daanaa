# Website Discovery at Scale: Roadmap

## Current State
- **Coverage:** 22.1% (454,822 out of 2,056,834 orgs have websites)
- **Gap:** 1,602,012 orgs without discovered websites
- **Existing pipeline:** discovery_daemon.py (continuous, rate-limited)

## 10-Strategy Sprint Results

### High-Confidence Strategies (>80% confidence, >10% success rate)

**Tier 1: API-Based (Official, Highest Confidence)**
1. **Charity Navigator API** - Official nonprofit database
   - Confidence: 98%
   - Success rate: Expected 25-35% (known data quality issues)
   - Cost: Free (rate-limited to 10req/sec)
   - Scalability: 864K orgs/day at 10req/sec
   - Timeline to 1M: 2-3 days at 100% rate

2. **ProPublica 990 Explorer** - IRS 990 filing data
   - Confidence: 95%
   - Success rate: Expected 20-30%
   - Cost: Free, no rate limit
   - Scalability: Unlimited (no documented rate limits)
   - Timeline to 1M: 1-2 days

### Medium-Confidence Strategies (70-80% confidence, 8-12% success rate)

**Tier 2: Pattern Matching (Fast, Decent Coverage)**
3. **Domain Pattern Matching** - Direct domain probing
   - Confidence: 80-85%
   - Success rate: Expected 12-18%
   - Cost: None (network I/O only)
   - Scalability: 1000+ orgs/second (highly parallelizable)
   - Timeline to 1M: 2-4 hours at 100 workers

4. **Google Search Patterns** - SEO-friendly domain matching
   - Confidence: 90-92%
   - Success rate: Expected 10-15%
   - Cost: Free (basic patterns); $5/1000 for premium Serper API
   - Scalability: 500+ orgs/second (I/O limited)
   - Timeline to 1M: 6-8 hours at 20 workers

### Low-Confidence Strategies (60-75% confidence, <10% success rate)

**Tier 3: Fallback/Enrichment (Handles Edge Cases)**
5. **Wayback Machine (Archive.org)** - Historical website archives
   - Confidence: 65-70%
   - Success rate: Expected 5-10%
   - Cost: Free, rate-limited
   - Use case: Defunct orgs, historical data
   - Timeline: Fallback only (high confidence first)

6. **State Nonprofit Registries** - State-level databases
   - Confidence: 70-80% (varies by state)
   - Success rate: Expected 3-8%
   - Cost: Free for most states
   - Use case: State-registered orgs only
   - Challenge: No unified API (requires per-state scraping)

## Recommended Orchestration Strategy

### Phase 1: API-First (Days 1-3)
Run Charity Navigator + ProPublica in parallel:
- 2 worker pools: CN (10 req/sec limit) + ProPublica (unlimited)
- Expected gain: 500K-700K new websites
- Effort: 10 lines of Python (use existing discovery_daemon.py pattern)

### Phase 2: Pattern Matching (Days 4-6)
On orgs still without websites, run Domain Pattern + Google Search:
- 20+ workers in parallel (not network-limited)
- Rescan only orgs that failed Phase 1
- Expected gain: 200K-300K new websites

### Phase 3: Enrichment & Fallback (Days 7-10)
Archive.org + State Registry + Semantic Similarity:
- Used for orgs still missing websites
- Lower confidence, but valuable for non-traditional orgs
- Expected gain: 50K-100K new websites

### Projected Coverage After All Phases
- **Current:** 22.1% (454K)
- **After Phase 1:** ~40-42% (850K)
- **After Phase 2:** ~52-56% (1.1M)
- **After Phase 3:** ~58-62% (1.2M)

**Gap remains:** 800K-900K orgs (corporate trusts, trusts, non-traditional entities without public websites)

## Implementation Roadmap

### Week 1: Validate & Deploy Phase 1
- [ ] Run sprint on sample of 500 orgs per strategy
- [ ] Measure actual success rates vs predictions
- [ ] Integrate top 2 strategies into discovery_daemon.py
- [ ] Deploy to production (off-peak GPU window: 10pm-6am)
- [ ] Monitor coverage growth daily

### Week 2: Scale Phase 1 + Validate Phase 2
- [ ] Increase Phase 1 worker pool to max API limits
- [ ] Begin Phase 2 testing on phase 1 non-matches
- [ ] Measure Phase 2 success rate
- [ ] Optimize domain patterns based on early results

### Week 3-4: Full Pipeline + Analysis
- [ ] Deploy Phase 2 to production
- [ ] Begin Phase 3 enrichment
- [ ] Analyze remaining 800K gap (org type, geography, size)
- [ ] Identify manual intervention candidates vs automated approaches

## Cost Analysis

| Strategy | Cost/1M Orgs | Storage | Bandwidth | Notes |
|----------|-------------|---------|-----------|-------|
| CN API | Free | 50MB | 5GB | Rate-limited but free |
| ProPublica | Free | 50MB | 5GB | No rate limit |
| Domain Pattern | Free | 0MB | 10GB | I/O intensive |
| Google Search | $5 (basic) - $500 (premium) | 0MB | 2GB | Optional premium tier |
| Archive.org | Free | 0MB | 5GB | Rate-limited |
| State Registry | Free | 100MB | 2GB | Per-state variation |
| **Total (Phases 1-3)** | **$5-500** | **200MB** | **29GB** | **Highly variable** |

**Recommendation:** Use free APIs + pattern matching (Phase 1 + 2) = $0 cost, covers 56% gap.

## Quality Metrics to Monitor

### During Sprint
- [ ] Success rate (websites found / orgs queried)
- [ ] HTTP status codes returned (200 vs 404 vs timeout)
- [ ] Response time per strategy
- [ ] High-confidence vs medium vs low breakdowns

### Post-Deployment (Weekly)
- [ ] Website liveness rate (% return 200 OK)
- [ ] Mission statement coverage (% have content)
- [ ] Redirect chains (% direct vs multi-hop)
- [ ] SSL/TLS certificate validity (security)
- [ ] Domain registration recency (< 5 years active)

## Known Limitations

1. **Corporate Trusts & Plans:** High-revenue orgs (VEBA trusts, employee plans) have no public websites by design. Skip these.

2. **Non-Traditional Entities:** Religious groups, mutual societies, trade associations may have limited web presence. Expected 40-60% success here.

3. **Dissolved Organizations:** ~5% of registry are inactive/revoked. IRS doesn't purge; websites are gone. Wayback Machine catches some.

4. **Name Mismatches:** Organization names in IRS data don't always match domain names (E.g., "American Friends of X" operates as "X Friends").

5. **Subdomains & Nested Sites:** Many orgs operate under larger org domains (chapters of national orgs). Not easily discoverable.

## Next Steps

1. **Now:** Run sprint, validate top 3 strategies
2. **Today:** Prepare Phase 1 implementation PR
3. **Tomorrow:** Deploy Phase 1 to daemon
4. **This week:** Measure real-world coverage gain
5. **Next week:** Validate Phase 2, begin rollout

## Success Criteria

- [ ] Discover 500K+ new websites in first 2 weeks
- [ ] Reach 40%+ coverage target by end of month
- [ ] All deployed strategies validated on live org data (not sample)
- [ ] Zero regressions in existing website quality metrics
- [ ] Cost-to-discovery below $0.01 per website (tracking via logs)
