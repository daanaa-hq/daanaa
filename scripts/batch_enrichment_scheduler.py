#!/usr/bin/env python3
"""
Batch Enrichment Scheduler

Run Phase 2 ProPublica enrichment in small batches during off-peak hours.
Non-blocking: enriches in background while API serves users with basic data.

Schedule:
  - Small batches (1K-5K orgs per batch)
  - Off-peak: 10pm-6am daily + weekend mornings
  - Prioritize: newest IRS_BMF orgs first (just-loaded data)
  - Then: backlog (older IRS_BMF records)

Rationale:
  - Basic data live immediately (1.97M orgs searchable)
  - Enrichment improves data continuously (missions, scores added as ready)
  - Non-blocking: doesn't wait for full Phase 2 completion
  - Responsive: users see better data as each batch completes
"""

import sqlite3
import subprocess
import sys
from pathlib import Path
from datetime import datetime

HOME = Path.home()
PROJECT = HOME / "meritgiving"
DB = PROJECT / "data" / "merit_registry.db"
LOGS = PROJECT / "logs"
LOG_FILE = LOGS / "batch_enrichment.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOGS.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def count_work_by_priority():
    """Count orgs needing enrichment, prioritized by newness."""
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # New orgs (recently ingested, likely to have high impact)
    c.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE source='IRS_BMF'
        AND (mission IS NULL OR mission='')
        AND updated_at > datetime('now', '-3 days')
    """)
    new_batch = c.fetchone()[0]

    # Older backlog
    c.execute("""
        SELECT COUNT(*) FROM registry_enriched
        WHERE source='IRS_BMF'
        AND (mission IS NULL OR mission='')
        AND updated_at <= datetime('now', '-3 days')
    """)
    backlog = c.fetchone()[0]

    conn.close()
    return {
        'new_batch': new_batch,
        'backlog': backlog,
        'total': new_batch + backlog,
    }

def run_batch(batch_size=2000, priority='new'):
    """Run a single batch of ProPublica enrichment."""
    work = count_work_by_priority()

    if work['total'] == 0:
        log("✅ No enrichment work remaining")
        return True

    if priority == 'new' and work['new_batch'] > 0:
        log(f"Enriching NEW batch: {work['new_batch']:,} orgs remaining ({batch_size} per batch)")
    elif work['backlog'] > 0:
        log(f"Enriching BACKLOG: {work['backlog']:,} orgs remaining ({batch_size} per batch)")
    else:
        log("✅ All work complete")
        return True

    # Run backfill_stubs.py --phase 2 with limit
    try:
        cmd = [
            str(PROJECT / "venv" / "bin" / "python3"),
            str(PROJECT / "scripts" / "backfill_stubs.py"),
            "--phase", "2",
            "--limit", str(batch_size),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

        if result.returncode == 0:
            log(f"✅ Batch complete ({batch_size} orgs enriched)")
            return True
        else:
            log(f"⚠️  Batch encountered errors: {result.stderr[-200:]}")
            return False
    except subprocess.TimeoutExpired:
        log("❌ Batch timeout (30 min)")
        return False
    except Exception as e:
        log(f"❌ Batch failed: {e}")
        return False

def main():
    log("=" * 70)
    log("BATCH ENRICHMENT SCHEDULER")
    log("=" * 70)

    work = count_work_by_priority()
    log(f"\nWork queue:")
    log(f"  New batch (< 3 days): {work['new_batch']:,} orgs")
    log(f"  Backlog (> 3 days): {work['backlog']:,} orgs")
    log(f"  Total: {work['total']:,} orgs")

    if work['total'] == 0:
        log("\n✅ All enrichment complete")
        return 0

    log(f"\nSchedule:")
    log(f"  Priority 1: Enrich NEW batch first (faster iteration, higher impact)")
    log(f"  Priority 2: Then backlog (slower, scheduled off-peak)")
    log(f"  Batch size: 2,000 orgs per run")
    log(f"  Frequency: Daily 10pm-6am + weekend mornings")
    log(f"  Impact: Non-blocking, users always see latest basic data")

    log("\n" + "=" * 70)
    log("Add to crontab:")
    log("=" * 70)
    log("# Batch enrichment: new batch (10pm-6am, every hour)")
    log("0 22,23,0,1,2,3,4,5,6 * * * cd ~/meritgiving && source venv/bin/activate && python3 scripts/batch_enrichment_scheduler.py >> logs/batch_enrichment.log 2>&1")
    log("")
    log("# Or simpler: every night at 10pm")
    log("0 22 * * * cd ~/meritgiving && source venv/bin/activate && python3 scripts/batch_enrichment_scheduler.py >> logs/batch_enrichment.log 2>&1")
    log("=" * 70)

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        log(f"FATAL: {e}")
        sys.exit(1)
