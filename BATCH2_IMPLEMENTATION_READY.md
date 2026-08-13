# Batch 2 Implementation Ready — Org Page Provenance Redesign

**Status:** Ready to implement  
**Owner:** Claude (autonomous), can coordinate with Codex on peer review  
**Timeline:** Implement incrementally, test after each phase  

## Phase 1: Add Provenance Labels (Current)

**Goal:** Make data sources explicit without redesigning the entire page.

**Approach:** Wrap existing sections with source attribution labels.

```
[Header: Name, Mission, Location]

[QUICK VERIFICATION - Public Record]
- IRS Status
- Tax Deductibility  
- Data Freshness
- Source Attribution: "IRS Form 990 via ProPublica"

[FINANCIAL CONTEXT - Daanaa Analysis]
- Reserves, Solvency, Peer Percentile
- Source Attribution: "Calculated from IRS 990 filings, benchmarked against peer group"

[NONPROFIT PROFILE - Claimed by Organization]
(if claimed data exists)
- Mission refinement, programs, contact
- Source: "Organization-submitted profile"

[SIMILAR ORGANIZATIONS]
- Related orgs in peer group
```

**Files to modify:**
- `frontend/src/pages/OrganizationDetail.tsx` — wrap sections with source labels
- Optional: Create `frontend/src/components/SourceAttribution.tsx` component for reusable label

**Implementation order:**
1. Add source labels to IRS/verification section
2. Add source labels to financial context
3. Add source labels to similar orgs
4. Test on mobile + desktop
5. Build + commit

**Non-blocking:** Doesn't require new API data, doesn't change existing components deeply.

---

## Phase 2: Header Summary Enhancement (Next)

After Phase 1 merges, enhance header to show org size + peer percentile upfront.

---

## Phase 3: Related Orgs + Network (Future)

Integrate website discovery dedup (Task #10) to show organizational relationships.

---

## Codex Review Request

When Phase 1 is ready: Review for stewardship alignment, accessibility, no hidden data mixing.
