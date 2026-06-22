# Nonprofit Claiming Flow — With Data Transparency + Update Option

## Goal
Show nonprofits exactly what data we have, let them correct it during claiming (not after), and manage expectations about scoring timeline.

---

## Flow: 4 Steps

### STEP 1: Pre-Claim Review (Email Link)
**User sees:** "Before you claim, here's what we have about you"

```
┌─────────────────────────────────────────────────────────────┐
│  CLAIM YOUR NONPROFIT PROFILE                              │
│  Before we show donors your story, let's verify the data  │
└─────────────────────────────────────────────────────────────┘

🔍 HERE'S WHAT WE KNOW ABOUT YOU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Organization: [Name]
EIN: [EIN]
Location: [City, State]

FINANCIAL DATA (from IRS 990, FY 2024)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────┬──────────────┬────────┐
│ Metric           │ Value        │ Source │
├──────────────────┼──────────────┼────────┤
│ Total Revenue    │ $2,900,000   │ IRS    │
│ Total Expenses   │ $2,700,000   │ IRS    │
│ Program Expense %│ 78%          │ IRS    │
│ Months of Reserve│ 2.5 months   │ IRS    │
│ Latest Tax Year  │ FY 2024      │ IRS    │
└──────────────────┴──────────────┴────────┘

ℹ️  This data is 6 months old (filed Dec 2024). 
    If your 2025 numbers are different, you can update them below.

🔄 WANT TO CORRECT ANYTHING?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ ] Yes, some numbers have changed

If checked → shows update form:

  Annual Revenue (2025):
  [$________] (vs. $2.9M from IRS FY2024)

  Annual Expenses (2025):
  [$________] (vs. $2.7M from IRS FY2024)

  Program Expense %:
  [____%] (vs. 78% from IRS)

  Months of Reserve:
  [_____ months] (vs. 2.5 from IRS)

  What changed? (brief explanation)
  [textarea]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 TIMING COMMITMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If you update data today (Mon 6/24):
  ✓ Your updates are saved
  ✓ Your profile is live (donors can see your story)
  ✓ Your peer context recalculates Wed/Thu
  ✓ New peer context goes live Fri
  
Why wait? Your nonprofit shouldn't be penalized immediately 
for updating. We want you to have time to understand the impact.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Continue to Claim Profile]
```

---

### STEP 2: Verification (Email/Magic Link)
**User sees:** Standard email verification

```
Click the link below to claim your profile:
[Claim Profile Link]

This link is valid for 24 hours.
```

---

### STEP 3: Complete Claim
**User sees:** Minimal info (name, mission, website)

```
Complete Your Profile
━━━━━━━━━━━━━━━━━━━━━━

Mission Statement:
[textarea - prefilled with what we have]

Website:
[input - prefilled]

Leadership (optional):
Executive Director: [_______________]
Board Chair: [_______________]

[Save & Continue to Dashboard]
```

---

### STEP 4: Dashboard (Welcome)
**User sees:** Profile live + data transparency + update status

```
┌─────────────────────────────────────────────┐
│  WELCOME TO YOUR NONPROFIT DASHBOARD        │
│  [Org Name]                                 │
└─────────────────────────────────────────────┘

✅ Your profile is live on Daanaa

Donors can find you. Now let's show them why you matter.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 YOUR FINANCIAL DATA & PEER CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Data (Used for Peer Context):
┌────────────┬─────────────┬──────────────────┐
│ Metric     │ Value       │ Source           │
├────────────┼─────────────┼──────────────────┤
│ Revenue    │ $3,100,000  │ You (Updated)    │
│ Expenses   │ $2,850,000  │ You (Updated)    │
│ Program %  │ 81%         │ You (Updated)    │
│ Reserves   │ 3.2 months  │ You (Updated)    │
└────────────┴─────────────┴──────────────────┘

💡 Original IRS data:
   Revenue: $2.9M | Expenses: $2.7M | Program: 78% | Reserves: 2.5mo

📅 Update Status:
   Submitted: Mon Jun 24, 2:45pm
   Status: Pending scoring update
   Will be included: Fri Jun 27 (scoring run)
   New peer context live: Fri Jun 27 by 9am

"We're holding your data for 2-3 business days so you can review 
the impact before it changes your peer context. On Friday, donors 
will see your updated position."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW DONORS SEE YOU (Current = IRS Data)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Current peer context display using original IRS data]
[Will update Fri 6/27 with nonprofit's submitted data]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT'S NEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Your profile is live
✓ Donors can see your story
✓ Friday, peer context updates if you submitted new data
✓ Monday onwards: donors see your new financial position

Questions? We're here: [support link]
```

