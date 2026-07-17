#!/usr/bin/env python3
"""
Load v5.0 scores from JSON into registry_enriched table — DELTA MODE ONLY.

Delta mode: Only update orgs that have merit_score_v5 IS NULL.
Use after scoring new orgs added since last full refresh.

Usage:
    python3 scripts/load_v5_scores_delta.py scores_v5_0.json
"""
import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

if len(sys.argv) < 2:
    print("Usage: python3 load_v5_scores_delta.py <scores.json>")
    sys.exit(1)

scores_file = Path(sys.argv[1])
db_path = Path.home() / "meritgiving/data/merit_registry.db"
log_path = Path.home() / "meritgiving/logs/delta_scorer_nightly.log"

if not scores_file.exists():
    print(f"Error: {scores_file} not found")
    sys.exit(1)

def log(msg: str) -> None:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a') as fh:
        fh.write(line + '\n')

log(f"Loading v5.0 scores from {scores_file} (delta mode)")
with open(scores_file) as f:
    data = json.load(f)

# Handle both direct list and wrapped format
scores = data if isinstance(data, list) else data.get('scores', [])
log(f"Loaded {len(scores)} v5.0 scores total")

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get count of unscored orgs
c.execute("SELECT COUNT(*) FROM registry_enriched WHERE deductibility = '1' AND merit_score_v5 IS NULL")
unscored_count = c.fetchone()[0]
log(f"Unscored orgs in database: {unscored_count:,}")

# Update only unscored orgs
loaded = 0
skipped = 0
for score_data in scores:
    ein = score_data.get('ein')
    if not ein:
        skipped += 1
        continue

    # Check if this org is currently unscored
    c.execute("SELECT merit_score_v5 FROM registry_enriched WHERE EIN = ?", (ein,))
    result = c.fetchone()
    if result and result[0] is not None:
        # Already scored, skip
        skipped += 1
        continue

    merit_score_v5 = score_data.get('reserves_percentile')
    archetype_label = score_data.get('archetype')
    band_label = score_data.get('band')
    health_signal = score_data.get('health_signal')

    c.execute("""
        UPDATE registry_enriched
        SET merit_score_v5 = ?,
            merit_archetype_v5_label = ?,
            merit_band_v5_label = ?,
            merit_health_signal_v5 = ?
        WHERE EIN = ? AND merit_score_v5 IS NULL
    """, (
        merit_score_v5,
        archetype_label,
        band_label,
        health_signal,
        ein
    ))
    loaded += 1
    if loaded % 10000 == 0:
        log(f"  [{loaded}/{unscored_count}] ...")

# Record this scoring run
run_ts = datetime.now(timezone.utc).isoformat()

c.execute("""
    INSERT INTO scoring_runs (
        run_id, scorer_version, started_at, completed_at,
        input_ein_count, scorable_count, output_ein_count,
        notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    f'v5_0_delta_{run_ts}',
    'v5.0-delta',
    datetime.now(timezone.utc).isoformat(),
    datetime.now(timezone.utc).isoformat(),
    unscored_count,
    len(scores),
    loaded,
    f'Delta scoring: {loaded}/{unscored_count} unscored orgs updated (skipped {skipped} already-scored)'
))

conn.commit()
conn.close()

log(f"✅ Updated {loaded:,} new organizations with v5.0 scores")
log(f"✅ Skipped {skipped:,} already-scored orgs")
log(f"✅ Scores last updated: {run_ts}")
