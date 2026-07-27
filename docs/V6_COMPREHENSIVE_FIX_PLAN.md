# V6 Scoring Comprehensive Fix Plan

**Status:** PHASE 0 APPROVED — Founder decision: Create immutable versioned v6 scoring ledger  
**Priority:** High (major milestone)  
**Scope:** Complete v6 backend + frontend overhaul (9-12 days focused work)

---

## Current State Summary

**Audit findings (2026-07-26):**
- Two inconsistent v6 datasets: `tier_assignments` (61.3% Regional/35.9% Direct) vs `registry_enriched` (45.3% Broad/26.2% Full)
- 0% tier overlap between tables — completely different v6 runs
- No v6 scoring_run record (reproducibility gap)
- 13,991 Tier 1 orgs lack revenue data (violates "Direct" definition)
- 405,987 Tier 2 orgs have blank NTEECC (peer groups undefined)
- Frontend hardcodes "2.1 months" and "±10%" instead of reading DB values
- Search API omits v6 fields entirely
- Frontend deployed to daanaa.org but v6 displays still broken (field mismatches, hardcoding)

**Founder Decision (2026-07-26):**
Do NOT migrate between existing tables. Create new immutable, versioned v6 scoring ledger. Existing tables become inputs/snapshots/serving projections, never source-of-truth.

