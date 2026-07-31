# PHASE 1: TODAY'S KICKOFF (Immediate Actions)
## July 31, 2026 | Start Execution Now

---

## 🎯 TODAY'S MISSION

**Get Stage 1 (signals) deploying + all parallel streams (A-F) started.**

No waiting. Move immediately.

---

## ✅ STAGE 1: DEPLOY SIGNALS (START NOW)

### Owner: Backend Engineer

**Time:** 1-2 hours  
**Task:** Deploy signals to staging environment

**Steps:**

1. **Verify code is on master**
   ```bash
   git log --oneline -5 | grep "Implement 6 credibility signals"
   ```

2. **Copy signals module to staging environment**
   ```bash
   cp scripts/credibility_signals.py /staging/scripts/
   cp tests/test_credibility_signals.py /staging/tests/
   ```

3. **Verify API endpoint is live**
   ```bash
   curl -s http://localhost:5000/api/organizations/521231983/signals | python3 -m json.tool
   ```

4. **Test signal computation**
   - Sample 3 orgs (large, small, postcard)
   - Verify all 6 signals return
   - Check response time <200ms
   - Verify confidence scores (0-100)

5. **Report result**
   - Post to #credibility-phase1: "✅ Stage 1 COMPLETE - Signals live in staging"

**Quality Gate:** API responds <200ms, all 6 signals correct

**If Pass:** → Stage 2 can start anytime  
**If Fail:** → Post blocker to #credibility-phase1, escalate to founder

---

## 📊 STAGE 2: INGEST POSTCARD DATA (START WHEN DATA AVAILABLE)

### Owner: Data Engineering

**Time:** 6-8 hours (can run in parallel with Stage 1)  
**Task:** Download, transform, validate 200K postcard nonprofits

**Steps:**

1. **Get Form 990-N data source**
   - IRS data.irs.gov (Form 990-N e-postcard)
   - Or ProPublica data API
   - Confirm access by EOD today

2. **Run transformation pipeline**
   ```bash
   python3 scripts/postcard_prep_pipeline.py
   ```

3. **Validate output**
   - Check for data corruption
   - Verify EIN uniqueness
   - Confirm state codes valid
   - Spot-check 10 random records

4. **Stage data for load**
   - Output goes to `data/postcard_staging.json`
   - Confirm file size and record count
   - Ready for Ops to load to staging

5. **Report result**
   - Post to #credibility-phase1: "✅ Stage 2 COMPLETE - 200K postcards staged"

**Quality Gate:** Zero data corruption, EIN uniqueness verified

**If Pass:** → Ready for Stage 4 (load)  
**If Fail:** → Post blocker, escalate same day

---

## 🚀 STAGES A-F: PARALLEL STREAMS (START TODAY)

### All streams run in parallel (no dependencies)

**Stream A: Methodology Page + Copy**
- Owner: Product + Legal
- Deliverable: Public methodology page (internal review)
- Timeline: 3-4 days
- Status: ✅ START TODAY
- Slack: #credibility-phase1

**Stream B: UI/Copy + Tooltips**
- Owner: Design + Copy
- Deliverable: Signal cards, tooltips, responsive design
- Timeline: 3-4 days
- Status: ✅ START TODAY
- Slack: #credibility-phase1

**Stream C: QA Plan + Test Cases**
- Owner: Product QA
- Deliverable: Test plan, functional tests, edge cases
- Timeline: 2-3 days
- Status: ✅ START TODAY
- Slack: #credibility-phase1

**Stream D: Accessibility Audit**
- Owner: A11y Lead
- Deliverable: WCAG AA audit, remediation log
- Timeline: 2-3 days
- Status: ✅ START TODAY
- Slack: #credibility-phase1

**Stream F: Rollback Plan**
- Owner: Ops Lead
- Deliverable: Documented rollback procedure, dry-run tested
- Timeline: 1-2 days
- Status: ✅ START TODAY
- Slack: #credibility-phase1

---

## 📞 DAILY ASYNC STANDUP TEMPLATE

**Post daily to #credibility-phase1 (no scheduled call)**

```
🚀 [YOUR_NAME] — [STREAM_X] standup

✅ Yesterday:
- [What you shipped]

🔄 Today:
- [What you're building]

🚨 Blockers:
- [Any issues? (or "none")]

📊 Status: [ON_TRACK / AT_RISK / BLOCKED]
```

**Example:**

```
🚀 Jane — Stream B (UI/Copy) standup

✅ Yesterday:
- Completed signal card designs
- Drafted copy for all 6 signals

🔄 Today:
- Build tooltips for Confidence Badge
- Mobile responsiveness testing

🚨 Blockers:
- Need design token for navy (using var now)

📊 Status: ON_TRACK
```

---

## 🎯 TODAY'S CHECKLIST

### Right Now (Next 30 min)

- [ ] Backend: Start Stage 1 (deploy signals)
- [ ] Data Eng: Confirm Form 990-N data access path
- [ ] Product: Create #credibility-phase1 Slack channel
- [ ] All: Join #credibility-phase1

### Next 1-2 Hours

- [ ] Backend: Deploy signals + verify API endpoint
- [ ] Design: Start Stream B (UI/Copy design)
- [ ] QA: Start Stream C (test plan)
- [ ] A11y: Start Stream D (accessibility audit)
- [ ] Ops: Start Stream F (rollback plan)

### By EOD Today

- [ ] Backend: Report Stage 1 status to #credibility-phase1
- [ ] Data Eng: Report data source status
- [ ] All leads: First async standup posted to #credibility-phase1

---

## 🎯 SUCCESS TODAY

✅ Stage 1 signals deployed to staging  
✅ Stages A-F all started (parallel work underway)  
✅ Form 990-N data access confirmed  
✅ #credibility-phase1 Slack channel active  
✅ First async standups posted  

---

## 📋 WHAT COMES NEXT (This Week)

- **Day 2-3:** Stage 2 (postcard data) completes
- **Day 3-4:** Stages A-F complete
- **When ready:** Stage 4 (load to staging)
- **When ready:** Stage 5 (integration testing)
- **When ready:** Stage 6 (launch to production)

---

## 🚨 IF YOU HIT A BLOCKER TODAY

1. **Post to #credibility-phase1** with:
   - What you're blocked on
   - Why it's blocked
   - What unblocks it

2. **Tag founder** if it's critical (needs decision same day)

3. **Don't wait.** Keep moving on other work while blocker resolves.

---

## 📞 KEY CONTACTS

**Founder (Governance/Decisions):** Akbar Khowaja  
**Technical Lead:** Claude Code  
**Slack:** #credibility-phase1 (async updates)  

---

## ✅ GO

Everything is ready. Code is merged. Governance is locked. You have approval.

**Start Stage 1 now.** Start Stages A-F now. Post first updates to Slack by EOD.

No waiting. Move.

🚀

---

**Next Check-In:** Tomorrow EOD  
**Status:** ALL SYSTEMS GO  
**Action:** EXECUTE IMMEDIATELY
