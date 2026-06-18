# Launch Week Checklist — Aug 15 Public Soft Launch

**Goal:** Ship the public soft launch on Aug 15 with zero critical bugs, 1K+ searchable orgs, 50+ nonprofits claimed, agent working  
**Status:** Everything ready (plans + code + testing)  
**Owner:** Engineer (code) + Akbar (decisions + comms)

---

## Launch Week Timeline (Aug 10–15)

### Sunday Aug 10 (Sandbox Testing Starts)

**Morning (Engineer + Akbar, 1 hour)**

- [ ] Deploy to staging server (final pre-public environment)
  - [ ] Frontend built + served on droplet
  - [ ] API responding on port 5000
  - [ ] Elasticsearch indexed with all 1M orgs
  - [ ] Database migrations applied
  - [ ] All 6 endpoints tested locally

- [ ] Smoke test (5 min)
  ```bash
  # GET /health → {"status": "ok"}
  curl http://localhost:5000/health
  
  # GET /api/orgs?q=climate → results
  curl "http://localhost:5000/api/orgs?q=climate&limit=5"
  
  # POST /api/claims/submit → approved/flagged
  curl -X POST http://localhost:5000/api/claims/submit \
    -H "Content-Type: application/json" \
    -d '{
      "org_ein": "001234567",
      "org_name": "Test Org",
      "website": "https://test.org",
      "claimer_email": "test@test.org"
    }'
  ```

