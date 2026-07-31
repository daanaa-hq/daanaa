# ACTIVE INITIATIVES — Master Project Registry
**Last Updated:** 2026-07-31  
**Master Document:** One source of truth for all projects, owners, timelines, and status

---

## PHASES & PRIORITIES

### Phase 1: Credibility Enhancements ✅ COMPLETE
**Timeline:** 2026-07-20 → 2026-07-31  
**Owner:** Claude Code (Engineering) + Board  
**Status:** COMPLETE, MERGED, APPROVED 9-0

| Item | Status | Merged |
|------|--------|--------|
| 6 Credibility Signals | ✅ Complete | 2026-07-27 |
| Postcard Prep Pipeline (200K orgs) | ✅ Complete | 2026-07-27 |
| Validation Framework | ✅ Complete | 2026-07-27 |
| API Endpoint | ✅ Complete | 2026-07-27 |
| Tests (19 unit tests) | ✅ All passing | 2026-07-27 |
| IRS Revocation Daily Sync | ✅ Complete | 2026-07-21 |
| Board Governance Audit (21/21) | ✅ Complete | 2026-07-31 |
| UX/SEO Strategy | ✅ Approved 9-0 | 2026-07-31 |
| Visibility Initiatives | ✅ Shipped | Various |
| Board Simulation (9-0 unanimous) | ✅ Complete | 2026-07-31 |

**Next Action:** Push to staging/production (pending founder approval)

---

### Phase 2: Tier 0/1/2 Compliance & Legal Gating ⏸️ BLOCKED
**Timeline:** 2026-08-01 → TBD (attorney review blocking)  
**Owner:** Founder (legal) + Engineering  
**Status:** BLOCKED (IRS §170(f)(8) attorney review)

| Item | Status | Blocker | Owner |
|------|--------|---------|-------|
| Attorney engagement | ⏸️ BLOCKED | Needs your decision | Founder |
| IRS compliance review | ⏸️ BLOCKED | Waiting attorney | Founder |
| Phase 2 feature set | 📋 Documented | Waiting legal approval | Engineering |
| Donation letters | ⏸️ BLOCKED | Legal approval | Founder |

**Next Action:** Decide on attorney engagement scope + timeline

---

### Phase 3: IRS Eligibility + Design System ⏸️ PAUSED
**Timeline:** Started 2026-07-25, paused 2026-07-28  
**Owner:** Engineering  
**Status:** PAUSED pending investigation closure

| Item | Status | Notes |
|------|--------|-------|
| IRS Eligibility Columns | ✅ Code complete | 4 columns (verified/unverified/revoked/unknown) |
| Precompute rebuild | ✅ Code complete | 1.75M nested JSON files |
| Design system enhancements | ✅ Shipped | Card variants, IRS badges, serif typography |
| Volunteer interest capture | ✅ Shipped | Button → modal → API logging |
| Route audit (64 routes) | ✅ Complete | 0 broken links |
| Deployment incident (2026-07-28) | 🔴 INVESTIGATION | QA findings; needs closure |
| Staging activation | 🔄 Pending | Waiting investigation closure |

**Next Action:** Close investigation → resume staging deployment → schedule go-live

---

### Phase 4: Hidden Gems & Fairness 🔄 OPERATIONAL
**Timeline:** Started 2026-06-09, ongoing  
**Owner:** Engineering  
**Status:** LIVE + WEEKLY ROTATION

| Item | Status | Notes |
|------|--------|-------|
| Hidden gems discovery | ✅ LIVE | 33.9K small orgs searchable |
| Weekly rotation | ⏳ TODO | Cron not installed (needs sudo) |
| Fairness dashboard | ✅ LIVE | Small org equity audit |
| Peer context visibility | ✅ LIVE | Fair benchmarking shown |

**Next Action:** Install hidden gems weekly cron (5-min, needs your sudo)

---

### Phase 5: Enrichment Pipeline 🔄 OPERATIONAL
**Timeline:** Ongoing (started 2026-06-01)  
**Owner:** Engineering (autonomous agents)  
**Status:** ACTIVE

| Stream | Status | Output | Owner |
|--------|--------|--------|-------|
| **A: Org Website Discovery** | 🔄 Active | 50K+ websites | Agent (Ownership project) |
| **B: Mission Generation** | 🔄 Active | 286K+ missions | Local inference (Qwen3-30B) |
| **C: QA & Validation** | 🔄 Active | Quality metrics | QA team |
| **D: Donation Link Pipeline** | 🔄 Active | 130K links | Agent + verification |
| **E: Volunteer Hours Enrichment** | 🔄 Active | Impact data | Volunteer integration |
| **F: Leadership Network Mapping** | 🔄 Testing | Affiliate network | Agent 6 (discovery phase) |

**Experimental Discovery Scripts:** 16 scripts now tracked in `scripts/discovery-phase/`

---

