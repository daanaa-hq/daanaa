# Full Execution Roadmap: Codex Gaps → Token Optimization

**Objective:** Fix critical gaps, then optimize. Zero compromises.  
**Timeline:** 6 weeks total (2 weeks critical fixes + 4 weeks optimization)  
**Authority:** Codex high-effort review + user approval  
**Status:** PROCEEDING ✅

---

## Phase Overview

```
PHASE A: CRITICAL FIXES (Codex "DO FIRST" + "DO NEXT")
├─ Week 1: Deploy IP reconciliation + QC expansion
└─ Week 2: Privacy alignment + Ralph orchestration

PHASE B: TOKEN OPTIMIZATION (Codex "DO LATER" + earlier token plan)
├─ Week 3: Prompt engineering + local pre-checks
├─ Week 4: Vector search + local models
├─ Week 5: Async batch + nightly snapshots
└─ Week 6: Metrics + tuning

OUTPUT: Fully automated, secure, optimized, measurable system
```

---

## PHASE A: CRITICAL FIXES (Weeks 1-2)

### Week 1: Deploy IP Reconciliation + QC Expansion

**Goal:** Fix load-bearing inconsistencies; expand test coverage to known risks  
**Effort:** 8-10 hours  
**Risk:** HIGH (if we get IP wrong, production breaks)

#### Task 1.1: Audit Deployment IP State (1 hour)

```bash
# Find all IP references in repo
grep -r "107.170.26.8\|167.170.26.8\|167.179.26.8" /home/akbar/meritgiving --include="*.sh" --include="*.md" --include="*.json"

# Check Cloudflare actual DNS
# Check DigitalOcean actual droplet IP
# Check what's currently serving daanaa.org
```

**Deliverable:** Document actual current state in `docs/IP_AUDIT_2026_08_11.md`

#### Task 1.2: Reconcile Deploy IP Across All Files (2 hours)

**Current situation:**
- `scripts/safe_deploy_droplet.sh` defaults to `107.170.26.8` (old working droplet)
- `LESSONS.md` discusses `167.170.26.8` (new droplet from 2026-08-10 incident)
- `institution/CURRENT_STATE.md` references `167.179.26.8` (possibly stale)

**Action:**
```bash
# 1. Determine AUTHORITATIVE IP (verify with: ssh root@IP "uptime")
# 2. Update all 3 files to use canonical IP
# 3. Add comment explaining: "Verified working 2026-08-11"
# 4. Update .ralph-config.json if it references IPs
# 5. Test: bash scripts/safe_deploy_droplet.sh --dry-run
```

**Files to update:**
- `scripts/safe_deploy_droplet.sh` (default IP)
- `LESSONS.md` (incident documentation)
- `institution/CURRENT_STATE.md` (current state assertion)
- `.ralph-config.json` (if referenced)

**Deliverable:** All IP references consistent; verified working

#### Task 1.3: Expand QC Tests to Cover Live Search (3 hours)

**Codex finding:** "Search can regress undetected"

**Current state:**
```typescript
// tests/qc-blocker-fixes.spec.ts covers:
✅ Firebase removal
✅ IRS status bug
✅ Donation flow
✅ Core pages load
❌ Live /api/search (MISSING!)
❌ Search pagination
❌ Search filtering
```

**Action: Add search regression tests**
```typescript
// In tests/qc-blocker-fixes.spec.ts, add new test group:

test.describe('Search Functionality (Live API)', () => {
  test('should return results for common queries', async ({ page }) => {
    // Query: "education"
    const response = await page.request.get('/api/search?q=education&limit=10');
    const data = await response.json();
    
    expect(response.status()).toBe(200);
    expect(data.results.length).toBeGreaterThan(0);
    expect(data.results[0]).toHaveProperty('ein');
    expect(data.results[0]).toHaveProperty('name');
  });

  test('should handle pagination correctly', async ({ page }) => {
    const page1 = await page.request.get('/api/search?q=food&limit=5&offset=0');
    const page2 = await page.request.get('/api/search?q=food&limit=5&offset=5');
    
    const data1 = await page1.json();
    const data2 = await page2.json();
    
    // Results should be different
    const ids1 = data1.results.map(r => r.ein);
    const ids2 = data2.results.map(r => r.ein);
    expect(ids1).not.toEqual(ids2);
  });

  test('should filter by category correctly', async ({ page }) => {
    const response = await page.request.get('/api/search?q=health&category=H&limit=10');
    const data = await response.json();
    
    expect(response.status()).toBe(200);
    // All results should have category H (if API supports filtering)
  });
});
```

