# Post-Meeting Implementation Tracker
## Board Meeting July 22, 2026

**Purpose:** After board votes on 15 decisions, this tracker assigns implementation owners, deadlines, and success metrics for each decision.

**When to use:** Immediately after board meeting concludes. For each approved decision, identify owner + confirm deadline.

---

## Implementation Timeline Phases

| Phase | Timeline | Approvals | Focus |
|-------|----------|-----------|-------|
| **Phase A: Legal & Compliance** | Days 1–14 | Legal lead approval | Draft policies, insurance quotes, DUAs |
| **Phase B: Product Setup** | Days 15–30 | Product lead approval | Feature development, database changes |
| **Phase C: Operational Readiness** | Days 31–60 | Operations lead approval | Staff training, process documentation, supplier vetting |
| **Phase D: Pilot Launch** | Days 61–90 | Founder + Board approval | Launch to 1–3 schools, monitor, adjust |

---

## PHASE A: LEGAL & COMPLIANCE (Days 1–14)

### Decision 1: Student Account Model → Legal Framework

**Approved Option:** [Board chose: _______________________]

**Legal Deliverables (Days 1–7):**

| Deliverable | Owner | Due | Status | Notes |
|-------------|-------|-----|--------|-------|
| COPPA Terms of Service (separate <13 vs 13+) | Legal | Day 5 | ⬜ | Draft + board review |
| Parental consent form (if parent-dependent) | Legal | Day 5 | ⬜ | Template ready |
| FERPA DUA (if school-verified) | Legal | Day 7 | ⬜ | Ready for pilot schools |

**Success Metric:** Legal review completed; policies aligned with Decision 1 + Decision 6 (age).

**Owner:** [Legal Counsel Name] | **Approval Gate:** [Board Chair] | **Timeline:** Day 7

---

### Decision 6: Minimum Student Age → Age Verification Logic

**Approved Option:** [Board chose: _______________________]

**Product Deliverables (Days 1–7):**

| Deliverable | Owner | Due | Status | Notes |
|-------------|-------|-----|--------|-------|
| Age verification requirements (by state) | Legal + Product | Day 3 | ⬜ | Research state FLSA limits |
| Signup flow: age gating logic | Product | Day 7 | ⬜ | Block if <minimum age |
| Testing plan: age verification edge cases | QA | Day 10 | ⬜ | Test <min, =min, >min ages |

**Success Metric:** Age gating enforced; no underage signups possible; matches Decision 1 + 12 (verification).

**Owner:** [Product Lead Name] | **Approval Gate:** [Legal] | **Timeline:** Day 10

---

### Decision 2: AI Assistant Timing → Defer

**Approved Option:** [Board chose: Post-pilot]

**Action Item (Day 1):**

| Item | Owner | Due | Status |
|------|-------|-----|--------|
| **Document deferral rationale** | Founder | Day 1 | ⬜ |
| Explain to team: why post-pilot (P10: human-in-command) | Communications | Day 2 | ⬜ |

**Success Metric:** Team understands deferral logic; no AI assistant work scheduled in pilot sprint.

**Owner:** [Founder] | **Timeline:** Day 2

---

### Decision 3: Fraud Detection → Admin Review Process

**Approved Option:** [Board chose: _______________________]

**Operational Deliverables (Days 1–14):**

| Deliverable | Owner | Due | Status | Notes |
|-------------|-------|-----|--------|-------|
| Admin review UI mockups | Product | Day 7 | ⬜ | Flagged submissions queue |
| Admin process documentation | Operations | Day 10 | ⬜ | How to review/dismiss/resolve flags |
| Fraud detection unit tests (12+ cases) | QA | Day 14 | ⬜ | Test each detection method |
| Database queries: fraud flag retrieval | Engineering | Day 5 | ⬜ | Query optimization for review UI |

**Success Metric:** Admin can review flagged submissions in <30 sec per flag; process clear; tests passing.

**Owner:** [Product Lead Name] | **Approval Gate:** [QA] | **Timeline:** Day 14

---

### Decision 5: Pricing Model → Revenue Model Structure

**Approved Option:** [Board chose: _______________________]

**Legal + Finance Deliverables (Days 1–14):**

| Deliverable | Owner | Due | Status | Notes |
|-------------|-------|-----|--------|-------|
| IRS UBI ruling request (if freemium) | Tax | Day 3 | ⬜ | Submit to IRS for determination |
| Cost allocation model (if B2B + 501(c)(3)) | Finance | Day 7 | ⬜ | How overhead split between arms |
| LLC formation docs (if B2B approved) | Legal | Day 10 | ⬜ | Separate entity, ownership clear |
| Revenue model financial projections | Finance | Day 14 | ⬜ | Year 1–3 scenarios |

**Success Metric:** Tax treatment clarified; if hybrid, LLC formation complete; financial model approved by board.

