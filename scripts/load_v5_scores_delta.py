#!/usr/bin/env python3
"""
Load v5.0 scores from JSON into registry_enriched — DELTA MODE.

Only updates orgs whose merit_score_v5 is currently NULL. Already-scored
orgs are untouched (the Saturday full refresh handles staleness).

Usage:
    python3 scripts/load_v5_scores_delta.py <scores.json>
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

scores = data if isinstance(data, list) else data.get('scores', [])
log(f"Scorer output contains {len(scores):,} scores")

conn = sqlite3.connect(db_path)
c = conn.cursor()

# One pass: collect all currently-unscored EINs into a set (fast membership test)
unscored_eins = {
    row[0] for row in c.execute(
        "SELECT EIN FROM registry_enriched WHERE deductibility = '1' AND merit_score_v5 IS NULL"
    )
}
log(f"Unscored orgs in database: {len(unscored_eins):,}")

updates = []
for s in scores:
    ein = s.get('ein')
    if not ein or ein not in unscored_eins:
        continue
    updates.append((
        s.get('reserves_percentile'),
        s.get('archetype'),
        s.get('band'),
        s.get('health_signal'),
        ein,
    ))

log(f"New scores to load: {len(updates):,} (skipping {len(scores) - len(updates):,} already-scored)")

c.executemany("""
    UPDATE registry_enriched
    SET merit_score_v5 = ?,
        merit_archetype_v5_label = ?,
        merit_band_v5_label = ?,
        merit_health_signal_v5 = ?
    WHERE EIN = ? AND merit_score_v5 IS NULL
""", updates)

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
    run_ts,
    datetime.now(timezone.utc).isoformat(),
    len(unscored_eins),
    len(scores),
    len(updates),
    f'Delta load: {len(updates)} newly-scored orgs (already-scored untouched)',
))

conn.commit()
conn.close()

log(f"Loaded {len(updates):,} new v5.0 scores (delta run {run_ts})")
