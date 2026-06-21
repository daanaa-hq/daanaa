#!/usr/bin/env python3
"""
Phase 4 Progress Monitor — real-time tracking of semantic verification pipeline.

Reads `/tmp/phase4_progress.log` and displays:
- Candidates processed (cumulative)
- Verified count (matches above similarity threshold)
- Processing speed (embeddings/min)
- Estimated time to completion
- GPU status and alerts

Updates every 30 seconds to stdout + log file.
Alert if speed drops below 10 embeddings/min (GPU stalled).

Usage:
    python3 scripts/phase4_monitor.py
    python3 scripts/phase4_monitor.py --log-only  # Write to log, no stdout
"""

import os
import sys
import json
import time
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple

PROGRESS_LOG = Path("/tmp/phase4_progress.log")
MONITOR_LOG = Path.home() / "meritgiving/logs/phase4_monitor.log"
CHECKPOINT_PATH = Path.home() / "meritgiving/logs/phase4_checkpoint.json"

# Config
UPDATE_INTERVAL = 30  # seconds
MIN_SPEED_THRESHOLD = 10  # embeddings/min
ALERT_RESPONSE_THRESHOLD = 5 * 60  # 5 minutes without progress

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def parse_progress_log() -> dict:
    """Parse Phase 4 progress log and extract metrics."""
    metrics = {
        "processed": 0,
        "verified": 0,
        "fetched": 0,
        "embed_errors": 0,
        "last_update": None,
        "start_time": None,
        "lines_count": 0,
        "latest_line": None,
    }

    if not PROGRESS_LOG.exists():
        return metrics

    try:
        with open(PROGRESS_LOG, "r") as f:
            lines = f.readlines()
            metrics["lines_count"] = len(lines)

            if lines:
                metrics["latest_line"] = lines[-1].strip()

            for line in lines:
                # Extract timestamps and counts
                if "Processed:" in line:
                    match = re.search(r"Processed:\s*(\d+)", line)
                    if match:
                        metrics["processed"] = int(match.group(1))

                if "Verified:" in line:
                    match = re.search(r"Verified:\s*(\d+)", line)
                    if match:
                        metrics["verified"] = int(match.group(1))

                if "Fetched:" in line:
                    match = re.search(r"Fetched:\s*(\d+)", line)
                    if match:
                        metrics["fetched"] = int(match.group(1))

                if "Embed errors:" in line:
                    match = re.search(r"Embed errors:\s*(\d+)", line)
                    if match:
                        metrics["embed_errors"] = int(match.group(1))

                # Extract timestamp from ISO format log lines
                if metrics["latest_line"] and not metrics["last_update"]:
                    match = re.search(r"\[(\d{4}-\d{2}-\d{2}T[\d:\.]+\+\d{2}:\d{2})\]", line)
                    if match:
                        metrics["last_update"] = match.group(1)

                if "Starting" in line and not metrics["start_time"]:
                    match = re.search(r"\[(\d{4}-\d{2}-\d{2}T[\d:\.]+\+\d{2}:\d{2})\]", line)
                    if match:
                        metrics["start_time"] = match.group(1)

    except Exception as e:
        log_message(f"Error parsing progress log: {e}", level="ERROR")

    return metrics

def load_checkpoint() -> Optional[dict]:
    """Load Phase 4 checkpoint if exists."""
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH) as f:
                return json.load(f)
        except Exception as e:
            log_message(f"Checkpoint read error: {e}", level="WARNING")
    return None

def calculate_eta(processed: int, target: int = 500000) -> Optional[str]:
    """Estimate time to completion based on current progress."""
    checkpoint = load_checkpoint()
    if not checkpoint or "timestamp" not in checkpoint:
        return None

    try:
        last_checkpoint_time = datetime.fromisoformat(checkpoint["timestamp"])
        elapsed_secs = (datetime.now(timezone.utc) - last_checkpoint_time).total_seconds()

        if elapsed_secs > 0 and processed > 0:
            speed = processed / elapsed_secs
            remaining = target - processed
            eta_secs = remaining / speed if speed > 0 else 0
            eta_time = datetime.now(timezone.utc) + timedelta(seconds=eta_secs)
            return eta_time.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        pass

    return None

