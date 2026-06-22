# Nonprofit Dashboard Flow — After Claiming Profile

## Overview

After a nonprofit claims their profile, they get:
1. **Donor Interest Dashboard** — see who's bookmarking them + trends
2. **Research Data Transparency** — see the data we used for their peer context
3. **Update Form** — correct outdated/incorrect information
4. **Scoring Integration** — updates feed into next nightly batch

---

## Step 1: Nonprofit Claims Profile

**URL:** `/nonprofit/claim/{token}`
**Action:** "Verify your email → See your dashboard"
**Outcome:** Can now view their dashboard (authenticated)

---

## Step 2: Nonprofit Sees Dashboard Home

**Three sections:**

### A. How Donors See You
```
Your Peer Context (from "How Donors See You" display)
- Your Sector: [position + explanation]
- In Your State: [rank + explanation]
- Your Scale: [size category + explanation]
- Financial Health: [signal + explanation]

Last updated: FY 2024 (via IRS)
[Update your data button]
```

### B. Donor Interest (Weekly)
```
This Week's Bookmarks: 23 (↑5 from last week)

By Cause:
- Education: 12 bookmarks
- Youth Development: 8
- Community Development: 3

By Location:
- California: 15 bookmarks
- Oregon: 5
- Nevada: 3

"People in your area are discovering you. 
The more you update your mission & impact, 
the more specific your audience."
```

### C. Research Data — Verify & Update
```
[THIS COMPONENT: ResearchDataTransparency]

Shows:
- Latest Tax Year (FY 2024)
- Data Source (IRS 990)
- Financial Metrics Grid:
  * Total Revenue: $2.9M
  * Program Expense %: 78%
  * Months of Reserve: 2.5
  * Total Expenses: $2.7M

"Is this data correct? Update it below."

[Update Your Information button]
```

---

## Step 3: Nonprofit Clicks "Update Your Information"

**Modal opens with form:**

```
Update Your Financial Data

Help us get it right. We'll include your updates in our 
next scoring run (daily at 2am PT).

Your Latest Data (from FY 2024):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] This data is outdated. Here's what changed:

FORM FIELDS (optional — fill only if different from IRS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Annual Revenue
[input: $______ ]  (Current: $2.9M from FY2024)

Annual Expenses
[input: $______ ]  (Current: $2.7M from FY2024)

Program Expense %
[input: _____ % ]  (Current: 78% from IRS)

Months of Reserve
[input: _____ months ]  (Current: 2.5 from IRS)

What changed?
[textarea: explain briefly...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Cancel] [Submit Update]

"Your updates will be reviewed and included in tomorrow's 
scoring run. We'll email you when your peer context updates."
```

---

## Step 4: Backend Processing

**POST /api/nonprofit/update-data** receives:
```json
{
  "claim_token": "xyz...",
  "ein": "261234567",
  "updates": {
    "total_revenue": 3100000,
    "total_expenses": 2850000,
    "program_expense_pct": 81,
    "months_of_reserve": 3.2
  },
  "explanation": "2024 was stronger year. Built reserves after 2023 deficit."
}
```

**Flow:**
1. ✅ Validate update (sanity checks: revenue > expenses, % 0-100, etc.)
2. ✅ Store in `org_nonprofit_updates` table with:
   - `ein`, `claim_token`, `submitted_at`, `status: 'pending_review'`
   - Original values + updated values
   - `explanation` text
3. ✅ Flag for next scoring run
4. ✅ Email nonprofit: "Update received. Will be included in tomorrow's scoring run."

---

## Step 5: Nightly Scoring Pipeline Integration

**Current flow (overnight_pipeline.py):**
```
1. Run merit_scorer_v4_0.py
2. Rebuild FTS index
3. Refresh stats
```

