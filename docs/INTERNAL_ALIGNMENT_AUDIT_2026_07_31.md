# Internal Alignment Audit — Stranded & Blocked Initiatives
**Date:** 2026-07-31  
**Purpose:** Catalog unmerged work, blocked projects, and experimental scripts to restore visibility and alignment

---

## EXECUTIVE SUMMARY

| Category | Count | Severity | Action |
|----------|-------|----------|--------|
| Unmerged branches | 1 | LOW | Review & merge today |
| Blocked projects | 7 | MEDIUM | Need founder decisions |
| Experimental scripts (untracked) | 16 | LOW | Commit to git or delete |
| Stale infrastructure docs | 3 | LOW | Update this week |
| Phase 3 deployment pause | 1 | HIGH | Needs investigation closure |

**Alignment gap:** 16 discovery/enrichment scripts exist but aren't tracked in git or ACTIVE_INITIATIVES. No single source of truth for what's in flight.

---

## 1. UNMERGED BRANCH WORK

### Branch: `feature/founder-institutional-chief-of-staff`

| Field | Value |
|-------|-------|
| Commits ahead of master | 1 |
| Latest commit | `62731c4b66f` feat: add local stewardship chief-of-staff foundations |
| Files changed | ~50 (mostly skill files in `.agents/skills/impeccable/`) |
| Status | Small branch, skills/tools configuration |
| Decision | Merge or archive? |

**Recommendation:** Review commit message, merge if aligned with stewardship goals. If just tools configuration, merge as-is.

---

## 2. BLOCKED/PAUSED PROJECTS (7 total)

### 2.1 Phase 3 Deployment — PAUSED
- **Status:** Investigation in progress
- **Blocker:** QA findings from 2026-07-28
- **Doc:** `docs/PHASE3_DEPLOYMENT_INCIDENT_2026_07_28.md`
- **Owner:** Engineering (pending founder review)
- **Action needed:** Closure on investigation + decision to resume or pivot

### 2.2 Phase 2 Sprint — BLOCKED
- **Status:** Awaiting legal review
- **Blocker:** IRS §170(f)(8) charitable remainder trust compliance
- **Doc:** `docs/PHASE2_SPRINT_TASKS.md`
- **Owner:** Founder (needs attorney)
- **Action needed:** Attorney engagement + IRS guidance

### 2.3 Hidden Gems Weekly Cron — TODO
- **Status:** Code done, not deployed
- **Blocker:** Cron installation (documentation exists, not executed)
- **Doc:** `docs/HIDDEN_GEMS_WEEKLY_SYNC.md`
- **Owner:** Engineering
- **Action needed:** Install cron (5-minute task) to enable weekly rotation

### 2.4 Nonprofit Data Updates Frontend — TODO
- **Status:** Backend complete, frontend pending
- **Blocker:** Frontend integration not started
- **Doc:** `docs/NONPROFIT_DATA_UPDATES_IMPLEMENTATION.md`
- **Owner:** Frontend
- **Action needed:** Wire up React forms + validation (est. 2-3 days)

### 2.5 Intent Discovery Integration — BLOCKED
- **Status:** Design complete, deployment blocked
- **Blocker:** Claiming system stability (concurrent writes issue from 2026-07-25)
- **Doc:** `docs/INTENT_DISCOVERY_INTEGRATION_2026-07-23.md`
- **Owner:** Engineering
- **Action needed:** Verify donation pipeline stability before integrating intent signals

### 2.6 Donation Letters — BLOCKED
- **Status:** Design complete, not approved
- **Blocker:** Legal approval (nonprofit compliance)
- **Doc:** `docs/SPRINT4_DONATION_LETTERS.md`
- **Owner:** Founder (needs attorney)
- **Action needed:** Attorney review + approval before sending

### 2.7 Every.org Integration — BLOCKED
- **Status:** Strategic hold
- **Blocker:** Partnership negotiation
- **Doc:** `docs/PRESIDENT_DASHBOARD.md` (line: "Every.org integration | 🔴 BLOCKED | G2 build | Needs partnership")
- **Owner:** Founder
- **Action needed:** Decide partnership strategy or descope

