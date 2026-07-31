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

## Week 2: Phase 2 Attorney Engagement (Aug 8-14)

### Monday Aug 11 (Day 12)
- Schedule 2-hour attorney consultation ($500-800)
- Prepare documents:
  - ToS Section 7 (current draft from framework)
  - Privacy Policy Section 8 (current draft)
  - All wallet disclaimers (from framework)
  - Defense memo template

### Wednesday Aug 13 (Day 14)
- Attorney review meeting
- Get explicit sign-off on:
  - IRS §170(f)(8) compliance
  - User acknowledgment flow
  - Exact language for disclaimers

### Thursday Aug 14 (Day 15)
- Incorporate attorney feedback
- Update ToS, Privacy, disclaimers
- Document changes in DECISIONS.md

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
| Phase 2 attorney approval | Yes/No | Pending | Aug 13 decision |

---

## Cost Breakdown

| Item | Cost | Date |
|------|------|------|
| Attorney review (2hr) | $500-800 | Aug 11-13 |
| S3 storage (26GB, 1 month) | $0.60 | Aug 31 |
| S3 egress (100GB, 1 month) | $9 | Aug 31 |
| Total | ~$510-810 | Month |

---

## Decision Gates

**Aug 7 (Day 7):** Phase 1 quality assessment
- If ✅: Proceed to Phase 2
- If ❌: Debug signals, delay Phase 2

**Aug 14 (Day 15):** Attorney approval
- If ✅: Proceed with Phase 2 build
- If ⚠️: Revise language, retry
- If ❌: Reassess wallet design

**Aug 25 (Day 25):** Phase 2 QA sign-off
- If ✅: Ready for staging deployment
- If ❌: Extend QA window

**Aug 30 (Day 30):** Month review
- Final metrics report
- Lessons learned
- Plan Phase 2 production deployment (Sept)

