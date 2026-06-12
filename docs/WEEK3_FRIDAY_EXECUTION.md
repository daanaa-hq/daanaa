# Week 3 Friday Execution Plan
## v5.0 Beta Decision Gate & Contingency Execution

**Date**: Friday, June 13, 2026  
**Status**: Ready for execution  
**Owner**: Claude Code + decision maker  

---

## Friday Timeline

### 9:00am PT — Metrics Analysis

**Action**: Run metrics analysis
```bash
python3 scripts/analyze_v5_feedback.py --detailed --export
```

**Output**: 4 metrics vs thresholds
- Clarity: target ≥80%
- Preference: target ≥70%
- NTEE accuracy: target ≤20%
- Coverage: target ≥98%

**What to Look For**:
- Clarity: "Yes, it's clear" percentage (open text feedback if low)
- Preference: "Peer comparison is better" percentage
- NTEE: User funding source selections vs defaults (validation pending)
- Coverage: Estimated from feedback form appearance

**Decision Logic**:
```
IF all 4 metrics PASS
  → decision = "LAUNCH"
ELSE IF clarity PASS AND preference PASS
  → decision = "ITERATE"
ELSE
  → decision = "MAJOR_REVISION"
```

### 9:30am—3:00pm PT — Preparation & Planning

**If LAUNCH Decision**:
1. Review metrics report (15 min)
2. Brief decision maker (5 min)
3. Prepare launch window: Monday 10am PT
4. Code review: v4 removal changes (30 min)
5. Create database backup (5 min)
6. Confirm rollback procedure (10 min)
7. Draft communications (1 hour):
   - User email (Daanaa's New Financial Perspective)
   - Blog post outline (How Daanaa Compares Nonprofits)
   - Partner email (New Financial Context)
   - Social media posts (5 posts)

**If ITERATE Decision**:
1. Analyze clarity/preference responses in detail
2. Identify terminology/messaging gaps
3. Prepare updated explanations
4. Plan re-test on 5% cohort (2-3 days)
5. Schedule new decision gate (Wed-Thu next week)

**If MAJOR_REVISION Decision**:
1. Design review workshop scheduled
2. Gather user feedback patterns
3. Document recommended changes
4. Plan alternative approaches
5. Reschedule Week 3 beta with redesign

### 3:00pm—4:00pm PT — Final Verification

**Pre-decision Gate Checklist**:
- [ ] All 4 metrics reviewed and documented
- [ ] API health check: error rate <0.1%, response <100ms
- [ ] Database integrity check (PRAGMA integrity_check)
- [ ] Droplet API responding normally
- [ ] Feature flag status verified (currently 1%)
- [ ] Privacy checks passed (no tracking)
- [ ] No critical alerts or incidents

**Commands**:
```bash
# API health
curl http://localhost:5000/health

# Database integrity
sqlite3 data/merit_registry.db "PRAGMA integrity_check"

# Response time
curl -w "Response time: %{time_total}s\n" http://localhost:5000/health

# Error rate (last hour)
tail -500 logs/daanaa_api.log | grep ERROR | wc -l
```

### 5:00pm PT — Decision Gate

**Announcement**:
- Public statement of decision (LAUNCH / ITERATE / MAJOR_REVISION)
- Next steps and timeline
- If LAUNCH: Week 4 launch window confirmed (Monday 10am)
- If ITERATE: Re-test window and new decision date
- If MAJOR_REVISION: Design review schedule

**Format**: Email to Akbar + internal announcement

---

## If LAUNCH (Monday Morning)

### Pre-Launch Checklist (Mon 9am)

Execute in this order:
1. Verify Week 3 metrics one final time
2. Code review v4 removal changes (lines TBD in daanaa_api.py)
3. Create final database backup
4. Confirm rollback procedure documented
5. Verify communications drafts final
6. Confirm any stakeholder reviews complete

### Launch Sequence (Mon 10am—12pm)

**Automated by**: `scripts/week4_launch_sequence.py`

4 phases, ~2 hours total:

**Phase 1: PREPARE (1h)**
- API health check
- Database integrity verification (PRAGMA)
- Count scored orgs (v5_archetype column)
- Create timestamped database backup
- Log all actions

**Phase 2: REMOVE V4 (30 min)**
- Update feature flag to 100% (v5 now visible to all)
- Comment out v4 fields in API response:
  - Remove: `merit_score`, `merit_tier`, `merit_band`, `visibility_tier`
  - Keep: `v5_context` as primary response
- Update disclaimers and methodology links in API

**Phase 3: DEPLOY (30 min)**
- Frontend rebuild: `npm --prefix frontend run build`
- Droplet deployment: `bash scripts/safe_deploy_droplet.sh`
- Verify SPA live and serving new assets

**Phase 4: VERIFY (30 min)**
- API response time check (<100ms)
- v5_context field present in all responses
- Error rate check (<0.1%)
- Droplet health check

**Command**:
```bash
python3 scripts/week4_launch_sequence.py [--dry-run] [--skip-comms]
```

### Communications (Mon 2pm PT)

**1. User Email**
- Subject: "Your nonprofit's financial health just got smarter"
- Body: Explain peer-based comparison, link methodology page, show example
- Send to: All newsletter subscribers (daanaa@daanaa.org)

**2. Blog Post**
- Title: "How Daanaa Compares Nonprofits"
- Length: 1200 words
- Sections: Problem with absolute scores, solution with peers, 3 examples, limitations
- Publish: https://daanaa.org/blog/

**3. Partner Email**
- Target: Foundation advisors, strategic partners
- Content: How to verify peer group, use methodology, interpret health signals
- Links: Methodology page, research data

**4. Social Media** (5 posts over day)
- Twitter/X: Daily throughout Jun 16
- LinkedIn: 1-2 posts
- Announce, explain, deep-dive, examples, thank you

### Post-Launch Monitoring (Week 4)

**24/7 Monitoring Thresholds**:
- Error rate >1% → page on-call engineer
- Response time >500ms → investigate performance
- v5_context null rate >85% → potential data corruption
- Negative feedback >30% → escalate to decision maker

**Daily Health Checks**:
- 9am PT: Error rate review (tail logs)
- 12pm PT: Response time sample (curl timing)
- 3pm PT: Feedback sentiment review
- 6pm PT: Daily report

**Weekly Review** (Mon Jun 23):
- Metrics aggregation (1M+ page views expected)
- User engagement patterns
- Blog post performance (target: >1K views)
- Feature request analysis
- Plan any quick wins/iterations

### Rollback (If Needed)

**Quick Rollback** (5 min):
```bash
# Hide v5_context from all users
UPDATE feature_flags SET percentage = 0 WHERE name = 'v5_peer_taxonomy';
# Or comment out v5_context field in API response
```

**Graceful Rollback** (50 min):
- Deploy to 50% v5, 50% v4
- Monitor for 24 hours
- Complete rollback if issues persist

**Full Rollback** (database restore):
```bash
# Restore from backup created before launch
cp data/merit_registry_backup_[timestamp].db data/merit_registry.db
systemctl restart daanaa_api
```

---

## If ITERATE

### Re-Test Plan (2-3 days)

1. **Analyze feedback** (1 hour):
   - Extract all clarity_reason text responses
   - Identify common themes
   - Prioritize messaging gaps

2. **Update UI** (2-4 hours):
   - Revise archetype labels or add explanations
   - Improve peer group description
   - Add example or tooltip
   - Update donor copy generation

3. **Re-Deploy** (30 min):
   - Build frontend
   - Deploy to droplet (pre-production testing first)

4. **Re-Test** (2-3 days):
   - Roll out to 5% of users (via feature flag)
   - Collect 30-50 new feedback responses
   - Run analysis again

5. **New Decision Gate** (Wed or Thu):
   - Repeat metrics analysis
   - Final go/no-go for Week 4 launch

---

## If MAJOR_REVISION

### Design Review Workshop

**Schedule**: Mon-Tue (Jun 16-17)

**Participants**:
- Design lead
- Product manager
- 1-2 user research participants
- Backend architect

**Agenda**:
1. User feedback synthesis (30 min)
2. Archetype & peer framing (60 min)
3. Alternative approaches (60 min)
4. Recommendation & next steps (30 min)

**Outcomes**:
- Clear redesign scope
- Timeline for Week 3b (re-beta) or pivot
- Go/no-go decision for v5.0 launch

---

## Scripts Ready for Execution

| Script | Purpose | Command |
|--------|---------|---------|
| `analyze_v5_feedback.py` | Run metrics analysis | `python3 scripts/analyze_v5_feedback.py --detailed --export` |
| `monitor_v5_feedback.py` | Live dashboard (optional monitoring) | `python3 scripts/monitor_v5_feedback.py` |
| `week4_launch_sequence.py` | Execute launch (if LAUNCH) | `python3 scripts/week4_launch_sequence.py --dry-run` (test first) |

---

## Known Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Low feedback volume | Can't reach statistical confidence | 1% cohort ~100-500 daily actives; full Thu-Fri window |
| Archetype confusion | Clarity metric fails | Open-text reason capture; shows what's confusing |
| Rollback complexity | Extended outage if needed | Rollback procedure tested and documented |
| Terminology ambiguity | Users prefer absolute scores | Preference question captures this directly |

---

## Decision Record

**Recorded by**: Claude Code  
**Date**: Friday, June 13, 2026, 5:00pm PT  
**Metrics Status**: [To be filled in Friday]

**Decision**: ☐ LAUNCH   ☐ ITERATE   ☐ MAJOR_REVISION

**Metrics**:
- Clarity: ___%  (target: ≥80%)  [PASS / FAIL]
- Preference: ___%  (target: ≥70%)  [PASS / FAIL]
- NTEE accuracy: ___%  (target: ≤20%)  [PASS / FAIL]
- Coverage: ___%  (target: ≥98%)  [PASS / FAIL]

**Next Milestone**:
- If LAUNCH: Monday Jun 16, 10am PT (Week 4 launch)
- If ITERATE: Wednesday Jun 18, 5pm PT (new decision gate)
- If MAJOR_REVISION: Monday Jun 16, 10am PT (design review)

**Notes**:
[To be filled in Friday]

---

## Contact & Escalation

**Decision Maker**: Akbar Khowaja (founder)  
**Technical Owner**: Claude Code  
**Escalation Path**:
1. Run analysis, brief decision maker (5 min)
2. If uncertain, extend decision window to Sat morning (allow 24h review)
3. If critical issue arises, activate incident response

---

**Document Version**: 1.0  
**Created**: 2026-06-12  
**Status**: Ready for execution  
**Next Update**: Friday 2026-06-13, 9:00am PT (post-analysis)
