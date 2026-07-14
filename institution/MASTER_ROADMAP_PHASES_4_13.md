# Master Roadmap: Daanaa as Nonprofit Institutional Platform
## Phases 4-13 (Complete Vision)

**Authority:** User autonomous directive (2026-07-14 23:15 CST)  
**Scope:** Transform from discovery directory → comprehensive institutional platform  
**Timeline:** 8-12 weeks concurrent development  
**Hardware:** Home server (GPU) + Droplet (API) + Client (wallet)

---

## Phase Architecture

```
FOUNDATION (Phases 1-4)      NETWORK (Phase 9)            KNOWLEDGE (Phases 5-8, 10-13)
├─ Enrichment (1-3)          ├─ Peer connections         ├─ Trust verification (5)
├─ Voice (4)                 ├─ Mutual aid               ├─ Donor learning (6)
└─ Ready to scale            ├─ Community cohorts        ├─ Institutional memory (7)
                             └─ Stickiness for all       ├─ Marketplace (8)
                                                         ├─ Sector diagnostics (10)
                                                         ├─ Financial coaching (11)
                                                         ├─ Succession planning (12)
                                                         └─ Impact measurement (13)

KEY: Network effects compound all other features. Build peer network first.
```

---

## Phases 4-8: Already Documented

See `PHASE_4_ROADMAP.md` for full specs:
- **Phase 4:** Nonprofit Voice Amplification ✅ LIVE
- **Phase 5:** Trust Signal Verification
- **Phase 6:** Donor Learning System  
- **Phase 7:** Institutional Memory
- **Phase 8:** Nonprofit Services Marketplace

---

## Phase 9: Nonprofit Peer Network (KEYSTONE)

**Objective:** Create defensible network effects. Nonprofits become sticky through peer relationships, not just features.

**Why First:** All other phases compound when peer network is active.

### What Gets Built

#### 1. Peer Discovery & Connections
```
"Find orgs like you"
├─ By cause area
├─ By geography  
├─ By size/budget
├─ By focus (direct service, policy, research, capacity building)
└─ By stage (startup, mature, transitioning)
```

**Data Model:**
```sql
CREATE TABLE nonprofit_peer_groups (
    id INTEGER PRIMARY KEY,
    ein TEXT NOT NULL,
    peer_ein TEXT NOT NULL,
    connection_strength FLOAT (0-1),  -- based on cause, size, region overlap
    created_at TIMESTAMP,
    UNIQUE(ein, peer_ein)
);

CREATE TABLE nonprofit_connections (
    id INTEGER PRIMARY KEY,
    ein_from TEXT,
    ein_to TEXT,
    connection_type TEXT ('peer_mentor', 'collab_partner', 'learning_group', 'user_initiated'),
    initiated_by TEXT,
    status TEXT ('pending', 'accepted', 'active', 'archived'),
    created_at TIMESTAMP
);
```

**API Endpoints:**
- `GET /api/nonprofit/<ein>/peers` — Find similar orgs
- `GET /api/nonprofit/<ein>/network` — Your connections + peer groups
- `POST /api/nonprofit/<ein>/connect/<peer_ein>` — Request connection
- `POST /api/nonprofit/<ein>/connect/<peer_ein>/accept` — Accept connection

#### 2. Resource Sharing Ledger
**What it does:** Track what orgs share (volunteers, equipment, knowledge, space)

```sql
CREATE TABLE nonprofit_resource_shares (
    id INTEGER PRIMARY KEY,
    from_ein TEXT,
    to_ein TEXT,
    resource_type TEXT ('volunteer', 'equipment', 'knowledge', 'space', 'funds'),
    description TEXT,
    value_estimate INTEGER,  -- USD
    impact_note TEXT,
    created_at TIMESTAMP
);
```

**API:**
- `POST /api/nonprofit/<ein>/offer-resource` — "We have a volunteer mentor available"
- `POST /api/nonprofit/<ein>/request-resource` — "We need a tax lawyer"
- `GET /api/nonprofit/<ein>/shares` — All resource shares (incoming + outgoing)

#### 3. "What Worked" Case Studies
**Org-authored playbooks** (peer-curated, not AI)

