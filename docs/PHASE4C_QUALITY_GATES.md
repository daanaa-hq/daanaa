# Phase 4C: Quality Gates Framework (Not Timelines)

**Principle:** We measure until gates pass. We decide when confident. We ship when ready.
Time is not a constraint. Data quality is.

---

## Gate System Overview

**Three measurement phases, four gates each:**

### Phase A: Phase 3 Impact Measurement

**Objective:** Determine if better display of existing data helps small orgs reach parity with large orgs.

**Gate 1: Measurement Reliability**
- **Condition:** Measurement is stable and repeatable
- **Validation:**
  - Day-to-day CTR variance <15% (coefficient of variation)
  - No anomalies in raw event streams
  - Plausible dashboard queries return consistent results
  - Sample size sufficient (>100 micro org clicks per day)
- **Feedback:** Daily pulse check (5 min automated report)
  ```
  Aug 10: Micro CTR = 42% (baseline: 41%) — Δ: +2% ✓ stable
  Aug 11: Micro CTR = 43% (baseline: 41%) — Δ: +4% ✓ stable
  Aug 12: Micro CTR = 40% (baseline: 41%) — Δ: -2% ✓ stable
  (variance: 2.4% — PASS)
  ```
- **Exit Criteria:** 5-7 days of stable measurement, or earlier if oscillation settles

---

**Gate 2: Statistical Significance**
- **Condition:** Result reaches clear threshold (not ambiguous)
- **Validation:**
  - Small org CTR delta ≥ +30% (Phase 3 wins) OR
  - Small org CTR delta ≤ -5% (needs debug) OR
  - Result stays neutral (no clear signal after 3 weeks)
- **Feedback:** Weekly cohort review
  ```
  Week 1 Report:
  - Micro org CTR: 41% → 45% (Δ: +9.8%)
  - Large org CTR: 51% → 51% (Δ: 0%)
  - Ratio (Micro/Large): 80% → 88% (Δ: +10% relative)
  
  Interpretation: Moving in right direction (+9.8%) but below +30% threshold.
  Confidence: MODERATE (could be real or noise)
  Next: Continue measurement, reassess after Week 2.
  ```
- **Exit Criteria:**
  - +30%+ improvement → "Phase 3 Wins" gate
  - -5% deterioration → "Debug Needed" gate
  - ±5% to +30% for 3 weeks → "Inconclusive" verdict

---

**Gate 3: Root Cause Understanding**
- **Condition:** We explain the data (not just observe it)
- **Validation:**
  - If wins: Where are the clicks coming from? (search? direct? browse?)
  - If neutral: Why not? (At a Glance not visible? not compelling? UX issue?)
  - If loses: What regressed? (layout? performance? trust signal?)
- **Feedback:** Deep-dive analysis on secondary metrics
  ```
  Phase 3 "Wins" Scenario (CTR +30%+):
  - Where: 60% from Directory, 30% from Search, 10% from Direct
  - At a Glance visibility: 78% (expected: >60%) ✓
  - Time on page: +22% for Micro orgs ✓
  - Bookmark rate: Micro/Large ratio improved 40% ✓
  → Conclusion: Display clarity is working across all channels
  
  Phase 3 "Neutral" Scenario (CTR ±5%):
  - Where: 50% from Directory, 45% from Search, 5% from Direct
  - At a Glance visibility: 42% (expected: >60%) ⚠️ ISSUE
  - Time on page: no change for Micro orgs (expected: +15%)
  - Bookmark rate: no change
  → Hypothesis 1: Component not visible (above fold? needs testing)
  → Hypothesis 2: Component visible but not compelling (needs UX test)
  → Action: A/B test placement OR copy iteration
  ```
- **Exit Criteria:** Can articulate "why" with supporting secondary metrics

---

**Gate 4: Decision Confidence**
- **Condition:** Recommendation is defensible and clear
- **Validation:**
  - Quantitative + qualitative alignment (data matches narrative)
  - No contradictions in secondary metrics
  - Scenarios for Phase 4 decision are explicit
