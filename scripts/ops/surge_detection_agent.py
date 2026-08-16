#!/usr/bin/env python3
"""
Daanaa Autonomous Surge Detection Agent

Monitors search patterns for event-driven discovery:
- Detects keyword surges (e.g., "hurricane" spikes 10x)
- Maps surges to relevant org models + NTEE codes
- Auto-boosts high-performing orgs in affected peer groups
- Logs all actions for human review via /api/admin/surge-boosts

Respects Stewardship: transparent, reversible, human-in-command.
Run via cron: */5 * * * * python3 surge_detection_agent.py
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"

# Event triggers: (keyword, threshold_multiplier, NTEE codes, operating_models, boost_duration_hours)
EVENT_RULES = {
    'hurricane': {
        'keywords': ['hurricane', 'hurricane relief', 'disaster relief', 'emergency response'],
        'threshold': 5.0,  # 5x normal search volume
        'ntee_codes': ['M'],  # Disaster Relief
        'models': ['Direct_Service', 'Mission_Infrastructure'],
        'boost_duration_hours': 72,
        'relevance_reason': 'Event-driven discovery: disaster response surge detected',
    },
    'earthquake': {
        'keywords': ['earthquake', 'seismic', 'quake relief'],
        'threshold': 5.0,
        'ntee_codes': ['M'],
        'models': ['Direct_Service', 'Mission_Infrastructure'],
        'boost_duration_hours': 72,
        'relevance_reason': 'Event-driven discovery: earthquake response surge detected',
    },
    'flooding': {
        'keywords': ['flood', 'flood relief', 'flood recovery'],
        'threshold': 4.0,
        'ntee_codes': ['M'],
        'models': ['Direct_Service', 'Mission_Infrastructure'],
        'boost_duration_hours': 48,
        'relevance_reason': 'Event-driven discovery: flood response surge detected',
    },
    'food_crisis': {
        'keywords': ['food bank', 'hunger', 'food insecurity', 'food shortage'],
        'threshold': 3.0,
        'ntee_codes': ['K'],  # Food & Nutrition
        'models': ['Direct_Service', 'Mission_Infrastructure'],
        'boost_duration_hours': 168,  # 1 week
        'relevance_reason': 'Event-driven discovery: food security surge detected',
    },
    'homelessness': {
        'keywords': ['homelessness', 'homeless', 'housing crisis', 'shelter'],
        'threshold': 3.0,
        'ntee_codes': ['L'],  # Housing
        'models': ['Direct_Service', 'Mission_Infrastructure'],
        'boost_duration_hours': 120,  # 5 days
        'relevance_reason': 'Event-driven discovery: housing/homelessness surge detected',
    },
}

def get_search_volume(db, keyword, hours=1) -> dict:
    """Get search volume for a keyword in the last N hours."""
    since = datetime.utcnow() - timedelta(hours=hours)
    rows = db.execute("""
        SELECT query, COUNT(*) as count
        FROM search_events
        WHERE timestamp > ? AND (query LIKE ? OR query LIKE ?)
        GROUP BY query
    """, (since.isoformat(), f'%{keyword}%', f'%{keyword.replace(" ", "_")}%')).fetchall()

    total = sum(r[1] for r in rows)
    return {
        'keyword': keyword,
        'volume_1h': total,
        'volume_24h': get_search_volume_24h(db, keyword),
    }

def get_search_volume_24h(db, keyword) -> int:
    """Get search volume for keyword in last 24 hours."""
    since = datetime.utcnow() - timedelta(hours=24)
    count = db.execute("""
        SELECT COUNT(*) FROM search_events
        WHERE timestamp > ? AND (query LIKE ? OR query LIKE ?)
    """, (since.isoformat(), f'%{keyword}%', f'%{keyword.replace(" ", "_")}%')).fetchone()[0]
    return count

def detect_surges(db) -> list:
    """Detect keyword surges above threshold."""
    # search_events is populated by the API's search logging middleware.
    # If the table doesn't exist yet, there's nothing to detect.
    has_table = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='search_events'"
    ).fetchone()
    if not has_table:
        return []

    surges = []

    for event_name, config in EVENT_RULES.items():
        for keyword in config['keywords']:
            vol = get_search_volume(db, keyword, hours=1)
            vol_24h = vol['volume_24h']
            vol_1h = vol['volume_1h']

            # Surge = current volume is N× the 24h average
            if vol_24h > 0:
                avg_hourly = vol_24h / 24
                multiplier = vol_1h / avg_hourly if avg_hourly > 0 else 0

                if multiplier >= config['threshold'] and vol_1h > 5:  # Require at least 5 queries
                    surges.append({
                        'event': event_name,
                        'keyword': keyword,
                        'multiplier': multiplier,
                        'volume_1h': vol_1h,
                        'config': config,
                        'detected_at': datetime.utcnow().isoformat(),
                    })

    return surges

def find_boosted_orgs(db, surge: dict) -> list:
    """Find Strong/Stable orgs in affected models that aren't already boosted."""
    config = surge['config']
    ntee_codes = config['ntee_codes']
    models = config['models']

    # Find top-performing orgs (Strong + high peer percentile) in affected areas
    # that aren't already being boosted
    placeholders_ntee = ','.join('?' * len(ntee_codes))
    placeholders_models = ','.join('?' * len(models))

    rows = db.execute(f"""
        SELECT v4.EIN, r.organization_name, v4.financial_health,
               v4.operating_model, v4.peer_cell_size
        FROM v4_scores v4
        JOIN registry_enriched r ON v4.EIN = r.EIN
        WHERE r.NTEE1 IN ({placeholders_ntee})
          AND v4.operating_model IN ({placeholders_models})
          AND v4.financial_health IN ('Strong', 'Stable')
          AND v4.EIN NOT IN (
              SELECT ein FROM surge_boosts
              WHERE status = 'active' AND expires_at > datetime('now')
          )
        ORDER BY
          CASE WHEN v4.financial_health = 'Strong' THEN 1 ELSE 2 END,
          v4.peer_cell_size DESC
        LIMIT 20
    """, ntee_codes + models).fetchall()

    return [dict(r) for r in rows]

