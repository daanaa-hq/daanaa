# Nonprofit Overview Dashboard — Implementation Plan

## Overview
A single cohesive nonprofit dashboard showing what needs attention, upcoming deadlines, and quick-access tools.

## Current Status
- ✅ Volunteer hours approval system (done)
- ⏳ Dashboard overview (this task)
- 📋 Profile/provenance (next)
- 🔍 Donor perspective preview (next)
- 📊 Reporting pack (next)

---

## Dashboard Sections (Priority Order)

### 1. Overview Card (What Needs Attention)
Shows critical items in one place:
```
Items needing attention: 5
├─ 🕐 Pending volunteer approvals: 3
├─ 📝 Profile fields to review: 2
├─ 🔗 Missing donation link
├─ ⚠️  Outdated profile (last updated 8 months ago)
└─ 📅 Upcoming event: "Community Day" in 3 days
```

### 2. Volunteer Hours Summary Card
```
This Month: 12.5 hours
Previous Month: 8.0 hours
Trend: ↑ 56% increase
Top Volunteer: John (4.5 hours)

[View Pending] [Approve Hours]
```

### 3. Profile Health Card
```
Profile Completeness: 85%
✅ Name, EIN, Address
✅ Mission
✅ Donation link
❌ Programs (empty)
❌ Service areas (empty)

[Review Profile] [Edit]
```

### 4. Events Calendar
```
Upcoming Events (next 30 days):
- Community Cleanup Day - July 25 (3 days)
- Board Meeting - August 1 (10 days)
- Annual Gala - August 15 (24 days)

[View All] [Create Event]
```

### 5. Recent Activity
```
Profile Interactions (last 30 days):
- 342 profile views
- 28 saved by donors
- 5 volunteer signups

[View detailed analytics]
```

### 6. Quick Actions Menu
```
[Manage Profile] [Approve Hours] [Create Event]
[Export Report]  [View as Donor]  [Analytics]
```

---

## Data Requirements

### New Database Columns Needed
None - all data already exists in:
- `org_claims` — basic org info
- `volunteer_hours` — volunteer submissions
- `volunteer_events` — events
- `registry_enriched` — public profile data
- Analytics (to be added): profile views, saves

### Queries to Implement

```sql
-- Pending volunteer approvals count
SELECT COUNT(*) FROM volunteer_hours 
WHERE nonprofit_ein = ? AND status = 'submitted'

-- This month vs last month hours
SELECT 
  SUM(CASE WHEN strftime('%Y-%m', service_date) = ? THEN hours ELSE 0 END) as this_month,
  SUM(CASE WHEN strftime('%Y-%m', service_date) = ? THEN hours ELSE 0 END) as last_month
FROM volunteer_hours
WHERE nonprofit_ein = ? AND status = 'approved'

-- Profile completeness
SELECT 
  CASE WHEN name IS NOT NULL THEN 1 ELSE 0 END as has_name,
  CASE WHEN mission IS NOT NULL THEN 1 ELSE 0 END as has_mission,
  -- ... etc for each field
FROM registry_enriched WHERE EIN = ?

-- Upcoming events (next 30 days)
SELECT * FROM volunteer_events 
WHERE nonprofit_ein = ? AND event_date BETWEEN ? AND date('now', '+30 days')
ORDER BY event_date ASC

-- Top volunteers this month
SELECT volunteer_name, SUM(hours) as total_hours
FROM volunteer_hours
WHERE nonprofit_ein = ? AND status = 'approved' 
  AND strftime('%Y-%m', service_date) = ?
GROUP BY volunteer_name
ORDER BY total_hours DESC
LIMIT 3
```

---

## Backend Endpoints to Build

