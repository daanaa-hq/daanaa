# Daanaa Volunteer Hours System — Complete Specification
**Status:** Ready to build | **Timeline:** Sprint (5 days) | **Impact:** Platform-wide impact measurement foundation

---

## VISION

Nonprofits self-manage volunteer hour tracking. Daanaa aggregates into yearly impact totals that show collective nonprofit ecosystem health.

**By end of 2026:** "Daanaa nonprofits coordinated 2.1M volunteer hours, worth $47M in labor value"

---

## ARCHITECTURE

```
TIER 1: Individual Nonprofit Level
├── Event Creation (nonprofit dashboard)
│   ├── Event name, date, location, task types
│   ├── Auto-generate QR code + short URL
│   └── Tier 2 data classification
│
├── Volunteer Submission (QR/link → form)
│   ├── Name, email, hours, task type
│   ├── Auto-logged, status = "pending"
│   └── Audit log entry (timestamp, IP, etc.)
│
└── Nonprofit Approval (dashboard)
    ├── List pending/approved/rejected
    ├── Approve with 1 click (or reject with reason)
    ├── 30-day edit window → immutable lock
    ├── Audit trail (who approved, when)
    └── Export (CSV/PDF with metadata)

TIER 2: Nonprofit-Aggregated Reporting
├── Nonprofit dashboard shows:
│   ├── Total hours this year (all events)
│   ├── By task type (breakdown)
│   ├── Year-over-year trend
│   └── "Share impact" button (to public profile, optional)
│
└── Nonprofit can choose to expose:
    ├── Total volunteer hours on public profile
    ├── Impact statement: "X hours from Y volunteers"
    └── Or keep private (default)

TIER 3: Platform-Level Impact Dashboard
├── Daanaa-wide aggregates (admins only initially)
│   ├── Total volunteer hours submitted (all nonprofits)
│   ├── Total hours approved (quality metric)
│   ├── By cause/region/size
│   ├── Labor value estimate (hours × $22.50/hour avg)
│   └── Trend over time
│
├── Public impact page (eventually)
│   ├── "The nonprofit sector coordinated X hours in 2026"
│   ├── Breakdown by cause, state, sector
│   ├── "Discover organizations with high volunteer engagement"
│   └── (Privacy: only show aggregate, never individual volunteer data)
│
└── Reporting for Daanaa & partners
    ├── Annual impact report
    ├── Nonprofit-level dashboards (their own data)
    └── Never: external sale/use without consent (Tier 2 lock)
```

---

## DATABASE SCHEMA (NEW & MODIFIED)

### volunteer_events (EXISTING, enhance)
```sql
CREATE TABLE volunteer_events (
  id                    INTEGER PRIMARY KEY,
  nonprofit_ein         TEXT NOT NULL,
  title                 TEXT NOT NULL,
  event_date            TEXT NOT NULL,  -- YYYY-MM-DD
  location_city         TEXT,
  location_state        TEXT,
  short_id              TEXT UNIQUE,    -- For QR code short URL
  qr_code_url           TEXT,           -- Generated on creation
  status                TEXT DEFAULT 'active',
  
  -- NEW FIELDS
  task_types            JSON,           -- ["volunteer", "marshal", "registration", "cleanup"]
  total_hours_approved  FLOAT DEFAULT 0,  -- Cache for performance
  volunteer_count       INT DEFAULT 0,
  public_visibility     BOOLEAN DEFAULT 0,  -- Can nonprofit share this on their profile?
  
  created_by_ein        TEXT NOT NULL,
  created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at            TIMESTAMP  -- Soft delete for audit trail
);
```

### volunteer_hour_submissions (NEW - all submissions, immutable after 30d)
```sql
CREATE TABLE volunteer_hour_submissions (
  id                    TEXT PRIMARY KEY,  -- UUID
  event_id              INTEGER NOT NULL,
  nonprofit_ein         TEXT NOT NULL,
  
  -- Volunteer info (Tier 2)
  volunteer_name        TEXT NOT NULL,
  volunteer_email       TEXT NOT NULL,
  
  -- Hours submitted
  hours_submitted       FLOAT NOT NULL,
  task_type             TEXT NOT NULL,  -- "volunteer", "marshal", etc.
  notes                 TEXT,
  
  -- Status
  status                TEXT DEFAULT 'pending',  -- pending, approved, rejected
  rejected_reason       TEXT,  -- If rejected
  
  -- Approval
  approved_by_ein       TEXT,  -- Which nonprofit staff approved
  approved_at           TIMESTAMP,
  
  -- Audit & corrections
  submitted_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  edited_at             TIMESTAMP,  -- Last edit timestamp
  edit_count            INT DEFAULT 0,  -- How many times edited
  locked_at             TIMESTAMP,  -- Locked after 30 days (no more edits)
  
  FOREIGN KEY (event_id) REFERENCES volunteer_events(id),
  UNIQUE(event_id, volunteer_email, submitted_at)  -- Prevent duplicate
);
```

