# Phase Plan

**The contract between phases. Gates protect quality. Phases progress only when ready.**

---

## Phase 0: Directory + Badges (Months 1–6)

### What we are
A public, read-only IRS-grounded nonprofit directory with deterministic badge scoring and a tip jar for MERIT operations. No nonprofit accounts. No transactions. No claims yet.

### What's live
- meritgiving.org public site
- 1.8M+ EIN profile pages at meritgiving.org/[EIN]
- Search, filter, NTEE browse
- Badge system v1
- Giving wallet preview (client-side, demo only)
- "Follow" / "intent to give" signals (anonymous aggregate)
- Stripe Payment Link tip jar
- Newsletter signup
- Build-in-public blog
- Sector report archive

### What's NOT in Phase 0
- Profile claims by nonprofits
- Login or accounts for nonprofits
- Donor accounts
- Payment processing (donations)
- Direct nonprofit support
- GPO marketplace
- Sponsored content

### Phase 0 gates

**Gate 1 (Week 2): Legal Foundation**
- LLC formation paperwork submitted (parallel track, doesn't block build)
- EIN applied for
- DBA filed (if separate name needed)
- Business bank account opened (or in process)
- Mission lock language drafted for operating agreement
- Attorney + CPA intro calls completed

**Gate 2 (Week 4): Credits & Infrastructure**
- 5 credit applications submitted
- At least 2 approvals received
- All core accounts active: GitHub, Vercel, Cloudflare, Neon, Clerk, Sentry, PostHog, Resend, 1Password
- Local dev environment reproducible
- `.mcp.json` working in Claude Code

**Gate 3 (Week 8): Data Foundation**
- IRS EO BMF fully ingested into Postgres
- ProPublica enrichment running with proper attribution
- 1.8M+ EINs queryable
- DuckDB analytics layer working
- First 100 sample profile pages render
- Badge scoring v1 produces results

**Gate 4 (Week 12): Halfway Mirror**
- 10+ nonprofit operators interviewed
- 10+ donors interviewed
- Honest self-evaluation: PROCEED / ADJUST / PIVOT
- Burnout check
- Budget check vs. plan

**Gate 5 (Week 16): Trust Foundation**
- ToS, Privacy, Tip Disclosure, Data Credits attorney-reviewed
- Security headers, rate limiting, bot protection live
- Backup and restore tested end-to-end
- Vulnerability disclosure policy published
- Status page live
- Mobile experience polished
- Accessibility WCAG 2.1 AA verified

**Gate 6 (Week 20): Pre-Launch Readiness**
- Tech E&O / Cyber policy bound
- Final attorney sign-off on all public legal copy
- CPA sign-off on books setup
- Press kit ready
- Newsletter at 100+ subs
- Advisor circle of 3-5 committed
- Beta feedback from 50+ users

**Gate 7 (Week 24): Public Launch**
- All Gate 6 criteria still hold
- 7-day soft launch with 100 invited users complete
- No P0/P1 issues open
- Smoke tests pass in production
- Launch announcement drafted

---

## Phase 1: Claims + Nonprofit Support (Months 7–18)

### Activation criteria (from Phase 0)
- 500+ newsletter subscribers
- First sector report published and received
- 3+ advisors active
- At least 2 credit programs approved with material runway
- Public launch complete and stable for 60+ days
- No outstanding P0/P1 issues
- Insurance bound
- LLC formation complete

### What we add in Phase 1
- Profile claim flow (multi-layer verification)
- Nonprofit accounts (Clerk-backed)
- Acknowledgment letter automation
- Compliance education (filing reminders, NOT legal advice)
- Profile coaching (opt-in)
- Optional: 501(c)(3) formation parallel to LLC

### Phase 1 gates

**Gate 8 (Month 9): First 100 Claimed Profiles**
- 100 nonprofits verified via 4-layer process
- All claims manually reviewed (training the eventual auto-approver)
- Zero successful fraud claims
- Onboarding completion rate > 80%
- Nonprofit satisfaction surveys collected

**Gate 9 (Month 12): Sustainability Baseline**
- First grant funded OR sustainable tip jar baseline
- 1,000+ newsletter subs
- 5+ advisors active
- First sponsor partnership confirmed
- Monthly burn covered without EcoMargins subsidy

**Gate 10 (Month 15): 501(c)(3) Decision**
- Form 501(c)(3) parallel entity OR continue as LLC
- Decision driven by funder thesis + tax efficiency analysis
- If forming: file Form 1023 (or 1023-EZ if eligible)
- Mission lock preserved in new structure

**Gate 11 (Month 18): Partnership Co-Marketing**
- First partnership co-marketing launch
- Co-published sector report with established sector partner
- Speaking at first major conference

---

## Phase 2: GPO Vendor Ecosystem (Months 19+)

### Activation criteria (from Phase 1)
- 1,000+ claimed profiles, 60%+ active monthly
- Sustainable funding model proven
- Identity verification process bulletproof
- Security audit passed (external)
- At least 5 vendors interested in GPO participation
- 501(c)(3) operational (or LLC + clear path)

### What we add in Phase 2
- GPO vendor marketplace
- Curated mission-aligned vendor offers (payments, office tools, marketing, insurance)
- Vendor-to-nonprofit matching
- Cost-savings tracking ($ saved per nonprofit)
- Quarterly State of the Sector reports
- Public API for civic-tech projects

### Phase 2 gates

**Gate 12: GPO Vendor Pilot**
- 3 vendors active, 20 nonprofits enrolled
- First measurable savings recorded
- Vendor agreement template attorney-reviewed
- Conflict-of-interest policy public

**Gate 13: Meaningful Impact**
- First quarter of $-saved metric > $50K aggregate
- Time saved metric > 100 hours aggregate
- NPS > 50 from active nonprofits

**Gate 14: Sector Recognition**
- Major sector publication cites MERIT as primary source
- Speaking at top 3 nonprofit sector conferences
- Partnership with NTEN, Council on Foundations, or similar

---

## Phase 3: Sector Infrastructure (Year 4+)

### What this looks like
- Treated as default trusted source for verified nonprofit data
- Public API widely used by other civic-tech projects
- Annual "State of the Sector" report becomes industry standard
- Foundation funding sustains operations at scale
- Possibly: spin off 501(c)(3) as standalone, license data infrastructure to civic-tech ecosystem

### Open questions for Phase 3
- Geographic expansion? Other regulated nonprofit jurisdictions?
- Adjacent verticals? (Schools, churches, fiscal sponsorships separately?)
- Open governance model — community board?
- Acquisition or merger considerations?

These are future-Akbar's problems. Today's task is Phase 0.

---

## Phase transition discipline

**Phases are protected by gates. Gates are not aspirational.**

If a gate fails:
1. Document why (honest postmortem)
2. Decide: fix and retry, or extend phase
3. Never skip a gate "in the interest of time"
4. Phase transitions happen at gate completion, not calendar dates

**Why this discipline matters:**
- Phase 0 → 1 transition with broken Phase 0 means launching claim flow on bad foundations
- Phase 1 → 2 transition without solid identity means GPO ecosystem fraud
- Each phase compounds the previous; weak foundations collapse later

**The bias:** prefer extending a phase over rushing to the next.
