#!/usr/bin/env python3
"""Build corrected v6_context table for droplet sync.

Exports the real V6 financial context data from registry_enriched
(scoring_tier, tier_label, confidence, peer_group_size, peer_group_description)
into a lean v6_context table suitable for the droplet.

Current droplet v6_context has incorrect peer_group_size_v6/peer_group_description_v6
(disjoint pipeline). This script rebuilds with verified columns.
"""

import sqlite3
import sys

def build_v6_context(src_db_path, dst_db_path):
    """Build corrected v6_context table."""
    src = sqlite3.connect(src_db_path)
    src.row_factory = sqlite3.Row
    
    # Check columns
    cursor = src.execute("PRAGMA table_info(registry_enriched)")
    columns = {row[1] for row in cursor.fetchall()}
    
    required = {'EIN', 'scoring_tier', 'tier_label', 'confidence', 'peer_group_size', 'peer_group_description'}
    missing = required - columns
    
    if missing:
        print(f"ERROR: Missing required columns: {missing}")
        src.close()
        return False
    
    # Build v6_context
    dst = sqlite3.connect(dst_db_path)
    dst.execute("DROP TABLE IF EXISTS v6_context")
    dst.execute("""
    CREATE TABLE v6_context (
        EIN TEXT PRIMARY KEY,
        scoring_tier TEXT,
        tier_label TEXT,
        confidence REAL,
        peer_group_size INTEGER,
        peer_group_description TEXT
    )
    """)
    
    # Export all rows where EIN is not null
    cursor = src.execute("""
    SELECT EIN, scoring_tier, tier_label, confidence, peer_group_size, peer_group_description
    FROM registry_enriched
    WHERE EIN IS NOT NULL
    ORDER BY EIN
    """)
    
    rows = cursor.fetchall()
    dst.executemany("""
    INSERT OR REPLACE INTO v6_context VALUES (?, ?, ?, ?, ?, ?)
    """, rows)
    
    # Index
    dst.execute("CREATE INDEX IF NOT EXISTS idx_v6_ein ON v6_context(EIN)")
    dst.commit()
    
    # Stats
    cursor = dst.execute("SELECT COUNT(*) FROM v6_context")
    count = cursor.fetchone()[0]
    
    cursor = dst.execute("SELECT COUNT(*) FROM v6_context WHERE scoring_tier IS NOT NULL")
    scored = cursor.fetchone()[0]
    
    print(f"✅ v6_context built: {count:,} rows, {scored:,} scored ({scored/count*100:.1f}%)")
    
    dst.close()
    src.close()
    return True

if __name__ == "__main__":
    src = "data/merit_registry.db"
    dst = "/tmp/merit_registry_v6_export.db"
    
    if build_v6_context(src, dst):
        print(f"\nExport saved: {dst}")
        print("Next step: rsync to droplet /opt/daanaa/merit_registry.db")
        print("Command: scripts/ops/sync_droplet_api.sh or custom rsync")
    else:
        sys.exit(1)
