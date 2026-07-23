# Daanaa Profile Contexts — Shared Household & Entity Management

**Date:** 2026-07-23
**Status:** Ready for local testing (feature-flagged, no deployment)
**Feature Flag:** `ENABLE_PROFILE_CONTEXTS=false` (default)

---

## Overview

Daanaa Profile Contexts enables one person to have one private profile while optionally participating in shared contexts (household, DAF, business, other) with role-based access control.

**Core Principle:** One person = one permanent, independent profile (Firebase UID). Joining a shared context does NOT merge profiles, wallets, volunteer records, or activity history.

---

## Architecture

### Database Schema

**`profile_contexts`** — Shared contexts
```sql
CREATE TABLE profile_contexts (
  context_id      TEXT PRIMARY KEY,          -- ctx_{random_hex}
  context_type    TEXT NOT NULL,              -- household|daf|business|other
  created_by_uid  TEXT NOT NULL,              -- Creator's Firebase UID
  status          TEXT DEFAULT 'active',      -- active|archived|deleted
  display_name    TEXT,                       -- "Smith Family", "My DAF", etc.
  description     TEXT,                       -- Optional context description
  created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_profile_contexts_created_by ON profile_contexts(created_by_uid);
```

**`profile_context_members`** — Role-based membership
```sql
CREATE TABLE profile_context_members (
  context_id      TEXT NOT NULL,
  firebase_uid    TEXT NOT NULL,
  role            TEXT NOT NULL,              -- lead|support|member|viewer
  status          TEXT DEFAULT 'active',      -- active|invited|removed|declined
  invited_by_uid  TEXT,                       -- Who invited this member
  joined_at       TEXT,                       -- When they joined
  created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (context_id, firebase_uid),
  FOREIGN KEY (context_id) REFERENCES profile_contexts(context_id)
);

CREATE INDEX idx_profile_context_members_uid ON profile_context_members(firebase_uid);
CREATE INDEX idx_profile_context_members_status ON profile_context_members(context_id, status);
```

### Permission Roles

| Role | Can Add Members | Can Remove Members | Can Change Roles | Can Archive | Can View |
|------|---|---|---|---|---|
| **Lead** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Support** | ✓ | ✓ | ✗ | ✗ | ✓ |
| **Member** | ✗ | ✗ | ✗ | ✗ | ✓ |
| **Viewer** | ✗ | ✗ | ✗ | ✗ | ✓ |

**Creator is automatically Lead.**

### Context Types

- **household** — Household coordination (spouse, family members)
- **daf** — Donor-advised fund or foundation giving
- **business** — Corporate/business giving (CSR, employee giving)
- **other** — User-defined context

---

## API Endpoints

### List user's contexts

```
GET /api/profile-contexts

Response:
{
  "contexts": [
    {
      "context_id": "ctx_abc123...",
      "context_type": "household",
      "display_name": "Smith Family",
      "description": "...",
      "status": "active",
      "created_by_uid": "user_1",
      "created_at": "2026-07-23T...",
      "role": "lead",
      "member_status": "active",
      "joined_at": "2026-07-23T...",
      "member_count": 3
    }
  ]
}
```

### Create a new context

```
POST /api/profile-contexts
Content-Type: application/json

{
  "context_type": "household",
  "display_name": "Smith Family",
  "description": "Optional description"
}

Response: 201 Created
{
  "success": true,
  "context_id": "ctx_abc123...",
  "context": { ... }
}
```

### Get context members

```
GET /api/profile-contexts/<context_id>/members

Response: 200
{
  "members": [
    {
      "firebase_uid": "user_1",
      "role": "lead",
      "status": "active",
      "joined_at": "2026-07-23T...",
      "created_at": "2026-07-23T..."
    }
  ]
}
```

### Add member to context

```
POST /api/profile-contexts/<context_id>/members
Content-Type: application/json

{
  "firebase_uid": "user_2",
  "role": "member"  // lead|support|member|viewer
}

Response: 201 Created
{
  "success": true,
  "firebase_uid": "user_2",
  "role": "member"
}
```

### Update member role

```
PATCH /api/profile-contexts/<context_id>/members/<firebase_uid>
Content-Type: application/json

{
  "role": "support"
}

Response: 200
{
  "success": true,
  "firebase_uid": "user_2",
  "role": "support"
}
```

### Remove member from context

```
DELETE /api/profile-contexts/<context_id>/members/<firebase_uid>

Response: 200
{
  "success": true,
  "firebase_uid": "user_2",
  "status": "removed"
}
```

### Archive a context

```
POST /api/profile-contexts/<context_id>/archive

Response: 200
{
  "success": true,
  "context_id": "ctx_abc123...",
  "status": "archived"
}
```

---

## Security & Authorization

### Authentication
- All endpoints require Firebase authentication (`_require_firebase_user()`)
- User identity derived from verified Firebase token
- **Never trust client-supplied UID** — derived from token only

### Authorization
- **Membership check:** User must be a member of the context to access it
- **Role-based access:** Operations gated by user's role (lead/support/member/viewer)
- **Cannot access other contexts:** Cross-context isolation enforced
- **Cannot self-remove:** Lead must transfer lead role before removal

### Rate Limiting
- `GET /api/profile-contexts`: 60 per minute
- `POST /api/profile-contexts`: 10 per minute
- Member management: 10 per minute per endpoint

---

## Privacy & Data Protection

### No PII Collection
The schema **deliberately does not collect**:
- Tax returns, Form 990s
- Tax IDs, SSNs, EINs
- Donation amounts, receipt details
- Email or phone lists for invitations
- Household income or household member relationships
- Donation history or giving records

