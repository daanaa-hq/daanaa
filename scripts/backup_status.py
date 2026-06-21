#!/usr/bin/env python3
"""
Backup Status Monitor — tracks backup health and integrity.

Monitors:
- Last backup: age, size, integrity check result
- Next scheduled backup time
- Backup directory size and file count
- Alert if backup age > 24h or size < 1GB

Updates on request (called by unified dashboard) or cron.

Usage:
    python3 scripts/backup_status.py
    python3 scripts/backup_status.py --json  # Output as JSON
"""

import os
import sys
import json
import gzip
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Tuple

BACKUP_DIR = Path.home() / "meritgiving/backups"
DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
MONITOR_LOG = Path.home() / "meritgiving/logs/backup_status.log"

# Thresholds
MIN_BACKUP_SIZE_MB = 1000  # 1GB
MAX_BACKUP_AGE_HOURS = 24

# Color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def find_latest_backup() -> Tuple[Optional[Path], Optional[float]]:
    """Find the most recent backup file."""
    if not BACKUP_DIR.exists():
        return None, None

    backup_files = []

    for fpath in BACKUP_DIR.rglob("*"):
        if fpath.is_file() and (
            fpath.suffix in ['.gz', '.db', '.sql']
            or fpath.name.endswith('.db.gz')
            or fpath.name.endswith('.sql.gz')
        ):
            mtime = fpath.stat().st_mtime
            backup_files.append((fpath, mtime))

    if not backup_files:
        return None, None

    # Sort by modification time, most recent first
    backup_files.sort(key=lambda x: x[1], reverse=True)
    return backup_files[0][0], backup_files[0][1]

def check_backup_integrity(backup_path: Path) -> Tuple[bool, Optional[str]]:
    """Verify backup file integrity."""
    try:
        size_mb = backup_path.stat().st_size / 1024 / 1024

        # Check size
        if size_mb < MIN_BACKUP_SIZE_MB:
            return False, f"Too small ({size_mb:.1f}MB < {MIN_BACKUP_SIZE_MB}MB)"

        # Try to verify gzip compression if applicable
        if backup_path.suffix == '.gz':
            try:
                with gzip.open(backup_path, 'rb') as f:
                    # Read first 1MB to verify gzip integrity
                    f.read(1024 * 1024)
                return True, None
            except Exception as e:
                return False, f"Gzip integrity check failed: {e}"

        # For .db files, try to open with sqlite3
        if backup_path.suffix == '.db':
            try:
                conn = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True, timeout=2)
                conn.execute("SELECT COUNT(*) FROM sqlite_master")
                conn.close()
                return True, None
            except Exception as e:
                return False, f"SQLite integrity check failed: {e}"

        return True, None

    except Exception as e:
        return False, f"Error: {e}"

def get_backup_age_hours(mtime: float) -> float:
    """Get backup age in hours."""
    current_time = datetime.now(timezone.utc).timestamp()
    age_seconds = current_time - mtime
    return age_seconds / 3600

def calculate_next_backup_time() -> str:
    """Estimate next backup time based on typical schedule."""
    # Typical schedule: daily at 02:00 UTC
    now = datetime.now(timezone.utc)
    next_backup = now.replace(hour=2, minute=0, second=0, microsecond=0)

    if next_backup <= now:
        next_backup += timedelta(days=1)

    return next_backup.isoformat()

def get_backup_dir_stats() -> Dict[str, any]:
    """Get statistics about backup directory."""
    stats = {
        "file_count": 0,
        "total_size_gb": 0.0,
        "oldest_backup": None,
        "newest_backup": None,
    }

    if not BACKUP_DIR.exists():
        return stats

    backup_files = []

    for fpath in BACKUP_DIR.rglob("*"):
        if fpath.is_file():
            stats["file_count"] += 1
            stats["total_size_gb"] += fpath.stat().st_size / 1024 / 1024 / 1024
            mtime = fpath.stat().st_mtime

            if stats["newest_backup"] is None or mtime > stats["newest_backup"]:
                stats["newest_backup"] = mtime

            if stats["oldest_backup"] is None or mtime < stats["oldest_backup"]:
                stats["oldest_backup"] = mtime

    return stats

