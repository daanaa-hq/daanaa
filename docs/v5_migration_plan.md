# v5 Full Migration Plan

**Goal:** Make v5 the current financial-context system everywhere it is surfaced, keep lamp tiers (visibility), and never add live scoring work to the search path.

**Decisions locked (2026-06-14):**
- **No re-score.** Dry-run finding: the NTEE→archetype mapping only ever assigns 3 archetypes (donation_funded, endowment, fee_for_service); Membership & Mutual-Benefit are defined but never assigned. Coverage (~411K) is bounded by financial-data availability (61% of orgs fail metric extraction). A re-score would not repair coverage or add archetypes — the live 3-archetype / 411K state IS the stable v5 output. So the migration is frontend + snapshot only, off the v5 columns already in the DB.
- **Keep lamp tiers** (Beacon/Torch/Candle/Spark) as the visibility layer; v5 drives financial context only. Lamp tiers are brand-critical ("raise your flame") and computed separately from the financial score.
- **Search must not slow down.** v5 data stays in DB columns + baked into static precompute org JSON (already the case). FTS5 + RAM embeddings stay untouched. No live scoring joins on the search path.

**Revised: this is now a single surgical phase (research page → v5), no engine/pipeline/re-score work.**

## Current state (facts)
- v5 already in `registry_enriched`: `merit_score_v5`, `merit_archetype_v5(_label)`, `merit_band_v5(_label)`, `merit_health_signal_v5`, `merit_peer_group_v5`, `merit_peer_count_v5`.
- v5 coverage 411,531 vs v4 474,454; only 3/5 archetypes populated.
- Production scorer is still v4 (`overnight_pipeline.py` runs `merit_scorer_v4_0`); research summaries built from `v4_scores`; org pages already show v5 via `V5Context` (baked into precompute).
- Lamp tier `merit_tier` covers 1.66M (visibility, data-completeness based — keep).

## Phases (surgical, each independently shippable)

### Phase 1 — Research page documents v5 (frontend + snapshot; NO engine/search impact)
- `export_research_snapshot.py`: emit v5 aggregates (archetype × band counts, health-signal distribution, percentile context) computed directly from the v5 columns already in the DB. Keep `entity_types` and lamp-tier sections.
- Rewrite research sections to v5: Methodology (5 archetypes × 3 bands, percentile within archetype+band, health signals; lamp tiers described as the separate visibility layer), Operating Models → **Financial Archetypes**, Peer Context, Spending (archetype-based).
- Reversible, no scoring change, no search change. Ship after approval.

### Phase 2 — Fresh v5 re-score (local GPU; scoring data change → tests-first)
- Dry-run `merit_scorer_v5_0.py`, validate distributions, then full run. Repairs coverage + all 5 archetypes.
- Add/refresh a scoring test (validate v5 peer-cell integrity) before the run.
- Re-bake precompute org JSON (v5_context) + regenerate research snapshot. Approval before deploy.

### Phase 3 — Pipeline: keep v5 fresh (scoring change → tests-first)
- `overnight_pipeline.py` runs v5 alongside the lamp-tier computation. Decide whether v4 stays only as the lamp-tier source or is retired once lamp tiers are sourced independently.
- Update `research_summary_generator.py` to v5 (or fold its job into the snapshot generator).

### Phase 4 — Cleanup / docs
- Update CLAUDE.md ("current scorer" → v5 for financial context; lamp tier source noted), DECISIONS.md, LESSONS.md.

## Search-safety invariant (must hold every phase)
Search = FTS5 (`org_fts`) + RAM embeddings. v5 lives in precompute static files. No phase adds a scoring join, sort, or filter to `/api/search` or `/api/organizations`. Verify after each deploy that search latency is unchanged.
