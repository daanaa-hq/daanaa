# Build Manifest: Unified System Architecture
## From Board Decisions to Launch-Ready Product

**Status:** Strategy frozen. Build begins immediately after board vote.  
**Timeline:** 12 weeks to pilot launch (Q4 2026)  
**Team:** Founder + 1 backend + 1 frontend + QA contractor  
**Budget:** $30K founder capital (no external funding needed for Stage 1)

---

## The Bridge: Decisions → Features → Code

```
15 Board Decisions
  ↓ (vote + approval)
10 Stakeholder Briefings (stakeholders understand their role)
  ↓ (alignment confirmed)
Development Pipeline (what to build, in what order)
  ↓ (sprint planning)
4 Sprints × 3 weeks each = 12 weeks
  ↓ (sprint execution)
MVP Feature Complete
  ↓ (school recruitment)
Pilot Launch: 3–5 Houston Schools
  ↓ (measure + learn)
Gate Review (metrics check) → Stage 2 decision
```

---

## Stage 1 Build: 12 Weeks to Pilot Launch (Q4 2026)

### Decisions Being Implemented
- ✅ Decision 1: Student Account Model (tiered by age, school-verified <16)
- ✅ Decision 2: AI Assistant (defer to post-pilot)
- ✅ Decision 3: Fraud Detection (tiered admin review)
- ✅ Decision 6: Minimum Age (16+, no COPPA complexity)
- ✅ Decision 7: Hour Constraints (8h/day max, student protection)
- ✅ Decision 8: Communications (student-centric primary)

### NOT Implemented in Stage 1 (Deferred)
- ⏸️ Decision 4: Geographic Expansion (Houston only; selective expansion in Stage 2)
- ⏸️ Decision 5: Pricing (free pilot; freemium in Stage 2)
- ⏸️ Decision 9: Donor Profiles (single profile MVP; Head of Household in Stage 2)
- ⏸️ Decision 10: Revenue Model (free only; hybrid in Stage 2)
- ⏸️ Decision 11–15: Legal/compliance (basic mitigations; formal in Stage 2+)

### Why This Scope?
Keep Stage 1 **laser-focused** on three things:
1. School adoption (3–5 pilots)
2. Student engagement (500+ signups)
3. Nonprofit value (hours logged, feedback positive)

Do this, and Stage 2 fundraising/expansion is obvious.

---

## 4-Sprint Breakdown (3 weeks each)

### Sprint 1 (Weeks 1–3): Account Model + Age Gating

**Decisions:** 1 (account model), 6 (minimum age), T&S (COPPA legal)

**Features to Build:**
- [ ] OAuth signup (Google/Apple login)
- [ ] Age verification: ask DOB, block if <16
- [ ] Role selector: "I'm a student" vs. "I'm staff at nonprofit"
- [ ] Dependent flow (if <18, ask parent email, send parent verification link)
- [ ] Student dashboard: basic (upcoming opportunities, hours logged)
- [ ] Nonprofit admin: basic (view volunteer submissions)

**Tech:**
- Frontend: React signup component, role routing, age gate logic
- Backend: Age validation endpoint, role assignment, dependent email service
- Database: No schema changes (reuse existing student_accounts table)
- Legal: COPPA T&S + parental consent form (legal team, parallel)

**Dependencies:**
- Legal must finalize T&S by Week 1 (blocks signup flow testing)

**Definition of Done:**
- [ ] Sign up as student 16+ ✅
- [ ] Sign up as student 15, get blocked ✅
- [ ] Sign up as <18, parent gets email, approves ✅
- [ ] Role routing works (student → dashboard, nonprofit → admin) ✅
- [ ] 0 COPPA violations (manual review) ✅

**Owner:** [Frontend Lead] + [Backend Lead]  
**QA:** Manual testing (school testers)

---

### Sprint 2 (Weeks 4–6): Fraud Detection Admin UI + Hour Constraints

**Decisions:** 3 (fraud detection), 7 (hour constraints)