### GET /api/nonprofit/<ein>/dashboard/overview
Returns all dashboard data in one call:
```json
{
  "organization": {
    "ein": "10-1234567",
    "name": "Test Nonprofit",
    "mission": "...",
    "website": "...",
    "last_profile_update": "2026-06-15"
  },
  "attention": {
    "pending_approvals": 3,
    "profile_gaps": 2,
    "missing_links": 1,
    "days_since_profile_update": 37
  },
  "volunteer_summary": {
    "this_month_hours": 12.5,
    "last_month_hours": 8.0,
    "trend_percent": 56,
    "pending_count": 3,
    "approved_count": 18,
    "rejected_count": 1,
    "top_volunteers": [
      { "name": "John", "hours": 4.5 },
      { "name": "Jane", "hours": 3.2 }
    ]
  },
  "profile_health": {
    "completeness_percent": 85,
    "missing_fields": ["programs", "service_areas"],
    "needs_review": ["mission", "donate_url"]
  },
  "upcoming_events": [
    {
      "event_id": 1,
      "title": "Community Cleanup",
      "date": "2026-07-25",
      "days_until": 3,
      "volunteer_count": 0
    }
  ],
  "recent_activity": {
    "profile_views_30d": 342,
    "saves_30d": 28,
    "volunteer_signups_30d": 5
  }
}
```

---

## Frontend Components to Build

### Layout: `NonprofitDashboard.tsx` (Main Page)
```
├─ DashboardHeader (org name, sign out, notifications)
├─ AttentionCard (red alerts)
├─ VolunteerSummaryCard (chart or KPIs)
├─ ProfileHealthCard (progress bar)
├─ UpcomingEventsCard (list)
├─ RecentActivityCard (metrics)
└─ QuickActionsBar (buttons)
```

### Components Needed
1. **AttentionCard.tsx** — Shows items needing immediate attention
2. **VolunteerSummaryCard.tsx** — Hours, trend, top volunteers
3. **ProfileHealthCard.tsx** — Completeness meter + gaps
4. **UpcomingEventsCard.tsx** — Event list with countdown
5. **RecentActivityCard.tsx** — Aggregate analytics
6. **QuickActionsBar.tsx** — Navigation buttons

### Existing Components to Integrate
- VolunteerApproval.tsx (already built)
- VolunteerEventsPage.tsx (already built)

---

## Implementation Phases

### Phase 1: Backend API (Today)
- [ ] `/api/nonprofit/<ein>/dashboard/overview` endpoint
- [ ] Query implementation
- [ ] Firebase auth integration
- [ ] EIN validation

### Phase 2: Frontend Layout (Today)
- [ ] Main dashboard page layout
- [ ] Card components
- [ ] Data loading
- [ ] Error states

### Phase 3: Polish & Testing (Today)
- [ ] Responsive design
- [ ] Loading states
- [ ] Empty states
- [ ] E2E testing

---

## Success Criteria

- [ ] Dashboard loads in <1s
- [ ] All cards render with real data
- [ ] Responsive on mobile (stacks vertically)
- [ ] Error states handled gracefully
- [ ] No sensitive data exposed (only org data)
- [ ] Firebase auth required
- [ ] EIN verified on every request
- [ ] All counts match actual data
- [ ] Links to other tools work (approvals, events, profile)

---

## Files to Create/Modify

### New Files
- `backend: /api/nonprofit/<ein>/dashboard/overview` in daanaa_api.py
- `frontend: src/pages/nonprofit/DashboardOverview.tsx`
- `frontend: src/components/dashboard/AttentionCard.tsx`
- `frontend: src/components/dashboard/VolunteerSummaryCard.tsx`
- `frontend: src/components/dashboard/ProfileHealthCard.tsx`
- `frontend: src/components/dashboard/UpcomingEventsCard.tsx`
- `frontend: src/components/dashboard/RecentActivityCard.tsx`

### Modify
- `frontend: src/App.tsx` (add route)
- `frontend: src/pages/nonprofit/MyOrgsPage.tsx` (add link)

---

## Timeline: ~2 hours
- Backend API: 30 min
- Frontend components: 60 min
- Testing & polish: 30 min

Ready to start? Begin with backend API.
