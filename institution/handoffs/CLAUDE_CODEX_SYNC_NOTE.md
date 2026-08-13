# Claude ↔ Codex Sync Note
**Updated:** 2026-08-13 06:10 CDT  
**Source of truth:** `institution/tasks/T-2026-08-13-002-charter-safe-product-roadmap.md` and linked handoff  

---

## Current Status: Batch 1 Substantially Complete ✅

| Item | Status | Evidence | Next |
|------|--------|----------|------|
| **P1 Live Fixes** | ✅ COMMITTED | Commit 0f6838c5cb7 (directory perf, contrast, API contract) | ➜ Ready for droplet deployment |
| **Batch 1 (Discovery UX)** | ✅ SUBSTANTIALLY COMPLETE | Commits 36403d98c88, 3463e7e7932 (Get Started + directory cause simplification) | ➜ Mobile polish, edge cases, then Batch 2 |
| **Website Discovery Data** | ✅ LOADED | 461,682 URLs in DB, coverage verified (88.8%/67%/47.8%/12.8% by size) | ➜ Pending Codex: verification commit + dedup |
| **Behavioral Science Brief** | ✅ DELIVERED | BEHAVIORAL_SCIENCE_OPPORTUNITIES_BRIEF_20260813.md (6 evidence signals) | ➜ Informs Batch 2 opportunities model |

---

## Track A (Execute Now) — Batch 1 Scope: COMPLETE

Delivered **homepage + directory discovery UX clarity**. No approval gates crossed.

**✅ Completed:**
1. **Homepage:** Get Started section with 3 primary paths (search, volunteer, compare)
2. **Directory performance:** SearchBar suggestions disabled in directory scope
3. **Directory cause clarity:** Featured 8 causes shown, remaining 18 behind "Browse all"
4. **Accessibility:** IrsEligibilityContext WCAG AA color tokens applied
5. **API contract:** Frontend field refs aligned to uppercase (EIN, organization_name)

**Next phase (Batch 2):**
- Org page decision-grade redesign (provenance labels, action CTAs)
- Nonprofit clarity layer (claim flow, structured fields)
- Mobile edge case polish
- Performance baselines post-deployment

---

## Track B (Specification Only) — Behind Approval Gates

Do not activate code for:
- Ranking/visibility logic changes
- Public scoring/badges methodology
- Monetization touching exposure
- AI evaluative judgments
- Production migrations/deployments
- Private nonprofit data expansion

---

## Parallel Work (Codex)

**Website discovery:** 461K URLs discovered. Pending:
- Verification commit (HTTP status distribution)
- Dedup analysis (shared domains, parent-child mapping)
- Phi Theta Kappa example (598 chapters, one domain) ready for relationship tagging

**Research brief:** Awaiting literature synthesis + Phase 1 roadmap

---

## Coordination Pattern

1. **Claude:** Work on Track A in parallel (Batch 1, 2, etc.) using repo as source of truth
2. **Codex:** Lead on data-intensive work (discovery, research); Claude implements UX
3. **Sync:** Update repo task/handoff records; use chat only for urgent blockers
4. **Approval:** Founder approves Track B specs before code activation

---

## Repo Files (Always Read These First)

- Task record: `institution/tasks/T-2026-08-13-002-charter-safe-product-roadmap.md`
- Handoff: `institution/handoffs/2026-08-13-charter-safe-product-roadmap.md`
- This sync note: `institution/handoffs/CLAUDE_CODEX_SYNC_NOTE.md` (updated continuously)

---

## Immediate Actions

**Claude:** 
- [ ] Continue Batch 1 (directory filter IA)
- [ ] Verify build on each commit
- [ ] Defer to Codex on product skepticism

**Codex:**
- [ ] Commit website discovery findings
- [ ] Surface research brief when ready
- [ ] Ping if any blocker on data pipeline

**Founder:**
- [ ] Approve Track B specs when needed
- [ ] Sign off on Charter-Safe roadmap phases before production deployment
