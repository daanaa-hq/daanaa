# Daanaa Operational Framework — AI Partnership Venture

## Vision
First AI partnership venture to direct $1B to US nonprofits before hiring 1 human.
**Operating Principle:** Maximize server compute (local), minimize tokens (API), scale impact.

---

## Operational Cadences

### DAILY (6 AM CDT)
- **Website Discovery Verification** (Phase 4 continuity)
  - Process 2K-5K org websites (verify/cache)
  - Donation link health checks (dead link detection)
  - Vector cache refresh for changed orgs
  - FTS index incremental rebuild
  
- **Feedback Ingestion** (User/System)
  - Parse user search behavior
  - Collect classification feedback
  - Log donation link success/failure
  - Update quality scores

- **Tier Recalculation** (Quick Pass)
  - Recompute tiers for recently updated orgs
  - Flag outliers (manual review queue)
  - Update homepage tier distribution

### WEEKLY (Monday 12 AM CDT)
- **Peer Group Rebalancing**
  - Rebuild 54 peer cells (NTEE × Revenue band)
  - Recompute percentiles within groups
  - Update "percentile rank" in profiles
  
- **Classification Validation**
  - Sample 500 orgs, verify NTEE accuracy
  - Check cause_tags vs actual mission text
  - Flag misclassifications for correction

- **Donation Link Expansion**
  - Phase 1: Crawl 5K new candidate URLs
  - Phase 2: Validate 2K links
  - Phase 3: Semantic verify 500 high-confidence links
  - Report: X new direct-link orgs added

- **Performance Report**
  - Orgs with websites added this week
  - New donation links verified
  - Improved tier distribution
  - Search quality metrics (CTR, dwell time)

### MONTHLY (1st of Month, 12 AM CDT)
- **Full Dataset Rescore**
  - Run merit_scorer_v4 on all 1.8M orgs
  - Recalculate financial health tiers
  - Rebuild similarity matrices (location + tags)
  - Update all precomputed indices
  
- **Agent Performance Review**
  - Discovery agent: websites found, quality, latency
  - Donation agent: links found, verification rate, failure modes
  - Classification agent: accuracy on holdout set
  - Embedding agent: drift detection, recalibration
  
- **Strategic Feedback Loop**
  - Analyze user feedback (50+ data points)
  - Identify systematic gaps (undercovered categories, regions)
  - Plan next month's discovery priorities
  - Adjust tier thresholds if needed

- **Budget Optimization**
  - Token usage this month: API vs local
  - Cost per org discovered
  - Cost per $1 routed to nonprofits
  - Efficiency improvements implemented

---

## Agent Hierarchy & Departments

