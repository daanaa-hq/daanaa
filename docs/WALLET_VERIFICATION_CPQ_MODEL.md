# Wallet Verification — CPQ Model (Request-Based)

**Status:** Design proposal for Wallet Phase 2 (verified hours tracking)

---

## Concept

Volunteer hour verification follows a **request-based workflow** (CPQ-style):
- **Configure:** Volunteer logs hours + gives consent
- **Price:** (inherent in hours logged — volunteer's estimated value at $29.95/hr)
- **Quote/Request:** Volunteer clicks "Request verification" → nonprofit receives notification
- **Confirm:** Nonprofit reviews → verifies or declines → hours locked or rejected

**Key principle:** Volunteer *actively requests* verification rather than auto-pushing data. Aligns with Privacy Principle P2 (privacy is core) and keeps nonprofit in control.

---

## Data Model

### New Table: `verification_requests`

```sql
CREATE TABLE verification_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  volunteer_log_id UUID NOT NULL REFERENCES volunteer_hours(id),
  nonprofit_ein VARCHAR(50) NOT NULL,
  
  -- Request metadata
  status ENUM('pending', 'verified', 'declined') DEFAULT 'pending',
  requested_by_email VARCHAR(255) NOT NULL,  -- Firebase user email
  requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  -- Nonprofit response
  verified_by_email VARCHAR(255),             -- Nonprofit staff who verified
  verified_at TIMESTAMP,
  decline_reason TEXT,                        -- If declined, why?
  
  -- Immutability flag
  is_locked BOOLEAN DEFAULT FALSE,            -- Once verified, locked from edits
  
  INDEX (nonprofit_ein, status),
  INDEX (requested_at DESC),
  INDEX (volunteer_log_id),
  UNIQUE KEY (volunteer_log_id)  -- One request per log entry
);
```

### Updated Table: `volunteer_hours`

Add verification tracking:

```sql
ALTER TABLE volunteer_hours ADD COLUMN (
  verification_status ENUM('unshared', 'requested', 'verified', 'declined') DEFAULT 'unshared',
  request_id UUID REFERENCES verification_requests(id),
  verification_locked_at TIMESTAMP  -- When verified, when it can't be edited
);
```

---

## Workflow

### 1. Volunteer Logs Hours

```
POST /api/wallet/volunteer-hours
{
  "nonprofit_ein": "123456789",
  "date": "2026-06-15",
  "hours": 4,
  "notes": "Helped with grant writing",
  "allow_verification": true  // Consent is ON
}

Response:
{
  "id": "log_123",
  "status": "unshared",  // Not yet shared
  "estimated_value": "$119.80",  // 4 hrs × $29.95
  "show_request_button": true  // Volunteer can request verification
}
```

### 2. Volunteer Requests Verification

```
POST /api/wallet/logs/{log_id}/request-verification
{
  "nonprofit_ein": "123456789"
}

Response:
{
  "request_id": "req_456",
  "status": "pending",
  "nonprofit_name": "Example Org",
  "message": "Verification request sent to Example Org"
}

Volunteer sees:
- Status badge: "Verification pending"
- Nonprofit name + contact info (if available)
- "Withdraw request" button (to cancel before verified)
```

### 3. Nonprofit Receives Request

**Notification (Email):**
```
Subject: [Jane] requests verification of 4 hours

Hi Example Org,

Jane Smith requests verification of 4 volunteer hours contributed on 2026-06-15.

Hours: 4
Notes: "Helped with grant writing"
Estimated value: $119.80

[ Verify ] [ Decline with comment ] [ View all requests ]
```

**Dashboard card:**
```
Pending Verification Request
├─ Jane Smith
├─ 4 hours on 2026-06-15
├─ "Helped with grant writing"
├─ Est. value: $119.80
└─ [ Verify ] [ Decline ]
```

### 4. Nonprofit Verifies or Declines

**Verify:**
```
PATCH /api/nonprofit/{ein}/verification-requests/{request_id}/verify
{
  "verified_by_email": "staff@example.org"
}

Response:
{
  "request_id": "req_456",
  "status": "verified",
  "verified_at": "2026-06-18T14:32:00Z",
  "hours_locked": true,
  "volunteer_notification": "sent"
}
```

**Decline:**
```
PATCH /api/nonprofit/{ein}/verification-requests/{request_id}/decline
{
  "reason": "Hours don't match our records"
}

Response:
{
  "request_id": "req_456",
  "status": "declined",
  "declined_at": "2026-06-18T14:32:00Z",
  "volunteer_can_resubmit": true
}
```

### 5. Volunteer Sees Result

**If verified:**
- Status: "Verified by [Org Name]" ✓
- Estimated value: $119.80
- Hours locked (can't edit)
- Contribution appears in "Verified hours" section

**If declined:**
- Status: "Request declined"
- Reason: "[Org's message]"
- "Resubmit request" button (after discussion with nonprofit)
- Hours remain in "Unverified" section

---

## API Endpoints

### Volunteer (Frontend: `/wallet`)

```
POST /api/wallet/volunteer-hours
GET /api/wallet/volunteer-hours
GET /api/wallet/volunteer-hours/{id}
DELETE /api/wallet/volunteer-hours/{id}  // Only if unshared

POST /api/wallet/logs/{id}/request-verification
PATCH /api/wallet/requests/{request_id}/withdraw  // Withdraw pending request
GET /api/wallet/verification-status  // Quick summary: X verified, Y pending, Z declined
```

### Nonprofit (Frontend: `/nonprofit/verify-hours`)

```
GET /api/nonprofit/{ein}/verification-requests  // All requests (pending/verified/declined)
PATCH /api/nonprofit/{ein}/verification-requests/{id}/verify
PATCH /api/nonprofit/{ein}/verification-requests/{id}/decline
GET /api/nonprofit/{ein}/verified-summary  // Total hours verified, dollar value
```

---

## Audit Trail

All requests are logged for compliance:

```sql
SELECT 
  vr.id, vr.nonprofit_ein, vr.requested_at, vr.status,
  vr.verified_at, vr.verified_by_email,
  vh.hours, vh.notes
FROM verification_requests vr
JOIN volunteer_hours vh ON vr.volunteer_log_id = vh.id
WHERE vr.nonprofit_ein = '123456789'
ORDER BY vr.requested_at DESC;
```

---

## Benefits Over Auto-Share

| Aspect | Auto-Share | Request-Based (CPQ) |
|--------|-----------|-------------------|
| Privacy | Implicit consent | Explicit request per volunteer |
| Nonprofit Control | Passive notifications | Active action items |
| Audit Trail | Shared/verified events | Request → Response → Verified |
| Withdrawability | Can't withdraw once shared | Can withdraw pending requests |
| Fraud Prevention | No verification step | Nonprofit explicitly confirms |
| Donor Value | Unclear (just logged) | Visible: estimated + verified |

---

## Stewardship Alignment

✅ **P2 (Privacy):** Volunteer controls when data leaves their device. Nonprofit consent verified by action (clicking verify).

✅ **P3 (Trust signals evidence-based):** Verified hours backed by nonprofit attestation. Decline reasons create audit trail.

✅ **P6 (Mistakes corrected):** Volunteer can see decline reason, resubmit with corrections.

✅ **P9 (Decisions explainable):** Every request/verification/decline is logged and visible to both parties.

✅ **P10 (AI is tool):** No AI makes decisions. Nonprofit human decides to verify.

---

## Implementation Notes

1. **Estimated value display:** Show $29.95/hr × hours only in UI; don't store as currency (avoids rounding issues, tax implications).

2. **Resubmit logic:** Declined requests don't delete logs. Volunteer can resubmit same log after getting nonprofit feedback.

3. **Withdrawal:** Before nonprofit verifies, volunteer can withdraw the request (removes log from nonprofit's pending list). After verified, locked.

4. **Nonprofit audit report:** Monthly summary CSV: "X hours verified from Y volunteers for $Z value."

5. **Email notifications:** Async queue (same as vendor ratings). Subject line includes volunteer name + hours for clarity.

---

## Future Extensions (Phase 3+)

- **Bulk requests:** Volunteer checks multiple hours and requests batch verification
- **Skills-based value:** Different rate for specialized skills (e.g., grant-writing @ $45/hr)
- **Board onboarding:** Same request model for board member nominations
- **Recurring verification:** Nonprofit sets "standing approval" for monthly hours from regular volunteers
