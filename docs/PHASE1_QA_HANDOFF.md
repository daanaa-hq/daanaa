# PHASE 1: QA HANDOFF (Frequent Check-In Version)
## For QA Team — Check Every Few Hours

---

## 🎯 YOUR MISSION (Stream C)

Build comprehensive QA plan + test cases for 6 credibility signals.

**Timeline:** 2-3 days  
**Check-In Frequency:** Every 3-4 hours  
**Status Updates:** #credibility-phase1 Slack (brief + clear)

---

## 📋 DELIVERABLES (What You're Building)

### 1. QA Checklist (7 Sections)
- [ ] Signals compute correctly (all 6)
- [ ] API response format correct
- [ ] Performance <200ms per org
- [ ] Search performance <400ms
- [ ] WCAG AA compliance
- [ ] Error handling (graceful nulls)
- [ ] Edge cases (revoked, missing data, postcard orgs)

### 2. Functional Test Cases (12 tests)
- [ ] IRS Verification signal (3 cases: verified, unverified, revoked)
- [ ] Data Freshness signal (3 cases: fresh, aging, stale)
- [ ] Expense Ratio signal (3 cases: concern, fair, strong)
- [ ] Peer Context signal (2 cases: large peer cell, small peer cell)
- [ ] Recency & Completeness signal (1 case: mixed data)

### 3. Performance Test Suite (6 tests)
- [ ] Page load <200ms (3 test orgs: large, small, postcard)
- [ ] Search <400ms (5 queries, various complexity)
- [ ] Database indexes used (query explain plans)
- [ ] Memory stability (no leaks over 1h load)

### 4. Accessibility Audit (4 tests)
- [ ] WCAG AA on signal cards (color contrast, text sizes)
- [ ] Screen reader (all 6 signals readable)
- [ ] Keyboard nav (Tab, Enter, Escape work)
- [ ] Mobile responsive (signals render on <375px width)

### 5. Edge Case Tests (8 tests)
- [ ] Revoked org (signals show revoked status)
- [ ] Missing mission (mission signal = unknown)
- [ ] Missing website (completeness shows gap)
- [ ] Postcard org (limited data, peer group assigned)
- [ ] Recent org (freshness shows "fresh")
- [ ] Org with no 990 (all signals graceful)
- [ ] Concurrent requests (100 simultaneous)
- [ ] Error handling (invalid EIN, missing org)

### 6. Test Execution Plan (Who/When)
- [ ] Manual testing (QA manual, staging)
- [ ] Automated testing (CI, pre-deploy)
- [ ] Smoke tests (production, post-deploy)

