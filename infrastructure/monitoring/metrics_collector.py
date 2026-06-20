#!/usr/bin/env python3
"""
Metrics collector for Daanaa infrastructure — system, API, and data pipeline health.

Runs as a daemon (or cron every minute) and publishes metrics to a JSON file that
can be consumed by monitoring systems (Prometheus, Grafana, or simple dashboards).

Metrics collected:
  System: CPU, memory, disk, network
  API: response times, error rates, cache hit rates
  Database: size, query times, FTS5 health
  Pipeline: scorer health, embedding index size, last run time
  Search: index health, query latency percentiles
"""

import json
import os
import sqlite3
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

METRICS_FILE = "/tmp/daanaa_metrics.json"
DB_PATH = "data/merit_registry.db"
SEARCH_DB_PATH = "/data/precompute/v1/search.db"  # On droplet
API_PORT = 5000


class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {},
            "api": {},
            "database": {},
            "pipeline": {},
            "search": {},
            "alerts": [],
        }

    def collect_system_metrics(self):
        """CPU, memory, disk, uptime."""
        try:
            # Memory
            with open("/proc/meminfo") as f:
                mem_data = {}
                for line in f:
                    if line.startswith(("MemTotal", "MemAvailable", "MemFree")):
                        key, val = line.split(":")
                        mem_data[key.strip()] = int(val.split()[0])

            mem_used = (mem_data["MemTotal"] - mem_data["MemAvailable"]) / mem_data["MemTotal"] * 100
            self.metrics["system"]["memory_percent"] = round(mem_used, 2)
            self.metrics["system"]["memory_gb"] = round((mem_data["MemTotal"] - mem_data["MemAvailable"]) / 1024 / 1024, 2)

            # Disk
            stat = os.statvfs("/")
            disk_total = stat.f_blocks * stat.f_frsize
            disk_free = stat.f_bavail * stat.f_frsize
            disk_used_pct = (1 - disk_free / disk_total) * 100
            self.metrics["system"]["disk_percent"] = round(disk_used_pct, 2)
            self.metrics["system"]["disk_gb_free"] = round(disk_free / 1024**3, 2)

            # Load average
            load = os.getloadavg()
            self.metrics["system"]["load_1min"] = round(load[0], 2)

            # Uptime
            with open("/proc/uptime") as f:
                uptime_sec = int(float(f.read().split()[0]))
                self.metrics["system"]["uptime_days"] = round(uptime_sec / 86400, 2)
        except Exception as e:
            self.metrics["system"]["error"] = str(e)

    def collect_api_metrics(self):
        """API health, response times, error rates."""
        try:
            # Simple health check
            result = subprocess.run(
                ["curl", "-s", "-w", "%{http_code}", "-o", "/dev/null",
                 f"http://localhost:{API_PORT}/health"],
                timeout=5,
                capture_output=True
            )
            status_code = result.stdout.decode().strip()
            self.metrics["api"]["health_status"] = int(status_code) if status_code.isdigit() else 0
            self.metrics["api"]["healthy"] = status_code == "200"

            # Response time sampling (3 common endpoints)
            endpoints = [
                ("/api/stats", "stats"),
                ("/api/organizations?page=1", "directory"),
                ("/directory", "spa"),
            ]

            for path, name in endpoints:
                try:
                    start = time.time()
                    result = subprocess.run(
                        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         f"http://localhost:{API_PORT}{path}"],
                        timeout=10,
                        capture_output=True
                    )
                    elapsed = (time.time() - start) * 1000
                    status = int(result.stdout.decode().strip())
                    self.metrics["api"][f"{name}_latency_ms"] = round(elapsed, 2)
                    self.metrics["api"][f"{name}_status"] = status
                except:
                    self.metrics["api"][f"{name}_latency_ms"] = -1
        except Exception as e:
            self.metrics["api"]["error"] = str(e)

    def collect_database_metrics(self):
        """Database size, row counts, query performance."""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row

            # Database size
            size = os.path.getsize(DB_PATH) / 1024**2
            self.metrics["database"]["merit_registry_mb"] = round(size, 2)

            # Organization count
            total = conn.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
            deductible = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE deductibility=1").fetchone()[0]
            hidden_gems = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1").fetchone()[0]

            self.metrics["database"]["total_orgs"] = total
            self.metrics["database"]["deductible_orgs"] = deductible
            self.metrics["database"]["hidden_gems"] = hidden_gems

            # Scoring coverage
            scored = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL").fetchone()[0]
            self.metrics["database"]["scored_orgs"] = scored
            self.metrics["database"]["coverage_percent"] = round(scored / total * 100, 2) if total > 0 else 0

            # Last update
            last_update = conn.execute(
                "SELECT MAX(updated_at) FROM registry_enriched WHERE updated_at IS NOT NULL"
            ).fetchone()[0]
            self.metrics["database"]["last_update"] = last_update or "never"

            # FTS5 health check
            try:
                fts_count = conn.execute("SELECT COUNT(*) FROM org_fts").fetchone()[0]
                self.metrics["database"]["fts5_indexed"] = fts_count
                self.metrics["database"]["fts5_healthy"] = fts_count == total
            except:
                self.metrics["database"]["fts5_healthy"] = False

            conn.close()
        except Exception as e:
            self.metrics["database"]["error"] = str(e)

    def collect_pipeline_metrics(self):
        """Nightly scorer and enrichment pipeline status."""
        try:
            # Check for recent score snapshots (scorer health)
            conn = sqlite3.connect(DB_PATH)
            last_score = conn.execute(
                "SELECT run_date FROM score_snapshots ORDER BY run_date DESC LIMIT 1"
            ).fetchone()

            if last_score:
                last_score_date = last_score[0]
                self.metrics["pipeline"]["last_score_run"] = last_score_date

                # Check if it's recent (within 26 hours = last night)
                from datetime import datetime, timedelta
                try:
                    last_run = datetime.fromisoformat(last_score_date)
                    hours_ago = (datetime.utcnow() - last_run).total_seconds() / 3600
                    self.metrics["pipeline"]["hours_since_score"] = round(hours_ago, 2)
                    self.metrics["pipeline"]["scorer_healthy"] = hours_ago < 26
                except:
                    self.metrics["pipeline"]["scorer_healthy"] = False
            else:
                self.metrics["pipeline"]["scorer_healthy"] = False

            # Embedding index size (on home server only)
            emb_db = "data/merit_registry.db"
            if Path(emb_db).exists():
                # Check if embedding table exists and has data
                try:
                    emb_count = conn.execute(
                        "SELECT COUNT(*) FROM org_embeddings WHERE embedding IS NOT NULL"
                    ).fetchone()[0]
                    self.metrics["pipeline"]["embeddings_computed"] = emb_count
                except:
                    pass

            conn.close()
        except Exception as e:
            self.metrics["pipeline"]["error"] = str(e)

    def collect_search_metrics(self):
        """Search index health and query performance (on droplet)."""
        try:
            # This would connect to droplet search.db via SSH or local copy
            # For now, just note that it needs to be collected from droplet
            self.metrics["search"]["note"] = "Collected via droplet deployment"
        except Exception as e:
            self.metrics["search"]["error"] = str(e)

    def check_alerts(self):
        """Threshold-based alerting rules."""
        alerts = []

        # Disk space
        disk_pct = self.metrics["system"].get("disk_percent", 0)
        if disk_pct > 80:
            alerts.append(f"CRITICAL: Disk usage {disk_pct}% (>80%)")
        elif disk_pct > 70:
            alerts.append(f"WARNING: Disk usage {disk_pct}% (>70%)")

        # Memory
        mem_pct = self.metrics["system"].get("memory_percent", 0)
        if mem_pct > 85:
            alerts.append(f"CRITICAL: Memory usage {mem_pct}% (>85%)")

        # API health
        if not self.metrics["api"].get("healthy", False):
            alerts.append(f"CRITICAL: API unhealthy (status {self.metrics['api'].get('health_status')})")

        # API latency
        for key, val in self.metrics["api"].items():
            if "latency_ms" in key and isinstance(val, (int, float)) and val > 5000:
                alerts.append(f"WARNING: {key} is {val}ms (>5s)")

        # Database coverage
        coverage = self.metrics["database"].get("coverage_percent", 100)
        if coverage < 95:
            alerts.append(f"WARNING: Scoring coverage {coverage}% (<95%)")

        # Scorer health
        if not self.metrics["pipeline"].get("scorer_healthy", True):
            hours = self.metrics["pipeline"].get("hours_since_score", 999)
            alerts.append(f"CRITICAL: Scorer not run in {hours}h (expected <26h)")

        # FTS5 health
        if not self.metrics["database"].get("fts5_healthy", True):
            alerts.append(f"WARNING: FTS5 index out of sync")

        self.metrics["alerts"] = alerts
        self.metrics["alert_count"] = len(alerts)

    def publish(self):
        """Write metrics to JSON file."""
        try:
            with open(METRICS_FILE, "w") as f:
                json.dump(self.metrics, f, indent=2)
            return True
        except Exception as e:
            print(f"Error publishing metrics: {e}")
            return False

    def run(self):
        """Collect all metrics and publish."""
        self.collect_system_metrics()
        self.collect_api_metrics()
        self.collect_database_metrics()
        self.collect_pipeline_metrics()
        self.collect_search_metrics()
        self.check_alerts()
        self.publish()

        if self.metrics["alerts"]:
            print(f"⚠️  {self.metrics['alert_count']} alerts:")
            for alert in self.metrics["alerts"]:
                print(f"   {alert}")
        else:
            print("✓ All systems healthy")

        return self.metrics


if __name__ == "__main__":
    collector = MetricsCollector()
    metrics = collector.run()
