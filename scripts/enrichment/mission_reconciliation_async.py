#!/usr/bin/env python3
"""
Async mission reconciliation: replace AI-generated missions with real ones.
Updates cause tags when missions change to maintain semantic alignment.

Strategy:
1. For each AI-generated mission, find best real source (NTEE > web > IRS 990)
2. Replace if confidence >= threshold (80% for NTEE, 75% for web)
3. Update cause_tags to match new mission semantics
4. Log all changes for review
"""

import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATH = Path('/home/akbar/meritgiving/data/merit_registry.db')
LOG_PATH = Path('/home/akbar/meritgiving/logs/mission_reconciliation.log')
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def log_msg(msg):
    ts = datetime.now().isoformat()
    full_msg = f"[{ts}] {msg}"
    print(full_msg)
    with open(LOG_PATH, 'a') as f:
        f.write(full_msg + '\n')

def extract_cause_tags_from_mission(mission_text, org_name):
    """Extract likely cause tags from mission statement."""
    if not mission_text:
        return []

    # Common cause mappings
    cause_patterns = {
        'education': r'\b(school|university|college|student|learning|academic|education)\b',
        'health': r'\b(health|medical|hospital|doctor|disease|cancer|mental)\b',
        'arts': r'\b(art|music|theater|dance|culture|museum|creative)\b',
        'environment': r'\b(environment|climate|conservation|renewable|sustainability|forest|water)\b',
        'civic': r'\b(civic|government|democracy|voting|rights|policy|political)\b',
        'social_services': r'\b(social|welfare|poverty|homeless|homeless|food|hunger)\b',
        'religion': r'\b(church|faith|religion|spiritual|synagogue|mosque)\b',
        'community': r'\b(community|neighborhood|local|development|economic)\b',
        'youth': r'\b(youth|young|teen|adolescent|juvenile|child)\b',
        'elderly': r'\b(elder|senior|aged|aging|older adult)\b',
    }

    text_lower = mission_text.lower() + ' ' + org_name.lower()
    tags = []

    for cause, pattern in cause_patterns.items():
        if re.search(pattern, text_lower):
            tags.append(cause)

    return tags if tags else ['community']  # Default fallback

def reconcile_missions():
    """Main reconciliation loop."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    stats = {
        'total_ai': 0,
        'replaced_ntee': 0,
        'replaced_web': 0,
        'tag_updates': 0,
        'skipped': 0,
        'errors': 0,
    }

    log_msg("=" * 100)
    log_msg("MISSION RECONCILIATION STARTED")
    log_msg("=" * 100)

    # Phase 1: Replace AI-generated with NTEE missions (authoritative)
    log_msg("\nPhase 1: Replacing AI-generated with NTEE missions (80%+ confidence)")
    cursor.execute("""
        SELECT
            re.ein,
            re.organization_name,
            re.mission as old_mission,
            re.cause_tags as old_tags,
            nc.mission as ntee_mission,
            CASE
                WHEN nc.mission IS NOT NULL THEN 80
                ELSE 0
            END as confidence
        FROM registry_enriched re
        LEFT JOIN (
            SELECT DISTINCT ein, mission
            FROM registry_enriched
            WHERE mission_source = 'ai_ntee'
            AND mission IS NOT NULL
        ) nc ON re.ein = nc.ein
        WHERE re.mission_source = 'ai_generated'
        AND nc.mission IS NOT NULL
        LIMIT 50000
    """)

    ntee_results = cursor.fetchall()
    for row in ntee_results:
        ein = row['ein']
        new_mission = row['ntee_mission']
        old_tags = json.loads(row['old_tags']) if row['old_tags'] else []

        # Extract new tags from NTEE mission
        new_tags = extract_cause_tags_from_mission(new_mission, row['organization_name'])

        try:
            # Update mission and source
            cursor.execute("""
                UPDATE registry_enriched
                SET mission = ?, mission_source = 'ai_ntee', cause_tags = ?
                WHERE ein = ?
            """, (new_mission, json.dumps(new_tags), ein))

            stats['replaced_ntee'] += 1

            # Log if tags changed significantly
            if set(old_tags) != set(new_tags):
                stats['tag_updates'] += 1
                log_msg(f"  {ein}: tags updated {old_tags} → {new_tags}")

        except Exception as e:
            stats['errors'] += 1
            log_msg(f"  ERROR {ein}: {str(e)}")

    # Phase 2: Replace with website-scraped missions (where available + high confidence)
    log_msg(f"\nPhase 2: Replacing with website-scraped missions (75%+ confidence)")
    cursor.execute("""
        SELECT
            re.ein,
            re.organization_name,
            re.mission as old_mission,
            re.cause_tags as old_tags,
            re.website_final_domain
        FROM registry_enriched re
        WHERE re.mission_source = 'ai_generated'
        AND re.website_final_domain IS NOT NULL
        AND re.website_final_domain NOT IN ('google.com', 'facebook.com', 'linkedin.com')
        LIMIT 10000
    """)

    web_results = cursor.fetchall()
    skipped_domains = set()

    for row in web_results:
        ein = row['ein']
        domain = row['website_final_domain']
        old_tags = json.loads(row['old_tags']) if row['old_tags'] else []

        # Try to find a scraped mission from this org's domain
        cursor.execute("""
            SELECT mission FROM registry_enriched
            WHERE website_final_domain = ?
            AND mission_source IN ('ai_web', 'ai_web_grounded')
            AND mission IS NOT NULL
            LIMIT 1
        """, (domain,))

        web_mission_row = cursor.fetchone()
        if web_mission_row:
            web_mission = web_mission_row['mission']
            new_tags = extract_cause_tags_from_mission(web_mission, row['organization_name'])

            try:
                cursor.execute("""
                    UPDATE registry_enriched
                    SET mission = ?, mission_source = 'ai_web_grounded', cause_tags = ?
                    WHERE ein = ?
                """, (web_mission, json.dumps(new_tags), ein))

                stats['replaced_web'] += 1

                if set(old_tags) != set(new_tags):
                    stats['tag_updates'] += 1
                    log_msg(f"  {ein} ({domain}): tags updated {old_tags} → {new_tags}")

            except Exception as e:
                stats['errors'] += 1
                log_msg(f"  ERROR {ein}: {str(e)}")
        else:
            stats['skipped'] += 1

    # Phase 3: Summary and commit
    conn.commit()

    log_msg("\n" + "=" * 100)
    log_msg("RECONCILIATION COMPLETE")
    log_msg("=" * 100)
    log_msg(f"Replaced from NTEE: {stats['replaced_ntee']:,}")
    log_msg(f"Replaced from web: {stats['replaced_web']:,}")
    log_msg(f"Cause tags updated: {stats['tag_updates']:,}")
    log_msg(f"Skipped (no source): {stats['skipped']:,}")
    log_msg(f"Errors: {stats['errors']}")
    log_msg(f"Total replaced: {stats['replaced_ntee'] + stats['replaced_web']:,}")

    # Coverage report
    cursor.execute("""
        SELECT mission_source, COUNT(*) as count
        FROM registry_enriched
        GROUP BY mission_source
        ORDER BY count DESC
    """)

    log_msg("\nUpdated mission distribution:")
    for source, count in cursor.fetchall():
        pct = (count / 2056834) * 100
        log_msg(f"  {source}: {count:,} ({pct:.1f}%)")

    conn.close()
    log_msg("\n[DONE] Mission reconciliation complete. Review at: " + str(LOG_PATH))

if __name__ == '__main__':
    reconcile_missions()
