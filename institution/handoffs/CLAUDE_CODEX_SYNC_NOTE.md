# Claude ↔ Codex Sync Note
**Updated:** 2026-08-13 05:00 CDT  
**Source of truth:** `institution/tasks/T-2026-08-13-002-charter-safe-product-roadmap.md` and linked handoff  

---

## Current Status: Batch 1 in Progress

| Item | Status | Evidence | Next |
|------|--------|----------|------|
| **P1 Live Fixes** | ✅ COMMITTED | Commit 0f6838c5cb7 (directory perf, contrast, API contract) | Merge to droplet |
| **Batch 1 (Discovery UX)** | 🔄 IN PROGRESS | Commit 36403d98c88 (Get Started section, intent clarity) | Complete directory filters, then move to Batch 2 |
| **Website Discovery** | ✅ DATA LOADED | 461,682 URLs in DB, coverage verified | Needs: verification commit + dedup analysis |
| **Research Brief** | ⏳ AWAITING | No repo evidence yet | Surface findings when ready |

---

## Track A (Execute Now) — Batch 1 Scope

Working on **homepage + directory discovery UX clarity**. No approval gates.

**In progress:**
- Homepage: Added "Get Started" section showing 5 discovery paths (search, volunteer, compare)
- Directory: Performance optimization via SearchBar suggestions disabled ✓
- Accessibility: IrsEligibilityContext color tokens for WCAG AA ✓

**Next on Batch 1:**
- Directory filter hierarchy simplification (current: 30+ filter combinations, target: 5 primary paths)
- Mobile scanability on <375px
- Verify no charter conflicts

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
