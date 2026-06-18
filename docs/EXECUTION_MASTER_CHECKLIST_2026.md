# Execution Master Checklist — 2026 (Jun 18 – Dec 31)

**Goal:** Build "everyone rises together" from Jun 18 to Dec 31, 2026.  
**Principle:** Check weekly that everything connects. Quality over speed.  
**Status:** Living document — update as you go.

---

## Phase 0: Partnership & Funding (Jun 16–21)

**Status:** IN PROGRESS (calls happening Jun 17–19)

- [ ] **Jun 16:** Attorney call (G0_ATTORNEY_CALL_SCRIPT.md)
  - Q1: Can EcoMargins take grants directly?
  - Q2: Stewardship legal defensibility?
  - Q3: Public signatory list implications?
  - **Notes:** _______________

- [ ] **Jun 17–19:** Exploratory funder calls (3 calls)
  - [ ] DRK Foundation (95% fit) — Systems change angle
    - Contact: _______________
    - Reaction: _______________
    - Next step: _______________
  - [ ] Knight Foundation (90% fit) — Civic participation angle
    - Contact: _______________
    - Reaction: _______________
    - Next step: _______________
  - [ ] Omidyar Network (85% fit) — Responsible AI angle
    - Contact: _______________
    - Reaction: _______________
    - Next step: _______________

- [ ] **Jun 17:** Anthropic cold outreach (ANTHROPIC_CONTACT_RESEARCH.md)
  - [ ] Research contact
  - [ ] Draft email
  - [ ] Send by Jun 18

- [ ] **Jun 18:** File Texas DBAs (TEXAS_DBA_FILING_CHECKLIST.md)
  - [ ] Daanaa DBA filed
    - Confirmation #: _______________
    - Effective date: _______________
  - [ ] ZDPark DBA filed
    - Confirmation #: _______________
    - Effective date: _______________

- [ ] **Jun 21:** Summary in PARTNER_TRACKER.md
  - [ ] Attorney findings documented
  - [ ] Funder interest levels recorded
  - [ ] Next 3 weeks planned (formal conversations)

---

## Phase 1a: Sprint 1 Prep (Jun 20 – Aug 1)

**Status:** PLANNING (details in SPRINT_1_TASK_BREAKDOWN.md)

### Funding & Partnerships (Akbar's work)

- [ ] **Jun 24–30:** Week 2 formal funder conversations
  - [ ] Call #2 with most-interested funder
  - [ ] Gauge readiness to sign Stewardship Commitment
  - [ ] Discuss timeline & funding mechanics

- [ ] **Jul 1:** Founding partners locked in (3–5 signatories)
  - Partner 1: _______________
  - Partner 2: _______________
  - Partner 3: _______________

- [ ] **Jul 1:** Stewardship Commitments signed
  - Legal review complete
  - All partners sign

### Engineer Hiring (Akbar's work)

- [ ] **Jul 1:** Contract engineer onboarded (full-time through Dec)
  - Name: _______________
  - Rate: _______________
  - Start date: _______________
  - Knowledge transfer: (code walkthrough, doc review)

### Nonprofit Recruitment (Akbar's work, parallel with engineering)

- [ ] **Aug 1–15:** Sandbox recruitment (50 nonprofits)
  - [ ] Identify 50 nonprofits to beta test
  - [ ] Send recruitment email
  - [ ] Secure 20+ commitments by Aug 10

---

## Phase 1b: Sprint 1 Build (Aug 1–15)

**Status:** READY TO START (details in SPRINT_1_TASK_BREAKDOWN.md)

**Engineer owns all code tasks. Akbar owns decisions + sandbox.**

### Daily Standup (9am, 15 min)
- [ ] Every weekday, Aug 1–15
- [ ] Format: What shipped / What's building / Blockers
- [ ] Update DECISIONS.md for any design decisions

### Engineering Tasks (Engineer's work)

#### Phase 1a: Backend Foundation (Aug 1–5)
- [ ] Task 1: API architecture setup (2 days)
- [ ] Task 2: Search index (Elasticsearch or FTS) (2 days)
- [ ] Task 3: Nonprofit Onboarding Agent MVP (2 days)