**Features to Build:**
- [ ] Fraud detection engine integration (use existing volunteer_fraud_detection.py)
- [ ] Admin review UI: see flagged submissions, reason + risk score
- [ ] One-click approve/reject per submission
- [ ] Batch review mode (see 20 flagged items, approve all at once)
- [ ] Hour validation: block submissions >8h/day, show error
- [ ] Hour warning: yellow warning if >6h/day (suggest split into 2 days?)
- [ ] Fraud analytics: trending (% flagged, false positive rate)

**Tech:**
- Frontend: Fraud review dashboard (search, filter, sort by risk)
- Backend: Fraud flag query API, approve/reject endpoints
- Database: volunteer_fraud_flags table (already exists from previous work)
- No new dependencies (fraud engine already built)

**Definition of Done:**
- [ ] Admin can see flagged submissions <10 sec per item ✅
- [ ] Click one button, submission approved ✅
- [ ] Can't submit >8h/day ✅
- [ ] Error message is clear to student ✅
- [ ] False positive rate <10% (admin feedback loop) ✅

**Owner:** [Frontend Lead] + [Backend Lead]  
**QA:** Contractor QA (test fraud cases + edge cases)

---

### Sprint 3 (Weeks 7–9): School Verification + FERPA DUA

**Decisions:** 12 (verification, school path)

**Features to Build:**
- [ ] School admin panel: login with school Google Workspace account
- [ ] School roster upload: CSV or LMS sync (start with CSV for MVP)
- [ ] Student verification: school checks name + DOB against roster, marks "verified"
- [ ] FERPA DUA workflow: school must read + sign DUA before roster access
- [ ] Data access logging: every school data access logged (audit trail)
- [ ] School-verified badge: "Verified by [School Name]" on student profile
- [ ] School email template: "DUA signed on [date], X students verified"

**Tech:**
- Frontend: School admin panel (roster upload, DUA signature, student list)
- Backend: Roster import API, DUA signature endpoint, access logging
- Database: No new tables (use existing volunteer_hours + audit_log)
- Legal: FERPA DUA template finalized (legal team, Week 7)

**Dependencies:**
- Legal must finalize DUA by Week 7 (blocks school testing)

**Definition of Done:**
- [ ] School can upload roster CSV ✅
- [ ] School sees list of students to verify ✅
- [ ] School can bulk-verify students ✅
- [ ] DUA signature is logged + timestamped ✅
- [ ] 0 FERPA violations (legal review) ✅
- [ ] Audit log shows all school data access ✅

**Owner:** [Frontend Lead] + [Backend Lead]  
**School Partners:** [Education Lead] recruits 1–2 schools for pilot testing

---

### Sprint 4 (Weeks 10–12): Messaging, Monitoring, Launch Polish

**Decisions:** 8 (communications)

**Features to Build:**
- [ ] Student landing page: "Volunteer and make an impact" (hero copy)
- [ ] Nonprofit landing page: "Manage your volunteers" (value prop)
- [ ] Email templates: submission received, approved, rejected, hours claimed
- [ ] Error monitoring: Sentry integration (real-time alerts)
- [ ] Health dashboard: API response times, error rates, uptime
- [ ] Support playbook: common issues, escalation process
- [ ] Launch checklist: all systems green? ✅

**Tech:**
- Frontend: Landing pages, email template system
- Backend: Sentry integration, health endpoint
- DevOps: Monitoring dashboard setup
- Communications: Copy writing (student-centric tone)

**Definition of Done:**
- [ ] Copy is student-centric, empowering ✅
- [ ] No COPPA/legal violations in messaging ✅
- [ ] Error monitoring live + alerting works ✅
- [ ] Support team trained on playbook ✅
- [ ] All systems green, launch ready ✅

**Owner:** [Communications] + [DevOps] + [Support Lead]

---

## Parallel Work Streams (Not Sequential)

**Legal (Weeks 1–9):**
- [ ] Week 1–3: COPPA T&S finalization
- [ ] Week 1–3: Parental consent form
- [ ] Week 4–6: Fraud detection policy documentation
- [ ] Week 7–9: FERPA DUA template + school partnership agreements
- [ ] Week 9: Final review all docs

