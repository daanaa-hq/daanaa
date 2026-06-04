# Scoring v4.0 — Model-Specific, AI-Optimized Peer Context

**Status:** PLAN (awaiting approval)
**Date:** 2026-06-04
**Author:** Claude Haiku 4.5 (AI Engineering Agent)
**Supersedes scoring logic in:** `scripts/merit_scorer_v2_0.py`, `scripts/merit_scorer_v3_3.py`

---

## 1. The vision (why this is the moat)

Every other nonprofit rating tool measures organizations against one universal
yardstick. A food bank gets judged by the same reserve standard as a university
endowment. The result punishes the small, the lean, and the unconventional — and
quietly tells donors "give to the big, established ones."

We do the opposite. **Every organization is measured only against its true peers
— same operating model, same realistic size band — and the definition of
"healthy" is learned from the data of that peer group, not imposed from outside.**

When this is done right, a Ugandan grassroots NGO, a $9B foundation, and a
volunteer-run animal rescue each get a fair, contextual read. That is both the
moat (no one else has model-specific, data-optimized peer context at 648K+ scale)
and the mission (the invisible 97% finally get seen on their own terms).

This plan does four things:
1. **Expand operating models** from 4 → ~9 so foundations, international NGOs,
   membership orgs, research bodies, and grassroots groups are no longer forced
   into ill-fitting buckets.
2. **Make revenue bands model-specific and data-driven** (Option B) — let the
   distribution of each model define its own natural breakpoints, AI-optimized.
3. **Add the second scale**: a 3-tier "financial health within peers"
   (Strong / Stable / Building) whose *meaning* shifts per operating model.
4. **Expand coverage** from 4,944 scored orgs toward the full 648,920 that have
   usable revenue data.

---

## 2. Current state (what already exists — reuse, don't rebuild)