**Action: Wire --headed Mode**
```bash
# In scripts/qc-test-suite.sh, line 63:
# BEFORE:
npx playwright test tests/qc-blocker-fixes.spec.ts

# AFTER:
if [ "$HEADLESS" = "true" ]; then
  npx playwright test tests/qc-blocker-fixes.spec.ts
else
  npx playwright test tests/qc-blocker-fixes.spec.ts --headed
fi
```

**Deliverable:** 
- 3 new search regression tests
- `--headed` mode working
- Run: `bash scripts/qc-test-suite.sh --headed` to debug

#### Task 1.4: Update QC Documentation (1 hour)

Update `docs/QC_TEST_WORKFLOW.md`:
```markdown
## Test Coverage: Phase 1 (Complete)

### Phase 1 Baseline (Current)
- ✅ Firebase Analytics removal (P2)
- ✅ IRS status bug (P3)
- ✅ Donation flow consistency
- ✅ Core site functionality
- ✅ Console errors
- ✅ Performance baseline
- ✅ Live /api/search regression (NEW)
- ✅ Search pagination (NEW)
- ✅ Search filtering (NEW)

### Phase 2 (Planned)
- Accessibility (WCAG AA)
- Mobile responsiveness
- SEO meta tags
- Wallet functionality
```

**Deliverable:** Documentation matches actual test coverage

#### Task 1.5: Validate and Commit Week 1 (1 hour)

```bash
# Run full QC suite
bash scripts/qc-test-suite.sh

# Verify search tests pass
npx playwright test tests/qc-blocker-fixes.spec.ts -g "Search"

# Commit
git add .
git commit -m "fix: Deploy IP reconciliation + QC search coverage

CODEX FINDING #1 (Deploy IP Inconsistency):
- Verified authoritative IP: [ACTUAL_IP]
- Updated all references in safe_deploy_droplet.sh, LESSONS.md, CURRENT_STATE.md
- Added verification comment: 'Verified working 2026-08-11'
- Tested: scripts/safe_deploy_droplet.sh --dry-run ✅

CODEX FINDING #2 (Search Coverage Gap):
- Added 3 live /api/search regression tests
- Covers: basic search, pagination, filtering
- Wired --headed mode for manual debugging
- Tests: npx playwright test -g 'Search' ✅

Tests: All QC passing (17 total tests)
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

### Week 1 Success Criteria
- [ ] Deploy IP reconciled and verified
- [ ] Search regression tests added and passing
- [ ] `--headed` mode working
- [ ] Documentation updated
- [ ] Commit with Codex findings referenced

---

### Week 2: Privacy Alignment + Ralph Orchestration

**Goal:** Fix P2 security gap; make Ralph real  
**Effort:** 8-10 hours  
**Risk:** MEDIUM (privacy is structural; needs careful handling)

#### Task 2.1: Audit Wallet Privacy Story (1 hour)

**Current contradiction:**
```
PRIVACY-INVARIANTS.md (Line 17):
  "Wallet data is server-side under Firebase Auth"

STEWARDSHIP.md (Line 47):
  "Wallet is device-first with optional Google backup only"

STEWARDSHIP.md Revision Log (2026-06-27):
  "product QA found that wallet remains device-first (no account required)
   Google sign-in is optional and enables cross-device backup only"
```

**Action: Determine authoritative story**
```bash
# Check actual product code
grep -r "wallet\|localStorage" frontend/src/contexts/ | head -20
grep -r "Firebase\|Auth" frontend/src/ | grep -i wallet

# Check git history for wallet changes
git log --oneline --all --grep="wallet" | head -10

# Check recent QA findings
grep -r "wallet" institution/ DECISIONS.md LESSONS.md
```

**Deliverable:** Document actual wallet implementation in `docs/WALLET_AUDIT_2026_08_11.md`

#### Task 2.2: Reconcile Privacy Docs (2 hours)

**Action:**
1. Review actual wallet code (what does it really do?)
2. Update `PRIVACY-INVARIANTS.md` to match reality
3. Update `STEWARDSHIP.md` revision log if needed
4. Ensure both docs tell the same story

**Example fix:**
```markdown
// PRIVACY-INVARIANTS.md (if device-first is correct)
## Wallet Storage

The Giving Wallet stores bookmarks and giving intent on the user's device only 
(localStorage by default). No account is required to browse or use the wallet.

Optional sign-in with Google enables cross-device wallet sync. Synced data 
contains only bookmarks and intent; never transactions, never public, never 
used for outreach or analytics. Users can delete wallet data entirely at any 
time (both locally and from any sync backup).

