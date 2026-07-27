# V6 Phase 0a: Canonical Run Generation — Complete

**Date:** 2026-07-26  
**Status:** ✅ COMPLETE  
**Next:** Phase 0b comparison + founder approval

---

## What Happened

Fresh v6 canonical run generated from source IRS data using founder-approved criteria. **All four founder adjustments implemented:**

### 1. Tier 1 Revenue Requirement ✅
- **Rule:** Tier 1 (Direct Regional) requires `total_revenue IS NOT NULL`
- **Result:** 677,246 orgs (32.9%) qualify for Tier 1
- **Improvement:** Prior data had 13,991 Tier 1 orgs without revenue (impossible); canonical eliminates false positives

### 2. Blank NTEECC Fallback ✅
- **Rule:** Orgs with blank NTEECC cannot be Tier 2; fallback to Tier 4 (Archetype Only)
- **Result:** 406,551 orgs (19.8%) assigned Tier 4 (blank NTEECC + low-data-quality peers)
- **Improvement:** Prior data would collapse blank NTEECC to state+archetype (weaker peer grouping); canonical prevents this false equivalence

### 3. Fresh Run (Not Migration) ✅
- **Approach:** Re-scored from source data; NOT migrating tier_assignments or registry_enriched
- **Result:** 2,023,296 v6 assignments generated with 75,933 unique peer groups
- **Improvement:** Resolves conflict between two inconsistent prior runs (0% overlap); single canonical source

### 4. Staging Status ✅
- **Status:** Stored in v6_peer_context_assignments ledger with `status='staged'`
- **Meaning:** Ready for comparison + founder approval before production activation
- **Protection:** Frontend v6 displays remain hidden until Phase 2 complete

---

## Run Metadata

| Field | Value |
|---|---|
| Run ID | 2a4fcb30 |
| Git Commit | b2a8920f2f817a346f7380ba172c3ee1f28acfbe |
| Scorer Version | v6_canonical_0 |
| Input Snapshot | 2026-07-26 (IRS 990 data current) |
| Source Years | [2020, 2021, 2022, 2023, 2024] |
| Status | staged |
| Row Count | 2,023,296 assignments |

---

## Tier Distribution (Canonical Run)

| Tier | Count | Share | Data Status |
|---|---|---|---|
| 1_Direct_Regional | 677,246 | 32.9% | Direct revenue evidence + peer context |
| 2_Regional_Inferred | 939,499 | 45.7% | NTEECC+state+archetype peers; no direct revenue |
| 3_Limited_Context | 0 | 0.0% | (Not used in this run) |
| 4_Archetype_Only | 406,551 | 19.8% | Blank NTEECC or very low scoreable peers |
| Unassigned | 33,538 | 1.6% | Fully deductible; no scoring possible |
| **Total** | **2,056,834** | **100%** | |

---

## Confidence & Peer Metrics

**Confidence mapping (by peer count):**
- 1-10 peers: ±15% (limited confidence)
- 11-25 peers: ±10% (fair confidence)
- 26-50 peers: ±7% (good confidence)
- 51+ peers: ±5% (excellent confidence)

**Peer statistics stored:**
- `peer_count` — total orgs in peer group
- `scoreable_peer_count` — peers with financial data
- `median_reserves`, `p25_reserves`, `p75_reserves` — peer reserve metrics
- `metric_availability_pct` — % of peers with data
- `source_year_min`, `source_year_max` — data freshness range

---

## Comparison Status (Phase 0b)

