#!/usr/bin/env python3
"""
Sync financial data HOME → DROPLET.
Home is source of truth. Exports v5 context from home DB, pushes to droplet via SSH.
Strategy: export CSV, rsync to droplet, import via SSH.
"""
import sqlite3
import subprocess
import csv
import os
from pathlib import Path
from datetime import datetime
import tempfile

HOME_DB = Path.home() / "meritgiving" / "data" / "merit_registry.db"
DROPLET_HOST = "root@162.243.97.179"
DROPLET_DB = "/data/precompute/v1/search.db"
DROPLET_SYNC_DIR = "/tmp/daanaa_sync"

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
        # 1. Export financial data from home to CSV
        log("Exporting v5 context from home DB...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
            writer = csv.writer(f)
            writer.writerow(['ein', 'revenue', 'expenses', 'net_assets', 'months_of_reserve',
                           'program_pct', 'health_signal', 'archetype', 'band', 'peer_count'])

            cur = home.cursor()
            cur.execute("""
            SELECT EIN, total_revenue, total_expenses, net_assets,
                   months_of_reserve, program_expense_pct, merit_health_signal_v5,
                   merit_archetype_v5_label, merit_band_v5_label, merit_peer_count_v5
            FROM registry_enriched
            WHERE deductibility = 1 AND org_status = 'active'
            """)

            row_count = 0
            for row in cur.fetchall():
                writer.writerow(row)
                row_count += 1
                if row_count % 100000 == 0:
                    log(f"  {row_count:,} rows exported...")

            log(f"✓ Exported {row_count:,} orgs to {csv_path}")

        home.close()

        # 2. Rsync CSV to droplet
        log("Syncing to droplet...")
        result = subprocess.run(
            ["rsync", "-avz", csv_path, f"{DROPLET_HOST}:{DROPLET_SYNC_DIR}/financial_data.csv"],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            log(f"✗ rsync failed: {result.stderr}")
            return False

        log(f"✓ Data synced to droplet")

        # 3. Import on droplet via SSH
        log("Importing data on droplet...")
        import_sql = f"""
        CREATE TEMP TABLE financial_import (
            ein TEXT, revenue REAL, expenses REAL, net_assets REAL,
            months_of_reserve REAL, program_pct REAL, health_signal TEXT,
            archetype TEXT, band TEXT, peer_count INT
        );
        .mode csv
        .import {DROPLET_SYNC_DIR}/financial_data.csv financial_import
        UPDATE orgs SET
            revenue = i.revenue, expenses = i.expenses, net_assets = i.net_assets,
            months_of_reserve = i.months_of_reserve, program_pct = i.program_pct,
            health_signal = i.health_signal, archetype = i.archetype,
            band = i.band, peer_count = i.peer_count
        FROM financial_import i WHERE orgs.ein = i.ein;
        """

        cmd = f'sqlite3 {DROPLET_DB} "{import_sql}" && rm {DROPLET_SYNC_DIR}/financial_data.csv'
        result = subprocess.run(
            ["ssh", DROPLET_HOST, cmd],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode != 0:
            log(f"✗ Import failed: {result.stderr}")
            return False

        log(f"✓ Data imported on droplet")

        # Cleanup
        os.unlink(csv_path)
        log(f"✓ Financial data sync complete")
        return True

    except Exception as e:
        log(f"✗ Sync failed: {e}")
        return False

if __name__ == "__main__":
    success = sync()
    import sys
    sys.exit(0 if success else 1)
