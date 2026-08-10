# Student Service API Specification
**Status:** Design Phase (Week 1)  
**Scope:** REST API for student volunteer service tracking  
**Authentication:** Firebase for students (Google OAuth), Firebase for school admins  
**Privacy:** Student data never exposed publicly; minimal collection per COPPA  

---

## API Overview

### Base URL
- Development: `http://localhost:5000/api/student/`
- Production: `https://daanaa.org/api/student/`

### Authentication
- **Student endpoints:** Firebase ID token in `Authorization: Bearer {token}` header
- **School admin endpoints:** Firebase ID token in header
- **Nonprofit supervisor endpoints:** Existing nonprofit auth (via nonprofit_accounts)

### Response Format
All responses are JSON. Errors include `error` and `status_code` fields.

```json
{
  "data": {...} or [...],
  "error": null,
  "status_code": 200,
  "timestamp": "2026-07-22T15:30:00Z"
}
```

---

## STUDENT ENDPOINTS

### 1. Student Discovery & Opportunities

#### `GET /api/student/opportunities`
**Purpose:** Student searches for volunteer opportunities  
**Auth:** Student (optional for public view, required for filtering by enrollment status)  
**Query Params:**
- `cause` (optional) — Filter by cause area (e.g., "education", "health")
- `location` (optional) — Filter by location or location_type
- `nonprofit_ein` (optional) — Find opportunities at specific nonprofit
- `sort` (optional) — 'recent', 'popular', 'commitment_hours'
- `page` (optional) — Pagination (default 1)
- `limit` (optional) — Per page (default 20, max 100)

**Response (200):**
```json
{
  "data": [
    {
      "opportunity_id": "opp_123",
      "nonprofit_ein": "123456789",
      "nonprofit_name": "Community Health Center",
      "title": "Community Health Education",
      "description": "Help with after-school health education programs",
      "cause_area": "Health",
      "location": "Downtown Office",
      "location_type": "in-person",
      "commitment_hours": 8,
      "available_start": "2026-08-01",
      "available_end": "2026-12-15",
      "supervisor_name": "Jane Smith",
      "student_enrollment_status": null  // or "interested", "committed", "in-progress"
    }
  ],
  "total": 42,
  "page": 1,
  "pages": 3
}
```

---

#### `POST /api/student/opportunities/{opportunity_id}/enroll`
**Purpose:** Student expresses interest in an opportunity  
**Auth:** Student (required)  
**Body:**
```json
{
  "hours_committed": 12
}
```

**Response (201):**
```json
{
  "enrollment_id": "enr_456",
  "opportunity_id": "opp_123",
  "status": "interested",
  "hours_committed": 12,
  "message": "You're enrolled! When you complete hours, log them in your service log."
}
```

---

### 2. Service Log (Hour Submission)

#### `GET /api/student/service-log`
**Purpose:** View student's submitted hours  
**Auth:** Student (required)  
**Query Params:**
- `status` (optional) — Filter by 'submitted', 'approved', 'rejected', etc.
- `nonprofit_ein` (optional) — Filter by organization
- `sort` (optional) — 'recent', 'oldest', 'by_org'

**Response (200):**
```json
{
  "data": [
    {
      "service_log_id": "sl_789",
      "nonprofit_ein": "123456789",
      "nonprofit_name": "Community Health Center",
      "service_date": "2026-08-15",
      "hours_claimed": 4,
      "activity_description": "Taught health education class to 30 students",
      "submission_status": "approved",
      "supervisor_name": "Jane Smith",
      "submitted_at": "2026-08-15T16:30:00Z",
      "approved_at": "2026-08-16T09:00:00Z",
      "duplicate_flag": false,
      "total_hours_this_org": 12
    }
  ],
  "summary": {
    "total_hours_submitted": 28,
    "total_hours_approved": 24,
    "pending_approval": 4,
    "rejected": 0
  }
}
```

---

#### `POST /api/student/service-log/submit`
**Purpose:** Student logs volunteer hours  
**Auth:** Student (required)  
**Body:**
```json
{
  "nonprofit_ein": "123456789",
  "service_date": "2026-08-15",
  "hours_claimed": 4.5,
  "activity_description": "Taught health education class to 30 students",
  "supervisor_name": "Jane Smith"
}
```