**Education (Weeks 1–12):**
- [ ] Week 1–4: Identify 5 potential pilot schools (Houston area)
- [ ] Week 5–8: Initial conversations, gauge interest
- [ ] Week 9–10: Sign 3–5 schools to pilot (DUA signed)
- [ ] Week 11–12: School onboarding, admin training

**QA (Weeks 4–12):**
- [ ] Week 4–6: Fraud detection + hour constraints manual testing
- [ ] Week 7–9: School verification flow testing (work with school partners)
- [ ] Week 10–12: Full system regression testing (account → submission → approval)

---

## Key Mitigations (Stage 1)

**What We're NOT Doing (to keep scope tight):**

| What | Why Not | When We Do It |
|------|---------|---|
| Pricing/payments | Free pilot only; no money changes hands | Stage 2 (after school interest proven) |
| Donor profiles | Single profile MVP; don't need complexity | Stage 2 (when fundraising) |
| Geographic expansion | Houston only; don't expand yet | Stage 2 (after pilot success metrics) |
| Board governance | Informal agreements; formalize later | Stage 2 (when more stakeholders) |
| Insurance | Self-insure (risk acceptance); formal insurance Stage 2 | Stage 2 (when scaling) |
| Data retention | Keep all data for now; implement 7-yr deletion Stage 2 | Stage 2 (when GDPR matters) |
| Cyber insurance | Uninsured; add in Stage 2 | Stage 2 (when data grows) |
| AI assistant | Defer (Decision 2); build post-pilot | Stage 2+ (after learning from pilots) |

**Result:** MVP ships 12 weeks on time. No feature creep.

---

## Stage 1 Success Criteria (Gate to Stage 2)

**By Week 14 (end of pilot, early January 2027), board evaluates:**

| Metric | Target | Threshold | Owner |
|--------|--------|-----------|-------|
| **School Adoption** | 3–5 schools signed + active | ✅ 100% | Education Lead |
| **Student Engagement** | 500+ student signups | ✅ 400+ | Product |
| **Hour Logging** | 100+ hours submitted | ✅ 75+ | Product |
| **Nonprofit Feedback** | 80%+ rate as "useful" | ✅ 70%+ | Support |
| **Fraud Detection** | <5% false positives | ✅ <10% | QA |
| **COPPA Compliance** | 0 violations detected | ✅ 0 | Legal |
| **FERPA Compliance** | All school data access logged | ✅ 100% audit trail | Legal |
| **Retention** | 30% of students active >2 weeks | ✅ 20%+ | Product |

**Gate Decision:**
- 80%+ metrics met → **APPROVE Stage 2 fundraising** ($100–200K round)
- <80% metrics → **iterate Stage 1** (4 more weeks, re-evaluate)
- If any metric fails (COPPA, FERPA) → **pause, fix, re-test**

---

## Dependencies & Blockers

**Critical Path (must not slip):**

1. **Legal finishes T&S (Week 1)** → signup flow can't test without it
2. **Legal finishes DUA (Week 7)** → school testing can't proceed without it
3. **Education recruits schools (Week 9)** → need real schools for Sprint 3 testing
4. **Backend builds age validation (Week 2)** → blocks student signup
5. **Frontend builds fraud review UI (Week 5)** → blocks admin testing

**If any critical path item slips:**
- T&S slip → push signup flow start to Week 2 (recoverable)
- DUA slip → push school verification to Week 8 (2-week risk)
- School recruitment slip → use staff as testers (higher risk)
- Backend slip → frontend waits (schedule padding built in)

---

## Team Roles & Responsibilities

| Role | Person | Responsibilities |
|------|--------|---|
| **Founder/CEO** | [Akbar] | Product decisions, school recruitment, fundraising prep, overall direction |
| **Backend Lead** | [Hire or assign] | API endpoints, database, auth, fraud detection integration |
| **Frontend Lead** | [Hire or assign] | Signup flows, dashboards, school admin panel, responsive UI |
| **Legal Lead** | [External or internal] | T&S, COPPA compliance, FERPA DUA, school agreements |
| **Education Lead** | [Hire or assign] | School recruitment, pilot partnerships, onboarding |
| **QA Contractor** | [Freelance] | Manual testing, regression, edge cases (3 months contract) |
| **Support Lead** | [Founder or hire] | Playbook, school training, incident response |

