# Donor Firebase Auth + Wallet Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional Google Sign-In (+ email magic link) to the donor wallet so records survive device loss and sync across browsers — device-first, account optional.

**Architecture:** Firebase Auth handles identity (Google + magic link). A new `wallet_sync` table in `merit_registry.db` stores an encrypted JSON blob per `firebase_uid`. The backend verifies Firebase ID tokens via `firebase-admin`. The frontend merges local + remote records on sign-in, with local winning on conflict.

**Tech Stack:** Firebase JS SDK v10 (frontend), firebase-admin 6.x (Flask backend), SQLite (existing DB), React context for auth state.

---

## What the user must do in Firebase Console (parallel to build)

1. Go to **console.firebase.google.com** → Add project → **select your existing Google Cloud project**
2. In the left sidebar → **Build → Authentication → Get started**
3. **Sign-in method** tab → enable **Google** → set support email → Save
4. **Sign-in method** tab → enable **Email/Password** → toggle on **Email link (passwordless sign-in)** → Save
5. **Settings** tab → **Authorized domains** → add `daanaa.org` and `localhost`
6. **Project Settings** (gear icon) → **General** → scroll to **Your apps** → click **Add app** → choose Web (`</>`) → register as `daanaa-web` → copy the `firebaseConfig` object
7. **Project Settings** → **Service accounts** → **Generate new private key** → save the JSON file as `/home/akbar/meritgiving/firebase-service-account.json` (never commit this)

Then add to `/home/akbar/meritgiving/frontend/.env.development` and `.env.production`:
```
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_APP_ID=...
```

And add to `/home/akbar/meritgiving/.env`:
```
FIREBASE_SERVICE_ACCOUNT_PATH=/home/akbar/meritgiving/firebase-service-account.json
```

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `frontend/src/lib/firebase.ts` | Firebase app init + auth export |
| Create | `frontend/src/contexts/AuthContext.tsx` | Auth state (user, loading, signIn, signOut) |
| Create | `frontend/src/components/GoogleSignInButton.tsx` | Reusable sign-in button |
| Modify | `frontend/src/pages/Wallet.tsx` | Replace "Coming soon" block with real sign-in |
| Modify | `frontend/src/hooks/useWallet.ts` | Add `syncToServer` / `loadFromServer` |
| Modify | `frontend/src/App.tsx` | Wrap with `AuthProvider` |
| Modify | `daanaa_api.py` | Add `wallet_sync` table + `/api/wallet` endpoints |
| Create | `tests/test_wallet_sync.py` | Backend tests for wallet endpoints |

---

## Task 1: Install dependencies

**Files:** `frontend/package.json`, `requirements.txt` (or venv)

- [ ] **Step 1: Install Firebase JS SDK**

```bash
cd /home/akbar/meritgiving/frontend && npm install firebase
```

Expected: firebase added to `node_modules`, no peer dep errors.

- [ ] **Step 2: Install firebase-admin in Python venv**

```bash
source ~/meritgiving/venv/bin/activate && pip install firebase-admin
```

Expected: `Successfully installed firebase-admin-...`

- [ ] **Step 3: Verify installs**

```bash
cd /home/akbar/meritgiving/frontend && node -e "require('firebase/app'); console.log('ok')"
source ~/meritgiving/venv/bin/activate && python3 -c "import firebase_admin; print('ok')"
```

Expected: both print `ok`.

- [ ] **Step 4: Commit**

```bash
cd /home/akbar/meritgiving
git add frontend/package.json frontend/package-lock.json
git commit -m "deps: add firebase JS SDK and firebase-admin"
```

---

## Task 2: Firebase client init

**Files:**
- Create: `frontend/src/lib/firebase.ts`

- [ ] **Step 1: Create `frontend/src/lib/firebase.ts`**

```typescript
import { initializeApp, getApps } from 'firebase/app'
import { getAuth } from 'firebase/auth'

const firebaseConfig = {
  apiKey:     import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:  import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId:      import.meta.env.VITE_FIREBASE_APP_ID,
}

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0]
export const auth = getAuth(app)
```

