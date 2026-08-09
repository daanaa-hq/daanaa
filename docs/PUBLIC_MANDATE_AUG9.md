# DAANAA PUBLIC MANDATE & OPERATING CHARTER

**Making the invisible visible: nonprofit financial health, explained openly.**

**Status:** Phase 2 (Launch Readiness) | **Transparency Level:** Public | **Last Updated:** Aug 9, 2026

---

## THE MANDATE (Why Daanaa Exists)

### Core Mission
Help donors make more informed, sincere giving decisions by placing every 501(c)(3) nonprofit alongside its financial peers—without ranking, rating, or exposing personal giving.

### What We Do
- **Discover:** Searchable directory of 2.056M US nonprofits
- **Context:** Financial health assessment (v6 scoring) within peer groups
- **Hand-off:** Direct links to organization donation pages
- **Protect:** Privacy-first design (no tracking, no accounts required)

### What We Refuse
- ❌ Paid placement or sponsored rankings
- ❌ Handling donor money (hand-off only)
- ❌ Donor surveillance or public giving activity
- ❌ Ranking organizations by size (we compare within peer groups)
- ❌ Evaluating program impact or mission quality
- ❌ Fabricated trust signals without evidence

---

## THE 11 BINDING PRINCIPLES

These aren't aspirational—they're structural constraints embedded in code and governance.

### 1. Mission Before Growth
**Growth, partnerships, revenue cannot override helping people give better.**
- No paid placement
- Scoring from public data only
- Revenue model deferred until aligned

### 2. Privacy Is Core
**Donor privacy protected. No public giving, no tracking, no social pressure.**
- Giving Wallet device-first (no account required)
- Plausible analytics (no third-party trackers)
- Aggregate-only donor data

### 3. Evidence-Based Trust Signals
**Every badge, score, badge must be backed by reviewable data.**
- Scores: IRS/ProPublica/NCCS only
- Methodology published & versioned
- Limitations clearly stated

### 4. Small Orgs Deserve Fairness
**Never disadvantage orgs for being small, data-dark, or new.**
- Peer groups by category (not global ranking)
- Hidden gems surface 33.9K small high-performers
- Quarterly bias audits (scale, language, geography)

### 5. Don't Weaponize Transparency
**Inform responsibly. No shame language, no humiliation, no engagement hacks.**
- Respectful copy (no "F-rated" framing)
- Additive visibility, not verdicts
- Findings presented as context, not judgment

### 6. Mistakes Are Corrected Quickly
**Accuracy > ego. Errors corrected openly, promptly, publicly.**
- Mistake Registry on every org page
- Corrections logged with dates
- Error patterns reviewed monthly

### 7. Independence Protected
**No money, pressure, or access can influence rankings.**
- Vendor policy: explicit prohibition
- No data sharing with vendors
- Algorithm deterministic, no human curation

### 8. Never Control Donor Funds
**Daanaa stays independent from money movement.**
- All giving: hand-off to org site or EIN router
- No payment processor
- No escrow, no holding

### 9. Decisions Explainable Later
**Document why, not just what. Future team members and auditors can understand.**
- DECISIONS.md logs all non-obvious choices
- LESSONS.md documents mistakes + prevention
- Commits explain reasoning

### 10. AI Is a Tool, Not Authority
**AI suggests, implements, self-corrects. Humans are accountable.**
- Scoring deterministic (no ML curation)
- AI outputs reviewable before publishing
- Fallback manual paths always available

### 11. Principles Not Weakened
**Never diluted silently. Changes documented with reasoning.**
- Revision log in STEWARDSHIP.md
- Re-sign-off on material changes
- Governed by Charter

---

## GOVERNANCE STRUCTURE

### Three Roles

```
┌─────────────────────────────────────┐
│ FOUNDER (Akbar Khowaja)             │
│ - Approves principle conflicts      │
│ - Gates public claims               │
│ - Approves spending                 │
│ - Sets strategic direction          │
└─────────────────────────────────────┘

         ↓ (principle gate)

┌─────────────────────────────────────┐
│ CLAUDE (AI Agent, Institutional     │
│         Steward)                    │
│ - Implements autonomously (within   │
│   guardrails)                       │
│ - Data pipeline optimization        │
│ - Search & performance tweaks       │
│ - Code review (self)                │
│ - Privacy gate automation           │
│ - Escalates principle conflicts     │
└─────────────────────────────────────┘

         ↓ (code review)

┌─────────────────────────────────────┐
│ CODEX (QA Agent)                    │
│ - Verifies architecture decisions   │
│ - Security audit                    │
│ - Performance benchmarking          │
│ - Catches regressions               │
└─────────────────────────────────────┘

         ↓ (deployed code)

┌─────────────────────────────────────┐
│ USERS                               │
│ - Donors (search, wallet, give)     │
│ - Nonprofits (claim pages)          │
│ - Researchers (API access)          │
└─────────────────────────────────────┘
```