**Hiring Critical Path:**
- Week 1: Contract QA (start testing by Week 4)
- Week 1: Engage legal (T&S work)
- Week 2: Hire/assign backend lead (must start Week 1)
- Week 2: Hire/assign frontend lead (must start Week 1)
- Week 3: Hire/assign education lead (school recruitment)

---

## Day 1 Checklist (After Board Vote)

**Immediately (Day 1–2):**
- [ ] Board vote on 15 decisions (90 min meeting)
- [ ] Capture all votes in DECISION_VOTING_WORKSHEET
- [ ] Board chair signs decision summary
- [ ] Founder distributes decisions to all teams

**Week 1 Actions:**

**Founder:**
- [ ] Confirm budget authority ($30K personal capital)
- [ ] Draft founder commitment letter (to team: "We're going 12 weeks")
- [ ] Identify 5 potential Houston schools (email reach-out)
- [ ] Confirm backend + frontend lead assignments
- [ ] Engage legal firm for T&S + DUA ($5–10K budget)

**Legal:**
- [ ] Start COPPA T&S drafting (due Week 1 Friday)
- [ ] Start FERPA DUA template (due Week 7 Friday)
- [ ] Review parental consent form
- [ ] Set weekly sync with founder (Tuesdays)

**Backend Lead:**
- [ ] Clone repo, set up dev environment
- [ ] Review existing code (student_service_api_routes.py, volunteer_fraud_detection.py)
- [ ] Create Sprint 1 branch (feature/sprint-1-account-model)
- [ ] Define API contracts (signup endpoint, age check endpoint, role routing)
- [ ] Week 1 estimate: Account model backend (3 days)

**Frontend Lead:**
- [ ] Clone repo, set up dev environment
- [ ] Review existing UI patterns (frontend/src/components/)
- [ ] Create Sprint 1 branch (feature/sprint-1-account-model-ui)
- [ ] Design signup flow (Figma wireframes)
- [ ] Week 1 estimate: Signup UI mockup (2 days)

**QA Contractor:**
- [ ] Get repo access, dev environment setup
- [ ] Review existing test suites (tests/, e2e specs)
- [ ] Create test plan for Sprint 1 (account model scenarios)
- [ ] Week 1 estimate: Test case documentation (2 days)

**Education Lead:**
- [ ] Get list of 5 target schools from founder
- [ ] Research schools (size, volunteer program, tech adoption)
- [ ] Draft initial school outreach email
- [ ] Week 1 estimate: Contact 5 schools, schedule calls (3 days)

---

## Weekly Sync Cadence

**Every Monday 9 AM (30 min):**
- Frontend: Sprint progress, blockers, this week's PRs
- Backend: Sprint progress, blockers, this week's PRs
- Legal: T&S/DUA status, any review needed
- Education: School conversations, recruitment status

**Every Tuesday 10 AM (30 min, Legal + Founder only):**
- Legal review of week's decisions
- T&S/DUA progress
- School agreement review

**Every Friday 4 PM (all hands, 30 min):**
- Sprint demo (what shipped this week)
- Next week preview
- Blockers & escalations
- Go/no-go check on timeline

---

## Risk Mitigation

**Risk:** Legal doesn't finish T&S by Week 1  
**Mitigation:** Use generic template, founder approves temporary T&S for pilot schools  
**Backup:** Delay signup testing to Week 2 (acceptable, 1-week buffer built in)

**Risk:** Couldn't recruit 3 schools by Week 9  
**Mitigation:** Use staff/volunteers as test users, add student co-testers from friend network  
**Backup:** Test flow with synthetic data, add real schools Week 11–12 (tight but doable)

**Risk:** Fraud detection has false positive >10%  
**Mitigation:** Admin provides feedback loop (mark "incorrect flag" → ML model learns)  
**Backup:** Lower auto-flag threshold, admin reviews more manually (slower but works)