---

## Database Changes

### `org_nonprofit_updates` (Revised)
```sql
CREATE TABLE org_nonprofit_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ein TEXT NOT NULL,
    claim_token TEXT NOT NULL UNIQUE,

    -- Original IRS data
    irs_total_revenue REAL,
    irs_total_expenses REAL,
    irs_program_expense_pct REAL,
    irs_months_of_reserve REAL,
    irs_tax_year INTEGER,

    -- Nonprofit-submitted updates (during claiming)
    submitted_total_revenue REAL,
    submitted_total_expenses REAL,
    submitted_program_expense_pct REAL,
    submitted_months_of_reserve REAL,
    submitted_explanation TEXT,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Review & processing
    status TEXT DEFAULT 'pending_review',  
    -- Values: pending_review, validated, pending_scoring, included_in_run, rejected
    
    admin_notes TEXT,
    validated_at DATETIME,
    validated_by TEXT,
    
    -- Scoring integration
    scoring_run_date DATETIME,  -- Which run will include this
    included_in_run_at DATETIME,
    result_v5_percentile REAL,
    result_health_signal TEXT,

    FOREIGN KEY (ein) REFERENCES registry_enriched(EIN)
);
```

---

## Timeline & Messaging

### Nonprofit's Experience
```
Mon 6/24 at 2:45pm
├─ Submits update during claiming
└─ Sees: "Your data will be scored Fri 6/27"

Fri 6/27 at 2:00am
├─ Nightly scoring run includes their data
├─ Peer context recalculates
└─ Dashboard updates with new signal

Fri 6/27 at 9:00am
├─ Email: "Your peer context updated!"
├─ They see live change on daanaa.org
└─ Donors see new position
```

### Key Message
> "Your nonprofit data was submitted on [Mon]. We're giving you a 2-3 business day window 
> to review what changes before it affects your peer context. This way, you can prepare 
> your story for donors. On Friday, your updated position goes live."

---

## Why This Works

**For nonprofits:**
- ✅ Transparency BEFORE claiming (builds trust)
- ✅ Update opportunity DURING claiming (no friction)
- ✅ 2-3 day grace period (can prepare messaging)
- ✅ Clear timeline ("Fri morning, donors see new position")
- ✅ Proof we listened ("Your data was updated by org" shows in dashboard)

**For Daanaa:**
- ✅ High-signal data (nonprofits think before submitting)
- ✅ Reduced shock ("You knew this was coming")
- ✅ Improved claiming (transparency → higher conversion)
- ✅ Better donor experience (real, current nonprofit data)

**For donors:**
- ✅ Current data (nonprofits incentivized to update)
- ✅ Verified source ("Updated by Org" badge visible)
- ✅ Trust signal (nonprofits who claim are more transparent)

---

## Implementation (Priority Order)

**Phase 1 (This Week):**
- [ ] Update claim flow: add data review + update form
- [ ] Update dashboard: show data transparency + update status
- [ ] Update org_nonprofit_updates table
- [ ] Deploy 1% feature flag

**Phase 2 (Next Week):**
- [ ] Add to scoring pipeline: check for "pending_scoring" status
- [ ] Schedule updates: "Include in Fri scoring run"
- [ ] Email template: "Your peer context updated Fri morning"
- [ ] Test end-to-end: claim → update → score → email

---

## Key Dates (Example)
```
Mon 6/24 2:45pm — Nonprofit submits during claim
Fri 6/27 2:00am — Scoring run includes their data
Fri 6/27 9:00am — Dashboard + email shows new peer context live
Mon 6/30+ — Donors see updated position
```

