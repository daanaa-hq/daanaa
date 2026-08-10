# Profile Correction & Provenance — Implementation Plan

## Goal
Enable nonprofits to correct and enhance their profile with a complete audit trail. All changes are versioned and attributed to their source (IRS, nonprofit-supplied, AI-generated, Daanaa-corrected).

---

## Core Principle: Source Attribution

Every significant field shows:
```
Field Value
Source: IRS Form 990, 2023 filing
Last verified: 2026-06-15
Can nonprofit edit: Yes / No
```

Example variations:
- "Austin Community Coalition" (IRS) ← Can't change, sourced from official data
- "Provides after-school tutoring for underserved kids" (Nonprofit-supplied) ← Can edit, nonprofit wrote this
- "Education, Youth Services" (AI-generated tags) ← Nonprofit can refine

---

## Data Model

### New Table: `profile_edits` (Audit Log)
```sql
CREATE TABLE profile_edits (
  id INTEGER PRIMARY KEY,
  ein TEXT NOT NULL,
  field_name TEXT NOT NULL,  -- 'mission', 'website', 'donate_url', etc.
  old_value TEXT,
  new_value TEXT,
  edit_source TEXT NOT NULL,  -- 'nonprofit', 'admin', 'automated'
  editor_email TEXT,
  editor_name TEXT,
  reason TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  published_at TEXT,
  approval_status TEXT DEFAULT 'pending'  -- pending, approved, rejected
);
```

### New Table: `nonprofit_supplied_data`
```sql
CREATE TABLE nonprofit_supplied_data (
  id INTEGER PRIMARY KEY,
  ein TEXT NOT NULL UNIQUE,
  programs_description TEXT,
  service_areas TEXT,
  target_populations TEXT,
  impact_statement TEXT,
  leadership_bios TEXT,
  social_media_links TEXT,
  partnerships TEXT,
  last_updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  nonprofit_contact_email TEXT,
  nonprofit_verified_at TEXT
);
```

### Update: `registry_enriched`
Add fields for field-level source tracking:
```sql
ALTER TABLE registry_enriched ADD COLUMN IF NOT EXISTS
  mission_source TEXT DEFAULT 'irs',  -- 'irs' | 'ai_generated' | 'nonprofit_supplied'
  mission_last_verified TEXT;

ALTER TABLE registry_enriched ADD COLUMN IF NOT EXISTS
  website_source TEXT DEFAULT 'irs',
  website_last_verified TEXT;

-- Repeat for: donate_url, cause_tags, etc.
```

---

## Three-Tier Profile Data

### Tier 1: Public Records (IRS)
```
Field               Source              Editable
─────────────────────────────────────────────────
Name                Form 990            No (but can add context)
EIN                 Form 990            No
Address             Form 990            No
Tax Status          Form 990            No
```

### Tier 2: Nonprofit-Supplied (In Control)
```
Field               Source                    Editable
───────────────────────────────────────────────────────
Mission             Nonprofit (or AI initial) Yes
Programs            Nonprofit                 Yes
Service Areas       Nonprofit                 Yes
Leadership Bios     Nonprofit                 Yes
Contact Info        Nonprofit                 Yes
```

### Tier 3: Data Enhancements (Daanaa)
```
Field               Source              Editable
─────────────────────────────────────────────────
Cause Tags          AI-extracted        Yes (nonprofit refines)
Website Health      Automated check      No
Financial Metrics   IRS SOI             No
```

---

## Edit Flow

```
1. NONPROFIT EDITS FIELD
   Form: "Edit Mission Statement"
   ↓
2. SUBMIT WITH REASON
   "Updated for accuracy, now focuses on tech access"
   ↓
3. PREVIEW CHANGES
   Side-by-side: Old value | New value
   ↓
4. CONFIRM
   Stored in profile_edits (status: pending)
   ↓
5a. IMMEDIATE (Nonprofit Edits)
    Status: 'approved' automatically
    Visible to donors within 5 minutes
    ↓
5b. ADMIN REVIEW (If controversial)
    Status: 'pending'
    Admin reviews within 24 hours
    ↓
6. PUBLIC UPDATE
   Field updated in registry_enriched
   Change logged in version history
   Donors see: "Last updated by nonprofit on 2026-07-23"
```

---

## Frontend Components

### 1. ProfileEditor.tsx (Main Page)
- Tabs: Overview | Mission | Programs | Services | Contacts | History
- Each tab shows: Current value + Edit button
- Edit button opens modal with guidance

### 2. ProfileEditModal.tsx
- Form with field + reason textarea
- Preview of changes
- "Save" button
- Validation (mission min 50 chars, etc.)

### 3. ProfileChangeHistory.tsx
- Timeline of all edits
- Shows: Old → New, date, nonprofit email, status
- Filter by field
- Revert option for mistakes

