#!/usr/bin/env python3
"""
Cron Job Monitor — tracks cron job health and last run status.

Monitors log files for:
- health_check: API health monitoring
- backup_verify: Backup integrity verification
- cleanup_stale: Stale file cleanup
- db_optimize: Database optimization

For each job:
- Last run time
- Last run status (success/failed)
- Next scheduled run time
- Alert if job overdue (hasn't run in 2x scheduled interval)

Updates on request (called by unified dashboard) or independently.

Usage:
    python3 scripts/cron_job_monitor.py
    python3 scripts/cron_job_monitor.py --json
"""

import os
import sys
import json
import re
import gzip
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Tuple

LOG_DIR = Path.home() / "meritgiving/logs"
MONITOR_LOG = Path.home() / "meritgiving/logs/cron_monitor.log"

# Cron job definitions
CRON_JOBS = {
    "health_check": {
        "log_file": "health_check.log",
        "schedule": "every 5 minutes",
        "interval_minutes": 5,
    },
    "backup_verify": {
        "log_file": "backup_alert.log",
        "schedule": "daily at 03:00 UTC",
        "interval_minutes": 1440,
    },
    "cleanup_stale": {
        "log_file": "cleanup_stale.log",
        "schedule": "daily at 04:00 UTC",
        "interval_minutes": 1440,
    },
    "db_optimize": {
        "log_file": "db_optimize.log",
        "schedule": "daily at 05:00 UTC",
        "interval_minutes": 1440,
    },
    "precompute_orgs": {
        "log_file": "precompute_orgs.log",
        "schedule": "weekly (Sunday 06:00 UTC)",
        "interval_minutes": 10080,
    },
}

# Color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def open_log_file(log_path: Path) -> Optional[str]:
    """Open log file, handling both plain and gzipped files."""
    if not log_path.exists():
        return None

    try:
        if log_path.suffix == '.gz':
            with gzip.open(log_path, 'rt', encoding='utf-8', errors='ignore') as f:
                return f.read()
        else:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        log_message(f"Error reading {log_path}: {e}", level="ERROR")
        return None

def parse_log_for_status(log_content: str) -> Tuple[Optional[datetime], Optional[str]]:
    """Extract last run time and status from log."""
    if not log_content:
        return None, None

    lines = log_content.split('\n')

    # Look for last entry with timestamp and status
    for line in reversed(lines):
        if not line.strip():
            continue

        # Try to extract ISO timestamp
        iso_match = re.search(r'\[(\d{4}-\d{2}-\d{2}T[\d:\.]+\+\d{2}:\d{2})\]', line)

        if iso_match:
            try:
                timestamp_str = iso_match.group(1)
                timestamp = datetime.fromisoformat(timestamp_str)

                # Determine status from log line
                status = "UNKNOWN"
                if "OK" in line or "success" in line.lower() or "passed" in line.lower():
                    status = "SUCCESS"
                elif "ERROR" in line or "FAILED" in line or "failed" in line.lower():
                    status = "FAILED"
                elif "ALERT" in line or "WARNING" in line.lower():
                    status = "WARNING"

                return timestamp, status
            except ValueError:
                continue

    return None, None

def get_job_status(job_name: str, job_config: Dict) -> Dict[str, any]:
    """Get status for a specific cron job."""
    log_file = job_config.get("log_file")
    log_path = LOG_DIR / log_file

    status = {
        "job_name": job_name,
        "log_file": log_file,
        "schedule": job_config.get("schedule"),
        "interval_minutes": job_config.get("interval_minutes"),
        "log_found": log_path.exists(),
        "last_run": None,
        "last_status": None,
        "age_minutes": None,
        "overdue": False,
        "last_status_color": Colors.BLUE,
    }

    if not log_path.exists():
        status["last_status"] = "NO LOG"
        status["last_status_color"] = Colors.YELLOW
        return status

    log_content = open_log_file(log_path)
    if not log_content:
        status["last_status"] = "UNREADABLE"
        status["last_status_color"] = Colors.RED
        return status

    last_run, last_status = parse_log_for_status(log_content)

    if last_run:
        status["last_run"] = last_run.isoformat()
        status["last_status"] = last_status
        status["age_minutes"] = int(
            (datetime.now(timezone.utc) - last_run).total_seconds() / 60
        )

        # Check if overdue (no run in 2x interval)
        max_age_minutes = job_config.get("interval_minutes", 1440) * 2
        status["overdue"] = status["age_minutes"] > max_age_minutes

        # Set color based on status
        if last_status == "SUCCESS" and not status["overdue"]:
            status["last_status_color"] = Colors.GREEN
        elif last_status == "WARNING" or status["overdue"]:
            status["last_status_color"] = Colors.YELLOW
        elif last_status == "FAILED":
            status["last_status_color"] = Colors.RED

    return status

