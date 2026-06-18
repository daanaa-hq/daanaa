# Firestore Setup Guide

This document describes the Firestore database configuration for Daanaa, including collections, security rules, and deployment steps.

## Project Information

- **Firebase Project**: daanaa-af9c2
- **Database**: (default)
- **Console**: https://console.firebase.google.com

## Collections Overview

Firestore uses the following collection structure:

### User-Scoped Collections

Each user's data is stored under `/{uid}/` in the following collections:

| Collection | Purpose | Fields |
|---|---|---|
| `saved_organizations` | Bookmarked nonprofits from directory | `ein`, `name`, `created_at` |
| `funded_log` | Giving history entries | `nonprofit_name`, `nonprofit_ein`, `amount`, `date`, `notes`, `created_at` |
| `volunteer_hour_logs` | Volunteer hours logged | `nonprofit_name`, `nonprofit_ein`, `service_date`, `hours_logged`, `notes`, `status`, `created_at` |
| `volunteer_hour_confirmations` | Status of submitted confirmations | `nonprofit_id`, `status`, `submitted_at` |
| `consent_records` | Privacy acknowledgments | `type`, `version`, `accepted_at` |
| `audit_logs` | Read-only audit trail (backend-written) | `action`, `timestamp`, `details` |

### Shared Collections

| Collection | Purpose | Structure |
|---|---|---|
| `nonprofit_verifications/{nonprofit_id}` | Hour verification records for a nonprofit | `volunteer_uid`, `hour_log_id`, `status`, `verified_at` |

## Security Rules

Firestore rules are defined in `/firestore.rules` and enforce:

- **User isolation**: Users can only read/write their own collections
- **Nonprofit access**: Nonprofit staff can verify hours for their organization
- **Backend writes**: Only the backend (admin SDK) can write audit logs
- **Read-only public data**: Some collections may be public (added later as needed)

### Deploying Rules

#### Option 1: Firebase Console (Manual)

1. Go to https://console.firebase.google.com
2. Select "daanaa-af9c2" project
3. Navigate to Firestore Database → Rules tab
4. Copy the rules from `firestore.rules`
5. Paste into the editor and click "Publish"

#### Option 2: Firebase CLI (Automated)

```bash
# Install Firebase CLI (one-time)
npm install -g firebase-tools

# Authenticate with Firebase
firebase login

# Deploy rules from this project
firebase deploy --only firestore:rules
```

### Verifying Rules are Deployed

You can test rules in the Firebase Console:

1. Click "Rules" tab
2. Click "Simulate" at the bottom
3. Enter test parameters:
   - Request type: `Get`
   - Document path: `{testuid}/saved_organizations/test_org`
   - Auth context: Add field `uid` = `testuid`
4. Click "Run"
5. Should see: **Allowed**

## Collection Auto-Creation

Firestore automatically creates collections when you first write to them. All collections above are created when:

- **Wallet collections**: User first logs in and saves data
- **Nonprofit verifications**: Nonprofit staff first verifies hours

There's no need to manually create collections.

## Firestore Quotas & Limits

- **Reads**: 50,000 per day (free tier)
- **Writes**: 20,000 per day (free tier)
- **Document size**: 1 MB max
- **Subcollections**: Unlimited

As of June 2026, wallet usage is minimal (~10 daily active users), well within free tier limits.

## Backend Integration

The Flask backend (`daanaa_api.py`) accesses Firestore via REST API:

- **Authentication**: Firebase ID token in `Authorization: Bearer` header
- **Functions**: `_firestore_get()`, `_firestore_set()`, `_firestore_list()`, `_firestore_delete()`
- **Path format**: `/{uid}/{collection}/{document}` for user data
- **Error handling**: All functions return None on 404, raise on auth failures

### Key Endpoints Using Firestore

| Endpoint | Collections Used | Purpose |
|---|---|---|
| `POST /api/wallet/save-org` | saved_organizations | Bookmark organization |
| `POST /api/wallet/log-funding` | funded_log | Log donation |
| `POST /api/wallet/log-hours` | volunteer_hour_logs | Log volunteer hours |
| `GET /api/nonprofit/hours-pending` | volunteer_hour_logs | List pending hours for nonprofit |
| `POST /api/nonprofit/verify-hours` | volunteer_hour_logs | Verify/reject hours |

## Monitoring & Maintenance

### Check Usage

In Firebase Console → Firestore Database → Usage tab, you can see:
- Document reads/writes per day
- Storage size

### Backup Strategy

Firestore automatic backups are enabled:
- Retention: 7 days
- Frequency: Hourly
- Manual export: via `gcloud firestore export` (see docs/BACKUP.md)

### Known Issues & Solutions

| Issue | Solution |
|---|---|
| "Blocked by firestore rules" error | Check that user is authenticated; verify rules allow the operation |
| Collections not appearing in Console | They auto-create on first write; manually write a test document if needed |
| Slow Firestore reads | Ensure you're using indexed queries; check cloud.google.com for automatic index creation |

## Related Documentation

- [WALLET-SETUP.md](WALLET-SETUP.md) - Wallet troubleshooting
- [PRIVACY-INVARIANTS.md](../PRIVACY-INVARIANTS.md) - Data privacy guarantees
- [daanaa_api.py](../daanaa_api.py) - Backend Firestore functions (lines ~127-210)

## Future Enhancements

- [ ] Enable Firestore in-app messaging for user notifications
- [ ] Add structured logging to audit_logs collection
- [ ] Implement full-text search on Firestore (currently using SQLite FTS)
- [ ] Add data retention policies (e.g., delete logs after 1 year)
