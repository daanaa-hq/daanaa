# Critical Issues Found & Remediation Plan (2026-07-24)

**Status:** Three features need quality fixes before deployment  
**Severity:** High (production-facing, user experience impact)

---

## Issues Reported by User Testing

### **1. Randomize Button Not Working** 🔴
**Symptom:** Clicking "Randomize it" loads old results (no visible change)

**Root Cause Analysis Needed:**
- Is the button actually calling onClick handler?
- Is sessionShuffleRef.current being updated?
- Is randomizeCount being incremented?
- Is the API call including the new seed parameter?
- Is there browser caching of responses?

**Possible Fixes:**
- Add console logging to button click handler
- Verify sessionShuffleRef is actually changing
- Check Network tab in DevTools to see if new API call is made
- Ensure Cache-Control headers aren't preventing fresh responses

---

### **2. GuidedDiscovery Styling - "Looks Like AI Slob"** 🔴
**Issues:**
- Component doesn't match daanaa visual language
- Layout/spacing looks auto-generated
- Typography inconsistent with brand
- Form elements not styled properly
- Overall UX feels low-effort

**Components Needing Polish:**
- `frontend/src/pages/GuidedDiscovery.tsx` (entire component)
- `frontend/src/components/discovery/DiscoveryProgress.tsx`
- `frontend/src/components/discovery/DiscoveryQuestion.tsx`
- `frontend/src/components/discovery/DiscoveryChoice.tsx`
- `frontend/src/components/discovery/DiscoveryResults.tsx`
- `frontend/src/components/discovery/DiscoveryWhyHere.tsx`

**Design Standards to Match:**
- Daanaa color palette: soft-gold, deep-navy, warm-cream, cool-grey
- Typography: Playfair (display), Inter (body)
- Spacing: consistent 8px grid
- Borders: use light-grey, soft-gold on hover
- Buttons: soft-gold background, deep-navy text
- Reference: Directory.tsx, OrganizationDetail.tsx (production components)

---

### **3. Results Not Randomized After Filters** 🔴
**Symptom:** After applying discovery filters, results appear ordered (not shuffled)

**Root Cause Analysis Needed:**
- Check if `sort=random` is being sent to API
- Check if seed is being passed correctly
- Verify API is executing shuffle code (not falling back to A-Z)
- Check if WHERE clause results happen to be sorted

**Possible Issues:**
- Filters might be returning small result set that appears sorted by chance
- API might not be receiving seed parameter
- Sort parameter might not be 'random' (check querystring)

---

## Remediation Path

### **Option A: Polish & Deploy (Recommended)**
1. Fix Randomize button (debug frontend state management)
2. Polish GuidedDiscovery styling to match daanaa theme
3. Verify randomization works with filters applied
4. QA retest all three
5. Deployment

**Effort:** 2-3 hours  
**Risk:** Low (isolated UI components)  
**Outcome:** Production-ready features

### **Option B: Defer Discovery UI**
1. Fix Randomize button (critical)
2. Disable or hide GuidedDiscovery (put behind feature flag)
3. Keep Directory randomize working
4. Deploy partial solution
5. Polish GuidedDiscovery in next sprint

**Effort:** 30 minutes  
**Risk:** Low (removes non-critical feature)  
**Outcome:** Directory works, discovery deferred

---

## Recommended Immediate Actions

### **To Diagnose Randomize Button:**
1. Open DevTools → Console
2. Open Network tab
3. Click "Randomize it"
4. Check:
   - Were console.logs printed from onClick?
   - Did a new API request appear in Network tab?
   - Did seed parameter change in the request?
   - Are responses identical or different?

### **To Fix GuidedDiscovery Styling:**
1. Read production components (Directory.tsx, OrganizationDetail.tsx)
2. Study color/spacing patterns
3. Refactor GuidedDiscovery to match:
   - Header: dark navy background, warm-cream text (like Directory)
   - Progress bar: soft-gold on deep-navy
   - Form fields: light-grey borders, soft-gold focus
   - Buttons: soft-gold primary, light-grey secondary
   - Result cards: white background, light-grey borders

### **To Verify Randomization:**
1. Apply filters in discovery (e.g., cause=health, state=CA)
2. Note first 5 orgs displayed
3. Scroll down, come back up
4. Check if order changed
5. Click "Show another list"
6. Check if different orgs appear

---

## Decision Required

**Should we:**
- ✅ **A)** Fix all three issues before deployment (recommended)
- ❌ **B)** Deploy with known quality issues
- ⏸️ **C)** Defer GuidedDiscovery, deploy Directory only

**Recommendation:** Option A  
**Reason:** GuidedDiscovery is public-facing. Quality reflects on daanaa brand.

---

**Next Step:** Confirm remediation path, then execute fixes.