**Checkpoint (Aug 5):**
- [ ] 10 test nonprofits indexed
- [ ] Claiming agent handles first 5 test submissions ✓

#### Phase 1b: Frontend (Aug 5–12)
- [ ] Task 4: Search page (2 days)
- [ ] Task 5: Nonprofit detail page (2.5 days)
- [ ] Task 6: Wallet page (1.5 days)
- [ ] Task 7: Claim form (1.5 days)

**Checkpoint (Aug 9):**
- [ ] Frontend search working ✓
- [ ] Detail page rendering ✓
- [ ] Claiming form UX solid ✓

#### Phase 1c: Integration & Testing (Aug 12–15)
- [ ] Task 8: API integration (1 day)
- [ ] Task 9: Support Triage Agent MVP (1 day)
- [ ] Task 10: End-to-end testing (1 day)
- [ ] Task 11: Performance & security (1 day)
- [ ] Task 12: Final QA + bug fixes (1 day)

**Checkpoint (Aug 13):**
- [ ] Wallet persisting data ✓
- [ ] Support agent classifying emails ✓
- [ ] Zero critical bugs ✓

### Sandbox Testing (Akbar's work, Aug 10–15)

- [ ] **Aug 10:** Send invite to 50 nonprofits
- [ ] **Aug 10–15:** Collect feedback
  - Claim form UX: smooth? ✓
  - Profile visibility: working? ✓
  - Agent success rate: 80%+? ✓
  - Bug reports: zero blockers? ✓

**Checkpoint (Aug 15):**
- [ ] 50+ claims submitted
- [ ] Agent auto-approved 80%+
- [ ] Zero critical UX issues ✓

---

## Phase 1c: Sprint 1 Launch (Aug 15)

**Status:** LAUNCH DAY

- [ ] **Aug 15 Morning:** Final QA pass (Engineer + Akbar, 2 hours)
  - [ ] Smoke test (search, detail, claim, wallet)
  - [ ] No 500 errors in logs
  - [ ] Uptime check (API + frontend)

- [ ] **Aug 15 Afternoon:** Public soft launch
  - [ ] Frontend goes live (daanaa.org)
  - [ ] 1K+ nonprofits searchable
  - [ ] Can claim profiles
  - [ ] Can add to wallet
  - [ ] Demo ready for funders

- [ ] **Aug 15 EOD:** Announce to:
  - [ ] All 50 sandbox nonprofits
  - [ ] All founding partners
  - [ ] Early network

**Success Criteria (Aug 15):**
- ✅ 1K+ nonprofits indexed + searchable
- ✅ 100+ test donors using wallet
- ✅ 50+ nonprofits claimed (sandbox)
- ✅ Agent handles 80%+ of claims auto-approved
- ✅ Zero critical bugs blocking demo
- ✅ 99%+ uptime (no crashes)

---

## Phase 2: Volunteer Matching (Aug 15 – Sep 1)

**Status:** PLANNED (details in VOLUNTEER_BOARD_MATCHING_SPEC.md)

- [ ] **Aug 15–20:** Engineer refactors for volunteer signals
  - [ ] Wallet schema ready for volunteer intent
  - [ ] Database migration (zero data loss)

- [ ] **Aug 20–28:** Build volunteer signals + dashboard
  - [ ] Donor can signal volunteer + board interest
  - [ ] Nonprofit dashboard shows interested people
  - [ ] Skills checklist (8 categories)

- [ ] **Aug 28 – Sep 1:** Testing + feedback
  - [ ] E2E test: donor signals → nonprofit sees
  - [ ] Sandbox: 20+ nonprofits opt into volunteer matching
  - [ ] Zero critical issues

**Launch (Sep 1):**
- [ ] Volunteer interest signals live for donors
- [ ] Nonprofit dashboard shows aggregate counts
- [ ] All 5 agents operational (onboarding + support + growth + data + compliance)

