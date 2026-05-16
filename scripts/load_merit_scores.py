#!/usr/bin/env python3
"""
Load merit_scorer_v3_3 output into registry_enriched.

Adds merit_score (REAL, 0-100) and merit_band (TEXT) columns and populates
them by EIN. EINs are normalized to 9-digit zero-padded on both sides so
leading-zero EINs match. Orgs with no financial score remain NULL.

Usage:
    python3 scripts/load_merit_scores.py data/merit_scores_v3_3.json
"""
import json
import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'merit_registry.db')


def norm(ein: str) -> str:
    return ''.join(c for c in str(ein) if c.isdigit()).zfill(9)


def main():
    if len(sys.argv) < 2:
        print('usage: load_merit_scores.py <scores.json>', file=sys.stderr)
        sys.exit(1)
    scores_path = sys.argv[1]

    with open(scores_path) as f:
        data = json.load(f)

    rows = []
    for ein, payload in data.items():
        merit = payload.get('merit', {})
        score = merit.get('merit_score')
        band = merit.get('merit_band')
        if score is None:
            continue
        rows.append((float(score), band, norm(ein)))

    print(f'{len(rows):,} scored orgs to load')

    db = sqlite3.connect(DB_PATH)
    db.execute('PRAGMA journal_mode=WAL')

    cols = [r[1] for r in db.execute('PRAGMA table_info(registry_enriched)').fetchall()]
    if 'merit_score' not in cols:
        db.execute('ALTER TABLE registry_enriched ADD COLUMN merit_score REAL')
        print('added merit_score column')
    if 'merit_band' not in cols:
        db.execute('ALTER TABLE registry_enriched ADD COLUMN merit_band TEXT')
        print('added merit_band column')

    # Clear any prior load so re-runs are idempotent
    db.execute('UPDATE registry_enriched SET merit_score = NULL, merit_band = NULL')

    db.executemany(
        "UPDATE registry_enriched "
        "SET merit_score = ?, merit_band = ? "
        "WHERE printf('%09d', CAST(EIN AS INTEGER)) = ?",
        rows,
    )
    matched = db.execute(
        'SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL'
    ).fetchone()[0]
    db.execute(
        'CREATE INDEX IF NOT EXISTS idx_merit_score ON registry_enriched(merit_score)'
    )
    db.commit()

    print(f'matched + populated: {matched:,} of {len(rows):,}')
    dist = db.execute(
        'SELECT merit_band, COUNT(*) FROM registry_enriched '
        'WHERE merit_band IS NOT NULL GROUP BY merit_band ORDER BY 2 DESC'
    ).fetchall()
    print('band distribution in DB:')
    for band, n in dist:
        print(f'  {band:<12} {n:>6,}')


if __name__ == '__main__':
    main()
