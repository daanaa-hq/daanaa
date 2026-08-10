# Nonprofit Overview Dashboard — Complete

## Status: ✅ BUILT & READY

Built the foundational nonprofit overview dashboard in parallel while you're testing the volunteer hours system.

---

## What Was Built

### Backend API: `/api/nonprofit/<ein>/dashboard/overview`
- Single endpoint returns all dashboard data in one call
- Requires Firebase authentication
- EIN-gated (users can only access their claimed orgs)
- Returns:
  - Organization basics (name, EIN, mission, website)
  - Attention items (pending approvals, profile gaps)
  - Volunteer summary (hours, trend, top volunteers, counts)
  - Profile health (completeness %, missing fields)
  - Upcoming events (next 30 days)
  - Recent activity flags

### Frontend: `DashboardOverview.tsx`
- Main dashboard page at `/nonprofit/overview/:ein`
- Displays all dashboard data in visual cards
- Shows alerts for items needing attention
- Volunteer summary with trend analysis
- Profile completeness meter
- Upcoming events list
- Quick action buttons

### Integration
- Added route to App.tsx
- Updated MyOrgsPage to navigate to new dashboard
- Links to volunteer approval, profile editing, event creation
- Responsive design (mobile-first)

---

## Dashboard Sections

### 1. Attention Alert (Top)
Red/amber card showing:
- Pending volunteer approvals (clickable to approve)
- Profile gaps to complete (clickable to edit)
- Profile staleness (>90 days)

### 2. Volunteer Summary Card
- This month's hours (large display)
- Labor value estimate
- Trend vs last month (with % change)
- Counts: Pending, Approved, Rejected
- Top 3 volunteers by hours
- "Manage Approvals" quick button

### 3. Profile Health Card
- Completeness percentage (progress bar)
- Missing/incomplete fields listed
- "Edit Profile" quick button

### 4. Upcoming Events Card
- Events in next 30 days
- Event date with days countdown
- "View" link for each event

### 5. Quick Actions Bar
- 3 main buttons: Edit Profile, Approve Hours, Create Event

---

## Data Flows

```
User logs in to nonprofit portal
  ↓
Click organization in "My Organizations"
  ↓
Navigate to /nonprofit/overview/:ein
  ↓
API calls /api/nonprofit/<ein>/dashboard/overview
  ↓
API fetches from:
  - org_claims (org basics)
  - registry_enriched (mission, website)
  - volunteer_hours (approvals, hours, trends)
  - volunteer_events (upcoming events)
  ↓
Dashboard renders all cards with real data
```

---

## Technical Details

### Authentication
- Firebase UID required (`_require_firebase_user()`)
- Org claim verified before returning data
- No sensitive data exposed

### Performance
- Single API call (no waterfall)
- Queries optimized with WHERE clauses
- Data aggregation on backend (not frontend)
- <1s load time expected

### Responsive Design
- Desktop: 2-column grid (volunteer + profile side-by-side)
- Tablet: Stacked cards
- Mobile: Full-width cards
- Touch-friendly buttons

---

## Files Changed

### Backend
- `/home/akbar/meritgiving/daanaa_api.py`
  - Added `GET /api/nonprofit/<ein>/dashboard/overview` endpoint (80 lines)
  - Handles auth, data gathering, calculations
  - Returns JSON with all dashboard data

### Frontend
- `/home/akbar/meritgiving/frontend/src/pages/nonprofit/DashboardOverview.tsx` (NEW)
  - Main dashboard component (300 lines)
  - Renders all cards and sections
  - Handles loading/error states
  - Links to other nonprofit tools

- `/home/akbar/meritgiving/frontend/src/App.tsx`
  - Added import for DashboardOverview
  - Added route: `/nonprofit/overview/:ein`

- `/home/akbar/meritgiving/frontend/src/pages/nonprofit/MyOrgsPage.tsx`
  - Updated navigation to use `/nonprofit/overview/:ein` instead of `/nonprofit/dashboard/:ein`

---

## Next Steps

This dashboard is the foundation for:
1. ✅ Volunteer hours (already done)
2. ⏳ Profile/provenance (can reference dashboard for org data)
3. ⏳ Donor perspective preview (can show how donors see the org)
4. ⏳ Reporting pack (can export dashboard data)
5. ⏳ Anonymous donor feedback (can display feedback themes)

---

## Testing

Once you finish the volunteer hours E2E test, you can test the dashboard:

1. Sign in as nonprofit (Google or token)
2. Click organization in "My Organizations"
3. Should see: Overview Dashboard with all cards
4. Verify:
   - ✅ Organization name/EIN displayed
   - ✅ Volunteer hours showing (if you approved some)
   - ✅ Profile completeness meter working
   - ✅ Quick action buttons navigate correctly
   - ✅ Upcoming events show (if you created one)

---

## What's Next

Ready to build:
1. **Profile Correction & Provenance** (30 min) — Nonprofit can edit/correct org info with versioning
2. **Donor Perspective Preview** (30 min) — Show nonprofit exactly how donors see their profile
3. **Reporting Pack** (45 min) — Export dashboard + profile + volunteer data as PDF/CSV
4. **Anonymous Donor Feedback** (20 min) — Aggregate "was this helpful?" responses
5. **Public Evidence Exports** (30 min) — Researchers/ESG/DAF can download anonymized datasets

Which would you like me to start next while you finish testing?