### 7. Blockers & Escalation
- [ ] Critical blocker reporting (Slack #credibility-phase1)
- [ ] Daily summary (what passed, what failed)

---

## ⏱️ CHECK-IN SCHEDULE (Every 3-4 Hours)

### First Check-In (After 3-4 hours)

**Post to #credibility-phase1:**

```
🧪 QA — Stream C Check-In 1

✅ Completed:
- Wrote 12 functional test cases
- Drafted WCAG audit checklist

🔄 In Progress:
- Setting up staging test environment
- Writing performance test suite

🚨 Blockers:
- Waiting for Stage 1 (signals deployment) to test against live API

📊 % Complete: 30%
Next: Test signal API once Stage 1 deploys
```

---

### Second Check-In (After 6-8 Hours)

**Post to #credibility-phase1:**

```
🧪 QA — Stream C Check-In 2

✅ Completed:
- All 12 functional tests written
- Performance test suite complete
- WCAG AA audit checklist done

🔄 In Progress:
- Running performance tests on staging
- Spot-checking edge cases

🚨 Blockers:
- [None] or [specific issue]

📊 % Complete: 70%
Next: Finish edge case tests, compile full checklist
```

---

### Final Check-In (End of Day 1)

**Post to #credibility-phase1:**

```
🧪 QA — Stream C COMPLETE

✅ Deliverables:
- ✅ QA Checklist (7 sections, all tests documented)
- ✅ Functional tests (12 test cases written + executed)
- ✅ Performance tests (6 suites written)
- ✅ WCAG AA audit (4 audits documented)
- ✅ Edge case tests (8 edge cases covered)
- ✅ Execution plan (documented roles, phases)
- ✅ Blocker escalation (procedure + template)

📊 Status: READY FOR INTEGRATION TESTING
Next: Await Stage 4 (staging load) to run full suite
```

---

## 🔧 WHAT YOU NEED TO KNOW (Context)

### 6 Credibility Signals You're Testing

1. **IRS Verification** — verified/unverified/revoked/unknown
2. **Data Freshness** — fresh/aging/stale (based on filing_year)
3. **Expense Ratio** — concern/fair/strong (program % of revenue)
4. **Peer Context** — leader/strong/typical/developing (percentile rank)
5. **Recency & Completeness** — complete/partial/minimal (data gaps)
6. **Mission Alignment** — org-attested/AI-generated/unknown (source)

### Key Test Orgs (Use These)

**Large Org:** EIN that has full 990 data, >$5M revenue  
**Small Org:** EIN with 990 data, $100K-$500K revenue  
**Postcard Org:** EIN with Form 990-N only (<$50K, minimal data)  
**Revoked Org:** EIN marked in `revoked_eins` table  
**Recent Org:** EIN with <6 month old filing  

### Quality Gates You Must Pass

- [ ] All 6 signals compute correctly
- [ ] Page load <200ms (confirmed 3x)
- [ ] Search <400ms (confirmed 10 queries)
- [ ] WCAG AA (no failures on signals)
- [ ] Error handling (graceful on missing data)
- [ ] No data corruption

---

## 🚨 IF YOU HIT A BLOCKER

**Immediate:** Post to #credibility-phase1 with:
- What you're blocked on
- Why (missing data, environment issue, etc)
- What unblocks it

**Example:**
```
🚨 QA BLOCKER — Stream C

Stage 1 (signals deployment) not yet complete.
Cannot run functional tests without live API.

Will proceed with test case writing while waiting.
```

**Don't stop working.** Keep building test cases, checklists, documentation while waiting on dependencies.

---

## ✅ SUCCESS CHECKLIST (Your Definition of Done)

- [ ] All 7 sections of QA Checklist documented
- [ ] 12 functional tests written + validated
- [ ] 6 performance tests written + validated
- [ ] 4 WCAG AA audits completed
- [ ] 8 edge case tests written + validated
- [ ] Test execution plan documented (roles, phases)
- [ ] All tests pass on staging (when Stage 4 loads)
- [ ] No critical blockers (or documented + escalated)
- [ ] Handed off to integration testing team

---

## 📞 ESCALATION (Critical Only)

**Founder:** Akbar Khowaja  
**Slack:** @here in #credibility-phase1 (critical blocker)

---

## 🎯 YOUR FIRST ACTION (Right Now)

1. **Join #credibility-phase1 Slack**
2. **Read this handoff** (you're reading it now ✓)
3. **Start writing test cases** (functional, performance, edge cases)
4. **Post first check-in in 3-4 hours** (progress update to Slack)
5. **Await Stage 1 deployment** (signals live in staging)

---

## 📊 PROGRESS TRACKING (For You)

| Deliverable | Status | By When |
|---|---|---|
| QA Checklist (7 sections) | [ ] | Day 1 EOD |
| Functional tests (12) | [ ] | Day 1 EOD |
| Performance tests (6) | [ ] | Day 1 EOD |
| WCAG AA audit (4) | [ ] | Day 2 EOD |
| Edge case tests (8) | [ ] | Day 2 EOD |
| Execution plan | [ ] | Day 2 EOD |
| All tests passing | [ ] | When Stage 4 ready |

---

## 💡 TIPS

**Keep momentum:**
- Write tests before running them (don't wait for Stage 1)
- Document as you go (not at the end)
- Check in frequently (every 3-4 hours keeps team aligned)

**Test smart:**
- Use the 3 test orgs (large, small, postcard) for most tests
- Spot-check real data (don't just synthetic tests)
- Document failures (don't hide them)

**Communicate clearly:**
- Slack updates should be 1 message, scannable
- Include ✅/🔄/🚨 emoji for status
- Include % complete estimate

---

## GO

Everything is ready. Code is merged. You have approval.

**Start writing test cases now. Check in every few hours.**

🎯
