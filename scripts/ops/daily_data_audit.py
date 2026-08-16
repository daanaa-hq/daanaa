#!/usr/bin/env python3
"""
Daily data freshness audit — runs at 00:30 to report status of all data sources.

Checks:
1. IRS revocation list age + match count
2. ProPublica 990 new filings (last 24h)
3. IRS SOI coverage (2024 + 2025)
4. Link deployment queue status
5. Website discovery progress
6. Data freshness warnings
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
LOG = Path.home() / 'meritgiving' / 'logs' / 'daily_data_audit.log'
REVOKE_STAMP = Path.home() / 'meritgiving' / 'data' / 'irs_revocation_last_sync.txt'

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

def audit():
    db = sqlite3.connect(str(DB))
    c = db.cursor()
    
    log("=" * 70)
    log("DAILY DATA FRESHNESS AUDIT")
    log("=" * 70)
    
    # 1. IRS Revocations
    last_sync = "unknown"
    if REVOKE_STAMP.exists():
        last_sync = REVOKE_STAMP.read_text().strip()
    c.execute("SELECT COUNT(*) FROM revoked_eins")
    revoked_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM registry_enriched WHERE irs_revoked = 1")
    revoked_in_index = c.fetchone()[0]
    log(f"✅ IRS Revocations: {revoked_in_index:,} marked (of {revoked_count:,} total) | last sync: {last_sync}")
    
    # 2. ProPublica recent filings
    c.execute("""
        SELECT COUNT(*) FROM registry_enriched 
        WHERE data_source='propublica' 
        AND updated_at > datetime('now', '-1 day')
    """)
    pp_recent = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM registry_enriched WHERE data_source='propublica'")
    pp_total = c.fetchone()[0]
    log(f"📊 ProPublica: {pp_total:,} total, {pp_recent} new in 24h")
    
    # 3. IRS SOI coverage
    c.execute("""
        SELECT latest_tax_year, COUNT(*) 
        FROM registry_enriched 
        WHERE data_source='irs_soi'
        GROUP BY latest_tax_year
        ORDER BY latest_tax_year DESC
        LIMIT 3
    """)
    irs_coverage = c.fetchall()
    log(f"📋 IRS SOI: " + ", ".join([f"{y}({cnt:,})" for y,cnt in irs_coverage]))
    
    # 3b. Phantom link statuses (2026-07-19: 803 rows had status='beta' with
    # donate_url NULL — likely from the 2026-07-16 bulk status migration.
    # A donor-facing status must never exist without its URL.)
    c.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE donate_url IS NULL AND donate_url_status IN ('beta', 'claimed', 'verified')
    """)
    phantoms = c.fetchone()[0]
    if phantoms:
        log(f"🚨 PHANTOM LINK STATUSES: {phantoms} rows have a live donate status but NULL URL — investigate the writer")
    else:
        log("✅ Link status integrity: no status-without-URL rows")

    # 4. Link queue status
    c.execute("SELECT COUNT(*) FROM link_deployment_queue WHERE deployed_at IS NULL")
    pending = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM link_deployment_queue WHERE deployed_at > datetime('now', '-1 day')")
    deployed_24h = c.fetchone()[0]
    log(f"🔗 Links: {pending:,} pending, {deployed_24h:,} deployed in 24h")
    
    # 5. Website discovery progress
    c.execute("SELECT COUNT(*) FROM registry_enriched WHERE website IS NOT NULL AND website != ''")
    with_websites = c.fetchone()[0]
    total_active = 1850001  # from earlier check
    pct = (with_websites / total_active * 100)
    log(f"🌐 Websites: {with_websites:,}/{total_active:,} ({pct:.1f}%)")
    
    # 6. Data staleness warnings
    c.execute("SELECT MAX(updated_at) FROM registry_enriched")
    latest = c.fetchone()[0]
    if latest:
        latest_dt = datetime.fromisoformat(latest)
        hours_old = (datetime.now() - latest_dt).total_seconds() / 3600
        if hours_old > 24:
            log(f"⚠️  WARNING: Registry data is {hours_old:.0f}h old (>24h threshold)")
        else:
            log(f"✅ Registry: current ({hours_old:.1f}h old)")
    
    db.close()
    
    log("=" * 70)
    log("Audit complete. Full report: tail -50 {0}".format(LOG))

if __name__ == '__main__':
    audit()
