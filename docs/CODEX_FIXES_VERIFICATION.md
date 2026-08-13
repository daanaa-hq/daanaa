# Codex P1 Fixes Verification Checklist
**When Codex completes fixes (~11pm), use this checklist**

---

## Fix #1: Directory Page Slowness

**Before (from Codex QC):**
- Load time: 5923ms
- Console errors: 6
- Failed requests: 5
- User experience: Blank page for 6 seconds

**After (expected):**
- Load time: <2000ms (target: 1000-1500ms)
- Console errors: 0 or minimal
- Failed requests: 0
- User experience: Results visible in <2 seconds

**Verification Steps:**
1. Open DevTools on https://www.daanaa.org/directory?q=education&limit=20
2. Clear cache (Cmd+Shift+R or Ctrl+Shift+R)
3. Measure load time in DevTools Network tab
4. Check Console tab for errors (should be clean or minimal)
5. Verify all network requests return 200 or 304
6. Screenshot: DevTools showing load time

**Pass Criteria:**
- ✅ Load time <2000ms
- ✅ Console errors resolved
- ✅ All requests 200/304
- ✅ Results visible before 2 second mark

---

## Fix #2: Color Contrast (WCAG AA)

**Before (from Axe scan):**
- /research: 143 nodes with contrast violations
- /directory: 114 nodes
- /methodology: 103 nodes
- All pages: Systemic token issue

**After (expected):**
- All pages: 0 violations for contrast
- WCAG AA standard: 4.5:1 for normal text, 3:1 for large text

**Verification Steps:**
1. Install Axe DevTools browser extension (if not already)
2. Run scan on https://www.daanaa.org/research
3. Check "Contrast" violation count (should be 0)
4. Run scan on https://www.daanaa.org/directory
5. Run scan on https://www.daanaa.org/methodology
6. Verify all sampled pages pass contrast checks
7. Screenshot: Axe report showing 0 violations

**Pass Criteria:**
- ✅ /research: 0 contrast violations (was 143)
- ✅ /directory: 0 contrast violations (was 114)
- ✅ /methodology: 0 contrast violations (was 103)
- ✅ Other pages: Spot check passes

**Technical Check:**
- [ ] CSS token definitions updated (check `frontend/src/styles/`)
- [ ] Tailwind config updated if needed
- [ ] All text/link color pairs meet 4.5:1 ratio
- [ ] No hardcoded colors that bypass tokens

---

## Fix #3: API Contract Alignment

**Before (from Codex findings):**
- Live API returns: `EIN`, `organization_name`
- Frontend expected: `ein`, `name`
- Result: Data access errors, test failures

**After (expected):**
- Frontend uses: `EIN`, `organization_name`
- API response matches expected shape
- No more field name errors

**Verification Steps:**
1. Open DevTools on https://www.daanaa.org/directory?q=education&limit=20
2. Go to Network tab
3. Click on `/api/search` request
4. View Response body
5. Verify shape matches:
   ```json
   {
     "results": [
       {
         "EIN": "...",
         "organization_name": "...",
         ...
       }
     ]
   }
   ```
6. Check Console for data access errors (should be clean)
7. Screenshot: Network response showing correct field names

**Code Check:**
- [ ] `frontend/src/components/OrgCard.tsx` uses `EIN` not `ein`
- [ ] `frontend/src/pages/Directory.tsx` uses `organization_name` not `name`
- [ ] All org field references updated consistently
- [ ] Test fixtures updated to match live API shape

**Pass Criteria:**
- ✅ API response uses uppercase field names
- ✅ Frontend code accesses correct fields
- ✅ No console errors about missing properties
- ✅ Test fixtures match live response shape

---

## Bonus Check: Org Page Errors (P2)

**Before (from Codex findings):**
- Console errors: 11
- Failed requests: 5
- Content renders: Yes

**After (expected):**
- Console errors: <3 (some minor warnings acceptable)
- Failed requests: 0
- Content renders: Yes

**Quick Check:**
1. Navigate to https://www.daanaa.org/org/530196605
2. Open DevTools Console
3. Count critical errors (not just warnings)
4. Go to Network tab
5. Count failed requests (should be 0)

**Pass Criteria:**
- ✅ Errors reduced from 11 to <3
- ✅ No failed requests
- ✅ Content renders correctly

---

## Final Sign-Off

**When all three fixes pass verification:**

✅ Directory page is fast (<2s load)  
✅ Color contrast meets WCAG AA  
✅ API contract is aligned  
✅ Org page is clean  

**Then proceed with:**
1. Commit verification (all fixes on master)
2. Run final live-site QC suite (`tests/live-site-qc.spec.ts`)
3. Document fixes in DECISIONS.md
4. Green light for Task #5 deployment at 3:00am

---

## If Verification Fails

**For Directory slowness:**
- Check what API responses are slow (use Network tab to measure each request)
- Identify which of the 5 requests is failing and why
- May need to debug FTS query performance or missing data

**For Color contrast:**
- Identify specific colors that fail (Axe reports them)
- Check if all uses of that color pair have been updated
- May need to audit entire color token system

**For API contract:**
- Check actual live API response with curl: `curl -s https://www.daanaa.org/api/search?q=education | jq`
- If API is returning lowercase, update frontend
- If frontend isn't handling uppercase, fix data access code

**Rollback option:**
- If fixes don't work, revert commits: `git revert <commit-hash>`
- Still deploy Task #5 (independent)
- Schedule UX fixes for following day

---

**Verification Owner:** Claude Code  
**Sign-Off Time:** Before 23:00 (11pm)  
**Next Action:** Task #5 deployment at 03:00 (3am)
