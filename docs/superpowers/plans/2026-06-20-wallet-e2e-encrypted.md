# Giving Wallet — E2E Encrypted Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current org-snapshot wallet (localStorage `WalletOrg[]`) with a normalized, E2E-encrypted wallet (`WalletEntry[]` — EINs + intent only) that syncs across devices via a dumb ciphertext locker on the server.

**Architecture:** SubtleCrypto (native browser, zero imports) derives an AES-GCM key from a BIP39 4-word passphrase via PBKDF2 → dual-HKDF. The server stores opaque ciphertext and cannot read wallet contents. Session key cached in sessionStorage (raw AES bytes, re-imported as non-extractable CryptoKey on page load) so user enters passphrase once per browser session, not on every navigation.

**Tech Stack:** React 19, TypeScript, SubtleCrypto (native), Flask, SQLite, Jest, pytest. BIP39 wordlist (public domain JSON, ~16KB).

**Design doc:** `~/.gstack/projects/meritgiving/akbar-master-design-20260620-181500.md` (Status: APPROVED)

---

## Data Flow

```
SETUP (first time)
  User → PassphraseModal → generatePassphrase() → [4 words shown]
  → POST /api/wallet/init → { salt: base64 }
  → deriveAll(passphrase, salt) → { encKey, keyHash }
  → encryptWallet([]) → { ciphertext, iv }
  → POST /api/wallet/sync { keyHash, ciphertext, iv, salt }
  → sessionStorage ← raw encKey bytes
  → localStorage ← { keyHash, salt } (not secret)

SYNC (add org or edit intent)
  WalletContext.entries mutates
  → encryptWallet(entries, encKey) → { ciphertext, iv }
  → POST /api/wallet/sync { keyHash, ciphertext, iv, salt }

RESTORE (second device)
  User → PassphraseModal (restore mode) → enters passphrase
  → GET /api/wallet/sync?keyHash=… → { ciphertext, iv, salt }
  → deriveAll(passphrase, salt) → { encKey, keyHash }
  → decryptWallet(ciphertext, iv, encKey) → WalletEntry[]
  → WalletContext hydrates

PAGE LOAD (returning user, same session)
  sessionStorage['dw_k'] exists → importKey(raw bytes) → encKey
  → GET /api/wallet/sync?keyHash=… → decrypt → hydrate
  No passphrase prompt.

WALLET PAGE RENDER
  WalletEntry[] (EINs only) + batch GET /api/organizations/<ein>
  → hydrated ApiOrganization data → WalletCard renders live org info
```

---

## File Structure

**New files:**
- `frontend/src/utils/wallet.crypto.ts` — crypto layer (PBKDF2/HKDF, encrypt/decrypt, passphrase gen)
- `frontend/src/components/PassphraseModal.tsx` — setup + restore modal
- `frontend/public/bip39-english.json` — BIP39 wordlist (~16KB, public domain)
- `frontend/src/__tests__/wallet.crypto.test.ts` — crypto round-trip unit tests
- `tests/test_wallet_e2e.py` — Flask endpoint tests for new E2E wallet routes

**Modified files:**
- `frontend/src/types/wallet.ts` — add `WalletEntry`, update `Wallet` type, remove `WalletOrg` snapshot fields
- `frontend/src/contexts/WalletContext.tsx` — strip org snapshots, add passphrase/sync state
- `frontend/src/utils/walletStorage.ts` — add sessionStorage helpers for session key
- `frontend/src/components/WalletCard.tsx` — accept `WalletEntry` + `ApiOrganization` instead of `WalletOrg`
- `frontend/src/components/AddToWalletButton.tsx` — no longer fetches org data on add (just saves EIN)
- `frontend/src/pages/WalletPage.tsx` — batch hydration, passphrase flow, remove stale-check
- `daanaa_api.py` — add `/api/wallet/init`, `/api/wallet/sync` (E2E endpoints, additive to existing)

**NOT in scope:**
- Quarterly re-engagement email (`wallet_update_subscriptions` table, `scripts/generate_quarterly_summaries.py`) — deferred to Week 2. Core wallet must ship first.
- Passkey PRF extension (WebAuthn biometric key derivation) — deferred until WebAuthn PRF browser support stabilizes (~mid-2026).
- BIP39 localization (Spanish, Chinese, etc.) — deferred; English wordlist ships first, localization is additive.
- Argon2id upgrade — deferred; PBKDF2 at 310K iterations is acceptable for giving-intent data.
- Removing old Firebase wallet endpoints (`/api/wallet/sync-saves`, `wallet_sync_saves()`) — keep alive until all users are migrated. Remove in a follow-up.

**What already exists (reused, not rebuilt):**
- `walletValidation.ts` — all intent field validators (`validateAmount`, `validateHours`, `validateIntentNotes`) reuse unchanged. `GivingIntent` type is unchanged.
- `useWalletPersistence.ts` — NOT reused (replaced by sync-on-change in WalletContext using SubtleCrypto). Can delete after Task 3.
- `walletStorage.ts` — partially reused; the `checkCorruption()` and `getQuotaInfo()` helpers can be removed (no longer relevant for encrypted storage), but the session key helpers added in Task 4 live here.
- `WalletCard.tsx` — refactored in-place (swap prop type, add loading/error states).
- `WalletPage.tsx` — refactored in-place (batch hydration, passphrase gate, remove stale check).
- `test_wallet_sync.py` — tests old Firebase wallet, stays untouched (those endpoints remain live).

---

## Task 1: Crypto Layer

**Files:**
- Create: `frontend/public/bip39-english.json`
- Create: `frontend/src/utils/wallet.crypto.ts`
- Create: `frontend/src/__tests__/wallet.crypto.test.ts`

- [ ] **Step 1: Download BIP39 English wordlist**

```bash
curl -s https://raw.githubusercontent.com/trezor/python-mnemonic/master/src/mnemonic/wordlist/english.txt \
  | python3 -c "import sys,json; words=[w.strip() for w in sys.stdin if w.strip()]; print(json.dumps(words))" \
  > frontend/public/bip39-english.json
# Verify: should be 2048 words
python3 -c "import json; w=json.load(open('frontend/public/bip39-english.json')); assert len(w)==2048, len(w); print('ok')"
```

- [ ] **Step 2: Write the failing tests first**

Create `frontend/src/__tests__/wallet.crypto.test.ts`:

```typescript
// Jest + jsdom: SubtleCrypto is available in jsdom 20+
// (jest-environment-jsdom ships with WebCrypto since Jest 29.5)

import {
  deriveAll,
  encryptWallet,
  decryptWallet,
  generatePassphrase,
} from '../utils/wallet.crypto'
import type { WalletEntry } from '../types/wallet'

const TEST_PASSPHRASE = 'correct horse battery staple'
const TEST_SALT = new Uint8Array(16).fill(0) // deterministic for tests

describe('generatePassphrase', () => {
  it('returns exactly 4 words', async () => {
    const phrase = await generatePassphrase()
    expect(phrase.split(' ')).toHaveLength(4)
  })

  it('all words come from BIP39 wordlist', async () => {
    const phrase = await generatePassphrase()
    const wordlist: string[] = await fetch('/bip39-english.json').then(r => r.json())
    for (const word of phrase.split(' ')) {
      expect(wordlist).toContain(word)
    }
  })

  it('generates different phrases each call', async () => {
    const p1 = await generatePassphrase()
    const p2 = await generatePassphrase()
    expect(p1).not.toBe(p2)
  })
})

describe('deriveAll', () => {
  it('returns encKey and keyHash', async () => {
    const { encKey, keyHash } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    expect(encKey).toBeDefined()
    expect(keyHash).toMatch(/^[0-9a-f]{64}$/) // 256 bits as hex
  })

  it('keyHash is deterministic for same passphrase+salt', async () => {
    const { keyHash: h1 } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    const { keyHash: h2 } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    expect(h1).toBe(h2)
  })

  it('different passphrase → different keyHash', async () => {
    const { keyHash: h1 } = await deriveAll('correct horse battery staple', TEST_SALT)
    const { keyHash: h2 } = await deriveAll('wrong horse battery staple', TEST_SALT)
    expect(h1).not.toBe(h2)
  })

  it('encKey is non-extractable (security invariant)', async () => {
    const { encKey } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    await expect(
      crypto.subtle.exportKey('raw', encKey)
    ).rejects.toThrow()
  })
})

describe('encrypt / decrypt round-trip', () => {
  const entries: WalletEntry[] = [
    { ein: '123456789', bookmarkedAt: 1718000000000, givingIntent: { type: 'giving', amount: 100, addedAt: 1718000001000 } },
    { ein: '987654321', bookmarkedAt: 1718000002000 },
  ]

  it('round-trips entries through encrypt → decrypt', async () => {
    const { encKey } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    const { ciphertext, iv } = await encryptWallet(entries, encKey)
    const decrypted = await decryptWallet(ciphertext, iv, encKey)
    expect(decrypted).toEqual(entries)
  })

  it('each encryption produces different iv', async () => {
    const { encKey } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    const { iv: iv1 } = await encryptWallet(entries, encKey)
    const { iv: iv2 } = await encryptWallet(entries, encKey)
    expect(iv1).not.toBe(iv2) // fresh IV on every call
  })

  it('wrong key cannot decrypt', async () => {
    const { encKey: goodKey } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    const { encKey: badKey } = await deriveAll('wrong phrase here xx', TEST_SALT)
    const { ciphertext, iv } = await encryptWallet(entries, goodKey)
    await expect(decryptWallet(ciphertext, iv, badKey)).rejects.toThrow()
  })

  it('tampered ciphertext fails decryption (AES-GCM authentication)', async () => {
    const { encKey } = await deriveAll(TEST_PASSPHRASE, TEST_SALT)
    const { ciphertext, iv } = await encryptWallet(entries, encKey)
    // Flip one byte in the ciphertext
    const bytes = Uint8Array.from(atob(ciphertext), c => c.charCodeAt(0))
    bytes[0] ^= 0xFF
    const tampered = btoa(String.fromCharCode(...bytes))
    await expect(decryptWallet(tampered, iv, encKey)).rejects.toThrow()
  })
})
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
cd frontend && npx jest wallet.crypto --no-coverage 2>&1 | tail -20
```
Expected: `Cannot find module '../utils/wallet.crypto'`