### Phase 6: Extended Discovery 🔄 EXPERIMENTAL
**Timeline:** 2026-07-24 → ongoing (6+ new agents)  
**Owner:** Autonomous agents + Engineering  
**Status:** ACTIVE (background agents running)

| Source | Status | Coverage | Owner |
|--------|--------|----------|-------|
| 990-N websites | 🔄 Running | 200K orgs | Agent 19 |
| State AG registries | 🔄 Running | 50 states | Agent (multi-state) |
| Foundation grantee lists | 🔄 Running | ~500 foundations | Agent 14 |
| Government nonprofit registries | 🔄 Running | Federal/state | Agent 13 |
| Charity Navigator data | 🔄 Running | ~1M orgs | Agent (CN scraper) |
| Recently granted 501(c)(3) | 🔄 Running | New orgs | Agent 21 |
| IRS bulk XML/CSV | 🔄 Testing | 2M+ orgs | Agent 22 |

**Output:** Direct to DB (after validation), then precompute refresh

---

## BLOCKED/PAUSED PROJECTS (7 total)

| Project | Status | Blocker | Timeline | Owner |
|---------|--------|---------|----------|-------|
| **Phase 2 Sprint** | 🔴 BLOCKED | IRS §170(f)(8) attorney | 2026-08-01 | Founder (legal) |
| **Phase 3 Deployment** | ⏸️ PAUSED | Investigation (QA findings) | 2026-08-01 | Engineering |
| **Intent Discovery** | 🔴 BLOCKED | Claiming system stability | 2026-08-05 | Engineering |
| **Donation Letters** | 🔴 BLOCKED | Legal approval | TBD | Founder (legal) |
| **Every.org Integration** | 🔴 BLOCKED | Partnership negotiation | TBD | Founder (strategy) |
| **Fiscal Sponsor Research** | 🔴 BLOCKED | Founder decision | TBD | Founder |
| **Nonprofit Data Updates UI** | 🔄 TODO | Frontend not started | 2026-08-07 | Frontend |

---

## INFRASTRUCTURE GAPS (Quick Wins Available)

| Gap | Effort | Impact | Owner | Status |
|-----|--------|--------|-------|--------|
| Hidden gems weekly cron | 5 min | Small org visibility | Engineering | TODO (needs sudo) |
| Uptime monitoring (Kuma) | 2 min | Prod visibility | Engineering | TODO |
| Plausible CE (docker+CF) | 30 min | Analytics pipeline | Engineering | TODO |
| AUTONOMOUS_BUILD_LOG refresh | 15 min | Transparency | Engineering | TODO (stale since Jul 14) |
| COST_LEDGER reconciliation | 30 min | Budget tracking | Founder | TODO (monthly) |

**Total: ~50 minutes to close gaps**

---

## GOVERNANCE & INSTITUTIONAL

| Project | Status | Last Update | Owner |
|---------|--------|-------------|-------|
| **Stewardship Principles (11)** | ✅ Live | 2026-07-13 | Board |
| **Charter Never-Promises (10)** | ✅ Live | 2026-07-31 | Board |
| **Board Decision Framework** | ✅ Active | 2026-07-31 | Board |
| **Chief-of-Staff Infrastructure** | ✅ Merged | 2026-07-31 | Engineering |
| **AI Governance Policy** | ✅ Documented | 2026-07-13 | Founder |
| **Constitutional Framework** | ✅ Documented | 2026-07-12 | Founder |
| **Cost Ledger** | ⚠️ Stale | 2026-07-10 | Founder |
| **Budget State** | ⚠️ Stale | Unknown | Founder |
| **AUTONOMOUS_BUILD_LOG** | ⚠️ Stale | 2026-07-14 | Engineering |

---

## OPERATIONAL METRICS

### Database Coverage
| Type | Count | % Coverage |
|------|-------|-----------|
| Full 990-filers | 2.06M | 83% of all 501(c)(3)s |
| Postcard (990-N) | 0.2M | 8% (Form 990-N only) |
| **Total tracked** | **2.26M** | **91%** |
| Recently granted | +50K/year | Backfill ongoing |
| Revoked (last 24h sync) | ~2K | Real-time |

### Visibility & Discovery
| Metric | Count | Status |
|--------|-------|--------|
| Org pages precomputed | 1.76M | Static, server-precomputed |
| Hidden gems (weekly rotation) | 33.9K | Weekly refresh (cron pending) |
| Donation links verified | 130K | 90%+ confidence |
| Missions generated/curated | 286K | Org-attested + AI-assisted |
| Volunteer events indexed | 2K+ | Integrated, searchable |

### API & Infrastructure
| Component | Status | Performance |
|-----------|--------|-------------|
| API response time | ✅ <200ms | (org pages, signals) |
| Search performance | ✅ <400ms | FTS5 + vector search |
| Droplet availability | ✅ Live | 162.243.97.179 (2GB RAM) |
| Search index freshness | ✅ Daily | Synced nightly 08:15 UTC |
| IRS revocation sync | ✅ Daily | 24h lag target |

---