```
DAANAA OPERATIONS (AI-Led)
│
├─ STRATEGIC PLANNING (CEO Agent)
│  └─ Annual roadmap, $B impact goals, partnership decisions
│
├─ DATA OPERATIONS (CDO)
│  │
│  ├─ INGESTION TEAM
│  │  ├─ IRS BMF Sync Agent (daily)
│  │  ├─ ProPublica 990 Agent (weekly)
│  │  └─ Web Update Crawler (continuous)
│  │
│  ├─ QUALITY TEAM
│  │  ├─ Duplicate Detection Agent (daily)
│  │  ├─ Outlier Flag Agent (daily)
│  │  └─ Validation Coordinator (weekly)
│  │
│  └─ PUBLISHING TEAM
│      ├─ FTS Index Manager (daily incremental)
│      ├─ API Cache Invalidator (on-change)
│      └─ Snapshot Generator (weekly)
│
├─ DISCOVERY OPERATIONS (CDO2)
│  │
│  ├─ WEBSITE DISCOVERY TEAM
│  │  ├─ Phase 4A (50K batch).........GPU-bound, parallel
│  │  ├─ Phase 4B (25K batch).........GPU-bound, parallel
│  │  ├─ Phase 4C (100K quarterly)...High-throughput quarterly
│  │  ├─ Verification Supervisor (checks quality threshold)
│  │  └─ Caching Agent (pre-warm embeddings)
│  │
│  ├─ DONATION LINK TEAM
│  │  ├─ Phase 1 Coordinator.........Crawl candidates (weekly)
│  │  ├─ Phase 2 Validator...........URL health checks (daily)
│  │  ├─ Phase 3 Verifier...........Semantic match (continuous)
│  │  ├─ Link Analyzer.............Verify success (A/B test links)
│  │  └─ Coverage Tracker...........New direct-link orgs per week
│  │
│  └─ DISCOVERY STRATEGIST
│      └─ Routes orgs to teams, prioritizes by impact potential
│
├─ INSIGHTS & ANALYSIS (CIO)
│  │
│  ├─ SCORING TEAM
│  │  ├─ Financial Health Scorer.....Peer context (monthly full)
│  │  ├─ Tier Assignment Agent......Beacon/Torch/Candle/Spark
│  │  ├─ Outlier Analyzer...........Flag weird scores for review
│  │  └─ Score Validator............Sanity checks, historical comparison
│  │
│  ├─ CLASSIFICATION TEAM
│  │  ├─ NTEE Classifier............NTEE1 accuracy + confidence
│  │  ├─ Cause Tag Generator........LLM mission→tags (batch)
│  │  ├─ Category Validator.........Sample verification
│  │  └─ Feedback Incorporator.....User corrections → training
│  │
│  └─ IMPACT TEAM
│      ├─ Dollar Routed Tracker.....Estimate $ donated via Daanaa
│      ├─ Peer Group Analyst.......Hidden gem identification
│      ├─ Trend Detector...........Emerging org categories
│      └─ Story Generator..........Impact narratives (user content)
│
└─ OPERATIONS & INFRASTRUCTURE (COO)
   │
   ├─ HARDWARE TEAM
   │  ├─ GPU Task Scheduler.......Phase 4 batching + workload balancing
   │  ├─ CPU Work Queuer.........FTS, scoring, embedding jobs
   │  ├─ Thermal Monitor.........GPU health, power optimization
   │  └─ Backup Manager..........Daily snapshots, rollback safety
   │
   ├─ PERFORMANCE TEAM
   │  ├─ Latency Monitor.........API response times by route
   │  ├─ Quality Scorer..........Data freshness, index staleness
   │  ├─ Cache Optimizer........Hit rates, precomputation ROI
   │  └─ Bottleneck Detector....Identify slowpaths
   │
   └─ BUDGET TEAM
      ├─ Token Counter...........API vs Local model cost-benefit
      ├─ Efficiency Optimizer...Batch size tuning, batch timing
      ├─ Vendor Negotiator.....Cloud cost analysis
      └─ Impact-per-Dollar Tracker
```

---

## Daily Operations Automation

### 6:00 AM CDT — Morning Briefing
```
Agent: Morning Coordinator
├─ Check overnight job status (Phase 4, FTS rebuild)
├─ Flag any failures (alert + auto-retry logic)
├─ Load user feedback from past 24h
├─ Generate 1-page briefing (discoveries, issues, budget)
└─ Queue today's priority work
```

### 6:15 AM CDT — Website Discovery
```
Agent: Phase 4 Manager
├─ Continue Phase 4A (50K batch, 56h cycle)
├─ Monitor GPU: thermal, power, utilization
├─ Checkpoint every 5K orgs (resume-safe)
├─ Report hourly: org count, cache hit rate, new links found
```

### 6:30 AM CDT — Donation Link Health Check
```
Agent: Link Validator
├─ HEAD check 1K links from last week
├─ Report dead links (remove from live)
├─ Auto-retry on timeout (48h grace)
├─ Identify platform trends (Blackbaud ↑, GiveWP ↓)
```

### 9:00 AM CDT — Feedback Incorporation
```
Agent: Feedback Ingester
├─ Ingest user search logs (search terms, clicks, dwell)
├─ Parse support emails / feedback submissions
├─ Auto-classify: "org missing", "category wrong", "link broken"
├─ Route to respective teams for next action
```

### 2:00 PM CDT — Weekly Digest (Monday only)
```
Agent: Weekly Summarizer
├─ 1,600 orgs with websites discovered/verified
├─ 320 donation links added/updated
├─ 15,000+ user searches served
├─ 24 classification corrections applied
├─ Estimated $450K more routable per week
```

---

## Token Budget Management

