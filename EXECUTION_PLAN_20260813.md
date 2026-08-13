# Execution Plan — Batch 1 + Tasks #10 & #11
**Date:** 2026-08-13  
**Status:** ✅ APPROVED FOR EXECUTION  
**Owner:** Claude Code + Codex  

---

## Phase 1: Local Testing (You at Server)

### Step 1: Browser Testing — Batch 1 (15 min)

**When:** When you return to server  
**Location:** http://localhost:3001 in Brave browser

**Test Checklist:**

#### Homepage (http://localhost:3001)
- [ ] Page loads without red errors (F12 → Console tab)
- [ ] "Choose your path" section visible (below hero)
- [ ] 3 cards show: Search, Volunteer, Compare
- [ ] Each card has icon + description + CTA arrow
- [ ] Click "Browse directory" card → navigates to /directory
- [ ] Click "Open Giving Wallet" card → navigates to /wallet
- [ ] No console errors after interactions

#### Directory (http://localhost:3001/directory)
- [ ] Page loads HTTP 200
- [ ] Filter pills show: "All", then 8 featured causes (E, B, P, C, D, A, O, S)
- [ ] "Browse all →" link appears at end of pills
- [ ] Type in search bar → NO dropdown suggestions (performance fix)
- [ ] Search returns results fast
- [ ] Click a cause pill → filters results
- [ ] Click "Browse all" → opens full cause list filter sheet
- [ ] No console errors

#### Org Detail (http://localhost:3001/org/NY0101234567)
- [ ] Page loads without errors
- [ ] Org info displays correctly

#### Console Check (F12)
- [ ] No red errors
- [ ] No "Failed to fetch" warnings
- [ ] No TypeErrors or ReferenceErrors

**Report:**
- ✅ All tests pass → Ready for production deploy
- ❌ Found issues → Report what, where, and reproduce steps

---

## Phase 2: Production Deployment (If Tests Pass)

### Step 2: Deploy to daanaa.org (5 min)

**When:** After local tests pass  
**What:** Push Batch 1 code (3 commits) to production

```bash
# Verify current branch
git branch -v

# Push to origin
git push origin master

# Verify on droplet
ssh root@167.170.26.8 "cd /home/akbar/meritgiving && git pull && npm run build"

# Smoke test
curl https://daanaa.org/directory | grep "Browse all" && echo "✅ Deployed"
```

**Rollback (If needed):**
```bash
git reset --hard f9d6290437d
git push -f origin master
```

---

## Phase 3: Task #10 Handoff (Codex)

### Step 3: Website Discovery Verification Commit

**Owner:** Codex  
**What:** Implement dedup analysis findings

**Checklist:**
- [ ] Read `TASK10_WEBSITE_DISCOVERY_DEDUP_ANALYSIS_20260813.md`
- [ ] Confirm HTTP status distribution (87,039 active, 37,871 dead, etc.)
- [ ] Confirm dedup classes (931 platform aggregators, 1,567 umbrella/chapter, 16,810 nulls)
- [ ] Create `WEBSITE_DISCOVERY_DEDUP_RULES.md` with:
  - Why facebook.com and google.com are excluded
  - How to mark in API response
  - Trade-off rationale (lose 931 browse points, gain honesty)
- [ ] Tag umbrella/chapter relationships (1,567 orgs):
  - Phi Theta Kappa: 191 orgs
  - Kappa Delta Pi: 328 orgs
  - Beta Gamma Sigma: 224 orgs
  - Others: 594 orgs
- [ ] Create `website_discovery_verification_20260813.json` with all metrics
- [ ] Push verification commit with message from doc

**Expected Time:** 4–6 hours  
**Deliverable:** Public commit + tagged dedup data

---

## Phase 4: Task #11 Implementation (Claude + Codex)

### Step 4: Small Org Visibility Phase 1 Kickoff

**Owner:** Claude Code (UX) + Codex (API/backend)  
**Timeline:** 90 days (Week 1–12)

**Week 1–2: Foundation**
- [ ] Codex: Build `/api/organizations/nearby?zip=ZIP&radius=MI&sort=relevance` endpoint
- [ ] Claude: Design "Find near me" section (homepage) + local discovery tab (directory)
- [ ] Claude: Design volunteer-first discovery flow (`/directory?mode=volunteer`)
- [ ] Data: Re-parse 16,810 null domains, recover ~2K–4K sites

