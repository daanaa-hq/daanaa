# Early User Outreach — Phase 2 Feedback

## Email Template: Initial Feedback Request

**To:** Early nonprofit partners using volunteer hours feature

---

**Subject:** We'd love your feedback on Daanaa's new volunteer hours feature

Hi [Name],

You've been using Daanaa's new volunteer hours feature. We'd love to know how it's working.

**Quick questions (2 min):**
1. Have you submitted any volunteer hours yet?
2. Did the process feel straightforward?
3. What was hardest, if anything?
4. One thing we could improve?

**Just reply to this email** or use our feedback form: [form URL — to be created]

Your feedback directly shapes what we build next.

Thanks,  
Akbar & the Daanaa Team

---

## Target List (Week 1)

**Nonprofits we know are active:**
- American Red Cross (360822808) - guild member, likely to try features
- Nature Conservancy (135630589) - guild member
- YMCA (236527919) - guild member
- Boys & Girls Clubs (133921386) - guild member
- Room to Read (943412822) - guild member

**How to reach:**
- LinkedIn (org pages)
- Email via website contact form
- Direct contact if you have it

**Goal:** Get feedback from ≥5 nonprofits + ≥10 volunteers in first 2 weeks

---

## Feedback Follow-up (If They Reply)

**If positive:** "That's great! Please keep using it. Let us know if anything changes."

**If negative/confused:** 
1. Ask clarifying question ("Can you describe what happened?")
2. Offer to jump on a quick call (15 min)
3. Document the issue
4. Check if it's a real bug or just documentation gap
5. Fix + follow up with solution

**If feature request:**
1. Thank them
2. Add to roadmap (note who requested it)
3. Give timeline if known ("We're exploring that for Q3")
4. Don't over-promise

---

## Weekly Check Schedule

**Every Monday 9am:**

```bash
# 1. Check emails (2 min)
# 2. Scan error logs (5 min)
ssh root@162.243.97.179 "tail -50 /opt/daanaa/logs/error.log | grep -E 'volunteer|guild' || echo 'No recent errors'"

# 3. Check database (2 min)
sqlite3 /home/akbar/meritgiving/data/merit_registry.db << 'SQL'
SELECT 'Volunteer Submissions' as metric, COUNT(*) FROM volunteer_hours
UNION ALL
SELECT 'Pending Approvals', COUNT(*) FROM volunteer_hours WHERE status='pending'
UNION ALL
SELECT 'Approved', COUNT(*) FROM volunteer_hours WHERE status='approved';
SQL

# 4. Manual spot check (5 min)
# - Visit /partner/salesforce-nonprofit
# - Visit random org detail page
# - Check /volunteer/submit on mobile

# 5. Log findings (2 min)
# - Anything concerning? → note it
# - Good news? → celebrate it
# - Users complaining? → add to feedback log
```

---

## Feedback Log (Spreadsheet Template)

Keep a running spreadsheet with these columns:

| Date | User Type | Feature | Category | Severity | Feedback | Status | Action | Owner | Deadline |
|------|-----------|---------|----------|----------|----------|--------|--------|-------|----------|
| 2026-07-05 | Nonprofit | Volunteer Hours | Bug | Medium | Email didn't match error confusing | new | Document + test | - | - |
| 2026-07-05 | Volunteer | Volunteer Hours | Feature Request | Low | Bulk upload CSV would save time | new | Add to Q3 roadmap | - | - |

**Store at:** [TBD - Google Sheets, Notion, or GitHub Issues]

---

## Success Metrics (30 days)

Track these by July 31:

- [ ] Feedback collected from ≥5 nonprofits
- [ ] Feedback collected from ≥10 volunteers
- [ ] ≥1 bug fixed based on user report
- [ ] ≥3 documentation updates based on confusion points
- [ ] 0 critical unfixed issues
- [ ] Approval rate trending (should be >70%)

---

## If You Find a Bug

1. **Reproduce locally** — does it happen on localhost?
2. **Check the logs** — what does the error message say?
3. **Fix it** — make the fix in code
4. **Test it** — confirm fix works
5. **Deploy it** — push to droplet
6. **Tell the user** — email them the fix

Timeline: **24 hours** for anything users hit.

---

## Next Steps

1. **This week:** Send outreach emails to 5 nonprofits
2. **This week:** Prepare to run Monday weekly check
3. **Week 2:** Review feedback, identify patterns
4. **Week 3:** Decision gate (proceed to Phase 3 or fix issues?)

---

**Status: Ready to reach out**

Start with American Red Cross + Nature Conservancy this week.
