# v5.0 Peer-Based Taxonomy: Complete Roadmap

**Project**: Daanaa v5.0 Launch  
**Status**: Week 3 Beta → Week 4 Launch → Ongoing Optimization  
**Success Criteria**: All phases documented and ready to execute

---

## Executive Summary

Replace Daanaa's absolute 0-100 scoring system with peer-based financial context. Show each nonprofit how it compares to financially similar organizations (not all nonprofits, which is unfair).

**Timeline**: 
- Weeks 1-2: Build and migrate (COMPLETE ✓)
- Week 3: Beta test with 1% (feedback collection Thu-Fri)
- Week 4: Full launch to 100% (IF metrics ≥80%)
- Week 5+: Optimize and iterate

**Data**: 447,557 orgs scored (21.6% of registry), 1.75M org-years IRS data, 92.5% YoY stability

---

## Phases Overview

### Phase 1: Weeks 1-2 Build ✓ COMPLETE

**Deliverables**:
- merit_scorer_v5_0.py: 447K orgs scored, K=5 clustering, 92.5% YoY stable
- Database migration: 8 new columns in registry_enriched
- enrich_api_responses.py: v5_context enrichment function
- API integration: /api/organizations/<ein> returns v5_context

**Status**: All code committed, tested locally, ready for deployment

**Files**:
- scripts/merit_scorer_v5_0.py
- scripts/enrich_api_responses.py
- scripts/ntee_questionnaire_v5_0.py
- scripts/validate_v5_scores.py
- docs/API_V5_RESPONSE_FORMAT.md
- docs/methodology.md

---

### Phase 2: Week 3 Beta Testing → CURRENT PHASE

**Timeline**: June 12-13, 2026 (Thu-Fri)

**Objectives**:
1. Deploy to 1% of users (deterministic feature flag)
2. Collect feedback on clarity, preference, NTEE accuracy
3. Measure success against thresholds
4. Make go/no-go decision for Week 4 launch

**Feature Flag**:
- useFeatureFlag.ts: Hash-based 1% cohort selection
- Persistent across sessions (localStorage)
- 1.03% users in test (verified)

**What 1% See**:
```
┌─────────────────────────────────┐
│ Financial Context (Beta)        │
│ Donation-Funded Programs        │
│ Percentile: 25 (among 62K)      │
│ Reserves: 3.4 mo vs 11 mo peer  │
│ ████░░░░░░░░░░░ (progress bar)  │
│ CAUTION (health signal)         │
│ [Auto-generated donor copy]     │
└─────────────────────────────────┘
```

**What 99% See**:
- No change (v4 FinancialContext only)

**Feedback Collection**:
- In-app form: 5 questions (clarity, preference, NTEE, comments)
- Server tracking: response times, engagement metrics
- Frontend tracking: scroll depth, time on page

**Success Metrics** (Decision Gate Friday EOD):
| Metric | Target | Threshold |
|--------|--------|-----------|
| Clarity | ≥80% | "Yes, it's clear" votes |
| Preference | ≥70% | "Peer is better" vs absolute |
| NTEE accuracy | ≤20% | User vs default disagreement |
| Coverage | ≥98% | v5_context present on views |

**If All Metrics Pass**: → **LAUNCH WEEK 4**

**If Some Fail**: → **ITERATE WEEK 3**
- Adjust terminology, examples, explanations
- Re-test on 5% for 2-3 days
- Make revised decision

**Files**:
- docs/WEEK3_FEEDBACK_COLLECTION.md
- docs/WEEK3_BETA_STATUS.md (completed)
- docs/DROPLET_DEPLOYMENT_GUIDE.md (completed)

---

### Phase 3: Week 4 Full Launch (IF Metrics Pass)

**Timeline**: Monday-Friday, June 16-20, 2026

**Objectives**:
1. Remove v4 scores from API and UI
2. Deploy v5.0 to 100% of users
3. Publish methodology page
4. Send user communications
5. Activate monitoring

**Pre-Launch Checklist** (Monday 9am):
- Metrics verified (clarity ≥80%, preference ≥70%, NTEE ≤20%, coverage ≥98%)
- Code reviewed and approved
- Database backed up
- Rollback plan confirmed
- Communications drafted
- Monitoring dashboards ready

**Launch Sequence** (Monday 10am PT):
1. **Prepare** (1 hour): Verify health, database integrity, backups
2. **Remove v4** (30 min): Strip v4 fields from API, update feature flag to 100%
3. **Deploy** (30 min): Build frontend, deploy to droplet
4. **Verify** (30 min): API health, v5_context present, performance acceptable

