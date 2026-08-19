# Codex Review Gate — Quality Checkpoint

**Principle:** Claude reviews all Codex-suggested changes before deployment.

## Review Checklist (Before Commit/Deploy)

When Codex completes a task:

1. **Read the Code Diff**
   - [ ] What files changed?
   - [ ] Read the actual modifications
   - [ ] Does it match the issue description?

2. **Verify the Fix**
   - [ ] Does it address the root cause?
   - [ ] Are there side effects?
   - [ ] Test locally if possible

3. **Stewardship Check**
   - [ ] No new evaluative judgments?
   - [ ] No visibility ranking changes?
   - [ ] Data sources properly labeled?
   - [ ] Privacy boundaries intact?

4. **Quality Check**
   - [ ] Build passes?
   - [ ] No new console errors?
   - [ ] Accessibility not degraded?
   - [ ] Performance baseline maintained?

5. **Commit & Document**
   - [ ] Write clear commit message
   - [ ] Reference the task
   - [ ] Document any concerns in DECISIONS.md

---

## Application

**Task #7 (Batch 1):** ✅ I reviewed all changes before commit
- Read Home.tsx, Directory.tsx, SearchBar.tsx
- Verified intent clarity improvements
- Confirmed no methodology changes

**Task #10 (Codex: Website Discovery):** 
- [ ] PENDING: Will review dedup code before integrating

**Task #11 (Codex: Small Org Research):**
- [ ] PENDING: Will review research brief before incorporating

---

## Going Forward

Every Codex task follows this gate. No exceptions.

**Owner:** Claude Code (reviewer)  
**Approval:** Required before deployment  
**Fallback:** If Codex change unclear, ask for clarification before merging