**Owner:** [Finance Lead Name] | **Approval Gate:** [Tax] + [Board] | **Timeline:** Day 14

---

### Decision 9: Donor Profiles → Tax Receipt Strategy

**Approved Option:** [Board chose: _______________________]

**Deliverables (Days 1–14):**

| Deliverable | Owner | Due | Status | Notes |
|-------------|-------|-----|--------|-------|
| Dual profile data model | Engineering | Day 3 | ⬜ | Work/personal profiles linked to same user |
| Tax receipt format (separate lines for work/personal) | Finance | Day 5 | ⬜ | Year-end receipt template |
| DAF platform coordination (Fidelity, Vanguard) | Founder | Day 14 | ⬜ | Initial conversations on profile sync |

**Success Metric:** Profiles linked to user; tax receipts separate by profile; DAF platforms aware of new capability.

**Owner:** [Finance Lead Name] | **Approval Gate:** [Founder] | **Timeline:** Day 14

---

### Decision 10: Revenue Model → Firewall Documentation

**Approved Option:** [Board chose: _______________________]

**Legal + Board Deliverables (Days 1–14):**

| Deliverable | Owner | Due | Status | Notes |
|-------------|-------|-----|--------|-------|
| P7.1 Stewardship amendment (if hybrid approved) | Legal | Day 5 | ⬜ | B2B firewall language |
| Board vote on P7.1 amendment | Board Chair | Day 10 | ⬜ | Formal approval of amendment |
| STEWARDSHIP.md updated + re-sign-offs | Board Chair | Day 14 | ⬜ | Amendment published; all signers ✅ |
| B2B customer evaluation criteria | Founder | Day 14 | ⬜ | Which customers align with mission/firewall? |

**Success Metric:** P7.1 amendment adopted; firewall formalized in governance; B2B customer criteria vetted by board.

**Owner:** [Legal] + [Board Chair] | **Approval Gate:** [Board] | **Timeline:** Day 14

---

### Decision 11: Volunteer Liability → Insurance & Waiver

**Approved Option:** [Board chose: Shared liability]

**Legal + Finance Deliverables (Days 1–14):**

| Deliverable | Owner | Due | Status | Notes |
|-------------|-------|-----|--------|-------|
| E&O insurance quotes (3 providers) | Finance | Day 7 | ⬜ | $20–30K/year estimates |
| Volunteer liability waiver (nonprofit indemnifies Daanaa) | Legal | Day 10 | ⬜ | Ready for nonprofit signature |
| Insurance policy recommendation | Finance | Day 14 | ⬜ | Which carrier + coverage limits? |
| Insurance binding authorization | Board Chair | Day 14 | ⬜ | Board approval to purchase |

**Success Metric:** Insurance quotes compared; nonprofit waiver drafted; policy recommended to board.

**Owner:** [Finance Lead Name] | **Approval Gate:** [Board] | **Timeline:** Day 14

---

### Decision 12: Volunteer Verification → DUA + Vendor Vetting

**Approved Option:** [Board chose: _______________________]

**Legal + Vendor Deliverables (Days 1–14):**

| Deliverable | Owner | Due | Status | Notes |
|-------------|-------|-----|--------|-------|
| FERPA Data Use Agreement (DUA) template | Legal | Day 7 | ⬜ | Ready for school signature |
| Third-party vendor vetting (SOC 2, GDPR) | IT Security | Day 10 | ⬜ | If vendor option approved, audit them |
| Identity verification process (school or vendor) | Product | Day 14 | ⬜ | UX flow for signup verification |

**Success Metric:** DUA ready for schools; vendor vetted if used; verification flow UX complete.

**Owner:** [Legal] | **Approval Gate:** [Board] + [Education Partner] | **Timeline:** Day 14

---

### Decision 13: Data Retention → Deletion Pipeline

**Approved Option:** [Board chose: Hybrid (7-yr PII, ∞ aggregates)]

**Legal + IT Security Deliverables (Days 1–14):**

| Deliverable | Owner | Due | Status | Notes |
|-------------|-------|-----|--------|-------|
| P2.1 Stewardship amendment (if hybrid approved) | Legal | Day 5 | ⬜ | Data retention policy language |
| Data retention policy (published, public) | Legal + IT | Day 7 | ⬜ | Deletion timeline + process |
| Deletion request process (GDPR/CCPA/COPPA compliant) | IT Security | Day 10 | ⬜ | Respond to requests in <30 days |
| Automated deletion pipeline (test run) | Engineering | Day 14 | ⬜ | 7-year purge job, ready to run |

**Success Metric:** Policy published; deletion request process live; automated pipeline tested; ready to deploy.

**Owner:** [IT Security Lead] | **Approval Gate:** [Legal] + [Board] | **Timeline:** Day 14