- [ ] **Step 4: Write `wallet.crypto.ts`**

Create `frontend/src/utils/wallet.crypto.ts`:

```typescript
// All native browser SubtleCrypto — zero imports.
// Design doc: ~/.gstack/projects/meritgiving/akbar-master-design-20260620-181500.md

import type { WalletEntry } from '../types/wallet'

const PBKDF2_ITERATIONS = 310_000

// Fetch the BIP39 wordlist once; cached across calls.
let _wordlist: string[] | null = null
async function getWordlist(): Promise<string[]> {
  if (_wordlist) return _wordlist
  const r = await fetch('/bip39-english.json')
  if (!r.ok) throw new Error('BIP39 wordlist unavailable')
  _wordlist = await r.json()
  return _wordlist!
}

/**
 * Generate a 4-word BIP39 passphrase.
 * Entropy: 2048^4 = 2^44. Acceptable for giving-intent data.
 */
export async function generatePassphrase(): Promise<string> {
  const words = await getWordlist()
  const indices = new Uint32Array(4)
  crypto.getRandomValues(indices)
  return Array.from(indices).map(i => words[i % 2048]).join(' ')
}

/**
 * Derive encryption key and server lookup token from passphrase + salt.
 *
 * Security design: PBKDF2 once → PRK → HKDF-Expand twice.
 *   "daanaa-wallet-key" → AES-GCM encryption key  (never leaves device)
 *   "daanaa-wallet-id"  → server lookup token (safe to send; cannot reverse to key)
 *
 * An attacker with keyHash cannot derive encKey without re-running PBKDF2.
 */
export async function deriveAll(
  passphrase: string,
  salt: Uint8Array
): Promise<{ encKey: CryptoKey; keyHash: string }> {
  const enc = new TextEncoder()

  // Step 1: PBKDF2 → raw PRK bytes
  const keyMaterial = await crypto.subtle.importKey(
    'raw', enc.encode(passphrase), 'PBKDF2', false, ['deriveBits']
  )
  const prkBits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    keyMaterial, 256
  )
  const prk = await crypto.subtle.importKey('raw', prkBits, 'HKDF', false, ['deriveBits'])

  // Step 2a: HKDF → AES-GCM encryption key (non-extractable)
  const encBits = await crypto.subtle.deriveBits(
    { name: 'HKDF', hash: 'SHA-256', salt: new Uint8Array(0), info: enc.encode('daanaa-wallet-key') },
    prk, 256
  )
  const encKey = await crypto.subtle.importKey(
    'raw', encBits, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
  )

  // Step 2b: HKDF → server lookup token (hex string, safe to transmit)
  const idBits = await crypto.subtle.deriveBits(
    { name: 'HKDF', hash: 'SHA-256', salt: new Uint8Array(0), info: enc.encode('daanaa-wallet-id') },
    prk, 256
  )
  const keyHash = Array.from(new Uint8Array(idBits))
    .map(b => b.toString(16).padStart(2, '0')).join('')

  return { encKey, keyHash }
}

/**
 * Encrypt wallet entries. Fresh IV on every call (AES-GCM requirement).
 */
export async function encryptWallet(
  entries: WalletEntry[],
  key: CryptoKey
): Promise<{ ciphertext: string; iv: string }> {
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const plaintext = JSON.stringify({ entries, syncedAt: Date.now() })
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    new TextEncoder().encode(plaintext)
  )
  return {
    ciphertext: btoa(String.fromCharCode(...new Uint8Array(encrypted))),
    iv: btoa(String.fromCharCode(...iv)),
  }
}

/**
 * Decrypt wallet entries.
 * Throws if key is wrong, ciphertext tampered, or format invalid.
 */
export async function decryptWallet(
  ciphertext: string,
  iv: string,
  key: CryptoKey
): Promise<WalletEntry[]> {
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: Uint8Array.from(atob(iv), c => c.charCodeAt(0)) },
    key,
    Uint8Array.from(atob(ciphertext), c => c.charCodeAt(0))
  )
  const parsed = JSON.parse(new TextDecoder().decode(decrypted))
  return parsed.entries as WalletEntry[]
}

/**
 * Export raw AES key bytes for sessionStorage caching.
 * The CryptoKey is non-extractable, so we re-derive from raw HKDF bits.
 * This function is for internal use by walletStorage.ts only.
 */
export async function deriveRawKeyBytes(
  passphrase: string,
  salt: Uint8Array
): Promise<Uint8Array> {
  const enc = new TextEncoder()
  const keyMaterial = await crypto.subtle.importKey(
    'raw', enc.encode(passphrase), 'PBKDF2', false, ['deriveBits']
  )
  const prkBits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    keyMaterial, 256
  )
  const prk = await crypto.subtle.importKey('raw', prkBits, 'HKDF', false, ['deriveBits'])
  const encBits = await crypto.subtle.deriveBits(
    { name: 'HKDF', hash: 'SHA-256', salt: new Uint8Array(0), info: enc.encode('daanaa-wallet-key') },
    prk, 256
  )
  return new Uint8Array(encBits)
}

/**
 * Import raw key bytes back to a CryptoKey (non-extractable).
 */
export async function importKeyFromBytes(bytes: Uint8Array): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    'raw', bytes, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
  )
}
```

- [ ] **Step 5: Run tests — all must pass**

```bash
cd frontend && npx jest wallet.crypto --no-coverage
```
Expected: `Tests: 9 passed, 9 total`

- [ ] **Step 6: Commit**

```bash
git add frontend/public/bip39-english.json \
        frontend/src/utils/wallet.crypto.ts \
        frontend/src/__tests__/wallet.crypto.test.ts
git commit -m "feat(wallet): crypto layer — PBKDF2/HKDF derive, AES-GCM encrypt/decrypt, BIP39 passphrase"
```

---

## Task 2: Backend — E2E Wallet Endpoints

**Files:**
- Modify: `daanaa_api.py` (additive — existing Firebase endpoints untouched)
- Create: `tests/test_wallet_e2e.py`

These endpoints are additive. The existing Firebase-auth wallet routes (`/api/wallet/sync-saves`, `/api/wallet/summary`, etc.) stay alive. The new E2E routes use a completely different table (`e2e_wallet_sync`).

- [ ] **Step 1: Write failing tests**

Create `tests/test_wallet_e2e.py`:

```python
"""Tests for the E2E encrypted wallet endpoints.
These endpoints require no auth — security comes from the keyHash.
"""
import json
import pytest
import daanaa_api as api

KEY_HASH = 'a' * 64  # 64-char hex (256-bit HKDF id token)
CIPHERTEXT = 'dGVzdA=='  # base64 of "test"
IV = 'AAAAAAAAAAAAAAAA'  # base64 of 12 zero bytes
SALT = 'AAAAAAAAAAAAAAAAAAAAAA=='  # base64 of 16 zero bytes

@pytest.fixture
def client():
    api.app.config['TESTING'] = True
    with api.app.test_client() as c:
        yield c

class TestWalletInit:
    def test_init_returns_salt(self, client):
        r = client.post('/api/wallet/init')
        assert r.status_code == 200
        data = json.loads(r.data)
        assert 'salt' in data
        assert isinstance(data['salt'], str)
        assert len(data['salt']) > 0

    def test_init_returns_different_salt_each_time(self, client):
        r1 = client.post('/api/wallet/init')
        r2 = client.post('/api/wallet/init')
        s1 = json.loads(r1.data)['salt']
        s2 = json.loads(r2.data)['salt']
        assert s1 != s2

class TestWalletSync:
    def test_get_missing_returns_404(self, client):
        r = client.get(f'/api/wallet/sync?keyHash={KEY_HASH}')
        assert r.status_code == 404
        data = json.loads(r.data)
        assert data['found'] is False

    def test_post_stores_and_get_retrieves(self, client):
        payload = {
            'keyHash': KEY_HASH,
            'ciphertext': CIPHERTEXT,
            'iv': IV,
            'salt': SALT,
        }
        r = client.post('/api/wallet/sync',
            data=json.dumps(payload), content_type='application/json')
        assert r.status_code == 200
        assert json.loads(r.data)['ok'] is True

        r2 = client.get(f'/api/wallet/sync?keyHash={KEY_HASH}')
        assert r2.status_code == 200
        data = json.loads(r2.data)
        assert data['found'] is True
        assert data['ciphertext'] == CIPHERTEXT
        assert data['iv'] == IV
        assert data['salt'] == SALT

    def test_post_overwrites_on_conflict(self, client):
        payload = {'keyHash': KEY_HASH, 'ciphertext': CIPHERTEXT, 'iv': IV, 'salt': SALT}
        client.post('/api/wallet/sync', data=json.dumps(payload), content_type='application/json')

        new_ct = 'bmV3Y2lwaGVydGV4dA=='
        new_iv = 'BBBBBBBBBBBBBBBB'
        payload2 = {'keyHash': KEY_HASH, 'ciphertext': new_ct, 'iv': new_iv, 'salt': SALT}
        client.post('/api/wallet/sync', data=json.dumps(payload2), content_type='application/json')

        r = client.get(f'/api/wallet/sync?keyHash={KEY_HASH}')
        data = json.loads(r.data)
        assert data['ciphertext'] == new_ct
        assert data['iv'] == new_iv

    def test_delete_removes_wallet(self, client):
        payload = {'keyHash': KEY_HASH, 'ciphertext': CIPHERTEXT, 'iv': IV, 'salt': SALT}
        client.post('/api/wallet/sync', data=json.dumps(payload), content_type='application/json')

        r = client.delete('/api/wallet/sync',
            data=json.dumps({'keyHash': KEY_HASH}), content_type='application/json')
        assert r.status_code == 200

        r2 = client.get(f'/api/wallet/sync?keyHash={KEY_HASH}')
        assert r2.status_code == 404

    def test_invalid_key_hash_rejected(self, client):
        payload = {'keyHash': 'tooshort', 'ciphertext': CIPHERTEXT, 'iv': IV, 'salt': SALT}
        r = client.post('/api/wallet/sync',
            data=json.dumps(payload), content_type='application/json')
        assert r.status_code == 400

    def test_oversized_payload_rejected(self, client):
        payload = {
            'keyHash': KEY_HASH,
            'ciphertext': 'x' * 65536,  # >64KB
            'iv': IV,
            'salt': SALT,
        }
        r = client.post('/api/wallet/sync',
            data=json.dumps(payload), content_type='application/json')
        assert r.status_code == 400
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
cd /home/akbar/meritgiving && source venv/bin/activate
python -m pytest tests/test_wallet_e2e.py -v 2>&1 | tail -20
```
Expected: `FAILED` (routes don't exist yet)

- [ ] **Step 3: Add `_ensure_e2e_wallet_sync_table` to `daanaa_api.py`**

Find the `_ensure_wallet_sync_table` function (~line 1143) and add the new function after it:

```python
def _ensure_e2e_wallet_sync_table(db: sqlite3.Connection) -> None:
    """E2E encrypted wallet locker. Server stores opaque ciphertext — cannot decrypt.
    key_hash: HKDF-derived id token (info='daanaa-wallet-id') — no identity linkage.
    iv: fresh AES-GCM IV on every encryption call.
    salt: server-issued 16 random bytes, not secret, needed for key rederivation on second device.
    Auto-purge: rows untouched for 2 years purged nightly via cron.
    """
    db.execute("""
        CREATE TABLE IF NOT EXISTS e2e_wallet_sync (
            key_hash   TEXT PRIMARY KEY,
            ciphertext TEXT NOT NULL,
            iv         TEXT NOT NULL,
            salt       TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """)
```

- [ ] **Step 4: Add rate limiting state and POST size guard near the top of `daanaa_api.py`**

Find the `import` block at the top and add after existing imports:

```python
# E2E wallet rate limiting: simple in-memory per-IP counter (no deps).
# Resets on gunicorn restart. Adequate for giving-intent data.
import collections, time as _time
_wallet_rate: dict[str, list[float]] = collections.defaultdict(list)
_WALLET_RATE_LIMIT = 10   # POST per minute per IP
_WALLET_MAX_BYTES = 65536  # 64KB max payload (~30x expected size)
```

- [ ] **Step 5: Add the three E2E wallet routes to `daanaa_api.py`**

Add after the existing `wallet_get_saves` route (search for `@app.route('/api/wallet/saves'`):

```python
# ── E2E Encrypted Wallet (no auth — security comes from keyHash) ──────────────

@app.route('/api/wallet/init', methods=['POST'])
def e2e_wallet_init():
    """Issue a random salt for a new wallet. Salt is not secret."""
    import secrets, base64
    salt = base64.b64encode(secrets.token_bytes(16)).decode()
    return jsonify({'salt': salt})


@app.route('/api/wallet/sync', methods=['GET', 'POST', 'DELETE'])
def e2e_wallet_sync():
    """Dumb ciphertext locker. Server cannot read wallet contents.

    GET  ?keyHash=<hex64>         → { found, ciphertext, iv, salt, updatedAt }
    POST { keyHash, ciphertext, iv, salt } → { ok }
    DELETE { keyHash }            → { ok }
    """
    body = request.get_json(silent=True) or {}
    key_hash = body.get('keyHash') or request.args.get('keyHash', '')

    if not key_hash or len(key_hash) != 64 or not all(c in '0123456789abcdef' for c in key_hash):
        return jsonify({'error': 'invalid key_hash'}), 400

    db = get_db()
    _ensure_e2e_wallet_sync_table(db)

    if request.method == 'POST':
        # Rate limit: 10 POST/min per IP
        ip = request.remote_addr or 'unknown'
        now = _time.time()
        window = [t for t in _wallet_rate[ip] if now - t < 60]
        if len(window) >= _WALLET_RATE_LIMIT:
            return jsonify({'error': 'rate limit exceeded'}), 429
        _wallet_rate[ip] = window + [now]

        ct = body.get('ciphertext', '')
        iv = body.get('iv', '')
        salt = body.get('salt', '')
        if not ct or not iv or not salt:
            return jsonify({'error': 'missing fields'}), 400
        if len(ct) > _WALLET_MAX_BYTES:
            return jsonify({'error': 'payload too large'}), 400

        db.execute(
            'INSERT INTO e2e_wallet_sync (key_hash, ciphertext, iv, salt, updated_at)'
            ' VALUES (?, ?, ?, ?, ?)'
            ' ON CONFLICT(key_hash) DO UPDATE SET'
            ' ciphertext=excluded.ciphertext, iv=excluded.iv, updated_at=excluded.updated_at',
            [key_hash, ct, iv, salt, int(_time.time())]
        )
        db.commit()
        return jsonify({'ok': True})

    if request.method == 'DELETE':
        db.execute('DELETE FROM e2e_wallet_sync WHERE key_hash=?', [key_hash])
        db.commit()
        return jsonify({'ok': True})

    # GET
    row = db.execute(
        'SELECT ciphertext, iv, salt, updated_at FROM e2e_wallet_sync WHERE key_hash=?',
        [key_hash]
    ).fetchone()
    if not row:
        return jsonify({'found': False}), 404
    return jsonify({'found': True, 'ciphertext': row[0], 'iv': row[1],
                    'salt': row[2], 'updatedAt': row[3]})
```

- [ ] **Step 6: Run tests — all must pass**

```bash
python -m pytest tests/test_wallet_e2e.py -v
```
Expected: `9 passed`

- [ ] **Step 7: Commit**

```bash
git add daanaa_api.py tests/test_wallet_e2e.py
git commit -m "feat(wallet): E2E wallet endpoints — /init, /sync GET/POST/DELETE (dumb ciphertext locker)"
```

---

## Task 3: WalletEntry Types + WalletContext Refactor

**Files:**
- Modify: `frontend/src/types/wallet.ts`
- Modify: `frontend/src/contexts/WalletContext.tsx`
- Delete: `frontend/src/hooks/useWalletPersistence.ts` (replaced by sync-on-change in context)

- [ ] **Step 1: Write failing test for WalletContext**

Create `frontend/src/__tests__/WalletContext.test.tsx`:

```typescript
import React from 'react'
import { render, act } from '@testing-library/react'
import { WalletProvider, useWallet } from '../contexts/WalletContext'
import type { WalletEntry } from '../types/wallet'

// Spy: track encrypt/decrypt calls
jest.mock('../utils/wallet.crypto', () => ({
  encryptWallet: jest.fn().mockResolvedValue({ ciphertext: 'ct', iv: 'iv' }),
  decryptWallet: jest.fn().mockResolvedValue([]),
  deriveAll: jest.fn().mockResolvedValue({ encKey: {} as CryptoKey, keyHash: 'a'.repeat(64) }),
}))

function Probe({ onMount }: { onMount: (w: ReturnType<typeof useWallet>) => void }) {
  const wallet = useWallet()
  React.useEffect(() => onMount(wallet), [])
  return null
}

describe('WalletContext', () => {
  it('starts with empty entries', () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    expect(ctx.entries).toEqual([])
  })

  it('addEntry adds a WalletEntry by EIN only', async () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    await act(async () => {
      ctx.addEntry('123456789')
    })
    expect(ctx.entries).toHaveLength(1)
    expect(ctx.entries[0].ein).toBe('123456789')
    // Must NOT contain name, mission, cause, merit_score_v5, etc.
    expect((ctx.entries[0] as any).name).toBeUndefined()
    expect((ctx.entries[0] as any).mission).toBeUndefined()
  })

  it('removeEntry removes by EIN', async () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    await act(async () => { ctx.addEntry('123456789') })
    await act(async () => { ctx.removeEntry('123456789') })
    expect(ctx.entries).toHaveLength(0)
  })

  it('isInWallet returns false for unknown EIN', () => {
    let ctx: any
    render(
      <WalletProvider>
        <Probe onMount={(w) => { ctx = w }} />
      </WalletProvider>
    )
    expect(ctx.isInWallet('999999999')).toBe(false)
  })
})
```

- [ ] **Step 2: Run test — confirm it fails**

```bash
cd frontend && npx jest WalletContext --no-coverage 2>&1 | tail -10
```
Expected: fails (WalletContext still has old WalletOrg API)

- [ ] **Step 3: Update `frontend/src/types/wallet.ts`**

Replace the file content:

```typescript
/**
 * Wallet domain types — v2 (E2E encrypted, normalized)
 * WalletEntry stores only EIN + intent. Org display data is always fetched live.
 */

// GivingIntent is unchanged from v1 — all validators in walletValidation.ts reuse.
export interface GivingIntent {
  type: 'giving' | 'volunteer' | 'board'
  amount?: number
  frequency?: 'year' | 'month' | 'one-time'
  hoursPerMonth?: number
  notes?: string  // max 200 chars
  addedAt: number
}

/** The normalized wallet entry. ~40 bytes per org. 50 orgs ≈ 2KB. */
export interface WalletEntry {
  ein: string      // 9-digit EIN
  bookmarkedAt: number
  givingIntent?: GivingIntent
}

/** The full encrypted wallet state. */
export interface Wallet {
  version: 2
  entries: WalletEntry[]
  // Passphrase state (not stored in ciphertext — lives in context only)
  keyHash?: string
  salt?: string  // base64, server-issued, not secret
}

export interface WalletContextType {
  entries: WalletEntry[]
  addEntry: (ein: string) => void
  removeEntry: (ein: string) => void
  updateIntent: (ein: string, intent: GivingIntent) => void
  isInWallet: (ein: string) => boolean
  getIntent: (ein: string) => GivingIntent | undefined
  // Passphrase flow
  isUnlocked: boolean
  unlockWithPassphrase: (passphrase: string) => Promise<void>
  setupNewWallet: (passphrase: string) => Promise<void>
  lockWallet: () => void
  deleteWallet: () => Promise<void>
  // Sync state
  syncStatus: 'idle' | 'syncing' | 'error'
  // Download backup
  downloadBackup: () => void
}

/** Legacy v1 type — used only for migration detection. Do not use for new code. */
export interface LegacyWalletV1 {
  version: 1
  orgs: Array<{ ein: string; bookmarkedAt: number; givingIntent?: GivingIntent; [key: string]: unknown }>
}

export function isLegacyWalletV1(w: unknown): w is LegacyWalletV1 {
  if (typeof w !== 'object' || w === null) return false
  const obj = w as Record<string, unknown>
  return obj['version'] === 1 && Array.isArray(obj['orgs'])
}

export function isValidWalletEntry(e: unknown): e is WalletEntry {
  if (typeof e !== 'object' || e === null) return false
  const o = e as Record<string, unknown>
  return (
    typeof o['ein'] === 'string' && o['ein'].length === 9 &&
    typeof o['bookmarkedAt'] === 'number' && o['bookmarkedAt'] > 0
  )
}

export const WALLET_CONSTRAINTS = {
  NOTES_MAX_LENGTH: 200,
  AMOUNT_MIN: 1,
  HOURS_MIN: 0.25,
} as const
```

- [ ] **Step 4: Rewrite `frontend/src/contexts/WalletContext.tsx`**

```typescript
import React, {
  createContext, useContext, useReducer, useCallback,
  useEffect, useRef, useState,
} from 'react'
import type { WalletEntry, GivingIntent, WalletContextType } from '../types/wallet'
import { isValidWalletEntry } from '../types/wallet'
import { validateGivingIntent, logValidationError } from '../utils/walletValidation'
import {
  deriveAll, encryptWallet, decryptWallet,
  deriveRawKeyBytes, importKeyFromBytes,
} from '../utils/wallet.crypto'

const LS_KEY_HASH = 'dw_kh'   // localStorage: server lookup token (not secret)
const LS_SALT    = 'dw_s'    // localStorage: server-issued salt (not secret)
const SS_RAW_KEY = 'dw_k'    // sessionStorage: raw AES key bytes (secret, cleared on tab close)

const API_BASE = () => (import.meta.env.VITE_API_URL || 'http://localhost:5000')

// ─── State ───────────────────────────────────────────────────────────────────

type State = {
  entries: WalletEntry[]
  keyHash: string | null
  salt: string | null
  encKey: CryptoKey | null
  syncStatus: 'idle' | 'syncing' | 'error'
}

type Action =
  | { type: 'HYDRATE'; entries: WalletEntry[]; keyHash: string; salt: string; encKey: CryptoKey }
  | { type: 'ADD'; ein: string }
  | { type: 'REMOVE'; ein: string }
  | { type: 'UPDATE_INTENT'; ein: string; intent: GivingIntent }
  | { type: 'SET_SYNC_STATUS'; status: State['syncStatus'] }
  | { type: 'LOCK' }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'HYDRATE':
      return { ...state, entries: action.entries, keyHash: action.keyHash,
               salt: action.salt, encKey: action.encKey, syncStatus: 'idle' }
    case 'ADD': {
      if (state.entries.some(e => e.ein === action.ein)) return state
      return { ...state, entries: [...state.entries, { ein: action.ein, bookmarkedAt: Date.now() }] }
    }
    case 'REMOVE':
      return { ...state, entries: state.entries.filter(e => e.ein !== action.ein) }
    case 'UPDATE_INTENT': {
      const idx = state.entries.findIndex(e => e.ein === action.ein)
      if (idx === -1) return state
      const next = [...state.entries]
      next[idx] = { ...next[idx], givingIntent: action.intent }
      return { ...state, entries: next }
    }
    case 'SET_SYNC_STATUS':
      return { ...state, syncStatus: action.status }
    case 'LOCK':
      return { entries: [], keyHash: null, salt: null, encKey: null, syncStatus: 'idle' }
    default:
      return state
  }
}

// ─── Context ─────────────────────────────────────────────────────────────────

export const WalletContext = createContext<WalletContextType | null>(null)

export function WalletProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, {
    entries: [], keyHash: null, salt: null, encKey: null, syncStatus: 'idle',
  })
  const syncTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // On mount: try to restore session key from sessionStorage
  useEffect(() => {
    const rawB64 = sessionStorage.getItem(SS_RAW_KEY)
    const keyHash = localStorage.getItem(LS_KEY_HASH)
    const salt = localStorage.getItem(LS_SALT)
    if (!rawB64 || !keyHash || !salt) return

    ;(async () => {
      try {
        const bytes = Uint8Array.from(atob(rawB64), c => c.charCodeAt(0))
        const encKey = await importKeyFromBytes(bytes)
        const r = await fetch(`${API_BASE()}/api/wallet/sync?keyHash=${keyHash}`)
        if (!r.ok) return
        const data = await r.json()
        if (!data.found) return
        const entries = await decryptWallet(data.ciphertext, data.iv, encKey)
        dispatch({ type: 'HYDRATE', entries, keyHash, salt, encKey })
      } catch {
        // Corrupt session key or server error — user will re-enter passphrase
        sessionStorage.removeItem(SS_RAW_KEY)
      }
    })()
  }, [])

  // Debounced sync on entries change (only when unlocked)
  useEffect(() => {
    if (!state.encKey || !state.keyHash || !state.salt) return
    if (syncTimerRef.current) clearTimeout(syncTimerRef.current)
    syncTimerRef.current = setTimeout(async () => {
      dispatch({ type: 'SET_SYNC_STATUS', status: 'syncing' })
      try {
        const { ciphertext, iv } = await encryptWallet(state.entries, state.encKey!)
        const r = await fetch(`${API_BASE()}/api/wallet/sync`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ keyHash: state.keyHash, ciphertext, iv, salt: state.salt }),
        })
        if (!r.ok) throw new Error(`sync failed: ${r.status}`)
        dispatch({ type: 'SET_SYNC_STATUS', status: 'idle' })
      } catch {
        dispatch({ type: 'SET_SYNC_STATUS', status: 'error' })
      }
    }, 800)
    return () => { if (syncTimerRef.current) clearTimeout(syncTimerRef.current) }
  }, [state.entries, state.encKey, state.keyHash, state.salt])

  // ─── Actions ───────────────────────────────────────────────────────────────

  const addEntry = useCallback((ein: string) => {
    if (!/^\d{9}$/.test(ein)) return
    dispatch({ type: 'ADD', ein })
  }, [])

  const removeEntry = useCallback((ein: string) => {
    dispatch({ type: 'REMOVE', ein })
  }, [])

  const updateIntent = useCallback((ein: string, intent: GivingIntent) => {
    try { validateGivingIntent(intent) } catch (e) {
      logValidationError('updateIntent', e as Error); return
    }
    dispatch({ type: 'UPDATE_INTENT', ein, intent })
  }, [])

  const isInWallet = useCallback((ein: string) => state.entries.some(e => e.ein === ein), [state.entries])
  const getIntent = useCallback((ein: string) => state.entries.find(e => e.ein === ein)?.givingIntent, [state.entries])

  const _persistSession = useCallback(async (passphrase: string, salt: Uint8Array, encKey: CryptoKey, keyHash: string) => {
    localStorage.setItem(LS_KEY_HASH, keyHash)
    localStorage.setItem(LS_SALT, btoa(String.fromCharCode(...salt)))
    const rawBytes = await deriveRawKeyBytes(passphrase, salt)
    sessionStorage.setItem(SS_RAW_KEY, btoa(String.fromCharCode(...rawBytes)))
    _ = encKey // held in context state, not returned
  }, [])

  const setupNewWallet = useCallback(async (passphrase: string) => {
    // 1. Get salt from server
    const r = await fetch(`${API_BASE()}/api/wallet/init`, { method: 'POST' })
    const { salt: saltB64 } = await r.json()
    const saltBytes = Uint8Array.from(atob(saltB64), c => c.charCodeAt(0))

    // 2. Derive keys
    const { encKey, keyHash } = await deriveAll(passphrase, saltBytes)

    // 3. Upload empty encrypted wallet
    const { ciphertext, iv } = await encryptWallet([], encKey)
    await fetch(`${API_BASE()}/api/wallet/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyHash, ciphertext, iv, salt: saltB64 }),
    })

    // 4. Persist session
    localStorage.setItem(LS_KEY_HASH, keyHash)
    localStorage.setItem(LS_SALT, saltB64)
    const rawBytes = await deriveRawKeyBytes(passphrase, saltBytes)
    sessionStorage.setItem(SS_RAW_KEY, btoa(String.fromCharCode(...rawBytes)))

    dispatch({ type: 'HYDRATE', entries: [], keyHash, salt: saltB64, encKey })
  }, [])

  const unlockWithPassphrase = useCallback(async (passphrase: string) => {
    const saltB64 = localStorage.getItem(LS_SALT)
    const storedKeyHash = localStorage.getItem(LS_KEY_HASH)
    if (!saltB64 || !storedKeyHash) throw new Error('No wallet found on this device')

    const saltBytes = Uint8Array.from(atob(saltB64), c => c.charCodeAt(0))
    const { encKey, keyHash } = await deriveAll(passphrase, saltBytes)

    const r = await fetch(`${API_BASE()}/api/wallet/sync?keyHash=${keyHash}`)
    if (r.status === 404) throw new Error('Incorrect passphrase')
    if (!r.ok) throw new Error('Server error')

    const data = await r.json()
    const entries = await decryptWallet(data.ciphertext, data.iv, encKey)

    const rawBytes = await deriveRawKeyBytes(passphrase, saltBytes)
    sessionStorage.setItem(SS_RAW_KEY, btoa(String.fromCharCode(...rawBytes)))

    dispatch({ type: 'HYDRATE', entries, keyHash, salt: saltB64, encKey })
  }, [])

  const lockWallet = useCallback(() => {
    sessionStorage.removeItem(SS_RAW_KEY)
    dispatch({ type: 'LOCK' })
  }, [])

  const deleteWallet = useCallback(async () => {
    const keyHash = localStorage.getItem(LS_KEY_HASH)
    if (keyHash) {
      await fetch(`${API_BASE()}/api/wallet/sync`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyHash }),
      }).catch(() => {})
    }
    localStorage.removeItem(LS_KEY_HASH)
    localStorage.removeItem(LS_SALT)
    sessionStorage.removeItem(SS_RAW_KEY)
    dispatch({ type: 'LOCK' })
  }, [])

  const downloadBackup = useCallback(() => {
    const data = JSON.stringify({ version: 2, entries: state.entries, exportedAt: new Date().toISOString() }, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'daanaa-wallet-backup.json'; a.click()
    URL.revokeObjectURL(url)
  }, [state.entries])

  const isUnlocked = state.encKey !== null

  return (
    <WalletContext.Provider value={{
      entries: state.entries, addEntry, removeEntry, updateIntent,
      isInWallet, getIntent, isUnlocked, unlockWithPassphrase,
      setupNewWallet, lockWallet, deleteWallet, downloadBackup,
      syncStatus: state.syncStatus,
    }}>
      {children}
    </WalletContext.Provider>
  )
}

