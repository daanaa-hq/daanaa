# Impact Wallet Setup & Troubleshooting

## Current Implementation

### Preview Mode ✅
- Users can visit `/wallet` without authentication
- All forms are visible and functional in preview state
- Data is NOT saved until user authenticates with Google
- Clear banner explains preview mode and prompts sign-in

### Privacy Disclosures ✅
- Banner shows privacy commitment when authenticated
- Explains data is never shared with third parties
- Clarifies giving history and volunteering records stay private

### Features
- **Funding History**: Log gifts with nonprofit name, EIN, amount, date
- **Volunteer Hours**: Log with organization search/autocomplete
- **Saved Organizations**: Bookmark nonprofits from directory
- **Funding Impact**: See total funded organizations and amounts

---

## Google Login Troubleshooting

### Issue: Google sign-in popup doesn't appear or fails

**Root Causes & Solutions:**

#### 1. Firebase Configuration Missing/Incorrect
Check frontend environment variables are loaded:
```bash
# Frontend .env files should have:
VITE_FIREBASE_API_KEY=AIzaSyBQJtYdLYX-51d89y0JDcgx-g8Hi5HeRgQ
VITE_FIREBASE_AUTH_DOMAIN=daanaa-af9c2.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=daanaa-af9c2
VITE_FIREBASE_APP_ID=1:962354510737:web:d8d9a2c0716ba1166bf830
```

**Fix**: Rebuild frontend to load env vars
```bash
npm run build
```

#### 2. Google OAuth Not Enabled in Firebase
**Check in Firebase Console (console.firebase.google.com):**
1. Go to daanaa-af9c2 project
2. Authentication → Sign-in method
3. Ensure "Google" is enabled
4. Click Google, verify Configuration:
   - Client ID from Google Cloud Console should be set
   - Support email configured
   - Authorized Domains includes: daanaa.org

**Fix**: Enable Google auth in Firebase if disabled

#### 3. OAuth Consent Screen Not Configured
**In Google Cloud Console (console.cloud.google.com):**
1. Go to APIs & Services → OAuth 2.0 Consent Screen
2. User Type should be "External"
3. App Information filled (app name, user support email)
4. Authorized Domains includes: daanaa.org
5. Scopes: Default (email, profile) is fine
6. Test Users: Add yourself for testing

**Fix**: Complete the OAuth consent screen configuration

#### 4. Authorized JavaScript Origins Missing
**In Google Cloud Console:**
1. APIs & Services → Credentials
2. Find the OAuth 2.0 Client ID (Web application)
3. Edit → Authorized JavaScript Origins
4. Must include:
   - https://daanaa.org
   - https://www.daanaa.org
   - http://localhost:5173 (for local dev)

**Fix**: Add missing origins to authorized list

#### 5. Browser Blocking Popups
**User-side issue:**
- Browser popup blocker enabled
- Third-party cookies disabled
- Incognito/Private window with stricter settings

**Fix**: Disable popup blocker for daanaa.org, or add to whitelist

#### 6. CORS or Network Issues
**Check browser console (F12):**
- Look for CORS errors
- Network tab shows failed requests to identitytoolkit.googleapis.com
- Check if behind corporate firewall/VPN blocking Google services

**Fix**: 
- Check network connectivity to Google APIs
- Verify Daanaa CSP headers allow Google origins (already configured)

---

## Testing Google Login

### Local Development
```bash
cd frontend
npm run dev  # runs on http://localhost:5173
# Visit http://localhost:5173/wallet
# Click "Preview Mode" → "Sign in with Google"
```

### Production Testing
1. Visit https://daanaa.org/wallet
2. See "Preview Mode" banner
3. Click "Sign in with Google"
4. Should see Google consent popup
5. Select account and consent
6. Should redirect back with auth state
7. Wallet should show "Signed in as [email]"

### Debug Steps
1. **Open browser DevTools** (F12)
2. **Console tab** - look for errors (red messages)
3. **Network tab** - check requests to:
   - securetoken.googleapis.com (should be 200)
   - identitytoolkit.googleapis.com (should be 200)
4. **Application tab** - check Firebase config loaded:
   - Storage → Local Storage → daanaa.org
   - Should see Firebase auth data if signed in

---

## Firestore Security Rules

Current rules in Firestore:
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users own their wallet data
    match /{uid}/wallet/{document=**} {
      allow read, write: if request.auth.uid == uid;
    }
    match /{uid}/funding/{document=**} {
      allow read, write: if request.auth.uid == uid;
    }
    match /{uid}/hours/{document=**} {
      allow read, write: if request.auth.uid == uid;
    }
  }
}
```

These rules mean:
- Only logged-in users can read/write their own data
- Data is isolated per user (keyed by Firebase UID)
- No cross-user data sharing

---

## Data Flow

### Preview Mode (No Auth)
```
User → Wallet Page
  ↓ (local state only)
Form Fields (nonprofit name, date, amount)
  ↓ (click save)
Error: "Please sign in to save"
  ↓ (click sign-in button)
Google OAuth Popup
```

### After Authentication
```
Google Sign-in → Firebase Token → API endpoint
  ↓
API validates token → Firestore write
  ↓
Data saved in Firestore (Firestore/{uid}/wallet/...)
  ↓
Page shows "Signed in as user@gmail.com"
  ↓
All saves now persist to Firestore
```

---

## Known Limitations

1. **No Desktop/Mobile Cross-Sync Yet**
   - Wallet data is per-device/per-browser
   - Signing in on phone doesn't see desktop data (Firestore structure supports it, frontend not built yet)

2. **No Offline Support**
   - Data requires internet to save
   - Preview mode works offline, but can't save

3. **No Export Until User Pays**
   - CSV export planned post-launch
   - Currently wallet data viewable in browser, not downloadable

---

## Next Steps to Fix Google Login

If Google login still doesn't work after checks above:

1. **Enable Debug Logging** in AuthContext.tsx:
   ```typescript
   const signInWithGoogle = async () => {
     const provider = new GoogleAuthProvider()
     console.log('Attempting Google sign-in...')
     try {
       await signInWithPopup(auth, provider)
       console.log('Sign-in successful!')
     } catch (err) {
       console.error('Sign-in error:', err)
     }
   }
   ```

2. **Check Firebase Console Logs**:
   - https://console.firebase.google.com
   - daanaa-af9c2 project
   - Firestore → Logs
   - Look for auth errors

3. **Verify Google Cloud Project Setup**:
   - https://console.cloud.google.com
   - Select "daanaa-af9c2" project
   - Check APIs & Services are enabled:
     - Identity Toolkit API ✓
     - Cloud Firestore API ✓
     - Authentication ✓

4. **Test Token Validation**:
   - After sign-in, check API can read wallet data
   - Visit API endpoint: https://daanaa.org/api/wallet/summary
   - Should return wallet data if auth works

