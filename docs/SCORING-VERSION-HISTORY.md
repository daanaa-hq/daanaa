# Daanaa Scoring Version History

**Purpose:** Reconstruct how Daanaa’s nonprofit financial-context methodology evolved through v6, with explicit coverage and evidence status.

**As-of:** 2026-07-28  
**Important status note:** v6 is being made public as of this record. The repository still contains reconciliation findings from the pre-rollout audit, so this document distinguishes the public rollout from a fully verified, stable production state.

## Executive summary

The scoring system moved through four major improvements:

1. From a general composite score to cause-aware peer comparison.
2. From broad peer cells to operating-model and revenue-band context.
3. From a single numeric score to descriptive, donor-facing financial context.
4. From assuming data coverage to explicitly separating direct evidence, peer inference, confidence, and data gaps.

The strongest improvement is not simply more organizations covered. It is that the system increasingly distinguishes what is known about an organization from what is typical of similar organizations. The main remaining weakness is historical reproducibility: several coverage figures are launch claims or snapshots rather than results tied to a durable scoring-run record.

## Version-by-version history

| Version | Methodological change | Data / coverage evidence | Main improvement | Evidence status |
|---|---|---|---|---|
| **v1.0 baseline** | Composite of six financial metrics: program ratio, fundraising efficiency, liabilities, administration, revenue growth, and reserves. Peers were grouped primarily by NTEE code and seven revenue bands. | The changelog says approximately **86,451** organizations received a revenue-percentile-only score, while the underlying XML source had about **27K** organizations with fuller 990 data. | Established the first auditable 0–100 score and peer-relative comparison. | Historical scorer is preserved in `archive/legacy_scorers_20260609/merit_scorer.py`. The changelog labels the production state “v1.0” while naming the v3.3 script, so the release label needs normalization. |
| **v2.0** | Restricted the universe to deductible organizations; introduced four operating-model groups × six revenue bands; corrected percentage scaling; handled reserve sentinels; excluded revoked organizations. | No single authoritative v2 coverage total was found in the reviewed records. | Corrected major validity problems: non-deductible entities, distorted reserve values, and unlike organizations being benchmarked together. | The archived scorer and changelog document the design. A durable v2 scoring-run record was not found. |
| **v3.3** | Used four metrics—program ratio, sustainability ratio, reserves ratio, and leverage ratio—with NTEE-major × revenue-band peers and fallback groups. Read NTEE directly from extracted 990 XML. | The scorer header says this expanded the scorable set from about **11K to 15K+** organizations. The v1 changelog describes the broader XML source as approximately **27K** organizations. | Improved input extraction and increased the fully financial-data-backed population. | Scorer is preserved in `archive/legacy_scorers_20260609/merit_scorer_v3_3.py`; exact final v3 run counts are not recorded in one canonical run table. |
| **v4.0** | Introduced model-specific financial health: eight operating models, model-specific revenue bands, percentile ranking within peer cells, robust metrics, and Strong / Stable / Inspiring language. Added a separate visibility/data-completeness scale. | **71,473** Tier A organizations with complete financial fingerprints. Launch records also claim **379,990** total organizations across Tier A and Tier B, or **81%** of the then-claimed 501(c)(3) universe. | Made small-org fairness explicit: organizations are compared with similar operating models and budgets rather than the whole sector. Added honest separation between data visibility and financial context. | Strongest historical deployment documentation, but launch records contain conflicting tier definitions and totals. Treat 71,473 as the clearest fully-scored figure. |
| **v5.0** | Replaced the v4 model taxonomy with financial archetypes × three revenue bands: Donation-Funded, Fee-for-Service, and Endowment in the implemented mapping. Scores are percentile ranks within the archetype/band cell. Added health signals, peer counts, and donor-facing explanations. | The roadmap claims **447,557** organizations and 1.75M org-years; later recorded full recomputations show **364,369** and then **376,776** scored, with **three archetypes** actually assigned. The current local database has **372,781** non-null `merit_score_v5` values. | Simplified the taxonomy for donor comprehension and made the peer group itself part of the explanation. Added repeatable full and delta scoring runs. | v5 has the best run-history evidence in `scoring_runs`, but its planned five-archetype design did not fully materialize; this should be stated plainly. |
| **v6 — public rollout** | Moves from one score toward a tiered peer-context system. The checked-in scorer proposes NTEE2 × revenue band × Census region, then national and broad-category fallbacks, with minimum scoreable-peer thresholds and confidence labels. Related inference documents add direct vs. inferred context and archetype/geographic fallback logic. | The audited local database contains **2,056,834** registry rows; **2,053,335** have v6 assignment fields: 738,130 Tier 1, 1,260,923 Tier 2, 52,057 Tier 3, and 2,225 Tier 4. **3,499** are unassigned. This is about **97.2%** with Tier 1–2 assignment fields, but not 97.2% direct financial scoring. | Biggest conceptual advance: missing organization-level financial data is no longer silently presented as the organization’s own health. Context can be direct, inferred from peers, limited, or archetype-only, with confidence and uncertainty. | **Public rollout in progress.** The pre-rollout v6 audit found that the checked-in scorer, populated database fields, methodology, API, and frontend did not yet form one reproducible contract. Those items should be tracked as rollout verification work, not treated as evidence that v6 is not public. |

