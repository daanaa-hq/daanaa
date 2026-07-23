# Scoring Model Research: Small Nonprofits with Limited Data

**Date:** 2026-07-23  
**Status:** Framework ready for agent team analysis

## Objective

Determine which scoring model best represents small nonprofits (revenue < $500K) when financial data is sparse or incomplete.

## The Challenge

Small nonprofits often lack complete financial data because:
- Not all file Form 990 (some file simplified 990-N)
- NCCS/ProPublica data may have gaps for smallest organizations
- Score accuracy depends on finding comparable peer organizations

When peer groups are too small (<5 orgs), a fallback strategy is needed:
- Expand geographic scope (e.g., state-wide instead of county)
- Broaden category (e.g., all health nonprofits instead of specific type)
- Result: score quality decreases as peer groups become too broad

## Three Models Evaluated

### Model 1: v3 — NTEE1 × Revenue Bands
- **Formula:** 26 NTEE1 codes × 7 revenue bands = ~182 peer cells
- **Peer definition:** "All nonprofits with same NTEE major code and revenue band"
- **Strength:** Simple, stable peer groups
- **Weakness:** NTEE1 is very broad (e.g., all "health" nonprofits together)
- **For small orgs:** Large peer groups (avg 8,303) but coarse categorization

### Model 2: v4 — Operating Models × Revenue Bands
- **Formula:** 9 operating models × 8 revenue bands = ~72 peer cells
- **Peer definition:** "All nonprofits with same financial operating model and revenue band"
- **Strength:** Models group by financial behavior (grant-funded, fee-for-service, etc.), not topic
- **Weakness:** Abstract model layer loses category specificity
- **For small orgs:** Largest peer groups (avg 11,894) but most abstract

### Model 3: agent2 — NTEE × STATE × Revenue Bands (with Fallback)
- **Formula:** Full NTEE × state × 5 revenue bands with cascade fallback
- **Peer definition:** 
  - **Primary:** "All nonprofits with same full NTEE code, state, and revenue band"
  - **Fallback 1:** "All nonprofits with same NTEE and state" (drop revenue band)
  - **Fallback 2:** "All nonprofits with same NTEE" (drop state)
- **Strength:** Specific categories, geographic context, graceful degradation
- **Weakness:** Complex fallback logic requires careful implementation
- **For small orgs:** Moderate peer groups (avg 107), 1% fallback activation, best specificity

## Research Framework

### Run the Analysis

```bash
cd ~/meritgiving
source venv/bin/activate
python3 scripts/research_scoring_models_small_orgs.py --threshold 500000
```

Output: `logs/scoring_model_research.json`

### Metrics Measured

For each model, the script calculates:

| Metric | Meaning |
|--------|---------|
| `coverage_pct` | % of small orgs falling into peer groups with ≥5 orgs |
| `avg_cohort_size` | Average peer group size |
| `median_cohort_size` | Median peer group size (more robust to outliers) |
| `min_cohort_size` | Smallest peer group |
| `max_cohort_size` | Largest peer group |
| `fallback_rate_pct` | % of orgs requiring fallback peer group (agent2 only) |

### Interpreting Results

**High coverage + moderate cohort size** = Good (specific yet stable peers)
**Low coverage + huge cohort size** = Bad (can't score small orgs)
**High fallback rate** = Risk (scores depend on degraded peer groups)

## Agent Team Research Tasks

After running the baseline, investigate these questions:

### 1. Peer Group Quality by Revenue Band
- Which revenue bands have stable peer groups?
- Which bands collapse when filtering by state/NTEE?
- Do smaller revenue bands need different minimum cohort thresholds?

**Code pointer:** Modify the script to add a `--analyze-bands` flag that breaks down results by revenue band.

### 2. Geographic Variation (for agent2)
- How many states have ≥5 orgs in each NTEE category?
- Which states have the most/least data?
- Are fallback rates higher in rural states?

**Code pointer:** Add state-by-state coverage analysis to agent2 function.

### 3. NCCS Data Gap Coverage
- How many small orgs now have net_assets/liabilities data from NCCS?
- Did NCCS help most in specific NTEE categories?
- Are there NTEE/state combinations still without financial data?

**Code pointer:** Add a query to count orgs with NCCS data, cross-tabulate by NTEE and state.

### 4. Score Stability Testing
- If an org moves from primary → fallback peer group, how much does the score change?
- Which metrics are most sensitive to peer group changes?
- Is there a "score volatility" threshold we should monitor?

**Code pointer:** Compute scores under primary and fallback peer groups, measure deltas.

### 5. Hybrid Approach
- Could we use agent2 (NTEE×STATE×band) for large orgs but fall back to v4 (operating model×band) for very small orgs?
- Does this reduce volatility while maintaining specificity?

**Code pointer:** Implement a threshold (e.g., "use agent2 if primary cohort ≥20, else use v4").

## Next Steps for Foundation

1. **Run baseline** (`research_scoring_models_small_orgs.py`)
2. **Agent team investigates** the 5 research questions above
3. **Validate on real data:** Score a small-org sample under each model, compare results to known outcomes
4. **Implement chosen model** in `merit_scorer_v6_0.py`
5. **Deploy with monitoring:** Track fallback activation rates, flag high-volatility scores

## Key Decision Point

**When peer groups are too small (<5), do we:**
- **A) Refuse to score** (no score if peer group too small)
- **B) Degrade gracefully** (fallback to broader category, flag as "lower confidence")
- **C) Hybrid** (different thresholds by NTEE/revenue combination)

agent2's approach is **(B)** with documented fallback path. This is good for coverage but requires score confidence signaling to users.

## References

- Previous models: `/home/akbar/meritgiving/archive/legacy_scorers_20260609/`
- Current v4 scorer: `scripts/merit_scorer_v4_0.py`
- NCCS data: `docs/NCCS_DATA_INGESTION_STRATEGY.md` (566K+ orgs with financial data now available)
- Stewardship Principle 3: "Trust signals must be evidence-based" → ensure fallback peer groups are sufficiently large and documented

---

**Contact:** Send findings to this issue/channel with agent2 analysis results and recommendation.
