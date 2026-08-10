# CRITICAL DEPLOYMENT PACKAGE (2026-07-24)

**Status:** 🔴 URGENT - Multiple fixes must deploy together  
**Commits Ready:** 6 commits (shuffle fix + stewardship fix)  
**Build:** ✅ Clean (4.07s)  

---

## Critical Issues Being Fixed

### **Issue 1: Shuffle Not Working (URGENT)**
**Symptom:** Directory page loads with Z-A reverse sort, not random  
**Root Cause:** Frontend hasn't been deployed with seed parameter support  
**Fix:** Deploy rebuilt frontend (frontend/dist/)  
**Stewardship Impact:** P4, P7 compliance (fairness, independence)

### **Issue 2: Ranking Sorts Violate Stewardship (CRITICAL)**
**Symptom:** "Top Performers" (merit_score) and "Largest Orgs" (total_revenue) in sort dropdown  
**Root Cause:** Ranking sorts contradict P7 independence principle  
**Fix:** Remove both ranking sorts, keep only: Random, A-Z (neutral)  
**Stewardship Impact:** **Direct P7 violation** - "No rankings" (STEWARDSHIP.md line 118)

---

## Changes Ready to Deploy

### Commit 1: Remove Ranking Sorts (893abe023bb)
**File:** frontend/src/pages/Directory.tsx  
**Change:** Removed 'merit_score' and 'total_revenue' sort options  
**Before:** Random, Name A-Z, Top Performers, Largest Orgs  
**After:** Random, Name A-Z (only neutral options)  
**Compliance:** ✅ P4 (fairness), ✅ P7 (independence)

### Commit 2: Add 'random' to allowed_sorts (8093402d38f)
**File:** daanaa_api.py, droplet_api.py  
**Change:** Added 'random' to whitelist so shuffle executes  
**Impact:** Backend now processes sort=random requests properly

### Commit 3-6: Seed generation, GuidedDiscovery, documentation
**Complete shuffle implementation ready to deploy**

---

## Deployment Steps (CRITICAL ORDER)

### Step 1: Backend Deployment ✅
**Already committed, no additional action needed**
- daanaa_api.py has 'random' in allowed_sorts
- droplet_api.py has 'random' in allowed_sorts
- Both files ready on master branch

### Step 2: Frontend Deployment (MUST DO)
**Frontend rebuild just completed (4.07s)**

Command:
```bash
/daanaa-deploy --code-only
```

Or manual:
```bash
scp -r frontend/dist/* root@162.243.97.179:/opt/daanaa/dist/
```

### Step 3: Verify Post-Deploy ✅
```bash
# Test 1: Default page loads random, not Z-A
curl https://daanaa.org/directory
# Should show random orgs, NOT reverse alphabetical

# Test 2: Different seeds produce different results
curl "https://daanaa.org/api/organizations?sort=random&seed=test1&per_page=3"
curl "https://daanaa.org/api/organizations?sort=random&seed=test2&per_page=3"
# Results should differ

# Test 3: Sort dropdown has only 2 options
# Check browser DevTools: should show "Shuffle" and "Name A to Z" only
# Should NOT show "Top Performers" or "Largest Orgs"
```

---

## What's Being Fixed

### ✅ **Shuffle Feature**
- Directory "Randomize it" button will work
- GuidedDiscovery "Show another list" will work
- Initial page load will show random orgs (not ranking)

### ✅ **Stewardship Compliance**
- **P4 (Fairness):** Removed size-based ranking
- **P7 (Independence):** Removed score-based ranking
- **Result:** Only neutral sort options remain (random + alphabetical)

### ❌ **What's NOT changing**
- Scores still visible on org detail pages (transparency)
- Peer context available (for informed decisions)
- Hidden gems still surfaced (small org discovery)
- No data is deleted or hidden

---

## Risk Assessment

**Risk Level:** 🟢 **LOW**
- Change is strategic (stewardship fix), not operational
- Removes problematic features (safer)
- Frontend/backend both ready
- Simple deployment (code only)

**Rollback:** If issues arise, simply redeploy previous frontend build

---

## Stewardship Compliance

**STEWARDSHIP.md References:**
- **P4** (line 73-88): Small orgs deserve fairness
  - ✅ Removed "Largest Orgs" ranking
  
- **P7** (line 115-122): Independence protected, no rankings
  - ✅ Removed "Top Performers" ranking
  - ✅ Quote: "No partner... may influence... rankings" (line 118)

---

## DEPLOYMENT CHECKLIST

Before deploying, confirm:
- [ ] Frontend rebuilt (4.07s clean build)
- [ ] All commits reviewed and stewardship-compliant
- [ ] Smoke tests understood (3 tests listed above)
- [ ] Founder has reviewed stewardship changes
- [ ] Decision made: deploy now or defer GuidedDiscovery styling?

---

## Next Steps

**Immediate:**
1. Review commit 893abe023bb (ranking sort removal)
2. Confirm stewardship alignment with founder
3. Deploy via `/daanaa-deploy --code-only`
4. Run 3 smoke tests
5. Verify directory page now loads random (not Z-A)

**Post-Deploy (24 hours):**
- Monitor error logs for any issues
- Check analytics for sort option usage
- Verify shuffle randomness in production

**Future:**
- Polish GuidedDiscovery styling to match theme
- Decide: keep frontend-only sort options, or add backend filters later
- Document stewardship decision (why ranking sorts removed)

---

## Commits Ready

```
893abe023bb - fix: Remove ranking sorts (P7 stewardship)
8093402d38f - fix: Add 'random' to allowed_sorts
c7317671f95 - fix: GuidedDiscovery seed generation
4954b527991 - docs: QA documentation
```

**All on master, ready to ship.**

---

**Status:** ✅ Ready for deployment  
**Compliance:** ✅ Stewardship-aligned  
**Risk:** 🟢 Low  
**Action:** Deploy frontend/dist/ via `/daanaa-deploy --code-only`
