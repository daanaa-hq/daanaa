# Priority 0 Fixes - Daanaa QA Blockers
**Date:** July 22, 2026  
**Status:** Action Plan for Immediate Resolution

---

## Issue #1: Firebase QA Account - INVALID_LOGIN_CREDENTIALS ❌

### Problem
QA account `test@testnonprofit.org` returns `INVALID_LOGIN_CREDENTIALS` when attempting authentication.

### Root Cause
- Firebase user not created or account credentials incorrect
- Test account may not be linked to Test Food Bank (EIN: 123456789)
- Account may be disabled or email unverified

### Fix

**Option A: Verify existing account (5 minutes)**
```bash
# Check if account exists in Firebase Console
1. Go to: https://console.firebase.google.com
2. Project: daanaa-prod (or your project)
3. Authentication → Users
4. Search for: test@testnonprofit.org
5. Verify email is verified
6. Check linked nonprofit EIN
```

**Option B: Create new disposable test account (15 minutes)**
```bash
# Via Firebase CLI
firebase auth:create test@testnonprofit.org --password TestNonprofit2024! --project daanaa-prod

# Then link to test nonprofit in database:
sqlite3 data/merit_registry.db "
  INSERT OR REPLACE INTO nonprofit_users 
    (email, ein, role, created_at)
  VALUES 
    ('test@testnonprofit.org', '123456789', 'admin', datetime('now'))
;"
```

**Option C: Use existing nonprofit account (fastest)**
- Ask founder for a real test nonprofit EIN + email
- Use that for QA instead of fictional "Test Food Bank"

### Verification
```bash
# Test login
curl -X POST https://daanaa.org/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@testnonprofit.org",
    "password": "TestNonprofit2024!"
  }'

# Should return 200 with auth token
```

**Status:** ⏳ **REQUIRED BEFORE** authenticated QA can proceed

---

## Issue #2: Missing `/api/public/nonprofit/{ein}/profile/sources` ❌

### Problem
Frontend calls `/api/public/nonprofit/123456789/profile/sources` but endpoint returns 404.

### Root Cause
- Endpoint exists in `daanaa_api.py` (home server)
- **NOT** in `scripts/droplet_api.py` (production droplet)
- Droplet's search.db schema doesn't have nonprofit_supplied_data table

### Fix

**Step 1: Add endpoint to droplet_api.py**

```python
# Add to scripts/droplet_api.py around line 2000 (before serve_qa)

@app.route('/api/public/nonprofit/<ein>/profile/sources', methods=['GET'])
def public_profile_sources_droplet(ein: str):
    """Public: Show data sources for nonprofit profile (droplet version)."""
    ein_clean = ''.join(c for c in ein if c.isdigit())[:10]
    if not ein_clean:
        return jsonify({'error': 'Invalid EIN'}), 400

    db = get_db_search()
    org = db.execute(
        """SELECT organization_name, mission FROM organizations 
           WHERE ein = ?""",
        (ein_clean,)
    ).fetchone()
    
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    # Return available sources from search.db
    return jsonify({
        'ein': ein_clean,
        'organization_name': org['organization_name'],
        'sources': {
            'mission': {
                'value': org['mission'],
                'source': 'IRS Form 990 / ProPublica'
            }
        },
        'note': 'Profile enrichment data available on home server'
    })
```

**Step 2: Deploy updated droplet_api.py**
```bash
bash scripts/ops/sync_droplet_api.sh
```

**Step 3: Verify endpoint**
```bash
curl https://daanaa.org/api/public/nonprofit/123456789/profile/sources
# Should return 200 with sources object
```

**Status:** ⏳ **REQUIRED BEFORE** frontend render can fully test

---

## Issue #3: Malformed volunteer_hours Data (18 rows) ❌

### Problem
18 volunteer_hours rows contain shifted/malformed data:
- Mission text in hours column
- Location text in status column
- Missing or invalid IDs

### Root Cause
Migration error or test data inserted incorrectly. Fields are offset.

### Fix

**Step 1: Quarantine malformed data**
```sql
-- Create backup table for corrupted rows
CREATE TABLE volunteer_hours_corrupted_backup AS
  SELECT * FROM volunteer_hours 
  WHERE id IS NULL 
     OR hours IS NULL 
     OR (typeof(hours) NOT IN ('integer', 'real'));

-- Count: should show 18 rows
SELECT COUNT(*) FROM volunteer_hours_corrupted_backup;
```