**Success Criteria (Sep 1):**
- ✅ 100+ volunteer interest signals
- ✅ 500+ nonprofits claimed
- ✅ 5 agents operational in production
- ✅ Zero agent failures

---

## Phase 3: Volunteer Messaging (Sep 1 – Oct 1)

**Status:** PLANNED (Phase 3 in roadmap)

- [ ] **Sep 1–15:** Build nonprofit → donor messaging
  - [ ] Nonprofit can message interested volunteers
  - [ ] Direct email contact exchange
  - [ ] Message tracking (who reached out)

- [ ] **Sep 15–28:** Messaging + full dashboard
  - [ ] Nonprofit dashboard complete (view, filter, message)
  - [ ] Volunteer can withdraw interest anytime
  - [ ] Nonprofit sees who's interested

- [ ] **Sep 28 – Oct 1:** Testing + launch
  - [ ] Sandbox: 10+ volunteer relationships initiated
  - [ ] Messaging flow works end-to-end

**Launch (Oct 1):**
- [ ] Full volunteer ecosystem live (signal + see + message)
- [ ] All agents proven in production

**Success Criteria (Oct 1):**
- ✅ 10+ volunteer relationships initiated
- ✅ Small orgs see 2x volunteer signals vs large orgs (fairness)
- ✅ Messaging working, zero failures
- ✅ Support load remains manageable (agents handling 80%+)

---

## Phase 4: Q4 Growth Sprint (Oct 1 – Dec 31)

**Status:** PLANNED (details in Q4_STRATEGY.md)

### October (Donor Acquisition + Publicity)

- [ ] **Oct 1–14:** Donor messaging pivot
  - [ ] Paid ads live (Google + LinkedIn, $2K budget)
  - [ ] Email list growing (5K+ subscribers target)
  - [ ] Content marketing (blog 2x/week)

- [ ] **Oct 15–31:** Momentum
  - [ ] Social media blitz (10K followers target)
  - [ ] Nonprofit testimonial videos (5–10)
  - [ ] Holiday giving guide (downloadable)

**Checkpoint (Oct 31):**
- [ ] 10K+ donors (MAU)
- [ ] 1K+ nonprofits claimed
- [ ] 1K+ donors in wallet

### November (Giving Tuesday + Momentum)

- [ ] **Nov 1–27:** Holiday prep
  - [ ] Giving Tuesday campaign (Nov 28)
  - [ ] Nonprofit matching push (partner with networks)
  - [ ] Press + podcast blitz

- [ ] **Nov 28:** Giving Tuesday surge
  - [ ] Email blasts (3–4 leading up)
  - [ ] Social countdown
  - [ ] Support team ready for surge

**Checkpoint (Nov 30):**
- [ ] 20K+ MAU
- [ ] 5K+ donors in wallet
- [ ] 0 support failures (agent handling load)

### December (Year-End Surge)

- [ ] **Dec 1–31:** Peak giving season
  - [ ] Email campaigns 2–3x/week
  - [ ] Social media daily
  - [ ] Paid ads ramped ($1K/week)
  - [ ] Hidden gems spotlighting (daily)

- [ ] **Dec 15:** Impact report published
  - [ ] Donor count
  - [ ] Giving intent tracked
  - [ ] Hidden gems funded
  - [ ] Volunteer relationships formed

**Checkpoint (Dec 31):**
- [ ] 50K+ MAU
- [ ] 10K+ donors in wallet
- [ ] 1K+ claimed nonprofits
- [ ] 50+ media mentions
- [ ] 200+ hidden gems funded

---

## Vendor Network (Oct 1+)

**Status:** PLANNED (lowest priority, Phase 4)

- [ ] **Oct 1–15:** Design vendor governance
  - [ ] VENDOR-POLICY.md enforced in code
  - [ ] Compliance monitoring live

- [ ] **Oct 15 – Dec 31:** Vendor recruitment + compliance
  - [ ] 20+ vendors verified
  - [ ] Zero vendor influence on rankings (compliance audit)
  - [ ] Service listings live (optional)

---

## Stewardship Checkpoints (Weekly)

**Every Friday, check:**

