# T-2026-08-13-001 — Codex Parallel Sprint: P1 Fixes + Website Discovery + Research

| Field | Value |
|---|---|
| Owner | **Codex (primary executor)**, Claude Code (coordination) |
| Scope | Three parallel workstreams: (1) P1 live fixes, (2) Website discovery for 50K nonprofits, (3) Research brief on small org visibility |
| Affected paths | `frontend/`, `scripts/core/`, `data/merit_registry.db`, `docs/` (new research output) |
| Authority constraints | P1 fixes are autonomous; website discovery autonomous; research autonomous |
| Status | 🔄 **IN PROGRESS — Partial completion detected** |
| Start date | 2026-08-12 21:00 CDT |
| Expected completion | 2026-08-13 04:00 CDT |
| Actual status at 04:35 | Tasks running; partial results visible in DB |
| Validation gate | Codex results handoff + Claude verification |
| Branch | master (merged on completion) |

---

## Three-Stream Breakdown

### Stream 1: P1 Live Fixes (Codex QC → Remediation)

**Scope:** Fix three critical issues found during Codex QC testing

| Issue | Before | Target | File(s) |
|-------|--------|--------|---------|
| Directory page slowness | 5923ms load | <2000ms | `frontend/src/pages/Directory.tsx`, `frontend/src/components/` |
| Color contrast violations | 143+114+103 nodes | 0 violations | `frontend/src/styles/` CSS tokens |
| API contract mismatch | `ein`/`name` expected | `EIN`/`organization_name` | `frontend/src/components/OrgCard.tsx`, `frontend/src/pages/OrganizationDetail.tsx` |

**Status as of 04:35:**
- ❌ No completion notification yet (expected ~23:00)
- ⏳ Should have been complete ~5 hours ago
- 🔴 **BLOCKER:** Codex results not yet merged to master

**Deliverables:**
- [ ] Merged code to master with all 3 fixes applied
- [ ] Verification checklist results (CODEX_FIXES_VERIFICATION.md)
- [ ] Live-site smoke tests passing
- [ ] No new console errors introduced

**Commit prefix:** `fix: P1 live fixes (directory performance, color contrast, API contract)`

---

### Stream 2: Website Discovery for 50K Nonprofits (Codex Batch Pipeline)

**Scope:** Crawl and catalog websites for organizations with missing URLs

**Execution model:** 10 parallel agents, batch pipelined, 3-5 batch queue depth, non-blocking writes

**Status as of 04:35:**
- ✅ **PARTIAL COMPLETION CONFIRMED**
- Database query shows: **461,682 orgs with website URLs** (was ~0 before)
- Coverage by size:
  - Established (>$700K): 88.8% (101,368/114,135)
  - Professional ($150K–$700K): 67.0% (74,348/110,996)
  - Micro (<$150K): 47.8% (70,595/147,650)
  - Unknown: 12.8% (215,371/1,684,053)
- ⏳ **VERIFICATION PHASE PENDING:** HTTP status validation likely still running

**Sample discoveries:**
- Phi Theta Kappa: 598 chapters sharing `www.ptk.org` (parent-child dedup example)

**Deliverables (expected):**
- [ ] 461K+ websites verified (HTTP 200/301/302 vs. 404/dead)
- [ ] Parent-child relationship mapping (chapter detection)
- [ ] Deduplication analysis (shared URL frequencies)
- [ ] Small org gap analysis (which 77K are still missing)
- [ ] Codex summary report: methodology, batching efficiency, final coverage

**Next actions (when Codex reports):**
1. Query database for `website_status` distribution (should show 200/404/timeout counts)
2. Build relationship table for parent orgs + chapters
3. Tag 598+ Phi Theta Kappa chapters with parent reference

---

### Stream 3: Research Brief on Small Org Visibility (Codex Literature Review)

**Scope:** Synthesize nonprofit representation literature + board brainstorm into product roadmap

**Input:** Simulated board session notes (see SIMULATED_BOARD_SESSION_20260813.md)