### 4. SourceAttribution.tsx
- Small component showing:
  ```
  [Source icon] IRS Form 990
  Last verified: June 15, 2026
  [Edit] [History]
  ```

### 5. NonprofitProfilePreview.tsx
- Shows nonprofit exactly how donors see it
- Read-only
- "This is what donors see" messaging
- "Edit" button takes to ProfileEditor

---

## Backend Endpoints

### GET /api/nonprofit/<ein>/profile/editable
Returns all editable fields with current values, sources, and edit history:
```json
{
  "organization": { ... },
  "editable_fields": {
    "mission": {
      "value": "...",
      "source": "nonprofit_supplied",
      "last_updated": "2026-06-15",
      "last_updated_by": "exec@org.org",
      "editable": true,
      "char_count": 145,
      "char_limit": 500
    },
    "programs": { ... }
  },
  "recent_edits": [
    {
      "field": "mission",
      "old_value": "...",
      "new_value": "...",
      "date": "2026-06-15",
      "editor": "exec@org.org",
      "reason": "Updated for accuracy",
      "status": "approved"
    }
  ]
}
```

### POST /api/nonprofit/<ein>/profile/edit
Submit a field edit:
```json
{
  "field_name": "mission",
  "new_value": "...",
  "reason": "Updated for accuracy",
  "nonprofit_email": "exec@org.org"
}
```

Response:
```json
{
  "edit_id": "e-12345",
  "status": "approved",
  "message": "Mission updated. Visible to donors within 5 minutes."
}
```

### GET /api/nonprofit/<ein>/profile/history
Get full edit history:
```json
{
  "changes": [
    {
      "field": "mission",
      "old_value": "...",
      "new_value": "...",
      "date": "2026-06-15",
      "editor": "exec@org.org",
      "status": "approved"
    }
  ]
}
```

### GET /api/public/nonprofit/<ein>/profile/sources
Public endpoint showing data provenance:
```json
{
  "organization_name": {
    "value": "Austin Community Coalition",
    "source": "irs",
    "source_label": "Form 990 (IRS)",
    "last_verified": "2026-06-15"
  },
  "mission": {
    "value": "...",
    "source": "nonprofit_supplied",
    "source_label": "Nonprofit-supplied",
    "last_updated": "2026-06-15"
  }
}
```

---

## Validation Rules

### Mission
- Min: 50 characters
- Max: 500 characters
- Required field
- No HTML

### Programs & Services
- Min: 100 characters
- Max: 2000 characters
- Markdown allowed (basic: **bold**, *italic*, links)
- No HTML

### Service Areas
- Select from predefined list
- Max: 5 areas
- Or free-text if not listed

### Website
- Must be valid URL
- Must be accessible (health check)
- Must match org

### Contact Email
- Valid email format
- Will send verification email
- Only nonprofit can edit

---

## Privacy & Stewardship Alignment

✅ **Principle #2 (Privacy)** — No tracking of who views edits
✅ **Principle #3 (Trust signals)** — All sources visible, traceable
✅ **Principle #4 (Fairness to small orgs)** — Simple form, no complex approval
✅ **Principle #5 (No shame)** — Neutral language ("Review" not "Fix")
✅ **Principle #6 (Quick corrections)** — Immediate approval for nonprofits
✅ **Principle #9 (Explainable decisions)** — Full edit trail available

---

## Implementation Timeline

### Phase 1: Backend (1.5 hours)
- [ ] Create tables (profile_edits, nonprofit_supplied_data)
- [ ] Implement endpoints (GET editable, POST edit, GET history, GET sources)
- [ ] Add Firebase auth + EIN verification
- [ ] Add validation + rate limiting

### Phase 2: Frontend (1.5 hours)
- [ ] ProfileEditor page with tabs
- [ ] ProfileEditModal with form
- [ ] SourceAttribution component
- [ ] Edit history timeline

### Phase 3: Testing & Polish (45 min)
- [ ] E2E: Edit mission, see update on profile
- [ ] Verify: Old value preserved in history
- [ ] Verify: Donors see "last updated by nonprofit"
- [ ] Responsive design

---

## Success Criteria

- [ ] Nonprofit can edit mission, programs, services
- [ ] Every edit logged with reason & timestamp
- [ ] Donors see current values + "updated by nonprofit" date
- [ ] Public endpoint shows source of every field
- [ ] Change history shows old → new
- [ ] Edits appear within 5 minutes
- [ ] No duplicate edits (idempotent)
- [ ] Mobile-friendly edit form

---

## Feeds Into

1. **Donor Preview** — Shows donors the exact profile the nonprofit sees
2. **Reporting Pack** — Exports profile with source labels
3. **"What Changed?"** — Shows donors when orgs update
4. **Public Evidence** — Researchers see data provenance

---

Ready to implement? Start with backend tables + endpoints.
