# Nonprofit Pilot — Quick Start for Testing

## Status

✅ **Backend API:** Pilot invitations infrastructure complete
✅ **Frontend:** Pilot signup page built and tested
✅ **Testing Guide:** Full documentation available
⏳ **Ready for testing:** Yes

## 1-Minute Setup

```bash
# Activate environment
source ~/meritgiving/venv/bin/activate

# Start API (one terminal)
python3 daanaa_api.py

# Start frontend (another terminal)
cd frontend && npm run dev

# Generate a test invitation (third terminal)
python3 scripts/setup_pilot_invitations.py create 52-1234567 "Test Nonprofit"
```

You'll see output like:
```
✓ Invitation created for Test Nonprofit
  EIN: 52-1234567
  Invite code: <code_here>
  Link: http://daanaa.org/nonprofit/pilot-signup?code=<code_here>
```

## Test the Flow

1. Open the invitation link in a browser (use `http://localhost:5173` if testing locally)
2. You should see:
   - Organization name pre-filled
   - "What you'll get" section
   - Email input field
3. Enter your email and click "Get started"
4. You'll see a confirmation: "Check your email"

## Check Invitation Status

```bash
python3 scripts/setup_pilot_invitations.py list
```

Shows:
- All invitations created
- Which ones had email opened
- Which ones started signup
- Which ones completed signup

## Full Testing Guide

See `docs/PILOT_TESTING_GUIDE.md` for:
- API endpoint documentation
- Batch invitation creation
- Admin dashboard access
- Troubleshooting
- Development notes

## Database Schema

Tables created automatically:
- `pilot_invitations` — main invitation records
- `pilot_invite_tokens` — (optional) one-time tokens

## Files Created/Modified

### New Files:
- `pilot_invitations_api.py` — Backend API module
- `frontend/src/pages/PilotSignup.tsx` — Frontend signup page
- `scripts/setup_pilot_invitations.py` — CLI for managing invitations
- `docs/PILOT_TESTING_GUIDE.md` — Comprehensive testing documentation
- `docs/PILOT_QUICK_START.md` — This file

### Modified Files:
- `daanaa_api.py` — Added pilot invitations blueprint registration
- `frontend/src/App.tsx` — Added PilotSignup route

## Key Features

✅ Invite code verification
✅ Organization lookup (from registry)
✅ Pre-filled org info
✅ Email collection
✅ Signup tracking (opened, started, completed)
✅ Admin list endpoint
✅ Admin creation endpoint
✅ Batch CSV import

## Next Steps

1. **Test with local data:** Use the quick setup above
2. **Test with real orgs:** Pick 25 from `docs/pilot/pilot-candidates-2026-07-13.md`
3. **Create personalized emails:** Use template in `docs/pilot/invitation-draft-2026-07-13.md`
4. **Send invitations:** Once you're satisfied with the flow
5. **Monitor dashboard:** Track opens, signups, and completions

## Environment Variables

Optional:
- `DAANAA_ADMIN_KEY` — Required for admin endpoints (e.g., create, list invitations)
- `DAANAA_FRONTEND_URL` — Frontend URL for invitation links (default: https://daanaa.org)
- `DB_PATH` — Database path (default: data/merit_registry.db)

## Monitoring

While invitations are active, run:

```bash
# Check status every 30 minutes
watch -n 1800 'python3 scripts/setup_pilot_invitations.py list'
```

## Questions?

Refer to:
- `docs/PILOT_TESTING_GUIDE.md` — Detailed testing
- `pilot_invitations_api.py` — Code documentation
- `frontend/src/pages/PilotSignup.tsx` — Frontend logic