**Four Plan Adjustments from Founder:**
1. ✅ Generate fresh canonical v6 run (don't migrate existing data). Compare against both datasets, publish only after differences explained.
2. ✅ Blank NTEECC ≠ Tier 2. Use broader fallback tier or Tier 4 (do not describe state+archetype peers as same type).
3. ✅ Tier 1 requires direct revenue. Relabel or exclude 13,991 Tier 1 nulls (do not impute).
4. ✅ Frontend v6 display is deployed but broken (field mismatches, hardcoding). Keep v6 hidden/staged until Phase 2 complete.

---

## Comprehensive Fix Phases

### PHASE 0: V6 Scoring Ledger Foundation (3-4 days)
**Goal:** Create immutable versioned v6 scoring ledger with fresh canonical run

#### 0a. Create V6 Scoring Ledger Schema
- [ ] Create `v6_scoring_runs` table (metadata for each v6 run):
  ```sql
  run_id UUID PRIMARY KEY
  scorer_version VARCHAR (e.g. "v6_canonical_0")
  git_commit VARCHAR (code version for reproducibility)
  input_snapshot DATETIME (when input data was current)
  criteria_json JSONB (exact v6 definition: NTEE granularity, fallback rules, revenue requirements, peer minimums)
  source_years TEXT (e.g. "2020-2024")
  started_at DATETIME
  completed_at DATETIME
  row_counts JSONB (counts by tier: {"tier_1": X, "tier_2": Y, "tier_3": Z, "tier_4": W})
  status VARCHAR (in_progress | completed | staged | failed | active)
  notes TEXT
  ```

- [ ] Create `v6_peer_context_assignments` table (authoritative v6 assignments per EIN per run):
  ```sql
  run_id UUID (foreign key to v6_scoring_runs)
  EIN VARCHAR
  tier VARCHAR (1_Direct_Regional | 2_Regional_Inferred | 3_Limited_Context | 4_Archetype_Only)
  data_status VARCHAR (direct | inferred | limited | unavailable | contested)
  is_inferred BOOLEAN
  peer_group_key VARCHAR (NTEECC+STATE or fallback key when NTEECC blank)
  peer_group_description VARCHAR
  peer_count INTEGER (all orgs in peer group)
  scoreable_peer_count INTEGER (orgs in peer group with financial data)
  median_reserves DECIMAL (months of operating reserve, peer median)
  p25_reserves DECIMAL (months, peer 25th percentile)
  p75_reserves DECIMAL (months, peer 75th percentile)
  metric_availability DECIMAL (% of peers with reserve data)
  source_year_min INTEGER (earliest filing year in peer data)
  source_year_max INTEGER (latest filing year in peer data)
  confidence VARCHAR (good | fair | limited | unavailable)
  confidence_margin VARCHAR (±5% | ±7% | ±10% | ±15%)
  methodology_version VARCHAR (e.g. "v6_canonical_0")
  
  PRIMARY KEY (run_id, EIN)
  FOREIGN KEY (run_id) REFERENCES v6_scoring_runs(run_id)
  ```

- [ ] Preserve `tier_assignments` as historical snapshot (do not modify)
- [ ] Update `registry_enriched` schema to add columns for materialized copy of active run (for API performance)
- [ ] Create config table to track active run_id (single source of truth for API)

#### 0b. Define V6 Canonical Criteria (Four Founder Requirements)

**1. Tier 1 (Direct) requires non-null revenue:**
- [ ] Criterion: `total_revenue IS NOT NULL` → eligible for Tier 1
- [ ] Handle 13,991 current Tier 1 nulls: relabel to Tier 2 (inferred) or Tier 3 (limited)
- [ ] Do NOT impute missing revenue
- [ ] Document in criteria_json: `"tier_1_requires_revenue": true`

**2. Blank NTEECC has explicit fallback (not Tier 2):**
- [ ] Do NOT assign blank NTEECC orgs to Tier 2
- [ ] Fallback rule: Use Tier 3 (Limited Context) or Tier 4 (Archetype Only) depending on archetype match quality
- [ ] Rationale in notes: "state + archetype grouping is weaker than NTEE-based grouping; smaller peer counts, higher uncertainty"
- [ ] Document in criteria_json: `"blank_nteecc_fallback": "tier_3_or_tier_4_by_archetype_only"`
- [ ] Peer group description must reflect this: "Organizations similar in funding model (state not a factor)" vs full NTEE match

**3. Generate fresh canonical run (no migration):**
- [ ] Do NOT copy/migrate tier_assignments or registry_enriched v6 data
- [ ] Re-score from IRS 990 data using approved v6 criteria:
  - Criteria to document in criteria_json:
    - NTEE granularity: NTEECC (6-char) vs NTEE2 (first 2 chars)?
    - Geography: census region grouping? State? National?
    - Archetype: use merit_archetype_v5 (Donation-Funded / Fee-for-Service / Endowment-Funded)?
    - Peer count minimum per tier (e.g., Tier 2 minimum: 5 scoreable peers)
    - Scoreable peer definition: > X months of operating reserve data required?
    - Confidence margin mapping: peer count ranges to ±% confidence (e.g., 5-10 → ±15%, 11-25 → ±10%)

**4. Compare and document differences:**
- [ ] Row-by-row comparison: new v6 run vs tier_assignments
- [ ] Row-by-row comparison: new v6 run vs registry_enriched.scoring_tier
- [ ] For each material difference (tier mismatch, peer count divergence, etc.), explain why
- [ ] Document all findings in v6_scoring_runs.notes
- [ ] Examples of expected differences:
  - Blank NTEECC: old data may have Tier 2, new data has Tier 3/4 (fallback rule change)
  - Missing revenue: old data may have Tier 1, new data has Tier 2 (revenue requirement)
  - Peer count changes: new run uses different peer grouping criteria
- [ ] Only publish run after all material differences are explained + founder approves

#### 0c. Add Reproducibility & Audit Trail
- [ ] Create v6_scoring_runs record with:
  - `scorer_version`: "v6_canonical_0" (or version numbering scheme TBD)
  - `git_commit`: exact code commit hash (maker reproducible)
  - `input_snapshot`: timestamp when IRS/ProPublica data snapshot was created
  - `criteria_json`: complete definition (NTEE, geography, archetype use, peer minimums, fallback rules, confidence mapping)
  - `source_years`: [2020, 2021, 2022, 2023, 2024] or actual
  - `row_counts`: by tier (Tier 1: X, Tier 2: Y, Tier 3: Z, Tier 4: W, Total: N)
  - `started_at`, `completed_at`: run timing
  - `status`: "staged" (not yet active; must pass Phase 1-3 before activation)
  - `notes`: explanations of material differences vs prior runs

- [ ] Preserve all v6_scoring_runs records (never delete; historical accountability)
- [ ] Set up "active run" config: one run_id designated as live (API reads from this)
- [ ] Document this run in METHODOLOGY.md: "v6 Canonical, Run 1, Generated 2026-07-26"

### PHASE 1: Backend Alignment (2-3 days)
**Goal:** Wire v6 ledger into API; materialize to registry_enriched for serving

#### 1a. API Wiring
- [ ] Add v6 fields to search/list API response (`/api/organizations`):
  ```json
  {
    "scoring_tier_v6": "1_Direct_Regional",
    "data_status_v6": "direct",
    "is_inferred_v6": false,
    "confidence_v6": "good",
    "confidence_margin_v6": "±10%",
    "peer_group": {
      "description": "Education nonprofits in MA",
      "size": 127,
      "scoreable_count": 95,
      "median_reserve_months": 12.3,
      "p25_reserve_months": 4.1,
      "p75_reserve_months": 28.5,
      "metric_availability_pct": 95,
      "source_years": [2020, 2021, 2022, 2023]
    }
  }
  ```

- [ ] Update search API (daanaa_api.py lines 2318-2330) to include v6 fields (currently v5-only)
- [ ] Verify detail API includes v6 fields (should inherit from active run join)
- [ ] Create unified `financial_context_v6` object in both endpoints
- [ ] Ensure both list and detail responses use same schema

#### 1b. Materialization for Performance
- [ ] Query active v6_scoring_runs.run_id from config table
- [ ] Materialize v6_peer_context_assignments for active run into registry_enriched columns:
  - `scoring_tier_v6` ← tier
  - `data_status_v6` ← data_status
  - `is_inferred_v6` ← is_inferred
  - `confidence_v6` ← confidence
  - `confidence_margin_v6` ← confidence_margin
  - `peer_group_size_v6` ← peer_count
  - `median_reserve_months_v6` ← median_reserves
  - (and other peer metrics)
- [ ] Refresh materialized columns on v6 run activation (not continuously)
- [ ] Add index on (run_id, EIN) to v6_peer_context_assignments for fast lookups

#### 1c. Add Invariant Tests (to verify ledger correctness)
- [ ] Tier 1 requires revenue: `SELECT COUNT(*) FROM v6_peer_context_assignments WHERE tier = '1_Direct_Regional' AND EIN NOT IN (SELECT EIN FROM registry_enriched WHERE total_revenue IS NOT NULL)` → should be 0
- [ ] Blank NTEECC follows fallback: `SELECT COUNT(*) FROM v6_peer_context_assignments WHERE EIN IN (SELECT EIN FROM registry_enriched WHERE NTEECC IS NULL) AND tier IN ('1_Direct_Regional', '2_Regional_Inferred')` → should be 0
- [ ] Peer counts accurate: spot-check 10 random Tier 2 orgs; recount peers and verify `peer_count` matches
- [ ] Confidence margins consistent: verify margin maps to peer_count ranges (5-10 → ±15%, etc.)
- [ ] Run reproducible: re-run scorer with same criteria → same tier assignments for same inputs
- [ ] Ledger immutable: v6_scoring_runs is write-once (no updates to completed runs)

### PHASE 2: Frontend Migration (2 days)
**Goal:** Use real v6 data instead of hardcoded values; keep v6 hidden until complete

#### 2a. Remove Hardcoding
- [ ] FinancialContext.tsx: Read actual margin from `financial_context_v6.confidence_margin` (not hardcoded "±10%")
- [ ] FinancialContext.tsx: Read actual median from `financial_context_v6.peer_group.median_reserve_months` (not hardcoded "2.1 mo")
- [ ] Read peer group description from API: "Among X organizations in [description]"
- [ ] Remove all hardcoded v6 display values
- [ ] Link to methodology with current data version

#### 2b. Fix Frontend Field Mismatches
- [ ] Check all v6-related components read correct field names:
  - Read `scoring_tier_v6_inference` not `scoring_tier`
  - Read `confidence_v6` not old confidence fields
  - Read `peer_group_size_v6` not old peer counts
- [ ] Update Home, Directory, CategoryPage, ComparePage, OrganizationDetail, WalletPage to use v6 fields from active run

#### 2c. Implement Organization Profile Information Spec
Per the organization profile information spec provided by user (10-section):

**Information States:**
- [ ] State A: Broad information (show all)
- [ ] State B: Limited information (careful wording, no judgment)
- [ ] State C: Little/no information (identity facts only)
- [ ] State D: Contested information (preserve both, never overwrite)

**Field-level contract:**
- [ ] Every displayed field has: value, source, source_url, source_date, tax_year, supplied_by, confidence, inferred_flag, visibility_status
- [ ] No blending of sources without clear labels
- [ ] No bare zeros (show "not reported" or hide)

**Progressive disclosure:**
- [ ] Important info immediate (who, what, how to give)
- [ ] Expandable sections for deeper records
- [ ] Hide empty sections
- [ ] Keep financial history, leadership, methodology below fold

**Direct vs. inferred separation:**
- [ ] Direct org data: "Based on this organization's public filing"
- [ ] Peer context: "Typical for similar organizations"
- [ ] Clearly separate; never blend unlabeled

#### 2d. Keep V6 Displays Staged (Not Yet Live)
- [ ] Do NOT activate v6 displays on daanaa.org until Phase 2 is complete
- [ ] Frontend code is deployed, but feature-flag v6 displays as "staging"
- [ ] Show "In development" or similar indicator
- [ ] Once Phase 2 passes QA, enable v6 displays with founder approval

### PHASE 3: Testing & Validation (2 days)
**Goal:** Ensure v6 is data-sound and user-safe

#### 3a. Invariant Tests
- [ ] Tier 1 Direct requires non-null revenue (0 violations)
- [ ] Blank NTEECC follows fallback rule (0 Tier 1/2 assignments for blank)
- [ ] Peer counts accurate (spot-check matches database)
- [ ] Confidence margins correct (peer size ranges map correctly)
- [ ] V6 run reproducible (re-run scorer produces identical tier assignments)
- [ ] No hardcoded values (frontend reads all values from API)
- [ ] Every displayed financial value has source + date

#### 3b. QA Test Matrix (10 profiles minimum)
- [ ] Full public information
- [ ] Mission only
- [ ] Identity + website only
- [ ] No mission, website, or financial data
- [ ] Reported zero values (with source)
- [ ] Inferred peer context
- [ ] Organization-provided values
- [ ] Contested information (both sources shown)
- [ ] Claimed but unpublished fields
- [ ] Empty sections hidden

#### 3c. Privacy & Security
- [ ] Run `scripts/privacy_check.sh` (must pass)
- [ ] No Tier 0 data leakage
- [ ] Wallet privacy unchanged
- [ ] Volunteer/donor privacy unchanged
- [ ] No new PII exposed

### PHASE 4: Founder Review & Approval (1 day)
**Gate:** No reroll to production without founder sign-off

- [ ] Founder reviews v6 scoring ledger design
- [ ] Founder reviews v6_scoring_runs record (criteria, row counts, differences vs prior runs)
- [ ] Founder reviews profile information spec implementation
- [ ] Founder approves public wording (especially "limited information" cases)
- [ ] Founder confirms no reputational risks
- [ ] Founder approves reroll to daanaa.org

---

## Success Criteria

**Backend:**
- ✅ v6_scoring_runs table created (immutable, versioned)
- ✅ v6_peer_context_assignments table created (authoritative ledger)
- ✅ Fresh canonical v6 run generated + row counts recorded
- ✅ All material differences vs prior runs explained + documented
- ✅ Tier 1 requires revenue (0 violations)
- ✅ Blank NTEECC follows fallback (0 Tier 1/2 violations)
- ✅ All invariant tests pass
- ✅ Search API returns v6 fields
- ✅ Unified financial_context_v6 object in both endpoints
- ✅ Active run config set + API reads from v6 ledger

**Frontend:**
- ✅ No hardcoded values (all read from API)
- ✅ Information states implemented (A/B/C/D)
- ✅ Direct vs. inferred clearly separated
- ✅ No bare zeros (missing data hidden or labeled)
- ✅ Every financial value has source + date
- ✅ Empty sections hidden
- ✅ Progressive disclosure working
- ✅ Privacy tests pass
- ✅ v6 displays staged/hidden until Phase 2 complete

**QA:**
- ✅ All 10-profile test matrix passing
- ✅ Privacy check passing
- ✅ Founder approval obtained

---

## Risk Mitigation

1. **Data loss:** Preserve tier_assignments as historical snapshot; never delete v6_scoring_runs
2. **API contract break:** Unified v6 object ensures consistency; test against both old + new tier names
3. **User confusion:** Clear labeling of information source + state + data freshness
4. **Reputational:** Founder sign-off on all public wording + criteria transparency
5. **Performance:** Materialize active run to registry_enriched for fast lookups

---

## Timeline Estimate

| Phase | Days | Blocker |
|-------|------|---------|
| Phase 0 | 3-4 | None (founder approved) |
| Phase 1 | 2-3 | Depends on Phase 0 |
| Phase 2 | 2 | Depends on Phase 1 |
| Phase 3 | 2 | Depends on Phase 2 |
| Phase 4 | 1 | Founder availability |
| **Total** | **10-13** | N/A |

---

## Next Steps

1. ✅ Founder approves ledger architecture (DONE 2026-07-26)
2. Begin Phase 0: Create v6 schema + generate fresh canonical run
3. Weekly check-ins to validate each phase
4. Founder approval gate before Phase 4 production reroll

**This approach:**
✅ Creates reproducible, immutable v6 scoring history  
✅ Enables rollback to any prior run  
✅ Provides full audit trail (code, criteria, results)  
✅ Separates source-of-truth (ledger) from serving projections  
✅ Satisfies Stewardship P9 (decisions explainable later)
