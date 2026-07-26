#!/usr/bin/env python3
"""
Website search blitz efficiency tracker — phase-aware.

Measures live discovery throughput from `link_deployment_queue` row timestamps.

Why not registry_enriched.donate_url (the previous approach): the pipeline is
batched. The daemon queues links continuously, but `deploy_queued_links.py`
drains the queue into `registry_enriched.donate_url` only every 4 hours (cron
`0 */4 * * *`). Watching donate_url therefore reports 0/h for the ~4 hours
between drains no matter how well the daemon is running.

The old version compounded that by computing deltas against a state file it
rewrote on every run, so two runs minutes apart always showed zero. On
2026-07-26 it reported "0.0% SEVERE DROP" while the daemon was queuing 772
links/hour. See LESSONS.md.

Wall-clock windows off the row timestamps fix both: the reading no longer
depends on when the tracker last ran.
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

DB = Path.home() / 'meritgiving/data/merit_registry.db'
LOG_DIR = Path.home() / 'meritgiving/logs'
ALERT_FILE = LOG_DIR / 'blitz_efficiency_alert.log'

# Discovery is bounded by how many orgs permit crawling (robots.txt is honoured
# per DECISIONS.md 2026-07-18), not by hardware. 100/h is a healthy floor.
TARGET_LINKS_PER_HOUR = 100.0

# Stale queue rows mean the daemon stopped even if the drain looks fine.
STALL_MINUTES = 20


def query(conn, sql, default=0):
    try:
        row = conn.execute(sql).fetchone()
        return row[0] if row and row[0] is not None else default
    except sqlite3.Error:
        return default


def main():
    now = datetime.now()
    ts = now.strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=10)
    except sqlite3.Error as exc:
        print(f"[{ts}] ✗ cannot open {DB}: {exc}", file=sys.stderr)
        return 1

    with conn:
        # Live throughput, measured from row timestamps rather than from
        # whenever this script last happened to run.
        last_hour = query(conn, """
            SELECT COUNT(*) FROM link_deployment_queue
            WHERE created_at > datetime('now', '-1 hour')
        """)
        last_15m = query(conn, """
            SELECT COUNT(*) FROM link_deployment_queue
            WHERE created_at > datetime('now', '-15 minutes')
        """)
        pending = query(conn, """
            SELECT COUNT(*) FROM link_deployment_queue WHERE status = 'pending'
        """)
        minutes_idle = query(conn, """
            SELECT CAST((julianday('now') - julianday(MAX(created_at))) * 1440 AS INT)
            FROM link_deployment_queue
        """, default=99999)
        deployed_total = query(conn, """
            SELECT COUNT(*) FROM link_deployment_queue WHERE status = 'deployed'
        """)

    # 15-minute rate is the responsive signal; the hourly count is context.
    rate = last_15m * 4.0
    efficiency = min(100.0, (rate / TARGET_LINKS_PER_HOUR) * 100)

    if minutes_idle >= STALL_MINUTES:
        phase, status = 'stalled', '✗'
    elif pending == 0 and last_hour == 0:
        phase, status = 'idle', '·'
    else:
        phase, status = 'discovering', '✓'

    log_line = (
        f"[{ts}] {status} Phase: {phase:12s} | "
        f"Links: {last_15m:4d}/15m ({rate:5.0f}/h) | "
        f"1h: {last_hour:5d} | pending: {pending:5d} | "
        f"Efficiency: {efficiency:5.1f}%"
    )
    print(log_line)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / 'blitz_efficiency.log', 'a') as f:
        f.write(log_line + '\n')

    # Alert only on a real stall: nothing queued for STALL_MINUTES. A low rate
    # during a quiet stretch is normal and must not page anyone, or the alert
    # gets ignored and a genuine stall looks identical to noise.
    if phase == 'stalled':
        alert = (
            f"[{ts}] ⚠️  STALLED: no links queued in {minutes_idle} minutes "
            f"(threshold {STALL_MINUTES}). Check: ps aux | grep discovery_daemon; "
            f"tail logs/discovery_daemon.log\n"
        )
        with open(ALERT_FILE, 'a') as f:
            f.write(alert)
        print(alert, end='')
        return 1

    # Backlog only grows if the 4-hourly drain stopped. Worth surfacing, but it
    # is a different failure from the daemon dying.
    if pending > 5000:
        print(
            f"[{ts}] ⚠️  Queue backlog {pending}. deploy_queued_links.py runs "
            f"0 */4 * * *; check logs/deployment_cron.log.\n",
            end='',
        )

    if deployed_total:
        print(f"          lifetime deployed: {deployed_total}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
