#!/usr/bin/env python3
"""
Hourly IRS BMF Status Check — detect revoked/inactive nonprofits

Compares registry_enriched against irs_bmf table to detect:
1. Revoked status (irs_bmf.status != 'Unconditional Approval')
2. Deductibility changes (deductibility changed from 1 to 0)
3. Inactive orgs

Removes flagged orgs from public search and logs the change.

Run via cron: 0 * * * * cd ~/meritgiving && python3 scripts/hourly_irs_status_check.py

Logging: logs/irs_status_check.log
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
LOG_PATH = Path.home() / "meritgiving/logs/irs_status_check.log"

def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    log("━" * 70)
    log("IRS Status Check — Hourly Monitor")

    # 1. Find orgs whose IRS status changed
    c.execute("""
        SELECT
            r.EIN,
            r.organization_name,
            r.deductibility as db_deductibility,
            b.deductibility as irs_deductibility,
            b.status as irs_status
        FROM registry_enriched r
        LEFT JOIN irs_bmf b ON r.EIN = b.ein
        WHERE r.deductibility = '1'
          AND (b.deductibility IS NULL OR b.deductibility != '1' OR b.status NOT LIKE '%Unconditional%')
        LIMIT 100
    """)

    flagged = c.fetchall()

    if not flagged:
        log("✓ No status changes detected. All public orgs remain deductible.")
        conn.close()
        return

    log(f"⚠️  Found {len(flagged)} organizations with changed IRS status")

    for ein, name, db_ded, irs_ded, irs_status in flagged:
        reason = ""
        if irs_ded != '1':
            reason = f"Deductibility changed to {irs_ded}"
        elif irs_status and "Unconditional" not in irs_status:
            reason = f"Status: {irs_status}"
        else:
            reason = "IRS record not found"

        log(f"  [{ein}] {name} — {reason}")

        # Remove from public search by setting deductibility to NULL
        # (keeps record for historical tracking, removes from results)
        c.execute("""
            UPDATE registry_enriched
            SET deductibility = NULL, updated_at = datetime('now')
            WHERE EIN = ?
        """, (ein,))

    conn.commit()
    log(f"✓ Updated {len(flagged)} org(s) to remove from public search")
    log("━" * 70)
    conn.close()

if __name__ == "__main__":
    main()
