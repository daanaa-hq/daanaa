# V6 Realignment: Phase 0A-E (Data Foundation)

**Status:** Phase 0A Complete, Phases 0B-0E In Design  
**Target:** Complete Phase 0 (all 5 phases) before Phase 1 API wiring  
**Timeline Estimate:** 7-10 days

---

## Overview

This document describes the data foundation phases (0A-0E) required before v6 can be wired into the API and frontend. The purpose is to build v6 correctly — with proper source tracking, validation, and a clean 5-tier fallback hierarchy — rather than rushing the current candidate run into production.

The existing Phase 0 candidate run (2a4fcb30) has been archived as `v6_canonical_0_legacy_candidate` and will NOT be used for active API/frontend. It remains available for reference and rollback if needed.

---

## The 5-Phase Data Foundation (0A-0E)

### Phase 0A: Normalized Tables & Methodology Freeze ✅ COMPLETE

**What's Done:**
- ✅ Created `org_financial_years` — source-traceable financial data
- ✅ Created `org_classifications` — NTEE, archetype, funding model (reported vs inferred)
- ✅ Created `org_operating_context` — board, programs, service areas
- ✅ Created `org_data_assertions` — org-submitted corrections & claimed fields
- ✅ Extended `v6_peer_context_assignments` with geography, revenue_band, ntee_level
- ✅ Created `ingestion_audit_log` and `ingestion_quarantine` tables
- ✅ Froze v6 methodology (5-tier system per founder spec)

**Key Features:**
- **Idempotent:** `ein + tax_year + source_name + source_record_id` is unique key
- **Traceable:** Every value retains source, source_url, source_record_id
- **Audited:** created_at, updated_at, retrieved_at, record_hash tracked
- **Quarantined:** Invalid data captured before scoring (never silently enters)
- **Reversible:** Can rollback to prior state

**Next:** Phase 0B ingestion workflow

---

### Phase 0B: Ingestion, Provenance, Validation, Quarantine (DESIGN)

**Goal:** Build adapters to populate normalized tables from authoritative sources

**Data Sources:**
1. **IRS 990 Data** (primary)
   - Source: IRS SOI extract or ProPublica 990 database
   - Extract: total_revenue, expenses, assets, liabilities, net_assets, employees
   - Validation: year is valid, values pass sanity checks, totals reconcile

2. **NCCS Data** (secondary)
   - Source: NCCS SOI dataset (Part X, Part VII)
   - Extract: financial metrics, supplementary data
   - Validation: EIN format, year range, data consistency

3. **ProPublica 990 Metadata**
   - Source: ProPublica JSON API
   - Extract: organization name, address, NTEE, Form type, filing date
   - Validation: EIN, dates, geography

4. **Classification Data**
   - NTEECC from IRS/ProPublica
   - Funding archetype (to be inferred from revenue composition)
   - Service area (to be extracted from 990 narratives)