def calculate_next_run(last_run: Optional[datetime], interval_minutes: int) -> str:
    """Calculate next scheduled run time."""
    if not last_run:
        return "unknown"

    next_run = last_run + timedelta(minutes=interval_minutes)
    return next_run.isoformat()

def format_time_delta(minutes: int) -> str:
    """Format time delta in human-readable form."""
    if minutes < 60:
        return f"{minutes}m ago"
    elif minutes < 1440:
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m ago"
    else:
        days = minutes // 1440
        hours = (minutes % 1440) // 60
        return f"{days}d {hours}h ago"

def check_all_cron_jobs() -> Dict[str, Dict]:
    """Check status of all cron jobs."""
    jobs_status = {}

    for job_name, job_config in CRON_JOBS.items():
        jobs_status[job_name] = get_job_status(job_name, job_config)

    return jobs_status

def display_cron_status(jobs_status: Dict, log_only: bool = False):
    """Display cron job status."""
    output = []
    output.append("\n" + "=" * 80)
    output.append(f"{Colors.BOLD}Cron Job Monitor{Colors.RESET}")
    output.append("=" * 80)

    output.append(f"Timestamp:        {datetime.now(timezone.utc).isoformat()}")
    output.append("")

    all_healthy = True

    for job_name, status in jobs_status.items():
        job_color = Colors.GREEN

        if status["last_status"] == "FAILED":
            job_color = Colors.RED
            all_healthy = False
        elif status["overdue"]:
            job_color = Colors.RED
            all_healthy = False
        elif status["last_status"] == "WARNING":
            job_color = Colors.YELLOW

        output.append(f"{job_color}[{status['last_status']}]{Colors.RESET} {job_name}")
        output.append(f"  Schedule:       {status['schedule']}")
        output.append(f"  Log file:       {status['log_file']}")

        if status["last_run"]:
            age_text = format_time_delta(status["age_minutes"])
            output.append(f"  Last run:       {status['last_run']} ({age_text})")

            if status["overdue"]:
                output.append(f"  {Colors.RED}⚠ OVERDUE — not run in {status['age_minutes']}min!{Colors.RESET}")

            if status["last_status"] == "FAILED":
                output.append(f"  {Colors.RED}⚠ Last run FAILED{Colors.RESET}")

            next_run = calculate_next_run(
                datetime.fromisoformat(status["last_run"]),
                status["interval_minutes"]
            )
            output.append(f"  Next run:       {next_run}")
        else:
            output.append(f"  Last run:       {Colors.YELLOW}Not found{Colors.RESET}")

        output.append("")

    # Summary
    output.append("=" * 80)
    if all_healthy:
        output.append(f"Overall Status:   {Colors.GREEN}✓ ALL HEALTHY{Colors.RESET}")
    else:
        output.append(f"Overall Status:   {Colors.RED}✗ ISSUES DETECTED{Colors.RESET}")
    output.append("=" * 80 + "\n")

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

    parser = argparse.ArgumentParser(description="Cron Job Monitor")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--log-only", action="store_true", help="Log to file only, no stdout")
    args = parser.parse_args()

    jobs_status = check_all_cron_jobs()

    if args.json:
        # Convert datetime objects to strings for JSON serialization
        json_output = {}
        for job_name, status in jobs_status.items():
            json_status = status.copy()
            json_status.pop("last_status_color", None)  # Remove color code
            json_output[job_name] = json_status

        print(json.dumps(json_output, indent=2))
    else:
        display_cron_status(jobs_status, log_only=args.log_only)