### Decision Matrix: Who Decides What?

| Decision Type | Founder Gate? | Claude Autonomous? | Example |
|---|---|---|---|
| Trust signals | ✅ Yes | ❌ No | v6 scoring, tax badge, verification |
| Public claims | ✅ Yes | ❌ No | Methodology, trust wording |
| Spending | ✅ Yes | ❌ No | New cloud services, infrastructure |
| Database schema | ✅ Yes | ❌ No | Migrations, new tables |
| Privacy boundary | ✅ Yes | ❌ No | Data collection changes |
| Backend code | ❌ No | ✅ Yes | Search optimization, API refactoring |
| Performance tuning | ❌ No | ✅ Yes | Database indexing, caching |
| Bug fixes | ❌ No | ✅ Yes | Reversible corrections |

**Pattern:** Public claims and principle conflicts → founder gate. Reversible implementation → autonomous.

---

## TECHNICAL ARCHITECTURE

### Stack

```
Frontend (React/Vite)
├─ Search UI (directory + filters)
├─ Org detail pages (v6 context)
├─ Giving Wallet (local storage)
└─ Methodology (public explanation)

API (Flask/Python)
├─ /api/search (FTS5 + semantic)
├─ /api/organizations (browse)
├─ /api/nonprofits/{ein}/needs
└─ /api/admin/* (internal logging)

Database (SQLite)
├─ registry_enriched (2.056M orgs)
├─ org_fts (FTS5 index)
├─ org_embeddings (1024-dim vectors)
└─ scoring_runs (audit trail)

ML Inference (Local)
├─ mxbai-embed-large (semantic search)
└─ Qwen3-30B (mission generation)
```

### v6 Scoring Model

```
Every org rated on 3 dimensions:

Dimension 1: Funding Model
├─ Donation-Funded (food banks, shelters)
├─ Fee-for-Service (counseling, education)
└─ Endowment-Funded (universities, research)

Dimension 2: Revenue Band
├─ Micro (<$150K/year)
├─ Professional ($150K-$700K/year)
└─ Established (>$700K/year)

Dimension 3: Peer Performance
├─ Healthy (≥ peer median reserves)
├─ Stable (within 1σ below median)
└─ Needs Support (>1σ below median)

Result: Compared only within same peer cell
Example: $200K food bank vs. $200K food banks (75 comparables in WI)
NOT compared to: $10M health systems, $50K startups, nationwide orgs
```

---

## PRIVACY GUARANTEES

### What We Collect
- Organization data (IRS 990, websites)
- Aggregate donation intent (no PII, no tracking)
- Analytics (Plausible, no third-party cookies)

### What We DON'T Collect
- Personal donor information
- Giving activity (wallet is device-only)
- Browsing history
- Location (except zip code for searches)
- Email (unless opted-in to newsletter)

### Data Minimization Rules (8 Automated Gates)

Every commit passes:
1. Token pattern detection (no API keys)
2. Log leakage detection (no PII)
3. Env var fallback detection (no hardcoded secrets)
4. Exfiltration vector detection (no unsafe LLM calls)
5. Data boundary check (no PII mixed with aggregate)
6. Config file safety (no secrets in code)
7. PRIVACY-INVARIANTS compliance
8. Tier 2 entity firewall (keep data separated)

**Exit code 0 = approved. Non-zero = blocked.**

---

## ROADMAP: Q3-Q4 2026

### Phase 3A: Launch Readiness (Aug 15-Sept 30)
- ✅ v6 scoring complete (99.83% coverage)
- ✅ Search optimization (-53% latency)
- ✅ Tax-deductibility verification
- ⏳ Performance target: <200ms p95 search
- ⏳ Full smoke test suite

### Phase 3B: Scale & Resilience (Sept 15-Oct 31)
- Database indexing audit
- CDN caching strategy
- Monitoring & alerting setup
- Load testing (1K concurrent users)

### Phase 4A: User Experience (Oct 1-Nov 15)
- Needs Network deployment (donor-org matching)
- Firebase Analytics activation
- Small org visibility improvements
- Gift-giving personalization