```sql
CREATE TABLE nonprofit_case_studies (
    id INTEGER PRIMARY KEY,
    ein TEXT,
    title TEXT,
    problem TEXT,  -- "We couldn't find enough volunteers"
    solution TEXT,  -- "Started a peer mentor network"
    results TEXT,  -- "Went from 10 to 50 volunteers"
    lessons TEXT,  -- "What we'd do differently"
    by_title TEXT,  -- "Executive Director"
    by_name TEXT,
    published_at TIMESTAMP,
    peer_feedback JSON,  -- Other orgs commenting
    created_at TIMESTAMP
);
```

**API:**
- `POST /api/nonprofit/<ein>/case-study` — Publish what worked
- `GET /api/nonprofit/case-studies?cause=<cause>&challenge=<challenge>` — Find relevant studies
- `POST /api/nonprofit/case-study/<id>/feedback` — Peer comment

#### 4. Peer Mentoring Circles
**Cohort-based peer learning** (monthly calls)

```sql
CREATE TABLE nonprofit_cohorts (
    id INTEGER PRIMARY KEY,
    cohort_type TEXT ('leadership_transition', 'growth_stage', 'crisis_response', 'cause_focused'),
    cause_area TEXT,
    size_bracket TEXT,  -- 'micro', 'professional', 'established'
    max_members INTEGER DEFAULT 8,
    season TEXT,  -- '2026-Q3', '2026-Q4'
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    facilitator_ein TEXT,
    created_at TIMESTAMP
);

CREATE TABLE nonprofit_cohort_members (
    id INTEGER PRIMARY KEY,
    cohort_id INTEGER,
    ein TEXT,
    contact_name TEXT,
    contact_email TEXT,
    joined_at TIMESTAMP,
    FOREIGN KEY (cohort_id) REFERENCES nonprofit_cohorts(id)
);
```

**API:**
- `GET /api/nonprofit/cohorts` — Find cohorts matching your org
- `POST /api/nonprofit/cohorts/<id>/join` — Join cohort
- `GET /api/nonprofit/<ein>/cohort` — Your cohort + schedule

---

## Phase 10: Sector Health Diagnostics

**Objective:** Answer "How is this cause area doing?" — unique data advantage.

### What Gets Built

#### 1. Cause Area Heat Maps
- Service density (where is cause strong?)
- Coverage gaps (where do we have no orgs?)
- Funding distribution
- Impact per dollar invested

#### 2. Movement Capacity Analysis
- Is sector growing or contracting?
- Where is funding flowing?
- Org creation/closure trends
- Leadership pipeline health

#### 3. Collaboration Signals
- Which orgs work well together?
- Recommend "fund these 3 together" bundles
- Detect service overlap (opportunity for coordination)

#### 4. Sector Research Publications
- "State of [Cause] 2026" annual reports
- Trend analysis (data-backed)
- Movement gaps + opportunities
- Funder strategy guides

---

## Phase 11: Nonprofit Financial Health Coaching

**Objective:** Proactive coaching (prevent crises, build resilience).

### What Gets Built

#### 1. Early Warning System
- Reserve ratio trends
- Revenue volatility detection
- Expense growth vs revenue
- Funder concentration risk

#### 2. Customized Health Guidance
- "You're at 2 months reserves; peers have 6"
- "Your expense growth is unusual for your size"
- "Consider diversifying funding sources"

#### 3. Financial Stress Testing
- "If major funder leaves?"
- "If revenue drops 20%?"
- "Can you survive a crisis?"

#### 4. Actionable Connections
- Link to CFO services (Phase 8 marketplace)
- Peer orgs who solved similar problems
- Financial training resources

---

## Phase 12: Nonprofit Succession Planning Toolkit

