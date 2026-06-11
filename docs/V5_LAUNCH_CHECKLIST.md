# v5.0 Taxonomy Launch Checklist

**Target Launch Date**: Week 4 (after beta feedback)  
**Responsible**: Akbar + Engineering Team  
**Status**: ✅ Ready for Beta

---

## Week 2 Completion ✅

- [x] Scorer implementation (merit_scorer_v5_0.py)
- [x] Full-population scoring (447,557 orgs)
- [x] Database migration (8 new columns)
- [x] Data integrity validation
- [x] API enrichment function (enrich_api_responses.py)
- [x] Public methodology documentation
- [x] NTEE questionnaire design

---

## Week 3: Beta Testing & Feedback

### Monday–Wednesday: Shadow Deployment
- [ ] API integration: Add v5_context to /api/directory/org/{EIN}
- [ ] Frontend: Show v5 data in OrganizationDetail.tsx (alongside v4.0)
- [ ] Deploy to 1% of users with feature flag
- [ ] Monitor view count and error rates
- [ ] Collect feedback via in-app form

### Thursday–Friday: Analysis & Iteration
- [ ] Analyze user feedback
  - Archetype clarity: ≥80% understand label?
  - Peer comparison: ≥70% prefer it to absolute score?
  - NTEE questionnaire: ≤20% misclassification?
- [ ] Adjust terminology or defaults if needed
- [ ] Make decision: Proceed to launch or iterate?

### Decision Gate (Friday EOD)
```
IF satisfaction ≥ 80% THEN
  Proceed to Week 4 full launch
ELSE
  Adjust based on feedback
  Re-test on 5% of users
  (this extends to Week 4)
```

---

## Week 4: Full Launch

### Frontend Updates
- [ ] Remove v4.0 score from UI (full v5.0 cutover)
- [ ] Display archetype + band on org detail page
- [ ] Show peer benchmarks (P25, P50, P75)
- [ ] Display donor-facing health explanation
- [ ] Add link to /methodology page
- [ ] Update org comparison UI to show peer group instead of absolute rank

### API Updates
- [ ] Remove v4.0 fields from /api/directory/org responses (or mark deprecated)
- [ ] Ensure v5_context is present on all responses
- [ ] Update API documentation on daanaa.org
- [ ] Test API responses (100 orgs, all NTEE categories)

### Communication
- [ ] Publish /methodology page on frontend
- [ ] Write blog post: "How Daanaa Compares Nonprofits"
  - Explain the shift from absolute to peer-relative scoring
  - Show 3 examples of org comparisons
  - Emphasize: Not a judgment, a context
- [ ] Send email to users:
  ```
  Subject: Daanaa's New Financial Perspective
  
  We've redesigned how we compare nonprofit finances.
  Instead of an absolute "score," we now show you how each
  organization compares to financially similar peers.
  
  Learn why peer comparison is more fair:
  daanaa.org/methodology
  ```
- [ ] Update in-app onboarding to explain v5.0 system

### NTEE Questionnaire Deployment
- [ ] For 7 high-risk categories (B, C, E, L, N, S, U):
  - [ ] Show funding source question on org detail
  - [ ] Store user response (org can confirm or override)
  - [ ] Use response to refine archetype assignment if different from default
- [ ] Track accuracy: Do users' answers match our defaults?
- [ ] Iterate if >20% disagreement

### Database & Operations
- [ ] Set up monthly benchmark refresh (new script)
  ```
  # scripts/refresh_v5_benchmarks.py
  # Runs 1st of month to update P25/P50/P75 from latest data
  ```
- [ ] Document v5.0 as current methodology in DECISIONS.md
- [ ] Archive v4.0 scoring (move to /archive)
- [ ] Update CLAUDE.md with v5.0 references

### QA & Validation
- [ ] Sanity check: 100 random orgs, verify peer group assignment
- [ ] Cross-check: 10 orgs from each NTEE category
- [ ] Test on production-like data volume
- [ ] Verify API response times remain <100ms per request
- [ ] Check search results still rank correctly (if ranking by v5 score)

### Legal / Disclosures
- [ ] Review SCORE_DISCLAIMER in daanaa_api.py
  - Update to reference v5.0 system
  - Clarify: "Peer-relative, not absolute judgment"
- [ ] Add to methodology page:
  - Data sources (IRS 990, years covered)
  - Known limitations (21.6% of orgs unscored)
  - Disclaimer: "This is a starting point, not a verdict"

### Public Relations
- [ ] Email to nonprofit partners:
  ```
  Subject: New Financial Context Tool for Nonprofits
  
  If you claim your organization's page on Daanaa, you can
  now see exactly which peer group you're being compared against.
  No surprises—full transparency.
  ```
- [ ] Consider: Press release if significant media outlet interest

---

## Success Criteria for Week 4 Launch

| Metric | Target | Status |
|--------|--------|--------|
| API response time | <100ms | TBD (test in beta) |
| Data coverage | ≥98% of viewed orgs have v5 data | Will validate |
| User comprehension | ≥80% understand archetype | Beta will test |
| Data accuracy | No >5% gaps per peer group | Will audit |
| Search performance | No regression vs v4.0 | Will benchmark |

---

## Post-Launch (Week 5+)

### Monthly Maintenance
- [ ] 1st of month: Refresh benchmarks from latest org data
- [ ] Monitor feedback on questionnaire accuracy
- [ ] Watch for edge cases or misclassifications
- [ ] Gather anonymized improvement suggestions

### Potential Future Enhancements
- [ ] Comparison tool: "Show me other orgs like this"
- [ ] Trend tracking: "How has this org's health changed over 3 years?"
- [ ] Peer insight: "What do healthy orgs in this group do differently?"
- [ ] Mobile app: Bring v5.0 system to iOS/Android

---

## Blockers & Risks

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| >20% NTEE misclassification | Medium | Pre-test questionnaire with users |
| API performance regression | Low | Load-test with 447K orgs |
| User confusion on "peer group" concept | Medium | Invest in onboarding copy |
| Data stale (>1 month old) | Low | Automated monthly refresh |

---

## Sign-off Checklist

Before launching to 100%, confirm:

- [ ] CEO/Product lead approves wording & messaging
- [ ] Legal reviews disclosures & limitations language
- [ ] Engineering confirms API & DB stability
- [ ] QA validates 100-org sample (all NTEE categories)
- [ ] Communication team ready with blog/email/PR

---

**Version**: v5.0 Launch Plan  
**Last Updated**: 2026-06-11  
**Next Review**: After Week 3 beta feedback