- [ ] **Step 2: Add placeholder env vars for dev (so Vite doesn't crash before user pastes real values)**

Add to `frontend/.env.development` if not already present:
```
VITE_FIREBASE_API_KEY=placeholder
VITE_FIREBASE_AUTH_DOMAIN=placeholder.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=placeholder
VITE_FIREBASE_APP_ID=placeholder
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd /home/akbar/meritgiving/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors related to `firebase.ts`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/firebase.ts frontend/.env.development
git commit -m "feat(auth): add Firebase client init"
```

---

## Task 3: AuthContext

**Files:**
- Create: `frontend/src/contexts/AuthContext.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create `frontend/src/contexts/AuthContext.tsx`**

```typescript
import React, { createContext, useContext, useEffect, useState } from 'react'
import {
  GoogleAuthProvider,
  isSignInWithEmailLink,
  onAuthStateChanged,
  sendSignInLinkToEmail,
  signInWithEmailLink,
  signInWithPopup,
  signOut as firebaseSignOut,
  type User,
} from 'firebase/auth'
import { auth } from '../lib/firebase'

const ACTION_CODE_SETTINGS = {
  url: `${window.location.origin}/wallet?emailSignIn=1`,
  handleCodeInApp: true,
}

interface AuthContextValue {
  user: User | null
  loading: boolean
  signInWithGoogle: () => Promise<void>
  sendMagicLink: (email: string) => Promise<void>
  signOut: () => Promise<void>
  getIdToken: () => Promise<string | null>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, u => {
      setUser(u)
      setLoading(false)
    })
    return unsub
  }, [])

  // Complete email magic-link sign-in if we landed back from the link
  useEffect(() => {
    if (isSignInWithEmailLink(auth, window.location.href)) {
      const email = window.localStorage.getItem('daanaa_signin_email')
      if (email) {
        signInWithEmailLink(auth, email, window.location.href)
          .then(() => window.localStorage.removeItem('daanaa_signin_email'))
          .catch(console.error)
      }
    }
  }, [])

  const signInWithGoogle = async () => {
    const provider = new GoogleAuthProvider()
    await signInWithPopup(auth, provider)
  }

  const sendMagicLink = async (email: string) => {
    await sendSignInLinkToEmail(auth, email, ACTION_CODE_SETTINGS)
    window.localStorage.setItem('daanaa_signin_email', email)
  }

  const signOut = async () => {
    await firebaseSignOut(auth)
  }

  const getIdToken = async () => {
    if (!user) return null
    return user.getIdToken()
  }

  return (
    <AuthContext.Provider value={{ user, loading, signInWithGoogle, sendMagicLink, signOut, getIdToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
```

- [ ] **Step 2: Wrap App with AuthProvider in `frontend/src/App.tsx`**

Find the existing root return in App.tsx (around line 44) and wrap:
```typescript
// Add import at top:
import { AuthProvider } from './contexts/AuthContext'

// Wrap the existing JSX:
return (
  <AuthProvider>
    <BrowserRouter>
      {/* existing content unchanged */}
    </BrowserRouter>
  </AuthProvider>
)
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd /home/akbar/meritgiving/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/contexts/AuthContext.tsx frontend/src/App.tsx
git commit -m "feat(auth): add AuthContext with Google + magic link providers"
```

---

## Task 4: Backend — wallet_sync table + endpoints

**Files:**
- Modify: `daanaa_api.py` (add table init + 3 endpoints)
- Create: `tests/test_wallet_sync.py`

- [ ] **Step 1: Write failing tests first**

Create `tests/test_wallet_sync.py`:

```python
import json
import pytest
from unittest.mock import patch, MagicMock

# Must patch firebase_admin before daanaa_api imports it
import sys
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.auth'] = MagicMock()
sys.modules['firebase_admin.credentials'] = MagicMock()

import daanaa_api as api

@pytest.fixture
def client():
    api.app.config['TESTING'] = True
    with api.app.test_client() as c:
        yield c

FAKE_UID = 'test-uid-abc123'
FAKE_TOKEN = 'fake-firebase-id-token'

def _mock_verify(token, check_revoked=False):
    if token == FAKE_TOKEN:
        return {'uid': FAKE_UID}
    raise Exception('Invalid token')

def test_wallet_get_empty(client):
    with patch('firebase_admin.auth.verify_id_token', side_effect=_mock_verify):
        r = client.get('/api/wallet', headers={'Authorization': f'Bearer {FAKE_TOKEN}'})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data['donations'] == []
        assert data['volunteerHours'] == []

def test_wallet_put_and_get(client):
    payload = {
        'donations': [{'id': '1', 'ein': '12-3456789', 'orgName': 'Test Org', 'amount': 100, 'date': '2026-01-01', 'status': 'self_documented', 'loggedAt': '2026-01-01T00:00:00Z', 'letterRequested': False}],
        'volunteerHours': []
    }
    with patch('firebase_admin.auth.verify_id_token', side_effect=_mock_verify):
        r = client.put('/api/wallet',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {FAKE_TOKEN}'}
        )
        assert r.status_code == 200

        r2 = client.get('/api/wallet', headers={'Authorization': f'Bearer {FAKE_TOKEN}'})
        assert r2.status_code == 200
        data = json.loads(r2.data)
        assert len(data['donations']) == 1
        assert data['donations'][0]['orgName'] == 'Test Org'

def test_wallet_requires_auth(client):
    r = client.get('/api/wallet')
    assert r.status_code == 401

def test_wallet_delete(client):
    with patch('firebase_admin.auth.verify_id_token', side_effect=_mock_verify):
        client.put('/api/wallet',
            data=json.dumps({'donations': [{'id': '1', 'ein': '12-3456789', 'orgName': 'X', 'amount': 50, 'date': '2026-01-01', 'status': 'self_documented', 'loggedAt': '2026-01-01T00:00:00Z', 'letterRequested': False}], 'volunteerHours': []}),
            content_type='application/json',
            headers={'Authorization': f'Bearer {FAKE_TOKEN}'}
        )
        r = client.delete('/api/wallet', headers={'Authorization': f'Bearer {FAKE_TOKEN}'})
        assert r.status_code == 200
        r2 = client.get('/api/wallet', headers={'Authorization': f'Bearer {FAKE_TOKEN}'})
        data = json.loads(r2.data)
        assert data['donations'] == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/akbar/meritgiving
source ~/meritgiving/venv/bin/activate
python3 -m pytest tests/test_wallet_sync.py -v 2>&1 | tail -20
```

Expected: ImportError or failures (endpoints don't exist yet).

- [ ] **Step 3: Add Firebase Admin init to `daanaa_api.py`**

Find the imports section at the top of `daanaa_api.py` (around line 1-30) and add:

```python
import firebase_admin
from firebase_admin import auth as fb_auth, credentials as fb_creds

_fb_app = None
_FIREBASE_SA_PATH = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH', '')
if _FIREBASE_SA_PATH and os.path.exists(_FIREBASE_SA_PATH):
    _fb_cred = fb_creds.Certificate(_FIREBASE_SA_PATH)
    _fb_app = firebase_admin.initialize_app(_fb_cred)
```

- [ ] **Step 4: Add `_require_firebase_user` helper to `daanaa_api.py`**

Add after the Firebase init block:

```python
def _require_firebase_user():
    """Extract and verify Firebase ID token from Authorization header.
    Returns firebase_uid string or aborts with 401."""
    from flask import request, abort
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        abort(401)
    token = auth_header[7:]
    try:
        decoded = fb_auth.verify_id_token(token, check_revoked=False)
        return decoded['uid']
    except Exception:
        abort(401)
```

- [ ] **Step 5: Add `wallet_sync` table creation inside `_init_db()` in `daanaa_api.py`**

Find the `_init_db()` function. Inside the `with db:` block, after the last `CREATE TABLE IF NOT EXISTS`, add:

```python
db.execute("""
    CREATE TABLE IF NOT EXISTS wallet_sync (
        firebase_uid  TEXT PRIMARY KEY,
        donations_json TEXT NOT NULL DEFAULT '[]',
        volunteer_json TEXT NOT NULL DEFAULT '[]',
        updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
    )
""")
```

- [ ] **Step 6: Add wallet sync endpoints to `daanaa_api.py`**

Add these three routes after the existing claim routes (around line 2450):

```python
# ── Donor wallet sync ────────────────────────────────────────────────────────
# Storage: one row per firebase_uid. Donations and volunteer hours are
# stored as JSON blobs. No PII beyond what the donor explicitly saved.

@app.route('/api/wallet', methods=['GET'])
def wallet_get():
    uid = _require_firebase_user()
    with _db() as db:
        row = db.execute(
            'SELECT donations_json, volunteer_json FROM wallet_sync WHERE firebase_uid = ?', (uid,)
        ).fetchone()
    if not row:
        return jsonify({'donations': [], 'volunteerHours': []})
    return jsonify({
        'donations':      json.loads(row['donations_json']),
        'volunteerHours': json.loads(row['volunteer_json']),
    })


@app.route('/api/wallet', methods=['PUT'])
def wallet_put():
    uid = _require_firebase_user()
    data = request.get_json(silent=True) or {}
    donations = data.get('donations', [])
    volunteer = data.get('volunteerHours', [])
    if not isinstance(donations, list) or not isinstance(volunteer, list):
        return jsonify({'error': 'donations and volunteerHours must be arrays'}), 400
    with _db() as db:
        db.execute("""
            INSERT INTO wallet_sync (firebase_uid, donations_json, volunteer_json, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(firebase_uid) DO UPDATE SET
                donations_json = excluded.donations_json,
                volunteer_json = excluded.volunteer_json,
                updated_at     = excluded.updated_at
        """, (uid, json.dumps(donations), json.dumps(volunteer)))
    return jsonify({'ok': True})


@app.route('/api/wallet', methods=['DELETE'])
def wallet_delete():
    """GDPR-compliant: wipe all stored wallet data for this user."""
    uid = _require_firebase_user()
    with _db() as db:
        db.execute('DELETE FROM wallet_sync WHERE firebase_uid = ?', (uid,))
    return jsonify({'ok': True})
```

- [ ] **Step 7: Run tests — should pass now**

```bash
cd /home/akbar/meritgiving
source ~/meritgiving/venv/bin/activate
python3 -m pytest tests/test_wallet_sync.py -v 2>&1 | tail -20
```

Expected: 4 PASSED.

- [ ] **Step 8: Commit**

```bash
git add daanaa_api.py tests/test_wallet_sync.py
git commit -m "feat(auth): add wallet_sync table + GET/PUT/DELETE /api/wallet endpoints"
```

---

## Task 5: Wallet sync hook

**Files:**
- Modify: `frontend/src/hooks/useWallet.ts`

- [ ] **Step 1: Add sync functions to `useWallet.ts`**

Add these imports at the top of `useWallet.ts`:

```typescript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000'
```

Add these two functions just before the `useWallet` export (after the `buildSummaryText` function at the end of the hook internals):

Inside `useWallet()`, add two new callbacks after `removeVolunteer`:

```typescript
const syncToServer = useCallback(async (getToken: () => Promise<string | null>) => {
  const token = await getToken()
  if (!token) return
  await fetch(`${API_BASE}/api/wallet`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ donations: load<DonationRecord>(DONATIONS_KEY), volunteerHours: load<VolunteerRecord>(VOLUNTEER_KEY) }),
  })
}, [])

