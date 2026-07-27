# V6 Backend Fix Plan

**Status:** Planning (post-audit)  
**Target:** Resolve all data consistency issues before daanaa.org reroll  
**Audit reference:** `docs/V6_SCORING_DATA_AUDIT_2026_07_26.md`

## Phase 1: Data Definition & Canonicalization

### 1a. Establish Canonical V6 Definition
- **What:** Document exact v6 criteria (published in METHODOLOGY.md or similar)
- **Specifics needed:**
  - NTEE granularity: Use NTEECC or NTEE2? (audit found NTEECC + state + archetype in DB)
  - Blank NTEECC handling: Fallback to NTEE1? To state + archetype only?
  - Revenue rules: Tier 1 = must have revenue; Tier 2+ = can be null (audit found 13,991 Tier 1 nulls)
  - Minimum peer counts per tier (currently 5, 5, 5 but unclear if enforced)
  - Census region logic (mentioned in docs but not in current data)

### 1b. Choose Canonical Output Table
**Current state:** `tier_assignments` and `registry_enriched` both have v6 columns but disagree on:
  - 8,672 tier values
  - 397,742 inference flags
  - 390,524 peer sizes
  - 423,944 confidence values
  - 1,222,255 margin values

**Decision needed:** Which is authoritative? Options:
- Option A: Keep registry_enriched (7.8B bytes), archive tier_assignments as snapshot
- Option B: Keep tier_assignments, backfill registry_enriched from it
- Option C: Rebuild both from canonical definition

### 1c. Fix Known Data Quality Issues
- **13,991 Tier 1 nulls:** Either fix to have revenue or relabel as Tier 2 inferred
- **405,987 blank NTEECC in Tier 2:** Apply consistent fallback rule (collapse to state + archetype?)
- **Peer group descriptions:** Currently just "N similar orgs in STATE". Add NTEE category + archetype.

---

## Phase 2: Scoring Run Record & Reproducibility

### 2a. Add v6 Scoring Run Entry
Create `scoring_runs` record with:
- run_id (UUID)
- version: "v6_0" or similar
- input_snapshot_date: when data was current
- code_ref: git commit hash
- source_years: [2020, 2021, 2022, 2023, 2024] or actual
- criteria: canonical definition (as JSON or reference)
- row_counts: by tier (Tier 1: 738130, etc.)
- timestamp: completion time
- notes: any manual adjustments or known limitations

### 2b. Update Methodology
- Publish exact v6 definition used (NTEE granularity, fallbacks, thresholds)
- Note publication date vs data date
- Link to scoring_runs record for reproducibility

---

## Phase 3: API Wiring Fixes

### 3a. Search API (`/api/organizations`) 
**Current:** Selects v5 fields only (lines 2318-2330 in droplet_api.py)
**Fix:** Add v6 fields to response:
```python
r.scoring_tier_v6_inference,
r.is_inferred_v6,
r.peer_group_size_v6,
r.confidence_v6,
r.confidence_margin_v6,
r.peer_group_description_v6,
```

### 3b. Detail API (`/api/organizations/<ein>`)
**Current:** Uses `r.*` so includes v6 fields
**Fix:** Verify it includes the fields listed in 3a, ensure response schema is documented

### 3c. Unified Response Schema
Create one `financial_context_v6` object returned by both endpoints:
```json
{
  "tier": "1_Direct_Regional",
  "is_inferred": false,
  "confidence": "good",
  "confidence_margin": "±10%",
  "peer_group": {
    "description": "Education nonprofits in MA",
    "size": 127,
    "median_reserve_months": 12.3,
    "p25_reserve_months": 4.1,
    "p75_reserve_months": 28.5,
    "source_years": [2020, 2021, 2022, 2023],
    "metric_availability": "complete"
  },
  "organization_data": {
    "revenue": 1250000,
    "revenue_year": 2024,
    "months_of_reserve": 18.2
  }
}
```

---

## Phase 4: Frontend Updates

### 4a. Remove Hardcoded Values
**Current (FinancialContext.tsx lines 65-74):**
```javascript
<span className="font-semibold text-lg">2.1 mo</span>  // HARDCODED
<span className="font-body text-label text-cool-grey">±10%</span>  // HARDCODED
```

**Fix:** Read from `financial_context_v6.peer_group`:
```javascript
<span className="font-semibold text-lg">
  {org.financial_context_v6?.peer_group?.median_reserve_months?.toFixed(1)} mo
</span>
<span className="font-body text-label text-cool-grey">
  {org.financial_context_v6?.confidence_margin}
</span>
```

