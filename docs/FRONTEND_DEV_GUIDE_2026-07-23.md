# Frontend Development Guide — Profile Contexts & Event Discovery

**Status:** ✅ API Ready (flags enabled locally)  
**Base URL:** `http://localhost:5000`  
**Auth:** Firebase ID token (required for all routes)  

---

## Starting the Dev Server

```bash
cd ~/meritgiving

# Enable feature flags
export ENABLE_PROFILE_CONTEXTS=true
export ENABLE_INTENT_SIGNALS=true
export ENABLE_EVENT_DISCOVERY=true

# Start API
source venv/bin/activate
python3 daanaa_api.py
# → Runs on http://localhost:5000
```

Frontend (separate terminal):
```bash
cd ~/meritgiving/frontend
npm run dev
# → Runs on http://localhost:5173
```

---

## API Endpoints — Profile Contexts

All endpoints require `Authorization: Bearer <firebase_id_token>` header.

### List User's Contexts
```
GET /api/profile-contexts

Response:
{
  "contexts": [
    {
      "context_id": "ctx_abc123...",
      "context_type": "household|daf|business|other",
      "status": "active",
      "created_by_uid": "user_123",
      "created_at": "2026-07-23T...",
      "role": "lead|support|member|viewer",
      "member_count": 3
    }
  ]
}
```

### Create New Context
```
POST /api/profile-contexts
Content-Type: application/json

{
  "context_type": "household"  // required: household|daf|business|other
}

Response: 201 Created
{
  "success": true,
  "context_id": "ctx_abc123...",
  "context": { ... }
}
```

### Get Context Members
```
GET /api/profile-contexts/{context_id}/members

Response:
{
  "members": [
    {
      "firebase_uid": "user_123",           // Lead sees raw UID
      "role": "lead|support|member|viewer",
      "status": "active",
      "joined_at": "2026-07-23T...",
      "created_at": "2026-07-23T..."
    },
    {
      "firebase_uid": "user_###",  // Non-lead sees masked UID
      "role": "member",
      "status": "active",
      "joined_at": "2026-07-23T...",
      "created_at": "2026-07-23T..."
    }
  ]
}
```

### Invite Member (Create Invitation)
```
POST /api/profile-contexts/{context_id}/members
Content-Type: application/json

{
  "firebase_uid": "user_456",              // required
  "role": "lead|support|member|viewer"     // default: "member"
}

Response: 201 Created
{
  "success": true,
  "invitation_id": "inv_abc123...",
  "invited_uid": "user_456",
  "role": "member"
}
```

### Get Pending Invitations
```
GET /api/profile-contexts/invitations/pending

Response:
{
  "invitations": [
    {
      "invitation_id": "inv_abc123...",
      "context_id": "ctx_xyz...",
      "role": "member",
      "context_type": "household",
      "invited_by_uid": "user_123",
      "created_at": "2026-07-23T...",
      "expires_at": "2026-08-06T..."  // 14 days
    }
  ]
}
```

### Accept Invitation
```
POST /api/profile-contexts/invitations/{invitation_id}/accept

Response: 200 OK
{
  "success": true,
  "invitation_id": "inv_abc123..."
}
```

### Reject Invitation
```
POST /api/profile-contexts/invitations/{invitation_id}/reject

Response: 200 OK
{
  "success": true,
  "invitation_id": "inv_abc123..."
}
```

### Update Member Role (Lead Only)
```
PATCH /api/profile-contexts/{context_id}/members/{firebase_uid}
Content-Type: application/json

{
  "role": "support|member|viewer"  // cannot demote lead
}

Response: 200 OK
{
  "success": true,
  "firebase_uid": "user_456",
  "role": "support"
}
```

### Remove Member (Lead/Support)
```
DELETE /api/profile-contexts/{context_id}/members/{firebase_uid}

Response: 200 OK
{
  "success": true,
  "firebase_uid": "user_456",
  "status": "removed"
}
```

### Archive Context (Lead Only)
```
POST /api/profile-contexts/{context_id}/archive

Response: 200 OK
{
  "success": true,
  "context_id": "ctx_abc123...",
  "status": "archived"
}
```

