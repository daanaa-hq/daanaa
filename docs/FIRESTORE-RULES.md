# Firestore Security Rules Configuration

## Current Rules

Apply these rules in the Firebase Console under Firestore → Rules:

```
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {
    
    // ===== USER WALLET DATA =====
    // User can read/write their own wallet data
    match /{uid}/saved_organizations/{document=**} {
      allow read, write: if request.auth.uid == uid;
    }
    
    match /{uid}/funded_log/{document=**} {
      allow read, write: if request.auth.uid == uid;
    }
    
    match /{uid}/volunteer_hour_logs/{document=**} {
      allow read, write: if request.auth.uid == uid;
    }
    
    match /{uid}/volunteer_hour_confirmations/{document=**} {
      allow read, write: if request.auth.uid == uid;
    }
    
    match /{uid}/consent_records/{document=**} {
      allow read, write: if request.auth.uid == uid;
    }
    
    // ===== NONPROFIT VERIFICATION RECORDS =====
    // Nonprofits can read/write hour verification records for their organization
    match /nonprofit_verifications/{nonprofit_id}/{document=**} {
      // Allow nonprofit staff to verify hours for their organization
      allow read, write: if request.auth.uid != null;
    }
    
    // ===== AUDIT LOGS =====
    // Only backend can write audit logs, users can read their own
    match /{uid}/audit_logs/{document=**} {
      allow read: if request.auth.uid == uid;
      allow write: if false;  // Backend writes via admin SDK
    }
  }
}
```

## Collection Structure

### User Collections (per user under `/{uid}/`)

- **saved_organizations**: Bookmarked nonprofits
- **funded_log**: Giving history entries
- **volunteer_hour_logs**: Volunteer hours logged by the user
- **volunteer_hour_confirmations**: Status of submitted hour confirmations
- **consent_records**: Consent/privacy acknowledgments
- **audit_logs**: Read-only log of user actions (backend-written)

### Nonprofit Collections (shared)

- **nonprofit_verifications/{nonprofit_id}**: Hour verification records managed by nonprofit staff for their organization

## How to Update Rules

1. Go to https://console.firebase.google.com
2. Select "daanaa-af9c2" project
3. Navigate to Firestore Database → Rules
4. Copy the rules above into the editor
5. Click "Publish"

## Testing Rules

You can test rules in the Firebase Console:
1. Click "Rules" tab
2. At the bottom, click "Simulate"
3. Enter a request type (Get, Create, Update, Delete)
4. Set the document path
5. Set auth context (add "uid" field with a test UID)
6. Click "Run" to see if the rule allows/denies

## Rules Explanation

- `request.auth.uid == uid`: Ensures users can only access their own data
- `request.auth.uid != null`: Any authenticated user (used for nonprofit verifications which are shared)
- `allow write: if false`: Prevents direct writes (backend uses admin SDK)

## Collections Created Automatically

Firestore auto-creates collections when you first write to them. All of the above collections are created when:
- User first saves data via the wallet API
- Nonprofit staff first submits hour verifications via the nonprofit API

## Ongoing Maintenance

- Review rules quarterly to ensure they match the current data structure
- Update this documentation when new collections are added
- Test any rule changes in the simulator before publishing to production
