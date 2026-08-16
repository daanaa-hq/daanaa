#!/usr/bin/env python3
"""Load v4.0 scores into v4_scores table."""

import json
import sqlite3
from pathlib import Path

DB = Path.home() / "meritgiving/data/merit_registry.db"
SCORES_FILE = Path("/tmp/scores_v4_0.json")

def load_scores_to_db(scores_file: str):
    """Load v4.0 scores into v4_scores table."""
    print(f"Loading {scores_file}...")

    with open(scores_file) as f:
        scores = json.load(f)

    print(f"Loaded {len(scores)} scores")

    conn = sqlite3.connect(str(DB))

    # Create v4 scores table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS v4_scores (
            EIN TEXT PRIMARY KEY,
            merit_score REAL,
            visibility_tier TEXT,
            financial_health TEXT,
            operating_model TEXT,
            revenue_band INTEGER,
            peer_cell_size INTEGER,
            metrics_json TEXT,
            percentiles_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Load scores
    print("Loading scores into v4_scores table...")
    inserted = 0

    for ein, score in scores.items():
        try:
            conn.execute("""
                INSERT OR REPLACE INTO v4_scores
                (EIN, merit_score, visibility_tier, financial_health,
                 operating_model, revenue_band, peer_cell_size, metrics_json, percentiles_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ein,
                score.get('merit_score'),
                score.get('visibility_tier'),
                score.get('financial_health'),
                score.get('operating_model'),
                score.get('revenue_band'),
                score.get('peer_cell_size'),
                json.dumps(score.get('metrics', {})),
                json.dumps(score.get('percentiles', {})),
            ))
            inserted += 1
            if inserted % 10000 == 0:
                print(f"  {inserted:,} loaded...")
        except Exception as e:
            print(f"Error loading EIN {ein}: {e}")

    conn.commit()
    print(f"✓ Inserted {inserted:,} scores")

    # Summary stats
    org_count = len(scores)
    health_dist = {}
    model_dist = {}
    tier_dist = {}

    for score in scores.values():
        h = score.get('financial_health')
        m = score.get('operating_model')
        t = score.get('visibility_tier')
        health_dist[h] = health_dist.get(h, 0) + 1
        model_dist[m] = model_dist.get(m, 0) + 1
        tier_dist[t] = tier_dist.get(t, 0) + 1

    avg_score = sum(s['merit_score'] for s in scores.values() if s['merit_score'] is not None) / org_count

    print(f"\nSummary: {org_count:,} orgs, avg score: {avg_score:.1f}")
    print("\nFinancial Health:")
    for health in ['Strong', 'Stable', 'Inspiring']:
        count = health_dist.get(health, 0)
        pct = 100 * count / org_count if org_count > 0 else 0
        print(f"  {health:<15s} {count:>8,} ({pct:>5.1f}%)")

    print("\nOperating Models:")
    for model in sorted(model_dist.keys()):
        count = model_dist[model]
        pct = 100 * count / org_count if org_count > 0 else 0
        print(f"  {model:<30s} {count:>8,} ({pct:>5.1f}%)")

    conn.close()
    print(f"\n✓ Done")

if __name__ == '__main__':
    load_scores_to_db(str(SCORES_FILE))
