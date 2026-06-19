# Daanaa — Business Architecture & Infrastructure Roadmap

**Vision:** First billion-dollar nonprofit infrastructure company — the operating system for the nonprofit sector  
**Model:** Three-sided marketplace (Nonprofits + Donors + Supply Partners) with AI agents at every layer  
**Authored:** Jun 18, 2026

---

## The Model (What This Actually Is)

The analogy is Stripe (payment infrastructure), Twilio (communication infrastructure), Shopify (commerce infrastructure). Daanaa is **nonprofit infrastructure** — the connective layer between every party in the charitable ecosystem.

**Revenue flywheel (stewardship-safe):**
- Nonprofits: **free always** (P1, P4 — mission before growth)
- Donors: **free always** (P1 — donor trust is the product)
- Vendors/Supply Partners: **paid** (pay to access verified nonprofit network, cannot influence rankings — P7)
- Employers: **paid** (employee giving programs, matching infrastructure)
- Impact Investors/Foundations: **paid** (aggregated, anonymized sector intelligence)
- API access: **paid** (foundations, researchers, other platforms)

Nonprofits stay free → trust builds → donors come → data improves → vendors pay to reach them → revenue funds product → more nonprofits join. The flywheel works because trust is structural (stewardship model prevents pay-to-play).

---

## Three-Sided Marketplace

```
                    DAANAA INFRASTRUCTURE
    ┌─────────────────────────────────────────────────┐
    │                                                  │
    │   DONORS          ←→         NONPROFITS          │
    │   - Discover                 - Claim profile     │
    │   - Giving wallet            - Receive donors    │
    │   - Track intent             - Verify volunteers │
    │   - Give (hand-off)          - Find vendors      │
    │   - Employer match           - Report outcomes   │
    │                                                  │
    │              ↑           ↑                       │
    │              │           │                       │
    │         SUPPLY PARTNERS / VENDORS                │
    │   - Legal, accounting, tech, marketing           │
    │   - Fundraising platforms                        │
    │   - Volunteer management                         │
    │   - Grant writing, compliance                    │
    │   - Paid access to verified nonprofit network    │
    │                                                  │
    │   AI AGENTS (stewardship-ingrained, always on)   │
    │   - Mission enrichment    - Volunteer matching   │
    │   - Donation verification - Compliance checks    │
    │   - Support triage        - Grant discovery      │
    └─────────────────────────────────────────────────┘
```

---

## Complete System Audit — Built vs. Missing

### Donor Layer
| Feature | Status | File |
|---------|--------|------|
| Search & discovery | ✅ Live | Directory.tsx, /api/search |
| Org detail page | ✅ Live | OrganizationDetail.tsx |
| Financial health context | ✅ Live | v5 scoring, merit_scorer_v4_0.py |
| Giving wallet | ✅ Built | WalletPage.tsx, WalletContext.tsx |
| Giving act (hand-off) | ⚠️ Partial | donate_url exists, no CTA live |
| Giving history | ❌ Missing | wallet tracks intent only |
| Employer matching | ❌ Missing | not built |
| Donor notifications | ❌ Missing | no email system |
| Social/community giving | ❌ Missing | Phase 4+ |

### Nonprofit Layer
| Feature | Status | File |
|---------|--------|------|
| Claim start form | ✅ Live | ForNonprofits.tsx, /api/claim/start |
| PIN verification | ✅ Live | ClaimVerify.tsx, /api/claim/verify |
| Profile editor | ✅ Live | OrgClaimEditor.tsx |
| Post-login portal | ✅ Built (Jun 18) | nonprofit/MyOrgsPage, DashboardPage |
| Volunteer hours verify | ✅ Live | NonprofitVerification.tsx |
| Board matching | ❌ Missing | spec'd, not built |
| Donor communications | ❌ Missing | not built |
| Grant discovery | ❌ Missing | not built |
| 990 reporting tools | ❌ Missing | not built |
| Donor acknowledgment letters | ❌ Missing | P8 — we can generate, hand off |
| Impact reporting | ❌ Missing | not built |
| Analytics dashboard | ❌ Missing | (how many donors viewed them) |