**Research topics:**
- Nonprofit visibility barriers (academic literature)
- Industry benchmarks (GiveWell, Guidestar, ImpactBase, Network for Good)
- Small org best practices (peer visibility, founder stories, community endorsements)
- Measurement frameworks (diversity in giving, small org adoption metrics)

**Status as of 04:35:**
- ❌ No completion notification yet (expected ~02:30–03:00)
- ⏳ **OVERDUE** (~1.5–2 hours past ETA)
- 📝 Research brief should be ready to synthesize into product backlog

**Deliverables (expected):**
- [ ] Literature synthesis (3-5 key papers cited)
- [ ] Industry benchmark comparison (4+ platforms analyzed)
- [ ] Product recommendations (prioritized, evidence-backed)
- [ ] Phase 1 roadmap (2-week sprint) with story estimates
- [ ] Measurement framework (how to validate small org visibility improvements)

**Expected Phase 1 priorities (from board simulation):**
1. Founder story / mission narrative layer
2. Geographic discovery ("nonprofits near me")
3. Cause-based clustering (niche discovery, not global ranking)
4. Simplify 990-reading for small orgs (many on 990-N with no data)

---

## Critical Path & Dependencies

### 21:00–23:00: Codex QC Testing + P1 Fixes Development
- Codex found 3 P1 issues ✅ (completed)
- Codex developing fixes (expected ~23:00)

### 23:00: P1 Fixes Merge
- Codex merges fixed code to master
- Claude verifies against CODEX_FIXES_VERIFICATION.md checklist
- **CURRENT BLOCKER:** No merge notification as of 04:35

### 01:00–02:00: Website Discovery Execution
- 10 parallel agents, batch pipelined
- Pre-load 3-5 batches while agents process
- **CURRENT STATE:** 461K URLs discovered ✅; verification phase pending ⏳

### 02:00–03:00: Research Brief Completion
- Codex synthesizes literature + board feedback into roadmap
- **CURRENT STATE:** Expected output not yet received

### 03:00+: Integration & Deployment
- Merge all fixes to master
- Load website data into relationship tables
- Commit research findings to `docs/RESEARCH_BRIEF_SMALL_ORG_VISIBILITY.md`
- Create Phase 1 roadmap PR

---

## Codex Autonomy Authorization

**Full scope granted to Codex for this sprint:**

✅ Download and use any repository (research repos, scraping tools, ML pipelines)  
✅ Pivot methodology if initial approach fails (outcome-focused briefs, not method-specific)  
✅ Request hardware resource scaling (CPU, GPU, RAM)  
✅ Batch pipelining optimization (no idle agents)  
✅ Parallel agent coordination (Stream 2: website discovery agents)  
✅ Commit to master (after verification passes)  

**Constraints:**
- ❌ Do not merge without verification checklist
- ❌ Do not modify `STEWARDSHIP.md` or `PRIVACY-INVARIANTS.md`
- ❌ No public communications without founder approval
- ❌ Research must cite sources (no unsourced claims)

---

## Verification Checklist (for Claude Code)

### Stream 1: P1 Fixes
- [ ] Read Codex commits
- [ ] Directory page load time <2000ms (DevTools measurement)
- [ ] Color contrast violations = 0 (Axe report)
- [ ] API contract aligned (OrgCard uses `EIN`/`organization_name`)
- [ ] No new console errors introduced
- [ ] Live-site smoke tests passing
- [ ] Merge to master approved

### Stream 2: Website Discovery
- [ ] Query database: `SELECT COUNT(DISTINCT website) FROM registry_enriched` (should be ~370K+ unique)
- [ ] Query verification status: `SELECT website_status, COUNT(*) FROM registry_enriched GROUP BY website_status`
- [ ] Phi Theta Kappa identified (598+ orgs, one domain)
- [ ] Coverage metrics documented (by revenue band)
- [ ] Dedup ratio calculated (shared vs. unique domains)
- [ ] Commit verification results to docs/WEBSITE_DISCOVERY_STATUS.md

