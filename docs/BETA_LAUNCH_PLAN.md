# Nonprofit Claiming Flow — Beta Launch Plan

**Date:** June 22, 2026  
**Status:** Ready for phased beta launch to 3–5 test nonprofits  
**Duration:** 2 weeks (June 22 – July 6)  

---

## What We're Testing

Complete end-to-end nonprofit claiming flow:
1. ✅ **Pre-verification:** PIN entry (ClaimVerify)
2. ✅ **Data transparency:** Show IRS data, sources, freshness (NEW)
3. ✅ **Data update option:** Nonprofit can correct stale/wrong info (NEW)
4. ✅ **Complete claim:** Mission, story, cause tags (OrgClaimEditor)
5. ✅ **Welcome dashboard:** Confirmation of claim + showing update status (ClaimSuccess)

All components built and tested locally. Ready for real users.

---

## Phase 1: Beta Launch to 3–5 Nonprofits

### Who to Invite
**Selection criteria:** Organizations you already know + have direct contact with
- Mix of sizes (small, mid, large)
- Diverse causes (arts, health, community dev)
- Known to be tech-friendly and patient
- Ideally people who've already seen the organization profile on daanaa.org

**Example test cohort (customize with real orgs):**
1. **Org A:** Small ($100K–$500K), strong local community presence
2. **Org B:** Mid-sized ($500K–$2M), tech-savvy ED
3. **Org C:** Large ($2M+), mission-critical + relationship with Akbar

### Outreach Email Template

```
Subject: Help us launch a new claiming feature for nonprofits

Hi [ED Name],

We're launching a new way for nonprofits to claim and manage their Daanaa profile. 
Before we open it widely, we're testing with a handful of organizations we know and trust.

We'd love for [Your Org] to be a beta testing partner for the next 2 weeks.

What you'll do:
1. Claim your organization's profile on Daanaa (takes ~10 minutes)
2. Review the financial data we have (from IRS records)
3. Optionally update any outdated information
4. Fill in your mission statement and impact areas
5. Answer a few quick questions about your experience

Why it matters:
- You'll be one of the first to claim your profile on Daanaa
- Your feedback directly shapes the feature before we launch widely
- You can update your financial data (usually 1–2 years old) immediately
- Your peer context will update within 2–3 business days

If interested, just reply or click here: [claiming-flow-link]

Takes ~10 minutes. No experience needed — we'll walk you through it.

Thanks for being an early partner,
Akbar
```

### Launch Sequence

**Day 1 (June 22, AM):** Send outreach to 3–5 nonprofits
- Aim for 80%+ response rate (they know you)
- Schedule verification calls if they prefer phone

**Days 2–5:** Test orgs claim + provide feedback
- Monitor for errors in logs
- Collect feedback via email/phone
- Track: claim success rate, data update adoption, time-to-complete

**Days 6–10:** Iterate on feedback
- Fix critical bugs (if any)
- Adjust copy based on real user reactions
- Document what worked, what didn't

**Days 11–14:** Final stabilization
- Run final end-to-end test with fresh org
- Monitor for edge cases
- Prepare for Phase 2 (gradual rollout to more nonprofits)

---

## Success Criteria (14-Day Beta)

