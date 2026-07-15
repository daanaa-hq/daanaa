#!/usr/bin/env python3
"""
Monitor discovery daemon health.

Tracks:
- Links discovered vs. verified (success rate)
- Error rate
- Queue depth
- Daemon uptime

Alerts if success rate drops below 25%.
"""

import sqlite3
import json
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler('/home/akbar/meritgiving/logs/discovery_health.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


def check_daemon_running():
    """Check if discovery daemon is running."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'discovery_daemon.py'],
            capture_output=True,
            text=True
        )
        return len(result.stdout.strip()) > 0
    except:
        return False


def get_discovery_stats(hours=24):
    """Get discovery stats from the last N hours."""
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()

    cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

    # Get queued links (successfully discovered + verified)
    cursor.execute("""
        SELECT COUNT(*) FROM link_deployment_queue
        WHERE created_at > ?
    """, (cutoff_time,))
    verified = cursor.fetchone()[0]

    # Get errors from logs (approximate from recent log entries)
    # This is a heuristic based on discovery_daemon.log
    try:
        log_file = Path.home() / 'meritgiving' / 'logs' / 'discovery_daemon.log'
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()[-1000:]  # Last 1000 lines
                discovered = len([l for l in lines if '✅' in l or '⚪' in l])
                errors = len([l for l in lines if '❌' in l])
        else:
            discovered = verified  # Fallback
            errors = 0
    except:
        discovered = verified
        errors = 0

    db.close()

    return {
        'verified': verified,
        'discovered': discovered if discovered > 0 else verified,
        'errors': errors,
        'success_rate': (verified / discovered * 100) if discovered > 0 else 0
    }


def get_queue_depth():
    """Get number of links waiting to be deployed."""
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM link_deployment_queue
        WHERE deployed_at IS NULL
    """)
    queue_depth = cursor.fetchone()[0]
    db.close()

    return queue_depth


def check_health():
    """Check daemon health. Alert if success rate < 25%."""
    logger.info("=" * 70)
    logger.info("🔍 DISCOVERY DAEMON HEALTH CHECK")
    logger.info("=" * 70)

    daemon_running = check_daemon_running()
    stats = get_discovery_stats(hours=24)
    queue_depth = get_queue_depth()

    logger.info(f"Daemon Status: {'🟢 RUNNING' if daemon_running else '🔴 NOT RUNNING'}")
    logger.info(f"Success Rate (24h): {stats['success_rate']:.1f}% ({stats['verified']}/{stats['discovered']})")
    logger.info(f"Errors (24h): {stats['errors']}")
    logger.info(f"Queue Depth: {queue_depth} links waiting to deploy")

    # Alert if below threshold
    THRESHOLD = 25
    if stats['success_rate'] < THRESHOLD and stats['discovered'] > 0:
        logger.critical("=" * 70)
        logger.critical(f"🚨 ALERT: Success rate {stats['success_rate']:.1f}% is below {THRESHOLD}% threshold")
        logger.critical("   Action: Contact founder for strategy adjustment")
        logger.critical("=" * 70)
        return False  # Unhealthy

    if not daemon_running:
        logger.critical("🚨 ALERT: Discovery daemon is not running")
        logger.critical("   Action: Restart with: nohup python3 scripts/discovery_daemon.py 100 > logs/discovery_daemon.log 2>&1 &")
        return False

    logger.info("✅ Daemon healthy")
    return True


if __name__ == '__main__':
    import sys
    healthy = check_health()
    sys.exit(0 if healthy else 1)
