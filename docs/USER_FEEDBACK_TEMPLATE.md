# User Feedback Collection Template

For gathering + organizing feedback from early Phase 2 users.

---

## How to Collect Feedback

### Option 1: Email
Send to early adopters:
```
Subject: We'd love to hear how Daanaa's volunteer hours feature is working

Hi [Name],

You've been using Daanaa's new volunteer hours feature. Would you mind sharing quick feedback?

- Is it working as expected?
- What's been hardest?
- What could we improve?

Reply here or visit: [feedback form URL]

Thanks,
Daanaa Team
```

### Option 2: In-App Form (To Be Built)
- After volunteer claims hours: "How did that go? Any feedback?"
- After nonprofit approves: "Anything we could improve?"
- Sidebar: "Report a mistake or suggest a feature"

### Option 3: Direct Interview
- Schedule 15-min call with 3-5 power users
- Ask about their workflow
- Watch them use the feature
- Note friction points

---

## Feedback Form Questions

For **Nonprofits:**
```
1. How many volunteers have you submitted hours for? [text]
2. Was the submission process clear? [Yes/No/Somewhat]
3. What was confusing? [open text]
4. How many have you approved so far? [number]
5. Any technical issues? [open text]
6. What would make this better? [open text]
```

For **Volunteers:**
```
1. Did you receive the claim code? [Yes/No]
2. Was the form easy to use? [Yes/No/Somewhat]
3. Any issues claiming your hours? [open text]
4. Would you use this again? [Yes/No/Maybe]
5. What could improve? [open text]
```

---

## Feedback Log Template

Keep a running log in this format:

```markdown
## Feedback Entry #1
**Date:** 2026-07-05  
**User:** nonprofit_ein=360822808 (American Red Cross)  
**Contact:** sarah@redcross.org  
**Feature:** Volunteer hours submission  
**Category:** [Feature Request / Bug / Question / Praise]  
**Severity:** [Low / Medium / High / Critical]  

**Feedback:**
"The submission form is great, but we'd love to be able to bulk upload CSV of volunteers instead of one at a time."

**Action:**
- [ ] Acknowledge receipt
- [ ] Add to Phase 2.1 roadmap
- [ ] Follow up with timeline

---

## Feedback Entry #2
**Date:** 2026-07-05  
**User:** volunteer_email=john@example.com  
**Feature:** Volunteer hours claim  
**Category:** Bug  
**Severity:** Medium  

**Feedback:**
"Got the claim code via email but the form said my email didn't match. Turns out they sent a different email variant (j.smith vs john.smith). Confusing!"

**Action:**
- [ ] Check if we can do fuzzy email matching
- [ ] Or add clear note: "Use exact email address"
- [ ] Update user guide with clarification
```

---

## Feedback Themes to Watch For

### Common Issues That Emerge
- Email matching (exact vs fuzzy)
- CSV bulk upload request
- Timezone confusion (service_date)
- "How do I undo an approval?"
- "Can volunteers update their hours?"

### Patterns That Indicate Success
- Repeat users (same nonprofit/volunteer using it again)
- Praise for ease of use
- Feature requests (means they want more!)
- Referrals ("Can you set up my friend's org?")

---

## Action Paths

| Feedback Type | Action | Owner | Timeline |
|---------------|--------|-------|----------|
| Bug (High) | Fix + deploy | Engineer | 24h |
| Bug (Low) | Log + roadmap | Engineer | Next sprint |
| Feature Request (Popular) | Scope + roadmap | Product | Next review |
| Feature Request (Niche) | Log + revisit Q4 | Product | Q4 review |
| Confusion | Update docs | Writer | 48h |
| Praise | Note + celebrate | Everyone | Immediate |

---

## Weekly Feedback Review

Every Monday:

1. **Collect** new feedback from all channels (email, form, calls)
2. **Categorize** by theme (bugs, features, confusion, praise)
3. **Prioritize** by severity + frequency
4. **Act** on high-priority items (bugs, confusion)
5. **Log** everything in spreadsheet for trend tracking

---

## Tools

### Where to Store Feedback
- Spreadsheet: [TBD - Google Sheets or Notion]
- Email: akbar.khowaja+support@daanaa.org
- Issue tracker: GitHub Issues (label: user-feedback)

### Template Columns (Spreadsheet)
```
Date | User Type | Feature | Category | Severity | Feedback | Status | Action | Owner | Deadline
```

---

## Success Metrics (30 days)

- [ ] Collected feedback from ≥5 nonprofits
- [ ] Collected feedback from ≥10 volunteers
- [ ] Identified 3+ actionable improvements
- [ ] Fixed 1+ bugs based on feedback
- [ ] Updated docs based on confusion points
- [ ] 0 "critical" unfixed issues

---

**Next Review:** July 12, 2026
