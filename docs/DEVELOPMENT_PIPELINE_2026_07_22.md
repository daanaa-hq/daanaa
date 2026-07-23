# Development Pipeline: Feature Breakdown by Decision
## Board Meeting July 22, 2026

**Current State:** Dashboard V2, notifications, fraud detection engine, student service API, volunteer hours tracking already built.

**Missing:** Account model tiering, age gating, verification integration, data retention pipeline, pricing/payment, B2B features.

---

## Already Built (✅ Committed)

| Feature | Status | Lines | Notes |
|---------|--------|-------|-------|
| Dashboard V2 (3 React pages) | ✅ Complete | 1,600 | NonprofitDashboardV2, Analytics, Directory |
| Volunteer notifications | ✅ Complete | 462 | Email service, duplicate prevention, idempotent |
| Fraud detection engine | ✅ Complete | 270 | 4 detection methods, risk scoring, admin review table |
| Student service API | ✅ Complete | 8 core + 5 new endpoints | Profile, enrollment, disputes |
| Volunteer hours tracking | ✅ Complete | Database + API | Submit, approve/reject, logs |
| Database migrations | ✅ Complete | 3 new migrations | Student service tables, notifications, fraud flags |

---

## Critical Path for Stage 1 (Q4 2026)

**Goal:** Reach 3–5 schools, 500 students, $0–6K pilot revenue

**Must-build features (12-week sprint):**

### Sprint 1 (Weeks 1–3): Account Model + Age Gating

**Decision 1 (Account Model) + Decision 6 (Minimum Age)**

| Feature | Owner | Effort | Dependencies | Notes |
|---------|-------|--------|---|---|
| **Account model UI** | Frontend | 2w | Auth | Signup flow: parent-dependent OR tiered (school) |
| **Age gating logic** | Backend | 1w | DB schema | Block signups <16 years old; log for audit |
| **School verification flow** | Frontend + Backend | 2w | FERPA DUA signed | If school-verified path: schools verify students |
| **Parent consent form** (if needed) | Legal + Frontend | 1w | T&S | COPPA-compliant form for <18 signups |
| **Testing + QA** | QA | 1w | All above | Edge cases: age boundary (16th birthday), school vs parent |
| **Total Sprint 1** | | **7w** | Must complete before pilot launch |

**Acceptance Criteria:**
- ✅ Students 16+ can signup (verified by age)
- ✅ Students <16 see "too young" message (if parent-dependent enabled)
- ✅ School can verify students (if school-verified path chosen)
- ✅ 0 COPPA violations detected

---

### Sprint 2 (Weeks 4–6): Fraud Detection Admin UI + Hour Constraints

**Decision 3 (Fraud Detection Policy) + Decision 7 (Hour Constraints)**

| Feature | Owner | Effort | Dependencies | Notes |
|---------|-------|--------|---|---|
| **Admin fraud review UI** | Frontend | 2w | Fraud detection engine (✅ exists) | Show flagged submissions, dismiss/resolve |
| **Admin review process** | Backend | 1w | fraud_flags table (✅ exists) | Queries, filtering by school/risk level |
| **Hour constraint enforcement** | Backend | 1w | Submission validation | Block submissions >8h/day; show error message |
| **Hour validation UI** | Frontend | 1w | Hour constraint logic | Warn user if entering >8 hours, prevent submit |
| **Testing + QA** | QA | 1w | All above | Test fraud flags, hour blocks, edge cases |
| **Total Sprint 2** | | **6w** | Can run parallel to Sprint 1 |

**Acceptance Criteria:**
- ✅ Admin can review flagged submissions in <30 sec
- ✅ Fraud flags include reason + risk score
- ✅ Students can't submit >8h/day
- ✅ False positives <10% (admin feedback loop)

---

### Sprint 3 (Weeks 7–9): FERPA DUA Integration + School Verification

**Decision 12 (Verification) — School-Mediated Path**

| Feature | Owner | Effort | Dependencies | Notes |
|---------|-------|--------|---|---|
| **School admin panel** | Frontend | 2w | Auth + role-based access | Schools add students, verify age/enrollment |
| **DUA signature workflow** | Backend | 1w | Legal docs signed | School signs DUA before accessing student data |
| **School data export** | Backend | 1w | Student list query | Schools can export their students' submitted hours |
| **FERPA compliance logging** | Backend | 1w | Audit trail | Log all school data access (compliance audit) |
| **Testing + QA** | QA | 1w | All above | FERPA compliance, DUA enforcement |
| **Total Sprint 3** | | **6w** | Parallel to Sprints 1–2 |

