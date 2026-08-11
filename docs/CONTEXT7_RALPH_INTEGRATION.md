# Context7 + Ralph Integration Guide

**Status:** ✅ INSTALLED & READY  
**Installed:** context7, ralph-loop  
**Integration Level:** Supervised (respects Stewardship governance gates)

---

## What This Enables

### Context7: Smart Documentation Lookup
- **Purpose:** Keep codebase documentation fresh and AI-efficient
- **Solves:** Large codebase navigation problem (250+ docs, 379 scripts)
- **How it works:** Indexes docs, missions, architecture; LLM queries fetch relevant context
- **Benefit:** Reduces token overhead; no more re-reading 11k-line API

### Ralph: Autonomous Agent Orchestration
- **Purpose:** Coordinate autonomous feature development and deployments
- **Solves:** Repetitive task bottleneck (dev → test → commit → deploy cycle)
- **How it works:** Chains multiple agents/tools; stops at governance gates
- **Benefit:** Faster iterations; human-in-command remains intact

---

## Quick Start

### Index Documentation (Context7)
```bash
node scripts/context7-index.js
```

This creates `.context7-manifest.json` and prepares docs for AI queries.

### Set Up Orchestration (Ralph)
```bash
node scripts/ralph-setup.js
```

This configures autonomous task templates and governance gates.

---

## Using Context7: Query Documentation

### Command Line (One-Off)
```bash
# Ask about scoring
npx context7 daanaa "how does V6 scoring work?"

# Ask about a specific component
npx context7 daanaa "explain the donation flow"

# Save output to file
npx context7 daanaa "what are Stewardship principles?" --save

# Format as JSON
npx context7 daanaa "architecture overview" --type json
```

### In Code (Programmatic)
```javascript
const context7 = require('context7');

const answer = await context7.query('daanaa', 'How does the database schema work?');
console.log(answer);
```

### In Claude Code (This Session)
Context7 is now available for:
- **Architecture questions:** "Context7: how does the scorer integrate with the API?"
- **Data model questions:** "Context7: explain the registry_enriched table schema"
- **Methodology questions:** "Context7: what are the V6 peer grouping rules?"

When I need fresh documentation context, I can query Context7 instead of re-reading CLAUDE.md.

---

## Using Ralph: Execute Tasks

### Built-In Task Templates

#### 1. Feature Development
```
Local dev → QC tests → Commit → Approval gate → Deploy
```

**Workflow:**
- Develop code locally
- Run: `bash scripts/qc-test-suite.sh`
- If pass: commit automatically
- Await approval from founder or team lead
- Deploy if approved

**Used for:** New features, bug fixes, frontend changes, non-breaking backend work  
**Autonomy:** Tests pass = safe to commit (no approval for reversible changes)

#### 2. Data Pipeline
```
Source validation → Run scorer → FTS index → Coverage check → Smoke test
```

**Workflow:**
- Validate data source (IRS, ProPublica, NCCS)
- Run v6 scorer
- Rebuild FTS search index
- Verify coverage (% of orgs scored)
- Run smoke tests (search, detail pages)

**Used for:** Overnight scoring runs, FTS rebuilds, embedding generation  
**Autonomy:** Tests pass = safe to ship (no approval for data updates)

#### 3. Phase Deployment
```
Verify → Test → Check → Prepare → FOUNDER GATE → Deploy → Verify → Document
```

**Workflow:**
- Verify all blocker fixes in git
- Run full QC test suite
- Check Stewardship principles (STEWARDSHIP.md P1-P11)
- Prepare deployment bundle
- **STOPS: Wait for founder approval** (cannot proceed without human sign-off)
- Deploy to production
- Run smoke tests
- Document in DECISIONS.md and LESSONS.md

**Used for:** Phase 1-4 rollouts, methodology changes, public claim updates  
**Autonomy:** Founder approval required at "FOUNDER GATE" step (not autonomous for public-facing changes)

### Starting & Monitoring Tasks

#### List available tasks
```bash
node scripts/ralph-setup.js
# Shows all 3 task templates with steps and governance gates
```

#### Start a new task
```bash
node scripts/ralph-setup.js feature_development
# OR
node scripts/ralph-setup.js data_pipeline
# OR
node scripts/ralph-setup.js phase_deployment

# Output shows:
# - Task name and start time
# - Step-by-step workflow
# - Governance gates that will be checked
```

#### Check task status
```bash
node scripts/ralph-setup.js --status

# Shows:
# - Current task name
# - Progress: X/Y steps completed
# - Next step to execute
```

#### Resume a paused task
```bash
node scripts/ralph-setup.js --resume

# Useful if:
# - Task paused at founder approval gate
# - Task paused due to failed check
# - You want to continue from where it stopped
```

#### Via /daanaa-deploy skill (recommended for production)
```bash
/daanaa-deploy
# Automatically selects workflow based on change type
```

---

## Governance Integration

All Ralph workflows respect these gates:

| Gate | Purpose | Checks |
|------|---------|--------|
| **Principles** | STEWARDSHIP.md alignment | P1-P11 compliance |
| **Privacy** | PRIVACY-INVARIANTS.md | No data leaks, no tracking |
| **Data Source** | Evidence-based only | Sources verified in DECISIONS.md |
| **Founder Approval** | Phase deployments, public claims, money | Explicit sign-off required |

