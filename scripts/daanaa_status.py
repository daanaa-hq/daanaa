#!/usr/bin/env python3
"""
Daanaa Unified Status Dashboard — combined monitoring of all infrastructure.

Integrates:
- Phase 4 semantic verification progress
- API health (health endpoint, gunicorn memory, response times)
- Backup integrity and age
- Cron job execution (health_check, backup_verify, cleanup, optimize)

Updates every 30 seconds (or configurable interval).
Color-coded status indicators (green/yellow/red).
Runs as background service or one-off dashboard.

Usage:
    python3 scripts/daanaa_status.py                    # Interactive dashboard
    python3 scripts/daanaa_status.py --once             # One-time check
    python3 scripts/daanaa_status.py --log-only         # Log to file only
    systemctl start daanaa-status                       # Start as systemd service
    tail -f /var/log/daanaa/status.log                  # Watch live log
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

# Import monitoring modules
sys.path.insert(0, str(Path(__file__).parent))

# Colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

SCRIPTS_DIR = Path.home() / "meritgiving/scripts"
LOG_DIR = Path.home() / "meritgiving/logs"
MONITOR_LOG = Path("/var/log/daanaa/status.log")
UPDATE_INTERVAL = 30  # seconds

def run_monitor_script(script_name: str, args: list = None) -> Dict:
    """Run a monitoring script and capture output as JSON."""
    if args is None:
        args = []

    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        return {"error": f"Script not found: {script_name}"}

    try:
        cmd = ["python3", str(script_path), "--json"] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"error": f"Invalid JSON from {script_name}"}
        else:
            return {"error": f"{script_name} failed: {result.stderr}"}

    except subprocess.TimeoutExpired:
        return {"error": f"{script_name} timed out"}
    except Exception as e:
        return {"error": f"Error running {script_name}: {e}"}

def get_phase4_status() -> Dict:
    """Get Phase 4 semantic verification status."""
    return run_monitor_script("phase4_monitor.py")

def get_api_health() -> Dict:
    """Get API health status (from subprocess call)."""
    # API health doesn't support --json, so we parse logs instead
    health_log = LOG_DIR / "api_health.log"

    status = {
        "status": "unknown",
        "last_check": None,
        "health_ok": None,
        "memory_ok": None,
    }

    if health_log.exists():
        try:
            with open(health_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    if "OK" in last_line:
                        status["status"] = "healthy"
                    elif "FAILED" in last_line:
                        status["status"] = "unhealthy"
        except Exception:
            pass

    return status

def get_backup_status() -> Dict:
    """Get backup integrity status."""
    return run_monitor_script("backup_status.py")

def get_cron_status() -> Dict:
    """Get cron job execution status."""
    return run_monitor_script("cron_job_monitor.py")

def get_system_status() -> Dict:
    """Get system-level status."""
    import psutil

    status = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "uptime_seconds": int(time.time() - psutil.boot_time()),
    }

    return status

def format_status_line(label: str, value: str, ok: bool = None) -> str:
    """Format a status line with optional color."""
    if ok is None:
        color = Colors.BLUE
    elif ok:
        color = Colors.GREEN
    else:
        color = Colors.RED

    status_text = f"{color}✓{Colors.RESET}" if ok else f"{color}✗{Colors.RESET}" if ok is False else ""

    return f"{label:<30} {status_text} {value}"

def display_unified_dashboard(log_only: bool = False):
    """Display unified status dashboard."""
    phase4 = get_phase4_status()
    api = get_api_health()
    backup = get_backup_status()
    cron = get_cron_status()
    system = get_system_status()

    output = []
    output.append("\n" + "=" * 80)
    output.append(f"{Colors.BOLD}{Colors.BLUE}Daanaa Infrastructure Status{Colors.RESET}")
    output.append("=" * 80)

    output.append(f"{Colors.DIM}Updated: {datetime.now(timezone.utc).isoformat()}{Colors.RESET}")
    output.append("")

    # System Status
    output.append(f"{Colors.BOLD}System Status{Colors.RESET}")
    output.append("-" * 80)

    system_ok = (
        system.get("cpu_percent", 100) < 80 and
        system.get("memory_percent", 100) < 85 and
        system.get("disk_percent", 100) < 90
    )
    output.append(format_status_line(
        "CPU / Memory / Disk",
        f"{system.get('cpu_percent', 0):.0f}% / {system.get('memory_percent', 0):.0f}% / {system.get('disk_percent', 0):.0f}%",
        system_ok
    ))

    uptime_hours = system.get("uptime_seconds", 0) / 3600
    output.append(f"{'Uptime':<30} {uptime_hours:.1f} hours")
    output.append("")

    # Phase 4 Status
    output.append(f"{Colors.BOLD}Phase 4 Semantic Verification{Colors.RESET}")
    output.append("-" * 80)

    if "error" in phase4:
        output.append(f"{Colors.YELLOW}Not running or no progress file{Colors.RESET}")
    else:
        processed = phase4.get("processed", 0)
        verified = phase4.get("verified", 0)
        output.append(f"{'Candidates processed':<30} {processed:,}")
        output.append(f"{'Verified matches':<30} {verified:,}")

    output.append("")

    # API Health
    output.append(f"{Colors.BOLD}API Health{Colors.RESET}")
    output.append("-" * 80)

    api_ok = api.get("status") == "healthy"
    status_text = f"{Colors.GREEN}Healthy{Colors.RESET}" if api_ok else f"{Colors.RED}Unhealthy{Colors.RESET}"
    output.append(f"{'Overall status':<30} {status_text}")
    output.append("")

    # Backup Status
    output.append(f"{Colors.BOLD}Backup Status{Colors.RESET}")
    output.append("-" * 80)

    if "error" in backup:
        output.append(f"{Colors.RED}Error: {backup['error']}{Colors.RESET}")
    else:
        backup_ok = backup.get("overall_ok", False)
        status_text = f"{Colors.GREEN}✓ Healthy{Colors.RESET}" if backup_ok else f"{Colors.RED}✗ Unhealthy{Colors.RESET}"
        output.append(f"{'Overall status':<30} {status_text}")

        if backup.get("backup_found"):
            size_mb = backup.get("backup_size_mb", 0)
            age_hours = backup.get("backup_age_hours", 0)
            output.append(f"{'Size':<30} {size_mb:.1f} MB")
            output.append(f"{'Age':<30} {age_hours:.1f} hours")

    output.append("")

    # Cron Jobs
    output.append(f"{Colors.BOLD}Cron Jobs{Colors.RESET}")
    output.append("-" * 80)

    if isinstance(cron, dict) and "error" not in cron:
        for job_name, job_status in cron.items():
            if isinstance(job_status, dict):
                last_status = job_status.get("last_status", "UNKNOWN")
                overdue = job_status.get("overdue", False)

                if overdue:
                    color = Colors.RED
                    status_indicator = "✗"
                elif last_status == "SUCCESS":
                    color = Colors.GREEN
                    status_indicator = "✓"
                elif last_status == "FAILED":
                    color = Colors.RED
                    status_indicator = "✗"
                else:
                    color = Colors.YELLOW
                    status_indicator = "○"

                age_text = ""
                if job_status.get("age_minutes"):
                    age_min = job_status.get("age_minutes", 0)
                    if age_min < 60:
                        age_text = f" ({age_min}m ago)"
                    else:
                        age_text = f" ({age_min // 60}h ago)"

                output.append(f"{color}{status_indicator}{Colors.RESET} {job_name:<25} {last_status}{age_text}")
    else:
        output.append(f"{Colors.YELLOW}Unable to retrieve cron status{Colors.RESET}")

    output.append("=" * 80 + "\n")

    msg = "\n".join(output)

    if not log_only:
        print(msg, flush=True)

    # Log to file
    log_message(msg, level="STATUS")

def log_message(msg: str, level: str = "INFO"):
    """Log to file."""
    ts = datetime.now(timezone.utc).isoformat()

    # Ensure log directory exists
    log_dir = MONITOR_LOG.parent
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fallback to home directory if /var/log not writable
        pass

    # Try system log first, fall back to home directory
    log_path = MONITOR_LOG
    if not log_dir.exists() or not os.access(log_dir, os.W_OK):
        log_path = Path.home() / "meritgiving/logs/daanaa_status.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        line = f"[{ts}] [{level}] {msg}\n"
        with open(log_path, "a") as f:
            f.write(line)
    except Exception as e:
        # Silent failure to avoid noise
        pass

def monitor_loop(once: bool = False, log_only: bool = False):
    """Main monitoring loop."""
    log_message("Unified dashboard started", level="INFO")

    try:
        if once:
            display_unified_dashboard(log_only=log_only)
        else:
            while True:
                try:
                    display_unified_dashboard(log_only=log_only)
                    time.sleep(UPDATE_INTERVAL)
                except KeyboardInterrupt:
                    log_message("Dashboard stopped by user", level="INFO")
                    break

    except Exception as e:
        log_message(f"Dashboard error: {e}", level="ERROR")
        raise

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Daanaa Unified Status Dashboard")
    parser.add_argument("--once", action="store_true", help="One-time check only")
    parser.add_argument("--log-only", action="store_true", help="Log to file only, no stdout")
    args = parser.parse_args()

    monitor_loop(once=args.once, log_only=args.log_only)