**Technical:**
- ✅ All 3–5 test orgs successfully complete claiming flow
- ✅ No critical errors (errors logged, but don't block flow)
- ✅ API endpoints respond in <500ms
- ✅ Data transparency shows correct IRS values
- ✅ Update form submits successfully and stores data
- ✅ No data leaks or privacy violations

**User Experience:**
- ✅ Nonprofits report "easy to use" (subjective, but important)
- ✅ At least 1–2 nonprofits update their financial data (proof of engagement)
- ✅ Claiming takes <15 minutes
- ✅ No confusion about "why are we showing IRS data?"
- ✅ Clear understanding that updates take 2–3 days to impact peer context

**Operational:**
- ✅ You can handle 3–5 support questions without stress
- ✅ Process for fielding feedback is documented
- ✅ Dashboard/logs show what's happening (errors, submissions, etc.)

---

## What to Monitor During Beta

### Daily Standup (5 minutes)
```
Questions to check:
1. Did all orgs successfully claim? (check claim status table)
2. Any API errors? (check logs/error tracking)
3. Any support emails? (respond within 24h)
4. Any unexpected behaviors? (ask orgs in follow-up emails)
```

### Database Queries

**Check claim status:**
```sql
SELECT ein, claim_status, verified_at, custom_mission
FROM org_claims
WHERE ein IN ('org1', 'org2', 'org3')
ORDER BY verified_at DESC;
```

**Check if any orgs submitted financial updates:**
```sql
SELECT ein, status, submitted_at, submitted_total_revenue
FROM org_nonprofit_updates
WHERE ein IN ('org1', 'org2', 'org3')
ORDER BY submitted_at DESC;
```

**Check API errors:**
```bash
tail -100 logs/daanaa_api.log | grep -i error
```

### Metrics to Track

Track these in a simple spreadsheet or notes:

| Org | Claim Completion | Time to Complete | Data Updated? | Feedback | Issues |
|-----|------------------|------------------|---------------|----------|--------|
| Org A | ✅ | 8 min | No | "Clear flow, easy" | None |
| Org B | ✅ | 12 min | Yes | "Updated revenue" | None |
| Org C | ✅ | 15 min | No | "Why is revenue from 2024?" | Request: show tax year |

---

## Common Issues (Likely + Fixes)

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| "PIN expired" | Too much time between /for-nonprofits and claim | Extend PIN validity in backend (currently 24h) |
| "Data is wrong" | IRS data is actually wrong (or different fiscal year) | Data update form handles this — test it |
| "I didn't see the update button" | UX — button placement unclear | Move button higher or make more visible |
| "How long until my peer context updates?" | Not stated clearly | Update dashboard to show "pending_scoring" status |
| "Can I edit later?" | Unclear if claim is final | Clarify that dashboard allows editing anytime |

---

## After Beta (Days 15–21)

### Decide: Go Wider or Iterate?

**Go wider if:**
- ✅ 3/3 orgs completed successfully
- ✅ No critical bugs
- ✅ Positive feedback on clarity + ease
- ✅ At least 1 org updated data

**Iterate if:**
- ⚠️ Copy confusion (orgs didn't understand something)
- ⚠️ UX friction (took >20 min to claim)
- ⚠️ Critical bug (login loop, data loss, etc.)

### Phase 2: Gradual Rollout (Optional, pending beta)

If beta goes well, phase the launch:
1. **Week 3:** 10 additional nonprofits (invite known partners)
2. **Week 4:** 30 nonprofits (public announcement + feature flag 10%)
3. **Week 5+:** Gradually increase feature flag (25% → 50% → 100%)

Each phase: monitor support load, gather feedback, iterate.

---

## Roles & Responsibilities

| Role | Task | Time |
|------|------|------|
| **Akbar (You)** | Select test orgs, send outreach, field support questions, monitor feedback | 30 min/day |
| **Claude (AI)** | Maintain logs, run queries, prepare daily status, suggest fixes | 15 min/day |

---

## Communication Plan

**Before Beta:**
- Email: Outreach to test orgs (Day 1)

**During Beta (daily):**
- Internal: "Daily standup" check (5 min)
- With Orgs: Auto-reply confirmation + "We're here if you hit any issues" link

**After Beta:**
- Email: "Thank you for testing! Here's what we learned" + results

---

## Fallback: If Something Breaks

**If API endpoint is down:**
1. Check logs: `tail -100 logs/daanaa_api.log`
2. Restart API: `./restart_api.sh`
3. Notify test orgs: "Brief issue, we're working on it" (set realistic expectations)

**If database is corrupted:**
1. Restore from backup: `sqlite3 data/merit_registry.db.backup < /path/to/backup.sql`
2. Re-apply migrations: migrations will auto-run on API startup
3. Notify orgs: "Brief maintenance, we're back up"

**If I need to revert:**
- Git reset to commit before new code: `git revert [commit-hash]`
- Rebuild frontend: `npm run build`
- Redeploy

---

## Files & Links

**Frontend:**
- OrgClaimEditor.tsx (updated with data transparency)
- DataUpdateForm.tsx (new component for updates)
- ResearchDataTransparency.tsx (existing component)

**Backend:**
- POST /api/nonprofit/update-data (new endpoint)
- GET /api/nonprofit/update-status/:id (new endpoint)
- Migration 003: org_nonprofit_updates table
- Migration 004: data_submitted_by_org columns

**Documentation:**
- NONPROFIT_DATA_UPDATES_IMPLEMENTATION.md (backend details)
- NONPROFIT_CLAIM_FLOW_REVISED.md (user flow)
- BETA_LAUNCH_PLAN.md (this file)

---

## Success Outcome (End of 2 Weeks)

You'll have:
- ✅ Validated that real nonprofits can claim their profiles
- ✅ Confirmed that data transparency doesn't confuse users
- ✅ Tested financial data update flow with real submissions
- ✅ Documented feedback + issues
- ✅ Green light for Phase 2 (wider rollout)

And you'll know:
- ✅ What support load looks like (can you handle 5+ nonprofits/week?)
- ✅ What copy/UX changes help (or hurt)
- ✅ Whether the 2–3 day scoring delay feels right
- ✅ Real user reactions to "Here's your IRS data" transparency

---

**Decision Point:** After 14 days of beta testing, decide:
1. **Go to Phase 2** (public announcement + gradual rollout)
2. **Iterate** (fix feedback + test again for 1 week)

**Current recommendation:** Launch beta now. Real users will surface issues you can't predict in testing.

---

**Ready to go? Pick your 3–5 test nonprofits and send the outreach email.**