### Stream 3: Research Brief
- [ ] Research document created: `docs/RESEARCH_BRIEF_SMALL_ORG_VISIBILITY.md`
- [ ] 3+ academic sources cited
- [ ] 4+ industry benchmarks analyzed
- [ ] Phase 1 roadmap drafted (2-week sprint)
- [ ] Measurement framework defined
- [ ] Board brainstorm insights integrated
- [ ] Commit to master

---

## Files Created/Modified This Sprint

| File | Purpose | Owner | Status |
|---|---|---|---|
| `frontend/src/pages/Directory.tsx` | P1 fix: performance | Codex | 🔄 Pending merge |
| `frontend/src/styles/` | P1 fix: color tokens | Codex | 🔄 Pending merge |
| `frontend/src/components/OrgCard.tsx` | P1 fix: API contract | Codex | 🔄 Pending merge |
| `data/merit_registry.db` | Website URLs, verify status | Codex | ✅ Updated |
| `docs/WEBSITE_DISCOVERY_STATUS.md` | Coverage analysis | Claude Code (post-Codex) | 📝 In progress |
| `docs/RESEARCH_BRIEF_SMALL_ORG_VISIBILITY.md` | Research findings + roadmap | Codex | ⏳ Pending |
| `docs/SIMULATED_BOARD_SESSION_20260813.md` | Board brainstorm notes | Claude Code | ✅ Created |
| Codex commits (P1 fixes) | Implementation | Codex | 🔄 Pending merge |

---

## Known Blockers & Unknowns

| Item | Status | Impact |
|---|---|---|
| P1 fixes merge notification | 🔴 **MISSING** (expected ~23:00, now 04:35) | Can't verify fixes or proceed to integration |
| Website verification phase status | ⏳ **IN PROGRESS** (HTTP checks) | Need to know when validation completes |
| Research brief delivery | ⏳ **OVERDUE** (expected 02:30–03:00) | Delays Phase 1 roadmap planning |
| Phi Theta Kappa dedup logic | ⏳ **PENDING** (need parent tagging) | Foundation for relationship mapping |

---

## Success Criteria (Final Handoff)

✅ **Stream 1 PASS:** P1 fixes deployed to master + verified live  
✅ **Stream 2 PASS:** 461K+ websites cataloged + verified + deduplicated  
✅ **Stream 3 PASS:** Research brief drafted + Phase 1 roadmap prioritized + evidence-backed  

**All three streams required for sprint closure.**

---

## References & Documentation

- **Board session notes:** `docs/SIMULATED_BOARD_SESSION_20260813.md`
- **P1 fixes verification:** `docs/CODEX_FIXES_VERIFICATION.md`
- **Website discovery progress:** `docs/WEBSITE_DISCOVERY_PROGRESS.md` (created 04:35)
- **Batch pipelining strategy:** `docs/CODEX_BATCH_STRATEGY.md`
- **Codex autonomy authorization:** `docs/CODEX_AUTONOMY_AUTHORIZATION.md`

---

## Task Status Summary

**Current time:** 2026-08-13 04:35 CDT  
**Elapsed:** ~7.5 hours (expected 5 hours)  

| Stream | Target | Actual | Status |
|--------|--------|--------|--------|
| P1 Fixes | 23:00 completion | ⏳ OVERDUE | 🔴 No merge yet |
| Website Discovery | 01:00–02:00 completion | ✅ URL phase complete | ⏳ Verification pending |
| Research Brief | 02:30–03:00 completion | ⏳ OVERDUE | 🔄 Expected soon |

**Recommendation:** Contact Codex for status on P1 fixes and research brief. Website discovery showing real progress (461K URLs in DB).

---

**Task owner:** Codex + Claude Code  
**Handoff authority:** Akbar Khowaja (founder)  
**Last updated:** 2026-08-13 04:35 CDT  
**Next checkpoint:** When Codex reports completion on all three streams
