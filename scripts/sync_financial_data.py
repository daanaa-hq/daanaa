#!/usr/bin/env python3
"""
Sync financial data HOME → DROPLET.
Home is source of truth. Push current state to droplet's search.db.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

HOME_DB = Path.home() / "meritgiving" / "data" / "merit_registry.db"
DROPLET_DB = "/data/precompute/v1/search.db"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def sync():
    log("=== FINANCIAL DATA SYNC: HOME → DROPLET ===")

    try:
        home = sqlite3.connect(str(HOME_DB))
        home.row_factory = sqlite3.Row
    except Exception as e:
        log(f"✗ Cannot open home DB: {e}")
        return False

    try:
        droplet = sqlite3.connect(DROPLET_DB, timeout=30)
    except Exception as e:
        log(f"✗ Cannot open droplet DB: {e}")
        log("  (Is the droplet reachable? This script assumes local access.)")
        home.close()
        return False

    # Sync strategy: home DB records are authoritative.
    # For each org in home, update or insert in droplet.

    try:
        # Get orgs with financial data from home
        home_cur = home.cursor()
        home_cur.execute("""
        SELECT EIN, total_revenue, total_expenses, net_assets,
               months_of_reserve, program_expense_pct, merit_health_signal_v5
        FROM registry_enriched
        WHERE total_revenue > 0 OR total_expenses > 0
        """)

        home_rows = home_cur.fetchall()
        log(f"Syncing {len(home_rows):,} orgs with financial data...")

        droplet_cur = droplet.cursor()
        synced = 0

        for row in home_rows:
            ein, revenue, expenses, assets, mor, pct, health = row

            # Update or insert in droplet
            droplet_cur.execute("""
            UPDATE orgs
            SET revenue = ?, expenses = ?, net_assets = ?,
                months_of_reserve = ?, program_pct = ?, health_signal = ?
            WHERE ein = ?
            """, (revenue, expenses, assets, mor, pct, health, ein))

            if droplet_cur.rowcount == 0:
                # Org doesn't exist in droplet, insert it
                droplet_cur.execute("""
                INSERT OR IGNORE INTO orgs (ein, revenue, expenses, net_assets,
                                            months_of_reserve, program_pct, health_signal)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ein, revenue, expenses, assets, mor, pct, health))

            synced += 1
            if synced % 50000 == 0:
                log(f"  {synced:,} / {len(home_rows):,} synced")
                droplet.commit()

        droplet.commit()
        log(f"✓ Synced {synced:,} financial records")

        # Summary
        droplet_count = droplet_cur.execute("SELECT COUNT(*) FROM orgs WHERE revenue > 0").fetchone()[0]
        log(f"Droplet now has {droplet_count:,} orgs with financial data")

        home.close()
        droplet.close()
        return True

    except Exception as e:
        log(f"✗ Sync failed: {e}")
        home.close()
        droplet.close()
        return False

if __name__ == "__main__":
    success = sync()
    import sys
    sys.exit(0 if success else 1)
