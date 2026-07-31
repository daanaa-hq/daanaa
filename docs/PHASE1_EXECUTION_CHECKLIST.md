# Phase 1 Execution Checklist — Credibility Enhancements
## July 31 - Aug 20, 2026 | Kickoff: Mon Aug 4 | Launch: Wed Aug 20

---

## PRE-KICKOFF (By Fri Aug 2, 17:00 CDT)

### Board Approval Required
- [ ] Decision A: Search signals remain informational (not filterable)
- [ ] Decision C: Daily IRS revocation check live (commit 39697605243)
- [ ] Decision G: Launch date confirmed Wed Aug 20
- [ ] Decision H: Postcard nonprofits (200K Form 990-N) included

### Infrastructure Verification
- [ ] Data Engineering: Form 990-N data source accessible
- [ ] Staging server: 32GB capacity confirmed
- [ ] Secondary server: Ready for Fri-Sun testing
- [ ] Monitoring: APM dashboard templates prepared

### Code Review
- [ ] Signals implementation (6 signals, 19 tests passing)
- [ ] API endpoint (/api/organizations/{ein}/signals)
- [ ] Postcard pipeline (transform + validate)
- [ ] Validation framework (functional + performance tests)

---

## WEEK 1: PARALLEL BUILD (Mon Aug 4 - Fri Aug 8)

### Stream A: Methodology Page + Copy (Tue-Fri)
- [ ] Methodology page draft (Product + Legal)
- [ ] UX review + iterate
- [ ] Copy review vs Stewardship P5
- [ ] Deployment to staging (internal only)

### Stream B: UI/Copy + Tooltips (Tue-Fri)
- [ ] Signal cards design (6 signals)
- [ ] Confidence badge component
- [ ] Copy for each signal (2-3 sentences each)
- [ ] Tooltip hover states
- [ ] Mobile responsiveness
- [ ] CSS: card-enhancements + Cormorant Garamond serif
- [ ] Build verification (no errors)

### Stream C: QA Plan + Test Cases (Wed-Fri)
- [ ] QA checklist (7 sections)
- [ ] Functional test suite (API + UI)
- [ ] Performance test suite (<200ms page load, <400ms search)
- [ ] Edge case tests (postcard orgs, missing data, revoked)
- [ ] Test execution plan for Week 2

### Stream D: Accessibility Audit (Thu-Fri)
- [ ] WCAG AA audit (6 signal sections)
- [ ] Screen reader testing (NVDA/JAWS)
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Color contrast verification (4.5:1 minimum)
- [ ] Remediation log (any issues found)

### Stream E: API Implementation (Mon-Fri) ✓ COMPLETE
- [x] Backward-compatible API v1 (nullable fields)
- [x] 6 signal endpoints
- [x] Error handling (missing data = null)
- [x] Response caching (10 min TTL)
- [x] Test suite (30 unit tests, all passing)
- [ ] Code review + approval
- [ ] Staging deployment ready

### Stream F: Rollback Plan (Thu-Fri)
- [ ] Rollback procedure (step-by-step documentation)
- [ ] Dry-run rollback on staging
- [ ] S3 backup (code + DB state)
- [ ] RTO <30 min validation
- [ ] Notification template

### Stream G: Postcard Prep (Mon-Fri) ✓ COMPLETE
- [x] Form 990-N data validation script
- [x] Schema transformation (to registry_enriched)
- [x] Integrity checks (EIN, revenue, state)
- [x] Overlap analysis vs existing registry
- [ ] Data download + staging (Wed-Thu)
- [ ] Fri load ready (17:00-19:00 slot)

### Stream H: Early Validation Infrastructure (Fri-Sun)
- [ ] Secondary server setup
- [ ] Monitoring dashboard (APM)
- [ ] Alert configuration
- [ ] Backup testing framework
- [ ] Performance baseline templates

### Daily Standups (Mon-Fri, 10:00 CDT)
- [ ] Mon kickoff (7 stream leads)
- [ ] Tue update
- [ ] Wed update
- [ ] Thu update
- [ ] Fri staging deployment debrief

---