- **Feedback:** Structured decision memo
  ```
  DECISION MEMO (Template):
  
  Measurement Period: [dates]
  Primary Result: [CTR delta + confidence]
  Secondary Validation: [scroll depth, time, bookmarks, search patterns]
  
  Conclusion: [Phase 3 Wins / Neutral / Needs Debug]
  
  IF WINS:
    → Phase 4 Path: [ProPublica / Candid / None] based on measurement
    → Timeline: [no rush — whenever data source is ready]
    → Success: [what Phase 4 adds on top of Phase 3]
  
  IF NEUTRAL:
    → Root Cause: [specific hypothesis from secondary data]
    → Next Action: [A/B test / UX iteration / pivot]
    → Timeline: [iterate until Gate 3 clarity achieved]
  
  IF LOSES:
    → Issue: [specific regression identified]
    → Rollback: [ready in < 1 hour]
    → Investigation: [what broke and why]
    → Retry: [after fix + retesting]
  
  Confidence Level: [Low / Moderate / High]
  Who reviews: [Founder + Product]
  ```
- **Exit Criteria:** Memo signed off, recommendation is actionable

---

### Phase B: Phase 4 Data Source Decision (if Gate A.4 passes with "Wins")

**Objective:** Choose Phase 4 data source (ProPublica, Candid, defer, none)

**Gate 1: Business Need**
- **Condition:** Measurement proves Phase 3 helps; Phase 4 has clear ROI
- **Validation:** Phase 3 CTR improvement persists beyond measurement window
- **Feedback:** 2-week stability check post-Phase-3-live
- **Exit:** Consistent +30%+ CTR improvement for 2+ weeks

**Gate 2: Data Source Quality**
- **Condition:** Candidate source is reliable and relevant
- **Validation:**
  - Coverage ≥80% of registry (or >50% of Micro orgs)
  - Data freshness suitable for use case
  - API/schema is stable
  - No ToS violations
- **Feedback:** Source evaluation spreadsheet
  ```
  | Source | Coverage | Freshness | API Stability | ToS OK? | Effort | Rating |
  |--------|----------|-----------|---------------|---------|--------|--------|
  | ProPublica | 22% (156K) | Good (weekly) | Proven | ✓ | 2d | 7/10 |
  | Candid | 95% (1.6M) | OK (monthly) | Stable | ✓ | 3d | 8/10 |
  | Mission Capital | TBD | TBD | Blocked | ? | ? | ? |
  ```
- **Exit:** Source scores ≥7/10 and no blockers

**Gate 3: Integration Readiness**
- **Condition:** API + schema design is solid, no breaking changes
- **Validation:**
  - API endpoints documented and tested
  - Response schema matches org response structure
  - Backwards compatibility maintained
  - Rollback plan exists
- **Feedback:** Integration test report
- **Exit:** Integration plan reviewed, no unknowns remain

**Gate 4: Stewardship Compliance**
- **Condition:** Phase 4 passes all Stewardship principles
- **Validation:**
  - P2 (Privacy): No donor/user data shared with source
  - P3 (Evidence-based): Attribution clear, data freshness documented
  - P4 (Small org fairness): Source doesn't bias against small orgs
  - P7 (Independence): No outside influence on scores/visibility
- **Feedback:** Stewardship audit checklist
- **Exit:** Legal review complete, no principle conflicts

---

### Phase C: Phase 4 Launch (if Gate B.4 passes)

**Gate 1: Code Quality**
- **Condition:** Implementation is tested and stable
- **Validation:** All tests pass, no new warnings, no breaking changes
- **Exit:** CI/CD green across all checks

**Gate 2: Staging Validation**
- **Condition:** Feature works in production-like environment
- **Validation:**
  - Staging runs 48 hours with no regressions
  - Search performance maintained
  - API response times within SLA
  - Rollback tested and verified
- **Feedback:** Staging test report
- **Exit:** 48h clean run, rollback confirmed working

