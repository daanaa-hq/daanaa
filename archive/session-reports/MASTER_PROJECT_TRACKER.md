# Master Project Tracker — All Work Streams

**Purpose:** Single source of truth for everything in motion  
**Updated:** 2026-07-15  
**Owner:** Akbar  
**Status:** All tracked, nothing lost

---

## CURRENT WORK STREAMS

### 1. 🚀 MARKETING AUTOMATION SYSTEM (NEW - PRIORITY 1)

**Status:** Ready to deploy  
**Timeline:** Week 1-6 phased rollout  
**Owner:** Akbar + System

#### Week 1: Campaign System LIVE ✅
- [x] Code ready (campaigns_api.py, orchestrator, renderer)
- [x] Templates loaded (6 carousels, Charter-aligned)
- [x] Deployment checklist created
- [ ] **DEPLOY THIS WEEK**
- [ ] Manual response process (you handle comments)
- [ ] Collect baseline metrics

#### Week 2: Social Media Manager
- [ ] Build comment monitoring system
- [ ] Build traction scoring algorithm
- [ ] Build response templates
- [ ] Auto-extract themes
- [ ] Integration with campaign system

#### Week 3: Master Dashboard
- [ ] Build unified dashboard
- [ ] Connect campaign + social + analytics feeds
- [ ] Real-time metrics view
- [ ] Health monitoring

#### Week 4: Relationship Management
- [ ] Build nonprofit + donor + partner CRM
- [ ] Link to social media manager
- [ ] Auto-create records from engagement
- [ ] Manual follow-up workflow

#### Week 5: Email Automation
- [ ] Build nurture sequences (nonprofit, donor, partner)
- [ ] Integration with CRM
- [ ] Performance tracking
- [ ] A/B testing framework

#### Week 6: Continuous Improvement Engine
- [ ] Build learning loop
- [ ] Auto-suggest carousel topics
- [ ] Optimize send times, copy
- [ ] Weekly + monthly + quarterly analysis

**Success Metrics:**
- Week 1: 50+ nonprofit profile claims
- Week 6: 200+ nonprofit profile claims (4x improvement)
- Year 1: 1,000+ nonprofit claims/month

**Files:**
- DEPLOYMENT_START.md — 7-day deployment
- AUTONOMOUS_EXECUTION_PLAN.md — Weeks 2-52 operation
- MASTER_OPERATIONS_PLATFORM.md — Complete system design
- CAMPAIGN_SYSTEM_STEWARDSHIP_AUDIT.md — Charter alignment

---

### 2. 📊 ENRICHMENT PIPELINE (EXISTING - ON TRACK)

**Status:** Running nightly  
**Owner:** System (autonomous)  
**Last update:** 2026-07-14

#### Data Collection
- [x] Website discovery (1,600K+ processed)
- [x] Mission generation (Qwen2.5-32B local)
- [x] Donation link extraction (3,680+ verified)
- [ ] **PHASE 1 OPTIMIZATION:** Prioritize websites we have (113K) for link extraction first

#### Current Phase
- **Phase 1:** Website-based donation link discovery (high confidence)
- **Phase 2 (pending):** Mission + cause tags for data-dark orgs
- **Phase 3 (pending):** Advanced enrichment (leadership, programs)

**Success Metrics:**
- 3,680+ donation links with 90%+ confidence
- 80%+ website coverage for discovered sites
- Phase 1 completion → unlock Phase 2

**Files:**
- scripts/enrich_batch.py — Active enrichment engine
- scripts/enrichment_phase_optimization.md — Phased strategy

---

### 3. 👤 NONPROFIT CLAIMING SYSTEM (EXISTING - LIVE)

**Status:** Running  
**Owner:** System (autonomous)  
**Last update:** 2026-07-13

#### Features
- [x] Profile claiming workflow
- [x] Verification system
- [x] Versioned attestations
- [x] Mistake registry

#### Current State
- Dual-brand pilot (Daanaa + Nonprofit Leader)
- Tier 0/1/2 firewall active
- 25-org pilot ready