**API Changes**:
- Remove merit_score, merit_tier, merit_band, visibility_tier
- Keep v5_context as primary
- Update disclosures and disclaimers
- Add methodology URL to responses

**Frontend Changes**:
- Update useFeatureFlag to 100% (or remove feature flag entirely)
- Change "Financial Context (Beta)" → "Financial Context"
- Remove beta badges and disclaimers
- Update styling and component text

**Communications** (Monday 2pm PT):
1. User email: "Daanaa's New Financial Perspective"
   - Explain peer-based comparison
   - Link to methodology page
   - Show example org

2. Blog post: "How Daanaa Compares Nonprofits"
   - Problem with absolute scores
   - Solution: peer comparison
   - 3 real examples
   - Limitations

3. Partner email: "New Financial Context for Nonprofits"
   - How to see peer group
   - Verify funding sources
   - Link to dashboard

4. Social media: 3-5 posts over launch day

5. Methodology page: daanaa.org/methodology
   - Executive summary
   - How it works (5 archetypes × 3 bands)
   - Data source and validation
   - Examples and FAQ
   - Limitations

**Monitoring** (24/7):
- Error rate <0.1%
- Response time <100ms
- v5_context null rate 78% (unscored orgs)
- No rollback needed

**Success Looks Like**:
- Monday EOD: v5.0 live for 100%, zero errors
- Tuesday: Positive user feedback
- Wednesday: Blog post shared widely
- Friday: All metrics stable, no incidents

**If Issues Occur**:
- Quick rollback: Hide v5_context (revert feature flag to 0%)
- Graceful rollback: Deploy to 50% v5, 50% v4, monitor
- Full rollback: Restore database from backup, revert API/frontend

**Files**:
- docs/WEEK4_FULL_LAUNCH.md (detailed procedures)
- docs/methodology.md (public page)
- Blog post (new post)
- Communications templates

---

### Phase 4: Post-Launch Monitoring (Week 4+)

**Timeline**: Ongoing (Week 4, then monthly)

**Objectives**:
1. Ensure stability and performance
2. Track user engagement and satisfaction
3. Identify and fix issues quickly
4. Plan improvements based on feedback

**Daily Monitoring** (Week 1):
- API error rate check
- Response time tracking
- Database integrity verification
- User feedback review
- Alert threshold monitoring

**Weekly Monitoring** (Weeks 2+):
- Metrics aggregation and analysis
- Trend identification
- Feedback sentiment analysis
- Performance optimization
- Bug triage and fix

**Monthly Deep Dive**:
- Data validation (scores stable?)
- Methodology review (K=5 still optimal?)
- Feature request analysis
- Roadmap planning

**Real-Time Dashboard**:
```
Adoption:        95% of org detail views show v5_context
Error Rate:      0.08% (target: <0.1%)
Response Time:   95ms p99 (target: <100ms)
User Feedback:   81% clarity, 72% preference (PASS ✓)
```

**Alert Thresholds**:
- Error rate >1% → page on-call
- Response time >500ms → investigate
- Null rate >85% → data corruption suspected
- Negative feedback >25% → escalate

**Success Metrics** (Month 1):
- Zero data corruption
- <0.1% error rate sustained
- User clarity ≥75%
- No major regressions
- Blog post >1K views

**Files**:
- docs/POSTLAUNCH_MONITORING.md (detailed procedures)

---

### Phase 5: Optimization (Week 5+)

**Timeline**: Ongoing

**Quick Wins** (1-2 days):
- Terminology tweaks based on feedback
- FAQ updates
- Link improvements

**Medium Term** (1-2 weeks):
- Comparison tool: "Show me other orgs like this"
- Trend tracking: "How has this org's health changed?"
- Export functionality

**Long Term** (1+ months):
- Mobile app with v5.0
- Nonprofit dashboard
- Bulk analysis tools
- Research features

**Continuous Improvement**:
- Monthly metrics review
- Quarterly roadmap update
- Gather user feedback
- Implement high-value features

---

## Decision Gates

### Gate 1: Week 3 Friday EOD (Go/No-Go Week 4)

```
IF clarity ≥80% AND preference ≥70% AND NTEE accuracy ≤20% AND coverage ≥98%
  THEN → LAUNCH WEEK 4
ELSE IF clarity ≥80% AND preference ≥70%
  THEN → ITERATE (adjust terminology, re-test 5%)
ELSE
  THEN → MAJOR REVISION (design review, consider alternative approach)
```

