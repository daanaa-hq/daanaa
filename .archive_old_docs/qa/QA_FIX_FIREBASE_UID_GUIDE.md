# QA Fix: Firebase UID Linking
**Status:** Blocking authenticated testing  
**Issue:** test@testnonprofit.org authenticated but not linked to nonprofit in `org_claims` table  
**Solution:** Add Firebase UID to `org_claims` table

---

## The Problem

The backend checks `org_claims` table to verify nonprofit ownership:

```python
claim = db.execute(
    'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
    (ein, uid)
).fetchone()

if not claim:
    return jsonify({'error': 'You do not own this nonprofit'}), 403
```

**Current state:**
- ✅ test@testnonprofit.org has Firebase account (authentication works)
- ✅ EIN 123456789 (Test Food Bank) exists in `nonprofit_accounts` and `registry_enriched`
- ❌ Missing link in `org_claims` with correct Firebase UID

**Result:** Dashboard returns 500, volunteer list returns 403

---

## Solution: Get Firebase UID and Link It

### Option 1: Quick Fix (2 minutes)

**Step 1: Get Firebase UID from Console**

1. Go to: https://console.firebase.google.com
2. Select your **Daanaa Firebase project**
3. Navigate to: **Authentication** → **Users**
4. Find the user: **test@testnonprofit.org**
5. Click on the user row
6. Copy the **User UID** (long alphanumeric string, ~28 characters)

**Step 2: Run Fix Script**

```bash
cd ~/meritgiving
python3 scripts/manual_fix_qa_linking.py YOUR_FIREBASE_UID
```

Replace `YOUR_FIREBASE_UID` with the UID you copied (e.g., `AbCdEfGhIjKlMnOpQrStUvWxYz1234`)

**Example:**
```bash
python3 scripts/manual_fix_qa_linking.py "hJ7kL2mN5pQrStUvWxYzAbCdEfGhIjKl"
```

**Step 3: Verify**

```bash
sqlite3 data/merit_registry.db "SELECT ein, email, firebase_uid, claim_status FROM org_claims WHERE ein = '123456789';"
```

Should output:
```
123456789|test@testnonprofit.org|<YOUR_UID>|verified
```

✅ Done!

---

### Option 2: Interactive Fix (If you don't have UID handy)

```bash
cd ~/meritgiving
python3 scripts/manual_fix_qa_linking.py
```

The script will guide you through:
1. Finding the Firebase UID in the console
2. Or extracting it from browser storage
3. Confirming the link

---

### Option 3: Manual Database Update

If you prefer direct SQL:

```bash
sqlite3 data/merit_registry.db
```

Then run:

```sql
-- First, check if record exists
SELECT * FROM org_claims WHERE ein = '123456789';

-- If record exists, update it:
UPDATE org_claims 
SET firebase_uid = 'YOUR_FIREBASE_UID_HERE', 
    email = 'test@testnonprofit.org'
WHERE ein = '123456789';

-- If record doesn't exist, insert it:
INSERT INTO org_claims 
(ein, email, firebase_uid, claim_status, claim_verified_at, created_at)
VALUES 
('123456789', 'test@testnonprofit.org', 'YOUR_FIREBASE_UID_HERE', 'verified', datetime('now'), datetime('now'));

-- Verify:
SELECT ein, email, firebase_uid, claim_status FROM org_claims WHERE ein = '123456789';

-- Exit SQLite
.exit
```

---

## Finding Firebase UID: Detailed Steps

### Method 1: Firebase Console (Recommended)

**Screenshot path:**
1. **Console** → Select project
2. **Authentication** (left sidebar)
3. **Users** tab
4. Find **test@testnonprofit.org** in the list
5. Click the user row → Details panel opens
6. Copy **User UID**

---

### Method 2: Browser DevTools

**If you have the login session still open:**