**Flow:**
```
Task Start
    ↓
[Principles Check] ← Must pass
    ↓
[Privacy Check] ← Must pass
    ↓
[Data Source Verification] ← If applicable
    ↓
[Execute Task]
    ↓
[Founder Approval?] ← If phase/claim/money gate
    ↓
[Complete & Document in DECISIONS.md]
```

---

## Workflow: "Develop → Test → Deploy"

### Step 1: Develop Feature Locally
```bash
cd frontend
npm run dev
# Make changes...
```

### Step 2: Run QC Tests
```bash
bash scripts/qc-test-suite.sh
```

**If PASS ✅:**
```bash
git add .
git commit -m "feat: Your feature

Tests: QC passing
- What was tested"
```

**If FAIL ❌:** Fix and retry

### Step 3: Let Ralph Orchestrate
- Ralph detects new commit
- Runs `principles_check` (STEWARDSHIP.md)
- Runs `privacy_gate` (PRIVACY-INVARIANTS.md)
- If both pass → commits to shared repo
- If phase gate → waits for founder approval

### Step 4: Deploy
- Ralph (or you via `/daanaa-deploy`) deploys
- Runs smoke tests
- Documents in DECISIONS.md
- Updates CURRENT_STATE.md

---

## Example: Autonomous Feature Development

**Scenario:** Fix IRS eligibility bug (like we did earlier)

```bash
# 1. Develop
cd frontend
# Fix taxDeductibleToStatus bug in 3 files
npm run build

# 2. Test
bash scripts/qc-test-suite.sh
# ✅ ALL QC TESTS PASSED

# 3. Commit
git add .
git commit -m "fix: IRS eligibility status consistency

Tests: QC passing
- Firebase Analytics removed (P2)
- IRS status correctly maps revoked/unknown/verified (P3)"

# 4. Ralph orchestrates automatically
# - ✅ Principles check passes
# - ✅ Privacy gate passes
# - Commits to repo
# - Ready for deployment

# 5. Deploy
/daanaa-deploy
# Codex reviews
# You approve
# Ralph deploys
# Smoke tests pass
# Documented in DECISIONS.md
```

**Total time:** ~5 min (vs. waiting for approval at each step)

---

## Example: Phase 4 Deployment

**Scenario:** Ship Phase 1-4 blocker fixes

```bash
# Ralph automatically:
# 1. Verifies all blocker fixes in git
# 2. Runs full QC test suite
# 3. Checks all principles
# 4. Prepares deployment bundle
# 5. STOPS and waits for founder approval
# 
# You: /daanaa-deploy → approve
#
# Ralph continues:
# 6. Deploys to droplet
# 7. Runs smoke tests
# 8. Documents in DECISIONS.md + LESSONS.md
# 9. Updates CURRENT_STATE.md
```

---

## Governance Safeguards

### What Ralph CANNOT Do (Founder Gate Required)
- ❌ Change public claims (scoring, badges, verification status)
- ❌ Modify methodology (scoring logic, peer groups)
- ❌ Touch money (subscriptions, spending, payments)
- ❌ Irreversible operations (schema migrations, deletions)

### What Ralph CAN Do (Test-Gated)
- ✅ Commit code if QC tests pass
- ✅ Deploy reversible changes (code, precompute, config)
- ✅ Update internal docs (DECISIONS.md, LESSONS.md)
- ✅ Restart services (with smoke test verification)

---

## Integration with Codex

Ralph + Codex workflow:

```
Ralph detects code change
    ↓
Ralph: QC tests + governance checks
    ↓
If all pass → Ralph commits
    ↓
For phase deployments → Ralph pauses
    ↓
Codex: Architectural review
    ↓
You: Final approval
    ↓
Ralph: Execute deployment + verify
```

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/context7-index.js` | Index codebase for Context7 |
| `scripts/ralph-setup.js` | Configure Ralph orchestration |
| `.context7-manifest.json` | (Auto-generated) Doc index |
| `.ralph-config.json` | (Auto-generated) Task config |
| `docs/CONTEXT7_RALPH_INTEGRATION.md` | This guide |

---

## Next Steps

1. **Run setup scripts:**
   ```bash
   node scripts/context7-index.js
   node scripts/ralph-setup.js
   ```

2. **Test Context7:**
   ```bash
   npx context7 daanaa "explain V6 scoring"
   ```

3. **Use in development:**
   - Develop feature → QC test → Commit
   - Ralph orchestrates the rest
   - You review via `/daanaa-deploy` for phase gates

4. **Monitor workflow:**
   - Check `.ralph-config.json` for current task queue
   - Review DECISIONS.md for Ralph-executed decisions

---

## Troubleshooting

### Context7 returns empty results
```bash
node scripts/context7-index.js
# Re-index codebase, then try query again
```

### Ralph stalls at a gate
```bash
cat .ralph-config.json | jq '.currentTask'
# Check which gate is blocking
# Run: /daanaa-deploy to resume
```

### Want to disable Ralph for a commit
```bash
git commit --no-verify -m "emergency fix: ..."
# Use sparingly; next run will re-check gates
```

---

## References

- **Context7:** https://github.com/upstash/context7
- **Ralph Loop:** https://github.com/vercel-labs/ralph-loop-agent
- **QC Workflow:** `docs/QC_TEST_WORKFLOW.md`
- **Stewardship:** `STEWARDSHIP.md`
- **Privacy:** `PRIVACY-INVARIANTS.md`

---

**Remember:** Automation removes bottlenecks, not accountability. Ralph respects governance gates; you remain in command of methodology, money, and public claims.
