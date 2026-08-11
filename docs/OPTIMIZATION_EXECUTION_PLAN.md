# 5 OPTIMIZATIONS + OPEN ITEMS EXECUTION PLAN

**Date:** 2026-08-10  
**Coordinator:** Claude Code + Codex  
**Strategy:** Parallel workstreams, critical path first  

---

## WORKSTREAM COORDINATION

### CRITICAL PATH (Blocks Other Work)

**Workstream A: Emergency Fixes + Pre-Commit (12 hours total)**
- Fix Cron ImportError (1-2h)
- Fix Inference Server diagnosis (1-2h)
- Fix Watchdog state comparison (1-2h)
- **[PARALLEL]** Implement pre-commit hooks (4h)
- **[PARALLEL]** Implement daemon health standard (3h)
- **Status:** Ready to ship this week

**Workstream B: Test-First Infrastructure (5 hours)**
- Unit tests for critical paths (Cron, Inference, Watchdog)
- Contract tests for API routes
- CI integration
- **Status:** Integrated with pre-commit, shipping this week

### SECONDARY PATH (Optimization, Not Blocking)

**Workstream C: Precompute Snapshots (6 hours)**
- Modular phase system with checkpoints
- Resume logic
- Drift detection
- **Status:** Week 2, after emergency fixes verified

**Workstream D: Ops Runbook Generator (2 hours)**
- Auto-generate from LESSONS.md
- Deploy to wiki
- **Status:** Week 2, lightweight

### FOUNDER WORK (P11, P2, P6 Phase 2)

**Workstream E: Open Items**
- P11 succession policy approval (waiting on founder decision)
- P2 authentication ranking (autonomous engineering, no blocker)
- P6 Phase 2 remediation plan (ready when fixes verified)
- Local memory Phase 1 (can start immediately, 3h user time)

---

## EXECUTION SCHEDULE

### This Week (Aug 10-16)

**Mon-Tue (Aug 10-11):** Emergency fixes + tests
- [ ] Cron ImportError root cause fix
- [ ] Inference Server diagnosis + fix
- [ ] Watchdog state logic fix
- [ ] Unit tests for all three
- **Target:** All tests passing, no regressions

**Tue-Wed (Aug 12-13):** Pre-commit + daemon health
- [ ] Pre-commit hook integration
- [ ] Daemon health standard library
- [ ] Retrofit all scripts to use daemon_health_lib.py
- [ ] Watchdog updated to read published state
- **Target:** All daemons publish health; watchdog reads state

**Thu (Aug 14):** Quality gates + integration
- [ ] Codex review of all code
- [ ] Full test run (emergency fixes + new infrastructure)
- [ ] Smoke test on staging
- [ ] Documentation

**Fri (Aug 15):** Deployment + verification
- [ ] Deploy emergency fixes + pre-commit + daemon health
- [ ] Monitor for 24h
- [ ] Confirm P6 critical issues resolved

**Sat-Sun (Aug 16-17):** Measurement + review
- [ ] Week 1 recall log for local memory Phase 1
- [ ] P6 fix verification dashboard
- [ ] Prepare P6/P2/P11 Phase 2 recommendations for founder

### Week 2 (Aug 19-23)

**Mon-Wed:** Precompute snapshots + test suite completion
**Thu:** Ops runbook + documentation
**Fri:** Week 2 Phase 2 deliverables (P6/P2/P11)

---

## WHAT YOU DO (User)

**Parallel with our work:**

1. **Start Phase 1 memory system (3h, anytime this week)**
   - We'll have scripts ready
   - You run auto-save, manual search, log recalls
   - By Aug 16, you'll have 1 week of recall data

2. **P11 succession decision (async, this week)**
   - Review P11_FINDINGS_PHASE1.md
   - Approve succession language + recording method
   - Designate trustees (if hybrid backup chosen)

3. **P2 authentication decision (async, optional this week)**
   - We'll rank alternatives autonomously
   - You review + approve if recommendation changes privacy model

4. **Monitor P6 fixes (passive, this week)**
   - We'll deploy emergency fixes Fri Aug 15
   - You verify: Cron errors gone, Inference responding, Watchdog accurate
   - Confirm no regressions

---

## DELIVERABLES BY DATE

### Thursday, Aug 14 (Pre-Ship Review)
- [ ] 5-file code package (pre-commit, daemon health, tests, fixes, hook config)
- [ ] Codex review report (quality gates, risks, trade-offs)
- [ ] Smoke test results (all 3 fixes verified on staging)
- [ ] Deployment runbook (what ships, in what order, rollback procedure)

### Friday, Aug 15 (Deployed)
- [ ] Live on production
- [ ] Monitoring dashboards active
- [ ] Incident response runbook ready

### Saturday, Aug 16 (Week 1 Summary)
- [ ] P6 critical issues resolved? (Cron ImportError gone? Inference healthy? Watchdog accurate?)
- [ ] Recall log for Phase 1 memory (1 week of data)
- [ ] Prepare P6/P2/P11 Phase 2 decisions

---

## RISK MITIGATION

**Pre-commit strictness:** Test locally first; only enforce at push (not at commit).  
**Daemon health transition:** Run both old (log) + new (state) in parallel for 1 week; flip to state-only if no issues.  
**Test coverage:** Start with critical paths (Cron, Inference, Watchdog); expand later.  
**Precompute checkpoints:** Build on staging first; verify resume logic before prod.

---

## SUCCESS CRITERIA

**Week 1:**
- ✅ Emergency fixes deployed and verified
- ✅ Pre-commit + daemon health live (no false negatives)
- ✅ All tests passing
- ✅ Zero regressions on prod
- ✅ P6 critical issues resolved (Cron <10 errors/day, Inference responding, Watchdog accurate)

**Week 2:**
- ✅ Precompute snapshots shipping
- ✅ Ops runbook deployed
- ✅ P6/P2/P11 Phase 2 decisions made

**By end of month:**
- ✅ Infrastructure hardened (no new LESSONS.md entries for previous patterns)
- ✅ Rework reduced (failed precomputes stay <15 min)
- ✅ Security posture improved (daemons publish state, tests catch critical breakage)

---

## CODEX OVERSIGHT GATES

**Codex will challenge:**
1. **Each fix:** Is this the root cause, or a band-aid?
2. **Test coverage:** Does this actually prevent the failure from recurring?
3. **Performance impact:** Do pre-commit hooks slow down dev workflow?
4. **Transition risk:** Can we run old + new in parallel to reduce flip risk?

**Codex will approve before deploy:**
- [ ] Root cause analysis is solid
- [ ] Tests capture the failure scenario
- [ ] No false positives in automation
- [ ] Rollback plan is clear

---

**Start now. Report status daily. Codex reviews EOD each day.**