**Objective:** Help founders/leaders transition smoothly (small orgs' #1 vulnerability).

### What Gets Built

#### 1. Succession Readiness Assessment
- Leadership pipeline quiz
- Board strength evaluation
- Knowledge transfer status
- Transition risk score

#### 2. Leadership Pipeline Tools
- Document what you know (before you leave)
- Board member profiles + roles
- Succession candidate identification
- Onboarding playbooks

#### 3. Peer Transition Cohorts
- Founder + incoming ED in same group
- Monthly calls through transition
- "What we learned" from past transitions
- Post-transition follow-up

#### 4. Movement Capacity Building
- Identify next-generation leaders
- Training + mentorship connections
- Board development resources

---

## Phase 13: Impact Measurement Infrastructure

**Objective:** Standardize measurement without enforcing one-size-fits-all.

### What Gets Built

#### 1. Cause-Specific Outcome Templates
- Climate: what outcomes matter?
- Homelessness: what should we measure?
- Education: what indicates success?
- By cause area + program type

#### 2. Peer Benchmarking (Not Ranking)
- "You reached 500 people; peers reached 400-800"
- Progress visualization
- Trend analysis
- Learning from peers

#### 3. Donor Impact Tracking
- "Your giving helped reach 200 more people"
- Aggregate impact reporting
- Progress toward goals
- Multi-year trends

#### 4. Research-Grade Data
- Anonymized + aggregated
- Allow researchers to learn
- Publish sector insights
- Advance field knowledge

---

## Development Sequence

```
CONCURRENT (Parallel Development)
├─ Phase 9: Peer Network [THIS WEEK]
├─ Phase 10: Sector Diagnostics [Weeks 2-3]
├─ Phase 11: Financial Coaching [Weeks 2-3]
├─ Phase 12: Succession Planning [Weeks 3-4]
└─ Phase 13: Impact Measurement [Weeks 4-5]

INTEGRATION (After Phase 9 Live)
├─ Connect peer network to all phases
├─ Enable "find peers who solved this" from each feature
├─ Surface case studies + learnings across platform
└─ Iterate on UX based on nonprofit feedback
```

---

## Stewardship Alignment (All Phases)

| Principle | How Ensured |
|-----------|------------|
| **P1: Mission before growth** | All features serve nonprofits, not revenue (marketplace separate) |
| **P2: Privacy first** | Peer network is opt-in; data never shared without consent |
| **P3: Trust signals = real data** | All recommendations source-attributed + transparent |
| **P4: Small orgs fairness** | Network celebrates small/emerging; no size-based advantage |
| **P5: No weaponized transparency** | Failure + learning treated as strength, not shame |
| **P6: Fix mistakes quickly** | Nonprofits flag errors; we correct + publish corrections |
| **P7: Independence protected** | Vendor relationships quarantined (Phase 8); no influence over visibility |
| **P8: Never handle funds** | Giving = hand-off only; no escrow, no payment processing |
| **P9: Decisions explainable** | Every feature documented in this roadmap; rationale recorded |
| **P10: AI tool, not replacement** | Peer wisdom prioritized; AI assists, doesn't decide |
| **P11: No silent weakening** | Charter + principles reviewed quarterly; changes public |

---

## Definition of Done (Every Phase)

✅ Code complete + tests passing  
✅ Smoke tests on production  
✅ Privacy gates (GATE 1-8) all passing  
✅ Stewardship principles cross-checked  
✅ Decisions logged in DECISIONS.md  
✅ Deployed to production (backend autonomous)  
✅ 5+ nonprofits tested (gather feedback before Phase N+1)

---

## Success Metrics (By Phase)

| Phase | Metric | Target |
|-------|--------|--------|
| **9** | Peer connections made | 1,000+ connections in first month |
| **10** | Sector research published | 5+ "State of [Cause]" reports |
| **11** | Orgs using coaching | 500+ orgs accessing tools |
| **12** | Transitions supported | 50+ leadership transitions tracked |
| **13** | Impact data shared | 10,000+ orgs reporting outcomes |

---

## Competitive Moat

**After Phase 9-13, Daanaa becomes:**

1. **Network effects** — The more orgs, the more valuable (can't be replicated)
2. **Trust broker** — Neutral community leader (hard to earn, easy to lose)
3. **Data advantage** — 2M+ orgs + measurement data (unique database)
4. **Sector knowledge** — Publishing research others can't do (thought leadership)
5. **Defensible** — Switching cost becomes social (peer relationships), not just features

---

## Revenue (Phase 8 Separate)

EcoMargins Nonprofit Services:
- Vendor listing fees ($100-500/mo by category)
- Financial coaching premium tiers (optional)
- Research data licensing (anonymized)
- Sector intelligence subscriptions (for foundations)

**Key:** Separate from Daanaa. Zero influence over platform visibility or rankings (P7).

---

## Authority & Approval

**This roadmap is approved for autonomous backend development.**

- Phases 9-13 can be built in parallel
- Every commit must pass GATE 1-8
- Smoke tests required before each deploy
- Nonprofit feedback loop after Phase 9 (iterate before Phases 10-13)
- Decisions logged + rationale documented

**Status:** Ready to build. Starting Phase 9 now.

