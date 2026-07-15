#!/usr/bin/env python3
"""
Create database indexes for discovery queries.
Run once to optimize.
"""

import sqlite3
from pathlib import Path

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'

def create_indexes():
    """Create indexes for discovery queries."""
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()

    indexes = [
        # For finding orgs needing discovery
        ("idx_website_missing_links",
         "CREATE INDEX IF NOT EXISTS idx_website_missing_links ON registry_enriched(website, donate_url, volunteer_url) WHERE website IS NOT NULL AND website != ''"),

        # For checking if already processed
        ("idx_queue_ein_undeployed",
         "CREATE INDEX IF NOT EXISTS idx_queue_ein_undeployed ON link_deployment_queue(ein, deployed_at) WHERE deployed_at IS NULL"),

        # For deployment queries
        ("idx_queue_undeployed",
         "CREATE INDEX IF NOT EXISTS idx_queue_undeployed ON link_deployment_queue(created_at) WHERE deployed_at IS NULL"),

        # For monitoring
        ("idx_queue_created_deployed",
         "CREATE INDEX IF NOT EXISTS idx_queue_created_deployed ON link_deployment_queue(created_at, deployed_at)"),
    ]

    for name, sql in indexes:
        try:
            cursor.execute(sql)
            print(f"✅ {name}")
        except Exception as e:
            print(f"⚠️  {name}: {e}")

    db.commit()
    db.close()
    print("\n✅ Indexes optimized")

if __name__ == '__main__':
    create_indexes()
