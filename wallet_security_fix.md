# Wallet Security Fix: Session Key Caching Vulnerability

## Problem
WalletContext.tsx caches raw AES key bytes in sessionStorage (base64-encoded).
- XSS can exfiltrate the key and decrypt wallet data without passphrase
- Session key is non-extractable CryptoKey, but raw bytes bypass that

Location: wallet.crypto.ts:116-134, WalletContext.tsx:207-208

## Solution
Replace raw key caching with server-issued JWT tokens.

### Design

**Before (insecure):**
```
User enters passphrase
  ↓
Derive keyHash (lookup token) + raw key bytes
  ↓
Store raw bytes in sessionStorage
  ↓
Use raw bytes to decrypt on every sync
  ↓
ATTACK: XSS extracts raw bytes → full wallet compromise
```

**After (secure):**
```
User enters passphrase
  ↓
Derive keyHash (lookup token)
  ↓
POST to /api/wallet/token with keyHash
  ↓
Server validates keyHash exists
  ↓
Server issues JWT (5-min expiry, keyHash claim)
  ↓
Store JWT in httpOnly cookie (cannot be XSS'd)
  ↓
Use JWT for subsequent syncs
  ↓
Passphrase never re-derived, never stored
```

### API Changes

**New endpoint: POST /api/wallet/token**
```json
Request:
{
  "keyHash": "<server_lookup_token>"
}

Response:
{
  "token": "eyJhbGc...",
  "expiresIn": 300
}
```

**Modified: POST /api/wallet/sync**
- Old: keyHash in body, raw encryption key used locally
- New: JWT in Authorization header, keyHash derived from JWT claim

### Implementation

**Step 1:** Add token endpoint to Flask backend
**Step 2:** Update WalletContext to request token on unlock
**Step 3:** Store token in httpOnly cookie (automatic)
**Step 4:** Update sync to use Authorization header instead of sessionStorage
**Step 5:** Remove raw key byte caching entirely

### Why This Works

- JWT is httpOnly → safe from XSS
- JWT has short TTL → bounded attack window
- Passphrase never stored → cannot be exfiltrated
- Validation on server side → attacker cannot forge tokens
- No raw crypto material in browser storage

### Testing

- Unit: token generation, validation, expiry
- E2E: full unlock → sync → logout flow
- Security: verify XSS cannot access token, cannot forge JWT

### Timeline

- Backend: 30 min
- Frontend: 45 min
- Tests: 30 min
- Total: ~2 hours