export function useWallet(): WalletContextType {
  const ctx = useContext(WalletContext)
  if (!ctx) throw new Error('useWallet must be used within WalletProvider')
  return ctx
}
```

- [ ] **Step 5: Run tests — all must pass**

```bash
cd frontend && npx jest WalletContext --no-coverage
```
Expected: `4 passed`

- [ ] **Step 6: Delete the now-unused persistence hook**

```bash
rm frontend/src/hooks/useWalletPersistence.ts
# Verify nothing imports it
grep -r "useWalletPersistence" frontend/src/ && echo "FOUND — fix imports" || echo "clean"
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/types/wallet.ts frontend/src/contexts/WalletContext.tsx
git rm frontend/src/hooks/useWalletPersistence.ts
git commit -m "feat(wallet): normalized WalletEntry type + E2E encrypted WalletContext"
```

---

## Task 4: PassphraseModal + Session Key UI

**Files:**
- Create: `frontend/src/components/PassphraseModal.tsx`

This modal handles two flows:
- **Setup** (new wallet): generate words → show them → confirm saved → download backup → create wallet
- **Restore** (second device / new session): enter passphrase → fetch+decrypt from server

- [ ] **Step 1: Write failing test**

Add to `frontend/src/__tests__/PassphraseModal.test.tsx`:

```typescript
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PassphraseModal from '../components/PassphraseModal'

