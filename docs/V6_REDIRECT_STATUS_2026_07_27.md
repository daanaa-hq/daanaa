# V6 Redirect: Pausing Phase 1 for Data Foundation (Phase 0A-E)

**Date:** 2026-07-27  
**Status:** Phase 0A Complete, Pivoting to Phases 0B-0E  
**Previous Plan:** Phase 1 API wiring (now blocked)  
**New Plan:** Complete data foundation first (normalized tables, ingestion, new v6 run, validation)

---

## What Changed

**Founder's Realignment Directive (2026-07-27):**

You provided a comprehensive v6 realignment specification that goes significantly deeper than our Phase 0 candidate run. The spec includes:

- 5-tier fallback hierarchy (not our 4-tier system)
- Normalized data tables (org_financial_years, org_classifications, org_operating_context, org_data_assertions)
- Ingestion pipeline with validation + quarantine (before scoring)
- Revenue bands (Grassroots, Small, Mid, Established, Major)
- Minimum peer thresholds (30 preferred, 10 acceptable, 5 minimum, <5 never publish)
- Privacy + fairness validation before production

**Your direction:** "Do not treat the current Phase 0 run as the final canonical v6 methodology."

**Implication:** Our Phase 0 candidate (2a4fcb30) is a good starting point but incomplete. Before wiring the API, we need to:

1. Archive Phase 0 candidate as "legacy" (done)
2. Build normalized data tables (done)
3. Create ingestion pipeline (Phase 0B)
4. Backfill historical data (Phase 0C)
5. Generate new 5-tier v6 run using normalized data (Phase 0D)
6. Validate + get founder approval (Phase 0E)

---

## What's Complete (Phase 0A)

✅ **Historical Version Inventory**
- v4 scoring (537K orgs with merit_score)
- v5 scoring (372K orgs with merit_score_v5)
- v6 candidate run (2.02M assignments, now archived)
- tier_assignments table (2.05M rows, preserved)

✅ **Normalized Table Schema**
- `org_financial_years` — source-traceable financial data (ein + tax_year unique)
- `org_classifications` — NTEE, archetype, funding model (reported vs inferred tracked)
- `org_operating_context` — board size, programs, service areas
- `org_data_assertions` — org-submitted corrections + claimed fields
- `ingestion_audit_log` — batch audit trail per source
- `ingestion_quarantine` — invalid records before scoring