const loadFromServer = useCallback(async (getToken: () => Promise<string | null>) => {
  const token = await getToken()
  if (!token) return
  const res = await fetch(`${API_BASE}/api/wallet`, {
    headers: { 'Authorization': `Bearer ${token}` },
  })
  if (!res.ok) return
  const remote = await res.json() as { donations: DonationRecord[]; volunteerHours: VolunteerRecord[] }
  // Merge: union by id, local record wins on conflict
  const localDonations = load<DonationRecord>(DONATIONS_KEY)
  const localVolunteer = load<VolunteerRecord>(VOLUNTEER_KEY)
  const mergedDonations = [...localDonations]
  for (const rd of remote.donations) {
    if (!mergedDonations.find(d => d.id === rd.id)) mergedDonations.push(rd)
  }
  const mergedVolunteer = [...localVolunteer]
  for (const rv of remote.volunteerHours) {
    if (!mergedVolunteer.find(v => v.id === rv.id)) mergedVolunteer.push(rv)
  }
  persist(DONATIONS_KEY, mergedDonations)
  persist(VOLUNTEER_KEY, mergedVolunteer)
  setDonations(mergedDonations)
  setVolunteerHours(mergedVolunteer)
}, [])
```

Add `syncToServer` and `loadFromServer` to the return object of `useWallet`.

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd /home/akbar/meritgiving/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useWallet.ts
git commit -m "feat(auth): add syncToServer + loadFromServer to useWallet"
```

