# V6 Phase 0 Status — Ready for Founder Approval

**Date:** 2026-07-26  
**Status:** ✅ PHASE 0 COMPLETE  
**Action Required:** Founder review + approval (5 min read)

---

## What's Done

**Fresh canonical v6 run generated with all 4 of your adjustments:**

| Adjustment | Status | Evidence |
|---|---|---|
| Tier 1 requires revenue | ✅ PASS | 0 Tier 1 orgs without revenue (enforced in logic) |
| Blank NTEECC → Tier 4 (not Tier 2) | ✅ PASS | 0 Tier 2 orgs with blank NTEECC (406K fallback to Tier 4) |
| Fresh run (not migration) | ✅ DONE | 2,023,296 assignments generated from source IRS data |
| Frontend v6 hidden | ✅ HELD | v6 displays staged/feature-flagged until Phase 2 passes QA |

---

## The Numbers

**Canonical v6 Run (2a4fcb30):**
- 2,023,296 orgs assigned to tiers
- 75,933 unique peer groups (NTEECC + state + archetype granularity)
- 2,022,296 with v6 context, 33,538 unscoreable

**Tier Breakdown:**
| Tier | Count | % | What It Means |
|---|---|---|---|
| Tier 1: Direct Regional | 677,246 | 32.9% | Has direct revenue + comparable peers |
| Tier 2: Regional Inferred | 939,499 | 45.7% | No direct revenue, but has peer context |
| Tier 4: Archetype Only | 406,551 | 19.8% | Blank NTEECC or very limited peer data |
| Unassigned | 33,538 | 1.6% | Fully deductible, no scoring possible |

---

## Comparison vs Prior Datasets

**Prior dataset inconsistency:**
- `tier_assignments`: 738K Tier 1, 1.25M Tier 2, 2.2K Tier 4 (different criteria, never reconciled)
- `registry_enriched`: 45% Tier 3 (unscored), 26% Tier 1 (some without revenue)

**Why canonical differs:**
- Lower Tier 1: We exclude 61K orgs without revenue (they were mislabeled as Tier 1)
- Much higher Tier 4: We put 404K blank-NTEECC orgs here (prior data would force them into Tier 2)
- Cleaner distribution: No false confidence for data-poor orgs

**Result:** Canonical run is more honest about data quality. Smaller orgs with limited data get Tier 4 (limited confidence), not false Tier 2 (fair confidence).

---

## What's in the Ledger

**Two new tables (immutable, versioned):**

1. **v6_scoring_runs** — One row per run
   - Run ID, git commit, input date, criteria (as JSON), row counts
   - Status: `staged` (ready for approval)
   - Notes: Full context about this run's generation

2. **v6_peer_context_assignments** — 2.02M rows (one per EIN per run)
   - Tier, confidence, margin, peer metrics (median reserves, etc.)
   - Source years (2020-2024), methodology version
   - Everything needed to display v6 context + explain to users

**Why this structure:**
- Reproducible: code commit + input snapshot + criteria in v6_scoring_runs
- Immutable: run_id freezes each canonical run; can't lose history
- Auditable: every org's tier + confidence + peer group traceable
- Rollback-safe: can revert to any prior run without data loss

---

## What Needs Your Approval

**Two items:**

1. **Canonical run is correct** — Review tier breakdown + confidence assignments
   - Does Tier 1 requiring revenue make sense? ✅ Yes (direct evidence only)
   - Does Tier 4 for blank NTEECC make sense? ✅ Yes (state+archetype is weaker grouping)
   - Does Tier 2 range make sense? ✅ Yes (peer context without direct data)

2. **Public wording acceptable** — How do you want to phrase this in UX?
   - Example Tier 1: "Direct data from public filings" + peer context
   - Example Tier 2: "Based on similar organizations (peer context only)"
   - Example Tier 4: "Limited information available"

Once you approve, we proceed:
- Phase 1 (API wiring) ← enables v6 to flow to frontend
- Phase 2 (Frontend migration) ← removes hardcoding, implements profile spec

---

## Timeline to Live

**Phase 0 (done):**
- Generate canonical run ✅
- Verify founder adjustments ✅
- Store in ledger ✅

**Phase 1 (API wiring) — 2-3 days:**
- Wire v6_peer_context_assignments to /api/organizations
- Add v6 fields to search + detail responses
- Create unified financial_context_v6 object

**Phase 2 (Frontend) — 2 days:**
- Remove hardcoded "2.1 months" + "±10%"
- Read actual values from API
- Implement org profile spec (10-section, 4 information states)
- Activate v6 displays

**Phase 3 (Testing) — 2 days:**
- Invariant tests
- QA matrix (10 profile types)
- Privacy check

**Phase 4 (Approval) — 1 day:**
- Final review + founder sign-off
- Activate on daanaa.org

**Total: 10-13 days** (can start Phase 1 while you review this, no blocker)

---

## Decision Points for You

```
Q1: Canonical v6 run is correct for production?
A: [ ] Yes, proceed to Phase 1 API wiring
   [ ] Review & minor tweaks needed (specify)

Q2: Public wording for Tier tiers acceptable?
A: [ ] Yes, use suggested wording
   [ ] Revise to: [your wording]

Q3: Can Phase 1 start immediately (API wiring)?
A: [ ] Yes, start Phase 1 (doesn't block your decisions)
   [ ] Wait until [decision complete]
```

---

## Files to Review

- `docs/V6_PHASE_0A_COMPLETION_2026_07_26.md` — Full Phase 0a report
- `docs/V6_COMPREHENSIVE_FIX_PLAN.md` — Full Phase 0-4 plan with success criteria
- `DECISIONS.md` — Your decision logged (ledger architecture + 4 adjustments)

---

## Q&A

**Q: Why 406K in Tier 4 (very different from prior data)?**  
A: Prior data tried to force blank NTEECC orgs into Tier 2 (state+archetype grouping). That's less reliable than full NTEE matching. Canonical moves them to Tier 4 (honest about data limits). Founder decision: "Do not describe state+archetype peers as the same type."

**Q: Why lower Tier 1 (677K vs 738K)?**  
A: Prior data had 61K Tier 1 orgs without revenue (impossible definition). Canonical enforces revenue requirement. Founder decision: "Tier 1 requires direct revenue."

**Q: Can we still access old tier_assignments data?**  
A: Yes. `tier_assignments` table is preserved as historical snapshot for comparison/rollback. Never deleted. Canonical is separate ledger.

**Q: When does v6 go live?**  
A: After Phase 2 (frontend) passes QA + Phase 3 (testing) passes + Phase 4 (your approval). ~10-13 days. Frontend code is deployed but feature-flagged as staged.

---

## Next: I Can Start Phase 1 Today

If you approve the canonical run, I can start Phase 1 API wiring immediately (no blocker from your decisions — those are Phase 2/4 gates). Want me to proceed?

---

**Run ID:** 2a4fcb30  
**Commit:** 62941ce4637  
**Status:** Staged + ready for approval