**Response (201):**
```json
{
  "service_log_id": "sl_789",
  "submission_status": "submitted",
  "message": "Hours logged! Waiting for supervisor approval.",
  "expected_approval_time": "1-2 business days",
  "submitted_at": "2026-08-15T16:30:00Z"
}
```

**Errors:**
- `400` — Missing required fields
- `409` — Duplicate detected (same student, same org, same date)
- `422` — Hours exceed 24 in one day (flagged for review)

---

#### `PUT /api/student/service-log/{service_log_id}`
**Purpose:** Student edits submitted (but unapproved) hours  
**Auth:** Student (required)  
**Body:**
```json
{
  "hours_claimed": 4.0,
  "activity_description": "Updated description..."
}
```

**Response (200):**
```json
{
  "service_log_id": "sl_789",
  "hours_claimed": 4.0,
  "message": "Updated. Waiting for supervisor approval.",
  "updated_at": "2026-08-15T17:00:00Z"
}
```

**Constraints:** Can only edit if status is 'submitted' (not after approval/rejection)

---

#### `DELETE /api/student/service-log/{service_log_id}`
**Purpose:** Student deletes unapproved hours (right to deletion)  
**Auth:** Student (required)  
**Response (204):** No content

---

### 3. Student Disputes

#### `POST /api/student/disputes`
**Purpose:** Student disputes rejected or adjusted hours  
**Auth:** Student (required)  
**Body:**
```json
{
  "service_log_id": "sl_789",
  "dispute_type": "hours_rejected",
  "dispute_reason": "I worked 4 hours but was told 3 were approved. I have documentation.",
  "evidence_url": null  // Optional link to documentation
}
```

**Response (201):**
```json
{
  "dispute_id": "disp_123",
  "service_log_id": "sl_789",
  "resolution_status": "open",
  "school_admin": {
    "name": "John Coordinator",
    "email": "john@school.edu"
  },
  "message": "Dispute filed. School coordinator will review within 3 business days.",
  "filed_at": "2026-08-16T10:00:00Z"
}
```

---

### 4. Certificates & Verification

#### `GET /api/student/certificate`
**Purpose:** Get student's verified service certificate  
**Auth:** Student (required)  
**Response (200):**
```json
{
  "certificate_id": "cert_456",
  "certificate_number": "DAANAA-2026-08-12345",
  "total_hours_verified": 24,
  "service_period_start": "2026-08-01",
  "service_period_end": "2026-12-15",
  "issued_at": "2026-12-20T00:00:00Z",
  "certificate_status": "active",
  "organizations_served": [
    {
      "nonprofit_name": "Community Health Center",
      "hours_verified": 12
    },
    {
      "nonprofit_name": "Food Bank",
      "hours_verified": 12
    }
  ],
  "message": "Download your verified service certificate below.",
  "download_url": "/api/student/certificate/download",
  "verification_url": "https://daanaa.org/verify/DAANAA-2026-08-12345"
}
```

---

#### `GET /api/student/certificate/download`
**Purpose:** Download certificate as PDF  
**Auth:** Student (required)  
**Response (200):** PDF file (Content-Type: application/pdf)

---

#### `GET /api/verify/{certificate_number}`
**Purpose:** Public endpoint to verify certificate authenticity  
**Auth:** None (public)  
**Response (200):**
```json
{
  "valid": true,
  "certificate_number": "DAANAA-2026-08-12345",
  "student_name": "Redacted (privacy)",
  "total_hours": 24,
  "issued_by": "Daanaa Student Service Program",
  "issued_at": "2026-12-20",
  "status": "active",
  "message": "This certificate is authentic and verified."
}
```

**Note:** Student name is redacted from public verification (privacy-first).

---

### 5. Student Profile & Account