- [ ] Launch 50 nonprofit sandbox
  - [ ] Send claiming links to all 50 nonprofits (SANDBOX_RECRUITMENT_GUIDE.md Email #3)
  - [ ] Instructions clear? Y/N
  - [ ] Tech support email monitored (engineer on-call)

**Mid-day (Akbar)**

- [ ] Announce to founding partners
  - [ ] "We're live in beta testing today. Public launch Friday."
  - [ ] Feedback forms ready
  - [ ] Partner dashboard live (if any)

**EOD**

- [ ] First tech support issues logged
  - [ ] Any claiming blockers? Fix immediately
  - [ ] Any search issues? Fix immediately
  - [ ] Performance baseline (response times): _______________

---

### Monday Aug 11 (Sandbox Testing Full Swing)

**Morning (9am standup)**

- [ ] Engineer report
  - [ ] How many nonprofits claimed so far? [X]
  - [ ] Auto-approval rate? [X]%
  - [ ] Any critical bugs? [Yes/No] [If yes, list]
  - [ ] Search working for all cause/location/health filters?
  - [ ] Wallet persisting correctly?

- [ ] Plan for day: bug fixes only, no new features

**Throughout Day**

- [ ] Monitor support emails
  - [ ] Any claiming issues? Fix immediately
  - [ ] Any search issues? Fix immediately
  - [ ] Any agent failures? Debug + fix

- [ ] Collect feedback (SANDBOX_RECRUITMENT_GUIDE.md feedback form)
  - [ ] Responses coming in? Y/N
  - [ ] Common themes? _______________

**EOD**

- [ ] Update PARTNER_TRACKER.md
  - [ ] Partner updates? Any concerns heard?
  - [ ] Nonprofit traction so far? [X] claims

---

### Tuesday Aug 12 (Testing + Fixes)

**Morning (9am standup)**

- [ ] Status from engineer
  - [ ] Bugs fixed since yesterday: [list]
  - [ ] Outstanding issues: [list]
  - [ ] Claims: [X] total
  - [ ] Auto-approval rate holding? [X]%

- [ ] Status from Akbar
  - [ ] Partner feedback? _______________
  - [ ] Nonprofit feedback? _______________
  - [ ] Any scope creep? (Stop it)

**Mid-day**

- [ ] Run full QA checklist (SPRINT_1_TESTING_STRATEGY.md Manual QA Checklist)
  - [ ] Search page: all 7 features tested? Y/N
  - [ ] Detail page: all 5 elements rendering? Y/N
  - [ ] Wallet: persistence working? Y/N
  - [ ] Claim form: all 4 steps working? Y/N
  - [ ] Agent: 80%+ auto-approval? Y/N

- [ ] Performance check
  - [ ] Search <500ms? Y/N [Actual: _____ ms]
  - [ ] Detail <200ms? Y/N [Actual: _____ ms]
  - [ ] Wallet <100ms? Y/N [Actual: _____ ms]

- [ ] Security baseline
  - [ ] HTTPS only? Y/N
  - [ ] No API keys in logs? Y/N
  - [ ] Rate limiting working? Y/N

**EOD**

- [ ] Decide: Ready for public? Y/N / [If not, what's blocking?]

---

### Wednesday Aug 13 (Final QA + Bug Fixing)

**Morning (9am standup)**

- [ ] Engineer status
  - [ ] How many bugs fixed yesterday? [X]
  - [ ] Outstanding critical bugs? [Y/N] [If Y, list]
  - [ ] Outstanding minor bugs? [Y/N] [If Y, defer to Sep 1]
  - [ ] Test suite passing? Y/N

- [ ] Sandbox update
  - [ ] Claims: [X] total
  - [ ] Feedback collected: [X] responses
  - [ ] Any patterns in feedback? _______________

**All Day**

- [ ] Deep QA (focus: edge cases + error handling)
  - [ ] Search with 0 results → helpful message? Y/N
  - [ ] Invalid EIN claim → proper rejection? Y/N
  - [ ] Non-domain email claim → proper flag? Y/N
  - [ ] Website unreachable → proper flag? Y/N
  - [ ] Missing fields in claim → validation error? Y/N

- [ ] Regression test suite (full pytest + Playwright)
  - [ ] All unit tests pass? Y/N
  - [ ] All integration tests pass? Y/N
  - [ ] All E2E tests pass? Y/N
  - [ ] Coverage ≥80%? Y/N

- [ ] Documentation check
  - [ ] API documentation complete? Y/N
  - [ ] Codebase comments where needed? Y/N
  - [ ] Deployment runbook clear? Y/N
  - [ ] Known issues documented? Y/N

**EOD**

- [ ] Decision: Ready to go public Friday? Y/N
  - [ ] If NO: what needs fixing? [Fix immediately Thurs]
  - [ ] If YES: prepare announcement materials

---

### Thursday Aug 14 (Final Push + Preparation)

**Morning (9am standup)**

- [ ] Engineer status
  - [ ] Any last-minute bugs fixed? [X]
  - [ ] Test suite still passing? Y/N
  - [ ] Ready to go live tomorrow? Y/N

- [ ] Sandbox status
  - [ ] Final claim count: [X] of 50
  - [ ] Any last feedback? _______________
  - [ ] Thank you emails ready to send? Y/N

**Mid-day**

- [ ] Final checks before public
  - [ ] Database backed up? Y/N
  - [ ] Rollback plan documented? Y/N (git tag from yesterday's version)
  - [ ] Monitoring/alerting set up? Y/N
  - [ ] Support email monitored (engineer on-call)? Y/N

- [ ] Prepare announcement
  - [ ] Blog post written (for daanaa.org homepage)? Y/N
  - [ ] Social media posts drafted (Twitter, LinkedIn)? Y/N
  - [ ] Email to sandbox partners drafted? Y/N
  - [ ] Email to founding partners drafted? Y/N

- [ ] Prepare launch day comms
  - [ ] Status page ready (uptime status)? Y/N
  - [ ] Support email template ready? Y/N
  - [ ] "We're live!" announcement text ready? Y/N

**EOD**

- [ ] Dry run: can you deploy the exact code that will go public? Y/N
  - [ ] Full fresh install on staging? Y/N
  - [ ] All migrations run cleanly? Y/N
  - [ ] All tests pass on staging? Y/N
  - [ ] Search index loads fully? Y/N

- [ ] Final Stewardship check (use WEEKLY_STEWARDSHIP_CHECK.md)
  - [ ] No principle violations? Y/N
  - [ ] Ready to ship? Y/N
  - [ ] Document any last-minute decisions in DECISIONS.md

---

### Friday Aug 15 (LAUNCH DAY)

**Morning (6am–9am, Engineer + Akbar)**

- [ ] Final smoke test (30 min before public)
  - [ ] All 6 API endpoints responding
  - [ ] Elasticsearch search working
  - [ ] Agent running without errors
  - [ ] Wallet persisting
  - [ ] <500ms search, <200ms detail

- [ ] Deploy to production
  - [ ] Engineer runs: `./safe_deploy.sh` (or your deploy script)
  - [ ] Frontend rebuilt and served on droplet
  - [ ] API restarted on home server
  - [ ] All services healthy? Y/N

- [ ] Post-deploy verification (5 min)
  - [ ] Frontend loads at daanaa.org? Y/N
  - [ ] Search works? Y/N
  - [ ] Detail page works? Y/N
  - [ ] Wallet works? Y/N
  - [ ] Claim form works? Y/N

**9am (Morning Announcement)**

- [ ] Post to social media + send emails
  - [ ] Twitter: "Daanaa is live! 1.87M nonprofits, evidence-based discovery, free for all"
  - [ ] LinkedIn: [Longer version of why this matters]
  - [ ] Email to sandbox partners: "You helped us ship this. Thank you!"
  - [ ] Email to founding partners: "We made it. Here's what's live..."

**9am–5pm (Launch Day Monitoring)**

- [ ] Engineer on-call (standing by for critical issues)
  - [ ] Monitor error logs continuously
  - [ ] Check API response times every 30 min
  - [ ] Check database health
  - [ ] Monitor support email (watch for patterns)
  - [ ] Slack/available for urgent fixes

- [ ] Akbar on-call (standing by for comms issues)
  - [ ] Monitor social media feedback
  - [ ] Send manual responses to early users if needed
  - [ ] Manage founding partner/sandbox partner comms
  - [ ] Celebrate milestones (1K searches, 100 claims, etc.)

**Hourly Status (Aug 15, 9am–5pm)**

| Time | API Health | Search Status | Agent Status | Uptime | Notes |
|------|-----------|---------------|--------------|--------|-------|
| 9am | ✓ | ✓ | ✓ | 100% | Launched! |
| 10am | ✓ | ✓ | ✓ | 100% | [note] |
| 11am | ✓ | ✓ | ✓ | 100% | [note] |
| 12pm | ✓ | ✓ | ✓ | 100% | [note] |
| 1pm | ✓ | ✓ | ✓ | 100% | [note] |
| 2pm | ✓ | ✓ | ✓ | 100% | [note] |
| 3pm | ✓ | ✓ | ✓ | 100% | [note] |
| 4pm | ✓ | ✓ | ✓ | 100% | [note] |
| 5pm | ✓ | ✓ | ✓ | 100% | [note] |

**EOD (5pm)**

- [ ] Celebrate 🎉
  - [ ] You shipped it
  - [ ] 1K+ nonprofits searchable
  - [ ] 50+ claimed profiles
  - [ ] Agent working (80%+ auto-approval)
  - [ ] Zero critical bugs blocking users
  - [ ] 99.9%+ uptime

- [ ] Send end-of-day summary
  - [ ] To founding partners: "We did it! Launch stats + thank you"
  - [ ] To sandbox partners: "You're live! See you on the platform"
  - [ ] Internal: "Success. Minor issue X noted for Sep 1 sprint"

---

## If Something Breaks (Disaster Recovery)

### Critical Bug Found (Search broken, agent down, API errors)

1. **Immediate (minute 1):**
   - Engineer: investigate + attempt fix
   - Akbar: post on status page "We're aware of X, working on it"

2. **Within 5 minutes:**
   - If fixable in <15 min → fix + redeploy
   - If >15 min → prepare rollback

3. **Rollback decision (if fix takes >30 min):**
   - Redeploy yesterday's git tag: `git reset --hard [previous-tag]`
   - Frontend + API restart
   - Verify all systems healthy
   - Post: "We rolled back. Investigating issue. ETA for fix: [time]"

4. **After fix:**
   - Fixed version tested on staging (20 min)
   - Redeploy to production
   - Verify systems healthy
   - Post: "Fixed and redeployed. Thanks for patience."

### Minor Bug (Sorting wrong, label unclear, slow query)

- Log it, don't fix during launch day
- Create issue for Phase 2 sprint (Sep 1)
- Continue monitoring other systems

---

## Success Criteria (Aug 15 EOD)

✅ **Deployment**
- [ ] Frontend live at daanaa.org
- [ ] API responding on port 5000
- [ ] All 6 endpoints working
- [ ] Elasticsearch search working
- [ ] Agent auto-approving claims

✅ **Performance**
- [ ] Search <500ms: [Actual: _____ ms]
- [ ] Detail <200ms: [Actual: _____ ms]
- [ ] Uptime 99.9%: [Actual: _____ %]

✅ **Features**
- [ ] 1K+ nonprofits searchable: [Actual: _____ ]
- [ ] Claim form working: Y/N
- [ ] Wallet persisting: Y/N
- [ ] Agent 80%+ auto-approval: [Actual: _____ %]

✅ **Quality**
- [ ] Zero critical bugs blocking users: Y/N
- [ ] All tests passing: Y/N
- [ ] No API errors in logs: Y/N

✅ **Sandbox**
- [ ] 50+ nonprofits claimed: [Actual: _____ ]
- [ ] Feedback collected: [Actual: _____ responses]
- [ ] Thank you emails sent: Y/N

✅ **Comms**
- [ ] Founding partners notified: Y/N
- [ ] Sandbox partners notified: Y/N
- [ ] Social media announced: Y/N
- [ ] Status page up: Y/N

---

## Post-Launch (Aug 16+)

### Aug 16 (Day After)

- [ ] Review launch logs + feedback
- [ ] Document any issues in LESSONS.md
- [ ] Plan Phase 2 start date (Aug 20? Sep 1?)
- [ ] Celebrate with team

### Aug 20–31 (First Two Weeks)

- [ ] Monitor for stability issues
- [ ] Fix P1 bugs from launch
- [ ] Collect user feedback (nonprofits + donors)
- [ ] Plan volunteer matching sprint (Phase 2)

### Sep 1 (Phase 2 Kickoff)

- [ ] Launch volunteer interest signals
- [ ] Nonprofit admin dashboard
- [ ] Support Triage Agent
- [ ] All 5 agents operational

---

## People + Responsibilities

| Role | Aug 10–14 | Aug 15 Morning | Aug 15 (9am–5pm) | Aug 15 EOD |
|------|-----------|---|---|---|
| **Engineer** | Testing + fixes | Deploy (6–9am) | Monitor + stand by for fixes | Send EOD summary |
| **Akbar** | Sandbox + comms | Final verification | Monitor feedback + comms | Celebrate + debrief |

---

## Resources

- **Deployment script:** `./safe_deploy_droplet.sh` (or equivalent)
- **Rollback:** `git reset --hard [previous-tag]`
- **Monitoring:** logs + status page
- **Support:** support@daanaa.org (monitored by engineer)
- **Social:** Twitter (@daanaaorg), LinkedIn (if account exists)

---

**Owner:** Engineer + Akbar  
**Status:** Ready  
**Launch Date:** Aug 15, 2026  
**Confidence:** 9/10 (all systems ready, one last run-through recommended)

---

*This checklist is your launch day playbook. Print it. Check items as you go. If something isn't on here that you're doing, add it. If something doesn't apply, cross it out. Make it yours.*

*Launch day is a celebration of all the work done to get here.*

*Ship it.*