### Gate 2: Week 4 Monday (Go/No-Go Launch)

```
IF all pre-launch checks PASS
  THEN → PROCEED WITH LAUNCH
ELSE
  THEN → DELAY (fix issues, recheck)
```

### Gate 3: Week 4 EOD (Rollback Decision)

```
IF error rate ≥0.1% OR response time ≥200ms OR negative feedback >30%
  THEN → CONSIDER ROLLBACK
ELSE
  THEN → LAUNCH SUCCESSFUL
```

---

## Critical Success Factors

1. **Data Quality**: 447K scored orgs with validated peer groups
2. **Clarity**: Archetype labels understood by ≥80% of users
3. **Preference**: ≥70% prefer peer comparison to absolute scores
4. **Stability**: <0.1% error rate, <100ms response time
5. **Communication**: Users understand why peer comparison is fairer
6. **Rollback Ready**: Quick procedure if issues occur

---

## Known Risks & Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Users confused by peer concept | Medium | Add examples, explanations, video |
| NTEE misclassification >20% | Medium | Pre-test questionnaire with users |
| API performance regression | Low | Load test with 447K orgs |
| Data stale (>1 month old) | Low | Automated monthly refresh |
| User adoption slow (<50%) | Medium | Strong communication, incentives |
| Negative press on methodology | Low | Pre-publish research, get buy-in |

---

## Timeline Summary

```
Week 3 (Jun 12-13)
  Thu: Feedback collection starts
  Fri EOD: Metrics analysis, decision gate

  IF PASS → Week 4
  IF ITERATE → Extended Week 3 (2-3 more days)
  IF FAIL → Major revision

Week 4 (Jun 16-20)
  Mon 9am: Pre-launch checklist
  Mon 10am: Launch sequence begins
  Mon 10am-12pm: Deploy to 100%
  Mon 12pm-5pm: Verify, monitor, communicate
  Tue-Fri: Stabilization, monitoring
  Fri: Post-launch review

Week 5+ (Jun 23+)
  Ongoing: Daily monitoring
  Weekly: Metrics review
  Monthly: Deep validation
  Continuous: Feature requests, optimization
```

---

## Success Definition

**Week 3**: Metrics show users understand and prefer peer comparison

**Week 4**: Launch with zero data loss, <0.1% error rate, <100ms response time

**Week 5+**: Sustained engagement, positive feedback, no major issues

**Month 1**: 95%+ adoption, ≥75% user clarity, <0.1% error rate

---

## Files Reference

### Implementation (Complete)
- scripts/merit_scorer_v5_0.py — K=5 clustering, 447K orgs
- scripts/enrich_api_responses.py — v5_context enrichment
- scripts/ntee_questionnaire_v5_0.py — UI for ambiguous categories
- frontend/src/components/V5Context.tsx — Beta UI component
- frontend/src/hooks/useFeatureFlag.ts — 1% cohort selection
- daanaa_api.py — API integration (lines 966-984)

### Documentation (Complete)
- docs/API_V5_RESPONSE_FORMAT.md — Full API schema
- docs/methodology.md — Public explanation
- docs/WEEK3_BETA_STATUS.md — Beta status report
- docs/WEEK3_FEEDBACK_COLLECTION.md — Feedback procedures
- docs/WEEK4_FULL_LAUNCH.md — Launch procedures
- docs/POSTLAUNCH_MONITORING.md — Monitoring guide
- docs/V5_COMPLETE_ROADMAP.md — This document

---

## Approval & Sign-Off

### Pre-Week 3
- [ ] Product approves metrics thresholds
- [ ] Engineering confirms deployment readiness
- [ ] Legal reviews disclaimers and methodology language

### Pre-Week 4
- [ ] Product approves Week 3 metrics (decision gate pass)
- [ ] Engineering confirms no show-stoppers
- [ ] Communications ready (blog, emails, templates)
- [ ] Rollback plan documented and rehearsed

### Post-Week 4
- [ ] Launch metrics documented
- [ ] Lessons learned captured
- [ ] Week 5+ roadmap approved

---

**Document Version**: v1.0  
**Last Updated**: 2026-06-11  
**Next Review**: After Week 3 decision (Friday, June 13)  
**Owner**: Claude Code + Daanaa Product Team