#### `GET /api/student/profile`
**Purpose:** Get student's profile and enrollment status  
**Auth:** Student (required)  
**Response (200):**
```json
{
  "student_id": "stu_123",
  "first_name": "Alex",
  "last_name": "Student",
  "school_name": "Lincoln High School",
  "enrollment_status": "active",
  "age_group": "13-17",
  "enrolled_at": "2026-08-01T10:00:00Z",
  "service_hours": {
    "total_submitted": 28,
    "total_approved": 24,
    "pending": 4
  },
  "opportunities_enrolled": 2,
  "certificates_earned": 1
}
```

---

#### `PUT /api/student/profile`
**Purpose:** Update student profile (minimal fields allowed)  
**Auth:** Student (required)  
**Body:**
```json
{
  "email": "alex.student@school.edu",
  "phone": "+1-555-0123"
}
```

**Note:** Name and school are immutable (set at enrollment by school admin)

---

#### `POST /api/student/data-export`
**Purpose:** Export all student data (GDPR/CCPA right to portability)  
**Auth:** Student (required)  
**Response (200):**
```json
{
  "data_export_id": "exp_789",
  "status": "processing",
  "message": "Your data export is being prepared. Download link will be emailed in 24 hours.",
  "expires_at": "2026-08-24T10:00:00Z"
}
```

---

#### `DELETE /api/student/account`
**Purpose:** Delete student account and all data (right to be forgotten)  
**Auth:** Student (required)  
**Body:**
```json
{
  "reason": "No longer need to track hours",
  "confirm": true
}
```

**Response (204):** No content

**Note:** Approved service records de-identified but retained for audit; unapproved records deleted.

---

## NONPROFIT SUPERVISOR ENDPOINTS

### 1. Pending Approvals (extended from existing)

#### `GET /api/nonprofit/{ein}/student-hours/pending`
**Purpose:** See student service submissions awaiting approval  
**Auth:** Nonprofit supervisor (existing nonprofit auth)  
**Query Params:**
- `status` (optional) — 'submitted', 'flagged'
- `sort` (optional) — 'recent', 'oldest'

**Response (200):**
```json
{
  "data": [
    {
      "service_log_id": "sl_789",
      "student_name": "Alex Student",  // School-mediated; supervisor knows student
      "service_date": "2026-08-15",
      "hours_claimed": 4,
      "activity_description": "Taught health education class",
      "submitted_at": "2026-08-15T16:30:00Z",
      "submitted_by_school": "Lincoln High School",
      "duplicate_flag": false,
      "outofnorm_flag": false
    }
  ],
  "pending_count": 3,
  "flagged_count": 1
}
```

---

#### `POST /api/nonprofit/{ein}/student-hours/{service_log_id}/approve`
**Purpose:** Supervisor approves hours  
**Auth:** Nonprofit supervisor (required)  
**Body:**
```json
{
  "hours_verified": 4,
  "notes": "Attendance confirmed. Great work!"
}
```

**Response (200):**
```json
{
  "service_log_id": "sl_789",
  "approval_status": "approved",
  "hours_verified": 4,
  "approved_at": "2026-08-16T09:00:00Z",
  "message": "Hours approved. Certificate will be generated at semester end."
}
```

---

#### `POST /api/nonprofit/{ein}/student-hours/{service_log_id}/reject`
**Purpose:** Supervisor rejects hours with reason  
**Auth:** Nonprofit supervisor (required)  
**Body:**
```json
{
  "rejection_reason": "Student did not show up for scheduled shift",
  "notes": "Check with attendance office"
}
```

**Response (200):**
```json
{
  "service_log_id": "sl_789",
  "approval_status": "rejected",
  "rejected_at": "2026-08-16T09:00:00Z",
  "message": "Hours rejected. Student can dispute if they disagree."
}
```

---

### 2. Student Opportunities Management

#### `POST /api/nonprofit/{ein}/opportunities`
**Purpose:** Create volunteer opportunity for students  
**Auth:** Nonprofit admin (required)  
**Body:**
```json
{
  "title": "Community Health Education",
  "description": "Help teach health education to high school students",
  "cause_area": "Health",
  "location": "Downtown Office",
  "location_type": "in-person",
  "commitment_hours": 8,
  "available_start": "2026-08-01",
  "available_end": "2026-12-15",
  "supervisor_name": "Jane Smith",
  "supervisor_email": "jane@nonprofit.org"
}
```

