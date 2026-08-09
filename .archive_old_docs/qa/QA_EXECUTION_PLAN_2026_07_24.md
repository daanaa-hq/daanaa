# QA Execution Plan — Search Fix + Shuffle-Default Feature (2026-07-24)

**Status:** ✅ Code complete and committed | Awaiting QA execution  
**Build:** ✅ Frontend build passes | ✅ Backend code ready  
**Commit:** `5420cabe94a` — "feat: search performance fix + discovery-first directory UX"

---

## Quick Summary

**Two independent fixes deployed together:**

1. **Search Performance** — Fixed 60+ second timeouts (FTS index rebuild)
2. **Directory UX** — Changed default sort from A-Z to seeded random shuffle (engagement + fairness)

Both are **backward compatible** (users can always switch back to A-Z) and **low-risk** (no schema changes, no data changes).

---

## Testing Environment Setup

### Prerequisites
```bash
# 1. Activate venv
source ~/meritgiving/venv/bin/activate

# 2. Start API
cd ~/meritgiving
python3 daanaa_api.py  # Or: ./restart_api.sh

# 3. Start frontend (separate terminal)
cd ~/meritgiving/frontend
npm run dev  # Port 5173

# 4. Open browser
# http://localhost:5173/directory
```

---

## Critical Path Tests (Must Pass — 20 minutes)

### Test 1: Search is Fast
**Action:** Navigate to directory, search for "health"  
**Expected:** Results appear in <1 second, no timeout  
**Verification:**  
- [ ] Typed query returns results immediately (not spinning)
- [ ] Result count shows "1000+" (not zero)
- [ ] Browser DevTools Network tab: `/api/search` request <500ms
- [ ] Can click through 5 results without delays

### Test 2: Directory Loads with Shuffle
**Action:** Navigate to `/directory` (no search)  
**Expected:** Random org appears (not alphabetical "0 TIENOU")  
**Verification:**
- [ ] First org is NOT "0 TIENOU TI DIERO BAAFIRI"
- [ ] First org name is recognizable (e.g., "American Heart Association", "Habitat for Humanity")
- [ ] Refreshing page shows DIFFERENT first org (shuffle working)
- [ ] Refreshing 3 times shows 3 different orgs

### Test 3: User Can Switch to A-Z
**Action:** Click sort dropdown, select "Name A-Z"  
**Expected:** Results immediately re-sort to alphabetical  
**Verification:**
- [ ] Sort dropdown shows "🎲 Shuffle" as current
- [ ] Click "Name A-Z" option
- [ ] First result changes to "0 TIENOU TI DIERO BAAFIRI"
- [ ] Clicking "Shuffle" again shows random org

### Test 4: Health Check Script Works
**Action:** Run health check
```bash
bash scripts/health_check.sh
```
**Expected:** All checks pass (green ✓)  
**Verification:**
- [ ] Homepage: 200
- [ ] Directory: 200
- [ ] Volunteer: 200
- [ ] API health: 200
- [ ] No error lines

### Test 5: Shuffle Works with Filters
**Action:** In directory, click "Health" cause tag while shuffle is active  
**Expected:** Shuffles within health subset  
**Verification:**
- [ ] Results show only health-related orgs (cause tags include "health")
- [ ] Refreshing page shows different health orgs (shuffle still active)
- [ ] Result count decreases (filtered subset)

---

## Important Behaviors (Understand These)

### Shuffle Determinism
- **Session seed:** Generated per session (browser load), stored in localStorage
- **Same session:** Same seed = same org order every reload
- **New session:** New seed = different shuffle
- **This is by design:** Users see consistent results within a session, but discover different orgs each visit

### Sort Dropdown Order
1. 🎲 **Shuffle** (default, discovery-first)
2. Name A-Z (neutral control)
3. 📊 Top Performers (quality opt-in, if scores enabled)
4. 📈 Largest Orgs (size opt-in)

### Stewardship Compliance
- ✅ P7 (Independence): Random is neutral, not ranking
- ✅ P4 (Small orgs fairness): Shuffle is fairer than A-Z (no name bias)
- ✅ P5 (Dignity): No shame, just discovery
- ✅ P3 (Evidence-based): Shuffle is transparent and user-controlled

---

## Full Test Checklist (All 50+ tests)

See: `QA_CHECKLIST_2026_07_24.md` for comprehensive test matrix.

**Priority 1 (Critical — 20 min):** Tests 1.1–1.3  
**Priority 2 (Important — 30 min):** Tests 2.1–2.5  
**Priority 3 (Regression — 20 min):** Tests 3.1–3.3  
**Priority 4 (Edge cases — 10 min):** Tests 4.1–4.3

**Total time to execute:** 45–60 minutes  
**Minimum to ship:** Priority 1 + Priority 2 pass

---

## Known Limitations & Deferred Work

