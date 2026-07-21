# Nonprofit Pilot Signup Environment — Implementation Summary

**Date:** 2026-07-21  
**Status:** ✅ Ready for testing  
**Monitoring:** Active (discovery daemon + mission batch)

## What's Been Built

A complete invitation-based signup environment for the 25-organization pilot, with:

### Backend Infrastructure (`pilot_invitations_api.py`)
- Invitation creation with unique invite codes
- Invite code verification
- Signup progress tracking (opened → started → completed)
- Admin endpoints for creating and listing invitations
- Database tables: `pilot_invitations` and `pilot_invite_tokens`

### Frontend Signup Page (`PilotSignup.tsx`)
- Invite code verification from URL parameter
- Organization details pre-filled from registry
- Pilot benefits explained ("What you'll get")
- Email collection
- Integration with existing `/api/claim/start` flow
- Error handling for invalid codes

### CLI Management Tool (`setup_pilot_invitations.py`)
- Create single invitations: `python3 scripts/setup_pilot_invitations.py create <EIN> [name]`
- List all invitations with stats: `python3 scripts/setup_pilot_invitations.py list`
- Batch import from CSV: `python3 scripts/setup_pilot_invitations.py create-batch file.csv`

### Documentation
- **PILOT_QUICK_START.md** — 1-minute setup guide
- **PILOT_TESTING_GUIDE.md** — Comprehensive testing with API docs
- **This file** — Implementation summary

## Testing Checklist

- [ ] Start API: `python3 daanaa_api.py`
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Create test invitation: `python3 scripts/setup_pilot_invitations.py create 52-1234567 "Test Org"`
- [ ] Open invitation link in browser
- [ ] Verify invite code acceptance
- [ ] Fill email and submit
- [ ] Check status: `python3 scripts/setup_pilot_invitations.py list`

## Key Design Decisions

### Security
- Invite codes are 24-byte URL-safe strings (~180-bit entropy)
- Admin endpoints require `DAANAA_ADMIN_KEY` header
- One-click links (not multi-step) for minimal friction

### Privacy (per STEWARDSHIP.md)
- No unsolicited email until the founder manually sends
- Invitation list is admin-only
- Signup data collected only with explicit action

### Usability
- Pre-filled org info from registry (no manual lookup)
- Clear benefits statement ("What you'll get")
- Single email field + existing claim flow (no new verification needed)
- Error messages are specific and actionable

## Database Changes

Two new tables (created automatically on first invitation):

```sql
pilot_invitations (
  id, ein, organization_name, invite_code, invite_link,
  email_sent_to, status, email_opened, signup_started,
  signup_completed, created_at, updated_at
)

pilot_invite_tokens (
  id, pilot_invitation_id, token, expires_at,
  used, used_at, used_by_account_id, created_at
)
```

## Deployment Notes

### Local Testing
No additional setup needed. Uses existing database and API.

### Staging/Production
When deploying to droplet:
1. Tables are created automatically (safe to run on existing DB)
2. Admin endpoints require `DAANAA_ADMIN_KEY` env var
3. Invitation links use `DAANAA_FRONTEND_URL` env var

## Integration Points

### With Existing Flow
- Verify invite → pre-fill EIN → `/api/claim/start` → PIN verification → dashboard access
- Invitation tracking happens in new tables, not disrupting existing claims flow

### With Stewardship Commitment
- ✅ P2 (Privacy): No tracking without consent
- ✅ P3 (Evidence-based): Invitations are data-driven (org selection is founder's choice)
- ✅ P5 (Honest communication): Benefits statement is clear and non-pressure
- ✅ P7 (Independence): No curation, pure invitation list

## Files Changed/Created

### New Files
- `pilot_invitations_api.py` (411 lines)
- `frontend/src/pages/PilotSignup.tsx` (225 lines)
- `scripts/setup_pilot_invitations.py` (265 lines)
- `docs/PILOT_QUICK_START.md`
- `docs/PILOT_TESTING_GUIDE.md`

### Modified Files
- `daanaa_api.py` (+4 lines for blueprint registration)
- `frontend/src/App.tsx` (+2 lines for import/route)

## What Still Needs to Be Done

### For Live Pilot (not blocking testing)
1. **25-org selection** — Pick organizations from `docs/pilot/pilot-candidates-2026-07-13.md`
2. **Personalized email copy** — Use template in `docs/pilot/invitation-draft-2026-07-13.md`
3. **Manual email send** — Send from hello@daanaa.org with org-specific highlight
4. **Feedback collection** — Set up mechanism for pilot responses (currently: reply to email)

### Optional Enhancements
1. Admin dashboard for viewing signup metrics
2. Automated email sending (currently founder sends manually)
3. Invitation expiration (currently: no expiration)
4. Nonprofit self-discovery dashboard completion

## Monitoring

Background task monitoring is active:
- Discovery daemon: 400+ orgs/30min, 507 links/hour
- Mission batch: Qwen3 30B A3B running (23,359 orgs)
- Monitoring scheduled every 30 minutes

## Next Session

When you return to this project:
1. Check `docs/PILOT_QUICK_START.md` to test
2. If testing passes, pick 25 orgs from `docs/pilot/pilot-candidates-2026-07-13.md`
3. Create batch invitations: `python3 scripts/setup_pilot_invitations.py create-batch pilot_25.csv`
4. Send personalized emails with invitation links
5. Monitor signup progress: `python3 scripts/setup_pilot_invitations.py list`

## Technical Questions?

- **Backend logic:** See `pilot_invitations_api.py` docstrings
- **Frontend flow:** See `frontend/src/pages/PilotSignup.tsx` comments
- **Testing:** See `docs/PILOT_TESTING_GUIDE.md`
- **API endpoints:** See `pilot_invitations_api.py` routes

---

Ready to test when you are. Monitoring loop will keep watch on background tasks.
