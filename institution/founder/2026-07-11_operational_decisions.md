# Founder Ruling — Operational Decisions — 2026-07-11

**Authority:** Founder, under Stewardship Constitution  
**Classification:** Temporary Decision (specific operational guidance for current session)  
**Status:** In Execution  
**Previous:** Stewardship Board Resolution 2026-07-11  

---

## DECISION 1: CONCIERGE SHIP GATE — APPROVED, SUBJECT TO FINAL CLEAN TEST

**Status:** Ready for deployment sequence

**Requirements before ship:**

1. ✅ Confirm disclosure language is present:
   > "We prepared a draft of your organization's public profile using publicly available information to save your team time. We would like to review it with you, correct anything needed, and only publish enhancements you approve."

2. ⏳ Run test_concierge_confirm.py in clean environment
   - Requirement: All 13 tests pass
   - Focus: governance, authorization, provenance, verification tests
   - No secrets or production credentials in logs
   - Migrations compatible with production
   - Rollback documented

3. ⏳ Post-deployment smoke test:
   - Authentication boundary
   - Verified-organization gate
   - Confirmation flow
   - Provenance record
   - Activity log
   - Disclosure wording
   - Rollback readiness

**Condition:** If any governance or verification test fails, **do not deploy**.

**Expected outcome:** Feature live on droplet with full verification audit trail.

---

## DECISION 2: AI OPERATIONAL MEMORY — BEGIN THIS WEEK, STRUCTURED MIGRATION

**Status:** Structure in place; migration begins today

**Key principle:** Do not directly copy ~/.claude/projects/meritgiving/memory/ into git.

**Why:** Raw store may contain credentials, PII, transient material, vendor artifacts, machine-specific state.

**Approach:** Curated migration into institution/ai-memory/ with 7 structured files:

| File | Content | Source |
|------|---------|--------|
| README.md | Purpose + how successors use it | ✅ Created |
| DECISIONS.md | Significant architectural/operational choices | ⏳ Extract this week |
| STANDING_CONSTRAINTS.md | Recurring institutional rules + gotchas | ⏳ Extract this week |
| INCIDENTS.md | Root causes + prevention rules | ⏳ Extract this week |
| LESSONS_LEARNED.md | Validated patterns + evidence | ⏳ Extract this week |
| OPEN_QUESTIONS.md | Unresolved questions + context | ⏳ Extract this week |
| MEMORY_MANIFEST.md | Summary: count, dates, size, review date | ⏳ Create after extraction |

**Migration requirements (non-negotiable):**

1. Inventory the source store
2. Scan for secrets and personal information
3. Classify each item (decision vs. incident vs. lesson vs. artifact)
4. Extract durable institutional knowledge only
5. Exclude: raw sessions, credentials, caches, embeddings, machine-specific state
6. Record exclusions and why
7. Preserve provenance without exposing sensitive sources
8. Keep repository private
9. Encrypt necessary sensitive backup outside normal repo
10. Test: successor can reconstruct institutional context from curated files

**Security pre-commit scan (automatic):**
```bash
grep -r -E '(AKIA|ghp_|Bearer|api_key|password|secret|token|credential)' institution/ai-memory/ && exit 1
```

**Timeline:**
- 2026-07-11: Structure (done) + planning (done)
- 2026-07-12: INCIDENTS.md + STANDING_CONSTRAINTS.md
- 2026-07-13: DECISIONS.md + LESSONS.md
- 2026-07-14: OPEN_QUESTIONS.md + MEMORY_MANIFEST.md
- 2026-07-15: Security scan
- 2026-07-16: Git commit + close migration

**Expected outcome:** Institutional knowledge is portable, durable, and secure. Successor can inherit without exposure to credentials or transient data.

---

## DECISION 3: BACKUP ROBUSTNESS — AUTHORIZED, HIGH PRIORITY

**Status:** ✅ COMPLETE

**What was broken:** daanaa_backup.sh silently skipped offsite push if rclone was missing. Operators would see "backup ok" even when critical step failed.

**What was fixed:**

