# score-orgs — Run the Daanaa Financial Context Scorer (v5)

Scores active 501(c)(3) organizations in `data/merit_registry.db` and writes
the v5 financial context columns back to `registry_enriched`:
`merit_score_v5`, `merit_archetype_v5_label`, `merit_band_v5_label`,
`merit_health_signal_v5`, `merit_peer_group_v5`, `merit_peer_count_v5`.

**Why this exists (the vision):** Daanaa is giving infrastructure. Financial
context is one of the trust rails that lets a donor act in seconds — see the
work, see honest context, give directly. Scoring exists to *enable* giving,
never to gatekeep it.

**Language rule (governance/LANGUAGE_AND_MINDSET.md):** these are peer
*context* signals, never grades. HEALTHY / STABLE / NEED_SUPPORT is the only
health vocabulary. The v4 lamp tiers still exist in the database for the
nonprofit-facing claim flow, but were retired from donor-facing profiles on
2026-07-17 — never reintroduce them on donor-facing surfaces.

---

## When to use this skill

- After refreshing IRS/ProPublica financial data (total_revenue,
  months_of_reserve, program_expense_pct)
- When the v5 scoring methodology itself changes
- Normally you do NOT need to run this manually: `overnight_pipeline.py`
  runs the full v5 scorer + loader every night at 02:30.

## How scoring works (v5)

Each org is placed in a peer cell = funding archetype × revenue band:

- **Archetypes:** Donation-Funded, Fee-for-Service, Endowment-Funded
- **Bands:** Micro (<$150K), Professional ($150K–$700K), Established (>$700K)

`merit_score_v5` is the org's percentile *within its cell only* — a $200K
community org is never compared against a hospital system (STEWARDSHIP P4,
enforced structurally). Orgs missing any of the three financial inputs are
never scored (P3: evidence-based signals only); unscored orgs get cause-cohort
context at serve time instead of a blank panel.

## Run it

```bash
source ~/meritgiving/venv/bin/activate
python3 scripts/merit_scorer_v5_0.py --output /tmp/scores_v5.json
python3 scripts/load_v5_scores.py /tmp/scores_v5.json
```

Delta-only variant (only orgs with `merit_score_v5 IS NULL`, e.g. after a
Monday IRS load): `python3 scripts/delta_scorer_v5_nightly.py` — removed from
cron 2026-07-17 because the nightly pipeline full-score made it redundant,
but still valid for manual catch-up runs.

## Verify

```bash
sqlite3 data/merit_registry.db "
  SELECT merit_health_signal_v5, COUNT(*) FROM registry_enriched
  WHERE merit_score_v5 IS NOT NULL GROUP BY 1;"
sqlite3 data/merit_registry.db "
  SELECT COUNT(*) FROM registry_enriched
  WHERE deductibility='1' AND merit_score_v5 IS NOT NULL;"
```

Expect 420K+ scored (bounded by financial-data availability, not run
completeness). Every run is recorded in `scoring_runs`; snapshots in
`score_snapshots` (P9 traceability).

## Gotchas

- **Legacy scorers are archived — never run them.** Earlier versions of this
  skill pointed at `merit_scorer_db.py`; that scorer (and v2/v3/tier
  variants) lives in `archive/legacy_scorers_20260609/` and must not be run.
  `scripts/merit_scorer_v5_0.py` is the only canonical scorer.
- v5 assigns only 3 archetypes by NTEE mapping; re-scoring will not expand
  coverage for orgs missing financial inputs — that requires data backfill
  (`scripts/data_audit_fix.py` derives reserves + expense ratios from primary
  990 fields).
- Concurrent writers (discovery daemon) hold the WAL — loaders need
  `PRAGMA busy_timeout` (already set in load scripts).
