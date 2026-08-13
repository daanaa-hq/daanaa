# 2026-08-13 — Codex Parallel Sprint Status & Handoff

**Date:** 2026-08-13 04:35 CDT  
**Session:** Evening deployment sprint (21:00–present, ongoing)  
**Primary task:** T-2026-08-13-001-codex-parallel-sprint.md  
**Owner:** Codex (executor), Claude Code (coordination), Akbar Khowaja (founder approval)

---

## Executive Summary

Three Codex workstreams are executing in parallel:

1. **✅ Website Discovery (60% complete):** 461,682 orgs now have cataloged websites
2. **⏳ P1 Live Fixes (status unknown, expected merge ~23:00):** Directory performance, color contrast, API contract alignment
3. **⏳ Research Brief (status unknown, expected ~02:30–03:00):** Small org visibility literature + product roadmap

**Issue:** P1 fixes and research brief completion notifications have not yet arrived (4:35am). Website discovery is showing real progress in database.

**Next action:** Contact Codex for status on P1 and research streams; confirm merge readiness on fixes.

---

## Stream 1: P1 Live Fixes — Repository Status Unknown

**What it is:** Codex QC testing found three critical live-site issues. Codex is remediating them.

**Issues being fixed:**

| Issue | Before | Target | File |
|-------|--------|--------|------|
| Directory page slowness | 5923ms | <2000ms | `frontend/src/pages/Directory.tsx` |
| WCAG color contrast violations | 360+ nodes | 0 violations | `frontend/src/styles/` CSS tokens |
| API contract mismatch | API returns `EIN`/`organization_name`, frontend expects lowercase | Use uppercase consistently | `frontend/src/components/` |

**Expected merge:** ~23:00 (Aug 12, ~5.5 hours ago)  
**Actual merge status:** ❌ Not merged yet  
**Verification checklist:** `docs/CODEX_FIXES_VERIFICATION.md` (created and ready)

**Next: Get Codex status on P1 fixes. If merged, run verification checklist against live site.**

---

## Stream 2: Website Discovery — Clear Progress Signal

**What it is:** Codex is crawling 50K nonprofit websites using parallel batch-pipelined agents.

**Status as of 04:35:** PARTIAL COMPLETION CONFIRMED

**Evidence (from database query at 04:35):**
```
Total orgs: 2,056,834
Orgs with website URLs: 461,682 (22.4% coverage)

By revenue band:
- Established (>$700K):       88.8%  (101,368 / 114,135)
- Professional ($150K–$700K): 67.0%  (74,348 / 110,996)
- Micro (<$150K):             47.8%  (70,595 / 147,650)
- Unknown:                    12.8%  (215,371 / 1,684,053)
```

**Major finding:** Phi Theta Kappa — 598 chapters sharing `www.ptk.org`
- Perfect example of parent-child relationship needing dedup
- Proves the concept: chapters ARE discoverable if we look

**What's done:**
- ✅ URL discovery (web crawl completed)
- ✅ URLs loaded into `merit_registry.db`
- ✅ Network patterns detected (Phi Theta Kappa)

**What's pending:**
- ⏳ Website verification (HTTP 200/404/timeout status checks)
- ⏳ Parent-child relationship mapping (chapters tagged with parent)
- ⏳ Deduplication analysis (how many of 461K are unique vs. duplicates)

**Next: When Codex reports, query for `website_status` distribution. Build parent-child relationship table.**

---

## Stream 3: Research Brief — Literature Synthesis on Small Org Visibility

**What it is:** Codex is researching how to better represent and discover smaller nonprofits.

**Input:** Board brainstorm session (SIMULATED_BOARD_SESSION_20260813.md) identified five key insights:

1. **Frame small as focused, not limited** (intentional lean ops, not poverty)
2. **Leverage relationships, not metrics** (founder credibility, peer endorsements, community presence)
3. **Discovery is the real problem** (not trust; small orgs are trustworthy but invisible)
4. **Authenticity beats metrics** (let orgs tell their story, show choices not constraints)
5. **Measurement: give to small orgs increases** (success = more small org funding, not more total funding)

**Research topics assigned to Codex:**
- Academic literature on nonprofit representation + visibility
- Industry benchmarks (GiveWell, Guidestar, ImpactBase, Network for Good)
- Small org discovery best practices
- Measurement frameworks for small org visibility

**Expected deliverables:**
- Evidence-based product recommendations
- Phase 1 roadmap (2-week sprint)
- Measurement framework

**Expected Phase 1 priorities (from board):**
1. Founder story / mission narrative layer
2. Geographic discovery ("nonprofits near me")
3. Cause-based clustering (niche discovery)
4. Simplify 990-reading for small orgs

**Status:** Expected ~02:30–03:00, not yet received (04:35)  
**Next: Get Codex status on research completion.**

---

## Critical Decisions & Autonomy Granted

**Codex has full autonomy on this sprint:**

✅ Download any repos (research, tools, ML)  
✅ Pivot methodology if initial approach fails  
✅ Request hardware scaling  
✅ Parallel agent coordination  
✅ Commit to master (after verification)  

**Constraints:**
- Don't merge without passing verification checklist
- Don't modify STEWARDSHIP.md or PRIVACY-INVARIANTS.md
- Research must cite sources
- No public comms without founder approval

---

## Files & References

**Task record (primary):** `institution/tasks/T-2026-08-13-001-codex-parallel-sprint.md`

**Supporting docs:**
- `docs/CODEX_FIXES_VERIFICATION.md` — Verification checklist for P1 fixes
- `docs/WEBSITE_DISCOVERY_PROGRESS.md` — Database analysis + dedup ratios
- `docs/SIMULATED_BOARD_SESSION_20260813.md` — Board brainstorm input
- `docs/CODEX_BATCH_STRATEGY.md` — Batch pipelining documentation
- `docs/CODEX_AUTONOMY_AUTHORIZATION.md` — Full autonomy grant

**Expected output files:**
- `docs/RESEARCH_BRIEF_SMALL_ORG_VISIBILITY.md` (when Codex reports)
- Codex commits to master for P1 fixes (when ready)

---

## What Founder Needs to Know

1. **Website discovery is real:** 461K URLs in DB, organized by size, chapters detected
2. **P1 fixes should be merged:** Expected merge ~5.5 hours ago; need status
3. **Research brief incoming:** Will inform Phase 1 product roadmap
4. **All three streams required:** For sprint closure, all three must complete
5. **Codex is well-coordinated:** Autonomy working well; parallel execution efficient

---

## Next Checkpoints

| Time | Expected Event | Current Status |
|------|---|---|
| 04:35 (now) | P1 fixes should be merged + verified | ⏳ Unknown — need status |
| 04:35 (now) | Website verification phase completing | ⏳ In progress |
| 04:35 (now) | Research brief should be drafted | ⏳ Overdue — need status |
| 05:00 | Codex status handoff to Claude | ⏳ Awaiting |
| 06:00 | Verification checklist run (if P1 merged) | ⏳ Depends on P1 status |
| 07:00 | Website dedup analysis complete | ⏳ Next phase |
| 08:00 | Research brief reviewed + integrated | ⏳ Next phase |

---

**Handoff prepared by:** Claude Code  
**For review by:** Akbar Khowaja  
**Codex assignment:** Active  
**Status:** Awaiting Codex completion on P1 and research streams