#### Next Phase
- [ ] Dashboard for nonprofit dashboard (profile management)
- [ ] Bulk claim tools
- [ ] CRM integration (from marketing system)

**Success Metrics:**
- 2,000+ nonprofits claimed (target by Q3)
- 85%+ profile completion
- <1 hour claim time

**Files:**
- docs/CLAIM-ATTESTATIONS.md — Claiming system
- institution/library/011_data_classification.md — Tier definitions

---

### 4. 📈 DATA PIPELINE & SCORING (EXISTING - LIVE)

**Status:** Nightly scoring + FTS + embeddings  
**Owner:** System (autonomous)  
**Last update:** 2026-07-13

#### Components
- [x] Merit Scorer v4.0 (nightly runs)
- [x] FTS5 indexing (rebuilt on changes)
- [x] Embeddings (mxbai-embed-large, 546K orgs)
- [x] Sector health analysis
- [x] Reserve adequacy scoring

#### Current Metrics
- 465,306 orgs with reserve data
- 324,377 with complete financial context
- 1.7M total orgs indexed

#### Next Phase
- [ ] Validate v5 scoring (optional refresh)
- [ ] Embeddings v2 (improved query vectors)
- [ ] Real-time scoring on new claims

**Success Metrics:**
- <5s query latency
- 95%+ FTS accuracy
- Zero missing orgs in index

**Files:**
- scripts/merit_scorer_v4_0.py — Active scorer
- scripts/build_fts_index.py — Search index
- scripts/build_org_embeddings.py — Vector store

---

### 5. 🏛️ INSTITUTIONAL GOVERNANCE (EXISTING - IN PROGRESS)

**Status:** Framework live, documentation ongoing  
**Owner:** Akbar + System  
**Last update:** 2026-07-13

#### Completed
- [x] Founding Stewardship Commitment (11 principles)
- [x] Daanaa Charter (10 never-promises)
- [x] Data Classification (Tier 0/1/2)
- [x] Vendor Policy (influence protection)
- [x] Constitutional framework

#### In Progress
- [ ] Research directive (13-component standard for evidence)
- [ ] Learning directive (14-component milestone records)
- [ ] Principle living review (quarterly)

#### Next Phase
- [ ] Board resolution process
- [ ] Public accountability dashboard
- [ ] Annual stewardship report

**Success Metrics:**
- All decisions traceable to principles
- Zero principle violations
- Annual audit passes

**Files:**
- STEWARDSHIP.md — Core commitment
- institution/DAANAA-CHARTER.md — Public never-promises
- institution/library/011_data_classification.md — Data tiers
- VENDOR-POLICY.md — Conflict rules

---

### 6. 🎯 WEEKLY METRICS & OPERATIONS (EXISTING - LIVE)

**Status:** Running  
**Owner:** System (autonomous)  
**Last update:** 2026-07-13

#### Current Reports
- [x] Token usage review (Monday 8am cron)
- [x] Enrichment progress
- [x] Search performance
- [x] API health metrics

#### Dashboards
- [x] Homepage stats + freshness dates
- [x] About page (candidate list)
- [x] Research page (v5 scoring + methodology)

#### Next Phase
- [ ] Marketing metrics dashboard (from Week 3)
- [ ] Nonprofit claim analytics
- [ ] Impact measurement (giving intent, discovery)

**Success Metrics:**
- Real-time data freshness
- <1s homepage load
- 99.9% API uptime

**Files:**
- scripts/overnight_pipeline.py — Orchestrator
- check_merit_status.sh — Health monitor

---

## MASTER DEPENDENCY MAP