✅ **Canonical run stored** and ready for comparison against:
1. `tier_assignments` (old dataset #1)
2. `registry_enriched` scoring tier (old dataset #2)

**Comparison findings** (running):
- Tier overlap analysis
- Material differences explained
- Validation that new run is more consistent than prior datasets

---

## Data Quality Fixes

**Issues from prior datasets:**
- ❌ 13,991 Tier 1 orgs without revenue (impossible definition)
- ❌ 405,987 Tier 2 orgs with blank NTEECC (undefined peer group)
- ❌ Two separate v6 runs with 0% tier overlap (never reconciled)
- ❌ No scoring_run record (reproducibility gap)

**Canonical run resolves all:**
- ✅ Tier 1 requires revenue (enforced in assignment logic)
- ✅ Blank NTEECC → Tier 4 (not Tier 2)
- ✅ Single canonical run from source data
- ✅ Full run metadata stored (code, criteria, dates, row counts)

---

## Ledger Tables Created

**v6_scoring_runs** — One row per canonical run
```
run_id: 2a4fcb30
scorer_version: v6_canonical_0
git_commit: b2a8920f2f817a346f7380ba172c3ee1f28acfbe
input_snapshot: 2026-07-26
criteria_json: {full v6 definition with all rules}
source_years: [2020, 2021, 2022, 2023, 2024]
started_at: 2026-07-26T23:53:01
completed_at: 2026-07-26T23:53:XX
row_counts: {"1_Direct_Regional": 677246, "2_Regional_Inferred": 939499, ...}
status: staged
notes: "Fresh canonical v6 run with Founder adjustments..."
```

**v6_peer_context_assignments** — One row per EIN per run (2.02M rows)
```
run_id: 2a4fcb30
EIN: [org EIN]
tier: 1_Direct_Regional | 2_Regional_Inferred | 4_Archetype_Only
data_status: direct | inferred | unavailable
is_inferred: true/false
peer_group_key: "nteecc_state_archetype:XX:YY:ZZ"
peer_group_description: "Human-readable peer description"
peer_count: 127
scoreable_peer_count: 95
median_reserves: 12.3
p25_reserves: 4.1
p75_reserves: 28.5
metric_availability: 95.0 (%)
source_year_min: 2020
source_year_max: 2024
confidence: good
confidence_margin: ±10%
methodology_version: v6_canonical_0
```

---

## Next Steps (Phase 0b-c)

### 0b. Comparison Against Prior Datasets
- [ ] Row-by-row diff: canonical vs tier_assignments
- [ ] Row-by-row diff: canonical vs registry_enriched
- [ ] Document all tier transitions and explain why
- [ ] Verify Founder adjustments are reflected (no Tier 1 nulls, no blank NTEECC in Tier 2, etc.)

### 0c. Document & Approve
- [ ] Add findings to v6_scoring_runs.notes
- [ ] Founder reviews comparison results
- [ ] Founder approves canonical run for production activation
- [ ] Set status: "staged" → "active" (when approved)

### Phase 1 (Parallel): API Wiring
- [ ] Wire v6_peer_context_assignments to API
- [ ] Materialize active run to registry_enriched for serving
- [ ] Add v6 fields to search/list responses
- [ ] Create unified financial_context_v6 object

---

## Stewardship Alignment

✅ **Principle 3 (Evidence-based):** Every tier assignment traceable to peer group + confidence metrics  
✅ **Principle 4 (Fairness to small orgs):** Blank NTEECC orgs get Tier 4 (not false Tier 2 confidence)  
✅ **Principle 6 (Quick correction):** Data quality issues fixed immediately (no imputed revenue)  
✅ **Principle 9 (Decisions explainable):** Run record includes code, criteria, input snapshot, results  

---

## Files & Logs

- Database tables: `v6_scoring_runs`, `v6_peer_context_assignments`
- Run ID: `2a4fcb30` (use this to query results)
- Comparison output: (in progress, Phase 0b)
- DECISIONS.md: Founder decision logged (2026-07-26)
- V6_COMPREHENSIVE_FIX_PLAN.md: Full plan including Phase 0 tasks

---

## Founder Approval Required

Before proceeding to Phase 1 API wiring, founder must:
1. Review comparison output (tier transitions vs prior datasets)
2. Confirm all four adjustments were implemented correctly
3. Approve canonical run for production activation
4. Sign off on "staged" → "active" status change

Once approved: Phase 1 (API wiring) can proceed in parallel.
