# Build Priority Roadmap — "Everyone Rises Together"

**Principle:** Build in order of impact. Each layer enables the next.

---

## Priority 1: Donor Experience + Wallet (Aug 1–15)

**Goal:** Donors discover organizations, understand them, signal intent

### Features
- [ ] Search (cause, location, financial health, hidden gems)
- [ ] Nonprofit detail page (mission, scores, peer context, donation link)
- [ ] Giving Wallet (bookmark + giving intent + local-first)
- [ ] Filter by archetype/health/hidden gem status
- [ ] "Add to Wallet" flow

### Why First?
- Donors create market demand
- Nonprofits won't claim profiles if no one visits
- Wallet is the foundation for all intent signals (giving, volunteering, board)

### Success Metric (Aug 15)
- 1K+ nonprofits indexed + searchable
- 100+ test users can search and add to wallet
- Wallet persists across sessions (localStorage)

### Related Documents
- G0_LAUNCH_READINESS_CHECKLIST.md (donor UX)
- Q4_STRATEGY.md (donor acquisition starts Sep, but experience ready Aug)

---

## Priority 2: Nonprofit Self-Service (Aug 15–Sep 1)

**Goal:** Nonprofits claim profiles, control their narrative, see donor interest

### Features
- [ ] Nonprofit claim form (basic: name, EIN, mission, website)
- [ ] Claim verification (email domain check, EIN match)
- [ ] Profile editor (update mission, tags, donation link)
- [ ] Admin dashboard (view profile, see edits pending, basic stats)
- [ ] **NEW:** Checkbox for "looking for volunteers" + "looking for board"
- [ ] **NEW:** Skills selection (what they need)

### Why Second?
- Now that donors exist, nonprofits have reason to claim
- Claiming is self-service (no Daanaa staff bottleneck)
- Nonprofit onboarding agent can handle most claims

### Success Metric (Sep 1)
- 500+ nonprofits claimed
- 80%+ claim completion rate
- Admin dashboard shows them who's interested

### Related Documents
- ALIAI_OPERATIONS_PLAYBOOK.md (Nonprofit Onboarding Agent)
- G0_DAILY_GUIDE_JUN16_21.md (recruiting first 50 nonprofits via sandbox)
- TEXAS_DBA_FILING_CHECKLIST.md (legal entity ready for partnerships)

---

## Priority 3: Volunteer & Board Matching (Sep 1–Oct 1)

**Goal:** Connect volunteers/board candidates directly to nonprofits that need them