**Week 3–4: Launch to Staging**
- [ ] Frontend: Implement local discovery UX
- [ ] Frontend: Implement volunteer-first route
- [ ] QA: Test all new flows
- [ ] Deploy to staging (not production yet)

**Week 5–8: Elevate Proven-But-Unknown**
- [ ] Backend: Filter "financially healthy + small" cohort
- [ ] UX: Add filter checkbox to directory
- [ ] UX: Add "Help needed" section to org pages
- [ ] Integration: Wayback Machine fallback for dead sites

**Week 9–12: Measure & Plan Phase 2**
- [ ] Analytics: Set up Plausible tracking + DB audit queries
- [ ] Research: Collect user behavior data
- [ ] Survey: Get donor feedback on small-org discovery
- [ ] Plan: Phase 2 roadmap (alumni, profession, veteran paths)

**Success Metrics to Track:**
- Micro-org website coverage: 19% → 22%
- Local discovery sessions: 0 → 5K/month
- Volunteer inquiries (small orgs): 20 → 200+/month
- Small-org repeat visitor: 3% → 8%

**Handoff Document:** `TASK11_SMALL_ORG_VISIBILITY_ROADMAP_20260813.md`

---

## Current Status

| Task | Status | What's Done | What's Next |
|------|--------|------------|------------|
| **Batch 1** | 🟡 Ready | Code committed, servers running | You: Test locally. Then: Deploy to production. |
| **Task #10** | 🟡 Ready | Analysis complete, documents written | Codex: Implement verification commit |
| **Task #11** | 🟡 Ready | Roadmap documented, Phase 1 defined | Claude+Codex: Start Week 1 work |

---

## Files Created Today

```
✅ BATCH1_LOCAL_DEPLOYMENT_20260813.md
   → Testing checklist + server status
   
✅ TASK10_WEBSITE_DISCOVERY_DEDUP_ANALYSIS_20260813.md
   → HTTP status distribution, dedup classes, coverage metrics
   → Umbrella/chapter mapping (PTK, KDP, BGS)
   → Null domain recovery strategy
   → Commit checklist for Codex
   
✅ TASK11_SMALL_ORG_VISIBILITY_ROADMAP_20260813.md
   → Behavioral science foundation
   → Phase 1 roadmap (90 days)
   → Success metrics
   → Stewardship alignment
   
✅ EXECUTION_PLAN_20260813.md (this file)
   → Step-by-step execution with owners and timelines
```

---

## Decision Points Confirmed

✅ **Batch 1:** Test locally, then deploy to production  
✅ **Task #10:** Full dedup analysis + verification commit (Codex)  
✅ **Task #11:** Full Phase 1 implementation (90 days, local + volunteer)  

---

## What You Do When You Return to Server

1. **Test Batch 1** (15 min)
   - Open http://localhost:3001 in Brave
   - Follow checklist above
   - Report pass/fail

2. **If Pass:** Deploy to Production (5 min)
   - git push origin master
   - Verify on daanaa.org

3. **Review & Approve Task #10** (10 min)
   - Read dedup findings
   - Confirm API exclusion rules (facebook.com, google.com)
   - Give Codex green light

4. **Kick Off Task #11** (informal)
   - Share roadmap link with team
   - Set Week 1 goals
   - Assign leads (Claude Code for UX, Codex for API)

---

## Communication Plan

**To Codex:**
- Task #10: "Analysis ready. Implement verification commit per checklist."
- Task #11: "Roadmap approved. Ready for Phase 1 Week 1 kickoff."

**To Team:**
- "Batch 1 deployed to daanaa.org. New discovery paths live."
- "Website dedup analysis complete. Phase 1 visibility roadmap approved for 90-day sprint."

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Local tests fail | Rollback: `git reset --hard f9d6290437d` → Fix issues → Re-test |
| Production deploy breaks | Rollback: `git reset --hard f9d6290437d && git push -f` → Verify → Retry |
| Codex dedup commit has issues | Code review before merge; rollback if needed |
| Phase 1 timeline unrealistic | Weekly standup + adjust scope; defer Phase 1.2 if needed |

---

## Completion Criteria

- [ ] Batch 1: Local tests pass
- [ ] Batch 1: Deployed to daanaa.org + verified live
- [ ] Task #10: Verification commit pushed by Codex
- [ ] Task #11: Week 1 work started (API + UX design)
- [ ] Artifacts: All documents accessible to team

---

**Status: APPROVED & READY TO EXECUTE**

When you return to the server, start with Step 1. Report results, and we'll proceed accordingly.