---

## Error Responses

**403 Forbidden** — Feature flag disabled or not authorized
```json
{ "error": "Profile contexts not enabled" }
{ "error": "Unauthorized (requires lead or support role)" }
```

**400 Bad Request** — Invalid input
```json
{ "error": "Invalid context_type. Must be one of: household, daf, business, other" }
{ "error": "Invalid role. Must be one of: lead, support, member, viewer" }
```

**404 Not Found** — Resource not found
```json
{ "error": "Submission not found" }
```

---

## Privacy & Security Notes

### UID Masking
- **Lead role** sees raw Firebase UIDs (e.g., `user_123abc...`)
- **Non-lead roles** see masked UIDs (e.g., `user_###`)
- Masking happens automatically in `get_context_members()`

### Invitation Expiry
- Invitations expire after 14 days
- Expired invitations return 400 Bad Request

### No PII Collection
- Schema deliberately has NO display_name, description, email lists, donation amounts, etc.
- Wallet data remains separate (not stored in profile_contexts)
- Each person keeps independent wallet even in shared contexts

### Role Hierarchy
- **Lead** (4): Full context control, can invite/remove anyone, can change roles
- **Support** (3): Can invite/remove members, cannot change roles or archive
- **Member** (2): View-only access to members, cannot invite or remove
- **Viewer** (1): Read-only, no management permissions

---

## Frontend Implementation Checklist

### Phase 1: Context Management
- [ ] Profile context selection at signup/login
- [ ] Create new context UI (household/DAF/business/other)
- [ ] List contexts (`GET /api/profile-contexts`)
- [ ] Display context members with role badges

### Phase 2: Invitation Flow
- [ ] Invite member form (email or Firebase UID)
- [ ] Pending invitations list (`GET /api/profile-contexts/invitations/pending`)
- [ ] Accept/reject invitation UI
- [ ] Show invitation expiry countdown (14 days)

### Phase 3: Member Management
- [ ] View context members with roles
- [ ] Change member role (PATCH, lead only)
- [ ] Remove member from context (DELETE, lead/support only)
- [ ] UID masking for non-lead users

### Phase 4: Admin Features
- [ ] Archive context (POST /archive, lead only)
- [ ] Unarchive context (future phase)
- [ ] Audit log of context changes (future phase)

---

## Testing Utilities

### Create Test Context (manual)
```bash
curl -X POST http://localhost:5000/api/profile-contexts \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"context_type":"household"}'
```

### List Contexts
```bash
curl http://localhost:5000/api/profile-contexts \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
```

### Get Firebase Token (dev)
```javascript
// In browser console on localhost:5173
const token = await auth.currentUser.getIdToken();
console.log(token);
```

---

## Debugging

### Enable Verbose Logging
```bash
export FLASK_DEBUG=1
export FLASK_ENV=development
python3 daanaa_api.py
```

### Check Database State
```bash
sqlite3 ~/meritgiving/data/merit_registry.db

# List all contexts
SELECT context_id, context_type, created_by_uid FROM profile_contexts;

# List all members
SELECT context_id, firebase_uid, role FROM profile_context_members;

# List pending invitations
SELECT invitation_id, context_id, invited_uid, role FROM profile_context_invitations WHERE status='pending';

# Intent signals
SELECT * FROM intent_signals ORDER BY created_at DESC LIMIT 10;
```

---

## Common Issues

**"Profile contexts not enabled"**
→ Did you set `ENABLE_PROFILE_CONTEXTS=true`? Restart API after setting flags.

**"Unauthorized (requires lead role)"**
→ Only the context creator (lead) can perform this operation. Check your role.

**"Invitation already pending"**
→ Can't invite the same user twice to the same context. They must reject first.

**"Email does not match"**
→ For volunteer hours flow, the email must match the invitation email.

---

## Next Steps

1. ✅ API ready (flags enabled)
2. → Build context selection UI at signup
3. → Build invitation accept/reject UI
4. → Build member management dashboard
5. → Wire volunteer hours approval workflow

Ready to code!
