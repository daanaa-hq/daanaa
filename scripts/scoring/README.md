# Scoring — Financial Context System

## Canonical Files

- **`daanaa_scorer.py`** — v6 tiered peer financial context (active, runs nightly). Writes v6 tier, peer-group, confidence, and percentile fields.
- **`compute_composite_score.py`** — Supporting utilities for peer group ranking.

## Scoring Versions (Historical Archive)

| Version | Status | Location | Use Case |
|---------|--------|----------|----------|
| v6 | **ACTIVE** | `daanaa_scorer.py` | Tiered peer context (NTEE2 × revenue band × region) |
| v5 | Archived | `../archive/scorers/v4_v5/merit_scorer_v5_0.py` | Do not use (superseded) |
| v4 | Archived | `../archive/scorers/v4_v5/merit_scorer_v4_0.py` | Do not use (superseded) |

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
4. Run the applicable focused validation before committing. A consolidated
   `scripts/testing/scoring_validation.py` helper is planned, not yet built.
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
- `scoring_tier` / `tier_label` — v6 peer-context tier assignment
- `peer_group_size` / `peer_group_description` — Size and description of the assigned peer group
- `confidence` — Confidence based on peer-group coverage
- `merit_percentile_v6` / `merit_percentile_confidence_v6` — v6 percentile and its confidence
- `merit_peer_count_v6_scoreable` — Count of scoreable peers

## Testing

```bash
# Focused legacy score validations (run the one matching the data under review)
python3 scripts/testing/validate_v4_scores.py
python3 scripts/testing/validate_v5_scores.py

# Spot-check a few orgs
python3 -c "
import sqlite3
conn = sqlite3.connect('data/merit_registry.db')
orgs = conn.execute(
    'SELECT EIN, org_name, merit_percentile_v6, scoring_tier FROM registry_enriched WHERE merit_percentile_v6 IS NOT NULL LIMIT 5'
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

- `docs/METHODOLOGY_V6_INFERENCE.md` — v6 context methodology notes
- `docs/research/DAANAA_V6_SCORING_RESEARCH_PAPER_v0.1.md` — v6 scoring research
- `STEWARDSHIP.md` — Principles governing scoring