**Acceptance Criteria:**
- ✅ Schools can verify their students (yes/no)
- ✅ No student data accessible without DUA signature
- ✅ Audit log shows all school data access
- ✅ 0 FERPA violations

---

### Sprint 4 (Weeks 10–12): Nonprofit Messaging + Launch Polish

**Decision 8 (Communications)**

| Feature | Owner | Effort | Dependencies | Notes |
|---------|-------|--------|---|---|
| **Nonprofit-facing copy** | Communications | 1w | None | Landing page, email templates, admin messaging |
| **Student-centric copy** | Communications | 1w | None | Signup flow, student dashboard messaging |
| **Launch checklist** | Product | 1w | All above | Go-live readiness, monitoring, support docs |
| **Monitoring + dashboards** | DevOps | 1w | Sentry, logs | Error tracking, performance monitoring live |
| **Support playbook** | Operations | 1w | None | Common issues, escalation process |
| **Total Sprint 4** | | **5w** | Final polish |

**Acceptance Criteria:**
- ✅ Copy is student-centric, empowering tone
- ✅ No COPPA/legal violations in messaging
- ✅ Error monitoring live
- ✅ Support team trained

---

## Stage 1 Critical Path Summary

| Sprint | Duration | Features | Dependencies | Owner |
|--------|----------|----------|---|---|
| 1 | 7w | Account model, age gating, parent consent | Legal (T&S, consent form) | Frontend + Backend |
| 2 | 6w (parallel) | Fraud UI, hour constraints | Fraud engine ✅ exists | Frontend + Backend |
| 3 | 6w (parallel) | School admin, DUA, FERPA logging | Legal (DUA template) | Frontend + Backend |
| 4 | 5w | Messaging, monitoring, support | All Sprints 1–3 | All |
| **Total** | **12 weeks** | **MVP ready for 3–5 schools** | **Must ship by Q4 2026** | **1 frontend, 1 backend, 1 QA** |

**Team for Stage 1:** 1 frontend + 1 backend engineer + QA contractor (= junior dev doing testing). Can be done with $20–30K.

---

## Stage 2 Development (Q1–Q2 2027)

**Goal:** Expand to 10–20 schools, add pricing/payments, dual donor profiles

**Sprints 5–8 (16 weeks):**

| Decision | Feature | Effort | Owner | Why |
|----------|---------|--------|-------|-----|
| **5: Pricing** | Payment integration (Stripe) | 3w | Backend | Schools must pay $X/month |
| **5: Pricing** | Billing dashboard (invoices, receipts) | 2w | Frontend | Schools manage subscriptions |
| **9: Donor Accounts** | Head of Household + co-giver data model | 2w | Backend | Store HoH + linked co-givers (spouse, kids, etc.) |
| **9: Donor Accounts** | Household wallet aggregation | 2w | Backend | All co-giver giving pooled; HoH sees total |
| **9: Donor Accounts** | Tax receipt generation (consolidated HoH) | 2w | Backend | Year-end receipt to HoH, includes all co-givers |
| **9: Donor Accounts** | Donor UI (add co-givers, manage roles) | 2w | Frontend | HoH can invite spouse/kids as co-givers |
| **4: Geographic Expansion** | State-specific hour laws | 2w | Backend | Verify hour limits by state |
| **10: Revenue Model** | Freemium vs premium feature gating | 2w | Backend | Premium features locked behind paywall |
| **11: Liability** | Nonprofit liability waiver workflow | 1w | Backend | Nonprofits sign waiver before using |
| **Legal/Compliance** | Data retention policy implementation | 2w | Backend | 7-year PII deletion, compliance logging |
| **Monitoring** | Analytics dashboard (school retention, revenue) | 2w | Frontend | Track metrics for growth |
| **Total Stage 2** | | **20w** | Mixed team | Revenue-dependent features |

**Team for Stage 2:** 1 frontend + 2 backend engineers + QA (= junior dev). Revenue covers salaries.

---

## Stage 3 Development (Q3–Q4 2027)

**Goal:** Compliance complete, 50–100 schools, multi-city expansion, insurance integration