### volunteer_hours_audit_log (NEW - immutable log)
```sql
CREATE TABLE volunteer_hours_audit_log (
  id                    INTEGER PRIMARY KEY,
  submission_id         TEXT NOT NULL,
  action                TEXT,  -- "submitted", "edited", "approved", "rejected", "locked"
  changed_by_ein        TEXT,  -- WHO made the change
  changed_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  change_details        JSON,  -- {"field": "hours_submitted", "old": 8, "new": 10}
  ip_address            TEXT,  -- For security
  
  FOREIGN KEY (submission_id) REFERENCES volunteer_hour_submissions(id)
);
```

### nonprofit_yearly_impact_cache (NEW - for performance)
```sql
CREATE TABLE nonprofit_yearly_impact_cache (
  nonprofit_ein         TEXT PRIMARY KEY,
  year                  INT,
  
  total_hours_approved  FLOAT,
  volunteer_count       INT,
  event_count           INT,
  
  -- Breakdowns
  hours_by_task_type    JSON,  -- {"volunteer": 150, "marshal": 30}
  hours_by_month        JSON,  -- {"01": 50, "02": 60, ...}
  
  -- Cache metadata
  last_updated          TIMESTAMP,
  is_public             BOOLEAN,  -- Is nonprofit's data visible on their profile?
  
  UNIQUE(nonprofit_ein, year)
);
```

### platform_impact_cache (NEW - for admin dashboard)
```sql
CREATE TABLE platform_impact_cache (
  year                  INT PRIMARY KEY,
  
  total_hours_submitted FLOAT,  -- Across all nonprofits
  total_hours_approved  FLOAT,
  total_events          INT,
  total_unique_volunteers INT,
  
  -- Aggregates
  hours_by_cause        JSON,  -- {"health": 500000, "education": 400000, ...}
  hours_by_state        JSON,
  hours_by_nonprofit_size JSON,  -- {"micro": ..., "professional": ..., "established": ...}
  
  -- Metrics
  approval_rate         FLOAT,  -- % of submitted hours that get approved
  avg_hours_per_volunteer FLOAT,
  labor_value_estimate  FLOAT,  -- total_hours_approved * $22.50
  
  last_updated          TIMESTAMP
);
```

---

## API ENDPOINTS (COMPLETE)

### Nonprofit Event Management
```
POST   /api/nonprofit/events
       Create new event
       Body: {title, event_date, location_city, location_state, task_types}
       Returns: {event_id, qr_code_url, short_url}

GET    /api/nonprofit/events
       List all events for authenticated nonprofit

GET    /api/nonprofit/events/{event_id}/qr.png
       Download QR code as PNG

GET    /api/nonprofit/events/{event_id}/submissions
       List volunteer submissions for this event (with filtering)
```

### Volunteer Submission
```
POST   /api/volunteer/submit-hours
       Volunteer logs hours via QR link
       Query param: event_id or short_id
       Body: {volunteer_name, volunteer_email, hours_submitted, task_type, notes}
       Returns: {submission_id, status: "pending"}
       No auth required (open to public via QR)
```

### Nonprofit Approval
```
POST   /api/nonprofit/submissions/{submission_id}/approve
       Approve a submission
       Body: {approver_ein} (from auth token)
       Returns: {status: "approved", approved_at}
       Creates audit log entry

POST   /api/nonprofit/submissions/{submission_id}/reject
       Reject a submission
       Body: {reason}
       Returns: {status: "rejected"}

PATCH  /api/nonprofit/submissions/{submission_id}/edit
       Edit a submission (only within 30-day window)
       Body: {hours_submitted, task_type, notes}
       Returns: {status: "pending_reapproval", edit_count}
       Requires re-approval if hours changed
```

### Reporting & Export
```
GET    /api/nonprofit/impact/{year}
       Nonprofit's yearly impact (their own data)
       Returns: {total_hours, volunteer_count, by_task_type, by_month}

GET    /api/nonprofit/impact/{year}/export
       Export nonprofit's volunteer hours data
       Query: format=csv|pdf
       Returns: File with "nonprofit-approved" label + metadata

GET    /api/admin/platform-impact/{year}
       Daanaa-wide impact (admin only)
       Returns: {total_hours, total_events, by_cause, by_state, approval_rate, labor_value}

GET    /api/public/nonprofit/{ein}/volunteer-impact
       Public impact data (only if nonprofit has opted into visibility)
       Returns: {year, total_hours_approved, volunteer_count, or error 404 if private}
```

---

## FRONTEND PAGES (NEW & MODIFIED)

