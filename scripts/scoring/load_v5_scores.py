#!/usr/bin/env python3
"""Load v5 scorer output into merit_registry.db"""

import json
import sqlite3
from pathlib import Path
import logging

DB_PATH = Path('data/merit_registry.db')
SCORES_FILE = Path('scores_v5_0_full.json')
LOG_DIR = Path('logs')

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'load_v5_scores.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_scores():
    logger.info(f"Loading scores from {SCORES_FILE}")
    with open(SCORES_FILE) as f:
        data = json.load(f)
    return data['scores']

def update_db(scores):
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    logger.info(f"Updating {len(scores):,} orgs")

    updated = 0
    for i, score in enumerate(scores):
        if i % 100000 == 0:
            logger.info(f"  {i:,}/{len(scores):,}")

        ein = score.get('ein')
        if not ein:
            continue

        # Map score fields to DB columns
        updates = {
            'merit_archetype_v5': score.get('archetype_key'),
            'merit_archetype_v5_label': score.get('archetype'),
            'merit_band_v5': score.get('band_key'),
            'merit_band_v5_label': score.get('band'),
            'merit_score_v5': score.get('reserves_percentile'),
            'merit_health_signal_v5': score.get('health_signal'),
            'merit_peer_group_v5': score.get('peer_group_label'),
            'merit_peer_count_v5': score.get('peer_org_count'),
        }

        # Build UPDATE query
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [ein]
        query = f"UPDATE registry_enriched SET {set_clause} WHERE ein = ?"

        try:
            c.execute(query, values)
            updated += 1
        except Exception as e:
            logger.error(f"Error updating {ein}: {e}")

    conn.commit()
    conn.close()

    logger.info(f"Updated {updated:,} orgs")

def main():
    logger.info("Loading v5 Scores into Database")
    scores = load_scores()
    update_db(scores)
    logger.info("Done")

if __name__ == '__main__':
    main()