**Risk:** COPPA/FERPA compliance review flags issues Week 11  
**Mitigation:** Legal reviews weekly (not just at end) → catch issues early  
**Backup:** Pause pilot 1 week for compliance fixes (acceptable if caught early)

**Risk:** Backend/frontend progress diverges (one falls behind)  
**Mitigation:** Weekly sync, clear API contracts defined Sprint 1 (no surprises)  
**Backup:** Founder can code if needed (can unblock frontend 2–3 days)

---

## Success Definition

**Stage 1 Success = Pilot Launch + Positive Metrics**

By Week 12 (end of Q4 2026):
- ✅ 3–5 Houston schools active on platform
- ✅ 500+ student signups
- ✅ 100+ hours submitted
- ✅ Nonprofit feedback positive (80%+ "useful")
- ✅ 0 COPPA/FERPA violations
- ✅ Code pushed to production (not just dev)
- ✅ Support team trained + monitoring live

**Gate Outcome:**
- Board reviews metrics (Week 14, mid-January 2027)
- If 80%+ targets met: **APPROVE Stage 2** ($100–200K raise, 10–20 schools, pricing/payments)
- If <80% targets: **iterate** (extend Stage 1 4 more weeks) or **pivot** (rethink scope)

---

## Build Culture (How We Ship)

**Definition of Done (every pull request):**
- ✅ Code reviewed (2+ reviewers, no "LGTM" solo approvals)
- ✅ Tests passing (unit + integration)
- ✅ No TypeScript errors (`npm run build` succeeds)
- ✅ Privacy check passes (`./privacy_check.sh` passes)
- ✅ Mobile responsive (tested on phone)
- ✅ Accessibility (keyboard nav works)
- ✅ Docs updated (README, API docs if needed)
- ✅ Deployed to staging, tested manually by founder/product

**No half-measures:** If any criterion fails, don't merge. Ever.

**Speed without recklessness:** Tight timeline, but quality non-negotiable.

---

## Go Date: Week 12, Launch Day

**Week 12 Friday (mid-December 2026):**
- [ ] All Stage 1 features shipped to production
- [ ] 3–5 schools fully onboarded (admins trained, students verified)
- [ ] Monitoring live (Sentry, health dashboard)
- [ ] Support team on standby (email, Slack)
- [ ] Founder + education lead at school launch events (celebrate with schools)
- [ ] Press release optional (but good timing before new year)

**Week 13–14 (monitoring & metrics):**
- [ ] Daily metric reviews (student signups, hour submissions, errors)
- [ ] Weekly school check-ins (are teachers happy? any issues?)
- [ ] Weekly team syncs (what's working? what's breaking?)
- [ ] Iterate fast if bugs found (48-hour fix target)

**Week 14 (end of pilot, board gate decision):**
- [ ] Board meeting: review 8 success metrics
- [ ] Decision: Stage 2 approval or extend Stage 1?
- [ ] If approved: begin Stage 2 fundraising + sprint planning

---

## Financial Summary (Stage 1)

| Item | Cost | Source |
|------|------|--------|
| Founder time (0.5 FTE, no salary) | $0 | Sweat equity |
| Backend engineer (3 months contract) | $12–15K | Founder capital |
| Frontend engineer (3 months contract) | $12–15K | Founder capital |
| QA contractor (3 months) | $2–3K | Founder capital |
| Legal (T&S, DUA, agreements) | $5–8K | Founder capital |
| Infrastructure (server, email, LLM) | $3–5K | Founder capital |
| **Total Stage 1** | **$34–46K** | **Founder-funded** |

**Budget buffer:** $30K available. Plan for $40K spend. Stretch at $50K (tight but doable).

**If budget runs short:** Reduce contractor scope (do manual testing instead of hired QA), delay legal review (founder does basic review), self-host infrastructure (save $2K).

---

## Next Document: Stage 2 Roadmap (After Pilot Metrics)

Once Stage 1 metrics are clear (Week 14):
- Board approves Stage 2 ($100–200K fundraising)
- Build plan for 10–20 schools (pricing, payments, geographic expansion)
- Timeline: Q1–Q2 2027

---

**Ready to Build.** Ship in 12 weeks.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/unified_build_manifest_2026_07_22
