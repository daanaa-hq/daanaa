#!/usr/bin/env python3
"""
Real-time daemon health monitor.
Tracks discovery progress, alerts on issues, estimates ETA.
"""

import sqlite3
import subprocess
import time
from datetime import datetime
from pathlib import Path

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
LOG = Path.home() / 'meritgiving' / 'logs' / 'discovery_daemon_blitz.log'

def get_daemon_count():
    result = subprocess.run(['pgrep', '-f', 'discovery_daemon.py'], capture_output=True)
    return len(result.stdout.decode().strip().split('\n')) if result.stdout else 0

def get_db_stats():
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()

    total_with_links = cursor.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL OR volunteer_url IS NOT NULL"
    ).fetchone()[0]

    remaining = cursor.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE website IS NOT NULL AND website != '' AND (donate_url IS NULL OR volunteer_url IS NULL)"
    ).fetchone()[0]

    db.close()
    return total_with_links, remaining

def get_log_stats():
    if not LOG.exists():
        return 0, 0

    try:
        with open(LOG, 'r', encoding='utf-8', errors='ignore') as f:
            last_1000 = f.readlines()[-1000:]

        success = sum(1 for line in last_1000 if 'links verified' in line)
        errors = sum(1 for line in last_1000 if 'Failed to fetch' in line)
    except Exception:
        return 0, 0

    return success, errors

def print_status():
    daemons = get_daemon_count()
    total, remaining = get_db_stats()
    success, errors = get_log_stats()

    clear = '\033[2J\033[H'
    print(clear, end='')

    print("=" * 70)
    print(f"  DAANAA DISCOVERY BLITZ — REAL-TIME MONITOR")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    # Status
    print(f"  Daemon Instances:     {daemons}/4 ({'✅ OK' if daemons == 4 else '⚠️  DEGRADED'})")
    print()

    # Progress
    percent = (total / (total + remaining) * 100) if (total + remaining) > 0 else 0
    bar_len = 40
    filled = int(bar_len * percent / 100)
    bar = '█' * filled + '░' * (bar_len - filled)

    print(f"  Progress: [{bar}] {percent:.1f}%")
    print(f"  Discovered:  {total:7d} orgs")
    print(f"  Remaining:   {remaining:7d} orgs")
    print()

    # Performance
    if success > 0:
        success_rate = 100 * success / (success + errors) if (success + errors) > 0 else 0
        print(f"  Success Rate: {success_rate:.1f}% ({success} verified, {errors} failed)")

        # ETA
        if remaining > 0 and success > 0:
            orgs_per_cycle = success
            cycles_needed = remaining / orgs_per_cycle
            hours_per_cycle = 0.5  # Rough estimate based on batch processing
            eta_hours = cycles_needed * hours_per_cycle

            print(f"  ETA: ~{eta_hours:.1f} hours to completion")
        print()

    # Alerts
    if daemons < 4:
        print(f"  ⚠️  WARNING: {4 - daemons} daemon(s) crashed! Restart with:")
        print(f"      bash scripts/optimized_discovery_launch.sh")
        print()

    if success == 0 and errors == 0:
        print(f"  ⚠️  WARNING: No recent activity in logs!")
        print(f"      Check: tail -100 {LOG}")
        print()

    print("  Status: " + ("🟢 HEALTHY" if daemons == 4 and success > 0 else "🟡 DEGRADED" if daemons >= 2 else "🔴 CRITICAL"))
    print()

if __name__ == '__main__':
    print("Starting monitor... (Ctrl+C to exit)")
    print()

    try:
        while True:
            print_status()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")
