# Scoring v4.0 — Complete System Summary

**Status:** Ready for P0 validation and implementation planning

**Date:** 2026-06-04

---

## What We Built

A **model-aware, data-driven peer-context scoring system** that measures every nonprofit against its true peers—not a universal yardstick.

### The Two-Scale System

**Scale 1 — Visibility (5 tiers, unchanged)**
- Blazing, Burning Bright, Steady Flame, Growing, Just Starting
- Public prominence / discoverability signal
- Already in database, no changes

**Scale 2 — Financial Health (3 tiers, peer-relative, model-specific meanings)**
- Strong, Stable, Inspiring
- Position within peer cell (same operating model + revenue band)
- Meaning changes by model (e.g., "Strong" for Foundations ≠ "Strong" for Grassroots)

### Operating Model Taxonomy (8 Models, 71,473 orgs)

| Model | NTEE | Count | Examples |
|-------|------|-------|----------|
| Direct Service | B,C,P,F,T,I,U,Z | 22,916 | Food banks, job training, animal rescue, emergency response |
| Mission Infrastructure | A,E,G,L,M,O,S,D | 26,413 | Schools, hospitals, arts centers, libraries, disease research |
| Research / Academia | J,R,N | 10,729 | Universities, medical research institutions |
| Foundations | Y | 3,266 | Grantmaking entities, endowments |
| Membership / Advocacy | X,V | 2,940 | Member orgs, advocacy networks, voluntarism |
| Religion / Spiritual | W | 3,764 | Faith communities, spiritual organizations |
| International Development | Q | 601 | Cross-border relief, humanitarian aid |
| Asset Stewards | K,H | 844 | Nursing homes, hospitals (facility stewardship) |

### Revenue Bands (8 per model, octile-based in log₁₀ space)

Each model has 8 bands defined by log-space quantiles, ensuring:
- ~12.5% of orgs per band (balanced peer cells)
- Outliers don't influence boundaries
- Natural breakpoints respect sector-specific revenue distributions

Example: Direct Service bands are $0–$27.5K, $27.5K–$51.4K, ... $1.47M+

---

## Key Decisions

| Decision | Approach | Why |
|----------|----------|-----|
| Models | 8 data-driven clusters (not proposed 9) | Grassroots/Cooperative too thin; absorbed into Direct Service |
| Revenue bands | 8 octile-based (not universal 6) | Sector-specific; Direct Service median ≠ Foundations median |
| Band definition | Log₁₀ quantiles (not gap/KDE) | Immune to outliers; deterministic; auditable |
| Financial health | Peer-relative terciles (not absolute) | Fairness: never punishes small orgs for being small |
| Vocabulary | Strong / Stable / Inspiring (not Building) | "Inspiring" honors underdog work; no consolation-prize feeling |

---

## Coverage Tiers

| Tier | Criteria | Count | Outputs |
|------|----------|-------|---------|
| A | Complete: revenue + expenses + assets + net_assets + reserves + program% | 71,473 | operating_model, revenue_band, peer_cell, financial_health, visibility_tier |
| B | Partial: revenue + some financials, no program% | ~425K | revenue_band, visibility_tier, financial_health_limited |
| C | Minimal: just name + NTEE | remainder | operating_model, cause_tags (no score) |

---

## Implementation Roadmap

### P0 — Operating-model validation (COMPLETE)
- ✅ Clustered 71K complete-fingerprint orgs into 8 models
- ✅ Validated all models meet peer-sufficiency guardrail (min 75 orgs/band)
- ✅ Confirmed Aga Khan (thin model test case) lands in real peer cell

### P1 — v4 Scorer + model_bands table
- Build scorer reading (model, band) assignment from org
- Compute percentile rank within (model, band) peer cell
- Map percentile to tercile → financial_health tier
- Validate against sanity panel (~50 hand-picked orgs)

### P2 — Validation + fairness probes
- Back-test: compare v4 scores vs. v3.3 on overlapping orgs
- Fairness: confirm small/lean/international orgs not pushed down
- Spot-check: top/bottom 0.1% by revenue don't sit on band boundaries

### P3 — Coverage expansion
- Extend to Tier B orgs (derive program_expense_pct where possible)
- Label partial scores with confidence flags

### P4 — API + Frontend + Docs
- Add financial_health, operating_model, peer_cell_size to API responses
- Render two-scale UI side-by-side
- Update Methodology page

### P5 — Deploy (with founder sign-off)

---

## Values Alignment Checklist

- ✅ Evidence-based: no score without real financial data
- ✅ Equal dignity: Small org "Inspiring" tier is not a consolation prize
- ✅ Explainable: band boundaries logged, vocab matched to model meanings
- ✅ Correctable: v4 ships behind validation gates; old scores remain until ready
- ✅ Human in command: all phase gates require founder review

---

## Next Steps

1. **Present findings to user** — operating models, revenue bands, financial health vocabulary approval
2. **On approval, begin P1** — build v4.0 scorer implementation
3. **Document all decisions** in DECISIONS.md and LESSONS.md

---

*This plan replaces the proposal in SCORING-V4-PLAN.md with real data-driven results.*