---

### Decision 14: Board Governance → COI Policy + Amendment

**Approved Option:** [Board chose: _______________________]

**Board + Legal Deliverables (Days 1–14):**

| Deliverable | Owner | Due | Status | Notes |
|-------------|-------|-----|--------|-------|
| P7.2 Stewardship amendment (governance firewall) | Legal | Day 5 | ⬜ | Board independence language |
| Formal Conflict of Interest Policy (written) | Legal | Day 7 | ⬜ | Annual disclosures, recusal process |
| Board member annual disclosure forms | Board Chair | Day 14 | ⬜ | Each member completes + signs |
| Form 990 Schedule O draft (COI policy disclosure) | Finance | Day 14 | ⬜ | For next 990 filing |

**Success Metric:** COI policy adopted; all board members signed disclosures; Form 990 ready for next filing.

**Owner:** [Board Chair] + [Legal] | **Approval Gate:** [Board] | **Timeline:** Day 14

---

### Decision 15: Insurance & Risk → Comprehensive Coverage Plan

**Approved Option:** [Board chose: _______________________]

**Finance Deliverables (Days 1–14):**

| Deliverable | Owner | Due | Status | Notes |
|-------------|-------|-----|--------|-------|
| Year 1 insurance budget ($10–15K) | Finance | Day 3 | ⬜ | Confirmed in operations budget |
| Insurance policy quotes (GL, E&O, Cyber optional) | Finance | Day 7 | ⬜ | 3 providers compared |
| Incident response plan (breach notification, forensics) | IT Security + Legal | Day 10 | ⬜ | Document required by insurance |
| Insurance policies bound + delivered | Finance | Day 14 | ⬜ | Certificates of insurance + policy PDFs |

**Success Metric:** Year 1 insurance active; incident response plan documented; certificates on file.

**Owner:** [Finance Lead Name] | **Approval Gate:** [Board] | **Timeline:** Day 14

---

## PHASE B: PRODUCT SETUP (Days 15–30)

### Decision 1–7: Core Feature Implementation

**Sprint 1 (Days 15–30):**

| Feature | Owner | Due | Status |
|---------|-------|-----|--------|
| Account model (parent/student/tiered) | Product | Day 30 | ⬜ |
| Age gating (by state FLSA limits) | Product | Day 30 | ⬜ |
| Hour constraints (8h/day max enforcement) | Product | Day 30 | ⬜ |
| Fraud detection (tiered review admin UI) | Product | Day 30 | ⬜ |
| Nonprofit messaging (student-centric first) | Communications | Day 30 | ⬜ |
| Donor profiles (work/personal separation) | Engineering | Day 30 | ⬜ |

**Success Metric:** All core features built; code reviewed; ready for QA sprint (Days 31–60).

**Owner:** [Product Lead Name] | **Approval Gate:** [Engineering Lead] | **Timeline:** Day 30

---

## PHASE C: OPERATIONAL READINESS (Days 31–60)

### Staff Training + Process Documentation

| Process | Owner | Due | Status | Notes |
|---------|-------|-----|--------|-------|
| Nonprofit admin training (dashboard, approvals) | Operations | Day 45 | ⬜ | Hands-on walkthrough |
| School admin training (student verification, reports) | Operations | Day 45 | ⬜ | If school verification path chosen |
| Fraud detection admin training (review + dismiss flags) | Operations | Day 45 | ⬜ | Reduce false positives |
| Support playbook (common questions, escalation) | Support | Day 60 | ⬜ | For launch readiness |

**Success Metric:** All staff trained; operations manual complete; ready to launch.

**Owner:** [Operations Lead] | **Timeline:** Day 60

---

## PHASE D: PILOT LAUNCH (Days 61–90)

### Pilot School Launch (3–5 schools, Houston area)

| Milestone | Owner | Due | Status | Notes |
|-----------|-------|-----|--------|-------|
| School recruitment (3 LOIs signed) | Education + Founder | Day 75 | ⬜ | DUA signed; tech setup complete |
| Student signup (target: 500 students) | School | Day 85 | ⬜ | Teachers/admins activate students |
| Volunteer submissions (target: 100+ hours logged) | Students | Day 90 | ⬜ | Monitor data quality, fraud flags |
| Nonprofit feedback (post-pilot survey) | Support | Day 90 | ⬜ | What worked? What didn't? |
| Board review (pilot results) | Founder + Board | Day 90 | ⬜ | Go/no-go decision for expansion |

**Success Metric:** 3+ schools launched; 500+ students, 100+ hours submitted, <5% fraud flags, nonprofits positive feedback.

**Owner:** [Founder] + [School Lead] | **Approval Gate:** [Board] | **Timeline:** Day 90

---

## Decision-Specific Success Metrics

