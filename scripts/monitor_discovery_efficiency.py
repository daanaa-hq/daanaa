#!/usr/bin/env python3
"""
Discovery Efficiency Monitor — tracks pipeline throughput and resources.

Watches for efficiency drop to 80% of peak. When detected, signals for
optimization + reconnection.

Tracks:
1. Throughput (websites/hour, links/hour)
2. Resource utilization (CPU %, GPU memory, I/O)
3. Success rates (website verification %, link extraction %)
4. Combined efficiency score (0–100%)

When efficiency < 80% of peak:
- Writes alert to efficiency_alert.log
- Creates EFFICIENCY_THRESHOLD_BREACHED marker
- Continues running (no auto-stop)

Run continuously:
    python3 scripts/monitor_discovery_efficiency.py

Run as cron (every 30 minutes):
    */30 * * * * python3 scripts/monitor_discovery_efficiency.py >> logs/efficiency_monitor.log 2>&1
"""

import sqlite3
import json
import subprocess
import time
import psutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict

DB = Path.home() / "meritgiving/data/merit_registry.db"
LOG_DIR = Path.home() / "meritgiving/logs"
STATE_FILE = LOG_DIR / ".efficiency_state.json"
ALERT_FILE = LOG_DIR / "efficiency_alert.log"
THRESHOLD_MARKER = LOG_DIR / ".EFFICIENCY_THRESHOLD_BREACHED"

# Target: 80% of peak efficiency
EFFICIENCY_THRESHOLD = 80.0


@dataclass
class EfficiencyMetrics:
    """Efficiency snapshot."""
    timestamp: str
    websites_per_hour: float
    links_per_hour: float
    website_verify_success_rate: float
    link_extraction_success_rate: float
    cpu_percent: float
    gpu_memory_percent: float
    disk_io_percent: float
    combined_efficiency: float  # 0–100


def get_throughput_last_hour():
    """Query discovery stats from last hour."""
    db = sqlite3.connect(DB)
    cursor = db.cursor()

    # Websites discovered in last hour
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    cursor.execute(
        """
        SELECT COUNT(DISTINCT EIN) FROM registry_enriched
        WHERE website_checked_at > ?
    """,
        (one_hour_ago,),
    )
    websites_found = cursor.fetchone()[0] or 0

    # Links queued in last hour
    cursor.execute(
        """
        SELECT COUNT(*) FROM link_deployment_queue
        WHERE created_at > ?
    """,
        (one_hour_ago,),
    )
    links_queued = cursor.fetchone()[0] or 0

    # Website verification success rate (last 100 attempts)
    cursor.execute(
        """
        SELECT
          SUM(CASE WHEN website_status = 'ok' THEN 1 ELSE 0 END) as good,
          COUNT(*) as total
        FROM registry_enriched
        WHERE website_checked_at IS NOT NULL
        ORDER BY website_checked_at DESC LIMIT 100
    """
    )
    result = cursor.fetchone()
    website_success = (result[0] / result[1] * 100) if result[1] > 0 else 0

    # Link extraction success rate (last 100 orgs with links)
    cursor.execute(
        """
        SELECT
          SUM(CASE WHEN donate_url_status = 'beta' THEN 1 ELSE 0 END) as good,
          COUNT(*) as total
        FROM registry_enriched
        WHERE donate_url IS NOT NULL
        ORDER BY rowid DESC LIMIT 100
    """
    )
    result = cursor.fetchone()
    link_success = (result[0] / result[1] * 100) if result[1] > 0 else 0

    db.close()

    return {
        "websites_per_hour": websites_found,
        "links_per_hour": links_queued,
        "website_verify_success_rate": website_success,
        "link_extraction_success_rate": link_success,
    }