### Features
- [ ] Volunteer interest signals (donor clicks button on nonprofit page)
- [ ] Skills checklist (grant writing, fundraising, etc.)
- [ ] Hours commitment (4-8, 8-16, 16+ hrs/month)
- [ ] Board interest signals (separate from volunteering)
- [ ] Nonprofit dashboard (see who's interested by skill)
- [ ] Nonprofit → Donor messaging (direct contact)
- [ ] Donor can withdraw interest anytime

### Why Third?
- Requires donor + nonprofit infrastructure to work
- Volunteer matching is value-add, not core (but completes "everyone rises")
- Nonprofits need to be claimed first

### Success Metric (Oct 1)
- 100+ volunteer signals
- 10+ volunteer relationships initiated
- Small orgs see 2x volunteer signal rate vs large orgs (fairness proof)

### Related Documents
- VOLUNTEER_BOARD_MATCHING_SPEC.md (full spec, ready to build)
- Q4_STRATEGY.md (volunteer recruitment supports Q4 giving)

---

## Priority 4: Vendor/Partner Network (Oct 1+)

**Goal:** Service providers (accountants, consultants, lawyers) can offer discounted services to verified nonprofits

### Features
- [ ] Vendor onboarding (who can offer services to nonprofits?)
- [ ] Service listings (grant writing support, bookkeeping, etc.)
- [ ] Nonprofit directory access (vendors see organizations, reach out to relevant ones)
- [ ] Vendor review/verification (Daanaa doesn't endorse, but verifies legitimacy)
- [ ] Commission/markup (how does Daanaa make money without compromising principles?)

### Why Fourth?
- Requires proven donor + nonprofit + volunteer base first
- Vendor influence on visibility = Stewardship risk (must be managed carefully)
- Can be deferred without breaking the core platform

### Success Metric (Dec 31)
- 20+ verified vendors
- 0 vendor influence on org rankings/visibility (compliance check passed)
- Revenue model validated (but NOT primary focus)

### Related Documents
- VENDOR-POLICY.md (exists; governance structure)
- FUNDER_RESEARCH_OMIDYAR.md (vendors = responsible AI governance question)

---

## Build Sprints (Aligned to Priority)

### Sprint 1: Aug 1–15 (Donor + Nonprofit Claim)
**Owner:** Akbar + contract engineer  
**Deliverables:**
- Donor search + detail page + wallet
- Nonprofit claim form + basic admin dashboard
- Onboarding agent MVP (handles claims)
- Support triage agent MVP (email handling)

**Launch:** Aug 15 (public soft launch)

---

### Sprint 2: Aug 15–Sep 1 (Volunteer Signals + Dashboard)
**Owner:** Akbar + contract engineer  
**Deliverables:**
- Volunteer/board interest signals (donor-side)
- Nonprofit admin dashboard (see interested volunteers/board)
- Growth analytics agent
- Data validation agent

**Launch:** Sep 1 (Phase 2 feature set)

---

### Sprint 3: Sep 1–Oct 1 (Volunteer Messaging + Agents)
**Owner:** Akbar + contract engineer  
**Deliverables:**
- Nonprofit → volunteer messaging
- Compliance monitor agent (all agents live)
- Q4 growth sprint begins
- Volunteer matching refinement based on real usage

**Launch:** Oct 1 (full volunteer ecosystem live)

---

### Sprint 4: Oct 1–Dec 31 (Vendor Network + Growth)
**Owner:** Akbar + partnership manager (if funded)  
**Deliverables:**
- Vendor onboarding + verification
- Service listings in nonprofit directory
- Vendor governance + compliance checks
- Q4 growth execution (media, nonprofits, donors, volunteers)

**Launch:** Ongoing (vendor partners added as qualified)

---

## What Gets Cut / Deferred

### ✂️ Deferred to Phase 2 (After Dec 31)
- Advanced volunteer matching (skill recommendations, time-zone matching)
- Board-specific marketplace
- Vendor revenue model (commission, markup, affiliate)
- Payment processing (3-year vision, not 2026)
- Academic partnerships (Omidyar research collabs)

### ✂️ Not Building (Out of Scope)
- Donor transaction processing (hand-off model only)
- Nonprofit CRM (they use their own)
- Giving analytics for nonprofits (privacy constraint)
- Volunteer scheduling/management (let nonprofits own)

---

## Funding Allocation (If $400K from G0 Partners)

| Item | Budget | Timeline |
|------|--------|----------|
| Contract engineer (Jul–Dec full-time) | $60K | Covers all sprints |
| Claude API (batch ML tasks) | $40K | Heavy Aug–Sep |
| Local inference (electricity, etc.) | $5K | Ongoing |
| Droplet + infrastructure | $20K | Ongoing |
| Third-party tools (email, analytics) | $15K | Ongoing |
| Vendor verification + legal | $20K | Oct+ |
| Q4 marketing + events | $40K | Sep–Dec |
| Buffer/contingency | $200K | Phase 2 |
| **Total** | **$400K** | 18 months |

---

## Stewardship Checkpoints (Weekly)

Every sprint, verify:
- ✅ **P1 (Mission):** Does this feature serve discovery, not growth hacking?
- ✅ **P2 (Privacy):** Are we storing only intent, not transactions/behavior?
- ✅ **P4 (Fairness):** Do small orgs benefit equally from this feature?
- ✅ **P7 (Independence):** Is vendor influence structural prohibited?

---

## Success Criteria by Phase

### Aug 15: Donor + Nonprofit Claim Live
- [ ] 1K+ nonprofits searchable
- [ ] 100+ test donors using wallet
- [ ] 50+ nonprofits claimed in sandbox
- [ ] 0 Stewardship violations found

### Sep 1: Volunteer Signals Live
- [ ] 500+ nonprofits claimed
- [ ] 100+ donor volunteer interest signals
- [ ] Nonprofit dashboard shows interests aggregated
- [ ] 0 privacy leaks

### Oct 1: Full Volunteer Ecosystem Live
- [ ] 10+ volunteer relationships initiated
- [ ] Messaging between nonprofits + volunteers working
- [ ] All 5 agents operational
- [ ] 0 agent failures in production

### Dec 31: Vendor Network + Growth
- [ ] 50K MAU donors
- [ ] 1K+ claimed nonprofits
- [ ] 10K+ donors in wallet
- [ ] 50+ media mentions
- [ ] 20+ vendors verified (0 violations of P7)

---

## What This Enables for G0 Pitch

**Priority 1 (Donors):** "We're a world-class discovery platform"  
**Priority 2 (Nonprofits):** "Nonprofits own their narrative"  
**Priority 3 (Volunteers):** "Talent flows to mission, not brand"  
**Priority 4 (Vendors):** "Service ecosystem, responsibly governed"

**Together:** "Everyone rises together."

---

## Documents That Map to This Roadmap

| Priority | Related Docs |
|----------|--------------|
| **1. Donors** | G0_LAUNCH_READINESS_CHECKLIST.md |
| **2. Nonprofits** | ALIAI_OPERATIONS_PLAYBOOK.md (Onboarding Agent) |
| **3. Volunteers** | VOLUNTEER_BOARD_MATCHING_SPEC.md |
| **4. Vendors** | VENDOR-POLICY.md (governance) |
| **All** | SESSION_CHECKPOINT_JUN15.md (decisions locked) |
| **All** | G0_PRINCIPLES_DEFENSE.md (when to say no) |
| **All** | STEWARDSHIP.md (11 principles guide every decision) |

---

**Owner:** Product Strategy  
**Status:** Approved for build  
**Next:** Create Sprint 1 detailed task breakdown

---

*Created: Jun 18, 2026*  
*Last updated: Jun 18, 2026*
