# Deploy Backend Fixes — NOW
**Status:** Firebase UID linked ✅  
**Next:** Deploy fixes + smoke tests  
**Timeline:** 20 minutes  

---

## Step 1: Deploy Your Changes (10 min)

```bash
cd ~/meritgiving

# Backup current version
cp daanaa_api.py daanaa_api.py.backup.2026-07-22

# Apply your local fixes (from your changes):
# 1. Column name: id AS event_id from volunteer_events
# 2. Authorization: Firebase UID exact match
# 3. Status: submitted → pending
# 4. Revoked claim check

# Verify syntax (should output nothing if OK)
python3 -m py_compile daanaa_api.py

# Restart API
./restart_api.sh
# Or: gunicorn -w 4 --preload daanaa_api:app
```

---

## Step 2: Smoke Tests (10 min)

```bash
# Test 1: Public health endpoint
curl -s http://localhost:5000/health | jq .
# Expected: {"status": "ok", ...}

# Test 2: Search API works
curl -s "http://localhost:5000/api/stats" | jq '.status'
# Expected: "ok" or "running"

# Test 3: Dashboard returns 200 (the critical one)
curl -s -H "Authorization: Bearer $(your_firebase_token)" \
  http://localhost:5000/api/nonprofit/123456789/dashboard | jq '.data.organization'
# Expected: organization data (not 500 error)

# Test 4: Volunteer list works
curl -s -H "Authorization: Bearer $(your_firebase_token)" \
  http://localhost:5000/api/nonprofit/123456789/volunteer_hours/pending | jq '.data | length'
# Expected: number (0 or more, not 403)
```

---

## If All Smoke Tests Pass ✅

```bash
# Tell QA to resume
git log -1 --oneline
# Note the commit SHA

echo "
✅ PRODUCTION DEPLOYED

Fixes deployed:
- Dashboard 500 → 200 (column names)
- Authorization tightening (Firebase UID exact)
- Revoked claim protection
- Canonical pending status

All smoke tests passing:
- Health ✅
- Search ✅
- Dashboard ✅
- Volunteer list ✅

QA can resume authenticated testing immediately.
Estimated time to completion: 2-3 hours
" > DEPLOY_STATUS_2026_07_22.txt

cat DEPLOY_STATUS_2026_07_22.txt
```

---

## If a Smoke Test Fails 🔴

Stop. Check the error:

**Dashboard still 500?**
- Verify your column name changes were applied
- Check if volunteer_events table has `id` column
- Run: `sqlite3 data/merit_registry.db ".schema volunteer_events"`

**Volunteer list 403?**
- Firebase UID mismatch — verify it's in org_claims
- Run: `sqlite3 data/merit_registry.db "SELECT firebase_uid FROM org_claims WHERE ein = '123456789';"`

**Syntax error?**
- Review your daanaa_api.py changes
- Look for typos in column names or query syntax

---

## After Smoke Tests Pass

**Notify QA team immediately:**

> All Priority 0 blockers fixed. Backend deployed and verified.
> 
> QA can resume authenticated testing (Phase 2 & 3):
> - Login: test@testnonprofit.org / TestNonprofit2024!
> - Expected: Dashboard loads, volunteer hours visible, can approve/reject
> - ETA to completion: 2-3 hours
>
> See QA_MANUAL_TESTS.md for detailed test plan.

---

## You're Here:

```
Firebase UID linked ✅
↓
Deploy backend fixes ← YOU ARE HERE
↓
Smoke tests pass ← THEN THIS
↓
QA resumes + completes ← THEN THIS
↓
All blockers cleared ✅
```

**Go deploy.** 20 minutes.
