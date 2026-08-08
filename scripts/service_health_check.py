#!/usr/bin/env python3
"""
Service Health Monitor — Watch API, inference servers, and enrichment daemon.
Catches silent failures before they impact production.

Incident: 2026-07-12 inference servers silently failed, breaking enrichment overnight.
This prevents a repeat.

Usage:
  python3 service_health_check.py                  # Check all services once
  python3 service_health_check.py --continuous     # Poll every 30s (for dashboard)
  python3 service_health_check.py --alert          # Alert if anything is down
"""

import json
import subprocess
import requests
import time
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
LOG_DIR = REPO_ROOT / "logs"
HEALTH_LOG = LOG_DIR / "service_health.jsonl"

SERVICES = {
    'api_home': {
        'name': 'API (Home)',
        'url': 'http://localhost:5000/health',
        'timeout': 5,
        'expected_status': 200,
    },
    'inference_embed': {
        'name': 'Inference — Embeddings',
        'port': 11434,
        'check': 'curl -s http://127.0.0.1:11434/health > /dev/null',
        'timeout': 5,
    },
    'inference_llm': {
        'name': 'Inference — LLM',
        'port': 8080,
        'check': 'curl -s http://127.0.0.1:8080/health > /dev/null',
        'timeout': 5,
    },
    'enrichment_daemon': {
        'name': 'Enrichment Daemon',
        'pidfile': str(LOG_DIR / 'archive_finder' / 'daemon.pid'),
        'logfile': str(LOG_DIR / 'archive_finder' / 'daemon.log'),
    },
    'search_index': {
        'name': 'Search Index (FTS5)',
        'db': str(REPO_ROOT / 'data' / 'merit_registry.db'),
        'check': 'sqlite3 {db} "SELECT COUNT(*) FROM org_fts LIMIT 1" > /dev/null',
    },
}

class ServiceMonitor:
    def __init__(self):
        self.results = {}
        self.alerts = []

    def check_http_service(self, name, config):
        """Check HTTP service health."""
        try:
            response = requests.get(config['url'], timeout=config['timeout'])
            status = response.status_code
            is_healthy = status == config.get('expected_status', 200)

            return {
                'healthy': is_healthy,
                'status_code': status,
                'details': f"HTTP {status}",
            }
        except requests.ConnectionError:
            return {'healthy': False, 'status_code': 0, 'details': 'Connection refused'}
        except requests.Timeout:
            return {'healthy': False, 'status_code': 0, 'details': 'Timeout'}
        except Exception as e:
            return {'healthy': False, 'status_code': 0, 'details': str(e)[:50]}

    def check_process_service(self, name, config):
        """Check if daemon process is running."""
        pidfile = config.get('pidfile')
        if not pidfile or not Path(pidfile).exists():
            return {'healthy': False, 'details': 'No pidfile'}

        try:
            with open(pidfile) as f:
                pid = int(f.read().strip())

            # Check if process is running
            result = subprocess.run(
                ['ps', '-p', str(pid)],
                capture_output=True,
                timeout=2
            )

            is_running = result.returncode == 0

            if not is_running:
                return {'healthy': False, 'details': f'PID {pid} not running'}

            # Check if recently active (touched log in last hour)
            logfile = config.get('logfile')
            if logfile and Path(logfile).exists():
                mtime = Path(logfile).stat().st_mtime
                age_sec = time.time() - mtime
                if age_sec > 3600:
                    return {'healthy': False, 'details': f'Log stale ({age_sec/60:.0f} min)'}

            return {'healthy': True, 'details': f'PID {pid} running'}

        except Exception as e:
            return {'healthy': False, 'details': str(e)[:50]}

    def check_database_index(self, name, config):
        """Check if database index exists and is queryable."""
        db = config.get('db')
        if not db or not Path(db).exists():
            return {'healthy': False, 'details': 'Database not found'}

        try:
            result = subprocess.run(
                ['sqlite3', db, 'SELECT COUNT(*) FROM org_fts LIMIT 1'],
                capture_output=True,
                timeout=5,
                text=True
            )

            if result.returncode == 0:
                count = result.stdout.strip()
                return {'healthy': True, 'details': f'{count} rows indexed'}
            else:
                error = result.stderr.strip()[:50]
                return {'healthy': False, 'details': f'Query failed: {error}'}

        except subprocess.TimeoutExpired:
            return {'healthy': False, 'details': 'Query timeout'}
        except Exception as e:
            return {'healthy': False, 'details': str(e)[:50]}

    def check_all(self):
        """Run all service checks."""
        self.results = {}
        self.alerts = []

        for service_id, config in SERVICES.items():
            if service_id.startswith('api_'):
                result = self.check_http_service(service_id, config)
            elif service_id.startswith('inference_'):
                # Try HTTP check first for inference services
                try:
                    port = config.get('port')
                    url = f'http://localhost:{port}/health'
                    response = requests.get(url, timeout=2)
                    result = {'healthy': response.status_code == 200, 'details': f'Port {port} responding'}
                except:
                    result = {'healthy': False, 'details': f'Port {config.get("port")} not responding'}
            elif service_id == 'enrichment_daemon':
                result = self.check_process_service(service_id, config)
            elif service_id == 'search_index':
                result = self.check_database_index(service_id, config)
            else:
                result = {'healthy': False, 'details': 'Unknown service type'}

            self.results[service_id] = result

            if not result.get('healthy'):
                self.alerts.append({
                    'service': config['name'],
                    'status': 'DOWN',
                    'details': result.get('details'),
                    'timestamp': datetime.now().isoformat(),
                })

    def report(self):
        """Print health report."""
        print("\n" + "=" * 70)
        print("🔧 SERVICE HEALTH MONITOR")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S Central')}")
        print()

        healthy_count = sum(1 for r in self.results.values() if r.get('healthy'))
        total_count = len(self.results)

        print(f"Status: {healthy_count}/{total_count} services healthy")
        print()

        for service_id, config in SERVICES.items():
            result = self.results.get(service_id, {})
            status_icon = "✅" if result.get('healthy') else "❌"
            details = result.get('details', 'Unknown')

            print(f"{status_icon} {config['name']:35} {details}")

        print()

        if self.alerts:
            print("🚨 ALERTS")
            for alert in self.alerts:
                print(f"  • {alert['service']}: {alert['details']}")
            print()

            # Log alerts
            for alert in self.alerts:
                with open(HEALTH_LOG, 'a') as f:
                    f.write(json.dumps(alert) + '\n')

        print("=" * 70)

        return len(self.alerts) == 0

def continuous_monitor(interval=30):
    """Run continuous monitoring."""
    print("Continuous monitoring started (Ctrl+C to stop)")
    while True:
        monitor = ServiceMonitor()
        monitor.check_all()

        # Show only alerts on stdout (less noise)
        if monitor.alerts:
            monitor.report()

        time.sleep(interval)

if __name__ == '__main__':
    monitor = ServiceMonitor()
    monitor.check_all()

    if '--continuous' in sys.argv:
        continuous_monitor()
    elif '--alert' in sys.argv:
        success = monitor.report()
        sys.exit(0 if success else 1)
    else:
        monitor.report()
