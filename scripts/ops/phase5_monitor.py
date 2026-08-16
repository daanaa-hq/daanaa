#!/usr/bin/env python3
"""
Phase 5 Monitor — Real-time progress tracking for mission & cause backfill.

Displays:
- Orgs processed (cumulative)
- Missions generated (success count)
- Processing speed (orgs/min)
- Estimated time to completion
- LLM health and errors
- Database lock counts
- Cause tag distribution (top 5)

Updates every 30 seconds to stdout + log file.
Alert if speed drops below 1 org/min (LLM stalled).

Usage:
    python3 scripts/phase5_monitor.py
    python3 scripts/phase5_monitor.py --log-only
    python3 scripts/phase5_monitor.py --interval 15
"""

import os
import sys
import json
import time
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple
from collections import Counter

PROGRESS_LOG = Path("/tmp/phase5_progress.log")
MONITOR_LOG = Path.home() / "meritgiving" / "logs" / "phase5_monitor.log"
CHECKPOINT_PATH = Path.home() / "meritgiving" / "logs" / "phase5_checkpoint.json"
DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"

# Config
UPDATE_INTERVAL = 30  # seconds
MIN_SPEED_THRESHOLD = 1.0  # orgs/min
STALL_THRESHOLD = 5 * 60  # 5 minutes without progress

# Color codes
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def parse_progress_log() -> dict:
    """Parse Phase 5 progress log and extract metrics."""
    metrics = {
        "processed": 0,
        "generated": 0,
        "skipped": 0,
        "errors": 0,
        "last_update": None,
        "start_time": None,
        "lines_count": 0,
        "latest_line": None,
        "batches": 0,
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
                # Extract start time
                if "Phase 5 Mission & Cause Backfill starting" in line:
                    match = re.search(r"\[(.*?)\]", line)
                    if match:
                        metrics["start_time"] = match.group(1)

                # Extract batch progress
                if "Batch" in line and "Processing" in line:
                    match = re.search(r"Batch (\d+):", line)
                    if match:
                        metrics["batches"] = int(match.group(1))

                # Extract final stats
                if "Processed:" in line:
                    match = re.search(r"Processed:\s*(\d+)", line)
                    if match:
                        metrics["processed"] = int(match.group(1))

                if "Generated:" in line:
                    match = re.search(r"Generated:\s*(\d+)", line)
                    if match:
                        metrics["generated"] = int(match.group(1))

                if "Skipped:" in line:
                    match = re.search(r"Skipped:\s*(\d+)", line)
                    if match:
                        metrics["skipped"] = int(match.group(1))

                if "Errors:" in line:
                    match = re.search(r"Errors:\s*(\d+)", line)
                    if match:
                        metrics["errors"] = int(match.group(1))

    except Exception as e:
        print(f"Error parsing log: {e}", file=sys.stderr)

    return metrics


def load_checkpoint() -> dict:
    """Load latest checkpoint."""
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {"generated_count": 0, "skipped_count": 0, "processed_eins": []}


def get_cause_distribution() -> dict:
    """Get distribution of cause tags from database."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.execute(
            "SELECT cause_tags FROM registry_enriched WHERE cause_tags IS NOT NULL LIMIT 10000"
        )
        all_causes = []
        for row in cursor.fetchall():
            try:
                tags = json.loads(row[0])
                if isinstance(tags, list):
                    all_causes.extend(tags)
            except Exception:
                pass
        conn.close()

        if all_causes:
            counter = Counter(all_causes)
            return dict(counter.most_common(5))
    except Exception:
        pass
    return {}


def get_db_stats() -> dict:
    """Get database stats."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN mission IS NOT NULL THEN 1 ELSE 0 END) "
            "FROM registry_enriched"
        )
        total, with_mission = cursor.fetchone()
        conn.close()
        return {"total_orgs": total, "with_mission": with_mission or 0}
    except Exception:
        pass
    return {}


def format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    if seconds < 0:
        return "N/A"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main(log_only: bool = False, interval: int = UPDATE_INTERVAL) -> None:
    """Main monitor loop."""
    # Initialize log file
    MONITOR_LOG.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        line = f"[{ts}] {msg}"
        with open(MONITOR_LOG, "a") as f:
            f.write(line + "\n")
        if not log_only:
            print(line)

    log(f"Phase 5 Monitor started (interval={interval}s)")

    last_processed = 0
    last_time = time.time()
    stall_time = None

    try:
        while True:
            metrics = parse_progress_log()
            checkpoint = load_checkpoint()
            db_stats = get_db_stats()
            causes = get_cause_distribution()

            # Calculate speed
            now = time.time()
            elapsed = now - last_time
            processed_delta = metrics["processed"] - last_processed

            if elapsed > 0:
                speed = processed_delta / (elapsed / 60.0)  # orgs/min
            else:
                speed = 0.0

            # Detect stalls
            if processed_delta == 0:
                if stall_time is None:
                    stall_time = now
                stall_duration = now - stall_time
            else:
                stall_time = None
                stall_duration = 0

            # Format output
            lines = []
            lines.append("")
            lines.append(f"{Colors.BOLD}=== Phase 5 Progress ==={Colors.RESET}")

            if metrics.get("start_time"):
                start = datetime.fromisoformat(metrics["start_time"])
                elapsed_sec = (datetime.now(timezone.utc) - start).total_seconds()
                lines.append(f"Elapsed: {format_duration(elapsed_sec)}")

            lines.append(f"Processed: {metrics['processed']:,}")
            lines.append(f"Generated: {metrics['generated']:,}")
            lines.append(f"Skipped: {metrics['skipped']:,}")
            lines.append(f"Speed: {speed:.1f} orgs/min")

            # Alerts
            if speed < MIN_SPEED_THRESHOLD and metrics["processed"] > 0:
                lines.append(
                    f"{Colors.YELLOW}⚠ Slow speed warning{Colors.RESET} (< {MIN_SPEED_THRESHOLD} orgs/min)"
                )

            if stall_duration > STALL_THRESHOLD:
                lines.append(
                    f"{Colors.RED}⚠ Stalled for {int(stall_duration / 60)} min{Colors.RESET}"
                )

            if metrics["errors"] > 0:
                lines.append(f"{Colors.RED}Errors: {metrics['errors']:,}{Colors.RESET}")

            # Database stats
            if db_stats:
                lines.append("")
                lines.append(f"Database: {db_stats['total_orgs']:,} total, {db_stats['with_mission']:,} with mission")

            # Top causes
            if causes:
                lines.append("")
                lines.append("Top causes:")
                for cause, count in causes.items():
                    lines.append(f"  {cause}: {count:,}")

            lines.append("")
            if metrics.get("latest_line"):
                lines.append(f"Latest: {metrics['latest_line'][:100]}")

            # Print all lines
            output = "\n".join(lines)
            log(output)

            # Update tracking
            last_processed = metrics["processed"]
            last_time = now

            time.sleep(interval)

    except KeyboardInterrupt:
        log("Monitor stopped by user")
        sys.exit(0)
    except Exception as e:
        log(f"Monitor error: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 5 Progress Monitor")
    parser.add_argument("--log-only", action="store_true", help="Write to log only, no stdout")
    parser.add_argument(
        "--interval", type=int, default=UPDATE_INTERVAL, help="Update interval in seconds"
    )

    args = parser.parse_args()
    main(log_only=args.log_only, interval=args.interval)
