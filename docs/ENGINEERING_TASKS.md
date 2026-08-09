# Daanaa Engineering Tasks — Build Only

**Last updated:** Aug 9, 2026  
**Audience:** Engineering team  
**Focus:** Code + product work (no admin, no legal, no marketing)

---

## PHASE 1: AUG 9–31 (Momentum White Paper Edits)

### White Paper Sections
- [ ] **Section 24: Traction Metrics**
  - Add: 2,056,834 orgs indexed, 66K links verified, ~293 MAU, $1.02/user cost
  - Frame: "Pre-free-tier baseline. Real growth Oct 1."
  - Done when: Section reviewed by founder

- [ ] **Section 25: Revenue Model**
  - Options A/B/C/D with decision deferred to Sept 2027
  - Done when: Section reviewed by founder

- [ ] **Positioning subsection** (Section 1)
  - Daanaa vs Charity Navigator vs GiveDirectly vs Idealist
  - Done when: Added to white paper

- [ ] **Executive Summary** (1 page for mentors)
  - Problem, solution, proof, ask
  - Done when: Draft reviewed

---

## PHASE 2: SEPT 1 – OCT 1 (Free Tier Launch Prep)

### Local Smoke Tests (Staging)
- [ ] **Homepage**
  - [ ] Loads (200 status)
  - [ ] Search box works
  - [ ] Done when: Tested locally, screenshot taken

- [ ] **Search**
  - [ ] Query "food bank" returns results
  - [ ] Latency p95 < 200ms
  - [ ] Zero-result rate ~6.5% (OK baseline)
  - [ ] Done when: Latency logged, screenshot taken

- [ ] **Org page** (sample: EIN 934334592)
  - [ ] Loads (200 status)
  - [ ] Donation link clickable
  - [ ] Server-rendered metadata correct (og:title, og:description are org-specific, not generic)
  - [ ] Mobile responsive
  - [ ] WCAG AA compliant
  - [ ] Done when: Tested on device, audit passed

- [ ] **Wallet**
  - [ ] Bookmark save works
  - [ ] Bookmark retrieve works
  - [ ] Volunteer interest capture works (button click → logged)
  - [ ] Done when: All 3 tested

### Bug Fixes (Critical Only)
- [ ] **Triage issues** from known bugs list
  - Rank: 🔴 Critical (breaks core) vs 🟡 Important (UX issue) vs 🟢 Nice-to-have
  - Done when: Issues ranked with owners

- [ ] **Fix critical bugs** (🔴 only)
  - Test each against smoke test
  - Done when: All 🔴 resolved

### Org Page Polish
- [ ] **Mission text capitalization** — fix forced uppercase
  - Done when: Tested on live page

- [ ] **Header density** — reduce clutter, improve readability
  - Done when: Tested on live page

- [ ] **Lazy-load below-fold** — financial history, peer groups, etc.
  - Done when: Load time measured, improvement logged

- [ ] **Error handling** — add visible retry/degraded states for optional requests
  - Done when: Tested with failure cases

- [ ] **Metadata verification** — verify og:title + og:description server-rendered (not generic)
  - Done when: Tested on live droplet

### Performance & Monitoring
- [ ] **Search latency baseline**
  - Measure: p50, p95, p99 for representative queries
  - Target: p95 < 200ms
  - Done when: Baseline logged in docs

- [ ] **Org page load time baseline**
  - Measure: initial load + interactive time
  - Target: < 1s initial
  - Done when: Baseline logged

- [ ] **Database backup** — ensure clean backup before launch
  - Done when: Backup verified + tested

- [ ] **Rollback procedure** — document how to revert to `.prev`
  - Test: On staging, verify rollback works
  - Done when: Procedure tested + documented

### Launch Day (Oct 1)
- [ ] **Pre-launch validation** (5 AM)
  - [ ] All smoke tests passing
  - [ ] Search p95 < 200ms
  - [ ] Zero critical bugs in logs
  - [ ] Database backup complete
  - [ ] Rollback `.prev` verified
  - Done when: All gates cleared, founder authorizes launch

---

## PHASE 3A: OCT 1–15 (One-Click Giving Gate 1)

### Pre-Filled Donations (Gate 1)
- [ ] **"Donate Now" button** on org pages
  - Link to org's donate_url + query params (donor_email, donor_name, suggested_amount)
  - Done when: Button tested on 5 partner orgs, handoff recorded

- [ ] **Wallet integration** — capture donor data
  - Store: donor_email, donor_name, donor_phone (from Google sign-in or manual entry)
  - Done when: Data captured + can be pre-filled on next donation

- [ ] **Completion rate tracking**
  - Measure: % of "Donate Now" clicks that complete (target 30% vs 5% cold)
  - Done when: Baseline measured on 5 test orgs

---

## PHASE 3B: OCT 15 – NOV 30 (Needs Network Backend + Gate 2)