✅ daanaa_backup.sh rewritten with:
- `set -Eeuo pipefail` (strict bash)
- ERR trap catches all failures
- Explicit rclone installation check (fails if missing)
- Explicit remote configuration check (fails if not configured)
- Connectivity test before offsite push (rclone about)
- Verification that files exist on remote after push
- Timestamped error log ($OUT/.backup_errors)
- Nonzero exit code on any failure
- Loud failure messages (never silent)

✅ Test suite (test_backup_robustness.sh):
- 12 checks covering all failure modes
- All 12 tests pass
- Validates: strict bash, error handling, connectivity test, offsite verification

**Before production adoption:**

Completed:
- ✅ Syntax validation
- ✅ Test suite

Still needed:
- [ ] Run successful backup cycle in production
- [ ] Simulate missing rclone (confirm failure)
- [ ] Simulate invalid credentials (confirm failure)
- [ ] Simulate unavailable remote storage (confirm failure)
- [ ] Confirm each failure returns nonzero exit code
- [ ] Perform sample restore from backup

**Key principle:** A backup that fails silently is not a backup system.

**Expected outcome:** Backup system is robust and failures cannot be missed.

---

## DECISION 4: GITHUB ORGANIZATION RESILIENCE — APPROVED, COMPLETE THIS WEEK

**Status:** Queued (after backup + concierge)

**What:** Add a second trusted organization owner to reduce single-founder-account risk.

**Safeguards:**

1. Individually named account (never shared login)
2. Strong MFA (preferably hardware security key)
3. At least two registered security keys
4. Recovery codes stored securely and separately
5. Minimal authority required (recovery + continuity only)
6. Documented: who has owner authority and why
7. Periodic access review
8. Branch protections + required review on production repos
9. No single administrator bypass without audit trail
10. Documented removal/transfer procedures for succession

**Also verify:**

- Billing ownership
- Domain and email recovery access
- Repository backup/mirror strategy
- Deploy-key ownership
- GitHub App and automation permissions
- Emergency recovery instructions in SUCCESSION.md

**Expected outcome:** Organization continuity is protected; if founder account is compromised or unavailable, operations continue.

---

## EXECUTION SEQUENCE

**1. Backup robustness (TODAY)** ✅
   - Commit: d86d422
   - Test suite: all pass
   - Status: Ready for production validation

**2. Add GitHub admin (THIS WEEK)**
   - Select trusted individual
   - Configure MFA + security keys
   - Document in SUCCESSION.md
   - Test recovery procedure

**3. Run clean concierge test (THIS WEEK)**
   - Run test_concierge_confirm.py in isolated DB
   - All 13 tests must pass
   - Deploy via safe_deploy if green

**4. Begin AI memory curation (THIS WEEK)**
   - Extract incident root causes
   - Extract standing constraints
   - Security scan before commit

**5. Update all documentation (BY 2026-07-18)**
   - SUCCESSION.md: GitHub admin access, recovery procedures
   - SUCCESSION.md: AI memory location and access
   - institution/ai-memory/MEMORY_MANIFEST.md: completion date
   - DECISIONS.md: log that these operational decisions were executed

---

## GOVERNANCE PRINCIPLE

**From the ruling:**

> Routine tasks should execute efficiently. Actions involving public trust, institutional memory, production data, governance authority, or irreversible consequences should remain deliberate, reviewable, and recoverable.

These decisions aim to:
- Reduce operational fragility (backup robustness)
- Protect institutional continuity (GitHub resilience)
- Secure institutional knowledge (memory curation, concierge governance)
- Maintain public trust (disclosure, verification gates)

---

## Sign-Off and Evidence

**Executed by:** AI institutional steward (Claude Code)  
**Authorized by:** Founder  
**Date authorized:** 2026-07-11  
**Date implemented:** 2026-07-11 (backup + structure); ongoing (concierge, memory, GitHub)  

**Evidence:**
- Commit d86d422: backup robustness + test suite + memory structure
- Commit 22eedf: concierge disclosure standard
- SUCCESSION.md: updated with Memory Substrate (commit 22eedf)
- institution/ai-memory/README.md, migration/*.md: curation planning docs

**Next review:** Upon completion of items 2–4, document results in this file.

---

**The work continues. These decisions reduce single points of failure and strengthen the institution for succession.**