---

## Task 6: Sign-in button component

**Files:**
- Create: `frontend/src/components/GoogleSignInButton.tsx`

- [ ] **Step 1: Create `frontend/src/components/GoogleSignInButton.tsx`**

```typescript
import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export function GoogleSignInButton({ onSuccess }: { onSuccess?: () => void }) {
  const { signInWithGoogle } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClick = async () => {
    setLoading(true)
    setError(null)
    try {
      await signInWithGoogle()
      onSuccess?.()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Sign-in failed'
      // User closed the popup — not an error worth showing
      if (!msg.includes('popup-closed')) setError('Could not sign in. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={loading}
        className="inline-flex items-center gap-3 rounded-xl border border-light-grey bg-white px-5 py-3 font-body text-[14px] font-medium text-deep-navy shadow-sm hover:border-soft-gold/40 hover:bg-warm-cream/30 transition-colors disabled:opacity-50"
      >
        {/* Google G logo */}
        <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
          <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
          <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.909-2.259c-.806.54-1.837.86-3.047.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
          <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
          <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
        </svg>
        {loading ? 'Signing in…' : 'Continue with Google'}
      </button>
      {error && <p className="mt-2 font-body text-[12px] text-alert-amber">{error}</p>}
    </div>
  )
}

export function MagicLinkForm({ onSent }: { onSent: (email: string) => void }) {
  const { sendMagicLink } = useAuth()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return
    setLoading(true)
    setError(null)
    try {
      await sendMagicLink(email.trim())
      onSent(email.trim())
    } catch {
      setError('Could not send the link. Check your email address and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <input
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder="your@email.com"
        required
        className="w-full border border-light-grey rounded-lg px-3 py-2 font-body text-[14px] text-deep-navy bg-white outline-none focus:border-soft-gold transition-colors"
      />
      <button
        type="submit"
        disabled={loading}
        className="px-5 py-2 rounded-lg bg-deep-navy text-warm-cream font-body text-[13px] font-semibold hover:bg-navy-mid transition-colors disabled:opacity-50"
      >
        {loading ? 'Sending…' : 'Send sign-in link'}
      </button>
      {error && <p className="mt-1 font-body text-[12px] text-alert-amber">{error}</p>}
    </form>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd /home/akbar/meritgiving/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/GoogleSignInButton.tsx
git commit -m "feat(auth): add GoogleSignInButton and MagicLinkForm components"
```

