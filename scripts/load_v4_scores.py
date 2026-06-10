#!/usr/bin/env python3
"""
Load v4.0 scores from JSON into registry_enriched table.
Run after merit_scorer_v4_0.py completes.

Usage:
    python3 scripts/load_v4_scores.py scores_v4_0_full.json
"""
import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

if len(sys.argv) < 2:
    print("Usage: python3 load_v4_scores.py <scores.json>")
    sys.exit(1)

scores_file = Path(sys.argv[1])
db_path = Path.home() / "meritgiving/data/merit_registry.db"

if not scores_file.exists():
    print(f"Error: {scores_file} not found")
    sys.exit(1)

print(f"[*] Loading scores from {scores_file}")
with open(scores_file) as f:
    data = json.load(f)

scores = data if isinstance(data, dict) else data.get('scores', {})
print(f"[*] Loaded {len(scores)} scores")

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Update each org with its score
loaded = 0
for ein, score_data in scores.items():
    merit_score = score_data.get('merit_score')
    financial_health = score_data.get('financial_health')  # Strong/Stable/Inspiring

    c.execute("""
        UPDATE registry_enriched
        SET merit_score = ?,
            financial_health = ?
        WHERE EIN = ?
    """, (
        merit_score,
        financial_health,
        ein
    ))
    loaded += 1
    if loaded % 10000 == 0:
        print(f"  [{loaded}/{len(scores)}] ...")

# Record this scoring run
run_ts = datetime.now(timezone.utc).isoformat()
c.execute("""
    INSERT INTO scoring_runs (
        run_id, scorer_version, started_at, completed_at,
        input_ein_count, scorable_count, output_ein_count,
        notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    f'v4_0_full_{run_ts}',
    'v4.0',
    '2026-06-04T09:31:28Z',
    '2026-06-04T09:36:51Z',
    1811930,
    71473,
    len(scores),
    'Full v4.0 recomputation: 71,473 complete-fingerprint orgs'
))

conn.commit()
conn.close()

print(f"[✓] Updated {loaded} organizations")
print(f"[✓] Scores last updated: {run_ts}")
print(f"[→] Restart API to load new scores: systemctl restart daanaa")