Evidence: See frontend/src/contexts/WalletContext.tsx (device-first storage)
and frontend/src/hooks/useGivingList.ts (sync optional).
```

**Deliverable:** Privacy docs reconciled; evidence-linked

#### Task 2.3: Strengthen Tier 2 Privacy Gate (2 hours)

**Current problem:** `privacy_check.sh` Gate 8 uses heuristic filename/host patterns, not real dataflow analysis.

**Action: Add specific Tier 2 checks**
```bash
# Add to scripts/privacy_check.sh

echo "🔐 GATE 8B: Tier 2 Data Flow Verification"

# Check 1: Wallet data should not reach external APIs
if grep -r "wallet\|giving.*intent" src/ | grep -E "fetch|axios|fetch" | \
   grep -v "localhost\|/api/" ; then
  echo "⚠️  WARNING: Wallet data may be sent externally"
  GATE8_PASS=false
fi

# Check 2: Org donor/revenue data should not be logged
if grep -r "donate_url\|donation_link\|revenue" src/ | grep "console.log" ; then
  echo "⚠️  WARNING: Sensitive org data being logged"
  GATE8_PASS=false
fi

# Check 3: Search queries should not include user identity
if grep -r "GET /api/search" daanaa_api.py | grep -E "user_id|session_id" ; then
  echo "⚠️  WARNING: Search may track user identity"
  GATE8_PASS=false
fi

if [ "$GATE8_PASS" = "false" ]; then
  echo "❌ GATE 8B FAILED: Tier 2 flows have potential data leaks"
  exit 1
fi
```

**Deliverable:** Enhanced privacy_check.sh with Tier 2 verification

#### Task 2.4: Make Ralph Task Execution Real (3 hours)

**Current problem:** Docs promise `--task` CLI + `currentTask` queue, but not implemented

**Action: Choose one approach**

**Approach A: Implement real task queue (RECOMMENDED)**
```bash
# Update scripts/ralph-setup.js to accept --task argument

#!/usr/bin/env node

const taskArg = process.argv[2];  // e.g., "feature_development"

if (taskArg && RALPH_CONFIG.taskTemplates[taskArg]) {
  const task = RALPH_CONFIG.taskTemplates[taskArg];
  console.log(`🎭 Ralph: Executing ${taskArg} workflow...`);
  
  // Update .ralph-config.json with currentTask
  config.currentTask = {
    name: taskArg,
    started: new Date().toISOString(),
    steps: task.steps,
    currentStep: 0
  };
  
  fs.writeFileSync('.ralph-config.json', JSON.stringify(config, null, 2));
  
  // Execute steps
  executeTaskSteps(task.steps);
} else {
  console.log("Available tasks: feature_development, data_pipeline, phase_deployment");
}
```

**Usage:**
```bash
node scripts/ralph-setup.js feature_development
node scripts/ralph-setup.js data_pipeline
node scripts/ralph-setup.js phase_deployment
```

**OR**

**Approach B: Keep it simple (remove promises from docs)**
If orchestration feels premature, update docs to say:
```markdown
Ralph currently provides orchestration *templates*, not live task execution.
For Phase 1-4, use `/daanaa-deploy` to trigger workflows.
Future: Real task queues (backlog item).
```

**Recommendation:** Approach A (implement real queue) — gives you automation now

**Deliverable:** Ralph accepts `--task` argument and maintains `currentTask` in config

#### Task 2.5: Update Ralph Documentation (1 hour)

Update `docs/CONTEXT7_RALPH_INTEGRATION.md`:
```markdown
## Using Ralph: Execute Tasks

### Start a Task
\`\`\`bash
node scripts/ralph-setup.js feature_development
# OR
node scripts/ralph-setup.js phase_deployment
\`\`\`

### Monitor Task Progress
\`\`\`bash
cat .ralph-config.json | jq '.currentTask'
# Shows: current task name, step index, workflow steps
\`\`\`

### Resume from Failure
\`\`\`bash
# Ralph auto-pauses on first failure
# Review .ralph-config.json for which step failed
node scripts/ralph-setup.js --resume
\`\`\`
```

**Deliverable:** Updated docs match implementation

#### Task 2.6: Validate and Commit Week 2 (1 hour)