**Response (201):**
```json
{
  "opportunity_id": "opp_123",
  "nonprofit_ein": "123456789",
  "is_active": true,
  "created_at": "2026-07-22T15:30:00Z",
  "message": "Opportunity published. Students can now enroll."
}
```

---

#### `GET /api/nonprofit/{ein}/opportunities`
**Purpose:** View nonprofit's opportunities and enrollment  
**Auth:** Nonprofit admin (required)  
**Response (200):**
```json
{
  "data": [
    {
      "opportunity_id": "opp_123",
      "title": "Community Health Education",
      "is_active": true,
      "students_enrolled": 3,
      "students_in_progress": 2,
      "created_at": "2026-07-22T15:30:00Z"
    }
  ]
}
```

---

## SCHOOL ADMIN ENDPOINTS

### 1. Student Enrollment (School-Mediated)

#### `POST /api/school/{school_ein}/students/enroll`
**Purpose:** School admin enrolls student in program  
**Auth:** School admin (required)  
**Body:**
```json
{
  "student_email": "alex@school.edu",
  "first_name": "Alex",
  "last_name": "Student",
  "date_of_birth": "2010-05-15",
  "parental_consent_required": true
}
```

**Response (201):**
```json
{
  "student_id": "stu_123",
  "enrollment_status": "invited",
  "message": "Student invited to program. Enrollment link sent to school email.",
  "enrollment_expires_at": "2026-08-15T00:00:00Z"
}
```

---

#### `GET /api/school/{school_ein}/students`
**Purpose:** View all enrolled students  
**Auth:** School admin (required)  
**Response (200):**
```json
{
  "data": [
    {
      "student_id": "stu_123",
      "name": "Alex Student",
      "enrollment_status": "active",
      "total_hours_submitted": 28,
      "total_hours_approved": 24,
      "certificates_earned": 1,
      "enrolled_at": "2026-08-01T10:00:00Z"
    }
  ],
  "summary": {
    "total_students": 42,
    "active": 38,
    "completed": 4
  }
}
```

---

### 2. Dispute Resolution

#### `GET /api/school/{school_ein}/disputes`
**Purpose:** View disputes pending school review  
**Auth:** School admin (required)  
**Response (200):**
```json
{
  "data": [
    {
      "dispute_id": "disp_123",
      "student_name": "Alex Student",
      "nonprofit_name": "Community Health Center",
      "dispute_type": "hours_rejected",
      "dispute_reason": "I worked 4 hours but was told 3 were approved",
      "filed_at": "2026-08-16T10:00:00Z",
      "resolution_status": "open"
    }
  ],
  "pending_count": 2
}
```

---

#### `POST /api/school/{school_ein}/disputes/{dispute_id}/resolve`
**Purpose:** School admin mediates dispute  
**Auth:** School admin (required)  
**Body:**
```json
{
  "decision": "hours_approved",
  "decision_reason": "Student documentation confirms 4 hours worked",
  "notes": "Contacted nonprofit supervisor; they will resubmit approval"
}
```

**Response (200):**
```json
{
  "dispute_id": "disp_123",
  "resolution_status": "resolved",
  "decision": "hours_approved",
  "resolved_at": "2026-08-17T14:00:00Z"
}
```

---

## ADMIN ENDPOINTS

### 1. Audit & Compliance

#### `GET /api/admin/student-service/audit-log`
**Purpose:** Admin views service records for compliance audit  
**Auth:** Admin (required, X-Admin-Key header)  
**Query Params:**
- `student_id` (optional)
- `nonprofit_ein` (optional)
- `action` (optional) — 'login', 'submit_hours', 'approve', etc.
- `date_range` (optional) — 'today', 'week', 'month'

**Response (200):**
```json
{
  "data": [
    {
      "audit_id": "aud_789",
      "action": "service_log_submitted",
      "resource_type": "service_log",
      "resource_id": "sl_789",
      "actor_type": "student",
      "timestamp": "2026-08-15T16:30:00Z",
      "ip_address_hash": "sha256:abc123..."  // Never full IP
    }
  ],
  "total": 142,
  "filtered_by": { "nonprofit_ein": "123456789", "action": "service_log_submitted" }
}
```

