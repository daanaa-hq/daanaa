# Nonprofit Data Updates Implementation

**Date Completed:** June 22, 2026  
**Status:** Backend complete, tested, ready for frontend integration  

---

## What Was Built

A complete backend system for nonprofits to submit financial data corrections during the claiming flow, with 2-3 business day delay before scoring impact.

### 1. Database Schema

**Migration 003:** `org_nonprofit_updates` table
- Stores EIN, claim token, IRS baseline values, nonprofit-submitted updates
- Tracks status: `pending_review` → `validated` → `pending_scoring` → `included_in_run` → `rejected`
- Flags large changes (>50%) for admin review
- Records scoring run date and final results (percentile, health signal)

**Migration 004:** Transparency columns on `registry_enriched`
- `data_submitted_by_org` (0=IRS, 1=nonprofit-submitted)
- `data_submitted_at` (when update was submitted)

### 2. Backend API Endpoints

**POST /api/nonprofit/update-data**
```json
{
  "claim_token": "xyz123",
  "ein": "12-3456789",
  "updates": {
    "total_revenue": 3100000,
    "total_expenses": 2850000,
    "program_expense_pct": 81,
    "months_of_reserve": 3.2
  },
  "explanation": "2024 was a stronger year"
}
```

**Response:**
```json
{
  "status": "received",
  "update_id": 1,
  "message": "Your update will be reviewed and included in the next scoring run"
}
```

**Validation:**
- Revenue ≥ 0, Expenses ≥ 0
- Program % between 0-100
- Revenue ≥ Expenses (sanity check)
- Flags changes >50% from IRS baseline

**GET /api/nonprofit/update-status/:id?claim_token=xyz**
- Returns: status, submitted_at, included_in_run_at, result_health_signal, result_v5_percentile

### 3. Overnight Pipeline Integration

**New function: `apply_nonprofit_updates()`**
- Called BEFORE v5 scorer runs
- Finds pending_review updates with no sanity flags
- Auto-validates them and marks as pending_scoring
- Updates registry_enriched with nonprofit data (total_revenue, total_expenses, program_expense_pct, months_of_reserve)
- Sets data_submitted_by_org=1 and data_submitted_at=CURRENT_TIMESTAMP

**After scoring:**
- All pending_scoring updates marked as included_in_run
- Scoring results (percentile, health_signal) stored back to org_nonprofit_updates

### 4. Testing

**7 comprehensive tests passing:**
- ✅ Successful update submission
- ✅ Invalid revenue rejection
- ✅ Invalid program % rejection  
- ✅ Missing claim_token rejection
- ✅ Get update status
- ✅ Data stored correctly in database
- ✅ Sanity check flagging (>50% changes)

Run tests:
```bash
source venv/bin/activate
python3 -m unittest tests.test_nonprofit_data_updates -v
```

---

## Frontend Integration (TODO)

The ResearchDataTransparency component already exists (`frontend/src/components/ResearchDataTransparency.tsx`). It needs to be integrated into the claiming flow with an update form modal.

### Flow:
1. **Pre-Claim Review** → Show ResearchDataTransparency (data + sources + freshness)
2. **Update Option** → Click "Update Your Information" → Opens form
3. **Submit** → Call POST /api/nonprofit/update-data
4. **Confirmation** → "Your update will be included in Fri scoring run"
5. **Complete Claim** → Proceed to rest of claiming flow

### Component Integration Points:
- ClaimVerify.tsx → After PIN verification, show data review
- OrgClaimEditor.tsx → Or include update form within profile completion
- Need to pass `claimToken` and `orgEIN` to update form
- On success, navigate to final profile completion step

### Email Templates (TODO):
- "Your data will be scored on [date]" (sent when update received)
- "Your peer context updated!" (sent when scoring completes)
- Include: old values, new values, change summary, health signal update

---

## Data Flow Example

```
Mon 6:00pm: Nonprofit submits update during claiming
  → POST /api/nonprofit/update-data
  → Status: pending_review
  → Database stores submission

Mon-Fri morning: Admin reviews flagged updates (>50% changes)
  → Status: validated (manual or auto for safe changes)
  → Email: "We received your update"

Fri 2:00am: Overnight pipeline runs
  → apply_nonprofit_updates() finds pending_scoring updates
  → Updates registry_enriched with nonprofit data
  → Runs v5 scorer with nonprofit data
  → Marks as included_in_run
  → Email: "Your peer context updated!"

Fri 9:00am: Donors see new peer context
  → Organization's peer context reflects nonprofit-submitted data
  → Dashboard shows "Updated by Org" badge on updated fields
```

---

## Key Features

✅ **Data Transparency:** Show source, year, freshness of each metric  
✅ **Update Ability:** Prefilled forms with IRS baseline for reference  
✅ **Sanity Checks:** Flag unrealistic changes (>50%) for review  
✅ **Grace Period:** 2-3 days before scoring impact (time to prepare messaging)  
✅ **Trust Signal:** "Updated by Org" badges show what nonprofit corrected  
✅ **Deterministic:** Same nonprofit always gets same peer group (no gaming)  
✅ **Traceable:** Every update logged with submission time, explanation, results  

---

## Known Limitations

**Admin Review:** Currently auto-validates safe updates. Flagged updates need manual admin review (admin interface TODO).

**Email Triggers:** Notifications coded in overnight_pipeline but need email service integration (handled by scripts/email_service.py).

**Peer Context Display:** Frontend needs to show "Updated by Org" badges next to nonprofit-corrected data (requires frontend work).

---

## Deployment Checklist

- [x] Database migrations applied (001-004)
- [x] API endpoints tested (7 tests passing)
- [x] Pipeline integration verified
- [ ] Frontend component integration
- [ ] Email service wiring
- [ ] Admin review interface (optional, can skip for MVP)
- [ ] Monitoring & alerts configured
- [ ] Nonprofit outreach copy finalized
- [ ] Privacy compliance audit (ready)
- [ ] Launch with feature flag (1% cohort)

---

## Files Changed

**Backend:**
- migrations/003_org_nonprofit_updates.sql (NEW)
- migrations/004_add_nonprofit_submission_flags.sql (NEW)
- nonprofit_portal_endpoints.py (+ 2 new endpoints)
- scripts/overnight_pipeline.py (+ apply_nonprofit_updates function)

**Testing:**
- tests/test_nonprofit_data_updates.py (NEW, 7 tests)

**Frontend (existing, needs integration):**
- frontend/src/components/ResearchDataTransparency.tsx

---

## Next Steps

1. **Frontend Integration** (3-4 hours)
   - Add update form modal to claiming flow
   - Pass claim_token and org data to update endpoint
   - Show "Submitted!" confirmation
   - Redirect to final claim completion

2. **Email Service Wiring** (1-2 hours)
   - Hook email_service.py to overnight_pipeline
   - Create email templates for update notifications
   - Test with test account

3. **Admin Interface** (optional, 4-6 hours if needed)
   - Dashboard showing pending_review updates
   - Approve/reject with notes
   - Bulk validation for safe changes

4. **Launch to 1% Cohort** (1 hour)
   - Enable feature flag for data transparency
   - Monitor for errors
   - Collect feedback from partner nonprofits

5. **Scale to Full Release** (ongoing)
   - 1% → 10% → 50% → 100% over 2-3 weeks
   - Monitor adoption, submission rates, error rates
   - Iterate based on feedback

---

**Implementation by:** Claude Code  
**Approved by:** Akbar Khowaja (2026-06-22)  
**Status:** ✅ Ready for frontend integration & launch
