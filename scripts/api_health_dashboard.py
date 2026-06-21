#!/usr/bin/env python3
"""
API Health Check Dashboard — monitors Daanaa API health and gunicorn process.

Checks every 5 seconds:
- /health endpoint returns 200 within 2s
- /api/stats returns valid JSON
- Gunicorn process exists and memory < 1GB
- Response time trend (last 10 requests)
- Memory trend (last 10 samples)

Updates to stdout + log file with color-coded status.
Alerts if memory > 1GB or response time > 2s.

Usage:
    python3 scripts/api_health_dashboard.py
    python3 scripts/api_health_dashboard.py --log-only
"""

import os
import sys
import json
import time
import requests
import psutil
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Tuple

API_URL = "http://localhost:5000"
HEALTH_ENDPOINT = f"{API_URL}/health"
STATS_ENDPOINT = f"{API_URL}/api/stats"
API_TIMEOUT = 2.0
MEMORY_LIMIT_MB = 1000
RESPONSE_TIME_WARNING = 2.0

MONITOR_LOG = Path.home() / "meritgiving/logs/api_health.log"
UPDATE_INTERVAL = 5  # seconds

# Color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class APIHealthMonitor:
    def __init__(self):
        self.response_times = deque(maxlen=10)
        self.memory_samples = deque(maxlen=10)
        self.error_count = 0
        self.success_count = 0
        self.uptime_start = datetime.now(timezone.utc)

    def check_health_endpoint(self) -> Tuple[bool, float, Optional[str]]:
        """Check /health endpoint."""
        try:
            start = time.time()
            resp = requests.get(HEALTH_ENDPOINT, timeout=API_TIMEOUT)
            elapsed = time.time() - start

            self.response_times.append(elapsed)

            if resp.status_code == 200:
                self.success_count += 1
                return True, elapsed, None
            else:
                self.error_count += 1
                return False, elapsed, f"Status {resp.status_code}"

        except requests.Timeout:
            self.error_count += 1
            self.response_times.append(API_TIMEOUT)
            return False, API_TIMEOUT, "Timeout"
        except requests.ConnectionError:
            self.error_count += 1
            return False, 0, "Connection refused"
        except Exception as e:
            self.error_count += 1
            return False, 0, str(e)

    def check_stats_endpoint(self) -> Tuple[bool, Optional[dict], Optional[str]]:
        """Check /api/stats endpoint."""
        try:
            start = time.time()
            resp = requests.get(STATS_ENDPOINT, timeout=API_TIMEOUT)
            elapsed = time.time() - start

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    self.response_times.append(elapsed)
                    return True, data, None
                except json.JSONDecodeError:
                    return False, None, "Invalid JSON"
            else:
                return False, None, f"Status {resp.status_code}"

        except requests.Timeout:
            return False, None, "Timeout"
        except requests.ConnectionError:
            return False, None, "Connection refused"
        except Exception as e:
            return False, None, str(e)

    def find_gunicorn_process(self) -> Optional[psutil.Process]:
        """Find gunicorn master process."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline') or []
                    if 'gunicorn' in proc.name() or 'gunicorn' in ' '.join(cmdline):
                        return proc
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
        return None

    def check_gunicorn_memory(self) -> Tuple[Optional[float], bool]:
        """Check gunicorn RSS memory."""
        try:
            proc = self.find_gunicorn_process()
            if not proc:
                return None, False

            rss_mb = proc.memory_info().rss / 1024 / 1024
            self.memory_samples.append(rss_mb)
            return rss_mb, rss_mb < MEMORY_LIMIT_MB

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None, False
        except Exception as e:
            log_message(f"Error checking memory: {e}", level="ERROR")
            return None, False

    def get_status_color(self, value: float, threshold: float, inverted: bool = False) -> str:
        """Determine color based on threshold."""
        if inverted:
            # For uptime/success (higher is better)
            if value >= threshold:
                return Colors.GREEN
            elif value >= threshold * 0.8:
                return Colors.YELLOW
            else:
                return Colors.RED
        else:
            # For errors/latency (lower is better)
            if value <= threshold:
                return Colors.GREEN
            elif value <= threshold * 1.5:
                return Colors.YELLOW
            else:
                return Colors.RED

    def get_uptime(self) -> str:
        """Get uptime since monitor started."""
        elapsed = (datetime.now(timezone.utc) - self.uptime_start).total_seconds()
        hours = int(elapsed / 3600)
        mins = int((elapsed % 3600) / 60)
        secs = int(elapsed % 60)

        if hours > 0:
            return f"{hours}h {mins}m {secs}s"
        else:
            return f"{mins}m {secs}s"

    def get_stats_summary(self, stats: dict) -> str:
        """Extract useful summary from /api/stats."""
        try:
            summary_parts = []

            if "registry_count" in stats:
                summary_parts.append(f"Registry: {stats['registry_count']:,} orgs")
            if "avg_cache_hit_rate" in stats:
                summary_parts.append(f"Cache hit: {stats['avg_cache_hit_rate']:.1%}")
            if "embedding_index_size" in stats:
                size_mb = stats["embedding_index_size"] / 1024 / 1024
                summary_parts.append(f"Embeddings: {size_mb:.0f}MB")

            return " | ".join(summary_parts) if summary_parts else "No stats"

        except Exception:
            return "Error parsing stats"

    def display_dashboard(self, log_only: bool = False):
        """Display API health dashboard."""
        health_ok, health_time, health_err = self.check_health_endpoint()
        stats_ok, stats_data, stats_err = self.check_stats_endpoint()
        mem_mb, mem_ok = self.check_gunicorn_memory()

        output = []
        output.append("\n" + "=" * 80)
        output.append(f"{Colors.BOLD}Daanaa API Health Dashboard{Colors.RESET}")
        output.append("=" * 80)

        output.append(f"Timestamp:        {datetime.now(timezone.utc).isoformat()}")
        output.append(f"Uptime:           {self.get_uptime()}")
        output.append("")

        # Health endpoint
        health_color = Colors.GREEN if health_ok else Colors.RED
        status_text = f"{health_color}✓ OK{Colors.RESET}" if health_ok else f"{health_color}✗ FAILED{Colors.RESET}"
        output.append(f"Health Endpoint:  {status_text}")
        output.append(f"  Response time:  {health_time * 1000:.0f}ms" +
                      (f" ({Colors.RED}SLOW{Colors.RESET})" if health_time > RESPONSE_TIME_WARNING else ""))
        if health_err:
            output.append(f"  Error:          {Colors.RED}{health_err}{Colors.RESET}")

        # Stats endpoint
        stats_color = Colors.GREEN if stats_ok else Colors.RED
        status_text = f"{stats_color}✓ OK{Colors.RESET}" if stats_ok else f"{stats_color}✗ FAILED{Colors.RESET}"
        output.append(f"Stats Endpoint:   {status_text}")
        if stats_ok and stats_data:
            output.append(f"  {self.get_stats_summary(stats_data)}")
        if stats_err:
            output.append(f"  Error:          {Colors.RED}{stats_err}{Colors.RESET}")

        # Gunicorn memory
        if mem_mb is not None:
            mem_color = self.get_status_color(mem_mb, MEMORY_LIMIT_MB)
            output.append(f"Gunicorn Memory:  {mem_color}{mem_mb:.0f}MB / {MEMORY_LIMIT_MB}MB{Colors.RESET}")
        else:
            output.append(f"Gunicorn Memory:  {Colors.YELLOW}Not found{Colors.RESET}")

        # Response time trend
        if self.response_times:
            avg_time = sum(self.response_times) / len(self.response_times)
            max_time = max(self.response_times)
            rt_color = self.get_status_color(avg_time, RESPONSE_TIME_WARNING)
            output.append(f"Response times:   {rt_color}Avg {avg_time * 1000:.0f}ms | Max {max_time * 1000:.0f}ms{Colors.RESET}")

        # Memory trend
        if self.memory_samples:
            avg_mem = sum(self.memory_samples) / len(self.memory_samples)
            max_mem = max(self.memory_samples)
            mem_color = self.get_status_color(avg_mem, MEMORY_LIMIT_MB)
            output.append(f"Memory trend:     {mem_color}Avg {avg_mem:.0f}MB | Max {max_mem:.0f}MB{Colors.RESET}")

        # Success rate
        total = self.success_count + self.error_count
        if total > 0:
            success_rate = (self.success_count / total) * 100
            sr_color = self.get_status_color(success_rate, 95, inverted=True)
            output.append(f"Success rate:     {sr_color}{success_rate:.1f}% ({self.success_count}/{total}){Colors.RESET}")

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

def monitor_loop(log_only: bool = False):
    """Main monitoring loop."""
    monitor = APIHealthMonitor()
    log_message("API health monitor started", level="INFO")

    while True:
        try:
            monitor.display_dashboard(log_only=log_only)
            time.sleep(UPDATE_INTERVAL)

        except KeyboardInterrupt:
            log_message("Monitor stopped by user", level="INFO")
            break
        except Exception as e:
            log_message(f"Monitor error: {e}", level="ERROR")
            time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="API Health Dashboard")
    parser.add_argument("--log-only", action="store_true", help="Log to file only, no stdout")
    args = parser.parse_args()

    monitor_loop(log_only=args.log_only)
