# Sprint 1: Task Breakdown (Aug 1–15)

**Goal:** Launch public soft launch with donor search + nonprofit claiming.

**Team:** 1 contract engineer (full-time) + Akbar (strategy/decisions)  
**Duration:** 15 days  
**Definition of Done:** 1K+ nonprofits indexed, 100+ test users, 50+ nonprofits claimed, 0 bugs blocking demo

---

## Task Ownership Model

**Akbar:** Strategy, decisions, funder calls, nonprofit recruitment (sandbox)  
**Engineer:** All code (frontend + backend + agents)  
**Shared:** Testing, QA, bug triage

---

## Phase 1a: Backend Foundation (Aug 1–5)

### Task 1: API Architecture Setup
- [ ] FastAPI endpoints for:
  - `GET /api/orgs` (search, filter, pagination)
  - `GET /api/orgs/{ein}` (detail view)
  - `POST /api/claims/submit` (nonprofit claiming)
  - `GET /api/wallet` (donor wallet view)
  - `POST /api/wallet/add-bookmark` (add to wallet)
  - `POST /api/wallet/add-intent` (giving intent signal)
- [ ] Database schema: `org_claims` updates, wallet endpoints
- [ ] Authentication: Google OAuth for wallet sync
- **Time:** 2 days

### Task 2: Search Index (Elasticsearch or Full-Text Search)
- [ ] Index 1M+ nonprofits with:
  - Name, EIN, mission, location, NTEE category
  - Financial health score (v5 archetype + health signal)
  - Hidden gem status (boolean)
  - Donation link (verified or pending)
- [ ] Filter support: cause, location, health, archetype, hidden gem
- [ ] Sort: relevance, hidden gems, financial health
- **Time:** 2 days

### Task 3: Nonprofit Claiming Agent (MVP)
- [ ] Flow: nonprofit submits claim → agent validates EIN → checks email domain → creates org_claim record
- [ ] Validation rules:
  - EIN matches IRS database (existing tool available)
  - Email domain matches nonprofit website OR is generic (hotmail, gmail → manual review)
  - Name matches IRS records within 80% similarity
- [ ] If valid: auto-approve + send welcome email
- [ ] If flagged: add to manual review queue (Akbar approves)
- **Time:** 2 days

**Definition of Done:** Agent handles 80% of test claims without human intervention.

---

## Phase 1b: Frontend (Aug 5–12)

### Task 4: Nonprofit Search Page
- [ ] Components:
  - Search bar (keyword search)
  - Filters (cause, location, health, hidden gem)
  - Results grid (nonprofit cards)
  - Pagination (20 per page)
- [ ] Card shows:
  - Name, mission (excerpt)
  - Location
  - Financial health badge (HEALTHY / STABLE / CAUTION)
  - Hidden gem indicator (if applicable)
  - "View Details" link
- [ ] Responsive (mobile-first)
- **Time:** 2 days

### Task 5: Nonprofit Detail Page
- [ ] Shows full profile:
  - Mission (full text)
  - Location, website, EIN
  - Financial context:
    - Archetype (Donation-Funded / Fee-for-Service / Endowment-Funded)
    - Revenue band (Micro / Professional / Established)
    - Health signal (HEALTHY / STABLE / CAUTION)
    - Percentile rank vs peers ("Top 30% of peers in Education")
  - Hidden gem explanation (if applicable)
  - Donation link (if verified)
- [ ] Actions:
  - [+ Add to Wallet] button
  - [💰 Donate] link (if verified)
- [ ] Related: "Similar nonprofits in your area" (6 orgs)
- **Time:** 2.5 days

### Task 6: Giving Wallet Page
- [ ] Shows donor's bookmarks + giving intent
- [ ] Card per nonprofit:
  - Name, mission excerpt
  - Status: "In Wallet" or "Interested in giving"
  - Last added date
  - Actions: [View Full Profile] [Remove] [Mark as Gave]
- [ ] Summary stats:
  - Orgs bookmarked
  - Orgs interested in giving
  - Total amount considering (if tracked)
- [ ] Local storage persistence + Google account sync (if logged in)
- **Time:** 1.5 days

### Task 7: Nonprofit Claim Form
- [ ] Multi-step form:
  1. Basic info (name, EIN, website)
  2. Mission statement
  3. Donation link verification
  4. Contact email
- [ ] Validation (client + server):
  - EIN format check
  - Website reachability (HEAD request)
  - Email domain verification
- [ ] Confirmation page: "Thanks for claiming. We'll verify within 24 hours."
- [ ] Success: auto-redirects to profile (claimed, not public yet)
- **Time:** 1.5 days

**Total Frontend: 7.5 days** (parallel with backend where possible)

---

## Phase 1c: Integration & Testing (Aug 12–15)

### Task 8: API Integration
- [ ] Frontend calls all endpoints correctly
- [ ] Wallet stores data in localStorage (client) + syncs to server (if Google account)
- [ ] Search results load + filter correctly
- [ ] Detail page calls agent-flagged claims correctly
- **Time:** 1 day

### Task 9: Support Triage Agent (MVP)
- [ ] Listens to support@daanaa.org inbox
- [ ] Reads incoming emails
- [ ] Classify: nonprofit-claim-question / search-help / bug-report / other
- [ ] Draft response templates for common questions
- [ ] Approved response → send with human-in-loop
- [ ] Log all interactions
- **Time:** 1 day

**Definition of Done:** 20 test emails → agent classifies + drafts 100% correctly.

### Task 10: End-to-End Testing
- [ ] Donor flow: Search → Find org → Add to wallet → See in wallet ✅
- [ ] Nonprofit flow: Fill claim form → Auto-approve (if valid) → See profile ✅
- [ ] Edge cases:
  - EIN doesn't match IRS → Manual review
  - Email domain doesn't verify → Manual review
  - Search with no results → Shows helpful message
  - Mobile search → responsive, usable