❌ **Not in this release:**
- Event API proxy routes (disabled 2026-07-24, need separate fix)
- Trending/New sort option (deferred to Phase 2)
- Personalization based on viewing history (deferred)
- A/B testing infrastructure (manual measurement only)

✅ **In this release:**
- Shuffle-default
- A-Z override option
- Health checks
- Monitoring infrastructure

---

## Deployment Checklist

- [x] Code committed and privacy-checked
- [x] Build passes (TS, Jest, Vite)
- [x] Health check script created
- [x] Stewardship compliance verified
- [ ] **QA execution (your job)**
- [ ] Founder approval (after QA passes)
- [ ] A/B test configured (50/50 shuffle vs A-Z, 48h)
- [ ] Production deployment via safe_deploy_droplet.sh
- [ ] Post-deploy smoke test (health_check.sh)

---

## Running Tests Efficiently

### Parallel Testing
These can run in parallel (different browser tabs/windows):
- Search speed test (one tab)
- Directory shuffle test (another tab)
- Filtering tests (third tab)

### Serial Testing
These must run in order:
- Sort dropdown (affects subsequent shuffle tests)
- Filter combination tests (depend on shuffle being active)

### Fastest Path
1. Open 3 browser tabs
2. Tab 1: `/directory` → test shuffle
3. Tab 2: `/directory?q=health` → test search
4. Tab 3: `/directory?ntee=E` → test filters + shuffle
5. Each tab independently refresh and verify behavior
6. Run `bash scripts/health_check.sh` in terminal

**Estimated time:** 20 minutes for full Critical Path validation

---

## What Success Looks Like

✅ **Search:** Instant results, no timeouts  
✅ **Shuffle:** Random org on every page load (same session sees same order)  
✅ **Controls:** User can switch to A-Z anytime  
✅ **Filters:** Shuffle works within filtered subsets  
✅ **Regressions:** No new errors in console, all prior features work  
✅ **Health:** All health check endpoints return 200

---

## Troubleshooting

### "Shuffle not working" — Seeing same org always
- Clear browser cache (Ctrl+Shift+Delete)
- Clear localStorage (DevTools → Application → localStorage, delete daanaa_session_seed)
- Refresh page
- Expected: Different org appears

### "Sort dropdown not showing shuffle"
- Verify frontend build succeeded (`npm run build` green checkmark)
- Verify dev server reloaded (`npm run dev` shows vite rebuilding)
- Hard-refresh (Ctrl+Shift+R) to bypass cache

### "Health check failing"
- Verify API is running (`curl http://127.0.0.1:5000/health` returns 200)
- Check for port conflicts (`lsof -i :5000`)
- Check API logs for errors (`tail -50 logs/daanaa_api.log`)

### "Search timing out"
- Verify FTS index was rebuilt (`bash scripts/rebuild_fts_index_quick.sh`)
- Check API is responsive (`curl http://127.0.0.1:5000/api/stats`)
- If slow, run diagnostics (`python3 scripts/diagnose_search_perf.py`)

---

## Post-Test Cleanup

```bash
# 1. Stop API
pkill -f "python3 daanaa_api.py"

# 2. Stop frontend
# Ctrl+C in frontend terminal

# 3. Review results
# All tests passing?  → Proceed to deployment
# Any failures? → Debug + re-test specific area
```

---

## Expected Test Results

### Successful Outcomes
- ✅ All Priority 1 tests pass (search fast, shuffle works, controls available)
- ✅ All Priority 2 tests pass (events work, performance OK, FTS in sync)
- ✅ No new regressions in Priority 3 (prior fixes still working)
- ✅ Health check all green

### Acceptable Outcomes
- ✅ Edge cases (Priority 4) have known limitations (documented above)
- ✅ A/B testing deferred (manual measurement OK for MVP)
- ✅ Some cosmetic refinements deferred (not blocking ship)

### Unacceptable Outcomes
- ❌ Search still slow (> 1 second for common queries)
- ❌ Shuffle always shows same org (randomness broken)
- ❌ Can't switch back to A-Z (controls broken)
- ❌ Health check failing (downtime risk)
- ❌ Filtering broken (core feature regression)

---

## After Testing

1. **All pass?** → Document results, proceed to deployment
2. **Some fail?** → File issues, prioritize by severity:
   - **Blocker:** Anything in "Unacceptable" list
   - **High:** Priority 1 or 2 tests failing
   - **Low:** Priority 3 or 4 edge cases
3. **Questions?** → Refer to docs:
   - UX audit: `UX_AUDIT_DIRECTORY_2026_07_24.md`
   - Implementation: `DIRECTORY_UX_IMPROVEMENTS_PLAN.md`
   - Stewardship: `docs/STEWARDSHIP_COMPLIANCE_SHUFFLE_2026_07_24.md`

---

**Ready to test? Start with Critical Path tests above.**  
**Estimated total time: 45–60 minutes**  
**Report results back when complete.**