1. Go to: https://daanaa.org/org/login
2. Log in with: test@testnonprofit.org / TestNonprofit2024!
3. Press `F12` to open DevTools
4. Go to: **Application** tab → **Local Storage**
5. Look for key: `firebase:authUser:*` (will show your project's Firebase config)
6. Click on that key to view its value
7. In the JSON object, find: `"uid":"YOUR_UID_HERE"`
8. Copy the UID (without quotes)

---

### Method 3: Decode ID Token

**If you capture the ID token:**

The Firebase client sends an ID token in the request. You can decode it:

```bash
# If you have the token saved
echo "eyJhbGc..." | python3 -c "
import sys, json, base64
token = sys.stdin.read().strip().split('.')
# ID tokens have three parts; the middle is the payload
payload = token[1] + '=='  # Add padding if needed
decoded = base64.urlsafe_b64decode(payload)
print(json.dumps(json.loads(decoded), indent=2))
"
```

Look for the `"sub"` field—that's the Firebase UID.

---

## Verification

After applying the fix, verify everything works:

### 1. Database Check

```bash
sqlite3 data/merit_registry.db << EOF
SELECT 'org_claims record:' as check;
SELECT ein, email, firebase_uid FROM org_claims WHERE ein = '123456789';

SELECT '';
SELECT 'nonprofit_accounts record:' as check;
SELECT ein, email, verified FROM nonprofit_accounts WHERE ein = '123456789';

SELECT '';
SELECT 'registry record:' as check;
SELECT ein, organization_name FROM registry_enriched WHERE ein = '123456789';
EOF
```

Should show all three records linked correctly.

### 2. API Test

```bash
# Make sure API is running
curl -s http://localhost:5000/health | jq .

# Test unauthenticated endpoint (should work)
curl -s http://localhost:5000/api/stats | jq .status
```

### 3. Authenticated Test (Manual)

1. Go to: https://daanaa.org/org/login
2. Log in with: test@testnonprofit.org / TestNonprofit2024!
3. You should see:
   - ✅ Dashboard loads (no 500 error)
   - ✅ Organization name: "DAANAA INTERNAL TEST ORGANIZATION"
   - ✅ Volunteer hours list (if any exist)
   - ✅ Profile editor tab accessible

---

## If Fix Doesn't Work

### Dashboard still returns 500

**Debug:**
```bash
tail -f /var/log/daanaa_api.log | grep -i error
```

Check for:
- SQL errors (malformed query)
- Missing columns
- Database connection issues

### Still getting 403 "You do not own this nonprofit"

**Verify:**
1. ✅ org_claims record exists with correct EIN and Firebase UID
2. ✅ claim_status is "verified" or "active" (not "revoked")
3. ✅ Firebase UID matches exactly (check for whitespace)

```bash
sqlite3 data/merit_registry.db "SELECT * FROM org_claims WHERE ein = '123456789' AND firebase_uid = 'YOUR_UID';"
```

Should return 1 row.

### Still getting "Invalid EIN"

**Check EIN format:**
```bash
# The backend strips non-digits
echo "123456789" | python3 -c "import sys; ein = ''.join(c for c in (sys.stdin.read().strip() or '') if c.isdigit())[:10]; print(f'Cleaned EIN: {ein}')"
```

Should output: `Cleaned EIN: 123456789`

---

## After Fix: QA Can Resume

Once the Firebase UID is linked, authenticated testing can proceed:

**Phase 1: Authenticated Read Tests**
- [ ] Nonprofit dashboard loads (GET /api/nonprofit/profile)
- [ ] Volunteer hours list displays (GET /api/nonprofit/{ein}/volunteer/pending)
- [ ] Profile editor renders (GET /api/nonprofit/profile)
- [ ] Help tooltips work
- [ ] Mobile viewport responsive

**Phase 2: Authenticated Write Tests** (Mutating)
- [ ] Can approve volunteer hours
- [ ] Can reject volunteer hours
- [ ] Can edit nonprofit profile
- [ ] Can create wallet records

**Expected Duration:** 2-3 hours total

---

## Next: Run QA Tests

Once Firebase UID is linked and login works:

```bash
# Test authenticated dashboard
curl -s -H "Authorization: Bearer YOUR_ID_TOKEN" \
  http://localhost:5000/api/nonprofit/profile | jq .

# Or manually:
# 1. Go to https://daanaa.org/org/login
# 2. Login as test@testnonprofit.org
# 3. Check each page loads without errors
```

---

## Summary

| Step | Status | Time |
|------|--------|------|
| Get Firebase UID | ⏳ Your action | 2 min |
| Run fix script | ⏳ Your action | 1 min |
| Verify database | ✅ Automated | 30 sec |
| Test login | ⏳ Your action | 2 min |
| Resume QA | ✅ Ready | 2-3 hrs |

**Total time to unblock:** ~5-10 minutes hands-on

---

**Ready?** Run the fix when you have the Firebase UID!