### Vendor / Supply Partner Layer
| Feature | Status | File |
|---------|--------|------|
| Vendor directory page | ✅ Live | ForVendors.tsx |
| Vendor policy | ✅ Live | VENDOR-POLICY.md |
| Vendor portal / dashboard | ❌ Missing | no backend, no auth |
| Nonprofit-vendor matching | ❌ Missing | not built |
| Service catalog | ❌ Missing | not built |
| Vendor billing | ❌ Missing | Stripe Connect needed |
| Referral tracking | ❌ Missing | GuildReferral.tsx exists but no backend |

### AI Agent Layer
| Agent | Status | File |
|-------|--------|------|
| Mission generation | ✅ Live | scripts/generate_missions.py |
| Donation link pipeline | ✅ Live | scripts/donation_link_pipeline.py |
| Web discovery | ✅ Live | scripts/web_finder_agent.py |
| Surge monitor | ✅ Live | scripts/agent_surge_monitor.py |
| Cause tag extraction | ✅ Live | scripts/agents/cause_tags.py |
| Stewardship audit | ✅ Live | scripts/agents/stewardship_audit.py |
| Quality agent | ✅ Live | scripts/agents/quality.py |
| Onboarding agent | ❌ Missing | guide nonprofits through setup |
| Support triage | ❌ Missing | triage support@daanaa.org |
| Volunteer matching | ❌ Missing | match volunteers to orgs |
| Grant research | ❌ Missing | find funding for nonprofits |
| Compliance checker | ❌ Missing | flag 990 anomalies |
| Vendor matching | ❌ Missing | match vendors to nonprofits |

### Infrastructure Layer
| Component | Status | Notes |
|-----------|--------|-------|
| API (Flask) | ✅ Live | 5,966 lines, 105 routes, single file |
| Frontend (React 19) | ✅ Live | Vite, TypeScript, Tailwind |
| Database (SQLite) | ✅ Live | merit_registry.db, 1.87M orgs |
| Search (FTS5 + embeddings) | ✅ Live | org_fts, org_embeddings |
| Auth (Firebase) | ✅ Live | Google OAuth + magic link |
| Physical mail (Lob) | ✅ Live | Claim verification letters |
| Analytics (Plausible) | ⚠️ Partial | deployed but not active |
| Transactional email | ❌ Missing | no notification emails |
| Task queue | ❌ Missing | agents run synchronously or cron |
| Error tracking | ❌ Missing | no Sentry or equivalent |
| API documentation | ❌ Missing | no OpenAPI spec |
| Webhooks | ❌ Missing | no partner integrations |
| Rate limiting | ✅ Live | Flask-Limiter in daanaa_api.py |
| CDN / Cloudflare | ✅ Live | daanaa.org behind Cloudflare |
| Uptime monitoring | ✅ Live | Uptime Kuma in deploy/ |

---

## GitHub Repos — By Layer

### Layer 1: Core Data & Storage