### Wallet Privacy
- Wallet data **never stored** in profile_contexts schema
- Wallet contents **never exposed** to other context members
- Each person retains **independent wallet** regardless of context membership
- Sharing wallet items requires explicit user action (future phase)

### Independent Profiles
- Joining a context does **not merge** profiles
- Each person keeps **separate volunteer records**, **activity history**, **personal giving intent**
- Lead role does **not grant access** to member's personal wallet or profile data

---

## Feature Flag

```bash
# Disabled by default
ENABLE_PROFILE_CONTEXTS=false

# Enable in dev/test
ENABLE_PROFILE_CONTEXTS=true python3 daanaa_api.py
```

---

## QA Results

All 14 security and authorization tests pass ✓

```
test_one_uid_one_profile                 ✓
test_create_all_context_types            ✓
test_invalid_context_type_rejected       ✓
test_creator_is_lead                     ✓
test_all_roles_supported                 ✓
test_profiles_not_merged_on_join         ✓
test_wallet_fields_not_in_schema         ✓
test_no_pii_fields                       ✓
test_member_cannot_add_members           ✓
test_only_lead_can_change_roles          ✓
test_lead_can_remove_member              ✓
test_cannot_self_remove                  ✓
test_lead_can_archive_context            ✓
test_cannot_access_other_context         ✓
```

**Test Coverage:**
1. ✓ One person = one profile (Firebase UID)
2. ✓ Shared contexts (household, DAF, business, other)
3. ✓ Permission roles (Lead, Support, Member, Viewer)
4. ✓ Independent access (no profile merging)
5. ✓ Wallet privacy (never exposed in schema)
6. ✓ No PII collection (tax docs, IDs, amounts, etc.)
7. ✓ Role-based access control (enforced)
8. ✓ Member removal (with safeguards)
9. ✓ Context archival (lead-only)
10. ✓ Cross-context isolation (no unauthorized access)

---

## Core Functions (scripts/profile_contexts.py)

### Schema & Setup
- `ensure_schema(db)` — Create tables and indexes

### Context Management
- `create_context(db, created_by_uid, context_type, display_name, description)` → context_id
- `get_context_detail(db, context_id)` → dict
- `get_user_contexts(db, firebase_uid)` → list[dict]
- `archive_context(db, context_id, archived_by_uid)` → None

### Membership Management
- `add_member(db, context_id, firebase_uid, role, invited_by_uid)` → None
- `update_member_role(db, context_id, firebase_uid, new_role, changed_by_uid)` → None
- `remove_member(db, context_id, firebase_uid, removed_by_uid)` → None
- `get_context_members(db, context_id)` → list[dict]

### Authorization
- `can_access_context(db, context_id, firebase_uid, min_role='member')` → bool

---

## Deployment Checklist

**Before production deployment:**

1. ✓ Feature flag OFF by default (`ENABLE_PROFILE_CONTEXTS=false`)
2. ✓ All tests pass (14/14)
3. ✓ No PII fields in schema
4. ✓ Role-based access enforced
5. ✓ Cross-context isolation enforced
6. ✓ Authentication: Firebase token required
7. ✓ Authorization: Membership + role checks on every endpoint
8. ✓ Rate limiting: 10-60 per minute
9. ✓ Error handling: No sensitive data in error responses
10. Run privacy check: `bash scripts/privacy_check.sh`
11. Frontend NOT modified (blocked until review + approval)
12. Database: No migrations (additive only)
13. Founder approval obtained

---

## Integration with Existing Features

### Wallet (Independent)
- Wallets remain private to individual profiles
- Wallet data **not stored** in profile_contexts
- Sharing wallet items requires explicit user action (future phase)

### Volunteer Hours (Independent)
- Each volunteer record tied to individual Firebase UID
- Hours submitted in personal profile remain independent
- Shared context provides **coordination**, not data merging

### Giving Intent (Independent)
- Personal giving intent (Giving Wallet) stays in personal profile
- Context members can coordinate but don't share giving history
- Household giving flow (future phase) will be opt-in

---

## Signup Flow

Frontend asks: **"How would you like to organize your Daanaa activity?"**

Options:
- Just me
- Household coordination
- DAF or foundation
- Business or corporate
- Other

User selection determines initial context creation. Can add more contexts anytime via `/api/profile-contexts`.

---

## Known Limitations & Future Work

**Phase 1 (Current):** Basic shared contexts with role-based access
- ✓ Create contexts
- ✓ Add/remove members
- ✓ Role management
- ✓ Cross-context isolation
- ✓ Archival

**Phase 2 (Future):** Household coordination workflows
- Shared giving decisions (with audit trail)
- Approval workflows for giving
- Household impact dashboard (aggregate only)

**Phase 3 (Future):** DAF + business tax coordination
- DAF grant recommendation flows
- Business giving strategies
- Tax receipt coordination (external service)

---

## Stewardship Alignment

✓ **P1 (Mission before growth)** — Contexts enable better coordination without tracking
✓ **P2 (Privacy is structural)** — No wallet/PII in schema; wallet stays independent
✓ **P3 (Evidence-based)** — Membership explicit and auditable
✓ **P7 (Independence protected)** — No partner influence on context creation or membership
✓ **P8 (No fund control)** — Daanaa records intent; funds flow through org/DAF/bank

---

**Status:** Ready for local testing. Deployment blocked until event-claiming system stabilizes + founder approval obtained.

Files:
- `scripts/profile_contexts.py` — Core logic (290+ lines)
- `daanaa_api.py` — REST endpoints (200+ lines added)
- `tests/test_profile_contexts.py` — 14 comprehensive tests
- `docs/PROFILE_CONTEXTS_2026-07-23.md` — This document