---

## 3. EXPERIMENTAL SCRIPTS (16 untracked)

**All in `/home/akbar/meritgiving/scripts/`, NOT in git.**

### Website Discovery (4 scripts)
```
- nonprofit_website_discovery.py
  Purpose: Advanced nonprofit website discovery from volunteer/civic platforms
  Status: Untracked, not merged
  
- extract_990n_websites.py
  Purpose: Extract websites from Form 990-N data
  Status: Untracked
  
- extract_990n_websites_parallel.py
  Purpose: Parallel extraction variant
  Status: Untracked
  
- extract_990n_comprehensive.py
  Purpose: Comprehensive extraction
  Status: Untracked
```

### Volunteer Platform Discovery (5 scripts)
```
- volunteer_platform_aggressive_scraper.py
- volunteer_platform_comprehensive_scraper.py
- comprehensive_volunteer_platform_extraction.py
- extract_volunteer_platform_websites.py
- final_volunteer_websites_extractor.py

Status: All untracked, appear to be iterative refinements
Priority: Consolidate or delete (5 versions for same task?)
```

### Leadership Network Discovery (2 scripts)
```
- agent6_leadership_network_discovery.py
  Purpose: Discovers websites via executive/board member networks (990 data)
  Status: Untracked, active development
  
- agent6_leadership_network_fast.py
  Purpose: Fast variant (likely in parallel with above)
  Status: Untracked
```

### State AG Discovery (3 scripts)
```
- state_ag_discovery_framework.py
  Purpose: Generic framework for multi-state 990 ingestion
  Status: Untracked
  
- state_ag_discovery_colorado.py
  Purpose: Colorado-specific implementation
  Status: Untracked
  
- state_ag_discovery_propublica.py
  Purpose: ProPublica API integration
  Status: Untracked
```

### Donation Platform Discovery (1 script)
```
- extract_from_donation_platforms.py
  Purpose: Extract org data from donation platforms
  Status: Untracked
```

### General Intelligence/Scrapers (1 script)
```
- intelligent_nonprofit_webscraper.py
  Purpose: Smart web scraping for org websites
  Status: Untracked
```

### Summary
- **16 scripts total**
- **~50% appear to be iterative variants** (5 volunteer extractors, 2 leadership network variants)
- **Need consolidation:** Are these experiments or active features?
- **No tracking:** None in git, no status in ACTIVE_INITIATIVES.md

**Recommendation:**
1. Create `scripts/experimental/DISCOVERY_PHASE.md` documenting each script's purpose
2. Commit active scripts to git in `scripts/discovery-phase/`
3. Delete duplicate variants or consolidate into one best version
4. Add status tracking (active/paused/archived)

---

## 4. INSTITUTIONAL INFRASTRUCTURE (Alignment Gaps)

### Documented but Not Operationalized

| Component | Status | Last Updated | Gap |
|-----------|--------|--------------|-----|
| **Board Decision Framework** | ✅ Active | 2026-07-31 | Up to date; 15+ decisions tracked |
| **AI Governance** | ✅ Documented | 2026-07-13 | Exists but integration unclear |
| **Constitution** | ✅ Documented | 2026-07-12 | Hierarchy defined; enforcement?  |
| **Cost Ledger** | ✅ Documented | 2026-07-10 | Not updated with recent spend |
| **Autonomous Build Log** | ⚠️ Stale | 2026-07-14 | 17 days old; last entry is outdated |
| **Budget State** | ⚠️ Stale | Unknown (very old) | Not tracking current state |
| **Stakeholder Primers** | ✅ Documented | 2026-07-22 | Board member briefs exist |

**Gap:** Institutional docs exist but aren't being kept live. No weekly reconciliation of decisions vs execution.