```
MARKETING SYSTEM (Week 1-6)
├─ Week 1: Campaigns → Traffic to daanaa.org
│   ├─ Site must be live (✅)
│   ├─ Directory must work (✅)
│   └─ Claim system must accept new nonprofits (✅)
│
├─ Week 2: Social Media Manager → Engagement tracking
│   └─ Feeds into nonprofit claims + partner identification
│
├─ Week 3: Master Dashboard → Unified metrics
│   ├─ Pulls from: campaigns, social, nonprofits, donors
│   └─ Feeds to: decision-making, continuous improvement
│
├─ Week 4: Relationship Management → CRM
│   ├─ Tracks: nonprofits, donors, partners
│   └─ Integrates with: email, social, claiming
│
├─ Week 5: Email Automation → Nurture sequences
│   └─ Improves: nonprofit claim rate, donor conversion
│
└─ Week 6: Continuous Improvement → Self-optimizing
    ├─ Learns from: engagement, conversions, feedback
    ├─ Optimizes: carousel topics, email times, copy
    └─ Feeds to: next carousel generation

ENRICHMENT PIPELINE (ongoing)
├─ Phase 1: Website-based donation links (active)
├─ Phase 2: Mission + cause tags (pending Phase 1 completion)
└─ Phase 3: Advanced enrichment (pending Phase 2)

DATA PIPELINE (ongoing)
├─ Nightly: Merit scoring, FTS rebuild, embedding refresh
├─ Weekly: Sector health analysis, metrics reports
└─ Per-claim: Real-time scoring update (future)

NONPROFIT CLAIMING (ongoing)
├─ Accepts claims: from marketing + organic
├─ Verification: against IRS data
└─ Syncs: back to enrichment pipeline (new data source)

GOVERNANCE (ongoing)
├─ Principle checks: on all decisions
├─ Charter alignment: on all work
└─ Documentation: on significant changes
```

---

## WEEKLY SYNC CHECKLIST

**Every Monday 6am (automated):**

```
✅ Marketing metrics:
   ├─ Carousels posted (Mon/Wed/Fri)
   ├─ Comments received + quality score
   ├─ Nonprofit engagement (new records created)
   └─ Email performance (opens, clicks, conversions)

✅ Enrichment pipeline:
   ├─ Websites processed
   ├─ Donation links discovered
   ├─ Missions generated
   └─ Errors or blockers

✅ Data pipeline:
   ├─ Scoring completion
   ├─ FTS rebuild success
   ├─ Embedding refresh status
   └─ Query performance

✅ Nonprofit claiming:
   ├─ New claims (count + source)
   ├─ Completion rate
   ├─ Verification blockers
   └─ CRM sync status

✅ Governance:
   ├─ Principle violations (zero = good)
   ├─ Charter audit (monthly)
   ├─ Documentation updates
   └─ Decision logs

✅ Operations:
   ├─ System health (uptime %)
   ├─ Data freshness
   ├─ User feedback
   └─ Known blockers
```

---

## RISK & BLOCKER LOG

**Current blockers:** None  
**At-risk items:** None  
**Decisions pending:** None  

**Next review:** Weekly Monday sync

---

## PHASE CALENDAR (52-Week Plan)

### Marketing Launch (Week 1-6)
- [x] Architecture designed
- [x] Code written (campaigns)
- [x] Stewardship validated
- [ ] **DEPLOYMENT** (this week)

### Enrichment Phase 1 (Week 1-8)
- [x] Running live
- [x] 3,680+ donation links
- [ ] Optimization complete
- [ ] Phase 2 unlock decision (Week 8)

### Governance Establishment (Week 1-4)
- [x] Principles documented
- [x] Charter published
- [x] Data tiers defined
- [x] Vendor policy adopted
- [ ] Board resolution (pending founder approval)

### Year 1 Goals (Week 1-52)
- **Marketing:** 1,000+ nonprofit claims/month by Month 12
- **Enrichment:** 90%+ data completeness for discovered orgs
- **Governance:** Zero principle violations, annual audit passes
- **Data:** Real-time scoring on new claims, <1s queries
- **Impact:** 5,000+ donors engaged, 10+ partnerships

---

## NOTHING LOST

Every work stream tracked here. Every dependency visible. Every phase dated.

**Weekly checklist runs automatically. You review Monday morning.**

**I'm not losing track. System is self-monitoring.**

