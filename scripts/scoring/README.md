# Scoring — Financial Context System

## Canonical Files

- **`daanaa_scorer.py`** — v6 tiered peer financial context (ACTIVE, runs nightly). Computes merit_score_v6, merit_tier, merit_band_v5_label, merit_health_signal_v5.
- **`score_snapshots.py`** — Version tracking + historical snapshots (for rollback, auditing, A/B testing).
- **`compute_composite_score.py`** — Supporting utilities for peer group ranking.

## Scoring Versions (Historical Archive)

| Version | Status | Location | Use Case |
|---------|--------|----------|----------|
| v6 | **ACTIVE** | `daanaa_scorer.py` | Tiered peer context (NTEE2 × revenue band × region) |
| v5 | Archived | `archive/merit_scorer_v5_0.py` | Do not use (superseded) |
| v4 | Archived | `archive/merit_scorer_v4_0.py` | Do not use (superseded) |

## How To...

**Run nightly scoring:**
```bash
# Runs automatically via overnight_pipeline.py at 2am
# Manual run (for testing or one-off recompute):
python3 scripts/scoring/daanaa_scorer.py
```

**Update scoring logic:**
1. Edit `daanaa_scorer.py` (change peer groups, thresholds, etc.)
2. Test locally with subset of data
3. Run full score via nightly pipeline
4. Verify via `scripts/testing/scoring_validation.py`
5. Commit with DECISIONS.md entry explaining why

**Rollback to previous scoring:**
```bash
# Scoring is versioned in DB; check score_snapshots table
SELECT * FROM score_snapshots ORDER BY created DESC LIMIT 5;
# Restore old scores if needed (talk to Akbar first)
```

## Database Schema

**Input:** `registry_enriched` (org data: EIN, revenue, NTEE, region, etc.)
**Output:** `registry_enriched` columns updated:
- `merit_score_v6` — 0-100 financial health percentile
- `merit_tier` / `merit_band_v5_label` — Peer group tier assignment
- `merit_health_signal_v5` — HEALTHY / STABLE / NEED_SUPPORT
- `merit_peer_count_v5` — Size of peer cell

## Testing

```bash
# Validate scoring logic (checks peer group assignments, thresholds, etc.)
python3 scripts/testing/scoring_validation.py

# Spot-check a few orgs
python3 -c "
import sqlite3
conn = sqlite3.connect('data/merit_registry.db')
orgs = conn.execute(
    'SELECT EIN, org_name, merit_score_v6, merit_tier FROM registry_enriched WHERE merit_score_v6 > 0 LIMIT 5'
).fetchall()
for ein, name, score, tier in orgs:
    print(f'{ein} | {name[:40]:40} | {score:5.1f} | {tier}')
"
```

## Governance

**Stewardship Principle #3** (Trust signals evidence-based): Scores are deterministic from public IRS data only. No human curation per org. No paid placement can affect scores.

**Stewardship Principle #4** (Small orgs fairness): v6 scores are benchmarked within NTEE peer groups, NOT against the entire registry.

## Do Not Use

- `merit_scorer_v4_0.py`, `merit_scorer_v5_0.py` (archived, use v6 only)
- Hand-curated score overrides (never exists in codebase)
- Cloud APIs for scoring (use local peer group math only)

## Recent Changes

- 2026-08-12: Task #2 expansion added cause synonym expansion to search (improves org discovery for peer groups)
- 2026-07-25: v6 scored 1.94M orgs, live in DB
- 2026-07-26: Peer group methodology documented in `docs/RESEARCH.md`

## See Also

- `docs/METHODOLOGY.md` — v6 context system design
- `docs/PEER_GROUPS.md` — NTEE2 × revenue band × region breakdown
- `STEWARDSHIP.md` — Principles governing scoring