### /nonprofit/events (NEW)
- List all nonprofit's events
- "Create Event" button
- Each event shows:
  - Date, location, status
  - Total submissions, approved count
  - QR code (downloadable)
  - Short link (copyable)
  - Link to submissions list

### /nonprofit/events/{id} (NEW)
- Event detail page
- Submissions list with filtering (pending/approved/rejected)
- Click to approve/reject
- "Export this event's hours"
- Volunteer email, hours, task type, status

### /nonprofit/impact (NEW)
- Yearly impact dashboard
- Total hours approved (this year)
- Breakdown: by task type, by month
- Chart: hours over time (last 5 years)
- "Make my impact public?" toggle
- Export button

### /e/{short_id} (NEW - public-facing)
- Volunteer signup page (reached via QR)
- Shows: nonprofit name, event name, date, location
- Form: volunteer name, email, hours (dropdown 0.5-8), task type, optional notes
- "Submit" button
- Success page: "Thank you! Org will review and approve."

### /volunteer/submit-hours (REDIRECT to /e/{short_id})
- Same experience, just different entry point

---

## PRIVACY & COMPLIANCE (STEWARDSHIP ALIGNMENT)

### Data Classification
- **Volunteer submissions:** Tier 2 (entrusted)
  - Name, email, hours, task type
  - Only nonprofit & volunteer can see
  - Never shared externally
  - Auto-delete after 7 years

- **Nonprofit-aggregated impact:** Tier 1 (optional public)
  - "Total hours approved this year"
  - "X volunteers contributed"
  - Only if nonprofit opts into visibility
  - Never individual volunteer data

- **Platform-level aggregates:** Tier 1 (public)
  - "Sector coordinated 2.1M hours in 2026"
  - No identifiable data
  - Cause/state/size breakdowns only

### Data Use Agreement
- Nonprofit signs on first event creation
- States:
  - Daanaa holds Tier 2 data as custodian, not owner
  - Data never shared externally without consent
  - 7-year retention, then auto-delete
  - Nonprofit approves their own data (Daanaa doesn't verify)
  - Audit trail available for legal disputes
  - Nonprofit can request data export/deletion anytime

### Export Labeling
All exports include:
```
VOLUNTEER HOURS REPORT
Nonprofit: [Name]
Year: 2026
Total Approved Hours: 1,234

⚠️ IMPORTANT: These hours were approved by nonprofit staff.
Daanaa does not independently verify volunteer hours.
This report is for your records only.

Prepared by: [nonprofit staff name]
Date: 2026-07-22
```

---

## DEPLOYMENT PLAN

### Phase 1: Core (Days 1-2)
- [ ] Database schema (tables + indexes)
- [ ] API endpoints (submit, approve, reject, export)
- [ ] Nonprofit event creation UI
- [ ] Volunteer submission form
- [ ] Audit logging

### Phase 2: Polish (Days 3-4)
- [ ] 30-day edit window + immutable lock
- [ ] Nonprofit impact dashboard
- [ ] Export (CSV + PDF)
- [ ] Data use agreement modal
- [ ] QR code generation + short URLs

### Phase 3: Aggregation (Day 5)
- [ ] Nonprofit yearly impact cache (auto-update)
- [ ] Platform impact dashboard (admin)
- [ ] Public profile integration (optional visibility)
- [ ] Impact page on Daanaa homepage

### Phase 4: Launch (After testing)
- [ ] Golf tournament trial (real data)
- [ ] Feedback loop
- [ ] General availability

---

## SUCCESS METRICS

- ✅ Nonprofits creating events (adoption)
- ✅ Volunteers submitting hours (engagement)
- ✅ Approval rate (quality)
- ✅ Export usage (they're really using it)
- ✅ Privacy incidents (zero)
- ✅ Data accuracy disputes (track & resolve quickly)
- ✅ Year-end platform impact metric (scale validation)

---

## FUTURE (POST-MVP)

1. **Volunteer profiles:** Volunteers can track their own hours across nonprofits
2. **Impact matching:** "Your X hours helped [nonprofit] achieve Y"
3. **Volunteer badges:** "100-hour volunteer" on Daanaa profiles
4. **Nonprofit comparisons:** "Peer organizations average 50K hours/year"
5. **Funder insights:** "This nonprofit mobilized 10K volunteers in 2026"
6. **Time-banking:** Nonprofits credit donors with "volunteer time value"

---

## DECISION LOG

**Approved by:** Extended Board Council (simulated 2026-07-22)
**Data Classification:** Tier 2 (Volunteer data), Tier 1 (Aggregates)
**Verification Model:** Nonprofit-approved (they're liable)
**Edit Window:** 30 days, then immutable
**Retention:** 7 years, then auto-delete
**Public Visibility:** Opt-in (nonprofit controls)
**Launch:** MVP ready for golf tournament trial (2026-07-22)

