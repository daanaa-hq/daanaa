# Frontend Dev Quickstart — Profile Contexts

**Status:** ✅ API Ready Now  
**All flags enabled locally**

---

## Start the Backend

```bash
cd ~/meritgiving
export ENABLE_PROFILE_CONTEXTS=true
export ENABLE_INTENT_SIGNALS=true
export ENABLE_EVENT_DISCOVERY=true
source venv/bin/activate
python3 daanaa_api.py
```

API runs on `http://localhost:5000`

---

## Start the Frontend

```bash
cd ~/meritgiving/frontend
npm install  # first time only
npm run dev
```

Dev server on `http://localhost:5173`

---

## Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/profile-contexts` | List user's contexts |
| POST | `/api/profile-contexts` | Create new context |
| GET | `/api/profile-contexts/{id}/members` | List members |
| POST | `/api/profile-contexts/{id}/members` | Invite member |
| GET | `/api/profile-contexts/invitations/pending` | List pending invites |
| POST | `/api/profile-contexts/invitations/{id}/accept` | Accept invite |
| POST | `/api/profile-contexts/invitations/{id}/reject` | Reject invite |

**All require:** `Authorization: Bearer <firebase_token>`

---

## Full Reference

See `docs/FRONTEND_DEV_GUIDE_2026-07-23.md` for:
- Complete endpoint documentation
- Error responses
- Privacy/security notes
- Implementation checklist
- Debugging tips

---

## What's Working

✅ Profile context management (create, list, members)  
✅ Invitation workflow (invite, accept, reject)  
✅ Role-based access (lead/support/member/viewer)  
✅ UID masking (non-leads see masked UIDs)  
✅ Intent signal tracking (volunteer workflow)  
✅ Event discovery queue  

---

## Build These UI Components

1. **Context selector** — Show household/DAF/business/other options
2. **Member list** — Display members with roles
3. **Invite form** — Invite new members to context
4. **Pending invites** — Accept/reject invite UI
5. **Member management** — Change roles, remove members (lead only)

---

## Next Steps

1. ✅ Read `docs/FRONTEND_DEV_GUIDE_2026-07-23.md`
2. Build context selection UI
3. Build invitation accept/reject flow
4. Wire member management dashboard
5. Test end-to-end with real Firebase auth

Go!
