# v6 Scoring Data Audit

**Date:** 2026-07-26  
**Scope:** Local `data/merit_registry.db`, checked-in v6 methodology/scorer, API serialization, and frontend display  
**Mode:** Read-only audit. No scoring, database, deployment, or public methodology changes were made.

## Executive finding

The local database already contains v6 assignments, but the current database values, the checked-in scorer, the methodology document, and the frontend do not yet form one reliable end-to-end contract.

The v6 direction is promising for smaller nonprofits because it can provide useful peer context without pretending that missing financial data is known. It should not be released publicly until the source of truth and display language are reconciled.

## What is currently in the database

`registry_enriched` contains **2,056,834** organizations. v6 fields are populated for **2,053,335** organizations; **3,499** have no v6 assignment.

| Stored v6 tier | Rows | Share of registry | Observed characteristics |
|---|---:|---:|---|
| `1_Direct_Regional` | 738,130 | 35.9% | `is_inferred_v6=0`; 724,139 have non-null revenue, but 13,991 do not |
| `2_Regional_Inferred` | 1,260,923 | 61.3% | All have null revenue; peer group size is at least 5 |
| `3_Limited_Context` | 52,057 | 2.5% | All have null revenue; peer group size is at least 5 |
| `4_Archetype_Only` | 2,225 | 0.1% | No revenue; stored peer size is 1 rather than null |
| Unassigned | 3,499 | 0.2% | All are deductible records; all have missing/blank NTEECC |

The current data therefore shows approximately **97.2%** in Tier 1 or Tier 2, not the **72% / 1.49M** coverage stated in `docs/METHODOLOGY_V6_INFERENCE.md`. The document and data appear to represent different runs or different criteria.

## Criteria and data mismatches

### 1. Two different v6 models exist

The checked-in `scripts/merit_scorer_v6_0.py` implements:

- NTEE2 + revenue band + Census region for Tier 1
- NTEE2 + revenue band nationally for Tier 2
- NTEE2 nationally for Tier 3
- scoreable peers counted by `months_of_reserve`
- thresholds of 25, 20, and 5 scoreable peers

The populated v6 tables instead point to peer groups keyed by:

- `NTEECC`
- `STATE`
- `merit_archetype_v5`

That is closer to the newer inference methodology, but there is no checked-in generator or v6 scoring-run record that explains how the current fields were produced. The checked-in scorer would not reproduce the current tier names or current distributions.

### 2. Tier 2 is not always the documented peer group

The documentation promises NTEE subcategory + state + archetype. In the current data, **405,987 Tier 2 rows have blank NTEECC**. Their peer grouping effectively collapses to state + archetype unless blank NTEECC was intentionally defined as a valid category.

The stored descriptions also say only, for example, `76 similar organizations in OH`. They do not identify the NTEE category or funding archetype, so a donor cannot understand what “similar” means.

For sampled groups, the stored peer count matches `peer_group_stats`, and the groups have at least one revenue-data peer. The minimum revenue-data peer count observed for Tier 2 groups is 1. That can be acceptable as a carefully labeled fallback, but it is not equivalent to a stable estimate of a median financial pattern.

### 3. Direct labels include organizations without revenue

Tier 1 is documented as using an organization’s own revenue data. **13,991 Tier 1 rows have `total_revenue IS NULL`**. This needs either a data correction or a different label and definition. A zero-revenue filing should also be distinguished from no reported revenue rather than silently treated as the same state.

### 4. Inferred financial values are not present in the v6 data contract

The current v6 columns store tier, inference flag, peer count, description, confidence, and margin text. They do not store the inferred peer median, percentile range, metric availability, or source-year summary described by the methodology.

The existing `peer_benchmarking` table contains 537,529 rows, but it contains only `reserve_ratio` and is built around organizations with their own `your_value`. It does not provide the v6 inferred metrics for the sampled Tier 2 organizations.

### 5. Confidence margins are populated consistently, but the UI does not use them

The database margin mapping is internally consistent:

- 5–10 peers → ±15%
- 11–25 peers → ±10%
- 26–50 peers → ±7%
- 51+ peers → ±5%

However, `frontend/src/components/FinancialContext.tsx` currently hardcodes `±10%` and hardcodes an inferred reserve value of **2.1 months**. That means an organization with a database margin of ±15%, ±7%, or ±5% can be shown the wrong uncertainty, and the displayed 2.1 months is not traceable to the organization’s peer group.

## API and frontend wiring gaps

### Search and directory responses

The organization list query in `daanaa_api.py` selects the older v5 fields but does not select the v6 fields (`daanaa_api.py:2318-2330`). Directory/search cards therefore cannot reliably display the v6 context.

### Organization detail response

The detail route selects `r.*` and adds the v6 fields (`daanaa_api.py:2613-2619`), so the raw detail response can contain them. This is not enough by itself because the display component currently reads `org.scoring_tier` (`frontend/src/components/FinancialContext.tsx:10`) rather than `org.scoring_tier_v6_inference`.

The component also uses the older tier names in its conditional rendering while checking for the newer tier names. As a result, the v6 inference display can be absent or can show stale/incorrect context even when the database has v6 data.

## Reproducibility and governance gaps

- `scoring_runs` contains v4 and v5 runs but no v6 run record.
- `tier_assignments` and `registry_enriched` disagree materially for the same EINs: 8,672 tier differences; 397,742 inference-flag differences; 390,524 peer-size differences; 1,222,255 confidence differences; 423,944 margin differences; and 773,004 description differences.
- `tier_assignments` has no run timestamp, source snapshot, or code/version reference.
- The methodology says v6 is effective 2026-08-01, while the local catalog is already populated on 2026-07-26. This is fine for a staged candidate run, but the release state needs to be explicit.

These are not reasons to abandon v6. They are reasons to keep it in candidate/staging status until one canonical assignment table and one reproducible run are established.

## Recommended order of work

1. Choose and write down the canonical v6 definition: exact NTEE granularity, geography, archetype use, revenue/no-revenue rules, minimum peer counts, and fallback behavior for blank NTEECC.
2. Choose one canonical output table. Treat the other v6 table as a snapshot only, or regenerate it from the canonical run.
3. Add a v6 scoring-run record with code version, input snapshot, source years, thresholds, row counts, and completion time.
4. Store inferred metrics with their peer count, available metric count, median/interval, source years, and uncertainty. Do not manufacture those values in the frontend.
5. Return one shared `financial_context_v6` object from both list and detail APIs. It should clearly separate direct organization data from peer-derived context.
6. Update the frontend to consume that object, use the stored margin, and describe the actual peer group. Remove hardcoded inferred values.
7. Add invariant tests before any rollout:
   - direct tier requires direct revenue evidence;
   - inferred tier has no claim about the organization’s actual finances;
   - blank NTEECC follows an explicit fallback tier;
   - peer counts and confidence margins agree;
   - every displayed metric has a source and data-year range;
   - the same run reproduces the same assignment for the same input snapshot.

No deployment or scoring-methodology change should happen until these checks pass and the founder approves the public wording. The stewardship-safe presentation is “context from similar organizations,” never “this organization’s financial health,” when the organization’s own data is unavailable.