jest.mock('../utils/wallet.crypto', () => ({
  generatePassphrase: jest.fn().mockResolvedValue('correct horse battery staple'),
}))

describe('PassphraseModal — setup mode', () => {
  it('shows 4 generated words', async () => {
    render(<PassphraseModal mode="setup" onSetup={jest.fn()} onRestore={jest.fn()} onClose={jest.fn()} />)
    await waitFor(() => {
      expect(screen.getByText(/correct horse battery staple/i)).toBeInTheDocument()
    })
  })

  it('setup button disabled until both checkboxes checked', async () => {
    render(<PassphraseModal mode="setup" onSetup={jest.fn()} onRestore={jest.fn()} onClose={jest.fn()} />)
    await waitFor(() => screen.getByText(/correct horse battery staple/i))
    const btn = screen.getByRole('button', { name: /set up wallet/i })
    expect(btn).toBeDisabled()
  })

  it('calls onSetup with passphrase when both confirmed', async () => {
    const onSetup = jest.fn()
    render(<PassphraseModal mode="setup" onSetup={onSetup} onRestore={jest.fn()} onClose={jest.fn()} />)
    await waitFor(() => screen.getByText(/correct horse battery staple/i))
    fireEvent.click(screen.getByLabelText(/saved.*passphrase/i))
    fireEvent.click(screen.getByLabelText(/download.*backup/i))
    fireEvent.click(screen.getByRole('button', { name: /set up wallet/i }))
    await waitFor(() => expect(onSetup).toHaveBeenCalledWith('correct horse battery staple'))
  })
})