def get_resource_usage():
    """Get CPU, GPU, I/O utilization."""
    cpu_percent = psutil.cpu_percent(interval=1)

    # GPU memory (estimate from llama-server process)
    gpu_memory_percent = 0
    try:
        result = subprocess.run(
            ["pgrep", "-f", "llama-server"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.stdout:
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                try:
                    p = psutil.Process(int(pid))
                    mem = p.memory_info().rss / (1024**3)  # GB
                    # Assume 16GB system, llama uses up to ~12GB
                    gpu_memory_percent = (mem / 12) * 100
                    break
                except:
                    pass
    except:
        gpu_memory_percent = 0

    # Disk I/O (quick sample)
    try:
        io_before = psutil.disk_io_counters()
        time.sleep(0.1)
        io_after = psutil.disk_io_counters()
        # Rough: if reads/writes happening, high %; else low
        io_activity = (io_after.read_bytes + io_after.write_bytes) / (1024**2)  # MB
        disk_io_percent = min(100, io_activity / 10)  # Scale to 100%
    except:
        disk_io_percent = 0

    return {
        "cpu_percent": cpu_percent,
        "gpu_memory_percent": min(100, gpu_memory_percent),
        "disk_io_percent": disk_io_percent,
    }


def calculate_efficiency(metrics_dict):
    """
    Calculate combined efficiency (0–100%).

    Factors:
    - Throughput: websites_per_hour + links_per_hour (normalized)
    - Success rates: average of website + link success
    - Resource efficiency: inverse of utilization (lower is better for idle)

    Result: 0–100% where 100% = peak performance
    """
    throughput_score = min(
        100,
        ((metrics_dict["websites_per_hour"] / 10) * 50)
        + ((metrics_dict["links_per_hour"] / 20) * 50),
    )
    success_score = (
        metrics_dict["website_verify_success_rate"]
        + metrics_dict["link_extraction_success_rate"]
    ) / 2
    resource_score = 100 - (
        (
            metrics_dict["cpu_percent"]
            + metrics_dict["gpu_memory_percent"]
            + metrics_dict["disk_io_percent"]
        )
        / 3
    )

    # Weighted: 50% throughput, 30% success, 20% resources
    combined = (throughput_score * 0.5) + (success_score * 0.3) + (resource_score * 0.2)
    return min(100, max(0, combined))


def load_peak_efficiency():
    """Load peak efficiency baseline (or None if first run)."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                state = json.load(f)
                return state.get("peak_efficiency")
        except:
            pass
    return None


def save_state(peak_eff, current_metrics):
    """Save efficiency state to disk."""
    state = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "peak_efficiency": peak_eff,
        "latest_metrics": asdict(current_metrics),
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def alert_efficiency_drop(peak, current, threshold_value):
    """Log alert when efficiency drops below threshold."""
    with open(ALERT_FILE, "a") as f:
        f.write(
            f"[{datetime.now().isoformat()}] EFFICIENCY THRESHOLD BREACHED\n"
        )
        f.write(
            f"  Peak efficiency: {peak:.1f}%\n"
            f"  Current efficiency: {current:.1f}%\n"
            f"  Threshold: {threshold_value:.1f}%\n"
            f"  Action: Reconnect for optimization\n"
            f"\n"
        )
    THRESHOLD_MARKER.touch()


def main():
    throughput = get_throughput_last_hour()
    resources = get_resource_usage()

    metrics = EfficiencyMetrics(
        timestamp=datetime.now(timezone.utc).isoformat(),
        websites_per_hour=throughput["websites_per_hour"],
        links_per_hour=throughput["links_per_hour"],
        website_verify_success_rate=throughput["website_verify_success_rate"],
        link_extraction_success_rate=throughput["link_extraction_success_rate"],
        cpu_percent=resources["cpu_percent"],
        gpu_memory_percent=resources["gpu_memory_percent"],
        disk_io_percent=resources["disk_io_percent"],
        combined_efficiency=0,  # Will calculate below
    )

    metrics.combined_efficiency = calculate_efficiency(asdict(metrics))

    peak_eff = load_peak_efficiency()
    if peak_eff is None:
        peak_eff = metrics.combined_efficiency
        print(
            f"[BASELINE] Efficiency established: {metrics.combined_efficiency:.1f}%"
        )
    else:
        threshold_breach = peak_eff * (EFFICIENCY_THRESHOLD / 100)
        if metrics.combined_efficiency < threshold_breach:
            alert_efficiency_drop(
                peak_eff, metrics.combined_efficiency, threshold_breach
            )
            print(
                f"[ALERT] Efficiency {metrics.combined_efficiency:.1f}% < threshold {threshold_breach:.1f}%"
            )
            print(f"Marker file: {THRESHOLD_MARKER}")

    save_state(peak_eff, metrics)

    # Log current metrics
    print(
        f"[{metrics.timestamp}] "
        f"Websites/h: {metrics.websites_per_hour:.0f} | "
        f"Links/h: {metrics.links_per_hour:.0f} | "
        f"Success: {metrics.website_verify_success_rate:.0f}% + {metrics.link_extraction_success_rate:.0f}% | "
        f"Efficiency: {metrics.combined_efficiency:.1f}%"
    )


if __name__ == "__main__":
    main()