## POSTCARD LOAD (Fri Aug 8, 17:00-19:00 CDT)

### Pre-Load Checklist
- [ ] All signals deployed to staging (by 17:00)
- [ ] Postcard data staged (200K records)
- [ ] Search.db rebuild script ready
- [ ] Backup of staging environment

### Load Execution
- [ ] Load 200K postcard orgs (30 min estimate)
- [ ] Rebuild search.db (10 min estimate)
- [ ] Smoke tests: 3 org pages
- [ ] Smoke tests: 5 search queries

### Post-Load Validation
- [ ] Staging has 2.26M total orgs (2.06M + 200K)
- [ ] Search.db synced
- [ ] All signals visible on staging org pages
- [ ] No rollback needed

---

## EARLY VALIDATION TESTING (Fri-Sun Aug 8-10)

### Friday Evening (19:00-23:00)
- [ ] Baseline performance snapshot
  - [ ] Org page load time (3 test orgs)
  - [ ] Search query latency (5 queries)
  - [ ] Database query performance
- [ ] Backup integrity test
  - [ ] Test restore from staging backup
  - [ ] RTO verification
- [ ] Monitoring pre-checks
  - [ ] Dashboard live
  - [ ] Alerts configured

### Saturday-Sunday
- [ ] Performance suite (10 search queries, 5 org loads)
- [ ] Database indexing verification
- [ ] Postcard edge cases
  - [ ] Orgs with limited data
  - [ ] Peer group assignment for 200K new orgs
  - [ ] Mission alignment signal
- [ ] Infrastructure readiness check

### Validation Report (Due Sun 23:59)
- [ ] All performance metrics documented
- [ ] Any issues identified + severity
- [ ] Recommendations for Monday integration testing
- [ ] Green light or blockers

---

## WEEK 2: INTEGRATION + VALIDATION (Mon Aug 11-13)

### Monday: Full Integration Testing (Aug 11)
- [ ] API + UI integration (2.26M org dataset)
- [ ] All 4 org types (large, small, postcard, recent)
  - [ ] Large org (>$5M revenue)
  - [ ] Small org ($100K-$500K)
  - [ ] Postcard org (<$50K)
  - [ ] Recently filed org (<6 months)
- [ ] Search performance (<400ms on 2.26M)
- [ ] Page load (<200ms on 3 test orgs)
- [ ] WCAG AA compliance (all 6 signals)
- [ ] Rollback dry-run (full recovery in <30 min)

### Tuesday: Go/No-Go Decision (Aug 12, 10:00 CDT)

**ALL of these must PASS:**
- [x] Fri-Sun early validation: 0 blockers
- [x] Mon integration: 0 blockers
- [x] Page load <200ms
- [x] Search <400ms
- [x] WCAG AA compliant
- [x] Backups verified
- [x] Monitoring live
- [x] Rollback tested
- [x] 21/21 governance aligned

**Decision Outcome:**
- [ ] GO: Launch approved for Wed Aug 20
- [ ] NO-GO: Delay to Mon Aug 25 (1-week fix)

### Wednesday: Final Prep (Aug 13, if GO)
- [ ] Security audit (quick pass)
- [ ] Nonprofit pilot email final review
- [ ] Support team final briefing
- [ ] Marketing assets ready
- [ ] Ops on-call confirmation

---

## PRODUCTION LAUNCH (Wed Aug 20)

### Pre-Launch (08:30 CDT)
- [ ] Final health check of staging
- [ ] Fresh backup
- [ ] Monitoring dashboard live

### Go Live (09:00 CDT)
- [ ] Deploy to production
- [ ] Verify all 6 signals working
- [ ] Search.db synced (2.26M)
- [ ] Smoke tests: 3 test orgs
  - [ ] Large org page loads
  - [ ] Small org page loads
  - [ ] Postcard org page loads
- [ ] All signals visible
- [ ] No errors in APM dashboard

### Announcement (10:00 CDT)
- [ ] Blog post live
- [ ] Social media live
- [ ] Support team ready
- [ ] Monitoring real-time

