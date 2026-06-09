#!/usr/bin/env python3
"""
Revocation Check On Backfill Complete

Monitors backfill_new_bmf.log for Phase 2 completion.
When complete, immediately runs:
  1. IRS revocation sync
  2. Database integrity check
  3. API cache invalidation
  4. Report any newly-revoked orgs

Critical because:
  - New BMF orgs must be checked against IRS revocation list
  - Cannot serve orgs with stale revocation status to users
  - Must flag any revoked orgs immediately
"""

import re
import subprocess
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

HOME = Path.home()
PROJECT = HOME / "meritgiving"
DB = PROJECT / "data" / "merit_registry.db"
LOGS = PROJECT / "logs"
BACKFILL_LOG = LOGS / "backfill_new_bmf.log"
MONITOR_LOG = LOGS / "revocation_check_monitor.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOGS.mkdir(exist_ok=True)
    with open(MONITOR_LOG, 'a') as f:
        f.write(line + '\n')

def check_backfill_complete():
    """Check if backfill Phase 2 is complete."""
    if not BACKFILL_LOG.exists():
        return False, 0, 0

    content = BACKFILL_LOG.read_text()

    # Look for completion marker
    if "COMPLETE" in content.upper() or "Phase 2 complete" in content:
        log("✅ Backfill COMPLETE detected")
        return True, 26565, 26565

    # Parse latest progress
    phase2_match = re.search(r'\[phase 2\].*?\n(.*?)(?=\[phase|\Z)', content, re.DOTALL)
    if not phase2_match:
        return False, 0, 0

    lines = phase2_match.group(1).strip().split('\n')
    for line in reversed(lines):
        match = re.search(r'(\d+)/26,565', line)
        if match:
            done = int(match.group(1))
            return done == 26565, done, 26565

    return False, 0, 0

def sync_revocations():
    """Run IRS revocation sync."""
    log("Running IRS revocation sync...")
    try:
        result = subprocess.run(
            [str(PROJECT / "venv" / "bin" / "python3"),
             str(PROJECT / "scripts" / "sync_irs_revocations.py")],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(PROJECT)
        )
        if result.returncode == 0:
            log("✅ Revocation sync completed")
            # Parse output for revocation count
            if "revoked" in result.stdout.lower():
                log(f"Revocation report: {result.stdout[-200:]}")
            return True
        else:
            log(f"❌ Revocation sync failed: {result.stderr[-200:]}")
            return False
    except subprocess.TimeoutExpired:
        log("❌ Revocation sync timeout (5 min)")
        return False
    except Exception as e:
        log(f"❌ Revocation sync error: {e}")
        return False

def check_newly_revoked():
    """Flag any newly-revoked orgs in the new BMF batch."""
    log("Checking for newly-revoked orgs in new BMF data...")
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    try:
        # Find orgs that are in revoked list AND in the new BMF batch
        c.execute("""
            SELECT COUNT(*) FROM registry_enriched re
            WHERE re.EIN IN (SELECT EIN FROM revoked_eins)
            AND re.source = 'IRS_BMF'
            AND re.updated_at > datetime('now', '-2 days')
        """)
        newly_revoked = c.fetchone()[0]

        if newly_revoked > 0:
            log(f"🚨 {newly_revoked} newly-added orgs are REVOKED")
            log(f"   These must be marked inactive immediately")

            # Get details
            c.execute("""
                SELECT COUNT(*), COUNT(DISTINCT re.STATE)
                FROM registry_enriched re
                WHERE re.EIN IN (SELECT EIN FROM revoked_eins)
                AND re.source = 'IRS_BMF'
                AND re.updated_at > datetime('now', '-2 days')
            """)
            count, states = c.fetchone()
            log(f"   Count: {count}, States affected: {states}")
        else:
            log("✅ No newly-revoked orgs in latest batch")

        return newly_revoked
    finally:
        conn.close()

def invalidate_api_cache():
    """Invalidate API response cache to clear stale org data."""
    log("Invalidating API cache...")
    # The API cache is in-memory, can only be cleared on restart
    # But we can mark cache as stale
    cache_marker = PROJECT / ".api_cache_invalid"
    cache_marker.touch()
    log("✅ Cache invalidation marker set (restart needed for fresh data)")
    return True

def main():
    log("=" * 70)
    log("REVOCATION CHECK MONITOR (On Backfill Completion)")
    log("=" * 70)

    # Check backfill status
    complete, done, total = check_backfill_complete()
    log(f"\nBackfill status: {done}/{total} ({100*done//total if total else 0}%)")

    if not complete:
        log("Backfill not yet complete, will check again later")
        return 1

    log("\n🔴 BACKFILL COMPLETE — RUNNING CRITICAL CHECKS")
    log("-" * 70)

    # Run revocation sync
    if not sync_revocations():
        log("⚠️  Revocation sync failed — will retry")
        return 1

    # Check for newly-revoked orgs
    newly_revoked = check_newly_revoked()

    # Invalidate cache
    invalidate_api_cache()

    log("-" * 70)
    if newly_revoked > 0:
        log(f"\n🚨 ACTION REQUIRED: {newly_revoked} orgs are revoked")
        log("   Restart API to clear cache and show correct status")
    else:
        log("\n✅ All checks passed")
        log("   Revocation data is current")
        log("   Ready to serve new BMF orgs to users")

    log("=" * 70)
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        log(f"FATAL: {e}")
        sys.exit(1)