### Needs Network Backend Infrastructure
- [ ] **Nonprofit Need intake flow**
  - Input modes: voice (transcription), text (form), document (upload)
  - AI draft generation: Daanaa suggests Need in plain language
  - Done when: Intake tested end-to-end, nonprofits can submit

- [ ] **Nonprofit approval + edit**
  - Nonprofit reviews AI draft
  - Nonprofit can edit + approve for publishing
  - Done when: Approval flow tested

- [ ] **Needs database schema**
  - Table: need_id, ein, need_type (FUNDING/VOLUNTEER), title, description, amount, needed_by, status, last_confirmed_date
  - Done when: Schema tested, sample Needs created

- [ ] **Freshness automation**
  - Periodic re-confirm: every 30 days, ask nonprofit "Does this Need still exist?"
  - Auto-archive if no response after 60 days
  - Done when: Cron job tested, archival logic confirmed

- [ ] **Nonprofit dashboard**
  - View published Needs
  - Edit Needs
  - Approve/reject new Needs
  - Done when: Dashboard tested with 5 nonprofits

### One-Click Giving Gate 2 (Recurring)
- [ ] **Recurring frequency toggle**
  - Option: "I give monthly" vs "One-time"
  - Pre-fill donation frequency in query params
  - Done when: Toggle tested, recurring suggestions logged

- [ ] **Measure recurring adoption**
  - Track: % of donors choosing recurring (target 40%+)
  - Done when: Baseline measured

---

## PHASE 3C: DEC 1 (Needs Network Frontend + Launch)

### Needs Network UI
- [ ] **Donor discovery of Needs**
  - Search + filter: by Need type (Funding/Volunteer), by cause, by location
  - List view: show open Needs
  - Done when: Tested end-to-end with 50 seed Needs

- [ ] **Nonprofit Needs management dashboard**
  - Create new Need
  - Edit existing Need
  - View responses (donor interest, volunteer applications)
  - Publish/unpublish/archive Needs
  - Done when: Dashboard tested with 5 nonprofits

- [ ] **Wallet integration**
  - Save Need interest
  - Track "I'm interested in [Need]" signals
  - Done when: Interest signals tracked + queryable

- [ ] **Freshness UI**
  - Show "Last confirmed: X days ago" on Needs
  - Nonprofit sees re-confirmation reminder
  - Done when: UI tested, re-confirmation workflow tested

---

## PHASE 3D: JAN – FEB (Gates 3 & 4)

### One-Click Giving Gate 3 (DAF + Employer Match)
- [ ] **DAF routing detection**
  - Wallet stores: user's DAF provider (Fidelity/Schwab/Vanguard/etc)
  - "Route to my DAF" button appears if user has DAF
  - Button links to org's DAF landing page + org EIN
  - Done when: Tested with 3 DAF providers

- [ ] **Employer match detection**
  - Wallet stores: user's employer
  - "Employer Match Available" badge on org page
  - Links to employer's match portal + org EIN
  - Done when: Tested with 2 employers

- [ ] **Measure DAF + match adoption**
  - Track: % of users using DAF route, employer match clicks
  - Done when: Baseline measured

### One-Click Giving Gate 4 (Suggestions)
- [ ] **Wallet suggestion engine (MVP)**
  - Read: User's giving history (bookmarks, donations)
  - Generate: Suggestions for similar orgs
  - Display: "You gave to X, orgs like X also need help"
  - Opt-in: User controls suggestion frequency
  - Done when: Suggestions tested, user engagement tracked

- [ ] **Measure suggestion impact**
  - Track: Do suggestions → clicks? → donations?
  - Metric: "User choice" (did they donate after suggestion?) NOT algorithm accuracy
  - Done when: Conversion rate measured

---

## ONGOING

### Weekly
- [ ] Performance audit (search latency, page load time)
- [ ] Error log review (any new crashes?)
- [ ] Database health check (size, backup status)

### Monthly
- [ ] MAU + engagement metrics snapshot
- [ ] Update traction data (for board reviews)
- [ ] Roadmap adjustment (based on learnings)

---

## Success Criteria

### Oct 1 (Free Tier Live)
✅ Smoke tests passing  
✅ Search p95 < 200ms  
✅ Org pages rendering correctly  
✅ Wallet functional  
✅ Zero critical production bugs day 1

### Feb 28 (Gates 1–4 Live)
✅ Pre-fill completion 30%+ → measure improvement with Gates 2–4  
✅ Needs Network: 50+ orgs, 100+ Needs, satisfaction >80%  
✅ Recurring giving baseline established  
✅ DAF + employer routing tested  
✅ Suggestions live + tracked

---

## How to Use This List

1. **Pick a task** from the current phase
2. **Mark it done** when success criteria met (not when "mostly done")
3. **Update weekly** — track % complete per phase
4. **Escalate blockers** to founder immediately (don't wait for weekly sync)
5. **Pull next task** from upcoming phase when current task done (don't go off-script)

Ship it.