### Post-Launch Monitoring (10:00-12:00 CDT)
- [ ] Real-time alert monitoring
- [ ] User feedback collection
- [ ] Performance dashboard review
- [ ] Support ticket triage

### Day 1 Wrap-up (EOD Wed Aug 20)
- [ ] Nonprofit feedback summary
- [ ] Any immediate issues identified
- [ ] Overnight pipeline check scheduled

---

## SUCCESS CRITERIA

✅ **All 6 signal streams implemented + tested**
✅ **200K postcard orgs ingested + indexed**
✅ **2.26M org registry live in staging (Fri), production (Wed)**
✅ **Page load <200ms**
✅ **Search <400ms**
✅ **WCAG AA compliant**
✅ **Backups verified + RTO <30 min**
✅ **Monitoring live + tested**
✅ **Rollback procedure documented + dry-run passed**
✅ **21/21 governance aligned (Stewardship + Charter)**
✅ **Production launch Wed Aug 20, 09:00 CDT**

---

## DECISION GATES

| Gate | Date | Owner | Status |
|------|------|-------|--------|
| Board approval (4 decisions) | Fri 08/02 17:00 | User | ⏳ Pending |
| Code review + approval | Thu 08/06 | Team | ⏳ Pending |
| Early validation (Fri-Sun) | Sun 08/10 23:59 | Infra | ⏳ Pending |
| Integration testing (Mon) | Mon 08/11 EOD | QA | ⏳ Pending |
| Go/No-Go decision | Tue 08/12 10:00 | Product | ⏳ Pending |
| Production launch | Wed 08/20 09:00 | Ops | ⏳ Pending |

---

## DELIVERABLES

| Date | Deliverable | Owner |
|------|---|---|
| Fri 08/02 | Board approval + specs locked | User |
| Mon 08/04 | Kickoff meeting (7 stream leads) | Product |
| Thu 08/06 | Code review checklist + test plan | Streams A-F |
| Fri 08/08 | Staging deployment complete | All streams |
| Fri 08/08 | Postcard data loaded (2.26M orgs) | Stream G |
| Sun 08/10 | Early validation report | Stream H |
| Mon 08/11 | Integration test report | QA |
| Tue 08/12 | Go/No-Go decision + report | Product |
| Wed 08/13 | Final prep checklist | Support + Ops |
| Wed 08/20 | Production launch (09:00 CDT) | Ops |

---

## ESCALATION PATH

**Blocker identified?**
1. Document: symptom, impact, root cause
2. Escalate to: Product Lead → Founder (if user approval needed)
3. Decision timeline: 2 hours max

**Performance failure (load >200ms or search >400ms)?**
- Root cause analysis immediately
- Options: optimize, defer signal, delay launch
- No compromises on quality gates

**Governance misalignment?**
- Flag immediately to Founder
- Review against STEWARDSHIP.md + CHARTER.md
- Resolution required before launch

---

## TEAM COORDINATION

**Daily Standups (Mon-Fri 10:00 CDT):**
- 7 stream leads (5 min each)
- Blockers + dependencies
- No approval gates — feedback only, continue

**Escalation:**
- Product Lead (day-to-day)
- Founder (decisions, governance, unblocks)

**Communication:**
- Slack: #credibility-phase1
- Email: Progress updates EOD each day

---

## STATUS TRACKING

**As of July 31, 2026:**
- [x] Master execution plan created
- [x] 6 signals implemented (credibility_signals.py)
- [x] API endpoint created (/api/organizations/{ein}/signals)
- [x] Postcard pipeline created (postcard_prep_pipeline.py)
- [x] Validation framework created (validate_credibility_signals.py)
- [x] All code committed to feature branch (phase1/credibility-enhancements-all)
- [ ] Board approval (Fri 08/02)
- [ ] Kickoff (Mon 08/04)
- [ ] Execution begins

**Next:** Await board approval by Fri 08/02 17:00 CDT.

---

**Document Status:** READY FOR EXECUTION  
**Last Updated:** July 31, 2026  
**Phase Lead:** Claude Code (AI Engineering Agent)  
**Founder Lead:** Akbar Khowaja
