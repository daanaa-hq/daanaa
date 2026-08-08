#!/usr/bin/env python3
"""
Daily Morning Review — Enrichment & Discovery Pipeline Health
Analyzes last night's runs, compares to historical performance, flags inefficiencies.

Usage:
  python3 enrichment_morning_review.py              # Print to console
  python3 enrichment_morning_review.py --save       # Save to daily report file
  python3 enrichment_morning_review.py --email      # Email report (if configured)

Runs automatically at 9am via cron, or manually any time to check status.
"""

import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import sys

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "merit_registry.db"
LOGS_DIR = REPO_ROOT / "logs"
METRICS_DIR = LOGS_DIR / "enrichment_metrics"
REPORTS_DIR = REPO_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

class MorningReview:
    def __init__(self):
        self.today = datetime.now().date()
        self.yesterday = self.today - timedelta(days=1)
        self.report = []
        self.alerts = []
        self.metrics = {}

    def log(self, msg):
        """Add line to report."""
        self.report.append(msg)

    def alert(self, severity, msg):
        """Flag an issue."""
        self.alerts.append((severity, msg))

    def load_last_night_log(self):
        """Read last night's enrichment-loop log."""
        log_file = LOGS_DIR / f"enrichment-loop-{self.yesterday.strftime('%Y%m%d')}.log"
        if not log_file.exists():
            return None, 0

        try:
            with open(log_file) as f:
                content = f.read()
            size_mb = log_file.stat().st_size / (1024 * 1024)
            return content, size_mb
        except:
            return None, 0

    def analyze_log(self, log_content):
        """Parse enrichment log for metrics."""
        if not log_content:
            return {}

        metrics = {
            'batches': 0,
            'duration_seconds': 0,
            'errors': log_content.count('[ERROR]'),
            'connection_refused': log_content.count('Connection refused'),
            'completed': 'COMPLETE' in log_content or 'DONE' in log_content,
            'killed_at_cutoff': 'KILLED AT CUTOFF' in log_content,
        }

        # Count batches
        metrics['batches'] = log_content.count('BATCH ') // 2  # START + COMPLETE

        return metrics

    def get_db_metrics(self):
        """Query database for enrichment coverage."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as total_orgs,
                    SUM(CASE WHEN website IS NOT NULL AND website != '' THEN 1 ELSE 0 END) as with_website,
                    SUM(CASE WHEN mission IS NOT NULL AND mission != '' THEN 1 ELSE 0 END) as with_mission,
                    SUM(CASE WHEN donate_url IS NOT NULL AND donate_url != '' THEN 1 ELSE 0 END) as with_donate_url,
                    SUM(CASE WHEN donate_confidence >= 90 THEN 1 ELSE 0 END) as verified_donate
                FROM registry_enriched
            """)
            row = cursor.fetchone()

            if row:
                return {
                    'total_orgs': row[0],
                    'with_website': row[1] or 0,
                    'with_mission': row[2] or 0,
                    'with_donate_url': row[3] or 0,
                    'verified_donate': row[4] or 0,
                }
        except Exception as e:
            self.alert('WARNING', f'DB query failed: {e}')
            return {}
        finally:
            conn.close()

    def load_historical_metrics(self):
        """Load last 7 days of metrics for comparison."""
        history = []
        for f in sorted(METRICS_DIR.glob("*.json"))[-7:]:
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    data['date'] = f.stem
                    history.append(data)
            except:
                pass
        return history

    def compute_deltas(self, current, previous):
        """Compute change since yesterday."""
        if not previous:
            return {}

        keys = ['with_website', 'with_mission', 'with_donate_url', 'verified_donate']
        deltas = {}
        for key in keys:
            if key in current and key in previous:
                deltas[key] = current[key] - previous[key]
        return deltas

    def check_inference_servers(self):
        """Verify inference servers are healthy."""
        servers = {
            'embeddings (11434)': 11434,
            'llm (8080)': 8080,
        }

        results = {}
        for name, port in servers.items():
            try:
                result = subprocess.run(
                    ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', f'http://localhost:{port}/health'],
                    capture_output=True,
                    timeout=3,
                    text=True
                )
                if result.stdout.strip() == '200':
                    results[name] = 'UP'
                else:
                    self.alert('CRITICAL', f'Inference server {name} not responding (HTTP {result.stdout.strip()})')
                    results[name] = 'DOWN'
            except:
                self.alert('CRITICAL', f'Inference server {name} unreachable (connection failed)')
                results[name] = 'DOWN'
        return results

    def generate_report(self):
        """Build the morning review report."""
        self.log("=" * 80)
        self.log("🌅 ENRICHMENT & DISCOVERY — DAILY MORNING REVIEW")
        self.log("=" * 80)
        self.log(f"Date: {self.today.strftime('%A, %B %d, %Y')}")
        self.log(f"Report generated: {datetime.now().strftime('%H:%M:%S %Z')}")
        self.log("")

        # Last night's run analysis
        self.log("📊 LAST NIGHT'S ENRICHMENT RUN")
        self.log("-" * 80)

        log_content, log_size_mb = self.load_last_night_log()
        if not log_content:
            self.log("❌ No enrichment log found for yesterday")
            self.alert('WARNING', 'No enrichment-loop log for yesterday — pipeline may not have run')
        else:
            log_metrics = self.analyze_log(log_content)

            if log_metrics['connection_refused'] > 0:
                self.alert('CRITICAL', f"Inference servers down during run ({log_metrics['connection_refused']:,} connection errors)")
                self.log(f"🔴 INFERENCE SERVERS WERE DOWN")
                self.log(f"   Connection refused errors: {log_metrics['connection_refused']:,}")
                self.log(f"   Impact: Zero enrichment progress; wasted {log_metrics['batches']} batch attempts")
            else:
                self.log(f"✅ Batches completed: {log_metrics['batches']}")
                self.log(f"   Status: {'Complete' if log_metrics['completed'] else 'Partial'}")
                self.log(f"   Killed at 8am cutoff: {log_metrics['killed_at_cutoff']}")

            self.log(f"   Log file size: {log_size_mb:.1f} MB", )
            if log_size_mb > 500:
                self.alert('WARNING', f'Unusually large log ({log_size_mb:.0f}MB) — may indicate verbose error logging')

            self.log(f"   Errors logged: {log_metrics['errors']:,}")
            if log_metrics['errors'] > 100000:
                self.alert('WARNING', f'High error count ({log_metrics["errors"]:,}) — check server health')

        self.log("")

        # Current enrichment coverage
        self.log("💾 ENRICHMENT COVERAGE (Current)")
        self.log("-" * 80)

        current_metrics = self.get_db_metrics()
        history = self.load_historical_metrics()
        prev_metrics = history[-2]['metrics'] if len(history) >= 2 else None

        if current_metrics:
            total = current_metrics['total_orgs']

            # Websites
            website_pct = 100 * current_metrics['with_website'] / total if total > 0 else 0
            website_growth = ""
            if prev_metrics and 'with_website' in prev_metrics:
                growth = current_metrics['with_website'] - prev_metrics['with_website']
                website_growth = f" ({'+' if growth >= 0 else ''}{growth:,} since yesterday)"
            self.log(f"🌐 Websites discovered: {current_metrics['with_website']:,} / {total:,} ({website_pct:.1f}%){website_growth}")

            # Missions
            mission_pct = 100 * current_metrics['with_mission'] / total if total > 0 else 0
            mission_growth = ""
            if prev_metrics and 'with_mission' in prev_metrics:
                growth = current_metrics['with_mission'] - prev_metrics['with_mission']
                mission_growth = f" ({'+' if growth >= 0 else ''}{growth:,})"
            self.log(f"💭 Missions generated: {current_metrics['with_mission']:,} / {total:,} ({mission_pct:.1f}%){mission_growth}")

            # Donation links
            donate_pct = 100 * current_metrics['with_donate_url'] / total if total > 0 else 0
            donate_growth = ""
            if prev_metrics and 'with_donate_url' in prev_metrics:
                growth = current_metrics['with_donate_url'] - prev_metrics['with_donate_url']
                donate_growth = f" ({'+' if growth >= 0 else ''}{growth:,})"
                if growth < 0:
                    self.alert('WARNING', f'Donation links coverage decreased by {abs(growth):,} — check pipeline')
            self.log(f"💳 Donation links verified: {current_metrics['verified_donate']:,} (confidence ≥90%){donate_growth}")

        self.log("")

        # Inference server health
        self.log("⚙️  INFRASTRUCTURE HEALTH")
        self.log("-" * 80)
        server_health = self.check_inference_servers()
        for server, status in server_health.items():
            icon = "✅" if status == "UP" else "❌"
            self.log(f"{icon} {server}: {status}")

        self.log("")

        # Alerts summary
        if self.alerts:
            self.log("⚠️  ALERTS & RECOMMENDATIONS")
            self.log("-" * 80)
            critical_alerts = [a for a in self.alerts if a[0] == 'CRITICAL']
            warning_alerts = [a for a in self.alerts if a[0] == 'WARNING']

            if critical_alerts:
                for _, msg in critical_alerts:
                    self.log(f"🔴 CRITICAL: {msg}")

            if warning_alerts:
                for _, msg in warning_alerts:
                    self.log(f"🟡 WARNING: {msg}")

            self.log("")

        # Efficiency trend
        if len(history) >= 2:
            self.log("📈 7-DAY TREND")
            self.log("-" * 80)
            for entry in history[-5:]:  # Last 5 days
                date = entry.get('date', 'unknown')
                website_pct = 100 * entry.get('with_website', 0) / entry.get('total_orgs', 1) if entry.get('total_orgs') else 0
                self.log(f"  {date}: {website_pct:.1f}% website coverage, {entry.get('with_donate_url', 0):,} donate links")

        self.log("")
        self.log("=" * 80)
        self.log("Next run: Tonight 8pm–8am CST (12-hour enrichment window)")
        self.log("=" * 80)

    def print_report(self):
        """Print report to console."""
        for line in self.report:
            print(line)

    def save_report(self):
        """Save report to dated file."""
        filename = REPORTS_DIR / f"enrichment_review_{self.today.strftime('%Y%m%d')}.txt"
        with open(filename, 'w') as f:
            f.write('\n'.join(self.report))
        print(f"\n✅ Report saved to {filename}")
        return filename

if __name__ == '__main__':
    review = MorningReview()
    review.generate_report()
    review.print_report()

    if '--save' in sys.argv:
        review.save_report()

    if review.alerts:
        sys.exit(1 if any(a[0] == 'CRITICAL' for a in review.alerts) else 0)