### 4b. Display Actual Peer Group
**Current:** Hardcoded "Good Confidence"  
**Fix:** Show actual peer group description:
```javascript
Among {org.financial_context_v6?.peer_group?.size} {org.financial_context_v6?.peer_group?.description}
```

### 4c. Update FinancialContext Component
- Read from `financial_context_v6` object
- Display organization's actual reserve if Tier 1
- Show peer-derived context for Tier 2+
- Include data-year range and metric availability

---

## Phase 5: Validation & Testing

### 5a. Invariant Tests
Add to `tests/` (new file or extend existing):
```python
def test_v6_tier1_has_revenue():
    """Tier 1 Direct requires non-null total_revenue"""
    tier1 = query("SELECT * FROM registry_enriched WHERE scoring_tier='1_Direct_Regional'")
    assert all(org['total_revenue'] is not None for org in tier1)

def test_v6_blank_nteecc_consistent():
    """Blank NTEECC follows explicit fallback rule"""
    blanks = query("SELECT * FROM registry_enriched WHERE NTEECC IS NULL AND scoring_tier='2_Regional_Inferred'")
    assert all(org['peer_group_description_v6'].startswith('Orgs in ') for org in blanks)

def test_v6_peer_counts_match():
    """Database peer counts match actual peer group sizes"""
    # Spot-check 10 random Tier 2 orgs
    # Count actual peers in their group
    # Assert count matches stored peer_group_size_v6

def test_v6_margins_consistent():
    """Confidence margins map correctly to peer counts"""
    margin_map = {(5, 10): "±15%", (11, 25): "±10%", (26, 50): "±7%"}
    for (min_p, max_p), expected_margin in margin_map.items():
        rows = query(f"SELECT * FROM registry_enriched WHERE peer_group_size_v6 BETWEEN {min_p} AND {max_p}")
        assert all(org['confidence_margin_v6'] == expected_margin for org in rows)

def test_v6_run_reproducibility():
    """Re-running v6 scorer produces identical tier assignments"""
    # Run scorer with canonical definition
    # Compare to current registry_enriched
    # Assert 100% match on tier, is_inferred, peer_group_size_v6
```

### 5b. Manual Spot Checks
- Pick 5 Tier 1 orgs, verify they have revenue + correct peer group
- Pick 5 Tier 2 orgs, verify peer group description is meaningful
- Check 2-3 orgs with blank NTEECC, verify fallback is applied correctly
- Compare displayed margin on frontend to database value

---

## Phase 6: Reroll to Production

Once all phases pass:
1. Commit v6 scoring_run record
2. Update METHODOLOGY.md with canonical definition
3. Merge backend fixes
4. Reroll frontend deployment to daanaa.org
5. Run smoke tests + spot checks
6. Monitor for data consistency issues

---

## Estimated Effort

| Phase | Owner | Duration | Blocker |
|-------|-------|----------|---------|
| 1a Definition | Founder/team | 4-8h | Needs decision: NTEECC vs NTEE2? |
| 1b Canon table | Backend | 2-4h | Depends on 1a |
| 1c Data fixes | Backend | 4-8h | Depends on 1b |
| 2 Scoring run | Backend | 1-2h | Depends on 1 |
| 3 API wiring | Backend | 2-4h | Can run in parallel with 1 |
| 4 Frontend | Frontend | 1-2h | Depends on 3 |
| 5 Testing | QA/Eng | 2-4h | Depends on all prior |
| 6 Reroll | DevOps | 10 min | Depends on 5 |

**Total:** 16-32 hours (2-4 days of focused work)

---

## Success Criteria

- ✅ Canonical v6 definition documented
- ✅ One authoritative output table (no disagreement)
- ✅ Scoring run recorded with full metadata
- ✅ All data quality issues fixed
- ✅ Search API returns v6 fields
- ✅ Frontend reads DB values, not hardcoded
- ✅ All invariant tests pass
- ✅ 5+ spot checks manual verification
- ✅ Zero hardcoded values in code
- ✅ Reroll to daanaa.org passes smoke tests

---

## Risk Mitigation

- If decisions on 1a take too long, proceed with current database state + add scoring_run record (get reproducibility first)
- Test on staging before reroll to production
- Keep original tier_assignments as backup until reroll succeeds
- Monitor frontend display closely post-reroll for data inconsistencies