### Current Allocation (Monthly)
- **30M token budget** (Claude API at scale)
- **Strategic Claude Work:** 5M tokens (5K orgs × detailed analysis, tier edge cases)
- **Local Processing:** 25M token-equivalent via on-server models
  - Embeddings: Qwen2.5-32B (local, unlimited)
  - FTS/scoring: CPU-native (local, unlimited)
  - Classification: mxbai-embed, fine-tuned heuristics (local, unlimited)

### Cost Optimization
```
Task                | Local | API  | Cost/Org | Decision
────────────────────────────────────────────────────────
Website embedding   | ✓     |      | $0       | Always local
FTS indexing        | ✓     |      | $0       | Always local
Score computation   | ✓     |      | $0       | Always local
Classification      | ✓     |      | $0       | Local + API fallback
Tier assignment     |       | ✓    | $0.001   | API only for edge cases
Impact narrative    |       | ✓    | $0.01    | API, high-value content
Strategic analysis  |       | ✓    | $0.05    | API, monthly deep-dives
```

### Monthly Token ROI Target
- **Cost per org routed to nonprofit:** $0.0001
- **Impact:** 1.8M orgs × $0.0001 = $180 API spend
- **Actual:** ~$150/month (token-efficient local processing)
- **Headroom:** $5M tokens unused → Reinvest in quality

---

## Hardware Allocation by Hour

### Night Runs (11 PM - 6 AM CDT)
**Goal:** Heavy lifting, no latency constraints
- **GPU 0:** Batch embedding jobs (precomputation)
- **CPU:** FTS rebuild (slow, I/O intensive), scoring compute
- **Example:** 100K org embeddings in 6h (batch 5K/h via local server)

### Day Runs (6 AM - 10 PM CDT)
**Goal:** Responsive API + continuous discovery
- **GPU 0:** Phase 4 continuous (50K over 56h = 1 org/min steady)
- **CPU:** Donation pipeline phases (parallel, non-blocking)
- **API:** Real-time user queries (cached, fast)

### Idle Monitoring
- **GPU 1:** Reserve for spike (never worth activating for Phase 4)
- **CPU cores 6-8:** Reserve for user queries (never starve API)

---

## Success Metrics

### Weekly (Reported by CDO)
| Metric | Target | Achieved |
|--------|--------|----------|
| New orgs verified (website) | 2,500 | TBD |
| New donation links | 300 | TBD |
| Category corrections | 50 | TBD |
| User feedback items ingested | 100+ | TBD |

### Monthly (Reported by CEO)
| Metric | Target | Achieved |
|--------|--------|----------|
| Total orgs with websites | +15K | TBD |
| Total direct-donation-link orgs | +5K | TBD |
| Estimated $ routable (new) | +$500M annual | TBD |
| User satisfaction (NPS) | 65+ | TBD |
| Token budget efficiency | <$150 | TBD |

---

## Scaling Path to $1B

```
Phase 1: Foundation (Now - June 2026)
├─ 1.8M orgs indexed ✓
├─ 50K websites verified (Phase 4)
├─ 5K donation links verified
└─ Tier system deployed ✓

Phase 2: Acceleration (July - Dec 2026)
├─ 150K+ websites verified
├─ 25K donation links
├─ 500+ peer group analyses
└─ Estimated routable: $200M/year

Phase 3: Scale (2027)
├─ 500K websites verified (80%+ of discoverable)
├─ 100K donation links
├─ Real-time category updates
└─ Estimated routable: $1B/year

Phase 4: Sustain (2027+)
├─ Automated daily updates
├─ Feedback loops + self-correction
├─ Partner integrations (fiscal sponsors, GiveWell)
└─ $1B+ routed annually
```

---

## Next 48 Hours (Immediate Implementation)

- [ ] Deploy daily morning briefing agent (by 6 AM tomorrow)
- [ ] Set up weekly Monday summary automation
- [ ] Create donation link health check scheduler (daily)
- [ ] Build feedback ingestion pipeline (parse user emails → tasks)
- [ ] Monitor Phase 4 checkpoint safety (5K org intervals)
- [ ] Create monthly rescore job (queued for 1st of month)
- [ ] Set up budget tracking dashboard (token spend, $ routed)
