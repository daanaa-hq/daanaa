#!/usr/bin/env python3
"""
Database Migration: Add v5.0 scores to registry_enriched.

New columns:
- merit_archetype_v5: Financial operating model (donation_funded, fee_for_service, etc.)
- merit_archetype_v5_label: Human-readable archetype
- merit_band_v5: Revenue band (micro, professional, established)
- merit_band_v5_label: Human-readable band label
- merit_score_v5: Percentile rank within peer group (0-99)
- merit_health_signal_v5: HEALTHY, STABLE, or CAUTION
- merit_peer_group_v5: Peer group label for reference
- merit_peer_count_v5: Number of orgs in peer group
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path.home() / "meritgiving/data/merit_registry.db"
SCORES_FILE = Path("/tmp/scores_v5_0_final.json")

def main():
    print("Migrating v5.0 scores to registry...")
    print(f"Loading scores from {SCORES_FILE}")

    # Load scores (stream to avoid memory overload)
    with open(SCORES_FILE) as f:
        data = json.load(f)

    scores_list = data['scores']
    scores = {s['ein']: s for s in scores_list if s['ein']}  # Skip null EINs
    print(f"Loaded {len(scores)} scores (skipped {len(scores_list) - len(scores)} with null EIN)")

    # Connect to database
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # Add columns if they don't exist
    columns_to_add = [
        ('merit_archetype_v5', 'TEXT'),
        ('merit_archetype_v5_label', 'TEXT'),
        ('merit_band_v5', 'TEXT'),
        ('merit_band_v5_label', 'TEXT'),
        ('merit_score_v5', 'REAL'),
        ('merit_health_signal_v5', 'TEXT'),
        ('merit_peer_group_v5', 'TEXT'),
        ('merit_peer_count_v5', 'INTEGER'),
    ]

    # Check which columns exist
    c.execute("PRAGMA table_info(registry_enriched)")
    existing_cols = {row[1] for row in c.fetchall()}

    for col_name, col_type in columns_to_add:
        if col_name not in existing_cols:
            try:
                c.execute(f"ALTER TABLE registry_enriched ADD COLUMN {col_name} {col_type}")
                print(f"  Added column: {col_name}")
                conn.commit()
            except sqlite3.OperationalError as e:
                print(f"  Warning: {col_name}: {e}")
        else:
            print(f"  Column {col_name} already exists")

    # Update registry with scores
    updated = 0
    skipped = 0

    for ein, score in scores.items():
        try:
            c.execute("""
                UPDATE registry_enriched
                SET
                    merit_archetype_v5 = ?,
                    merit_archetype_v5_label = ?,
                    merit_band_v5 = ?,
                    merit_band_v5_label = ?,
                    merit_score_v5 = ?,
                    merit_health_signal_v5 = ?,
                    merit_peer_group_v5 = ?,
                    merit_peer_count_v5 = ?
                WHERE EIN = ?
            """, (
                score['archetype_key'],
                score['archetype'],
                score['band_key'],
                score['band'],
                score['reserves_percentile'],
                score['health_signal'],
                score['peer_group_label'],
                score['peer_org_count'],
                ein,
            ))

            if c.rowcount > 0:
                updated += 1
            else:
                skipped += 1

        except Exception as e:
            print(f"Error updating {ein}: {e}")

    conn.commit()
    conn.close()

    print(f"\n✓ Migration complete!")
    print(f"  Updated: {updated:,} orgs")
    print(f"  Skipped: {skipped:,} (not in registry)")
    print(f"  Total scored: {updated + skipped:,}")

if __name__ == '__main__':
    main()
