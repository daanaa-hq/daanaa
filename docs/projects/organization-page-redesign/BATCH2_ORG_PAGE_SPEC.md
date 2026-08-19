# Batch 2 — Organization Page Decision-Grade Redesign

**Objective:** Make the org page a decision support tool, not a data dump.

## Current State
- Name + mission + location visible upfront ✓
- CTAs (Give, Website) present ✓
- IRS status shown ✓
- Financial signals (reserves, solvency) present ✓
- **Gap:** Provenance is invisible (what's public record vs nonprofit-supplied vs inferred)
- **Gap:** Related orgs/network context not easily discoverable

## Implementation Priorities

### Phase 1: Header Summary Enhancement
- [ ] Highlight key stats above mission (revenue size, peer percentile if available)
- [ ] Add "At a Glance" summary (what Daanaa infers about health)
- [ ] Keep CTA row prominent
- [ ] No new data collection — use existing fields only

### Phase 2: Provenance Layer Separation
- [ ] Label "Public Record" section (IRS data, ProPublica, NCCS)
- [ ] Label "Nonprofit-Supplied" section (claimed profile, if any)
- [ ] Label "Daanaa Inferred" section (peer context, health signals)
- [ ] Each section has visible source attribution
- [ ] No mixing of data sources in visual hierarchy

### Phase 3: Related Orgs + Network Context
- [ ] Show "Similar Organizations" from peer group (if available)
- [ ] Show "In This Cause" related orgs (if cause_tags available)
- [ ] Add "Organizations This Org Partners With" if relationship data exists
- [ ] Position below financial data, before deep dive sections

## Stewardship Guardrails
- No new evaluative judgments (no AI-generated ratings)
- No visibility ranking changes
- No data collection beyond what API already provides
- Source attribution on all data (real sources: IRS, ProPublica, NCCS, user-supplied)
- First-time donor can scan and understand: mission → size → health → next step

## Files to Modify
- `frontend/src/pages/OrganizationDetail.tsx` (main)
- `frontend/src/components/OrgInfoHierarchy.tsx` (if restructuring sections)
- Potentially new: `frontend/src/components/ProvenanceLayers.tsx` (to separate data sources visually)

## Non-blocking Dependencies
- Website discovery verification (Task #10) — can add network visualization later
- Research brief Phase 1 roadmap (Task #11) — doesn't block header redesign

## Definition of Done
- First-time donor flow: mission → size → health status → next steps → related orgs
- All data sources labeled (no mystery data)
- No performance regression (measure Time to First Contentful Paint)
- Build clean, no accessibility regressions
- Tested on mobile (<375px)
