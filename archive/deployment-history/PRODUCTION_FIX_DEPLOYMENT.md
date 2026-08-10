# Production Fix Deployment: Firebase UID Linking
**Status:** Ready to Deploy  
**Blocker:** Firebase UID must exactly match org_claims record  
**Timeline:** Deploy today + verify smoke tests  

---

## What's Fixed Locally

✅ **Dashboard 500 error** — Column name issues resolved  
✅ **Authorization tightening** — Firebase UID exact match (case-sensitive)  
✅ **Revoked claim protection** — Added  
✅ **Canonical status** — Changed from `submitted` to `pending`  
✅ **Regression tests** — 31 passed  

**Status:** Local fixes verified, ready to deploy to production

---

## Remaining Production Issue

**Problem:** Firebase UID in `org_claims` must exactly match the authenticated UID.

**Current state:**
- Firebase account (test@testnonprofit.org) authenticates successfully
- Dashboard returns 500 (pre-fix) → will return 200 after deploying fix
- Authorized endpoints return 403 because Firebase UID case mismatch

**Solution:** Update `org_claims` table with exact Firebase UID

---

## Step 1: Get Exact Firebase UID

### Option A: From Firebase Console (Fastest)
1. Go to https://console.firebase.google.com
2. Select Daanaa project → Authentication → Users
3. Find: test@testnonprofit.org
4. Copy: User UID (28-char alphanumeric string)

### Option B: From Browser DevTools (If logged in)
1. Go to https://daanaa.org/org/login
2. Log in with test@testnonprofit.org
3. Press F12 → Application → Local Storage
4. Find key: `firebase:authUser:*`
5. In JSON, copy the `"uid":"..."` value

### Option C: From Backend Token (If you capture it)
When authenticated request comes in, the Firebase token's `uid` claim is the answer.

---

## Step 2: Update Production Database

Once you have the exact Firebase UID (let's call it `EXACT_UID_HERE`):

```bash
cd ~/meritgiving

# Verify current state
sqlite3 data/merit_registry.db << EOF
SELECT id, email, firebase_uid, claim_status 
FROM org_claims 
WHERE ein = '123456789';
EOF

# You should see the mismatched UID

# Update with exact UID (replace EXACT_UID_HERE with the real one)
sqlite3 data/merit_registry.db << EOF
UPDATE org_claims 
SET firebase_uid = 'EXACT_UID_HERE'
WHERE ein = '123456789';
EOF

# Verify update
sqlite3 data/merit_registry.db << EOF
SELECT id, email, firebase_uid, claim_status 
FROM org_claims 
WHERE ein = '123456789';
EOF
```

---

## Step 3: Deploy Backend Fixes

### 3a. Backup current daanaa_api.py
```bash
cp daanaa_api.py daanaa_api.py.backup.2026-07-22
```

### 3b. Deploy your local fixes to production

If you have the fixes in a local branch:
```bash
git diff HEAD -- daanaa_api.py > /tmp/dashboard_fixes.patch
git apply /tmp/dashboard_fixes.patch
```

Or manually apply the three fixes from your local changes:
1. Column name fix: `id AS event_id` from volunteer_events
2. Authorization tightening: Firebase UID exact match
3. Status change: `submitted` → `pending`
4. Revoked claim check: added

### 3c. Verify syntax
```bash
python3 -m py_compile daanaa_api.py
# Should output nothing (success)
```

### 3d. Restart API
```bash
./restart_api.sh
# Or: gunicorn -w 4 --preload daanaa_api:app
```

---

## Step 4: Smoke Tests

### Test 1: Public endpoints work
```bash
curl -s http://localhost:5000/health | jq .
# Should return: {"status": "ok", ...}

curl -s "http://localhost:5000/api/stats" | jq '.status'
# Should return: "ok"
```

### Test 2: Unauthorized still blocked
```bash
curl -s -H "Authorization: Bearer invalid_token" \
  http://localhost:5000/api/nonprofit/123456789/volunteer_hours \
  | jq '.error'
# Should return error (403 or 401)
```

### Test 3: Dashboard with correct UID
```bash
# Get a valid Firebase token for test@testnonprofit.org
# Then test:
curl -s -H "Authorization: Bearer {VALID_TOKEN}" \
  http://localhost:5000/api/nonprofit/123456789/dashboard \
  | jq '.status'
# Should return 200 with org data
```

### Test 4: Volunteer list works
```bash
curl -s -H "Authorization: Bearer {VALID_TOKEN}" \
  http://localhost:5000/api/nonprofit/123456789/volunteer_hours/pending \
  | jq '.data | length'
# Should return count (200 status)
```

---

## Step 5: Clear QA to Resume Authenticated Testing

Once smoke tests pass:

```bash
# Notify QA team
echo "
✅ AUTHENTICATED QA READY TO RESUME

All Priority 0 blockers fixed:
1. Firebase UID linked correctly
2. Dashboard returns 200
3. Authorization working
4. Volunteer endpoints accessible

QA can now:
- Login with test@testnonprofit.org / TestNonprofit2024!
- View nonprofit dashboard
- Test volunteer hours approval workflow
- Complete Phase 2 & 3 tests

Estimated time to complete QA: 2-3 hours
" | tee QA_READY_2026_07_22.txt
```

---

## Checklist: Deploy with Confidence

Before deploying:
- [ ] Local fixes verified (your 31 regression tests passed)
- [ ] Exact Firebase UID obtained from console
- [ ] Backup of current daanaa_api.py created
- [ ] Syntax check passed
- [ ] API restarted

After deploying:
- [ ] Public health endpoint returns 200
- [ ] Unauthorized access still returns 403
- [ ] Test UID in org_claims exactly matches authenticated UID
- [ ] Dashboard returns 200 with test UID
- [ ] Volunteer endpoints return 200 with test UID
- [ ] Unrelated user still gets 403

---

## If Tests Fail

### Dashboard still returns 500
**Likely cause:** Column names or query logic still off
**Fix:** Review your changes to dashboard query, verify column names in volunteer_events table

### Still getting 403 "claim not owned"
**Likely cause:** Firebase UID still doesn't match exactly
**Fix:** Check org_claims record: `SELECT firebase_uid FROM org_claims WHERE ein = '123456789';`
Must be identical to authenticated UID (case-sensitive)

### Volunteer endpoints return 403
**Likely cause:** Authorization check in your fix
**Fix:** Verify the exact Firebase UID match in endpoint authorization

---

## After Smoke Tests Pass

1. **Notify QA team** — Authenticated testing can resume
2. **QA Phase 2 resumes** — 1-2 hours for authenticated read tests
3. **QA Phase 3 resumes** — 1-2 hours for authenticated write tests
4. **Submit QA report** — Mark QA complete

---

## Timeline

| Step | Owner | Time |
|------|-------|------|
| Get Firebase UID | You | 5 min |
| Update org_claims | You | 5 min |
| Deploy backend fixes | You | 10 min |
| Verify syntax | You | 2 min |
| Restart API | You | 2 min |
| Smoke tests (4 tests) | You | 10 min |
| Notify QA | You | 2 min |
| **Total** | | **36 min** |

**Then QA runs 2-3 more hours of testing.**

---

## Success = QA Clears

When this is done:
- ✅ Firebase UID linked
- ✅ Dashboard working (200)
- ✅ Authorization correct (exact match)
- ✅ Smoke tests passing
- ✅ QA can resume authenticated testing
- ✅ Phase 2 & 3 tests can complete
- ✅ All Priority 0 blockers cleared
- ✅ System ready for board + development

---

**You're 36 minutes from QA clearing. Go deploy.** 🚀