**`supabase/supabase`** — The most important upgrade  
- Replaces: Firebase (auth) + SQLite (DB) with PostgreSQL + row-level security
- Why: Row-level security is critical for multi-tenant (nonprofit owns their data, vendors see only permitted data)
- pgvector extension replaces current numpy embedding approach
- Realtime subscriptions enable live notifications (claim status changed, hours pending)
- Built-in auth replaces Firebase, reducing vendor lock-in
- Timeline: Phase 2 migration (don't block Aug 15 launch)
- Link: https://github.com/supabase/supabase

**`redis/redis`** — Task queue backbone  
- Needed for: async agent pipelines (mission gen, donation links, volunteer matching)
- Current problem: all pipeline scripts run synchronously/cron
- With Celery + Redis: agents run in background, don't block API
- Timeline: Phase 2 (needed before scaling agents)

### Layer 2: Search

**`typesense/typesense`** — Fast, self-hosted search  
- Replaces: FTS5 (SQLite full-text search)
- Why: Sub-10ms search, typo tolerance, faceting (cause tags, location, health signal)
- Simpler than Elasticsearch, more features than FTS5
- Easy to self-host on existing droplet + home server
- 1.87M orgs indexed in under 2 minutes
- Timeline: Phase 2
- Link: https://github.com/typesense/typesense

### Layer 3: AI Agent Orchestration

**Custom StewardshipAgent (built on `anthropics/anthropic-sdk-python`)**  
- DO NOT use LangChain, AutoGen, or CrewAI for core agents — they add complexity and don't natively support stewardship
- Build on existing `BaseAgent` class with stewardship middleware added
- See "Stewardship Agent Architecture" section below
- Link: https://github.com/anthropics/anthropic-sdk-python

**`celery/celery`** — Async task queue for agents  
- Run mission gen, donation discovery, volunteer matching in background
- Workers on home server (Ryzen 9700X + R9700 GPU — already idle at scale)
- Timeline: Phase 2
- Link: https://github.com/celery/celery

### Layer 4: Communication

**`resend/resend-python`** — Transactional email  
- Missing: claim verified emails, volunteer hour confirmations, wallet digest
- Resend is Stripe-quality DX for email
- Integrate at: /api/claim/verify (send confirmation), /api/nonprofit/verify-hours (confirmation), wallet sync
- Timeline: Phase 1 (before Aug 15 — nonprofits need emails)
- Link: https://github.com/resend/resend-python

### Layer 5: Analytics & Monitoring

**`posthog/posthog`** — Product analytics + feature flags  
- Plausible covers page views; PostHog covers product behavior (funnel analysis, feature flags, A/B tests)
- Replace the 1% cohort feature flag system with PostHog feature flags
- Privacy-safe (no PII required)
- Self-hosted on droplet
- Timeline: Phase 2
- Link: https://github.com/PostHog/posthog

**`getsentry/sentry`** — Error tracking  
- Currently: zero error monitoring. A 5,966-line API with no error tracking is flying blind.
- Self-host via `getsentry/self-hosted` or use Sentry.io free tier
- Timeline: Phase 1 (before Aug 15)
- Link: https://github.com/getsentry/sentry

### Layer 6: API & Developer Experience

**`tiangolo/fastapi`** — API migration path  
- Current Flask API (5,966 lines) will hit scaling limits
- FastAPI auto-generates OpenAPI docs, validates request/response with Pydantic
- Migration path: new endpoints in FastAPI, gradual migration from Flask
- Note: FastAPI was previously archived (`archive/api_fastapi_20260609/`). The archived version sorted by revenue (violation of P4). New FastAPI would be clean build.
- Timeline: Phase 3 (don't migrate Aug 15 — too risky)
- Link: https://github.com/tiangolo/fastapi

**`scalar/scalar`** — API documentation  
- Beautiful API docs from OpenAPI spec
- Needed for: vendor integrations, foundation API access, developer ecosystem
- Timeline: Phase 2
- Link: https://github.com/scalar/scalar

### Layer 7: Payments (Vendor Marketplace)

**Stripe Connect** — Vendor billing without holding nonprofit funds  
- P8 principle: Daanaa never holds money
- Stripe Connect: vendors pay Daanaa platform fee, Daanaa never touches charitable funds
- Use for: vendor marketplace subscriptions, API access billing
- Timeline: Phase 3
- Link: https://github.com/stripe/stripe-python

### Layer 8: Nonprofit-Specific Data

**ProPublica Nonprofit Explorer API** — Already using via pipeline  
**IRS BMF** — Already integrated (`data/bmf.csv`)  
**`candid-api`** (Candid/GuideStar) — Premium data on 1.8M nonprofits  
- Contact: technology@candid.org for API access
- Enriches: program descriptions, leadership, financials (990 data)
- Would improve cause tag extraction, mission quality, hidden gem detection
- Timeline: Phase 2

---

## Stewardship Agent Architecture

Every AI agent in Daanaa must be stewardship-ingrained. Not as a filter after-the-fact — as a first-class design constraint.

### StewardshipLayer (upgrade to existing BaseAgent)

```python
# scripts/agents/base.py — upgrade

STEWARDSHIP_GATES = {
    "P1_mission_check": "Does this action serve nonprofit discovery, not growth?",
    "P2_privacy_check": "Does this action expose individual user data?",
    "P3_evidence_check": "Is every output traceable to evidence?",
    "P4_fairness_check": "Does this disadvantage small orgs?",
    "P5_shame_check":    "Does this shame or pressure organizations?",
    "P7_independence_check": "Could this be influenced by a paying partner?",
    "P10_human_gate":    "Is human approval required for this action?",
}

class BaseAgent:
    # Add to existing class:
    
    def stewardship_check(self, action: str, output: any, context: dict) -> list[str]:
        """Returns list of violated principles. Empty = clear."""
        violations = []
        
        # P3: Output must be traceable to evidence
        if action in ("rank_org", "score_org", "badge_org"):
            if not context.get("evidence_source"):
                violations.append("P3: No evidence source for trust signal")
        
        # P4: Small org fairness
        if action == "search_sort" and context.get("sort_by") == "revenue":
            violations.append("P4: Sorting by revenue disadvantages small orgs")
        
        # P7: Independence
        if context.get("paying_partner_ein") and action in ("rank_org", "feature_org"):
            violations.append("P7: Paying partner cannot influence visibility")
        
        return violations
    
    def log_agent_decision(self, action: str, input_hash: str, 
                           output_summary: str, evidence: str,
                           human_approved: bool = False):
        """Every AI decision goes to audit log. P9: explainable decisions."""
        self.db().execute("""
            INSERT INTO agent_decision_log
              (agent, action, input_hash, output_summary, evidence,
               human_approved, principle_checks_passed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (self.name, action, input_hash, output_summary[:500], evidence,
              human_approved, 1, datetime.datetime.utcnow().isoformat()))
        self.db().commit()
    
    def llm_with_stewardship(self, prompt: str, action: str, 
                              evidence_required: bool = True) -> str:
        """LLM call that enforces evidence requirement (P3)."""
        if evidence_required:
            prompt = f"""You are a Daanaa data agent. Your outputs inform how 
501(c)(3) nonprofits are presented to the public. 

REQUIREMENTS:
- Every factual claim must cite IRS data, ProPublica 990 data, or organization's 
  own public website
- Never present assumptions as facts
- Never rank or compare organizations by size or revenue
- If evidence is weak, say so explicitly
- Treat small organizations with equal dignity to large ones

{prompt}

At the end of your response, include:
EVIDENCE: [cite your data sources]
CONFIDENCE: [HIGH/MEDIUM/LOW]"""
        
        result = self.llm(prompt)
        
        # Check for stewardship violations in output
        violations = self.stewardship_check(action, result, {"evidence": result})
        if violations:
            self.log.warning(f"Stewardship check failed: {violations}")
        
        return result
```

### Agent Decision Log Table (add to DB schema)

```sql
CREATE TABLE IF NOT EXISTS agent_decision_log (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    agent                   TEXT NOT NULL,
    action                  TEXT NOT NULL,
    input_hash              TEXT,           -- SHA256 of input (no raw PII)
    output_summary          TEXT,           -- First 500 chars only
    evidence                TEXT,           -- Data source cited
    human_approved          INTEGER DEFAULT 0,
    principle_checks_passed INTEGER DEFAULT 1,
    principle_violations    TEXT,           -- JSON array of violations
    created_at              TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_agent_decisions_agent ON agent_decision_log(agent, created_at);
```

### Human Gate (P10 — consequential actions)

Actions requiring human approval before going live:
- Changing an org's merit score by >10 points
- Adding or removing a verified badge
- Flagging an org's claim for review
- Surfacing an org in "featured" or cause spotlight
- Any agent action affecting >1,000 orgs at once

```python
HUMAN_GATE_ACTIONS = {
    "bulk_score_update",    # affects many orgs
    "badge_grant",          # trust signal (P3)
    "featured_placement",   # visibility (P7)
    "claim_flag",           # org reputation (P5)
}

def execute_with_human_gate(self, action: str, payload: dict) -> bool:
    if action in HUMAN_GATE_ACTIONS:
        # Write to pending_approvals table
        # Send email to Akbar (support@daanaa.org)
        # Block until approved
        self.db().execute("""
            INSERT INTO pending_approvals (agent, action, payload_json, created_at)
            VALUES (?, ?, ?, ?)
        """, (self.name, action, json.dumps(payload), 
               datetime.datetime.utcnow().isoformat()))
        self.log.info(f"Action {action} queued for human approval")
        return False
    return True
```

---

## What "No Open Ends" Means — 20 Gaps to Close

Priority order (1 = blocking, 5 = nice-to-have):

| # | Gap | Priority | Effort | Repo/Tool |
|---|-----|----------|--------|-----------|
| 1 | Transactional email (claim verified, hours confirmed) | P1 | 1 day | resend/resend-python |
| 2 | Sentry error tracking | P1 | 2h | getsentry/sentry |
| 3 | Vendor portal + auth | P1 | 3 days | Custom (Flask/React) |
| 4 | Agent decision audit log | P1 | 1 day | Add to BaseAgent |
| 5 | Stewardship checks in BaseAgent | P1 | 1 day | Upgrade base.py |
| 6 | Async task queue (Celery + Redis) | P2 | 2 days | celery/celery |
| 7 | Plausible analytics activation | P2 | 2h | Already in deploy/ |
| 8 | Onboarding agent (guides nonprofits) | P2 | 3 days | BaseAgent subclass |
| 9 | Support triage agent (support@daanaa.org) | P2 | 2 days | BaseAgent subclass |
| 10 | Donor notifications (wallet digest) | P2 | 2 days | resend |
| 11 | Volunteer matching (skills → org needs) | P3 | 4 days | BaseAgent + Supabase |
| 12 | Board matching | P3 | 4 days | new feature |
| 13 | Grant discovery agent | P3 | 3 days | ProPublica + Candid |
| 14 | Typesense search migration | P3 | 2 days | typesense/typesense |
| 15 | Vendor marketplace (billing, matching) | P3 | 5 days | Stripe Connect |
| 16 | Supabase migration (Firebase + SQLite) | P3 | 1 week | supabase/supabase |
| 17 | API documentation (OpenAPI + Scalar) | P3 | 2 days | scalar/scalar |
| 18 | PostHog product analytics | P4 | 1 day | PostHog |
| 19 | Donor acknowledgment letter gen | P4 | 2 days | Lob + templates |
| 20 | Employer giving infrastructure | P5 | 2 weeks | Custom + Stripe |

---

## Build Priority (Phases)

### Phase 1 (Before Aug 15) — FOUNDATION
**Goal: Everything works, nothing breaks, testers trust it**

1. **Sentry error tracking** (2h) — no more flying blind
2. **Transactional email** (1 day) — nonprofits need claim confirmation
3. **Vendor portal MVP** (3 days) — vendors need a login
4. **Stewardship checks in BaseAgent** (1 day) — principles ingrained before agents scale
5. **Agent decision audit log** (1 day) — P9 explainability
6. **Plausible analytics** (2h) — activate what's already deployed

### Phase 2 (Aug 15–Sep 30) — GROWTH
**Goal: Three-sided marketplace functional**

1. **Celery + Redis** (2 days) — async agents, no API blocking
2. **Onboarding agent** (3 days) — guide nonprofits from claim to active
3. **Support triage agent** (2 days) — scale support without hiring
4. **Volunteer matching** (4 days) — donors can volunteer, nonprofits find talent
5. **Donor wallet notifications** (2 days) — keep donors engaged
6. **Typesense search** (2 days) — better search for users
7. **API documentation** (2 days) — vendor/developer ecosystem starts here
8. **PostHog** (1 day) — product intelligence for decision-making

### Phase 3 (Oct–Dec) — SCALE
**Goal: Marketplace revenue + sector intelligence**

1. **Vendor marketplace** (5 days) — Stripe Connect, service catalog, matching
2. **Board matching** (4 days) — governance layer
3. **Grant discovery agent** (3 days) — help nonprofits find funding
4. **Supabase migration** (1 week) — PostgreSQL for scale
5. **Employer giving infrastructure** (2 weeks) — highest revenue potential
6. **Donor acknowledgment letters** (2 days) — § 170(f)(8) compliance

### Phase 4 (2027) — INFRASTRUCTURE COMPANY
**Goal: Platform others build on**

1. **Public API** (with billing) — foundations + researchers pay per call
2. **Webhook system** — partners integrate with real-time events
3. **Sector intelligence reports** — aggregated, anonymized, sold to impact investors
4. **White-label nonprofit discovery** — Candid, Community Foundations license Daanaa engine
5. **Employer giving API** — corporate benefits platforms integrate
6. **International expansion** — Canada (CRA), UK (Charity Commission) data sources

---

## The Stewardship-Ingrained Tech Stack (Full Vision)

```
USERS
  Donors      → React 19 (Giving Wallet)
  Nonprofits  → React 19 (Portal) + Daanaa API
  Vendors     → React 19 (Vendor Portal) + Daanaa API
  Developers  → Public API (OpenAPI) + Webhooks

FRONTEND
  React 19 + TypeScript + Vite + Tailwind
  Auth: Supabase Auth (replaces Firebase)
  State: React Context (existing) + React Query (add)
  Analytics: PostHog (feature flags + product analytics)

API GATEWAY
  Nginx (existing) → Flask (existing, port 5000)
  → FastAPI (Phase 3 migration, new endpoints)
  → Rate limiting: Flask-Limiter (existing)
  → Error tracking: Sentry

AGENT LAYER (Stewardship-Ingrained)
  BaseAgent (existing, upgraded)
  ├── StewardshipMiddleware (P1-P11 checks)
  ├── AuditLog (agent_decision_log table)
  ├── HumanGate (pending_approvals table + email)
  └── LLMRouter (local Ollama → Claude API)
  
  Agents:
  ├── MissionAgent (existing, upgraded)
  ├── DonationLinkAgent (existing, upgraded)
  ├── WebDiscoveryAgent (existing, upgraded)
  ├── CauseTagAgent (existing, upgraded)
  ├── OnboardingAgent (new)
  ├── SupportTriageAgent (new)
  ├── VolunteerMatchingAgent (new)
  ├── GrantResearchAgent (new)
  └── ComplianceAgent (new)
  
  Orchestration: Celery + Redis (async, distributed)

DATA LAYER
  Primary: merit_registry.db (SQLite → PostgreSQL/Supabase Phase 3)
  Search: FTS5 (existing) → Typesense (Phase 2)
  Vectors: numpy/org_embeddings → pgvector (Phase 3)
  Cache: In-process dict (existing) → Redis (Phase 2)

COMMUNICATIONS
  Physical mail: Lob (existing)
  Transactional email: Resend (add)
  Webhooks: Custom (Phase 2)
  
MONITORING
  Uptime: Uptime Kuma (existing)
  Web analytics: Plausible (activate)
  Product analytics: PostHog (add)
  Errors: Sentry (add)
  Metrics: Grafana + Prometheus (Phase 3)

INFRASTRUCTURE
  Droplet: DigitalOcean (static files + nginx + API proxy)
  Home server: Ryzen 9700X + R9700 (agents + SQLite)
  CDN: Cloudflare (existing)
```

---

## The Billion-Dollar Moat

Not technology. Not data. **Trust + Stewardship.**

1. **Trust from nonprofits:** We never profit from their vulnerability. They stay because we're safe.
2. **Trust from donors:** Privacy structural (P2). They give because we don't exploit.
3. **Independence from vendors:** No pay-to-play (P7). Rankings stay clean. Donors trust results.
4. **AI as a tool:** Stewardship-ingrained agents (P10). Outputs are auditable. No black boxes.
5. **Principles as moat:** Competitors CAN copy the tech. They CANNOT credibly copy 11 principled commitments signed by every contributor.

The billion-dollar thesis: as a infrastructure layer, Daanaa owns the trust stack for the $640 billion nonprofit sector. Every party pays to access the trusted network. The network grows because trust compounds — each new verified nonprofit, each stewardship check, each transparent AI decision makes the whole system more credible.

---

## What to Build Next (This Week)

Based on the audit, these three unlock the most value immediately:

1. **Sentry** — Zero error monitoring on a live production system is unacceptable
2. **Transactional email (Resend)** — Nonprofits who claim get no confirmation email right now
3. **Vendor portal** — ForVendors.tsx has a page but nothing behind it; vendors have no login

Then stewardship into the agents (BaseAgent upgrade) before they scale.

---

**Status:** Architecture complete  
**Next action:** Build the three immediate gaps  
**Document owner:** Claude Code + Akbar Khowaja  
**Date:** Jun 18, 2026
