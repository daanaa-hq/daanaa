# AKF Event Platform MVP — Build Manifest
**Date:** 2026-07-22  
**Status:** Framework Complete, Ready for Testing  
**Deadline:** 2026-09-21 (9 weeks)  
**Owner:** Akbar Khowaja

---

## Summary

The **AKF Golf Tournament Event Platform** MVP has been built and is ready for integration testing. The system enables volunteer registration, hour logging, real-time dashboards, and approval workflows.

## What's Been Built

### 1. **Database** ✓
- **Migration:** `database/migrations/027_event_volunteer_platform.sql`
- **Tables:**
  - `events` — Event metadata (name, date, organizer, donation_url)
  - `event_volunteers` — Volunteer registrations
  - `volunteer_hours` — Hour submissions (pending/approved)
  - `event_teams` — Team organization (foursomes for golf)
  - `event_stats` — Cached dashboard metrics
  - `event_audit_log` — Compliance audit trail

### 2. **Backend API** ✓
- **File:** `event_platform_api.py` (462 lines)
- **Endpoints:**
  - `POST /api/events` — Create event (organizer)
  - `GET /api/events/<id>` — Get event details
  - `PUT /api/events/<id>` — Update event (organizer only)
  - `POST /api/events/<id>/volunteers` — Register volunteer
  - `GET /api/events/<id>/volunteers` — List volunteers
  - `POST /api/events/<id>/hours` — Log hours
  - `POST /api/events/<id>/hours/<hour_id>/approve` — Approve hours (organizer)
  - `GET /api/events/<id>/dashboard` — Real-time stats
  - `GET /api/events/<id>/report` — Post-event report
- **Registration:** Added to `daanaa_api.py` at line 1795

### 3. **Frontend Pages** ✓
- **EventDetails.tsx** — Event info + donation link + action buttons
- **EventDashboard.tsx** — Real-time stats (volunteer count, total hours, check-ins)
- **VolunteerRegistration.tsx** — Sign up form (name, email, role, phone)
- **LogVolunteerHours.tsx** — Hour logging form (date, hours, job type, notes)
- **VolunteerApprovalDashboard.tsx** — Organizer dashboard (volunteer list + pending approvals)
- **Routing:** All pages added to `frontend/src/App.tsx`

### 4. **Authentication** ✓
- Firebase UID extracted from `Authorization: Bearer <token>` header
- Owner-only endpoints require auth (event update, hour approval)
- Public endpoints accessible without auth (event details, registration, logging)

---

## What's NOT in This Build (Scope Decisions)

| Feature | Reason | Future |
|---------|--------|--------|
| Email notifications | Out of scope for 9/21 | Phase 2 |
| Payment processing | Daanaa is hand-off layer | Phase 2 |
| Advanced team management | Golf foursomes are simplified | Phase 2 |
| Mobile app | Web-first MVP | Q4 2026 |
| Analytics/reports | Basic report API only | Phase 2 |
| Multi-event batch operations | Single event per org | Phase 2 |

---

## Integration Checklist

### Pre-Deployment
- [ ] Run migration on staging database
- [ ] Test API endpoints with Postman/curl
- [ ] Test all frontend pages (volunteer registration → hour logging → approval)
- [ ] Verify Firebase auth token handling
- [ ] Check donation URL integration (point to AKF Funraisin URL)
- [ ] Verify stewardship compliance (no PII leakage, audit logging works)

### Staging Deploy (by 2026-08-31)
- [ ] Migrate database
- [ ] Deploy `event_platform_api.py` to production API
- [ ] Build frontend (`npm run build`)
- [ ] Deploy to droplet
- [ ] Run smoke test: create event → register volunteer → log hours → approve
- [ ] Verify dashboard updates in real-time

### User Testing with AKF (by 2026-09-14)
- [ ] Create sample AKF Golf Tournament event
- [ ] Invite 5-10 volunteers to register
- [ ] Have volunteers submit sample hour entries
- [ ] Test approval workflow
- [ ] Gather feedback on UI/UX

### Launch (2026-09-21)
- [ ] Go live with real AKF Golf Tournament
- [ ] Monitor for errors (check logs, Sentry)
- [ ] Support volunteer onboarding via email/phone

---

## API Contract (for Outreach)

### Create Event
```bash
curl -X POST http://daanaa.org/api/events \
  -H "Authorization: Bearer $FIREBASE_UID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AKF Golf Tournament 2026",
    "event_date": "2026-09-21",
    "organizer_name": "Akbar Khowaja",
    "description": "Annual golf charity event",
    "donation_url": "https://fundraise.funraisin.com/akf-golf-2026"
  }'
```

