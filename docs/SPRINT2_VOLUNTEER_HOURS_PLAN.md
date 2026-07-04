# Sprint 2: Volunteer Hours Collection — Implementation Plan

**Status:** Infrastructure exists, just need API wiring + frontend forms

**Discovery:** Database tables already exist:
- `volunteer_hours` (pending submission form)
- `volunteer_hour_confirmations` (approval records)
- `org_claims` (nonprofit ownership)
- `org_activity` (activity log)

---

## Task 2.1: Nonprofit Event Submission API (2h, not 4h)

**Endpoint:** `POST /api/nonprofit/{ein}/volunteer/submit`

**What it does:**
1. Validate Firebase auth + claim ownership (ein must match)
2. Accept: volunteer_name, volunteer_email, hours, service_date, activity_description
3. Generate claim_code (short alphanumeric ID, e.g., "VOL-ABC123")
4. Insert into `volunteer_hours` (status='pending')
5. Return: claim_code (nonprofit displays to volunteer)

**Email to volunteer:** "Claim your volunteer hours: https://daanaa.org/volunteer/claim?code={claim_code}"

**Implementation:** ~15 lines Python + validation

---

## Task 2.2: Volunteer Claim Form + API (2h, not 4h)

**Frontend:** `/volunteer/claim?code=VOL-ABC123`
- Form: email (verify it matches), confirm hours + date
- Button: "Claim My Hours"

**Backend:** `POST /api/volunteer/claim`
- Lookup volunteer_hours by claim_code
- Verify email matches
- Update status='confirmed'
- Email nonprofit: "Volunteer hours claimed, pending your approval"

**Implementation:** ~10 lines Python + React form

---

## Task 2.3: Approval Dashboard (2h)

**Existing:** NonprofitDashboardPage already has volunteer tracking UI

**What's missing:** Wire to actual data
- GET `/api/nonprofit/{ein}/volunteer/pending` → list volunteer_hours where status='confirmed'
- POST `/api/nonprofit/{ein}/volunteer/{id}/approve` → status='approved', add approval_notes
- POST `/api/nonprofit/{ein}/volunteer/{id}/reject` → status='rejected', add rejection_reason

**Implementation:** 3 API endpoints, ~30 lines Python

---

## Task 2.4: E2E Testing (2h)

- Nonprofit submits volunteer event
- Volunteer receives claim code
- Volunteer claims hours
- Nonprofit sees pending approval
- Nonprofit approves
- Email confirmations sent

---

## Revised Effort Estimate

- 2.1: 2h (not 4h) — simple insert + code generation
- 2.2: 2h (not 4h) — form + lookup
- 2.3: 2h (existing)
- 2.4: 2h (testing)

**Total: 8 hours (not 12h)**

---

## Quick Implementation Path

**Option A: Complete now (tonight)**
- Build all 4 tasks sequentially (8h of work)
- Test full flow live on daanaa.org
- Deploy to production

**Option B: Build incrementally (next week)**
- Task 2.1 tomorrow (nonprofit submission)
- Task 2.2 Thursday (volunteer claim)
- Task 2.3 Friday (approval)
- Task 2.4 Monday (E2E testing + fixes)

---

## Why it's simpler than estimated

✅ Database schema exists  
✅ Authentication system proven (nonprofit claims)  
✅ Email infrastructure proven (welcome emails, PINs)  
✅ Frontend dashboard component ready  
✅ No new external dependencies

Missing: Just the glue between frontend forms + database inserts + email notifications

---

**Ready to execute. Which approach: A (finish tonight) or B (next week)?**
