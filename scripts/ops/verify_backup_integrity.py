#!/usr/bin/env python3
"""
Backup integrity verification cron job
Checks: last backup exists, size > 1GB, modified < 24h ago
If failed: logs to backup_alert.log and optionally emails
"""
import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
BACKUP_DIR = os.path.expanduser("~/meritgiving/backups")
MIN_BACKUP_SIZE_MB = 1000  # 1GB
MAX_BACKUP_AGE_HOURS = 24
LOG_FILE = os.path.expanduser("~/meritgiving/logs/backup_alert.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def find_latest_backup():
    """Find the most recent backup file"""
    if not os.path.isdir(BACKUP_DIR):
        return None, None

    backup_files = []
    # Search recursively for backup files
    for root, dirs, files in os.walk(BACKUP_DIR):
        for f in files:
            # Accept .db.gz, .sql.gz, and .db files
            if f.endswith('.db.gz') or f.endswith('.sql.gz') or f.endswith('.db'):
                fpath = os.path.join(root, f)
                mtime = os.path.getmtime(fpath)
                backup_files.append((fpath, mtime))

    if not backup_files:
        return None, None

    # Sort by modification time, most recent first
    backup_files.sort(key=lambda x: x[1], reverse=True)
    return backup_files[0][0], backup_files[0][1]

def check_backup_integrity():
    """Check backup file size and age"""
    backup_path, mtime = find_latest_backup()

    if not backup_path:
        logger.error("CRITICAL: No backup files found in %s", BACKUP_DIR)
        return False, "No backup files found"

    # Check file size
    size_mb = os.path.getsize(backup_path) / 1024 / 1024
    if size_mb < MIN_BACKUP_SIZE_MB:
        msg = f"CRITICAL: Backup too small ({size_mb:.1f}MB < {MIN_BACKUP_SIZE_MB}MB): {backup_path}"
        logger.error(msg)
        return False, msg

    # Check age
    age_hours = (time.time() - mtime) / 3600
    if age_hours > MAX_BACKUP_AGE_HOURS:
        msg = f"CRITICAL: Backup too old ({age_hours:.1f}h > {MAX_BACKUP_AGE_HOURS}h): {backup_path}"
        logger.error(msg)
        return False, msg

    # All checks passed
    logger.info(
        "OK: Backup verified (%s, %.1f MB, %.1f hours old)",
        os.path.basename(backup_path),
        size_mb,
        age_hours
    )
    return True, None

def send_alert_email(error_message):
    """Send alert email to root@localhost (placeholder)"""
    try:
        # This is a placeholder for email integration
        # In production, use sendmail, postfix, or an API
        logger.info("Email alert would be sent: %s", error_message)
    except Exception as e:
        logger.warning("Failed to send email alert: %s", e)

def main():
    logger.info("=" * 70)
    logger.info("Backup integrity check started")
    logger.info("=" * 70)

    success, error_msg = check_backup_integrity()

    if not success:
        logger.error("Backup check FAILED: %s", error_msg)
        send_alert_email(error_msg)
        return 1

    logger.info("Backup check PASSED")
    return 0

if __name__ == '__main__':
    sys.exit(main())