## DECISION QUEUE (Pending Founder Input)

| Decision | Impact | Timeline | Options |
|----------|--------|----------|---------|
| **1. Attorney engagement** | Unblocks Phase 2 | ASAP | Scope + budget discussion needed |
| **2. Phase 3 deployment** | Staging → prod | 2026-08-01 | Resume after investigation, or pivot? |
| **3. Fiscal sponsor research** | Funding timeline | Aug 2026 | Ready to start? |
| **4. Every.org partnership** | Strategic reach | Q4 2026 | Pursue, defer, or descope? |
| **5. Hidden gems cron** | Weekly rotation | Today | Can you run `sudo crontab -e`? |
| **6. Archive cleanup** | Repo health | Sep 2026 | Keep all versions or migrate to S3? |

---

## DECISION HISTORY (Recent)

| Decision | Date | Outcome | Owner |
|----------|------|---------|-------|
| Phase 1 UX/SEO Strategy | 2026-07-31 | APPROVED 9-0 | Board |
| Postcard nonprofits inclusion | 2026-07-26 | APPROVED | Founder |
| V6 Scoring Deployment | 2026-07-25 | APPROVED | Founder |
| Volunteer interest capture | 2026-07-22 | APPROVED | Founder |
| IRS daily sync (vs 28-day) | 2026-07-21 | APPROVED | Founder |
| Tier visibility filter removal | 2026-07-18 | APPROVED | Founder |

---

## LINKS TO DETAILED DOCS

**Phase 1 (Complete):**
- `docs/PHASE1_EXECUTION_CHECKLIST.md` — Day-by-day execution plan
- `docs/PHASE1_BOARD_SIMULATION_AUDIT.md` — Governance alignment (21/21)
- `docs/PHASE1_UX_STRATEGY_GOVERNANCE_AUDIT.md` — SEO strategy audit
- `docs/BOARD_SIMULATION_MEETING_TRANSCRIPT.md` — 9-0 vote record

**Phase 2 & 3:**
- `docs/PHASE2_SPRINT_TASKS.md` — Legal review blocking
- `docs/PHASE3_DEPLOYMENT_PLAYBOOK.md` — Deployment procedures
- `docs/PHASE3_DEPLOYMENT_INCIDENT_2026_07_28.md` — Investigation

**Enrichment Pipeline:**
- `docs/ENRICHMENT_INFRASTRUCTURE_GUIDE.md` — Architecture + agents
- `scripts/discovery-phase/README.md` — Experimental discovery scripts

**Operational:**
- `docs/HIDDEN_GEMS_WEEKLY_SYNC.md` — Weekly rotation setup (cron pending)
- `docs/WEEKLY_OPERATIONS_PLAYBOOK.md` — Daily/weekly tasks
- `docs/AUTONOMOUS_BUILD_LOG.md` — Build progress (stale, needs update)

---

## EXTERNAL DEPENDENCIES

| Dependency | Status | Impact | Owner |
|------------|--------|--------|-------|
| Attorney engagement | ⏳ Pending | Phase 2 blocker | Founder |
| ProPublica API | ✅ Live | 990 data source | Team (monitoring) |
| IRS API | ✅ Live | Revocation sync | Team (daily cron) |
| Local inference (Qwen3-30B) | ✅ Live | Mission generation | Team (night window) |
| Embedding service (mxbai) | ✅ Live | Semantic search | Team (night window) |
| Droplet SSH access | ✅ Live | Deployment | Team (verified 2026-07-14) |

---

## TEAM & OWNERSHIP

| Role | Owner | Contact | Responsibility |
|------|-------|---------|-----------------|
| **Founder/Tie-breaker** | Akbar Khowaja | @akbar.khowaja@gmail.com | Strategic decisions, legal, funding |
| **AI Engineering Agent** | Claude Code | (claude-haiku-4-5) | Implementation, automation, alignment |
| **Extended Agents** | 22+ autonomous agents | (running in background) | Discovery, enrichment, validation |
| **QA Team** | TBD | — | Testing, quality gates |

---

## METRICS & SUCCESS CRITERIA

### Phase 1 Launch Success (30-day check, est. 2026-08-30)
- [ ] Signals present on 99%+ of org pages
- [ ] >70% of users say signals increase trust
- [ ] Page load <200ms confirmed
- [ ] Search <400ms confirmed
- [ ] Zero governance violations (21/21 principles)
- [ ] Organic traffic rising (tracking 20K-30K/month target)

### Overall Project Health (Current)
- ✅ Code quality: Clean builds, all tests passing
- ✅ Governance: 21/21 principles aligned, board signed off
- ⚠️ Alignment: Discovery scripts now tracked, institutional docs stale
- 🔴 Blocking: 7 items pending founder decisions
- 🔄 In flight: 6 phases active, 22+ autonomous agents

---

**Document Status:** Master registry, updated 2026-07-31  
**Next Review:** 2026-08-07 (weekly)  
**Archive:** Historical registries at `institution/`
