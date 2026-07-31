# Phase 1 + Phase 2 Roadmap: 30-Day Plan

**Start:** 2026-07-31 (today)  
**End:** 2026-08-30  
**Phase 1 Status:** LIVE  
**Phase 2 Status:** Attorney review pending

---

## Week 1: Live Monitoring (Aug 1-7)

### Daily Tasks
- ✅ Check Plausible analytics for signal engagement
- ✅ Monitor `/api/organizations/{ein}/signals` endpoint health
- ✅ Watch for any user reports of signal inaccuracy
- ✅ Log observations in DECISIONS.md

### Quality Checks
- Signal accuracy: Random sample of 10 orgs, verify IRS status matches
- Data freshness: Confirm daily IRS sync is running (should see <24h lag)
- Performance: Org pages load <200ms consistently
- Search: No degradation from new website ingestion

### Success Criteria
- 0 critical bugs (signals returning wrong status)
- ≥90% of signals compute successfully
- Page performance stable
- No user complaints about signal accuracy

---

## Week 2: Phase 2 Internal Legal Review (Aug 8-14)

### Monday Aug 11 (Day 12)
- Founder legal review of Phase 2 framework
- Reference materials (already prepared):
  - PHASE2_LITIGATION_RISK_MITIGATION.md (5-layer framework)
  - LEGAL_BOARD_FINAL_REVIEW.md (simulated panel consensus)
  - Defense memo template (§170(f)(8) IRS compliance)
  - Lawsuit scenarios + defenses (3 analyzed)

### Wednesday Aug 13 (Day 14)
- Internal decision on Phase 2 viability
- Review decisions:
  - ✅ APPROVE → Proceed with Phase 2 build
  - ⚠️ REQUEST CHANGES → Revise and recheck
  - ❌ REJECT → Redesign wallet approach

### Thursday Aug 14 (Day 15)
- If approved: Begin Phase 2 implementation
- Document decision in DECISIONS.md
- No external attorney needed (framework pre-validated by simulated panel)

---

## Week 3-4: Phase 2 Preparation & S3 Optimization (Aug 15-30)

### Phase 2 Build (Days 16-25, ~2 weeks)
- [ ] Implement wallet backend (intent logging)
- [ ] Add user acknowledgment flow
- [ ] Build wallet UI (React component)
- [ ] Wire up localStorage for persistence
- [ ] Add export functionality
- [ ] QA testing (5 scenarios)

### S3 Optimization (Days 18-20, parallel, ~2 hours)
- [ ] Create S3 bucket for precompute (if not exists)
- [ ] Modify precompute script to push to S3 instead of local
- [ ] Update droplet deploy to pull from S3 (lazy-load)
- [ ] Test deployment time improvement
- [ ] Verify cost savings (should see ~50% faster deploys)

### Optional: Volunteer Integration (Days 21-30)
- [ ] QA test volunteer interest capture
- [ ] Deploy to production
- [ ] Monitor signup conversion

---

## Metrics to Track

| Metric | Target | Current | Notes |
|--------|--------|---------|-------|
| Signal accuracy | ≥95% | ? | Random sampling |
| API response time | <500ms | 1.4s | Still needs optimization |
| Page load (org) | <200ms | 114ms | ✅ Good |
| Signal endpoint uptime | 99.9% | ? | Check droplet fallback |
| New website coverage | +2,307 | TBD | Verify ingestion complete |
| Phase 2 internal approval | Yes/No | Pending | Aug 14 decision |

---

## Cost Breakdown

| Item | Cost | Date |
|------|------|------|
| Internal legal review | $0 | Aug 11-14 |
| S3 storage (26GB, 1 month) | $0.60 | Aug 31 |
| S3 egress (100GB, 1 month) | $9 | Aug 31 |
| AWS data transfer | $2-5 | Aug 31 |
| Total | ~$12-15 | Month |

---

## Decision Gates

**Aug 7 (Day 7):** Phase 1 quality assessment
- If ✅: Proceed to Phase 2
- If ❌: Debug signals, delay Phase 2

**Aug 14 (Day 15):** Internal legal approval
- If ✅: Proceed with Phase 2 build (framework defensible)
- If ⚠️: Revise language, retry
- If ❌: Reassess wallet design

**Aug 25 (Day 25):** Phase 2 QA sign-off
- If ✅: Ready for staging deployment
- If ❌: Extend QA window

**Aug 30 (Day 30):** Month review
- Final metrics report
- Lessons learned
- Plan Phase 2 production deployment (Sept)