def create_surge_detection(db, surge: dict) -> int:
    """Create surge_detections entry and return ID."""
    result = db.execute("""
        INSERT INTO surge_detections (
            query, keyword, event_type, multiplier, volume_1h,
            detected_at, expires_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now', '+7 days'), 'active')
    """, (
        surge['keyword'],
        surge['keyword'],
        surge['event'],
        surge['multiplier'],
        surge['volume_1h'],
        surge['detected_at'],
    ))
    db.commit()
    return result.lastrowid

def create_surge_boosts(db, surge_id: int, orgs: list, config: dict):
    """Create surge_boosts entries for relevant orgs."""
    boost_hours = config['boost_duration_hours']
    reason = config['relevance_reason']

    for org in orgs:
        # Relevance score: Strong=0.9, Stable=0.7, weighted by peer cell size
        base_score = 0.9 if org['financial_health'] == 'Strong' else 0.7
        peer_factor = min(1.0, org['peer_cell_size'] / 3000)  # normalize to ~3000 peer avg
        relevance_score = base_score * peer_factor

        db.execute("""
            INSERT INTO surge_boosts (
                surge_id, ein, relevance_score, relevance_reason,
                boosted_at, expires_at, status
            ) VALUES (?, ?, ?, ?, datetime('now'),
                     datetime('now', '+' || ? || ' hours'), 'active')
        """, (surge_id, org['EIN'], relevance_score, reason, boost_hours))

    db.commit()

def log_action(surge: dict, org_count: int):
    """Log agent action for transparency."""
    print(f"""
[{datetime.utcnow().isoformat()}] SURGE DETECTED
  Event: {surge['event']}
  Keyword: {surge['keyword']}
  Multiplier: {surge['multiplier']:.1f}x normal
  Volume (1h): {surge['volume_1h']} searches
  Orgs boosted: {org_count}
  Duration: {surge['config']['boost_duration_hours']}h

  → View at: /api/admin/surge-boosts (X-Admin-Key: $DAANAA_ADMIN_KEY)
  → Override any boost: POST /api/admin/surge-boosts/<id>/override
""")

def run_agent():
    """Main agent loop: detect surges, boost orgs, log for human review."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row

        # Detect surges
        surges = detect_surges(conn)
        if not surges:
            return  # No action needed

        # For each surge: find orgs, create boost entries
        for surge in surges:
            orgs = find_boosted_orgs(conn, surge)
            if not orgs:
                continue  # No eligible orgs to boost

            surge_id = create_surge_detection(conn, surge)
            create_surge_boosts(conn, surge_id, orgs, surge['config'])
            log_action(surge, len(orgs))

        conn.close()
    except Exception as e:
        print(f"[ERROR] Surge agent failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_agent()
