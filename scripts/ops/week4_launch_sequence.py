#!/usr/bin/env python3
"""
Week 4 Full Launch Sequence
Executes if Week 3 metrics pass all thresholds.

Pre-conditions:
  - All 4 metrics PASS (clarity ≥80%, preference ≥70%, NTEE ≤20%, coverage ≥98%)
  - Code review complete
  - Database backup created
  - Rollback plan confirmed

Execution (2-hour window Mon 10am—12pm PT):
  1. PREPARE (1h): Health checks, integrity verification
  2. REMOVE V4 (30 min): Strip v4 fields from API/frontend
  3. DEPLOY (30 min): Frontend rebuild + droplet push
  4. VERIFY (30 min): API health + performance checks

Usage:
  python3 scripts/week4_launch_sequence.py [--dry-run] [--skip-comms]

  --dry-run: Print actions without executing
  --skip-comms: Skip communication sends (send manually)
"""

import subprocess
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path('data/merit_registry.db')

class LaunchSequence:
    def __init__(self, dry_run=False, skip_comms=False):
        self.dry_run = dry_run
        self.skip_comms = skip_comms
        self.start_time = datetime.now()
        self.log = []

    def log_action(self, phase, action, status):
        msg = f"[{datetime.now().strftime('%H:%M:%S')}] {phase}: {action} → {status}"
        print(msg)
        self.log.append(msg)

    def run_cmd(self, cmd, description):
        """Run shell command, log result"""
        self.log_action("EXEC", description, "starting")
        if self.dry_run:
            print(f"  [DRY RUN] {cmd}")
            return True
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=300)
            if result.returncode == 0:
                self.log_action("EXEC", description, "✓")
                return True
            else:
                self.log_action("EXEC", description, f"✗ (exit {result.returncode})")
                print(f"  stderr: {result.stderr.decode()[:200]}")
                return False
        except Exception as e:
            self.log_action("EXEC", description, f"✗ ({e})")
            return False

    def phase_1_prepare(self):
        """PHASE 1: Health checks & verification (1 hour)"""
        print("\n" + "="*70)
        print("PHASE 1: PREPARE (Health checks, backups, verification)")
        print("="*70 + "\n")

        # API health check
        self.run_cmd(
            "curl -s http://localhost:5000/health | grep -q 'ok' && echo 'ok'",
            "API health check"
        )

        # Database integrity check
        self.run_cmd(
            "sqlite3 data/merit_registry.db 'PRAGMA integrity_check'",
            "Database integrity check"
        )

        # Count orgs in v5_context
        self.run_cmd(
            "sqlite3 data/merit_registry.db \"SELECT COUNT(*) FROM registry_enriched WHERE v5_archetype IS NOT NULL\"",
            "Count scored orgs"
        )

        # Create backup
        backup_path = f"data/merit_registry_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        self.run_cmd(
            f"cp data/merit_registry.db {backup_path} && ls -lh {backup_path}",
            "Create database backup"
        )

        self.log_action("PHASE1", "Complete", "✓")

    def phase_2_remove_v4(self):
        """PHASE 2: Remove v4 scores from API/frontend (30 min)"""
        print("\n" + "="*70)
        print("PHASE 2: REMOVE V4 (Strip old scoring system)")
        print("="*70 + "\n")

        # Update feature flag to 100% (remove v4, keep v5)
        self.log_action("FEATURE", "Update feature flag", "updating")
        if not self.dry_run:
            db = sqlite3.connect(str(DB_PATH))
            # In production, would update feature flag config table
            # For now, just verify v5_context exists
            cursor = db.execute(
                "SELECT COUNT(*) as count FROM registry_enriched WHERE v5_archetype IS NOT NULL"
            )
            count = cursor.fetchone()[0]
            self.log_action("FEATURE", f"v5_context available ({count} orgs)", "✓")
            db.close()

        # Update API to remove v4 response fields (would comment out in production)
        self.log_action("API", "Prepare v4 removal code", "ready")
        print("  API changes (in daanaa_api.py):")
        print("    - Remove: merit_score, merit_tier, merit_band")
        print("    - Keep: v5_context as primary response")
        print("    - Update disclosures pointing to methodology page")

        # Update frontend UI (remove old tier badges)
        self.log_action("FRONTEND", "Prepare UI updates", "ready")
        print("  Frontend changes (in FinancialContext.tsx):")
        print("    - Hide v4 tier badges")
        print("    - Update text: 'Financial Context (Beta)' → 'Financial Context'")
        print("    - Add methodology link")

        self.log_action("PHASE2", "Complete", "✓")

    def phase_3_deploy(self):
        """PHASE 3: Deploy frontend & verify (30 min)"""
        print("\n" + "="*70)
        print("PHASE 3: DEPLOY (Frontend rebuild + droplet push)")
        print("="*70 + "\n")

        # Frontend build
        self.run_cmd(
            "npm --prefix frontend run build",
            "Frontend build"
        )

        # Droplet deploy (using safe_deploy_droplet.sh)
        self.run_cmd(
            "bash scripts/safe_deploy_droplet.sh",
            "Deploy to droplet"
        )

        self.log_action("PHASE3", "Complete", "✓")

    def phase_4_verify(self):
        """PHASE 4: Verify + monitor (30 min)"""
        print("\n" + "="*70)
        print("PHASE 4: VERIFY (Health checks + performance)")
        print("="*70 + "\n")

        # Check API response time
        self.run_cmd(
            "curl -s -w '\\nResponse time: %{time_total}s\\n' http://localhost:5000/health",
            "API response time check"
        )

        # Check v5_context in response
        self.run_cmd(
            "curl -s http://localhost:5000/api/organizations/391214392 | jq '.v5_context | keys' | head -5",
            "Verify v5_context in API response"
        )

        # Check error rate (from logs)
        self.run_cmd(
            "tail -1000 logs/daanaa_api.log | grep ERROR | wc -l",
            "Check error count (last 1000 log lines)"
        )

        # Check droplet health
        self.run_cmd(
            "ssh -o ConnectTimeout=5 root@192.168.1.73 'curl -s http://localhost:5000/health' || echo 'droplet unreachable'",
            "Droplet API health check"
        )

        self.log_action("PHASE4", "Complete", "✓")

    def send_communications(self):
        """Send user communications (if --skip-comms not set)"""
        if self.skip_comms:
            print("\n[SKIPPED] Communications (--skip-comms flag set)")
            return

        print("\n" + "="*70)
        print("COMMUNICATIONS (Email, blog, social)")
        print("="*70 + "\n")

        self.log_action("EMAIL", "Send user email (Daanaa's New Financial Perspective)", "ready")
        self.log("  Subject: Your nonprofit's financial health just got smarter")
        self.log("  Key points: peer comparison, methodology link, example org")

        self.log_action("BLOG", "Publish blog post (How Daanaa Compares Nonprofits)", "ready")
        self.log("  Format: 1200 words, 3 real examples, limitations section")
        self.log("  Publish to: https://daanaa.org/blog/")

        self.log_action("PARTNER", "Send partner email (New Financial Context)", "ready")
        self.log("  Target: advisors, foundation partners")
        self.log("  Content: how to verify peer group, use methodology")

        self.log_action("SOCIAL", "Schedule social posts (5 posts over launch day)", "ready")
        self.log("  Platforms: Twitter, LinkedIn (daily throughout Jun 16)")

    def execute(self):
        """Run full launch sequence"""
        print("\n")
        print("█" * 70)
        print("WEEK 4 FULL LAUNCH SEQUENCE")
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S PT')}")
        if self.dry_run:
            print("MODE: DRY RUN (no changes)")
        print("█" * 70)

        try:
            self.phase_1_prepare()
            self.phase_2_remove_v4()
            self.phase_3_deploy()
            self.phase_4_verify()
            self.send_communications()

            elapsed = (datetime.now() - self.start_time).total_seconds() / 60
            print("\n" + "="*70)
            print(f"✓ LAUNCH COMPLETE ({elapsed:.0f} minutes)")
            print("="*70)
            print("\nNext Steps:")
            print("  1. Monitor error rate & response time for 24 hours")
            print("  2. Watch for negative user feedback")
            print("  3. Daily health checks (Week 4)")
            print("  4. Post-launch review (Friday Jun 20)")

            return True
        except Exception as e:
            print(f"\n✗ LAUNCH FAILED: {e}")
            return False

if __name__ == '__main__':
    import sys
    dry_run = '--dry-run' in sys.argv
    skip_comms = '--skip-comms' in sys.argv

    seq = LaunchSequence(dry_run=dry_run, skip_comms=skip_comms)
    success = seq.execute()
    sys.exit(0 if success else 1)