| Decision | Feature | Effort | Owner | Why |
|----------|---------|--------|-------|-----|
| **12: Verification** | Third-party ID verification fallback | 3w | Backend | For non-school students (homeschooled) |
| **12: Verification** | Vendor integration (Socure/Mitek) | 2w | Backend | Connect to age verification service |
| **13: Data Retention** | Automated 7-year PII deletion | 2w | Backend | Batch job, compliance audit trail |
| **13: Data Retention** | Deletion request workflow | 1w | Frontend + Backend | Handle GDPR/CCPA/COPPA deletion requests |
| **14: Board Governance** | Conflict-of-interest attestation system | 1w | Backend | Board members sign annual COI forms |
| **15: Insurance** | Claims/incident reporting workflow | 2w | Frontend + Backend | Nonprofit can file incident claim |
| **15: Insurance** | Breach notification automation | 1w | Backend | Auto-notify affected users <72h |
| **Geographic** | Regional server/CDN optimization | 2w | DevOps | Support multi-city latency requirements |
| **Analytics** | Advanced nonprofit dashboards (per-city, per-nonprofit) | 3w | Frontend | Nonprofits see impact by region |
| **B2B Foundation** | API infrastructure for corporate partners | 2w | Backend | Separate B2B endpoints (future Stage 4) |
| **Total Stage 3** | | **19w** | Mixed team | Compliance + scale |

**Team for Stage 3:** 1 frontend + 2 backend + DevOps + QA. Revenue covers all costs.

---

## Stage 4 Development (2028+)

**Goal:** B2B ESG features, national scale, long-term sustainability

| Feature | Effort | Owner | Why |
|---------|--------|-------|-----|
| **B2B ESG Platform** | 8w | Backend + Frontend | Corporate giving integration, separate product |
| **B2B API** | 4w | Backend | Corporations query orgs, manage donations |
| **B2B Dashboards** | 4w | Frontend | Corporate sponsor sees matching results |
| **Analytics ML** | 4w | Data | Predictive analytics, org success forecasting |
| **National Expansion** | 4w | DevOps | Multi-region infrastructure, compliance per state |
| **AI Assistant** (Decision 2 — finally) | 8w | Backend + Frontend | Nonprofit recommendations, smart discovery |
| **Total Stage 4** | **32w** | Team grows to 5–7 FTE | Revenue sustains all |

---

## Dependency Graph (What Blocks What)

```
Stage 1 Critical Path:
  Legal: COPPA T&S, FERPA DUA, parental consent form
    ↓
  Account Model + Age Gating (Sprints 1)
    ↓ (enables)
  School Verification (Sprint 3)
    ↓ (enables)
  Fraud Detection Admin UI (Sprint 2)
    ↓ (enables)
  Hour Constraints (Sprint 2)
    ↓ (enables)
  Launch readiness (Sprint 4)
    ↓ (enables)
  Stage 1 pilot with 3–5 schools (Q4 2026)

Stage 2 Gates:
  Pilot success (Stage 1) + Stage 1 revenue ✅
    ↓ (enables)
  Payment integration (Stripe) → billing → revenue collection
    ↓ (enables)
  Geographic expansion (state hour laws check)
    ↓ (enables)
  Dual donor profiles (tax compliance)
    ↓ (enables)
  Stage 2 scale to 10–20 schools (Q1–Q2 2027)

Stage 3 Gates:
  Stage 2 revenue ✅ + 10+ school retention ✅
    ↓ (enables)
  Advanced verification (third-party)
    ↓ (enables)
  7-year data deletion pipeline
    ↓ (enables)
  Insurance integration
    ↓ (enables)
  Stage 3 scale to 50–100 schools (Q3–Q4 2027)
```

---

## Engineering Staffing by Stage

| Stage | Timeline | Team | Roles | Cost |
|-------|----------|------|-------|------|
| **1** | Q4 2026 (12w) | 2–3 | 1 Frontend, 1 Backend, 1 QA | $20–30K (contract) |
| **2** | Q1–Q2 2027 (16w) | 3–4 | 1 Frontend, 2 Backend, 1 QA | $50–70K (from revenue) |
| **3** | Q3–Q4 2027 (19w) | 4–5 | 1 Frontend, 2 Backend, 1 DevOps, 1 QA | $100–150K (from revenue) |
| **4** | 2028+ (ongoing) | 5–7 | Full team + data/ML | $250–400K (from revenue) |

**Key assumption:** Founder is "CEO/founder engineer" across all stages (not counted in headcount). Salary comes from reinvested revenue in Stages 2+.

---

## Technology Stack (Current + Planned)

**Already in place:**
- React 19 (frontend)
- TypeScript (type safety)
- Flask + SQLite (API)
- Firebase Auth (authentication)
- Tailwind CSS + Radix UI (design)

**To add (Stages 1–2):**
- Stripe (payments) — Stage 2
- Sentry (error monitoring) — Stage 4 launch
- Plausible Analytics (no-tracking analytics) — Stage 2

