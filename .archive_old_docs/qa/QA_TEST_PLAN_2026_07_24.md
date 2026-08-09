# QA Test Plan — Guided Discovery Fixes (2026-07-24)

**Scope:** Three functional blockers from QA retest report  
**Build:** `eaed76598d4` (master branch)  
**Test Environment:** Local dev + staging droplet  
**Estimated Duration:** 30-45 minutes

---

## Overview

Three fixes addressing QA blockers:

1. **Random sort seeded shuffle** - Different seeds must produce different result orders
2. **"Show another list" exhaustion** - Must produce fresh result lists without emptying
3. **"Near me" placeholder** - Shows "coming soon" instead of broken flow

---

## Test 1: Random Sort Seeded Shuffle

### Test Contract

```
Same filters + same seed → same ordered list of EINs
Same filters + different seed → different ordered list of EINs
Same filters + no seed → documented fallback (A-Z alphabetical)
```

### Test Steps

#### 1a. Test reproducibility (same seed = same order)

1. Navigate to `/discover`
2. Step through: Purpose → Cause → Place → Connection → Results
3. Note the first 3 organization names shown
4. Click "Show another list" once
5. Note the new first 3 organization names
6. **Expected:** Different 3 orgs (new random shuffle)

#### 1b. Test different seeds produce different results

1. Open browser DevTools → Application → LocalStorage
2. Delete `daanaa_session_seed`
3. Refresh `/discover` page
4. Note first 3 orgs displayed
5. Delete the seed again and refresh
6. **Expected:** Different 3 orgs than before

#### 1c. Test URL parameter seeding (for shareable URLs)

1. Make a request to local API:
```bash
curl "http://localhost:5000/api/organizations?sort=random&seed=test-seed-1&per_page=3" | jq '.organizations[].organization_name'
```
2. Note the 3 org names
3. Repeat with same seed:
```bash
curl "http://localhost:5000/api/organizations?sort=random&seed=test-seed-1&per_page=3" | jq '.organizations[].organization_name'
```
4. **Expected:** SAME 3 orgs in same order
5. Now repeat with different seed:
```bash
curl "http://localhost:5000/api/organizations?sort=random&seed=different-seed&per_page=3" | jq '.organizations[].organization_name'
```
6. **Expected:** DIFFERENT 3 orgs than test 1c-2

### Pass Criteria

- ✅ "Show another list" produces genuinely different results (not cycling)
- ✅ Same seed always returns same org order
- ✅ Different seeds return different org order
- ✅ API response time < 500ms even for large filtered result sets

---

## Test 2: "Show another list" Exhaustion Fix

### Test Contract

```
"Show another list" must continue producing new results without immediately emptying
Minimum: 3 consecutive clicks must show different org pools
```

### Test Steps

1. Navigate to `/discover` and complete the 5-step flow
2. Record the first 5 org names shown (e.g., "Org A, B, C, D, E")
3. Click "Show another list" button
4. Record the new first 5 org names (e.g., "Org F, G, H, I, J")
5. Click "Show another list" again
6. Record the new first 5 org names (e.g., "Org K, L, M, N, O")
7. Click "Show another list" a third time
8. Record the new first 5 org names

### Pass Criteria

- ✅ Each click produces a visibly different list
- ✅ No message like "No more results available" appears prematurely
- ✅ Each list contains >= 3 organizations
- ✅ Lists are different from each other (not cycling through same 5)

---

## Test 3: "Near me" Placeholder

### Test Contract

```
"Near me" button must exist and show helpful "coming soon" message
No geolocation permission prompts must appear
```

### Test Steps

1. Navigate to `/discover`
2. Complete Steps 1-2 (Purpose → Cause)
3. Reach Step 3 (Place)
4. Look for a "Near me" button or equivalent
5. Click the "Near me" button
6. **Expected:** Message appears: "Coming soon! For now, use a city name or ZIP code above."
7. **Expected:** No browser permission prompt for location access
8. Verify the user can still enter a city or ZIP code in the input field below
9. Enter a city/ZIP and verify results load

### Pass Criteria

- ✅ "Near me" button exists and is accessible
- ✅ Clicking shows "Coming soon" message, not broken behavior
- ✅ No geolocation permission prompts appear
- ✅ Fallback to city/ZIP input works smoothly

---

## Regression Tests

### Frontend Build & Tests

```bash
cd frontend
npm run build  # Should complete in < 10s with no errors
npx jest       # Should pass 12 suites, 215 tests
```

### Navigation

- ✅ Directory page still loads with "Randomize it" button
- ✅ Default sort is random (not A-Z)
- ✅ Clicking "Randomize it" produces different order each time
- ✅ Home page "Start guided discovery" link works

### Core Pages

- ✅ `/` (home) loads
- ✅ `/directory` loads and shows orgs
- ✅ `/about`, `/terms`, `/privacy` all load
- ✅ Search bar on directory still works

---

## Deployment Checklist

After QA passes:

- [ ] Commit is on master branch
- [ ] Privacy gates passed
- [ ] All tests pass locally
- [ ] Run `/health` check post-deploy
- [ ] Verify `/api/organizations?sort=random&seed=test&per_page=3` returns different results on second request with different seed
- [ ] Founder approval obtained
- [ ] A/B test plan (50/50 shuffle vs A-Z for 48h) documented

---

## Known Limitations

1. **Geolocation "Near me"** — Marked as "coming soon"; reverse geocoding deferred to post-MVP
2. **daanaa_api.py dev server** — May need restart for shuffle seed changes to take effect (uses gunicorn workers); droplet_api.py is the canonical production API
3. **Result pages** — Pagination works across shuffled results (page 2 shows items 20-39 of shuffled list); intentional design

---

## Post-QA Next Steps

1. Monitor `/api/stats` and request logs for anomalies post-deploy
2. Schedule 48h A/B test of shuffle vs A-Z default
3. Plan geolocation MVP (Q3 2026 roadmap)
4. Evaluate "Show another list" discovery funnel effectiveness (Plausible event: `another_list_requested`)

---

**Test Plan Created:** 2026-07-24  
**Target QA Completion:** 2026-07-24 EOD  
**Contact:** Akbar Khowaja (akbar.khowaja@gmail.com)