**New flow:**
```
1. Check for pending org_nonprofit_updates
   └─ For each: Use nonprofit-submitted data instead of IRS
      └─ Mark as 'included_in_run'
      
2. Run merit_scorer_v4_0.py (uses org_nonprofit_updates)
   └─ Recalculates v5 context for affected orgs
   
3. Rebuild FTS index
4. Refresh stats
5. Email nonprofits: "Your peer context updated based on your submission"
```

**Example:**
- Org submitted: "Reserves are now 3.2 months"
- Scorer reads: `months_of_reserve = 3.2` (nonprofit value overrides IRS)
- Result: Health signal may change from STABLE → HEALTHY
- Email to org: "Good news: based on your 2024 data, you're now Financially Healthy!"

---

## Step 6: Nonprofit Sees Updated Peer Context

**Next time they visit dashboard:**
```
How Donors See You
(Updated based on your submission)

🎯 FINANCIAL HEALTH
✓ Financially Healthy

"You now have reserves and runway. Donors see a strong partner."

Last updated: [today's date] based on your FY2024 data
```

---

## Data Integrity Safeguards

**Validation in form:**
- Revenue cannot be 0 or negative
- Expenses cannot exceed revenue by >20% (sanity check)
- Program % must be 0-100
- Reserves months must be ≥0

**Flag for review if:**
- Nonprofit submits drastically different data (>50% change from IRS)
- Program % < 30% (unusual, may indicate data error)
- Reserves < -1 months (org in serious trouble)

**Action:** Flag updates in admin dashboard for manual review, but still include in scoring

---

## Communication to Nonprofits

### Email 1: "Update Received"
```
Subject: Your financial data update for [Org Name]

We received your update:
- Revenue: $3.1M (was $2.9M)
- Reserves: 3.2 months (was 2.5 months)

This will be included in tomorrow's scoring run at 2am PT.

We'll email you as soon as it's processed.

Questions? Reply to this email.
```

### Email 2: "Peer Context Updated"
```
Subject: Your peer context updated — good news!

Your updated financial data is now live on Daanaa.

Before: Financially Stable
Now: Financially Healthy ✓

"You have reserves and runway. Donors see a strong partner."

Visit your dashboard to see how donors understand your 
organization: [link to /nonprofit/dashboard]

Thank you for keeping your information current.
```

---

## Key Design Principles

✅ **Transparency:** Show exactly what data we have + where it's from
✅ **Correction Path:** Easy to update if wrong
✅ **Trust-Building:** "We use your updates, and here's proof (peer context changed)"
✅ **Nonprofit Dignity:** Updates are treated as credible (not "suspicious" until flagged)
✅ **Real-Time Feedback:** See peer context change immediately after submission
✅ **Stewardship-Aligned:** Evidence-based (uses actual data), correctable (mistake registry principle)

---

## Admin Oversight

**Dashboard:** `/admin/nonprofit-updates`
```
EIN | Organization | Submitted Data | IRS Data | Flags | Status | Action
--- | --- | --- | --- | --- | --- | ---
261234567 | Foundation Name | 3.2 mo | 2.5 mo | +28% change | Included | [Review]
```

**Spot-check process (weekly):**
1. Look for >50% changes
2. Check if explanation makes sense ("Had major gift" vs "System error")
3. Mark as "Verified" or "Needs Follow-up"
4. No blocking — all updates get used, but staff monitor

---

## Timeline to Ship

**Phase 1 (this week):**
- [ ] Build ResearchDataTransparency component
- [ ] Wire into nonprofit dashboard
- [ ] Create update form + validation

**Phase 2 (next week):**
- [ ] Build org_nonprofit_updates table
- [ ] Create POST /api/nonprofit/update-data endpoint
- [ ] Add pending updates processing to overnight_pipeline.py
- [ ] Test with 2-3 partner nonprofits

**Phase 3 (week after):**
- [ ] Roll out to all claimed nonprofits
- [ ] Monitor for strange submissions
- [ ] Adjust validation rules based on real data