---

### 2. Fraud Detection & Flags

#### `GET /api/admin/student-service/flagged-records`
**Purpose:** View records flagged for duplicate or fraud review  
**Auth:** Admin (required)  
**Response (200):**
```json
{
  "duplicate_flags": [
    {
      "flag_id": "flag_123",
      "service_log_id": "sl_789",
      "student_id": "stu_123",
      "nonprofit_ein": "123456789",
      "flag_type": "duplicate_submission",
      "flagged_at": "2026-08-15T16:35:00Z",
      "hours_involved": 4,
      "potential_duplicate": "sl_790"
    }
  ],
  "outlier_flags": [
    {
      "flag_id": "flag_124",
      "service_log_id": "sl_791",
      "hours_claimed": 16,  // Unusually high
      "flag_reason": "Hours exceed typical shift length",
      "requires_review": true
    }
  ]
}
```

---

### 3. Certificate Revocation

#### `POST /api/admin/student-service/certificate/{certificate_id}/revoke`
**Purpose:** Admin revokes certificate if fraud detected  
**Auth:** Admin (required)  
**Body:**
```json
{
  "reason": "Duplicate hour submission detected",
  "documentation": "See audit log entries 456, 457"
}
```

**Response (200):**
```json
{
  "certificate_id": "cert_456",
  "status": "revoked",
  "revoked_at": "2026-08-17T10:00:00Z",
  "message": "Certificate revoked. Student has been notified."
}
```

---

## Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad request (missing/invalid fields) | `{"error": "Missing required field: nonprofit_ein"}` |
| 401 | Unauthorized (no token or invalid token) | `{"error": "Invalid or expired Firebase token"}` |
| 403 | Forbidden (insufficient permissions) | `{"error": "You do not own this nonprofit"}` |
| 404 | Not found | `{"error": "Service log not found"}` |
| 409 | Conflict (duplicate submission) | `{"error": "Duplicate hour submission detected"}` |
| 422 | Unprocessable entity (validation fails) | `{"error": "Hours exceed 24 in one day"}` |
| 500 | Server error | `{"error": "Internal server error"}` |

---

## Rate Limiting

- **Students:** 100 requests/minute per user
- **Nonprofit supervisors:** 300 requests/minute per nonprofit
- **School admins:** 150 requests/minute per school
- **Admin endpoints:** 50 requests/minute per key

---

## Privacy & Security Notes

1. **No student PII in public API** — Verification endpoint redacts student names
2. **No IP persistence** — Logged for fraud detection, hashed in audit trail, deleted after 7 days
3. **No location tracking** — Only location_type (in-person/remote/hybrid) stored
4. **Supervisor-mediated** — School admin is intermediary for any nonprofit-student communication
5. **Data deletion** — Students can delete all data; soft-delete via `deleted_at` timestamp
6. **Audit trail** — All actions logged with actor, action, timestamp, IP hash
7. **Fraud detection** — Duplicate detection, outlier flags, manual audits

---

## Implementation Priority

**Phase 1 (Weeks 2-3):**
- Student discovery endpoints (GET opportunities)
- Service log submission (POST/PUT/DELETE)
- Nonprofit approval endpoints (extend existing)
- Certificate generation

**Phase 2 (Weeks 4-5):**
- Student disputes
- Student profile & account management
- School admin enrollment & dispute mediation

**Phase 3 (Weeks 6-8):**
- Audit & compliance endpoints
- Fraud detection & flagging
- Data export & deletion
- Advanced reporting

---

## Testing Strategy

- **Unit tests:** Each endpoint tested with valid/invalid inputs
- **Integration tests:** Full workflows (discover → enroll → log → approve → certificate)
- **Privacy tests:** Verify no student data exposed in public endpoints
- **Load tests:** Ensure endpoints perform under 1000+ concurrent requests
- **Manual QA:** Human testing of complete user flows (student & nonprofit perspectives)