**To add (Stages 3–4):**
- Postgres (scale from SQLite) — Stage 3, only if >100K students
- Redis (caching) — Stage 3, if needed
- Kafka/EventBridge (event streaming) — Stage 4 for B2B
- LLM local inference (Qwen2.5-32B) — Already running, keep for cost efficiency

**No changes:** Stay lean. Don't over-engineer. Use Vercel/Railway/Fly.io for hosting (cost ~$50–200/month, scales automatically).

---

## Testing & QA Strategy

**Stage 1 (Lean):**
- Manual QA (junior dev)
- Unit tests for critical paths (age gating, fraud detection, hour limits)
- Schools + founder as beta testers (free pilot feedback)

**Stage 2 (Moderate):**
- Automated integration tests (Playwright) for payment flow
- School admin UI tests
- Performance testing (load test with 10 schools, 5K students)

**Stage 3 (Comprehensive):**
- Full CI/CD pipeline (GitHub Actions)
- Penetration testing (external security firm)
- GDPR/CCPA compliance testing (data deletion, export)
- Load testing (50 schools, 25K students)

**Stage 4 (Enterprise):**
- SOC 2 Type II readiness
- Annual security audit
- Disaster recovery testing

---

## Definition of Done (per sprint)

**All work must meet these criteria before shipping:**

✅ Code reviewed (2+ reviewers)  
✅ Tests passing (unit + integration)  
✅ No TypeScript errors (`npm run build` succeeds)  
✅ Privacy check passes (no PII in logs) (`./privacy_check.sh` passes)  
✅ Mobile responsive (tested on phone)  
✅ Accessibility tested (keyboard nav, screen reader)  
✅ Documentation updated (README, API docs, T&S if legal change)  
✅ Deployed to staging, manually tested by product owner  
✅ Stakeholder (school, nonprofit) approval if affecting their flow  

---

## What We're NOT Building (Intentional Scope Cuts)

**Stage 1–2 excludes:**
- ❌ AI platform assistant (Decision 2 deferred to Stage 4)
- ❌ Comprehensive analytics (basic dashboard only)
- ❌ Mobile app (web-responsive only)
- ❌ White-label solutions
- ❌ Advanced ML recommendations
- ❌ B2B ESG features (Stage 4)

**Why:** Ship fast, validate market, bootstrap to revenue. Add features after proof of concept.

---

## Risk: Can 1 Frontend + 1 Backend + 1 QA Do This?

**Stage 1 (12 weeks): Yes**
- 20 weeks of work, but tight scoping + parallel sprints
- Junior developer can handle QA (learn on job)
- Founder handles product + planning (not coding infrastructure)

**Stage 2 (16 weeks): Tight**
- Need 2 backend engineers for payment + state logic + compliance
- 1 frontend can keep up if spec'd clearly
- Critical: hire good second backend engineer early (Q1 2027)

**Stage 3 (19 weeks): Must hire**
- 4–5 engineers needed for parallel work (verification, deletion pipeline, insurance, analytics)
- DevOps engineer for multi-region infrastructure
- Founder focuses on strategy/fundraising, not coding

**Key:** Hire smart, spec clearly, don't over-engineer. Use libraries, don't build from scratch.

---

## Commit Timeline (Candidate Dates)

**Stage 1 commits (Q4 2026):**
- Week 4 (Oct 25): Account model + age gating first feature commit
- Week 8 (Nov 22): Fraud admin UI + hour constraints
- Week 10 (Dec 6): School verification flow
- Week 12 (Dec 20): Launch to 3 pilot schools

**Stage 2 commits (Q1–Q2 2027):**
- Week 1 (Jan 3): Payment integration (Stripe)
- Week 6 (Feb 7): Billing dashboard
- Week 10 (Mar 7): Dual donor profiles
- Week 14 (Apr 4): Geographic expansion (state hour limits)

**Stage 3 commits (Q3–Q4 2027):**
- Week 1 (Jul 7): Third-party verification integration
- Week 8 (Aug 25): 7-year data deletion pipeline
- Week 12 (Sep 22): Board governance attestation
- Week 16 (Oct 20): Multi-city analytics + insurance integration

---

## Ready to Execute?

**Gating questions before building:**

1. **Do we have 1 backend engineer committed for Stage 1?** (If no, delay start)
2. **Are legal docs (COPPA T&S, FERPA DUA) ready?** (If no, legal blocks account model)
3. **Are 3+ schools ready to pilot?** (If no, we're building in vacuum)
4. **Do we have $20K committed for Stage 1?** (If no, hire engineer later)

**If answers are yes: Start coding immediately. 12-week sprint to pilot.**

---

**Next step:** Assign frontend + backend owners, schedule kickoff standup, start Sprint 1 Week 1.
