#!/usr/bin/env python3
"""
Load v5.0 scores from JSON into registry_enriched table.
Run after merit_scorer_v5_0.py completes.

Usage:
    python3 scripts/load_v5_scores.py scores_v5_0.json
"""
import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

if len(sys.argv) < 2:
    print("Usage: python3 load_v5_scores.py <scores.json>")
    sys.exit(1)

scores_file = Path(sys.argv[1])
db_path = Path.home() / "meritgiving/data/merit_registry.db"

if not scores_file.exists():
    print(f"Error: {scores_file} not found")
    sys.exit(1)

print(f"[*] Loading v5.0 scores from {scores_file}")
with open(scores_file) as f:
    data = json.load(f)

# Handle both direct list and wrapped format
scores = data if isinstance(data, list) else data.get('scores', [])
print(f"[*] Loaded {len(scores)} v5.0 scores")

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Update each org with its v5 score
loaded = 0
for score_data in scores:
    ein = score_data.get('ein')
    if not ein:
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
        WHERE EIN = ?
    """, (
        merit_score_v5,
        archetype_label,
        band_label,
        health_signal,
        ein
    ))
    loaded += 1
    if loaded % 50000 == 0:
        print(f"  [{loaded}/{len(scores)}] ...")

# Record this scoring run
run_ts = datetime.now(timezone.utc).isoformat()
total_scored = data.get('total_scored', len(scores)) if isinstance(data, dict) else len(scores)

c.execute("""
    INSERT INTO scoring_runs (
        run_id, scorer_version, started_at, completed_at,
        input_ein_count, scorable_count, output_ein_count,
        notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    f'v5_0_full_{run_ts}',
    'v5.0',
    datetime.now(timezone.utc).isoformat(),
    datetime.now(timezone.utc).isoformat(),
    1871724,  # canonical deductible count
    total_scored,
    loaded,
    f'Full v5.0 recomputation: {total_scored} scored, 3 archetypes (Donation/Fee/Endowment), 3 bands'
))

conn.commit()
conn.close()

print(f"[✓] Updated {loaded} organizations with v5.0 scores")
print(f"[✓] Scores last updated: {run_ts}")
print(f"[→] Restart API to load new scores: systemctl restart daanaa")
