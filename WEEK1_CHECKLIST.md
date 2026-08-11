# Week 1 Execution Checklist: Deploy IP + QC Search Coverage

**Target:** Complete by end of week  
**Effort:** 8-10 hours  
**Risk:** HIGH (IP is load-bearing; must verify)

---

## Task 1.1: Audit Deployment IP State ⏱️ 1 hour

### Step 1: Find all IP references
```bash
cd /home/akbar/meritgiving

# Find all references
grep -r "107.170.26.8\|167.170.26.8\|167.179.26.8" . \
  --include="*.sh" --include="*.md" --include="*.json" | tee /tmp/ip_audit.txt

# Count by file
echo "IP references by file:"
grep -r "107.170.26.8\|167.170.26.8\|167.179.26.8" . \
  --include="*.sh" --include="*.md" --include="*.json" | cut -d: -f1 | sort | uniq -c
```

### Step 2: Check current production IP
```bash
# Option 1: SSH to known working IP (old droplet)
ssh root@107.170.26.8 "uptime"
# Should show: system is running

# Option 2: SSH to new droplet (if it's running)
ssh root@167.170.26.8 "uptime"
# Check if it responds

# Option 3: Check Cloudflare DNS
dig daanaa.org +short
# Should show the IP currently in production
```

### Step 3: Verify via curl
```bash
# Test old IP
curl -w "HTTP %{http_code}\n" -o /dev/null https://167.170.26.8/health 2>/dev/null

# Test from production domain
curl -w "HTTP %{http_code}\n" -o /dev/null https://daanaa.org/health
```

### Step 4: Document findings
```bash
# Create audit doc
cat > docs/IP_AUDIT_2026_08_11.md << 'EOF'
# Deployment IP Audit (2026-08-11)

## References Found
- scripts/safe_deploy_droplet.sh: defaults to 107.170.26.8
- LESSONS.md: discusses 167.170.26.8 (from 2026-08-10 incident)
- institution/CURRENT_STATE.md: references 167.179.26.8

## Actual State
- Production domain (daanaa.org): Currently serving from [ACTUAL_IP]
- Old droplet (107.170.26.8): [Status: working/down]
- New droplet (167.170.26.8): [Status: working/down]

## Recommendation
Authoritative IP should be: [ACTUAL_IP]
All scripts/docs should reference this IP.

Date: 2026-08-11 | Verified by: [your name]
EOF
```

### ✅ Checklist
- [ ] Found all IP references
- [ ] Tested production connectivity
- [ ] Determined authoritative IP
- [ ] Created IP_AUDIT_2026_08_11.md

---

## Task 1.2: Reconcile IP Across All Files ⏱️ 2 hours

### Step 1: Update scripts/safe_deploy_droplet.sh
```bash
# Find the line with the default IP
grep -n "107.170.26.8\|167.170.26.8\|DROPLET_IP" scripts/safe_deploy_droplet.sh | head -5

# Edit the file to set AUTHORITATIVE_IP
# Example (if 167.170.26.8 is authoritative):
# OLD: DROPLET_IP="${1:-107.170.26.8}"
# NEW: DROPLET_IP="${1:-167.170.26.8}"

# Add verification comment
# NEW: # Verified working 2026-08-11
```

### Step 2: Update LESSONS.md
```bash
# Check current incident documentation
grep -A5 -B5 "167.170.26.8" LESSONS.md

# Add note at end of 2026-08-11 incident section:
# "Resolution: IP reconciled to [ACTUAL_IP] across all files (2026-08-11)"
```

### Step 3: Update institution/CURRENT_STATE.md
```bash
# Find IP reference
grep -n "167.179.26.8\|167.170.26.8\|107.170.26.8" institution/CURRENT_STATE.md

# Update to authoritative IP
# Add verification: "Verified 2026-08-11"
```

### Step 4: Update .ralph-config.json if needed
```bash
# Check if it references IP
grep -i "ip\|host\|droplet" .ralph-config.json

# If it does, update to authoritative IP
```

### Step 5: Test
```bash
# Verify scripts still work
bash scripts/safe_deploy_droplet.sh --dry-run

# Should show: "Would deploy to [AUTHORITATIVE_IP]"
```

### ✅ Checklist
- [ ] Updated scripts/safe_deploy_droplet.sh
- [ ] Updated LESSONS.md
- [ ] Updated institution/CURRENT_STATE.md
- [ ] Updated .ralph-config.json (if needed)
- [ ] Verified with --dry-run
- [ ] All IP references now point to authoritative IP

---

## Task 1.3: Add Search Regression Tests ⏱️ 3 hours