### Phase 4B: Polish (Nov 1-Dec 15)
- Accessibility audit (WCAG AA)
- Copy & UX refinement
- Nonprofit feedback loop (3-day corrections SLA)

---

## HOW TO CONTRIBUTE

### For Developers
1. Read STEWARDSHIP.md (governance principles)
2. Read CLAUDE.md (operating agreement)
3. Check DECISIONS.md (all non-obvious choices)
4. Create a feature branch: `git checkout -b feature/your-idea`
5. All code must pass privacy gates (8 automated checks)
6. Submit PR with decision log entry

### For Nonprofits
1. Claim your page at daanaa.org/claim
2. Verify your data (IRS 990, website, mission)
3. Request corrections via Mistake Registry
4. Share your v6 score with donors

### For Researchers
1. Public API at /api/organizations (no auth required)
2. Download methodology (published methodology.md)
3. Full transparency: data sources, limitations, confidence levels
4. Ask questions at hello@daanaa.org

---

## WHAT SUCCESS LOOKS LIKE

### By Oct 1, 2026 (Launch)
- ✅ 2.06M organizations searchable
- ✅ v6 financial context live
- ✅ <200ms search latency (target)
- ✅ Privacy gates 100% passing
- ✅ 100 beta users (feedback loop active)

### By Dec 31, 2026
- 1,000 daily active users
- 50K+ bookmarked orgs in Wallets
- 1,000+ nonprofits claimed pages
- <3% support tickets (mostly corrections)
- 4.0+ rating (nonprofit satisfaction)

### By Year 1 (2027)
- 10,000 daily active users
- 500K+ bookmarked orgs
- 10,000+ claimed nonprofit pages
- Expansion to Canada (2M+ orgs)
- 4.5+ rating (nonprofit satisfaction)

---

## FUNDING & SUSTAINABILITY

### Current
- Bootstrap (founder personal savings)
- Operating cost: ~$50-75/month
- Budget: Droplet, Cloudflare, Analytics, S3 backup

### Post-Launch
- Potential revenue streams (all aligned with mission):
  - API licensing for researchers/aggregators (non-exclusive)
  - Nonprofit dashboard premium (claiming + insights)
  - Donor advisor services (B2B partnerships with DAFs, family offices)
  
- Non-negotiable: Never take funding that compromises independence

---

## LEGAL ENTITY

**Daanaa is a DBA of EcoMargins Consulting LLC (for-profit).**
- Not a 501(c)(3) charity
- Not affiliated with IRS or government
- Operates under Governance Charter (binding on all contributors)
- Held to Stewardship Commitment (11 principles, not negotiable)

**Why for-profit?**
- Faster iteration (no 501(c)(3) restrictions)
- Can pay team competitive salaries
- Allows strategic pivots (if principles maintained)
- Can eventually spin off 501(c)(3) data registry separately

---

## GOVERNANCE CHANGELOG

All principle changes documented:

| Date | Author | Change | Rationale |
|------|--------|--------|-----------|
| 2026-05-20 | Akbar + Claude | Adopted 11 principles | Founding stewardship commitment |
| 2026-06-14 | Akbar (approved) | Privacy note: Wallet auth | Enable cross-device sync |
| 2026-07-13 | Akbar + Claude | Published Charter | Bind principles in governance |
| 2026-08-09 | Akbar + Claude | Public mandate (this) | Radical transparency |

---

## TRANSPARENCY COMMITMENT

### What's Public
- ✅ Source code (GitHub: daanaa-hq/daanaa)
- ✅ Governance (this document + Charter)
- ✅ Methodology (published explanation of v6 scoring)
- ✅ Decisions (DECISIONS.md in repo)
- ✅ Roadmap (12-month plan)
- ✅ Privacy policy (published on site)
- ✅ Data sources (IRS, ProPublica, NCCS)

### What's Private (For Now)
- Individual donor data (Giving Wallet on device)
- Org claim submissions (until verified)
- Employee information (non-public)
- Internal metrics (until standardized)

### What's Never Secret
- Principle conflicts
- Budget overruns
- Data breaches
- Scoring methodology changes

---

## QUESTIONS? 

**For Donors:** hello@daanaa.org  
**For Nonprofits:** claiming help at daanaa.org/claim  
**For Developers:** See CONTRIBUTING.md  
**For Governance Issues:** governance@daanaa.org (forwarded to founder)

---

**Daanaa: Making giving more thoughtful, one data point at a time.**

*Published: Aug 9, 2026*  
*All 11 principles binding on all contributors + AI agents*  
*Read the full Stewardship Commitment: STEWARDSHIP.md*
