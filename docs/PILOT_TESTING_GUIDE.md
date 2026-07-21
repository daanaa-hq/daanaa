# Nonprofit Leader Pilot — Testing Guide

This guide walks through testing the Daanaa nonprofit leader pilot signup and dashboard experience.

## Quick Start

### 1. Generate Test Invitations

Generate invitations for test organizations:

```bash
# Single invitation
python3 scripts/setup_pilot_invitations.py create 12-3456789 "My Test Org"

# Batch from CSV file
python3 scripts/setup_pilot_invitations.py create-batch pilot_test_orgs.csv
```

CSV format:
```csv
ein,organization_name,email
12-3456789,Test Nonprofit 1,contact@test1.org
98-7654321,Test Nonprofit 2,contact@test2.org
```

### 2. View Invitations

```bash
python3 scripts/setup_pilot_invitations.py list
```

This shows:
- All created invitations
- Status (pending/completed)
- Email open tracking
- Signup progress

### 3. Start Frontend Dev Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 4. Make API Calls (if API is running)

Restart the API:

```bash
source ~/meritgiving/venv/bin/activate
python3 daanaa_api.py
```

## Testing Flows

### Test 1: Invitation Link → Dashboard

**Objective:** Verify end-to-end signup flow

1. Generate a test invitation (get the link):
   ```bash
   python3 scripts/setup_pilot_invitations.py create 12-3456789 "Test Org"
   ```
   Note the `invite_link` URL.

2. Open the link in browser:
   ```
   http://localhost:5173/nonprofit/pilot-signup?code=<invite_code>
   ```

3. Expected behavior:
   - Page loads with organization name pre-filled
   - "What you'll get" section shows pilot benefits
   - User can enter email
   - Click "Get started" sends verification email

4. Check invitation status:
   ```bash
   python3 scripts/setup_pilot_invitations.py list
   ```
   Should show `email_opened: ✓` and `started: ✓`

### Test 2: Invalid Invite Code

**Objective:** Verify error handling

1. Try an invalid code:
   ```
   http://localhost:5173/nonprofit/pilot-signup?code=invalid-code-12345
   ```

2. Expected behavior:
   - Error page appears: "Invalid or expired invite code"
   - User can click to go back to /for-nonprofits

### Test 3: Missing Invite Code

**Objective:** Verify validation

1. Load without code:
   ```
   http://localhost:5173/nonprofit/pilot-signup
   ```

2. Expected behavior:
   - Error: "No invitation code provided"

## API Endpoints (for manual testing)

### Create Invitation (admin only)

```bash
curl -X POST http://localhost:5000/api/admin/pilot/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_KEY" \
  -d '{
    "ein": "12-3456789",
    "organization_name": "Test Org"
  }'
```

Response:
```json
{
  "id": "invitation-uuid",
  "ein": "12-3456789",
  "organization_name": "Test Org",
  "invite_code": "...",
  "invite_link": "...",
  "status": "pending"
}
```

### Verify Invite Code

```bash
curl -X POST http://localhost:5000/api/pilot/verify-invite \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invite-code-here"
  }'
```

Response:
```json
{
  "valid": true,
  "ein": "12-3456789",
  "organization_name": "Test Org",
  "invitation_id": "uuid"
}
```

### List Invitations (admin only)

```bash
curl -X GET http://localhost:5000/api/admin/pilot/invitations \
  -H "Authorization: Bearer YOUR_ADMIN_KEY"
```

Response includes stats and list of all invitations.

### Get Invitation Status

```bash
curl -X GET http://localhost:5000/api/pilot/signup-status/<invitation_id>
```

## Checklist for Full Pilot

When you're ready to send invitations to the 25 pilot organizations:

- [ ] Review `docs/pilot/invitation-draft-2026-07-13.md` for email copy
- [ ] Pick 25 organizations from `docs/pilot/pilot-candidates-2026-07-13.md`
- [ ] Create CSV file with their EINs and organization names
- [ ] Generate invitations:
  ```bash
  python3 scripts/setup_pilot_invitations.py create-batch pilot_25_orgs.csv
  ```
- [ ] Review invitation links and copy email addresses
- [ ] Send personalized emails from hello@daanaa.org with:
  - Org-specific highlight (hidden gem status, peer context, etc.)
  - Invitation link
  - Charter link and no-charge assurance
  - Call to action: "Reply to this email to get started"
- [ ] Track opens and engagement via `list` command
- [ ] Monitor signup completions
- [ ] Collect feedback on dashboard usability

## Test Data

### Example Test Organizations

```csv
ein,organization_name
52-1234567,Local Food Bank
61-2345678,Youth Mentoring Alliance
27-3456789,Community Arts Initiative
```

These are fictitious EINs for testing. Verify they exist in your local database before creating invitations.

## Troubleshooting

### "Organization not found in registry"

The EIN doesn't exist in the database. Check:
1. EIN is correctly formatted (XX-XXXXXXX)
2. EIN exists in `data/merit_registry.db`

```bash
sqlite3 data/merit_registry.db "SELECT organization_name FROM registry_enriched WHERE EIN = '12-3456789'"
```

### Frontend page shows "No authorization token"

The verify-invite API returned successfully but the frontend isn't storing the token. Check:
1. Browser console for errors
2. API is running and responding to `/api/pilot/verify-invite`
3. CORS headers are correct

### Emails not sending

Email integration is optional. The signup flow works without it (test endpoints manually).

## Development Notes

### File Structure

- **Backend:** `pilot_invitations_api.py` — invitation management
- **Frontend:** `frontend/src/pages/PilotSignup.tsx` — signup UI
- **Database:** Tables in `merit_registry.db`:
  - `pilot_invitations` — main invitations
  - `pilot_invite_tokens` — one-time signup tokens
- **Scripts:** `scripts/setup_pilot_invitations.py` — CLI management

### Key Flows

1. **Invitation Created** → invite code generated → link created
2. **User Clicks Link** → `PilotSignup` page loads → `/api/pilot/verify-invite` called
3. **Code Verified** → invitation marked as opened → org details shown
4. **User Enters Email** → `/api/claim/start` called → verification email sent
5. **User Verifies PIN** → account created → dashboard access unlocked

### Database Schema

```sql
CREATE TABLE pilot_invitations (
  id TEXT PRIMARY KEY,
  ein TEXT UNIQUE NOT NULL,
  organization_name TEXT NOT NULL,
  invite_code TEXT UNIQUE NOT NULL,
  invite_link TEXT,
  email_sent_to TEXT,
  status TEXT DEFAULT 'pending',
  email_opened BOOLEAN DEFAULT 0,
  signup_started BOOLEAN DEFAULT 0,
  signup_completed BOOLEAN DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Next Steps

After pilot signup testing:
1. Create admin dashboard to see pilot signup metrics
2. Build nonprofit self-discovery dashboard (showing peer context, etc.)
3. Set up feedback collection mechanism
4. Prepare 25-org pilot list with personalized highlights