**Step 2: Delete malformed rows from active table**
```sql
DELETE FROM volunteer_hours 
WHERE id IS NULL 
   OR hours IS NULL 
   OR (typeof(hours) NOT IN ('integer', 'real'));

-- Verify: should be 88 clean rows
SELECT COUNT(*) FROM volunteer_hours;
```

**Step 3: Inspect backup to understand origin**
```bash
sqlite3 data/merit_registry.db "SELECT * FROM volunteer_hours_corrupted_backup LIMIT 3;" > /tmp/corrupted_samples.txt
# Review to understand data shift pattern
```

**Complete Script:**
```bash
sqlite3 data/merit_registry.db << 'SQL'
CREATE TABLE volunteer_hours_corrupted_backup AS
  SELECT * FROM volunteer_hours 
  WHERE id IS NULL 
     OR hours IS NULL 
     OR (typeof(hours) NOT IN ('integer', 'real'));

DELETE FROM volunteer_hours 
WHERE id IS NULL 
   OR hours IS NULL 
   OR (typeof(hours) NOT IN ('integer', 'real'));

-- Verify
SELECT 'Clean rows remaining:', COUNT(*) FROM volunteer_hours;
SELECT 'Corrupted rows backed up:', COUNT(*) FROM volunteer_hours_corrupted_backup;
SQL
```

**Status:** ⏳ **REQUIRED BEFORE** volunteer testing can proceed

---

## Issue #4: QA Test Password Security ⚠️

### Problem
Test password `TestNonprofit2024!` may be:
- Shared publicly in QA documents
- Connected to real nonprofit data
- Visible in version control

### Fix

**If account is real/shared:**
```bash
# Rotate password immediately
# Update in:
# 1. QA_CREDENTIALS.txt
# 2. QA_TEST_CHECKLIST.txt
# 3. QA_MANUAL_TESTS.md
# 4. This plan
# 5. Firebase
```

**If account is disposable:**
- OK to leave as-is for QA only
- Never use for production data
- Rotate before launch

**Recommendation:** Use a real test nonprofit with a temporary password, rotate it after QA completes.

**Status:** ✅ **LOW RISK** if account is disposable

---

## Action Checklist

### Blocking (Start here - 30 minutes)
- [ ] **Firebase Account** - Verify or create `test@testnonprofit.org` → link to EIN 123456789
- [ ] **Profile Sources Endpoint** - Add to droplet_api.py → deploy via sync_droplet_api.sh
- [ ] **Malformed Data** - Backup 18 rows → delete from volunteer_hours
- [ ] **Verification** - Test each fix with curl commands above

### Verification Smoke Tests
```bash
# 1. Firebase login
curl -X POST https://daanaa.org/api/auth/login \
  -d '{"email":"test@testnonprofit.org","password":"TestNonprofit2024!"}'
# Should: 200 with auth token

# 2. Profile sources endpoint
curl https://daanaa.org/api/public/nonprofit/123456789/profile/sources
# Should: 200 with sources object

# 3. Volunteer data clean
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM volunteer_hours;"
# Should: return 88 (or your target clean count)
```

### Deployment Sequence
1. **Firebase account setup** (no deploy needed)
2. **Add endpoint + deploy droplet_api.py** (5 min deploy)
3. **Clean volunteer data** (no deploy needed, local DB only)
4. **Run verification tests** (5 min)

### Timeline
- **Now-30 min:** Priority 0 fixes
- **30-40 min:** Deployments + verification
- **40 min+:** Resume authenticated QA testing

---

## Why These Are Blocking

✗ **Without Firebase Fix:** Can't test nonprofit dashboard, approval flow, profile editing  
✗ **Without Endpoint Fix:** Frontend's "Data Sources" tab will 404  
✗ **Without Data Clean:** Volunteer testing results will be corrupted  

---

## Next Steps After Priority 0

Once these are fixed, QA can run:
1. Authenticated nonprofit login + dashboard
2. Volunteer hour submission → approval flow
3. Profile editing + data persistence
4. Wallet functionality
5. Event creation + linking
6. Complete end-to-end flows

**Estimated authenticated QA time:** 2-3 hours

---

**Owner:** Dev team  
**Target:** Complete by [date]  
**Verification:** Run automated script after each fix