## Coverage evolution: what the numbers mean

Coverage has not been measured consistently across versions. At least four different quantities appear in the repository:

- **Registry coverage:** how many organizations are present in the directory.
- **Financially scoreable coverage:** how many organizations have enough own financial data for a numeric score.
- **Peer-context coverage:** how many organizations can be placed in a sufficiently large peer group.
- **Display coverage:** how many organizations receive any badge or descriptive context, including data-gap states.

These must not be presented as interchangeable. For example, v6’s approximately 97.2% assignment-field coverage includes inferred and limited contexts; it does not mean 97.2% of organizations have complete financial records.

The current local database snapshot provides this verified baseline:

| Field | Rows |
|---|---:|
| Registry organizations | 2,056,834 |
| Deductible organizations | 1,881,286 |
| Non-null v4 `merit_score` | 537,776 |
| Non-null v5 `merit_score_v5` | 372,781 |
| Non-null v6 assignment | 2,053,335 |
| Unassigned v6 | 3,499 |

These are local database counts as of the audit query, not a claim about production. They should be dated whenever published.

## What materially improved

### 1. Peer fairness

Early versions compared organizations using relatively broad NTEE/revenue cells. v4 introduced operating-model-specific peers; v5 introduced financial archetypes; v6 makes NTEE granularity, geography, peer count, and fallback level explicit. This is the core fairness trajectory.

### 2. Data honesty

The system moved from displaying one score even when data was thin toward three distinct states:

- direct organization evidence;
- inferred context based on similar organizations;
- no numeric context when evidence is too sparse.

That change aligns with the stewardship rule that missing data should not become a fabricated estimate.

### 3. Dignity and interpretation

The language moved away from “Exceptional / Concerns” toward peer-relative, model-aware language such as Strong, Stable, Inspiring, and finally neutral context tiers. The purpose became helping donors understand a nonprofit’s situation, not issuing a universal charity grade.

### 4. Operational reproducibility

v5 introduced recurring full and delta scoring records in `scoring_runs`. v6’s next required improvement is to carry that discipline forward: every candidate run needs a code version, input snapshot, source-year range, exact rules, row counts, and completion status.

## What may have been missed

These are the main gaps to resolve before calling the history complete or publishing it externally:

1. **Normalize version names.** The methodology changelog calls the pre-v4 production state v1.0 but points to the v3.3 scorer. Decide whether v1–v3 are model versions, implementation iterations, or release labels.
2. **Separate “scored” from “context assigned.”** Coverage tables should report direct, inferred, limited, archetype-only, and unassigned populations separately.
3. **Reconcile v5 claims.** The design says five archetypes, while the implemented mapping and run notes say three were actually assigned. The 447,557 roadmap figure also differs from later 364K–377K run records.
4. **Create a v6 canonical run record.** `scoring_runs` contains v4/v5 history but no equivalent reproducible v6 run record; v6 tables also disagree materially in the audit.
5. **Record data freshness.** Each version should state the IRS filing years and the snapshot date, not only the number of organizations.
6. **Record field-level availability.** “Has a score” should be accompanied by which metrics were available: revenue, expenses, reserves, assets, liabilities, program spending, and source year.
7. **Document validation, not only implementation.** Every version should include distribution checks, peer-cell minimums, missing-data rates, small-organization fairness checks, revoked-organization checks, and regression comparisons against the prior version.
8. **Record rollout completion separately from methodology release.** v6 is being made public now; the remaining question is whether the implementation, coverage counts, API, frontend, and audit evidence are synchronized after rollout.

## Recommended canonical record for future versions

For each scoring version, retain one immutable record with:

```text
version
status: candidate | staging | production | retired
effective_at
code_commit
input_snapshot
source_year_range
registry_count
eligible_count
direct_context_count
inferred_context_count
limited_context_count
no_context_count
unassigned_count
peer_definition
minimum_peer_rules
metric_fields_and_weights
validation_results
known_limitations
approval_record
```

That structure would let the team answer “how did we improve?” with both a narrative and defensible numbers.

## Source files reviewed

- `archive/legacy_scorers_20260609/merit_scorer.py` (v1 baseline)
- `archive/legacy_scorers_20260609/merit_scorer_v2_0.py` (v2.0)
- `archive/legacy_scorers_20260609/merit_scorer_v3_3.py` (v3.3)
- `scripts/archive_scorers/merit_scorer_v4_0.py` (v4.0, archived)
- `scripts/archive_scorers/merit_scorer_v5_0.py` (v5.0, archived)
- `scripts/daanaa_scorer.py` (v6 — current active scorer, renamed from merit_scorer_v6_0.py)
- `docs/METHODOLOGY-CHANGELOG.md`
- `docs/V6_SCORING_DATA_AUDIT_2026_07_26.md`
- `docs/METHODOLOGY_V6_INFERENCE.md`
- `docs/V5_COMPLETE_ROADMAP.md`
- `LAUNCH-READY-2026-06-04.md`
- local `data/merit_registry.db` counts and `scoring_runs`