**Gate 3: Rollback Readiness**
- **Condition:** Can revert Phase 4 within 1 hour if needed
- **Validation:**
  - `.prev` snapshot created
  - Rollback script tested
  - Team knows how to trigger it
- **Feedback:** Runbook + team walkthrough
- **Exit:** Rollback plan documented, team trained

**Gate 4: Live Monitoring**
- **Condition:** Alerts and dashboards are active
- **Validation:**
  - Alerts firing on sample failures
  - Dashboards show Phase 4 impact
  - On-call playbook updated
- **Feedback:** Monitoring validation checklist
- **Exit:** All monitoring confirmed live and tested

---

## Decision Points (Not Timelines)

```
Start Phase 3 Measurement
    ↓
Pass Gate A.1 (Reliability)?
    Yes → Continue
    No → Troubleshoot measurement setup
    ↓
Pass Gate A.2 (Significance)?
    Yes (Phase 3 Wins) → Gate A.3
    Neutral → Gate A.3 (dig deeper)
    Yes (Negative) → PAUSE, investigate regression
    ↓
Pass Gate A.3 (Understanding)?
    Yes → Gate A.4
    No → Continue measurement longer
    ↓
Pass Gate A.4 (Confidence)?
    Yes + Wins → Phase B (Phase 4 decision)
    Yes + Neutral → A/B test or UX iterate
    Yes + Negative → Rollback Phase 3
    ↓
Phase B Gates (Data Source):
    All pass → Phase C (Launch)
    Any fail → Defer Phase 4 or choose different source
    ↓
Phase C Gates (Launch):
    All pass → Live
    Any fail → Staging fix and re-validate
```

---

## Feedback Loop Cadence

**No calendar dates. Data-driven checkpoints instead:**

- **Daily:** Pulse check (measurement reliability)
  - Takes 5 min
  - Looks for anomalies
  - Stops if something breaks
- **Weekly:** Cohort review (statistical progress)
  - Takes 30 min
  - Reassesses gate progress
  - Adjusts measurement approach if needed
- **As-needed:** Deep dive (root cause understanding)
  - Triggered when primary metric is unclear
  - Takes 2-4 hours
  - Validates secondary metrics
- **Final:** Decision memo (confidence assessment)
  - Only written when Gate A.4 is ready
  - Takes 1-2 hours
  - Decides Phase 4 path

---

## Why This Works

1. **Quality over time:** We measure as long as needed, not arbitrarily
2. **Feedback loops:** We catch problems early (daily) and iterate fast (weekly)
3. **Clear exits:** Every gate has explicit pass/fail criteria
4. **Defensible decisions:** Recommendations come with data + narrative + secondary validation
5. **Low risk:** We have rollback plans and staged gates before live launch

---

## Example: Phase 3 Measurement Runs 3 Weeks Instead of 1

Scenario: CTR improvement is small (+8%) but trending upward.

**Week 1:** Gate A.2 says "not significant yet" → continue
**Week 2:** CTR now +15% → still below +30% threshold but clear trend
**Week 3:** CTR now +28% → approaching significance, confidence rising

**Decision (Week 3, not Week 1):**
- Phase 3 didn't hit +30% ceiling, but +28% is real and stable
- Small org/large org gap has been cut from 80% to 88%
- At a Glance visibility is 72%, scroll depth +18%, bookmarks +22%
- Confidence: MODERATE-HIGH (trend is clear even if absolute gain is modest)

**Phase 4 Recommendation:** "Ship Phase 4 with measured expectations. Phase 3 helped 28%, Phase 4 might add 10-15% more. Total vision is narrowing the gap to 95%+ parity by end of year."

This is better than rushing to decide on Day 7 with noisy data.

---

## Success Criteria (Not Deadlines)

✅ **We've won Phase 4 when:**
- Gate A.4 passes with high confidence
- Data tells a clear story (wins, neutral, or needs debug)
- We can explain it with secondary validation
- Team agrees on next steps
- Rollback plans are solid

**None of this depends on Aug 9, Aug 16, or Aug 20.**