### Step 1: Understand current test structure
```bash
# Review existing tests
head -50 tests/qc-blocker-fixes.spec.ts

# Run existing tests to baseline
npx playwright test tests/qc-blocker-fixes.spec.ts
```

### Step 2: Add search test group
```bash
# Open tests/qc-blocker-fixes.spec.ts and add after existing test groups:

cat >> tests/qc-blocker-fixes.spec.ts << 'EOF'

  // ============================================================================
  // SEARCH REGRESSION TESTS (Live /api/search)
  // ============================================================================

  test.describe('Search API Regression', () => {
    test('should return search results for common queries', async ({ page }) => {
      // Test education query
      const response = await page.request.get('http://localhost:5173/api/search?q=education&limit=10');
      
      const data = await response.json();
      
      expect(response.status()).toBe(200);
      expect(data).toHaveProperty('results');
      expect(data.results.length).toBeGreaterThan(0);
      expect(data.results[0]).toHaveProperty('ein');
      expect(data.results[0]).toHaveProperty('name');
      
      console.log(`Search results: ${data.results.length} orgs found`);
    });

    test('should handle pagination correctly', async ({ page }) => {
      const page1 = await page.request.get('http://localhost:5173/api/search?q=food&limit=5&offset=0');
      const page2 = await page.request.get('http://localhost:5173/api/search?q=food&limit=5&offset=5');
      
      expect(page1.status()).toBe(200);
      expect(page2.status()).toBe(200);
      
      const data1 = await page1.json();
      const data2 = await page2.json();
      
      // Both pages should have results
      expect(data1.results.length).toBeGreaterThan(0);
      expect(data2.results.length).toBeGreaterThan(0);
      
      // Results should be different (pagination working)
      const ids1 = data1.results.map(r => r.ein);
      const ids2 = data2.results.map(r => r.ein);
      const overlap = ids1.filter(id => ids2.includes(id));
      expect(overlap.length).toBe(0); // No overlap between pages
      
      console.log(`Pagination: page 1 has ${ids1.length} orgs, page 2 has ${ids2.length} orgs`);
    });

    test('should handle empty search results gracefully', async ({ page }) => {
      const response = await page.request.get('http://localhost:5173/api/search?q=zzzzzzzzzzzzzzz&limit=10');
      
      expect(response.status()).toBe(200);
      const data = await response.json();
      expect(data.results.length).toBe(0);
    });
  });
EOF
```

### Step 3: Wire --headed mode
```bash
# Edit scripts/qc-test-suite.sh, find the test execution section (around line 63)

# BEFORE:
#   npx playwright test tests/qc-blocker-fixes.spec.ts

# AFTER (add support for --headed flag):
if [ "$HEADLESS" = "false" ]; then
  echo -e "${YELLOW}Running in headed mode (browser visible)...${NC}"
  npx playwright test tests/qc-blocker-fixes.spec.ts --headed
else
  npx playwright test tests/qc-blocker-fixes.spec.ts
fi
```

### Step 4: Test the new tests
```bash
# Make sure API is running
npm run dev &  # in frontend directory
# OR if you have API running separately

# Run just search tests
npx playwright test tests/qc-blocker-fixes.spec.ts -g "Search"

# Run in headed mode for debugging
bash scripts/qc-test-suite.sh --headed
```

### Step 5: Fix any failures
```bash
# If tests fail, check:
# 1. Is dev server running? (should be on port 5173)
# 2. Is API available? (should be on port 5000)
# 3. Are search queries returning results?

# Debug
curl http://localhost:5173/api/search?q=education

# If still failing, add more waits:
# await page.waitForLoadState('networkidle');
# await page.waitForTimeout(500);
```

### ✅ Checklist
- [ ] Added 3 search regression tests to qc-blocker-fixes.spec.ts
- [ ] Tests cover: basic search, pagination, empty results
- [ ] Wired --headed flag in qc-test-suite.sh
- [ ] Tests pass: `npx playwright test -g "Search" ✅`
- [ ] Verified --headed mode works

---

## Task 1.4: Update QC Documentation ⏱️ 1 hour

### Step 1: Update docs/QC_TEST_WORKFLOW.md

Find the "Test Coverage" section and update:

```markdown
## Test Coverage: Blocker Fixes (Phase 1)

### Current Coverage
- ✅ Firebase Analytics removed (P2 compliance)
- ✅ IRS eligibility status fixed (P3 trust signal)
- ✅ Donation flow consistent
- ✅ Core site functionality
- ✅ Console errors (no critical errors)
- ✅ Performance baseline (3s org detail, 1s search)
- ✅ Live /api/search regression (NEW - Codex finding)
- ✅ Search pagination (NEW)
- ✅ Search empty results (NEW)

**Total Tests:** 17 test cases across 8 test groups

### Phase 2 Planned Coverage (Future)
- Accessibility (WCAG AA)
- Mobile responsiveness
- SEO meta tags
- Wallet functionality
- Org detail page regressions
```

### Step 2: Add troubleshooting section
```markdown
## Debugging Failed Tests

### headed mode
\`\`\`bash
# Run tests in browser (you can see what's happening)
bash scripts/qc-test-suite.sh --headed
\`\`\`

### Search tests specifically
\`\`\`bash
# Run only search regression tests
npx playwright test tests/qc-blocker-fixes.spec.ts -g "Search"

# If failing, check:
curl http://localhost:5173/api/search?q=education
# Should return results
\`\`\`
```

### ✅ Checklist
- [ ] Updated test coverage section in docs/QC_TEST_WORKFLOW.md
- [ ] Added troubleshooting for headed mode
- [ ] Updated total test count (17)

---

## Task 1.5: Validate and Commit ⏱️ 1 hour

### Step 1: Run full QC suite
```bash
bash scripts/qc-test-suite.sh
# Should see: ✅ ALL QC TESTS PASSED
```

### Step 2: Verify changes
```bash
# Check what's changed
git status

# Review changes
git diff scripts/safe_deploy_droplet.sh
git diff tests/qc-blocker-fixes.spec.ts
git diff scripts/qc-test-suite.sh
```

### Step 3: Create commit
```bash
git add -A

git commit -m "fix: Deploy IP reconciliation + QC search coverage (Week 1)

CODEX FINDING #1: Deploy IP Inconsistency (CRITICAL)
- Reconciled 3 conflicting IPs across repo
  • scripts/safe_deploy_droplet.sh: [AUTHORITATIVE_IP]
  • LESSONS.md: updated incident note
  • institution/CURRENT_STATE.md: updated current state
- Verified with: ssh root@[IP] && curl https://daanaa.org/health
- Status: All references now consistent

CODEX FINDING #2: Search Regression Gap
- Added 3 live /api/search regression tests
  • Basic search query results (education)
  • Pagination: offset/limit works correctly
  • Empty results handled gracefully
- Wired --headed mode for manual debugging
- Updated docs/QC_TEST_WORKFLOW.md with new coverage

QC Test Suite Status:
✅ 17 total tests (10 from blockers + 3 from search + 4 other)
✅ All passing
✅ Includes live API calls to /api/search

See docs/IP_AUDIT_2026_08_11.md for IP reconciliation details.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

### Step 4: Push
```bash
git log --oneline -5  # Verify commit
git push origin master
```

### ✅ Checklist
- [ ] Full QC suite passes (17/17 tests)
- [ ] All changes reviewed with git diff
- [ ] Commit created with Codex findings referenced
- [ ] Changes pushed to master

---

## Week 1 Summary

### Starting State
- Deploy IP references inconsistent (3 different IPs)
- QC tests don't cover live search (known Codex gap)
- `--headed` mode documented but not wired
- Privacy story contradictions exist (for Week 2)

### Ending State (After Week 1)
- ✅ Deploy IP consistent and verified across all files
- ✅ 3 live search regression tests added and passing
- ✅ Manual debugging (--headed mode) working
- ✅ All documentation updated
- ✅ Commit with Codex findings referenced

### Files Modified
1. `docs/IP_AUDIT_2026_08_11.md` (new)
2. `scripts/safe_deploy_droplet.sh` (IP reconciliation)
3. `LESSONS.md` (incident note update)
4. `institution/CURRENT_STATE.md` (IP update)
5. `.ralph-config.json` (if needed)
6. `tests/qc-blocker-fixes.spec.ts` (add search tests)
7. `scripts/qc-test-suite.sh` (wire --headed)
8. `docs/QC_TEST_WORKFLOW.md` (update coverage)

### Next: Week 2
After Week 1 commit is pushed, proceed to **Week 2: Privacy Alignment + Ralph Orchestration**
- Reconcile wallet privacy story (P2 security fix)
- Make Ralph task execution real
- See `docs/EXECUTION_ROADMAP.md` Week 2 section

---

**Ready to start? Run:**
```bash
cd /home/akbar/meritgiving
# Task 1.1
grep -r "107.170.26.8\|167.170.26.8\|167.179.26.8" . --include="*.sh" --include="*.md" --include="*.json"
```

Let me know when each task is done, or if you hit any blockers! ⏱️