- **Time:** 1 day

### Task 11: Performance & Security
- [ ] Search returns results in <500ms (1K+ orgs)
- [ ] API rate limiting (100 req/min per IP)
- [ ] HTTPS only
- [ ] Google OAuth flow works
- [ ] Wallet data encrypted at rest
- **Time:** 1 day

### Task 12: Sandbox Recruitment (Aug 10–15, parallel)
- [ ] Akbar reaches out to 50 nonprofit partners (using contacts + networks)
- [ ] Pitch: "We're testing a nonprofit discovery platform. Claim your profile, invite donors to try it."
- [ ] Get first 50 claims + feedback during sprint
- [ ] Document any UX issues found
- **Time:** Akbar, 2–3 hours/day

---

## Definition of Done (Sprint 1 Complete)

- [ ] ✅ 1K+ nonprofits indexed and searchable
- [ ] ✅ 100+ test donors can search, add to wallet, persist data
- [ ] ✅ 50+ nonprofits claimed (via sandbox recruitment)
- [ ] ✅ Onboarding Agent handles 80%+ of claims without manual intervention
- [ ] ✅ Support Triage Agent classifies + drafts responses correctly
- [ ] ✅ Zero Stewardship violations found in testing
- [ ] ✅ Mobile responsive (iOS Safari, Android Chrome)
- [ ] ✅ 99.9% uptime on staging (no crashes during demo)
- [ ] ✅ All endpoints documented + tested
- [ ] ✅ Bug log reviewed, critical bugs fixed, non-critical deferred to Sprint 2

---

## Daily Standup Format

**Time:** 9am, 15 min  
**Owner:** Akbar

**Engineer reports:**
- What I shipped yesterday
- What I'm building today
- What's blocking me

**Akbar reports:**
- Sandbox recruitment progress
- Funder feedback (if any calls)
- Decisions needed from engineer feedback

**Decision log:** Anything that's a design decision gets logged in DECISIONS.md

---

## Blockers & Escalation

**If engineer blocked >2 hours:** Escalate to Akbar immediately (async in Slack, not email)

**Common blockers + resolutions:**
- "How should we handle EIN edge cases?" → Akbar decides (use IRS fuzzy match or manual review)
- "Search is slow with 1M orgs" → Optimize indexes or paginate differently
- "Claim form validation too strict" → Relax validation, move to manual review

---

## Success Signals During Sprint

**Day 3 (Aug 4):**
- Backend API working locally
- 10 test nonprofits indexed
- Claiming agent handles first 5 test submissions

**Day 8 (Aug 9):**
- Frontend search working
- Nonprofit detail page rendering
- Claiming form UX solid (based on early feedback)

**Day 12 (Aug 13):**
- Wallet persisting data
- Support agent classifying emails
- Sandbox nonprofits claiming (feedback collected)

**Day 15 (Aug 15):**
- Ready for soft launch demo
- Documentation complete
- No critical bugs

---

## Decisions Needed Before Sprint Starts

| Decision | Impact | Default |
|----------|--------|---------|
| **EIN validation:** Fuzzy match or exact match? | Claim rate | Fuzzy 80%+ similarity |
| **Email verification:** Require nonprofit email, or allow any? | Claim friction | Allow any, flag suspicious for manual review |
| **Hidden gems algorithm:** Already live? | Launch feature | Yes (already computed in DB) |
| **Wallet sync frequency:** Real-time or batch? | User experience | Real-time if logged in, localStorage default |
| **Donation link requirement:** Optional or required to claim? | Nonprofit incentive | Optional (but incentivized) |

**Akbar to confirm these before Aug 1.**

---

## Files to Create/Modify

**Create new:**
- `frontend/src/pages/Search.tsx`
- `frontend/src/pages/NonprofitDetail.tsx`
- `frontend/src/pages/Wallet.tsx`
- `frontend/src/pages/ClaimForm.tsx`
- `backend/api/orgs.py` (search endpoints)
- `backend/agents/onboarding_agent.py`
- `backend/agents/support_triage_agent.py`
- `db/migrations/001_volunteer_signals_schema.sql` (if needed)

**Modify existing:**
- `frontend/src/App.tsx` (add routes)
- `backend/daanaa_api.py` (register new endpoints)
- `db/schema.sql` (org_claims, wallet fields)

---

## Estimated Time Breakdown

| Category | Time |
|----------|------|
| Backend (Tasks 1–3) | 6 days |
| Frontend (Tasks 4–7) | 7.5 days |
| Integration & Testing (Tasks 8–12) | 4 days |
| Parallel (Sandbox recruitment, Task 12) | 2–3 hours/day (Akbar) |
| **Total Engineer Time** | **~17.5 days** (assumes 8 hr/day) |
| **Total Akbar Time** | **~15 hours** (decisions + recruitment) |

**Feasible in 15 days?** YES (engineer focused, Akbar handling recruitment + decisions).

---

## Contingency

**If delayed:**
- Drop "Similar nonprofits" card (Task 5) → saves 0.5 days
- Defer Support Agent to Sprint 2 → saves 1 day
- Defer mobile optimization → saves 0.5 days

**If ahead:**
- Add volunteer interest signals (Priority 3 early) → preparatory work
- Add nonprofit admin dashboard stub → Sprint 2 foundation
- Add detailed testing docs for QA

---

**Owner:** Engineering Lead (Contract)  
**Manager:** Akbar  
**Start Date:** Aug 1, 2026  
**End Date:** Aug 15, 2026  
**Status:** Ready to kick off

---

*Created: Jun 18, 2026*  
*Last updated: Jun 18, 2026*