✅ **Design Principles**
- Idempotent ingestion (ein + tax_year + source_name + source_record_id unique)
- Source provenance (every value tagged with source_url, retrieved_at, record_hash)
- Reported vs inferred tracking (confidence + is_inferred flags)
- Quarantine before scoring (invalid data doesn't silently enter v6)
- Reversible (can rollback to prior state)

---

## What's Paused

❌ **Phase 1 API Wiring — BLOCKED until Phase 0E complete**

We were ready to wire v6 to the API, but that's premature. The API should read from normalized, validated data — not from incomplete tables.

---

## What's Next (Phases 0B-0E)

**Phase 0B: Ingestion Workflow (2-3 days)**
- Build adapters for IRS 990, ProPublica, NCCS data sources
- Implement validation (EIN format, tax year, value sanity checks)
- Implement quarantine (invalid records before scoring)
- Output: quarantine report + audit log

**Phase 0C: Backfill Historical Data (2-3 days)**
- Extract financial years (2018-2024) from IRS/ProPublica
- Populate org_financial_years, org_classifications, org_operating_context
- Validate coverage by field, by year, by source
- Output: backfill audit report

**Phase 0D: Generate New 5-Tier v6 Candidate Run (1-2 days)**
- Use 5-tier fallback hierarchy (Tier 1/2/3/4 numeric + Tier 5 archetype-only)
- Enforce minimum peer thresholds (30 preferred, 10 acceptable, 5 minimum)
- Calculate peer metrics (median reserves, confidence, margins)
- Store in v6_peer_context_assignments with new run_id
- Output: 2M+ assignments + v6_scoring_runs record

**Phase 0E: Validation + Founder Review (1-2 days)**
- Validate coverage (% orgs by tier, % with each data element)
- Validate peer thresholds (no Tier 1/2/3 with <5 scoreable peers)
- Validate revocation exclusions (revoked orgs not in peer groups)
- Validate privacy (no PII, no donor data in comparisons)
- Validate fairness (small orgs get Tier 4/5, not false low confidence)
- Output: coverage report + peer threshold report + privacy test results
- **Founder decision:** Approve new v6 run for activation
- **Unlock:** Phase 1 API wiring can begin

---

## Timeline

| Phase | Duration | Status |
|---|---|---|
| Phase 0A: Schema | 1 day | ✅ Complete |
| Phase 0B: Ingestion | 2-3 days | Design |
| Phase 0C: Backfill | 2-3 days | Blocked on 0B |
| Phase 0D: New run | 1-2 days | Blocked on 0C |
| Phase 0E: Validation | 1-2 days | Blocked on 0D |
| **Total Phase 0** | **7-10 days** | In Progress |
| Phase 1: API wiring | 2-3 days | Blocked on Phase 0E |
| Phase 2: Frontend | 2 days | Blocked on Phase 1 |
| Phase 3: Testing | 2 days | Blocked on Phase 2 |
| Phase 4: Approval | 1 day | Blocked on Phase 3 |

**Total to production:** ~15-20 days (vs 10-13 days if we'd rushed Phase 0)

---

## Important Points

**The Phase 0 Candidate Run (2a4fcb30) is archived, not deleted:**
- 2.02M assignments preserved
- Status: `archived_legacy_candidate`
- Will NOT be used for active API/frontend
- Available for rollback reference if needed

**All historical data preserved:**
- v4 scoring (merit_score, merit_tier, merit_band)
- v5 scoring (merit_score_v5, merit_archetype_v5)
- tier_assignments table (all 2.05M rows)
- v6 candidate run (all 2.02M assignments)
- Nothing deleted, nothing overwritten

**Frontend v6 displays remain hidden:**
- Code deployed to daanaa.org is correct
- Feature-flagged as "staging" (not visible to users)
- Will not be activated until Phase 2 complete + Phase 4 approval

**Why this approach:**
- Builds v6 correctly, not quickly
- Ensures data integrity before exposing to API/frontend
- Provides clear rollback path if issues arise
- Keeps all historical versions available for comparison
- Follows founder's specification precisely

---

## Questions for Founder

1. **Ingestion priority:** Should we prioritize IRS 990 + ProPublica first, then add NCCS later? Or all three in parallel?

2. **Backfill window:** 5 years (2018-2024) or wider? (Affects Phase 0C duration)

3. **Peer thresholds:** Confirmed 30 preferred / 10 acceptable / 5 minimum / <5 never? These drive Tier assignments in Phase 0D.

4. **Revenue bands:** Confirmed breakpoints?
   - Grassroots: < $50K
   - Small: $50K - $199K
   - Mid: $200K - $499K
   - Established: $500K - $4.9M
   - Major: $5M+

5. **Compression:** Can Phases 0B-E fit in 1 week (aggressive) or prefer thorough 2-week approach?

6. **Start Phase 0B now?** Ready to begin ingestion adapter design/build immediately.

---

## Deliverables Before Phase 1 API Wiring

✅ Historical scoring version inventory  
✅ Additive database migration (Phase 0A schema)  
✅ Rollback migration  
✅ Normalized table schema  
□ Ingestion and provenance workflow (Phase 0B)  
□ Quarantine report (Phase 0B)  
□ New read-only v6 candidate run (Phase 0D)  
□ Coverage by tier (Phase 0E)  
□ Peer threshold report (Phase 0E)  
□ Revocation exclusion report (Phase 0E)  
□ Privacy and fairness test results (Phase 0E)  
□ Founder review package (Phase 0E)  

**Phase 1 will NOT proceed until all Phase 0 deliverables are complete and founder approves the new v6 run.**

---

## Summary

This redirect pauses our quick path to production in favor of building v6 correctly. Phase 0A foundation is solid. Phases 0B-E will ensure v6 is data-sound, fair, and explainable before it reaches users.

**Status:** Ready to begin Phase 0B ingestion workflow whenever you approve.