def calculate_speed(metrics: dict) -> float:
    """Calculate processing speed in embeddings/min."""
    checkpoint = load_checkpoint()
    if not checkpoint or "timestamp" not in checkpoint:
        return 0.0

    try:
        last_checkpoint_time = datetime.fromisoformat(checkpoint["timestamp"])
        elapsed_secs = (datetime.now(timezone.utc) - last_checkpoint_time).total_seconds()

        if elapsed_secs > 0:
            return (metrics["processed"] * 60) / elapsed_secs
    except Exception:
        pass

    return 0.0

def get_status_color(speed: float) -> str:
    """Determine status color based on speed."""
    if speed < MIN_SPEED_THRESHOLD:
        return Colors.RED
    elif speed < MIN_SPEED_THRESHOLD * 2:
        return Colors.YELLOW
    else:
        return Colors.GREEN

def log_message(msg: str, level: str = "INFO"):
    """Log to file and optionally stdout."""
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] [{level}] {msg}"

    # Always log to file
    try:
        MONITOR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(MONITOR_LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

def format_uptime(start_time: Optional[str]) -> str:
    """Format elapsed time from start."""
    if not start_time:
        return "unknown"

    try:
        start = datetime.fromisoformat(start_time)
        elapsed = datetime.now(timezone.utc) - start
        hours = elapsed.total_seconds() / 3600
        mins = (elapsed.total_seconds() % 3600) / 60

        if hours > 1:
            return f"{int(hours)}h {int(mins)}m"
        else:
            return f"{int(mins)}m {int(elapsed.total_seconds() % 60)}s"
    except Exception:
        return "unknown"

def display_dashboard(metrics: dict, log_only: bool = False):
    """Display Phase 4 dashboard."""
    speed = calculate_speed(metrics)
    status_color = get_status_color(speed)
    eta = calculate_eta(metrics["processed"])

    output = []
    output.append("\n" + "=" * 70)
    output.append(f"{Colors.BOLD}Phase 4 — Semantic Verification Progress{Colors.RESET}")
    output.append("=" * 70)

    output.append(f"Timestamp:        {datetime.now(timezone.utc).isoformat()}")
    output.append(f"Candidates proc:  {metrics['processed']:,} (fetched: {metrics['fetched']:,})")
    output.append(f"Verified matches: {metrics['verified']:,}")

    if metrics["processed"] > 0:
        match_rate = (metrics["verified"] / metrics["fetched"] * 100) if metrics["fetched"] > 0 else 0
        output.append(f"Match rate:       {match_rate:.1f}%")

    output.append(f"Embed errors:     {metrics['embed_errors']:,}")
    output.append(f"Uptime:           {format_uptime(metrics['start_time'])}")
    output.append("")
    output.append(f"Speed:            {status_color}{speed:.1f} embeddings/min{Colors.RESET}")

    if speed < MIN_SPEED_THRESHOLD:
        output.append(f"{Colors.RED}⚠ ALERT: GPU may be stalled (speed < {MIN_SPEED_THRESHOLD} e/min){Colors.RESET}")

    if eta:
        output.append(f"ETA:              {eta}")

    output.append("=" * 70 + "\n")

    msg = "\n".join(output)

    if not log_only:
        print(msg, flush=True)

    log_message(msg, level="STATUS")

def monitor_loop(log_only: bool = False):
    """Main monitoring loop."""
    log_message("Phase 4 monitor started", level="INFO")
    last_alert_time = 0

    while True:
        try:
            metrics = parse_progress_log()

            # Display dashboard
            display_dashboard(metrics, log_only=log_only)

            # Check for stalled GPU
            speed = calculate_speed(metrics)
            if speed < MIN_SPEED_THRESHOLD:
                current_time = time.time()
                if current_time - last_alert_time > ALERT_RESPONSE_THRESHOLD:
                    log_message(
                        f"ALERT: GPU stalled — speed {speed:.1f} < {MIN_SPEED_THRESHOLD} e/min",
                        level="ALERT"
                    )
                    last_alert_time = current_time
            else:
                last_alert_time = 0

            # Wait for next update
            time.sleep(UPDATE_INTERVAL)

        except KeyboardInterrupt:
            log_message("Monitor stopped by user", level="INFO")
            break
        except Exception as e:
            log_message(f"Monitor error: {e}", level="ERROR")
            time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 4 Progress Monitor")
    parser.add_argument("--log-only", action="store_true", help="Log to file only, no stdout")
    args = parser.parse_args()

    monitor_loop(log_only=args.log_only)