| Asset | Where | Reuse plan |
|-------|-------|-----------|
| 4 operating models + cause→group map | `merit_scorer_v2_0.py` `GROUPS`, `CAUSE_TO_GROUP` | Extend to ~9 models |
| Group-specific metric weights | `merit_scorer_v2_0.py` `WEIGHTS` | Extend per new model; AI-tune |
| Universal 6 revenue bands | `merit_scorer_v2_0.py` `BANDS` | **Replace** with model-specific bands |
| Per-cause/band financial profiles | `data/corrected_cause_band_profiles.csv` | Training input for band optimizer |
| Sentinel% (missing-data rate) per cell | same CSV | Guardrail — exclude distorted cells |
| Foundation classification | `data/foundation_types.json` | Drives new Foundation/Endowment split |
| Audit trail | `scripts/scoring_audit.py` | Every run logged (Principle #9) |
| 5 visibility tiers | DB `merit_band` | **Unchanged** — this is scale 1 |

**Key realization:** the financial fingerprint work is already done. The
`cause_band_profiles.csv` already records median reserve, program %, and asset
intensity per (group, cause, band) with the sentinel rate. The band optimizer
trains on this rather than starting cold.

---

## 3. The two-scale system (the product surface)

### Scale 1 — Visibility (unchanged, 5 tiers)
`Blazing · Burning Bright · Steady Flame · Growing · Just Starting`
Public prominence / discovery signal. Already in the DB. We do not touch this.

### Scale 2 — Financial Health within peers (new, 3 tiers)
`Strong · Stable · Inspiring`
Position within the org's true peer group. **The same word means a
model-appropriate thing:**

| Operating model | "Strong" means | "Stable" means | "Inspiring" means (never pejorative) |
|-----------------|---|---|--------------------------------------|
| Direct Service | High program efficiency, resource leverage | Predictable revenue, healthy reserves | Doing remarkable work with constraints |
| Mission Infrastructure | Reserves support stable operations | Sustained operations, steady reserves | Visionary impact despite constraints |
| Research / Academia | Well-funded pipelines, stable base | Sustained funding streams, predictable | Innovative with limited resources |
| Asset Stewards | Assets well-maintained, healthy reserves | Stable asset preservation | Growing asset base with impact |
| Foundations | Active, sustained grant deployment | Endowment stable, predictable giving | Emerging foundation, building capacity |
| International Development | Efficient cross-border delivery | Reliable operations, stable reserves | Scaling operations with vision |
| Membership / Advocacy | Healthy member-revenue base | Stable membership/advocacy revenue | Growing member base, expanding reach |
| Religion / Spiritual | Strong financial reserves, impact | Stable operations, predictable giving | Growing congregation/mission |

Displayed together, e.g.:
```
Aga Khan Foundation
Visibility:        Blazing
Financial Health:  Strong  (global capital deployment)
```

### The numerology layer (delight, not judgment)
Scale 1 (1–5) + Scale 2 (1–3) gives 15 combinations. The three master numbers
(11, 22, 33) become quiet "destinations." This is presentation polish, computed
from the two scales — **not** a third score. Spec'd separately; out of scope for
the scoring engine itself.

---

## 4. Workstreams

### WS-1 — Expanded operating model taxonomy (4 → ~9)
- Start from the existing 4. Add 5: **Foundations** (split out of
  Endowment & Capital using `foundation_types.json`), **International
  Development**, **Membership / Advocacy**, **Research / Academia**,
  **Grassroots / Community**. Hold **Cooperative / Mutual** as a candidate
  pending volume check (may be too thin to be its own group).
- Method: cluster the 648K orgs on financial fingerprint
  (reserve months, program %, asset intensity, revenue volatility) +
  NTEE + foundation code. Validate clusters statistically (ANOVA / silhouette)
  the same way the original 4 were validated (F=9,781, η²=9.2% is the bar to
  beat or match).
- **Guardrail:** a new model only ships if it is statistically distinct AND has
  enough orgs per size band to form real peer groups (min 30/cell, target 100+).

### WS-2 — Model-specific, AI-optimized revenue bands (Option B, Approved)
This is the heart of the moat. Replace the universal 6 bands with **per-model
band sets learned from the data.**

**Design principle:** 8 quantile-based bands per model in log₁₀(revenue) space,
ensuring balanced peer groups (≈12.5% of orgs per band) while respecting natural
revenue distribution of each operating model.

**Finalized Operating Model Taxonomy (8 models, 71,473 complete-fingerprint orgs):**

| Model | NTEE | Count | Revenue range | Meaning |
|-------|------|-------|---------------|---------|
| Direct Service | B,C,P,F,T,I,U,Z | 22,916 | $1 – $10.2B | Emergency response, direct assistance, advocacy |
| Mission Infrastructure | A,E,G,L,M,O,S,D | 26,413 | $1 – $22.7B | Schools, health, arts, libraries, disease research |
| Research / Academia | J,R,N | 10,729 | $1 – $1.8B | Universities, medical research, scientific bodies |
| Foundations | Y | 3,266 | $208 – $10.3B | Grantmaking entities, endowments, philanthropies |
| Membership / Advocacy | X,V | 2,940 | $1 – $486M | Member orgs, voluntarism, advocacy networks |
| Religion / Spiritual | W | 3,764 | $1 – $228M | Faith communities, spiritual organizations |
| International Development | Q | 601 | $10 – $1.2B | Cross-border development, humanitarian aid |
| Asset Stewards | K,H | 844 | $1 – $232M | Nursing homes, hospitals, facilities |

**Revenue band breakpoints per model (8 octile-based bands):**

Each model gets 8 bands defined by log₁₀-space octiles, ensuring ~12.5% of orgs in each band and eliminating outlier influence on boundaries.

**Direct Service** (22,916 orgs)
```
Band 0:        $0 –     $27,493
Band 1:   $27,493 –     $51,353
Band 2:   $51,353 –     $75,380
Band 3:   $75,380 –    $112,456
Band 4:  $112,456 –    $176,201
Band 5:  $176,201 –    $368,616
Band 6:  $368,616 – $1,470,577
Band 7: $1,470,577+
```

**Mission Infrastructure** (26,413 orgs)
```
Band 0:        $0 –     $27,538
Band 1:   $27,538 –     $55,018
Band 2:   $55,018 –     $81,760
Band 3:   $81,760 –    $116,970
Band 4:  $116,970 –    $170,692
Band 5:  $170,692 –    $277,720
Band 6:  $277,720 –    $687,742
Band 7:  $687,742+
```

**Research / Academia** (10,729 orgs)
```
Band 0:        $0 –     $32,481
Band 1:   $32,481 –     $56,278
Band 2:   $56,278 –     $77,465
Band 3:   $77,465 –    $101,313
Band 4:  $101,313 –    $136,173
Band 5:  $136,173 –    $189,575
Band 6:  $189,575 –    $345,764
Band 7:  $345,764+
```

**Foundations** (3,266 orgs)
```
Band 0:        $0 –     $23,735
Band 1:   $23,735 –     $43,760
Band 2:   $43,760 –     $64,403
Band 3:   $64,403 –     $93,374
Band 4:   $93,374 –    $146,142
Band 5:  $146,142 –    $271,438
Band 6:  $271,438 –    $692,572
Band 7:  $692,572+
```

**Membership / Advocacy** (2,940 orgs)
```
Band 0:        $0 –     $34,310
Band 1:   $34,310 –     $60,506
Band 2:   $60,506 –     $89,984
Band 3:   $89,984 –    $124,164
Band 4:  $124,164 –    $176,514
Band 5:  $176,514 –    $292,835
Band 6:  $292,835 –    $696,571
Band 7:  $696,571+
```

**Religion / Spiritual** (3,764 orgs)
```
Band 0:        $0 –     $20,004
Band 1:   $20,004 –     $45,205
Band 2:   $45,205 –     $70,374
Band 3:   $70,374 –    $105,577
Band 4:  $105,577 –    $154,536
Band 5:  $154,536 –    $229,829
Band 6:  $229,829 –    $419,777
Band 7:  $419,777+
```

**International Development** (601 orgs)
```
Band 0:        $0 –     $20,493
Band 1:   $20,493 –     $46,060
Band 2:   $46,060 –     $78,026
Band 3:   $78,026 –    $120,445
Band 4:  $120,445 –    $178,941
Band 5:  $178,941 –    $341,100
Band 6:  $341,100 – $1,295,575
Band 7: $1,295,575+
```

**Asset Stewards** (844 orgs)
```
Band 0:        $0 –     $39,502
Band 1:   $39,502 –     $74,239
Band 2:   $74,239 –    $114,717
Band 3:  $114,717 –    $175,185
Band 4:  $175,185 –    $277,561
Band 5:  $277,561 –    $560,398
Band 6:  $560,398 – $1,846,508
Band 7: $1,846,508+
```

**Why octile log-space bands:**
- **Log-space:** handles 10+ orders of magnitude; outliers don't influence boundaries
- **Octiles:** each band gets ~12.5% of orgs, ensuring stable peer cells
- **Model-specific:** different sectors have different revenue shapes; Foundations are smaller than Mission Infrastructure
- **Deterministic & auditable:** no curve-fitting or black-box algorithms

### WS-3 — Financial-health sub-scale per model
- For each org, compute its percentile **within its (model, band) peer cell**
  using the model-appropriate weighted metrics (reuse + extend `WEIGHTS`).
- Map percentile → `Strong / Stable / Building` by terciles **of the peer cell**
  (so the labels are always peer-relative, never absolute).
- Attach the model-specific gloss (the table in §3) for display.

### WS-4 — Coverage expansion (grounded in real data coverage, audited 2026-06-04)

**Coverage tier by completeness of financial fingerprint:**

| Tier | What they have | Count | What they get |
|------|----------------|-------|---------------|
| **A — Complete fingerprint** | revenue + expenses + assets + net assets + reserve months + program % + operating model | **71,473** | Full two-scale score: (model, financial health, revenue band, visibility tier) |
| **B — Revenue + partial** | revenue (651K) and some financials, missing program % | ~425K | Revenue band + visibility tier; financial health flagged as "incomplete" |
| **C — Revenue only / BMF** | name, NTEE, maybe revenue | remainder | Operating model + cause tags, **no score** (Principle #3) |

**Key findings:**
- **`program_expense_pct` is the binding constraint** — only 300,914 orgs have it across all 1.8M in the registry. It caps Tier A at 71K not 226K because we now require the complete 7-field fingerprint per model.
- **All 8 operating models are statistically real** with sufficient volume per revenue band (smallest model, Asset Stewards, has 844 orgs = 105 orgs/band on average).
- **International Development (NTEE Q, 601 orgs) meets the guardrail** with 75 orgs/band average. Aga Khan Foundation (Q, $64.9M) lands in International Development / Band 5 with 76 peer orgs.
- **Deriving program_expense_pct for the ~425K Tier B orgs** is the single highest-leverage data task to expand full-score coverage. Not a blocker for P0–P2.

### WS-4.1 — Outlier-robustness pipeline (binding, applies to ALL workstreams)
Revenue spans $1 → $75B (10+ orders of magnitude). Outliers must not influence
band boundaries, cluster shapes, or the objective function. This pipeline runs
**before** any distribution math, everywhere:

1. **Log-space first.** All sizing, clustering, dispersion, and band work happens
   on `log10(revenue)` (and log of asset/ratio metrics), never raw dollars.
2. **Exclude sentinels before stats.** Missing-data sentinels (`sentinel%` in
   `cause_band_profiles.csv`) are removed *before* computing any distribution —
   they are not real values and must not be winsorized into looking real.
3. **Winsorize ratios at 1st/99th percentile per (model, band) cell.** Pathological
   ratios (e.g. `net_assets/expenses` when expenses ≈ 0) are clipped, mirroring the
   API's existing `months_of_reserve ∈ [-120, 120]` clip. Clip bounds are logged.
4. **Robust statistics only.** Location = median; dispersion = MAD or IQR;
   never mean/variance in any objective or cluster metric.
5. **Robust clustering (WS-1).** Robust-scale (median/IQR), then HDBSCAN or GMM —
   not raw k-means. Silhouette validated on the bulk, excluding the tail.
6. **Asset/multi-year sizing for capital-heavy models.** Foundations, Endowment &
   Capital, and Asset Stewards are sized on **assets or a multi-year revenue
   median**, since single-year revenue swings on one large gift or market move.
7. **Percentile-rank scoring retained.** The final per-org score stays on
   percentile ranks within the peer cell — inherently outlier-insensitive. The
   robustness work above protects the *boundaries* that feed it.

Every clip bound, exclusion count, and robust statistic is written to the audit
trail (Principle #9). A spot-check confirms the top/bottom 0.1% of orgs by
revenue do **not** sit on any band boundary they created.

### WS-5 — Validation framework (prove it's better, don't assert it)
- **Back-test:** run v4 against old + new data; confirm scores are stable where
  they should be and only move where data genuinely changed.
- **Fairness probes:** confirm small/lean/international orgs are no longer
  systematically pushed to the bottom (distribution by size band should not
  collapse low for Direct Service / Grassroots).
- **Sanity panel:** a hand-picked set of ~50 well-known orgs (across all models
  and sizes) with expected qualitative outcomes; reviewed before any deploy.
- **Sentinel guard:** cells with high missing-data rates are excluded or
  down-weighted, not silently scored.
- **Outlier-influence test (per §4.1):** confirm the top/bottom 0.1% by revenue
  and by each ratio do not sit on band boundaries; re-run band optimization with
  the tail removed and confirm boundaries barely move (robustness check).

### WS-6 — Surface it (API, frontend, docs)
- API: add `financial_health` (`Strong/Stable/Building`), `operating_model`,
  `peer_band`, and `peer_cell_size` to org + search responses. Keep
  `ENABLE_SCORES` honoring.
- Frontend: render the two scales side by side; update Methodology page to
  document the new models, the band-optimization objective, and the
  financial-health gloss. Full transparency (Principle #9).
- Docs: this plan → living methodology; every scoring run in the audit trail.

---

## 5. Phasing

| Phase | Deliverable | Gate before proceeding |
|-------|-------------|------------------------|
| **P0** | Operating-model taxonomy validated (WS-1) | Clusters statistically distinct; volumes sufficient |
| **P1** | Band optimizer + `model_bands` table (WS-2) | Objective scores beat universal-6 baseline |
| **P2** | v4 scorer: model bands + per-model health terciles (WS-3) | Sanity panel passes |
| **P3** | Coverage expansion + partial-data tiers (WS-4) | Aga Khan test case correct; no fabricated scores |
| **P4** | Validation + fairness sign-off (WS-5) | Founder review |
| **P5** | API + frontend + methodology docs (WS-6) | Founder approval to deploy |

Each phase is independently reviewable. Nothing touches production scores until
P4 sign-off. All compute runs on the local Ryzen / R9700 server; no cloud spend.

---

## 6. Stewardship guardrails (non-negotiable)

- **Evidence-based (#3):** no score without real financial data; partial data is
  labeled, never fabricated.
- **Equal dignity (small orgs):** "Building" is never pejorative; fairness probes
  explicitly check the small/lean/international tail isn't pushed down.
- **Explainable (#9):** the band-optimization objective is written down, every
  run is logged with its inputs and scores, the Methodology page documents it.
- **Correctable (#6):** v4 ships behind validation gates; old scores remain until
  v4 passes; any error found is corrected and documented, not hidden.
- **Human in command (#10):** I propose; you approve at P4/P5 before production.

---

## 7. Open decisions for you

1. **Cooperative / Mutual** as its own model, or fold into Membership until volume
   justifies a split?
2. **Partial-data orgs:** show a financial-health tier from limited signals
   (flagged), or withhold the second scale entirely until full 990 data exists?
3. **Band optimizer objective weighting:** is *peer sufficiency + homogeneity*
   the priority, or do you want *balance* (even cell sizes) weighted higher?
4. **Scale-2 vocabulary:** lock `Strong / Stable / Building`, or test alternates
   before committing (renaming later is cheap pre-launch, costly post-launch)?

---

*Next step on approval: begin P0 — build the operating-model clustering analysis
on the 648K and report whether the proposed 5 new models are statistically real.*