| Decision | Success Metric | Measurement | By Day |
|----------|---|---|---|
| **1: Account Model** | Signup flow works; no COPPA violations | 0 compliance issues in pilot | 90 |
| **2: AI Assistant** | Deferred (not scheduled); team aware of post-pilot plan | No AI assistant sprints in pilot | 7 |
| **3: Fraud Detection** | Admin reviews flags in <30 sec; <10% false positives | Time + accuracy metrics | 60 |
| **4: Geographic Expansion** | Pilot successful in Houston; selective plan approved | Board approval for expansion plan | 90 |
| **5: Pricing Model** | Revenue model operational; first school payments collected | $X collected from schools | 90 |
| **6: Minimum Age** | Age gating enforced; 0 underage signups | Audit log: all signups >= min age | 90 |
| **7: Hour Constraints** | 8h/day limit enforced; students protected | 0 submissions >8h/day (blocked) | 90 |
| **8: Communications** | Student-centric messaging resonates; school adoption | School feedback positive | 90 |
| **9: Donor Profiles** | Dual profiles working; tax receipts separate | Year-end receipt test pass | 90 |
| **10: Revenue Model** | B2B firewall documented; first corporate conversation | 1+ B2B prospect in pipeline | 90 |
| **11: Liability** | Insurance active; waivers signed by nonprofits | 100% of nonprofits have signed waiver | 90 |
| **12: Verification** | School verification working; <1% fraud rate attributed to identity spoofing | Fraud flag analysis | 90 |
| **13: Data Retention** | Deletion pipeline tested; compliant with GDPR/CCPA/COPPA | Test run: 1 deletion request processed <30 days | 60 |
| **14: Board Governance** | COI policy adopted; all board members signed disclosures | 100% board member compliance | 14 |
| **15: Insurance** | Coverage active; incident response plan ready | Certificates of insurance on file | 14 |

---

## Implementation Owners Checklist

**To complete immediately after board meeting:**

```
ASSIGN OWNERS FOR EACH DECISION:

Decision 1 (Account Model):
  Legal deliverables: ________________________
  Product deliverables: ________________________
  
Decision 2 (AI Assistant):
  Owner (defer): ________________________
  
Decision 3 (Fraud Detection):
  Owner: ________________________
  
Decision 4 (Geographic Expansion):
  Owner: ________________________
  
Decision 5 (Pricing Model):
  Legal owner: ________________________
  Finance owner: ________________________
  
Decision 6 (Minimum Age):
  Owner: ________________________
  
Decision 7 (Hour Constraints):
  Owner: ________________________
  
Decision 8 (Communications):
  Owner: ________________________
  
Decision 9 (Donor Profiles):
  Owner: ________________________
  
Decision 10 (Revenue Model):
  Legal owner: ________________________
  Finance owner: ________________________
  
Decision 11 (Liability):
  Legal owner: ________________________
  Finance owner: ________________________
  
Decision 12 (Verification):
  Legal owner: ________________________
  Product owner: ________________________
  
Decision 13 (Data Retention):
  Legal owner: ________________________
  IT owner: ________________________
  
Decision 14 (Board Governance):
  Board chair: ________________________
  Legal owner: ________________________
  
Decision 15 (Insurance):
  Finance owner: ________________________
```

---

## Communication & Kickoff

**Day 1 Actions:**

- [ ] Board chair sends decision summary to all implementers
- [ ] All-hands kickoff meeting (30 min): explain 15 decisions + 90-day roadmap
- [ ] Each owner confirms deadline + commits to checklist
- [ ] Slack channel #board-decisions-2026-07-22 created (updates + blockers)

**Weekly Check-ins (Days 1–90):**

- [ ] Monday: sync all Phase A leads (legal, compliance)
- [ ] Wednesday: sync all Phase B leads (product, engineering)
- [ ] Friday: board update email (1 sentence per decision: status + blocker?)

**Board Review Meetings:**

- [ ] Day 14: Phase A complete (legal, compliance, insurance)
- [ ] Day 30: Phase B complete (product, data model)
- [ ] Day 60: Phase C complete (operations, training)
- [ ] Day 90: Phase D results (pilot data, go/no-go decision)

---

## Final Notes

**This is a 90-day execution plan.** Each decision has concrete deliverables, owners, and success metrics. Track daily. Report blockers immediately (don't wait for weekly sync).

**If any deliverable slips past deadline:**
1. Owner flags blocker in Slack #board-decisions-2026-07-22
2. Related owners notified (downstream impact?)
3. Board chair escalates if necessary

**Success = all 15 decisions executed on-time, legally compliant, with positive pilot feedback by Day 90.**

---

**Approved by:** [Board Chair Signature] Date: _________  
**Implementation Lead:** [Founder/Operations Lead] Date: _________

---

**Next: Distribute this tracker to all owners. Day 1 kickoff scheduled for: _______________**
