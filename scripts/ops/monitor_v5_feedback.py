#!/usr/bin/env python3
"""
Week 3 Feedback Monitoring Dashboard
Real-time tracking of v5_feedback responses and early metrics.

Updates every 30 seconds. Shows:
  - Total responses collected
  - Current clarity % (≥80% required)
  - Current preference % (≥70% required)
  - Response rate per hour
  - Sample feedback snippets
  - Alert if metrics trending toward failure

Usage:
  python3 scripts/monitor_v5_feedback.py [--interval 30] [--export-csv]

  --interval N: Update every N seconds (default 30)
  --export-csv: Write metrics to CSV for trending analysis
"""

import sqlite3
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path('data/merit_registry.db')

class FeedbackMonitor:
    def __init__(self, interval=30, export_csv=False):
        self.interval = interval
        self.export_csv = export_csv
        self.last_count = 0
        self.csv_file = Path('feedback_metrics.csv') if export_csv else None

        if export_csv and not self.csv_file.exists():
            with open(self.csv_file, 'w') as f:
                f.write("timestamp,total_responses,clarity_pct,preference_pct,hourly_rate\n")

    def get_metrics(self):
        """Fetch current metrics from database"""
        db = sqlite3.connect(str(DB_PATH))
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Total responses
        cursor.execute("SELECT COUNT(*) as total FROM v5_feedback")
        total = cursor.fetchone()['total']

        # Clarity breakdown
        cursor.execute(
            """SELECT COUNT(*) as total, SUM(clarity) as clear
               FROM v5_feedback WHERE clarity IS NOT NULL"""
        )
        clarity_row = cursor.fetchone()
        clarity_total = clarity_row['total']
        clarity_clear = clarity_row['clear'] or 0

        # Preference breakdown
        cursor.execute(
            """SELECT COUNT(*) as total, SUM(preference) as peer
               FROM v5_feedback WHERE preference IS NOT NULL"""
        )
        pref_row = cursor.fetchone()
        pref_total = pref_row['total']
        pref_peer = pref_row['peer'] or 0

        # Hourly rate
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute(
            "SELECT COUNT(*) as count FROM v5_feedback WHERE created_at > ?",
            (one_hour_ago,)
        )
        hourly = cursor.fetchone()['count']

        # Sample responses
        cursor.execute(
            """SELECT clarity, preference, clarity_reason, org_name
               FROM v5_feedback ORDER BY created_at DESC LIMIT 3"""
        )
        samples = cursor.fetchall()

        db.close()

        clarity_pct = (clarity_clear / clarity_total * 100) if clarity_total > 0 else 0
        pref_pct = (pref_peer / pref_total * 100) if pref_total > 0 else 0

        return {
            'total': total,
            'clarity_pct': clarity_pct,
            'clarity_count': clarity_clear,
            'clarity_total': clarity_total,
            'pref_pct': pref_pct,
            'pref_count': pref_peer,
            'pref_total': pref_total,
            'hourly_rate': hourly,
            'samples': samples
        }

    def format_bar(self, pct, width=30, target=None):
        """Format progress bar"""
        filled = int(pct / 100 * width)
        bar = "█" * filled + "░" * (width - filled)
        marker = " ✓ PASS" if pct >= (target or 100) else f" ✗ {pct:.0f}%"
        return f"{bar}{marker}"

    def print_dashboard(self, metrics):
        """Print formatted dashboard"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Clear screen (ANSI escape)
        print("\033[2J\033[H", end="")

        print("╔" + "═" * 68 + "╗")
        print(f"║ WEEK 3 v5.0 BETA — FEEDBACK MONITORING DASHBOARD                  ║")
        print(f"║ {timestamp}                                                    ║")
        print("╚" + "═" * 68 + "╝")
        print()

        print(f"RESPONSES: {metrics['total']} collected (target: 50-100 by Fri EOD)")
        print(f"  Hourly rate: {metrics['hourly_rate']}/hour")
        print()

        # Clarity metric
        print(f"1. CLARITY: {metrics['clarity_pct']:.1f}% clear (target: ≥80%)")
        print(f"   {metrics['clarity_count']}/{metrics['clarity_total']} responses")
        print(f"   {self.format_bar(metrics['clarity_pct'], target=80)}")
        print()

        # Preference metric
        print(f"2. PREFERENCE: {metrics['pref_pct']:.1f}% prefer peer (target: ≥70%)")
        print(f"   {metrics['pref_count']}/{metrics['pref_total']} responses")
        print(f"   {self.format_bar(metrics['pref_pct'], target=70)}")
        print()

        # Sample responses
        if metrics['samples']:
            print("RECENT RESPONSES:")
            for i, sample in enumerate(metrics['samples'], 1):
                org_name = sample['org_name'][:40] if sample['org_name'] else 'Unknown'
                clarity_txt = "clear" if sample['clarity'] else "unclear"
                pref_txt = "peer" if sample['preference'] else "single"
                reason = sample['clarity_reason'][:40] if sample['clarity_reason'] else ''
                print(f"  [{i}] {clarity_txt} | {pref_txt} | {org_name}")
                if reason:
                    print(f"      → {reason}")
        print()

        # Alert thresholds
        print("ALERTS:")
        if metrics['clarity_pct'] < 50:
            print("  ⚠  Clarity trending low (<50%) — may fail threshold")
        if metrics['pref_pct'] < 50:
            print("  ⚠  Preference trending low (<50%) — may fail threshold")
        if metrics['total'] < 3:
            print("  ℹ  Low response rate — continue monitoring")
        else:
            print("  ✓  No alerts")
        print()

        print("NEXT CHECKPOINT: Fri 9am metrics analysis")
        print("Decision gate: Fri 5pm PT")
        print()
        print("(Refreshing every 30 seconds. Press Ctrl+C to stop)")

    def export_metrics(self, metrics):
        """Write metrics to CSV"""
        if not self.csv_file:
            return

        with open(self.csv_file, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp},{metrics['total']},{metrics['clarity_pct']:.1f},{metrics['pref_pct']:.1f},{metrics['hourly_rate']}\n")

    def run(self):
        """Start monitoring loop"""
        print("Starting feedback monitor (refreshes every {} seconds)...".format(self.interval))
        time.sleep(2)

        try:
            while True:
                metrics = self.get_metrics()
                self.print_dashboard(metrics)
                if self.export_csv:
                    self.export_metrics(metrics)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            if self.csv_file and self.csv_file.exists():
                print(f"Metrics exported to {self.csv_file}")

if __name__ == '__main__':
    import sys
    interval = 30
    export = False

    for i, arg in enumerate(sys.argv[1:]):
        if arg == '--interval' and i + 1 < len(sys.argv):
            interval = int(sys.argv[i + 2])
        if arg == '--export-csv':
            export = True

    monitor = FeedbackMonitor(interval=interval, export_csv=export)
    monitor.run()