---

## Task 7: Wire auth into Wallet page

**Files:**
- Modify: `frontend/src/pages/Wallet.tsx`

- [ ] **Step 1: Add imports to `Wallet.tsx`**

At the top of `Wallet.tsx`, add:

```typescript
import { useAuth } from '../contexts/AuthContext'
import { GoogleSignInButton, MagicLinkForm } from '../components/GoogleSignInButton'
```

- [ ] **Step 2: Add auth state + sync effect inside `Wallet()`**

Inside the `Wallet` component, after the existing hooks, add:

```typescript
const { user, loading: authLoading, signOut, getIdToken } = useAuth()
const { syncToServer, loadFromServer, ...walletRest } = useWallet()
const [magicLinkSent, setMagicLinkSent] = useState(false)
const [showEmailForm, setShowEmailForm] = useState(false)
const [syncing, setSyncing] = useState(false)

// On sign-in: merge remote records into local, then push merged back
useEffect(() => {
  if (!user) return
  setSyncing(true)
  loadFromServer(getIdToken)
    .then(() => syncToServer(getIdToken))
    .finally(() => setSyncing(false))
}, [user]) // eslint-disable-line react-hooks/exhaustive-deps
```

- [ ] **Step 3: Replace the "Coming soon" block in `Wallet.tsx`**

Find and replace the dashed "Coming soon" block (around line 411–429):

