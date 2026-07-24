# Root Cause Analysis — QA Retest Failures (2026-07-24)

**Status:** Critical design issues found, fixes required  
**Commit:** `eaed76598d4` (has some correct code but broken defaults and logic)

---

## Three Root Causes

### **1. Directory.tsx Wrong Default Sort** ❌

**File:** `frontend/src/pages/Directory.tsx:106`  
**Problem:** `const [sortBy, setSortBy] = useState('random')`

**Impact:**
- Users see random order on first visit (not A-Z)
- "Randomize it" button doesn't toggle — shuffle already active
- Design intention violated (default should be A-Z, user clicks to randomize)

**Fix Required:** Change default from `'random'` to `'organization_name'`

---

### **2. daanaa_api.py Wrong Default Sort** ❌

**File:** `/home/akbar/meritgiving/daanaa_api.py:2076`  
**Problem:** `sort_by = request.args.get('sort', 'random')`

**Impact:**
- Mismatches production API (droplet_api.py defaults to 'organization_name')
- Causes confusion during testing/development
- QA tested against dev server expecting to see A-Z but got random

**Fix Required:** Change default from `'random'` to `'organization_name'` (match droplet_api.py)

---

### **3. GuidedDiscovery "Show Another List" No Seed Variation** ❌

**File:** `frontend/src/pages/GuidedDiscovery.tsx` lines 212-218  
**Problem:** 
```typescript
const handleShowAnother = () => {
  setShowAnotherCount((c) => c + 1)  // ← increments counter
  window.plausible?.('another_list_requested')
}

// Effect refetches, but NO NEW SEED generated
useEffect(() => {
  if (state.step !== 5) return
  const fetchResults = async () => {
    const filters = mapToDirectoryFilters(state)
    const orgs = await getOrganizations({
      ntee: filters.ntee,
      state: filters.state,
      per_page: 100,
      // ← NO seed parameter passed!
    })
```

**Impact:**
- Counter increments, API is called again
- But same seed is used (from sessionShuffleRef)
- Same organizations returned (shuffle is deterministic per seed)
- "Show another list" appears broken

**Fix Required:** Generate new seed in handleShowAnother, pass to API

---

## Why QA Test Failed

### **API Test Contract (QA curl commands)**
```bash
curl "http://localhost:5000/api/organizations?sort=random&seed=retest-one&per_page=3"
# → ZZYZX FOUNDATION (correct — shuffle is deterministic)

curl "http://localhost:5000/api/organizations?sort=random&seed=retest-two&per_page=3"
# → ZZYZX FOUNDATION (WRONG — should differ from retest-one)
```

### **Why This Happened**
1. QA tested daanaa_api.py (dev server) locally
2. daanaa_api.py defaults to 'random', so tests explicitly passed `sort=random&seed=X`
3. The shuffle code IS in daanaa_api.py (lines 2340-2347)
4. But the code isn't being executed (Flask test client caching or routing issue)
5. Results come back as 'organization_name' sort (default fallback) regardless of seed
6. All Z-named orgs appear in same A-Z order

---

## The Design Error

**Original user request:**
> "maybe we can add a sort option to random and also add a small button which says 'Randomize it' while the filters stay there?"

**Correct interpretation:**
1. Default sort: A-Z alphabetical ('organization_name')
2. "Randomize it" button: switch sort to 'random' (with seed)
3. User experience: predictable default, opt-in random

**What got built instead:**
1. Default sort: Random (wrong)
2. "Randomize it" button: exists but redundant (already random)
3. User experience: confusing (everything is already shuffled)

---

## Fix Checklist

- [ ] Change Directory.tsx line 106: `useState('random')` → `useState('organization_name')`
- [ ] Change daanaa_api.py line 2076: `'random'` → `'organization_name'`
- [ ] Generate new seed in GuidedDiscovery.handleShowAnother (use `Math.random().toString()`)
- [ ] Pass new seed to getOrganizations() in useEffect
- [ ] Verify droplet_api.py shuffle works (test locally with new seed + API call)
- [ ] Re-run QA tests with fixes
- [ ] Seek founder approval before deployment

---

**Analysis by:** Claude Code  
**Date:** 2026-07-24  
**Severity:** Critical (breaks contract for three core features)