### Register Volunteer
```bash
curl -X POST http://daanaa.org/api/events/evt_abc123/volunteers \
  -H "Content-Type: application/json" \
  -d '{
    "volunteer_name": "John Doe",
    "volunteer_email": "john@example.com",
    "role": "Setup",
    "phone": "(555) 123-4567"
  }'
```

### Log Hours
```bash
curl -X POST http://daanaa.org/api/events/evt_abc123/hours \
  -H "Content-Type: application/json" \
  -d '{
    "volunteer_id": "vol_xyz789",
    "hours": 4.5,
    "service_date": "2026-09-21",
    "job_description": "Setup",
    "notes": "Helped set up registration tables"
  }'
```

### Approve Hours (Organizer)
```bash
curl -X POST http://daanaa.org/api/events/evt_abc123/hours/hrs_xyz/approve \
  -H "Authorization: Bearer $ORGANIZER_UID" \
  -H "Content-Type: application/json"
```

---

## Known Limitations

1. **No Email Notifications** — Volunteers won't get automated email confirmations. Send manually via outreach.
2. **Single-Event Focus** — One event per organizer at a time. For future seasons, archive old events.
3. **No Team Auto-Sync** — Golf foursomes must be managed post-hoc (not UI-driven).
4. **No Duplicate Prevention on Frontend** — Volunteer can register twice for same event if they try. Backend prevents via UNIQUE constraint.
5. **No Time-Zone Handling** — All times assume Central Time (server TZ). Document this for AKF.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Database** | SQLite (merit_registry.db) |
| **Backend** | Flask + Python 3.11 |
| **Frontend** | React 19 + TypeScript + Vite |
| **Auth** | Firebase (token in header) |
| **Styling** | Tailwind CSS + shadcn/ui |
| **Deployment** | Droplet (Nginx reverse proxy) |

---

## File References

| File | Purpose | Lines |
|------|---------|-------|
| `database/migrations/027_event_volunteer_platform.sql` | Database schema | 169 |
| `event_platform_api.py` | Flask API blueprint | 462 |
| `frontend/src/pages/event/EventDetails.tsx` | Event info page | 100 |
| `frontend/src/pages/event/EventDashboard.tsx` | Real-time dashboard | 115 |
| `frontend/src/pages/event/VolunteerRegistration.tsx` | Registration form | 120 |
| `frontend/src/pages/event/LogVolunteerHours.tsx` | Hour logging form | 180 |
| `frontend/src/pages/event/VolunteerApprovalDashboard.tsx` | Organizer dashboard | 160 |
| `daanaa_api.py` | Main Flask app (updated at line 1795) | ~11K |
| `frontend/src/App.tsx` | React router (updated at line 76–78 + routes) | ~200 |

---

## Next Steps

1. **Run the migration**: `sqlite3 data/merit_registry.db < database/migrations/027_event_volunteer_platform.sql`
2. **Restart the API**: `./restart_api.sh`
3. **Rebuild frontend**: `cd frontend && npm run build`
4. **Deploy to staging**: `./scripts/ops/sync_droplet_api.sh`
5. **Test with sample data**: Create a test event at `http://daanaa.org/event/evt_test`

---

## Stewardship Compliance

✅ **Principle #1 (Mission):** No paid placement, pure volunteer coordination  
✅ **Principle #2 (Privacy):** No tracking of volunteers beyond event participation  
✅ **Principle #3 (Evidence):** Hours are user-submitted, verified by organizer  
✅ **Principle #6 (Mistakes):** Audit log captures all actions for correction  
✅ **Principle #10 (Human in Command):** Organizer manually approves all hours  

---

## Questions for Akbar

Before launch, confirm:

1. **Donation URL:** What's the AKF Funraisin URL for 2026-09-21 event?
2. **Email Handling:** How should volunteers be notified (email list / Mailchimp / manual)?
3. **Team Structure:** Are foursomes pre-assigned, or should volunteers self-organize?
4. **Hour Approval Process:** Should organizer batch-approve at end of day, or per-submission?
5. **Reporting:** Want detailed volunteer list exported post-event (CSV)?

---

**Built by:** Claude Code (AI Engineering Agent)  
**Ready for:** Integration testing & user validation  
**Last Updated:** 2026-07-22 23:00 UTC