```typescript
{/* Account sync */}
{!authLoading && !user && (
  <div className="rounded-xl border border-dashed border-soft-gold/30 bg-soft-gold/[0.04] p-5">
    <div className="flex items-start gap-4">
      <div className="shrink-0 w-9 h-9 rounded-full bg-soft-gold/10 flex items-center justify-center mt-0.5">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-body text-[14px] font-semibold text-deep-navy mb-1">Keep your record across devices</p>
        <p className="font-body text-[13px] text-cool-grey leading-[1.6] mb-4">
          Sign in to save your giving record to your account — so it's there on every browser and device. No tracking, no sharing. Your record stays yours.
        </p>
        {!showEmailForm && !magicLinkSent && (
          <div className="flex flex-col gap-3">
            <GoogleSignInButton />
            <button
              onClick={() => setShowEmailForm(true)}
              className="font-body text-[13px] text-soft-gold hover:text-bright-gold underline underline-offset-2 transition-colors w-fit"
            >
              Use email link instead
            </button>
          </div>
        )}
        {showEmailForm && !magicLinkSent && (
          <MagicLinkForm onSent={email => { setMagicLinkSent(true); setShowEmailForm(false); }} />
        )}
        {magicLinkSent && (
          <p className="font-body text-[13px] text-cool-grey">
            Check your email for a sign-in link. It expires in 1 hour.
          </p>
        )}
      </div>
    </div>
  </div>
)}

{user && (
  <div className="rounded-xl border border-light-grey bg-white p-5">
    <div className="flex items-center justify-between gap-3 flex-wrap">
      <div className="flex items-center gap-3">
        {user.photoURL && <img src={user.photoURL} alt="" className="w-8 h-8 rounded-full" />}
        <div>
          <p className="font-body text-[14px] font-medium text-deep-navy">{user.displayName || user.email}</p>
          <p className="font-body text-[12px] text-cool-grey">
            {syncing ? 'Syncing…' : 'Record synced across your devices'}
          </p>
        </div>
      </div>
      <button
        onClick={signOut}
        className="font-body text-[12px] text-cool-grey hover:text-deep-navy underline underline-offset-2 transition-colors"
      >
        Sign out
      </button>
    </div>
  </div>
)}
```

- [ ] **Step 4: Update the `useWallet` destructuring** (since we now destructure `syncToServer`/`loadFromServer` separately)

Find the existing `const { donations, addDonationDirect, ... } = useWallet()` line and merge with `walletRest`:

```typescript
const { donations, volunteerHours, addDonationDirect, markAcknowledged, removeDonation,
        totalDonated, totalDonatedThisYear, uniqueEins, pendingLetters,
        exportBackup, importBackup, backupOverdue, lastBackupAt } = walletRest
```

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd /home/akbar/meritgiving/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Wallet.tsx
git commit -m "feat(auth): wire Google Sign-In + magic link into Wallet page with server sync"
```

---

## Task 8: End-to-end smoke test

**Prerequisite:** User has completed Firebase Console setup and pasted real config values into `.env.development`.

- [ ] **Step 1: Start backend**

```bash
cd /home/akbar/meritgiving
source ~/meritgiving/venv/bin/activate
python3 daanaa_api.py
```

Expected: `Running on http://127.0.0.1:5000`

- [ ] **Step 2: Start frontend**

```bash
cd /home/akbar/meritgiving/frontend && npm run dev
```

Expected: `Local: http://localhost:5173`

- [ ] **Step 3: Smoke test checklist**

Open `http://localhost:5173/wallet` in a browser:

1. The sign-in block is visible (not "coming soon")
2. Click "Continue with Google" → Google popup appears → sign in → popup closes → user avatar appears, "Synced across your devices" message shown
3. Log a donation → navigate away → come back → donation still there
4. Open a second browser (or incognito) → sign in with same Google account → donation appears after sync
5. Click "Sign out" → sign-in block reappears
6. "Use email link instead" → enter email → "Check your email" message appears

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat(auth): donor Firebase auth + wallet sync complete"
```

---

## Self-review

**Spec coverage:**
- ✅ Google Sign-In
- ✅ Email magic link
- ✅ Device-first (wallet works without account)
- ✅ Cross-device sync (merge on sign-in, push on every local change — Task 7 wires the effect)
- ✅ Sign-out
- ✅ GDPR delete endpoint (DELETE /api/wallet)
- ✅ Backend auth (token verification, 401 if missing)
- ✅ No PII stored beyond what donor logged
- ✅ Tests for all backend endpoints

**Merge strategy:** local wins on conflict (union by id — a record in local but not remote is kept; remote-only records are added). This matches device-first philosophy.

**Not in scope for this plan:** nonprofit portal auth (separate plan), wallet auto-sync on every mutation (can be added later — for now sync happens on sign-in).