**Ingestion Requirements (per founder spec):**
- ✅ Idempotent (safe to rerun without duplicates)
- ✅ Source-traceable (every value tagged with source + URL + date)
- ✅ Versioned (track which import version produced this data)
- ✅ Reversible (can rollback to prior version)
- ✅ Validate on entry (EIN format, tax year, negative values, totals, geography)
- ✅ Quarantine invalid records (don't silently skip)

**Validation Checklist:**
- [ ] EIN format (9 digits)
- [ ] Tax year valid (1990-2024)
- [ ] No negative revenue (unless source confirms)
- [ ] Revenue component totals match total_revenue
- [ ] Expense component totals match total_expenses
- [ ] Net assets = total assets - total liabilities (with tolerance)
- [ ] State/territory code valid
- [ ] NTEE format (6 chars if NTEECC, 2 chars if NTEE1)
- [ ] No duplicate source records (by source_name + source_record_id)
- [ ] Revoked status checked

**Output:**
- [ ] Ingestion adapters for each source (IRS, NCCS, ProPublica)
- [ ] Quarantine report (invalid records + reasons)
- [ ] Audit log (batch_id, record counts, errors per source)
- [ ] Test coverage for validation rules

**Estimated:** 2-3 days

---

### Phase 0C: Backfill Historical Data (DESIGN)

**Goal:** Populate normalized tables with historical data (2018-2024)

**Process:**
1. Extract financial years for all active nonprofits (2018-2024)
2. Map to org_financial_years table
3. Extract classifications (NTEE, archetype from revenue composition)
4. Map to org_classifications table
5. Extract operating context (board size, program count from 990)
6. Map to org_operating_context table

**Data Coverage:**
- [ ] IRS SOI data (most recent 5 years)
- [ ] ProPublica 990 extracts (tax years in their database)
- [ ] NCCS Part X/VII data (5-year window)

**Validation:**
- [ ] No duplicate records per source
- [ ] All required fields present
- [ ] All records pass Phase 0B validation

**Output:**
- [ ] org_financial_years populated (est. 5M+ rows across years)
- [ ] org_classifications populated (est. 2M+ rows)
- [ ] org_operating_context populated (est. 1M+ rows)
- [ ] Backfill audit report (coverage by field, by year, by source)

**Estimated:** 2-3 days

---

### Phase 0D: Generate New 5-Tier v6 Candidate Run (DESIGN)

**Goal:** Generate new v6 assignments using normalized data + 5-tier fallback hierarchy

**Methodology (5-Tier Hierarchy):**

**Tier 1: Direct Verified**
- Criteria: NTEECC + Census region + archetype + verified revenue band
- Requirements:
  - NTEECC must be present (not blank)
  - Revenue must be non-null AND pass sanity checks
  - Revenue band assigned (Grassroots, Small, Mid, Established, Major)
  - Must have at least 5 scoreable peers
- If <5 scoreable peers → fallback to Tier 2

**Tier 2: Regional Context**
- Criteria: NTEECC + Census region + archetype (revenue may be missing)
- Requirements:
  - NTEECC must be present
  - Peer group = same NTEECC + region + archetype
  - Show conditional revenue-band context (if revenue available)
  - Minimum 5 scoreable peers preferred; if <5 → fallback to Tier 3
- Fallback: If no revenue data, show conditional tables by band

**Tier 3: Broader Peer Context**
- Criteria: Broader NTEE category + region + archetype
- Requirements:
  - NTEE category (first 2 chars of NTEECC)
  - Same Census region + archetype
  - Larger peer group (may have better data)
  - Minimum 5 scoreable peers required
  - If <5 → fallback to Tier 4

**Tier 4: National Archetype**
- Criteria: NTEECC + national (no region) + archetype
- Requirements:
  - NTEECC present (or use NTEE category if blank)
  - National peer group (all regions)
  - Archetype grouping only
  - May have <5 scoreable peers (acceptable at this level)
  - If no NTEECC → fallback to Tier 5

**Tier 5: Archetype Only**
- Criteria: Funding archetype only (no numeric comparison)
- Purpose: Descriptive context, not numeric comparison
- Use case: Orgs with blank NTEECC or no usable peer data
- Requirement: Never publish numeric comparison (median, range)
- Show: "Organizations with similar funding model typically..."

**Minimum Peer Thresholds:**
- Preferred: ≥30 scoreable peers
- Acceptable: ≥10 scoreable peers (clearly marked limited)
- Never publish numeric comparison: <5 scoreable peers
- Always use scoreable peer count (not total peer count)

**Scoring Process:**
1. For each org in active population:
   - Check if Tier 1 criteria met → assign Tier 1
   - Else check if Tier 2 criteria met → assign Tier 2
   - Else check if Tier 3 criteria met → assign Tier 3
   - Else check if Tier 4 criteria met → assign Tier 4
   - Else assign Tier 5 (archetype only, no numeric data)

2. Calculate peer metrics for each assignment:
   - peer_count (total orgs in group)
   - scoreable_peer_count (orgs with financial data)
   - median_reserves, p25_reserves, p75_reserves
   - source_year_min, source_year_max
   - confidence (based on peer size + data freshness)
   - confidence_margin (±5%, ±7%, ±10%, ±15%)

3. Store in v6_peer_context_assignments with run_id

4. Record metadata in v6_scoring_runs:
   - run_id, methodology_version, git_commit
   - input_snapshot (date normalized tables were refreshed)
   - criteria_json (exact v6 rules)
   - row_counts (by tier)
   - status: "candidate" (not yet active)

**Key Behaviors (per founder spec):**
- [ ] Exclude revoked organizations from peer groups
- [ ] Use Census region for states (national fallback for DC, territories, military)
- [ ] Never invent revenue band
- [ ] Never use total peer count as substitute for scoreable peer count
- [ ] Never publish numeric comparison with <5 scoreable peers
- [ ] Show whether each classification is reported or inferred
- [ ] Show source years, confidence, limitations

**Output:**
- [ ] New v6 candidate run (est. 2M+ assignments)
- [ ] v6_scoring_runs record with full metadata
- [ ] Tier distribution report
- [ ] Coverage by field (% of orgs with each data element)

**Estimated:** 1-2 days

---

### Phase 0E: Validation & Founder Review (DESIGN)

**Goal:** Ensure new v6 run meets quality standards before production activation

**Validation Checklist:**

**Coverage Validation:**
- [ ] Org count by tier (target distribution documented)
- [ ] % orgs with direct revenue (Tier 1 eligible)
- [ ] % orgs with NTEECC (for Tier 1/2/4)
- [ ] % orgs with scoreable peer count ≥5, ≥10, ≥30
- [ ] Field-by-field data availability (mission, revenue, board, etc.)

**Peer Threshold Validation:**
- [ ] No Tier 1/2/3 assignments with <5 scoreable peers
- [ ] Tier 4 allowed to have <5 (but documented)
- [ ] Tier 5 has no numeric comparison

**Revocation Validation:**
- [ ] All revoked orgs excluded from peer groups
- [ ] Revoked orgs shown as "inactive" in discovery (not hidden)

**Fallback Behavior Validation:**
- [ ] All blank NTEECC orgs assigned Tier 4 or Tier 5 (not Tier 2)
- [ ] All no-revenue orgs shown with conditional band context (Tier 2+)
- [ ] No invented revenue bands

**Privacy Validation:**
- [ ] No private claims exposed
- [ ] No donor/wallet data in peer calculations
- [ ] No PII in peer descriptions
- [ ] Organization-submitted data marked as such

**Fairness Review:**
- [ ] Small orgs with limited data get Tier 4/5 (not false lower confidence)
- [ ] No negative language ("insufficient," "failed," "struggling")
- [ ] Use supportive language ("building clearer picture," "limited info")

**API Contract Validation:**
- [ ] financial-context endpoint returns correct schema
- [ ] v6 fields present and consistent
- [ ] Backward compatibility maintained (old fields present but marked deprecated)

**Output:**
- [ ] Coverage report (by tier, by field, by region)
- [ ] Peer threshold report (validation pass/fail)
- [ ] Revocation exclusion report (number excluded by tier)
- [ ] Privacy test results (sensitive data not exposed)
- [ ] Fairness review findings
- [ ] Founder review package (all above + new v6 candidate run available for inspection)

**Founder Review:**
- [ ] Review coverage by tier (is distribution reasonable?)
- [ ] Review peer thresholds (are minimums appropriate?)
- [ ] Review sample orgs at each tier (does assignment logic make sense?)
- [ ] Review API response format (is it clear and complete?)
- [ ] Approve "candidate" run for activation to "active" status
- [ ] Approve Phase 1 API wiring to begin

**Estimated:** 1-2 days

---

## Timeline & Sequence

| Phase | Duration | Blocker | Status |
|---|---|---|---|
| 0A: Normalized tables | 1 day | None | ✅ COMPLETE |
| 0B: Ingestion adapters | 2-3 days | 0A done | Design |
| 0C: Backfill data | 2-3 days | 0B done | Design |
| 0D: Generate candidate run | 1-2 days | 0C done | Design |
| 0E: Validation + review | 1-2 days | 0D done | Design |
| **Total Phase 0** | **7-10 days** | — | In Progress |
| **Phase 1: API wiring** | 2-3 days | Phase 0E done | Blocked |
| **Phase 2: Frontend** | 2 days | Phase 1 done | Blocked |
| **Phase 3: Testing** | 2 days | Phase 2 done | Blocked |
| **Phase 4: Approval** | 1 day | Phase 3 done | Blocked |

---

## Deliverables Before Phase 1 API Wiring

**Required from Phase 0:**
1. ✅ Historical scoring version inventory
2. ✅ Additive database migration (Phase 0A)
3. ✅ Rollback migration
4. ✅ Normalized table schema
5. Ingestion and provenance workflow (Phase 0B)
6. Quarantine report (Phase 0B)
7. New read-only v6 candidate run (Phase 0D)
8. Coverage by tier (Phase 0E)
9. Peer threshold report (Phase 0E)
10. Revocation exclusion report (Phase 0E)
11. Privacy and fairness test results (Phase 0E)
12. Founder review package (Phase 0E)

**API wiring will NOT proceed until all Phase 0 deliverables complete and founder approves.**

---

## Important Notes

- **Phase 0 candidate run (2a4fcb30) is archived** — not for public use
- **v6 frontend displays remain hidden** until Phase 2 complete
- **All old v3/v4/v5 data preserved** — not deleted, just marked historical
- **Backward compatibility maintained** — old API fields still returned (marked deprecated)
- **Rollback path clear** — can revert to any historical version if issues arise

---

## Next Steps

1. ✅ Phase 0A: Schema created
2. **Next: Design Phase 0B ingestion adapters** (IRS, ProPublica, NCCS sources)
3. Then: Build & test Phase 0B
4. Then: Phase 0C backfill
5. Then: Phase 0D new v6 run
6. Then: Phase 0E validation
7. Then: Founder review + approval
8. Then: Phase 1 API wiring (only after approval)

**Status:** Ready for Phase 0B design and implementation.

---

## Questions for Founder

1. **Ingestion sources**: Should we prioritize IRS 990 + ProPublica first, then add NCCS later?
2. **Backfill window**: 5 years (2018-2024) or wider?
3. **Peer thresholds**: Confirmed 30 preferred / 10 acceptable / 5 minimum / <5 never?
4. **Revenue bands**: Confirmed breakpoints (Grassroots <$50K, Small $50K-$199K, Mid $200K-$499K, Established $500K-$4.9M, Major $5M+)?
5. **Timeline**: Can Phases 0B-E be compressed into 1 week, or prefer thorough 2-week approach?