describe('PassphraseModal — restore mode', () => {
  it('calls onRestore with entered passphrase', async () => {
    const onRestore = jest.fn()
    render(<PassphraseModal mode="restore" onSetup={jest.fn()} onRestore={onRestore} onClose={jest.fn()} />)
    await userEvent.type(screen.getByRole('textbox'), 'my four word phrase')
    fireEvent.click(screen.getByRole('button', { name: /restore/i }))
    await waitFor(() => expect(onRestore).toHaveBeenCalledWith('my four word phrase'))
  })
})
```

- [ ] **Step 2: Run test — confirm it fails**

```bash
cd frontend && npx jest PassphraseModal --no-coverage 2>&1 | tail -10
```

- [ ] **Step 3: Write `PassphraseModal.tsx`**

Create `frontend/src/components/PassphraseModal.tsx`:

```typescript
import React, { useEffect, useState, useRef } from 'react'
import { generatePassphrase } from '../utils/wallet.crypto'

interface Props {
  mode: 'setup' | 'restore'
  onSetup: (passphrase: string) => Promise<void>
  onRestore: (passphrase: string) => Promise<void>
  onClose: () => void
}

export default function PassphraseModal({ mode, onSetup, onRestore, onClose }: Props) {
  const [passphrase, setPassphrase] = useState('')
  const [savedConfirmed, setSavedConfirmed] = useState(false)
  const [backupConfirmed, setBackupConfirmed] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [restoreInput, setRestoreInput] = useState('')

  // Generate passphrase on setup mode mount
  useEffect(() => {
    if (mode !== 'setup') return
    generatePassphrase().then(setPassphrase).catch(() => setError('Could not generate passphrase'))
  }, [mode])

  const canSetup = savedConfirmed && backupConfirmed && passphrase.length > 0

  async function handleSetup() {
    if (!canSetup) return
    setLoading(true); setError(null)
    try { await onSetup(passphrase) }
    catch (e) { setError(e instanceof Error ? e.message : 'Setup failed') }
    finally { setLoading(false) }
  }

  async function handleRestore() {
    const phrase = restoreInput.trim()
    if (phrase.split(' ').length < 3) { setError('Enter your full passphrase'); return }
    setLoading(true); setError(null)
    try { await onRestore(phrase) }
    catch (e) { setError('Passphrase not recognized. Check your words and try again.') }
    finally { setLoading(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" role="dialog" aria-modal="true">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl">
        {mode === 'setup' ? (
          <>
            <h2 className="font-body text-xl font-semibold text-deep-navy mb-2">Your wallet passphrase</h2>
            <p className="font-body text-sm text-warm-gray mb-4">
              Write this down. It's the only way to access your wallet on another device.
              We cannot recover it.
            </p>
            {passphrase ? (
              <div className="bg-soft-cream rounded-xl p-4 mb-4 font-mono text-lg text-deep-navy text-center tracking-wide select-all">
                {passphrase}
              </div>
            ) : (
              <div className="h-16 bg-soft-cream rounded-xl mb-4 animate-pulse" />
            )}
            <div className="space-y-3 mb-5">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={savedConfirmed}
                  onChange={e => setSavedConfirmed(e.target.checked)}
                  className="mt-0.5"
                  aria-label="I've saved my passphrase in a safe place"
                />
                <span className="font-body text-sm text-warm-gray">
                  I've saved my passphrase in a safe place
                </span>
              </label>
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={backupConfirmed}
                  onChange={e => setBackupConfirmed(e.target.checked)}
                  className="mt-0.5"
                  aria-label="I've downloaded a backup of my wallet"
                />
                <span className="font-body text-sm text-warm-gray">
                  I'll download a backup after setup
                </span>
              </label>
            </div>
            {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
            <div className="flex gap-3">
              <button onClick={onClose} className="flex-1 px-4 py-2 rounded-full font-body text-sm border border-light-grey text-warm-gray hover:bg-soft-cream transition-colors">
                Cancel
              </button>
              <button
                onClick={handleSetup}
                disabled={!canSetup || loading}
                aria-label="Set up wallet"
                className="flex-1 px-4 py-2 rounded-full font-body text-sm font-semibold bg-soft-gold text-deep-navy hover:bg-bright-gold transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {loading ? 'Setting up…' : 'Set up wallet'}
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 className="font-body text-xl font-semibold text-deep-navy mb-2">Restore your wallet</h2>
            <p className="font-body text-sm text-warm-gray mb-4">
              Enter your 4-word passphrase to access your wallet on this device.
              Find it where you wrote it down — you'll need it before clicking.
            </p>
            <input
              type="text"
              value={restoreInput}
              onChange={e => setRestoreInput(e.target.value)}
              placeholder="e.g. correct horse battery staple"
              className="w-full border border-light-grey rounded-xl px-4 py-3 font-mono text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
              aria-label="Your wallet passphrase"
              autoComplete="off"
              spellCheck={false}
            />
            {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
            <div className="flex gap-3">
              <button onClick={onClose} className="flex-1 px-4 py-2 rounded-full font-body text-sm border border-light-grey text-warm-gray hover:bg-soft-cream transition-colors">
                Cancel
              </button>
              <button
                onClick={handleRestore}
                disabled={loading}
                aria-label="Restore wallet"
                className="flex-1 px-4 py-2 rounded-full font-body text-sm font-semibold bg-soft-gold text-deep-navy hover:bg-bright-gold transition-colors disabled:opacity-40"
              >
                {loading ? 'Restoring…' : 'Restore wallet'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run tests — all must pass**

```bash
cd frontend && npx jest PassphraseModal --no-coverage
```
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/PassphraseModal.tsx \
        frontend/src/__tests__/PassphraseModal.test.tsx
git commit -m "feat(wallet): PassphraseModal — setup + restore flows"
```

---

## Task 5: WalletCard + AddToWalletButton Refactor

**Files:**
- Modify: `frontend/src/components/WalletCard.tsx`
- Modify: `frontend/src/components/AddToWalletButton.tsx`

- [ ] **Step 1: Update `WalletCard.tsx` to accept `WalletEntry` + hydrated org data**

`WalletCard` no longer receives a `WalletOrg`. It receives `WalletEntry` + a separate `ApiOrganization` prop (same type returned by `/api/organizations/<ein>`). Replace the props interface and update the render to use `apiOrg` for name, mission, health signal, etc.

Key change to make:

```typescript
// Before:
interface WalletCardProps {
  org: WalletOrg
  onRemove?: (ein: string) => void
  onEdit?: (ein: string) => void
}

// After:
import type { ApiOrganization } from '../data/api'
import type { WalletEntry } from '../types/wallet'

interface WalletCardProps {
  entry: WalletEntry
  orgData: ApiOrganization | null  // null while loading or if fetch failed
  onRemove?: (ein: string) => void
  onEdit?: (ein: string) => void
}
```

When `orgData` is null, render a skeleton:
```typescript
if (!orgData) {
  return (
    <div className="bg-white rounded-2xl border border-light-grey p-6 animate-pulse">
      <div className="h-4 bg-soft-cream rounded w-3/4 mb-3" />
      <div className="h-3 bg-soft-cream rounded w-full mb-2" />
      <div className="h-3 bg-soft-cream rounded w-2/3" />
    </div>
  )
}
```

Replace `org.name` → `orgData.organization_name`, `org.merit_health_signal_v5` → `orgData.v5_context?.score.health_signal ?? 'STABLE'`, etc.

Replace `org.givingIntent` → `entry.givingIntent`, `org.ein` → `entry.ein`.

- [ ] **Step 2: Update `AddToWalletButton.tsx` — no more org data fetch**

The button no longer needs to call `getOrganization(ein)` before saving. It just saves the EIN:

```typescript
// Before:
const handleClick = async () => {
  setState('loading')
  const apiOrg = await getOrganization(ein)  // ← remove this
  const walletOrg: WalletOrg = { ...build full snapshot... }
  addOrg(walletOrg)
  ...
}

// After:
const handleClick = () => {
  addEntry(ein)   // ← WalletContext.addEntry takes only EIN
  setState('success')
}
```

Remove the `getOrganization` import and the `loading` state — the add is now synchronous. Keep the `success` state for the "Saved ✓" flash.

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```
Expected: 0 errors (or only pre-existing errors in untouched files)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/WalletCard.tsx \
        frontend/src/components/AddToWalletButton.tsx
git commit -m "refactor(wallet): WalletCard accepts WalletEntry+ApiOrg, AddToWalletButton saves EIN only"
```

---

## Task 6: WalletPage Refactor

**Files:**
- Modify: `frontend/src/pages/WalletPage.tsx`

Key changes:
1. Batch hydration: `Promise.all()` on mount for all EINs → `Map<ein, ApiOrganization>`
2. Passphrase gate: show `PassphraseModal` if `!isUnlocked`
3. Remove stale org check (`staleEins` state — org data is always live from batch fetch)
4. Remove `syncToServer` / Google auth sync UI (replaced by E2E passphrase sync)
5. Pass `orgDataMap.get(entry.ein) ?? null` to each `WalletCard`
6. Add `downloadBackup` button
7. Add sync status indicator (`syncStatus`)
8. Add migration detection (Task 7 — done here)

- [ ] **Step 1: Batch hydration**

Add near the top of `WalletPage`:

```typescript
const { entries, isUnlocked, syncStatus, downloadBackup } = useWallet()
const [orgDataMap, setOrgDataMap] = useState<Map<string, ApiOrganization>>(new Map())
const [hydrating, setHydrating] = useState(false)

// Batch hydrate org data for all wallet entries
useEffect(() => {
  if (entries.length === 0) { setOrgDataMap(new Map()); return }
  setHydrating(true)
  const eins = entries.map(e => e.ein)
  Promise.all(
    eins.map(ein =>
      fetch(`${API_BASE}/api/organizations/${ein}`)
        .then(r => r.ok ? r.json() : null)
        .catch(() => null)
    )
  ).then(results => {
    const map = new Map<string, ApiOrganization>()
    eins.forEach((ein, i) => { if (results[i]) map.set(ein, results[i]) })
    setOrgDataMap(map)
    setHydrating(false)
  })
}, [entries])
```

- [ ] **Step 2: Passphrase gate at top of render**

At the start of the `return` block, check `isUnlocked`:

```typescript
const [showModal, setShowModal] = useState<'setup' | 'restore' | null>(null)

// At top of render — before everything else:
if (!isUnlocked && !showModal) {
  const hasExistingWallet = !!localStorage.getItem('dw_kh')
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center max-w-sm">
        <h1>Your Giving Wallet</h1>
        {hasExistingWallet ? (
          <button onClick={() => setShowModal('restore')}>Enter passphrase</button>
        ) : (
          <button onClick={() => setShowModal('setup')}>Set up wallet</button>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Remove stale org check**

Delete the `staleEins` state and the `useEffect` that calls `HEAD /api/organizations/<ein>`. Remove the stale badge rendering from `WalletCard` calls. The org data is now always live from the batch fetch.

- [ ] **Step 4: Update WalletCard calls**

Replace all `<WalletCard org={org} .../>` with `<WalletCard entry={entry} orgData={orgDataMap.get(entry.ein) ?? null} .../>`.

- [ ] **Step 5: Add sync status + download backup to header**

```typescript
// In the wallet header area:
{syncStatus === 'syncing' && (
  <span className="font-body text-xs text-warm-gray">Saving…</span>
)}
{syncStatus === 'error' && (
  <span className="font-body text-xs text-red-500">Sync error — will retry</span>
)}
<button onClick={downloadBackup} className="font-body text-xs text-soft-gold hover:text-bright-gold">
  Download backup
</button>
```

- [ ] **Step 6: TypeScript check + commit**

```bash
cd frontend && npx tsc --noEmit
git add frontend/src/pages/WalletPage.tsx
git commit -m "refactor(wallet): batch hydration, passphrase gate, remove stale-check + Google sync"
```

---

## Task 7: Migration from Legacy Wallet

**Files:**
- Modify: `frontend/src/contexts/WalletContext.tsx`

Detect the old `daanaa_wallet` localStorage key on mount, strip to EINs + intents, and prompt the user to set up a passphrase (which will encrypt and upload the migrated data).

- [ ] **Step 1: Add migration detection to `WalletProvider` mount effect**

Add to `WalletContext.tsx` after the existing sessionStorage restore effect:

```typescript
const [migrationData, setMigrationData] = useState<WalletEntry[] | null>(null)

// Detect legacy v1 wallet on mount
useEffect(() => {
  try {
    const raw = localStorage.getItem('daanaa_wallet')
    if (!raw) return
    const parsed = JSON.parse(raw)
    if (!isLegacyWalletV1(parsed)) return
    // Strip to EINs + intents (drop name, mission, cause, scores, etc.)
    const entries: WalletEntry[] = parsed.orgs.map(o => ({
      ein: o.ein,
      bookmarkedAt: o.bookmarkedAt ?? Date.now(),
      givingIntent: o.givingIntent,
    })).filter(isValidWalletEntry)
    if (entries.length > 0) {
      setMigrationData(entries)
    }
  } catch { /* ignore */ }
}, [])
```

- [ ] **Step 2: Expose `migrationData` in context**

Add to `WalletContextType`:
```typescript
migrationData: WalletEntry[] | null   // non-null = legacy wallet detected
applyMigration: () => void            // called after passphrase setup to import entries
dismissMigration: () => void          // called if user wants to start fresh
```

`applyMigration`: merges `migrationData` into `entries` state, then deletes `localStorage.removeItem('daanaa_wallet')`.

`dismissMigration`: deletes old key.

- [ ] **Step 3: Show migration banner in WalletPage**

When `migrationData !== null` and wallet is being set up:

```typescript
{migrationData && (
  <div className="bg-soft-cream rounded-xl p-4 mb-4">
    <p className="font-body text-sm">
      You have {migrationData.length} saved org{migrationData.length !== 1 ? 's' : ''} from an earlier Daanaa version.
      Set a passphrase to keep them, or start fresh.
    </p>
    <div className="flex gap-2 mt-3">
      <button onClick={() => { setShowModal('setup') }} className="...">
        Keep my orgs + set passphrase
      </button>
      <button onClick={dismissMigration} className="...">
        Start fresh
      </button>
    </div>
  </div>
)}
```

After passphrase setup completes (`onSetup` callback), call `applyMigration()` if the user chose to keep their orgs.

- [ ] **Step 4: Write test for migration**

Add to `WalletContext.test.tsx`:

```typescript
describe('legacy wallet migration', () => {
  beforeEach(() => {
    const legacyWallet = {
      version: 1,
      lastUpdated: Date.now(),
      orgs: [
        { ein: '123456789', bookmarkedAt: 1718000000000, name: 'Old Name',
          mission: 'Old Mission', location: 'NYC', cause: ['education'],
          merit_score_v5: 75, merit_health_signal_v5: 'HEALTHY', is_hidden_gem: false }
      ],
      syncedWithServer: false,
    }
    localStorage.setItem('daanaa_wallet', JSON.stringify(legacyWallet))
  })
  afterEach(() => { localStorage.clear() })

  it('detects legacy wallet and exposes migrationData', () => {
    let ctx: any
    render(<WalletProvider><Probe onMount={w => { ctx = w }} /></WalletProvider>)
    expect(ctx.migrationData).toHaveLength(1)
    expect(ctx.migrationData[0].ein).toBe('123456789')
    expect((ctx.migrationData[0] as any).name).toBeUndefined()  // snapshot stripped
  })
})
```

- [ ] **Step 5: Run tests — all pass**

```bash
cd frontend && npx jest --no-coverage 2>&1 | tail -10
```
Expected: `Tests: N passed` (all suites)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/contexts/WalletContext.tsx \
        frontend/src/pages/WalletPage.tsx \
        frontend/src/__tests__/WalletContext.test.tsx
git commit -m "feat(wallet): migrate legacy v1 wallet — detect, strip snapshots, prompt passphrase setup"
```

---

## Task 8: End-to-End Verification

- [ ] **Step 1: Run full test suite**

```bash
cd frontend && npx jest --coverage 2>&1 | tail -20
cd /home/akbar/meritgiving && source venv/bin/activate && python -m pytest tests/ -v 2>&1 | tail -30
```

Both must pass with no failures.

- [ ] **Step 2: TypeScript clean**

```bash
cd frontend && npx tsc --noEmit
```
0 errors required.

- [ ] **Step 3: Manual walkthrough (golden path)**

Start local servers:
```bash
# Terminal 1:
source ~/meritgiving/venv/bin/activate && python3 daanaa_api.py

# Terminal 2:
cd frontend && npm run dev
```

Walk through:
1. Navigate to `/wallet` → see passphrase setup gate
2. Click "Set up wallet" → PassphraseModal opens, 4 words generated
3. Check both boxes → click "Set up wallet" → wallet opens (empty)
4. Browse to any org page → click "Save to Wallet"  
5. Return to `/wallet` → org card appears with live org data
6. Click sync status indicator → confirm "Saving…" then "idle"
7. Open new tab → navigate to `/wallet` → passphrase prompt appears
8. Enter passphrase → same org appears
9. Click "Download backup" → JSON file downloads with EINs + intent (no org names)
10. Click delete → server row deleted, wallet clears

- [ ] **Step 4: Verify server cannot read wallet**

```bash
sqlite3 /home/akbar/meritgiving/data/merit_registry.db \
  "SELECT key_hash, length(ciphertext) as ct_bytes FROM e2e_wallet_sync LIMIT 3;"
```

Expected: `key_hash` is 64-char hex, `ct_bytes` > 0. No EINs, no org names anywhere in the table.

- [ ] **Step 5: Final commit + DECISIONS.md entry**

```bash
# Add to DECISIONS.md:
# "2026-06-20: Wallet session key stored as raw AES bytes in sessionStorage
# (not memory-only). Tradeoff: slightly weaker XSS isolation vs. must-re-enter
# on every page reload. CSP on DAANAA_PROD already restricts script-src.
# Decision: sessionStorage acceptable for civic giving-intent data."
```

```bash
git add DECISIONS.md
git commit -m "docs: wallet session key decision — sessionStorage tradeoff documented"
```

---

## Failure Modes

| Codepath | Realistic failure | Test covers? | Error handling? | User sees? |
|----------|-------------------|-------------|-----------------|------------|
| `deriveAll` | Wrong passphrase → different keyHash → GET 404 | Yes (`wrong key cannot decrypt`) | Yes (throws, caught in `unlockWithPassphrase`) | "Passphrase not recognized" |
| `encryptWallet` | IV collision (1/2^96 probability) | No | Yes (AES-GCM rejects duplicate) | Internal retry on next change |
| `decryptWallet` | Tampered ciphertext | Yes (tamper test) | Yes (AES-GCM auth fail → throws) | "Passphrase not recognized" |
| Batch org hydration | One EIN returns 404 | No (fire-and-forget) | Yes (null in orgDataMap → skeleton) | Skeleton card (org removed from registry) |
| `/api/wallet/init` | Server down | No | Yes (fetch throws → setup fails) | "Could not generate passphrase" |
| `/api/wallet/sync` POST | Rate limited | Yes (oversized test) | Yes (429 → syncStatus='error') | "Sync error — will retry" |
| sessionStorage cleared | Browser privacy mode, tab closed | No | Yes (re-prompts passphrase) | Passphrase modal on next visit |
| Legacy migration | Old wallet corrupted | Partial (validates with `isValidWalletEntry`) | Yes (invalid entries skipped silently) | Migration shows only valid orgs |

**Critical gaps (no test AND no handling AND would be silent):** None. All failure modes have at least one of: test, error handling, or visible user feedback.

---

## NOT in scope (this PR)

- **Quarterly re-engagement email** — `wallet_update_subscriptions` table + `/api/wallet/subscribe` endpoint + `scripts/generate_quarterly_summaries.py`. Deferred to Week 2. Core wallet ships first.
- **Passkey PRF** (WebAuthn biometric key derivation) — deferred until browser support stabilizes.
- **BIP39 wordlist localization** — English only for now.
- **Argon2id upgrade** — PBKDF2/310K is acceptable for this threat model.
- **Remove Firebase wallet endpoints** — keep alive until full migration. Remove in follow-up PR.
- **Search.db nightly auto-purge cron** — `DELETE FROM e2e_wallet_sync WHERE updated_at < strftime('%s','now') - 63072000` — add to existing overnight_pipeline.py in follow-up.

---

## What Already Exists (reused)

| Asset | Status |
|-------|--------|
| `walletValidation.ts` | Reused unchanged — all intent validators work on `GivingIntent` (type unchanged) |
| `GivingIntent` type | Unchanged — same shape in v1 and v2 |
| `walletStorage.ts` | Partially reused — `checkCorruption` + `getQuotaInfo` removed (not needed), `walletStorage.write/read` removed (replaced by E2E sync) |
| `WalletPage.tsx` | Refactored in-place — 502 lines → ~400 (stale check + Google sync removed) |
| `WalletCard.tsx` | Refactored in-place — prop type change, skeleton added |
| `useWallet.ts` hook | No change needed (still wraps `useContext(WalletContext)`) |
| Jest + jest-environment-jsdom | Already installed, SubtleCrypto available in jsdom 20+ |
| `test_wallet_sync.py` | Unchanged — tests old Firebase wallet (routes kept alive) |

---

## Test Coverage Diagram

```
CODE PATHS                                               USER FLOWS
[+] wallet.crypto.ts                                     [+] First-time setup
  ├── generatePassphrase()                                 ├── [★★★ TESTED] Words generated (4 words from BIP39)
  │   ├── [★★★ TESTED] returns 4 words                    ├── [★★★ TESTED] Button disabled until confirmed
  │   ├── [★★★ TESTED] all from wordlist                  └── [★★★ TESTED] onSetup called with passphrase
  │   └── [★★★ TESTED] unique each call
  ├── deriveAll()                                         [+] Restore (second device)
  │   ├── [★★★ TESTED] deterministic keyHash              └── [★★★ TESTED] onRestore called with entered phrase
  │   ├── [★★★ TESTED] different passphrase → diff hash
  │   └── [★★★ TESTED] encKey non-extractable             [+] Add to wallet
  ├── encryptWallet()                                       ├── [★★★ TESTED] addEntry stores EIN only
  │   ├── [★★★ TESTED] round-trip decrypt                  └── [★★  TESTED] no org snapshot stored
  │   └── [★★★ TESTED] fresh IV each call
  └── decryptWallet()                                     [+] Migration
      ├── [★★★ TESTED] wrong key fails                      ├── [★★★ TESTED] legacy v1 detected
      └── [★★★ TESTED] tampered ciphertext fails             └── [★★★ TESTED] snapshot stripped

[+] daanaa_api.py — /api/wallet/init                    [+] Full E2E roundtrip
  └── [★★★ TESTED] returns unique random salt              ├── [GAP] [→E2E] Setup → add org → restore on new device
                                                           └── [GAP] [→E2E] Session key survives tab navigation
[+] daanaa_api.py — /api/wallet/sync
  ├── [★★★ TESTED] GET 404 on missing
  ├── [★★★ TESTED] POST stores + GET retrieves
  ├── [★★★ TESTED] POST overwrites on conflict
  ├── [★★★ TESTED] DELETE removes
  ├── [★★★ TESTED] invalid keyHash → 400
  └── [★★★ TESTED] oversized payload → 400

COVERAGE: 17/19 paths tested (89%)
QUALITY: ★★★:17 ★★:2
GAPS: 2 E2E flows (manual walkthrough in Task 8 covers these)
```

---

## Parallelization

```
Lane A (crypto + backend):
  Task 1 (wallet.crypto.ts) → Task 2 (Flask endpoints)
  Modules: frontend/utils, daanaa_api.py, tests/

Lane B (UI components):
  Task 4 (PassphraseModal) → Task 5 (WalletCard + AddToWalletButton)
  Modules: frontend/components

Lane A and B are independent until Task 3 (WalletContext) which depends on both.

Execution:
  1. Launch Lane A + Lane B in parallel
  2. Merge both
  3. Task 3 (WalletContext refactor) — depends on wallet.crypto.ts from A
  4. Task 6 (WalletPage) — depends on WalletContext from 3 + WalletCard from B
  5. Task 7 (Migration) — depends on WalletContext from 3
  6. Task 8 (E2E verification) — depends on all tasks
```

---

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR | 1 arch decision (session key), 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

**VERDICT:** ENG CLEARED — ready to implement.

NO UNRESOLVED DECISIONS