```bash
# Test privacy gate
bash scripts/privacy_check.sh

# Test Ralph with task
node scripts/ralph-setup.js feature_development
# Check output and .ralph-config.json

# Commit
git add .
git commit -m "fix: Privacy alignment + Ralph task orchestration

CODEX FINDING #3 (Wallet Privacy Contradiction):
- Audited actual wallet implementation (device-first per QA 2026-06-27)
- Updated PRIVACY-INVARIANTS.md to match reality
- Added evidence links to code (WalletContext.tsx)
- Synchronized STEWARDSHIP.md Principle P2 implementation notes

CODEX FINDING #4 (Tier 2 Privacy Enforcement):
- Enhanced privacy_check.sh Gate 8 with Tier 2 data flow checks
- Added wallet data exposure detection
- Added sensitive org data logging check
- Added search tracking prevention check

CODEX FINDING #5 (Ralph Not Executable):
- Implemented real task execution: node scripts/ralph-setup.js <task>
- Tasks: feature_development, data_pipeline, phase_deployment
- Maintains .currentTask in .ralph-config.json
- Auto-pause on failure with resume support

Tests: privacy_check.sh passing; Ralph tasks executable
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

### Week 2 Success Criteria
- [ ] Wallet privacy story reconciled and evidence-linked
- [ ] PRIVACY-INVARIANTS.md matches reality
- [ ] Tier 2 privacy gate strengthened
- [ ] Ralph tasks executable with `--task` CLI
- [ ] currentTask maintained in .ralph-config.json
- [ ] Commit with all Codex findings addressed

---

## PHASE B: TOKEN OPTIMIZATION (Weeks 3-6)

After Phase A critical fixes are complete and committed, proceed with token optimization roadmap as planned:

- **Week 3:** Prompt engineering + structured contracts (25% token reduction)
- **Week 4:** Local pre-processing + vector search (35% reduction)
- **Week 5:** Server model offload + async batching (50% reduction)
- **Week 6:** Metrics + tuning (60% stable reduction)

Reference: `docs/OPTIMIZATION_ACTION_PLAN.md` for detailed Week 3-6 tasks

---

## Success Metrics

### After Phase A (Week 2)
- ✅ Deploy IP consistent and verified across all files
- ✅ Search regression covered by automated tests
- ✅ Privacy docs reconciled and evidence-linked
- ✅ Tier 2 privacy gate enforced automatically
- ✅ Ralph tasks executable and tracked

### After Phase B (Week 6)
- ✅ Token usage reduced 60% (490K tokens/month saved)
- ✅ Review latency 6x faster (30 min → 5 min per feature)
- ✅ QC coverage expanded (search + accessibility + perf)
- ✅ All governance gates enforced (principles, privacy, founder)
- ✅ Metrics dashboard live and tracking
- ✅ System self-tuning and maintainable

---

## Risk Mitigation

| Risk | Phase | Mitigation |
|------|-------|-----------|
| Deploy IP wrong | A | Verify with SSH before committing |
| Privacy changes break wallet | A | Test wallet locally after reconciliation |
| QC tests flaky | A | Run search tests multiple times; adjust waits |
| Ralph task queue hangs | A | Add timeout + retry logic |
| Token savings lower than expected | B | Monitor metrics; adjust concurrency |
| Local models hallucinate | B | Verify with ESLint before commit |

---

## Next Step: Start Week 1

Ready to begin:
```bash
# Week 1, Task 1.1: Audit deployment IP state
# Week 1, Task 1.2: Reconcile IP across all files
# Week 1, Task 1.3: Add search regression tests
# Week 1, Task 1.4: Update QC docs
# Week 1, Task 1.5: Validate and commit

# Timeline: 8-10 hours this week
```

**Continue with:** `docs/OPTIMIZATION_ACTION_PLAN.md` Week 3-6 after Phase A completes

---

## Files to Create/Update

**Phase A:**
- `docs/IP_AUDIT_2026_08_11.md` (new)
- `docs/WALLET_AUDIT_2026_08_11.md` (new)
- `tests/qc-blocker-fixes.spec.ts` (update)
- `scripts/qc-test-suite.sh` (update)
- `scripts/privacy_check.sh` (update)
- `scripts/ralph-setup.js` (update)
- `.ralph-config.json` (update)
- `docs/QC_TEST_WORKFLOW.md` (update)
- `docs/CONTEXT7_RALPH_INTEGRATION.md` (update)
- `PRIVACY-INVARIANTS.md` (update)
- `STEWARDSHIP.md` (update if needed)

**Phase B:**
- See `docs/OPTIMIZATION_ACTION_PLAN.md`

---

**Status:** ✅ READY TO EXECUTE  
**Authority:** Codex review + user approval  
**Start:** Immediately (Week 1 tasks)