def format_time_delta(seconds: float) -> str:
    """Format time delta in human-readable form."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        return f"{hours}h {mins}m"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        return f"{days}d {hours}h"

def get_status_color(ok: bool) -> str:
    """Determine status color."""
    return Colors.GREEN if ok else Colors.RED

def check_backup_status() -> Tuple[bool, Dict[str, any]]:
    """Perform comprehensive backup status check."""
    status = {
        "backup_found": False,
        "backup_path": None,
        "backup_size_mb": 0.0,
        "backup_age_hours": 0.0,
        "backup_age_text": "unknown",
        "integrity_ok": False,
        "integrity_error": None,
        "age_ok": False,
        "size_ok": False,
        "next_backup": calculate_next_backup_time(),
        "dir_stats": get_backup_dir_stats(),
        "overall_ok": False,
    }

    backup_path, mtime = find_latest_backup()

    if not backup_path:
        status["overall_ok"] = False
        return False, status

    status["backup_found"] = True
    status["backup_path"] = str(backup_path)
    status["backup_size_mb"] = backup_path.stat().st_size / 1024 / 1024
    status["backup_age_hours"] = get_backup_age_hours(mtime)
    status["backup_age_text"] = format_time_delta(status["backup_age_hours"] * 3600)

    # Check age
    status["age_ok"] = status["backup_age_hours"] <= MAX_BACKUP_AGE_HOURS

    # Check size
    status["size_ok"] = status["backup_size_mb"] >= MIN_BACKUP_SIZE_MB

    # Check integrity
    integrity_ok, error = check_backup_integrity(backup_path)
    status["integrity_ok"] = integrity_ok
    status["integrity_error"] = error

    # Overall status
    status["overall_ok"] = status["age_ok"] and status["size_ok"] and status["integrity_ok"]

    return status["overall_ok"], status

def display_backup_status(status_data: Dict, log_only: bool = False):
    """Display backup status."""
    ok, status = status_data if isinstance(status_data, tuple) else (status_data.get("overall_ok"), status_data)

    output = []
    output.append("\n" + "=" * 70)
    output.append(f"{Colors.BOLD}Backup Status Monitor{Colors.RESET}")
    output.append("=" * 70)

    output.append(f"Timestamp:        {datetime.now(timezone.utc).isoformat()}")
    output.append("")

    if not status.get("backup_found"):
        output.append(f"{Colors.RED}✗ No backup found{Colors.RESET}")
    else:
        backup_path = status.get("backup_path")
        size_mb = status.get("backup_size_mb", 0)
        age_hours = status.get("backup_age_hours", 0)
        age_text = status.get("backup_age_text", "unknown")
        integrity_ok = status.get("integrity_ok", False)
        age_ok = status.get("age_ok", False)
        size_ok = status.get("size_ok", False)

        output.append(f"Latest backup:    {Path(backup_path).name}")
        output.append(f"Location:         {backup_path}")
        output.append("")

        # Size check
        size_color = Colors.GREEN if size_ok else Colors.RED
        output.append(f"Size:             {size_color}{size_mb:.1f}MB / {MIN_BACKUP_SIZE_MB}MB{Colors.RESET}")

        # Age check
        age_color = Colors.GREEN if age_ok else Colors.RED
        output.append(f"Age:              {age_color}{age_text} ({age_hours:.1f}h){Colors.RESET}")

        # Integrity check
        integrity_color = Colors.GREEN if integrity_ok else Colors.RED
        integrity_text = "✓ OK" if integrity_ok else "✗ FAILED"
        output.append(f"Integrity:        {integrity_color}{integrity_text}{Colors.RESET}")

        if status.get("integrity_error"):
            output.append(f"  Error:          {Colors.RED}{status['integrity_error']}{Colors.RESET}")

        output.append("")

    # Directory stats
    dir_stats = status.get("dir_stats", {})
    if dir_stats.get("file_count", 0) > 0:
        output.append(f"Backup directory:")
        output.append(f"  Files:          {dir_stats['file_count']}")
        output.append(f"  Total size:     {dir_stats['total_size_gb']:.2f}GB")

    output.append("")
    output.append(f"Next scheduled:   {status.get('next_backup', 'unknown')}")

    # Overall status
    overall_ok = status.get("overall_ok", False)
    status_text = f"{Colors.GREEN}✓ HEALTHY{Colors.RESET}" if overall_ok else f"{Colors.RED}✗ UNHEALTHY{Colors.RESET}"
    output.append(f"Overall status:   {status_text}")

    output.append("=" * 70 + "\n")

    msg = "\n".join(output)

    if not log_only:
        print(msg, flush=True)

    log_message(msg, level="STATUS")

def log_message(msg: str, level: str = "INFO"):
    """Log to file."""
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] [{level}] {msg}"

    try:
        MONITOR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(MONITOR_LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backup Status Monitor")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--log-only", action="store_true", help="Log to file only, no stdout")
    args = parser.parse_args()

    ok, status = check_backup_status()

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        display_backup_status((ok, status), log_only=args.log_only)

    sys.exit(0 if ok else 1)