- ✅ **P1 (Mission):** Is everything serving nonprofit discovery + fairness?
- ✅ **P2 (Privacy):** Are we storing only intent, not transaction/behavior?
- ✅ **P4 (Fairness):** Do small orgs benefit equally from each feature?
- ✅ **P7 (Independence):** Is vendor influence structurally blocked?

**Monthly update to STEWARDSHIP.md if principles drift.**

---

## Decision Log (Live)

**Update as you make decisions:**

| Decision | Choice | Why | Date |
|----------|--------|-----|------|
| Search index | Elasticsearch | Speed + filtering | Jun 18 |
| EIN validation | Fuzzy 80%+ | Balance usability + verification | Jun 18 |
| Volunteer skills | 8 categories | Complete but not overwhelming | Jun 18 |
| ... | ... | ... | ... |

---

## Success Criteria by Milestone

### Aug 15: Soft Launch
- ✅ 1K+ nonprofits indexed
- ✅ 100+ test donors
- ✅ 50+ nonprofits claimed
- ✅ Agent 80%+ auto-approval rate
- ✅ Zero critical bugs

### Sep 1: Volunteer Ecosystem
- ✅ 500+ nonprofits claimed
- ✅ 100+ volunteer signals
- ✅ All 5 agents operational
- ✅ Zero agent failures

### Oct 1: Full Features Live
- ✅ 10+ volunteer relationships
- ✅ 10K+ donors in wallet
- ✅ 1K+ nonprofits claimed
- ✅ Small orgs 2x volunteer interest vs large

### Dec 31: Growth Achieved
- ✅ 50K+ MAU
- ✅ 10K+ donors in wallet
- ✅ 1K+ nonprofits claimed
- ✅ 50+ media mentions
- ✅ 200+ hidden gems funded
- ✅ Zero Stewardship violations

---

## Documents Reference

| Phase | Key Docs |
|-------|----------|
| **G0 (Jun)** | G0_ATTORNEY_CALL_SCRIPT.md, G0_PARTNER_CALL_SCRIPT.md, FUNDER_RESEARCH_*.md, PARTNER_TRACKER.md |
| **Sprint 1 (Aug)** | SPRINT_1_TASK_BREAKDOWN.md, SPRINT_1_ARCHITECTURE.md, DATA_MODEL_SPRINT_1.md, SPRINT_1_TESTING_STRATEGY.md |
| **Sprint 2 (Sep)** | VOLUNTEER_BOARD_MATCHING_SPEC.md, BUILD_PRIORITY_ROADMAP.md |
| **Q4 Growth (Oct–Dec)** | Q4_STRATEGY.md |
| **All phases** | STEWARDSHIP.md, STEWARDSHIP_PARTNER_AGREEMENT.md, G0_PRINCIPLES_DEFENSE.md, ALIAI_OPERATIONS_PLAYBOOK.md |

---

## Weekly Status Template

**Every Friday, fill this out:**

```
WEEK OF: [Date]

COMPLETED THIS WEEK:
- [ ] [Task]
- [ ] [Task]

IN PROGRESS:
- [ ] [Task]

BLOCKERS:
- [ ] [Issue]

DECISIONS MADE:
- [ ] [Decision] → [Choice]

STEWARDSHIP CHECK:
- [ ] All principles honored? [YES/NO]
- [ ] Any drift? [Describe]

NEXT WEEK:
- [ ] [Task]
- [ ] [Task]

CONFIDENCE (1-10):
- Progress toward launch: [N]
- Quality of work: [N]
- Team morale: [N]
```

---

## Final Notes

**This is a living document.** Update it as:
- Milestones complete
- Priorities shift
- Decisions change
- Blockers appear

**Keep it honest.** Don't pretend everything's on track if it's not. Real feedback helps.

**Celebrate small wins.** Aug 15 launch is huge. Sep 1 volunteer ecosystem is huge. Dec 31 50K MAU is huge. Mark them.

---

**Owner:** Akbar  
**Last updated:** Jun 18, 2026  
**Status:** READY TO EXECUTE

---

*"Everything rises together. Check weekly that it connects."*