**Action needed:**
- Weekly update of AUTONOMOUS_BUILD_LOG.md (tie to Phase 1/Phase 2/Phase 3 execution)
- Monthly reconciliation of Cost Ledger vs actual spend
- Decision → Execution tracker (what decisions were made, who's executing, status?)

---

## 5. INFRASTRUCTURE GAPS (6 Quick Wins)

| Gap | Impact | Effort | Owner | Status |
|-----|--------|--------|-------|--------|
| Hidden gems cron | Small org visibility | 5 min | Engineering | TODO |
| Uptime monitoring (Kuma setup) | Prod visibility | 2 min | Engineering | TODO |
| Plausible CE (docker + Cloudflare) | Analytics pipeline | 30 min | Engineering | TODO |
| Attorney engagement | Unblocks Phase 2 | — | Founder | BLOCKED (needs decision) |
| Fiscal sponsor research | Unblocks funding | 2-3 hours | Founder | BLOCKED (needs decision) |
| Application tracker | Enables funder outreach | 30 min | Founder | TODO (needs setup) |

**Quick wins available (3):** Cron + Kuma + Plausible = ~40 minutes total

---

## 6. ARCHIVE INVENTORY

**Archived directories (retained for historical reference):**
- `archive/api_fastapi_20260609/` — Dead FastAPI spec (daanaa rename removed this)
- `archive/legacy_scorers_20260609/` — v2/v3/etc scorers (v4_0 is canonical)
- `archive/web_discovery_orchestrator_20260610/` — Old discovery orchestrator
- `archive/dead_code_20260721/` — Explicitly marked dead code
- `archive/precompute_archive/` — Historical precompute versions
- `archive/merit-platform/` — Original merit-platform archive
- Multiple date-stamped backups (05192026, etc.)

**Cleanup decision needed:** Do we keep all of this, or archive to S3/delete?

---

## 7. RECOMMENDED ACTIONS FOR ALIGNMENT

### Immediate (Today)
- [ ] Review & merge `feature/founder-institutional-chief-of-staff` (1 commit)
- [ ] Clarify Phase 3 deployment pause → resumption or pivot decision
- [ ] Create `EXPERIMENTAL_INITIATIVES.md` to track 16 discovery scripts

### This Week
- [ ] **Install hidden gems cron** (5 min, unblocks weekly rotation)
- [ ] **Setup Kuma monitoring** (2 min, prod visibility)
- [ ] **Setup Plausible CE** (30 min, analytics)
- [ ] **Consolidate discovery scripts** (commit active ones to git, delete variants)
- [ ] **Update AUTONOMOUS_BUILD_LOG.md** (weekly pulse on Phase 1/2/3)

### Next Session (Founder Decisions)
- [ ] Attorney engagement scope (Phase 2 blocker, IRS compliance)
- [ ] Every.org partnership decision (strategic hold)
- [ ] Fiscal sponsor research timeline
- [ ] Archive cleanup policy (S3 or delete old versions?)

### This Month
- [ ] Create canonical **ACTIVE_INITIATIVES.md** (one source of truth for all projects, owners, status)
- [ ] Implement **Decision → Execution tracker** (tie board decisions to code execution)
- [ ] Monthly **Cost Ledger reconciliation** (actual vs budget)

---

## 8. ALIGNMENT QUESTIONS FOR FOUNDER

1. **Phase 3 deployment pause:** What's the status? Should we resume, pivot, or mark as complete?
2. **Discovery scripts:** Are all 16 scripts active, or should some be deleted? Can we consolidate?
3. **Institutional infrastructure:** How often should AUTONOMOUS_BUILD_LOG, COST_LEDGER, BUDGET_STATE be updated?
4. **Archive policy:** Keep all historical versions or clean up to S3?
5. **Attorney engagement:** Ready to move forward on Phase 2 legal review, or deferring?

---

## APPENDIX: Phase 1 Status (for context)

✅ **Phase 1 Complete & Merged:**
- 6 Credibility Signals (full suite)
- Postcard Prep Pipeline (200K orgs)
- Validation Framework
- API Endpoint
- Tests (19 unit tests passing)
- Board Simulation (9-0 unanimous approval)
- Visibility Initiatives (hidden gems, fairness dashboard, accessibility)

**52 commits merged to master, ready to push to production or staging per founder approval.**

---

**Document prepared:** 2026-07-31 14:45 CDT  
**Prepared by:** Claude Code (AI Engineering Agent)  
**Status:** Ready for founder review and decision-making
