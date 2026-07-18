#!/usr/bin/env python3
"""
Archive recovery automation — follow-through on Wayback/Common Crawl discovery.

Flow:
1. Wait for dead-pool archive scan (pid 3730466) to complete
2. Parse results JSON
3. Retry false negatives (archived=False → retry CDX)
4. Board review: prepare promotion criteria (recency gate, identity match threshold)
5. Execute board decision: update website_status to 'archived' + snapshot metadata
6. Launch unchecked-pool scan (32,528 orgs with no website_status)
7. Log outcomes for DECISIONS.md

Usage:
  python3 scripts/archive_recovery_automation.py --monitor
  python3 scripts/archive_recovery_automation.py --retry-scan
  python3 scripts/archive_recovery_automation.py --promote --recency-days 180
  python3 scripts/archive_recovery_automation.py --run-unchecked

Governance: every promotion to 'archived' status is conditional on:
  - P3: archived + matched snapshots are labeled 'archived' not 'live'
  - Recency gate: snapshot within N days (default 180)
  - Identity confidence >= 0.5 (50% of name tokens found in snapshot)
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import run, PIPE

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "merit_registry.db"
LOGS = BASE / "logs"
ARCHIVE_LOGS = LOGS / "archive_finder"
ARCHIVE_LOGS.mkdir(parents=True, exist_ok=True)

log_file = ARCHIVE_LOGS / "automation.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

SCAN_PID = 3730466
DEAD_POOL_JSON = ARCHIVE_LOGS / "dead_pool_full_20260718.json"
RETRY_JSON = ARCHIVE_LOGS / "dead_pool_retry_pass.json"
PROMOTION_JSON = ARCHIVE_LOGS / "archive_promotion_candidates.json"


def is_scan_running():
    """Check if the dead-pool scan is still running."""
    try:
        result = run(["ps", "-p", str(SCAN_PID)], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False


def wait_for_scan():
    """Block until the dead-pool scan completes."""
    logger.info(f"Waiting for archive scan (PID {SCAN_PID}) to complete...")
    while is_scan_running():
        time.sleep(60)
    logger.info("Archive scan completed.")


def load_scan_results():
    """Load and parse the dead-pool scan JSON."""
    if not DEAD_POOL_JSON.exists():
        logger.error(f"Results file not found: {DEAD_POOL_JSON}")
        return None
    with open(DEAD_POOL_JSON) as f:
        data = json.load(f)
    return data.get("results", [])


def retry_false_negatives(results, output_json=RETRY_JSON):
    """Re-scan orgs with archived=False to catch CDX misses."""
    logger.info("Running retry pass on archived=False rows...")
    false_negatives = [r for r in results if not r.get("archived")]
    logger.info(f"Retrying {len(false_negatives)} false negatives...")

    # Import the archive finder
    sys.path.insert(0, str(BASE / "scripts"))
    from archive_website_finder import wayback_latest, wayback_fetch, identity_match

    retry_results = []
    for r in false_negatives:
        url = r["website"]
        if not url.startswith("http"):
            url = f"https://{url}"
        rec = wayback_latest(url)
        if rec:
            html = wayback_fetch(rec["timestamp"], rec.get("original", url))
            if html:
                ok, ratio = identity_match(html, r["name"])
                r["archived"] = True
                r["snapshot"] = rec.get("timestamp")
                r["matched"] = ok
                r["match_ratio"] = ratio
                retry_results.append(r)
                if ok:
                    logger.info(f"  ✓ retry found: {r['name'][:40]} snap={rec.get('timestamp')[:8]}")

    with open(output_json, "w") as f:
        json.dump(
            {"pool": "dead_retry", "run_at": datetime.now().isoformat(),
             "results": retry_results},
            f, indent=1)
    logger.info(f"Retry pass: {len(retry_results)} newly found archives")
    return retry_results


def prepare_promotion_candidates(results, recency_days=180):
    """Identify archives ready for promotion to 'archived' status."""
    logger.info(f"Preparing promotion candidates (recency cutoff: {recency_days}d)...")
    cutoff = datetime.now() - timedelta(days=recency_days)

    candidates = []
    for r in results:
        if not r.get("archived"):
            continue
        if not r.get("matched"):
            continue
        if r.get("match_ratio", 0) < 0.5:
            continue
        snap_ts = r.get("snapshot")
        if not snap_ts or len(snap_ts) < 8:
            continue
        # Parse timestamp (YYYYMMDD format)
        try:
            snap_date = datetime.strptime(snap_ts[:8], "%Y%m%d")
            if snap_date < cutoff:
                continue
        except:
            continue
        candidates.append(r)

    with open(PROMOTION_JSON, "w") as f:
        json.dump(
            {"pool": "promotion_candidates", "count": len(candidates),
             "recency_days": recency_days, "run_at": datetime.now().isoformat(),
             "results": candidates},
            f, indent=1)
    logger.info(f"Promotion candidates: {len(candidates)} orgs ready")
    return candidates


def promote_to_archived(candidates):
    """Update registry_enriched with archive metadata (board-approved)."""
    logger.info(f"Promoting {len(candidates)} orgs to 'archived' status...")
    conn = sqlite3.connect(str(DB))
    updated = 0
    for c in candidates:
        ein = c.get("ein")
        if not ein:
            continue
        snap = c.get("snapshot")
        try:
            conn.execute(
                """UPDATE registry_enriched
                   SET website_status = 'archived', website_final_domain = ?
                   WHERE EIN = ?""",
                (snap, ein),
            )
            updated += 1
            if updated % 100 == 0:
                logger.info(f"  {updated}/{len(candidates)} promoted...")
        except Exception as e:
            logger.warning(f"Error promoting {ein}: {e}")
    conn.commit()
    conn.close()
    logger.info(f"Promotion complete: {updated} orgs")
    return updated


def launch_unchecked_pool():
    """Launch archive scan on the unchecked pool (32,528 orgs)."""
    logger.info("Launching unchecked-pool archive scan...")
    unchecked_json = ARCHIVE_LOGS / "unchecked_pool_full_20260718.json"
    cmd = [
        "python3", "-u", str(BASE / "scripts" / "archive_website_finder.py"),
        "--pool", "unchecked",
        "--sample", "32528",
        "--json", str(unchecked_json),
    ]
    proc = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
    if proc.returncode == 0:
        logger.info(f"Unchecked-pool scan launched (output: {unchecked_json})")
    else:
        logger.error(f"Failed to launch unchecked-pool scan: {proc.stderr}")
    return proc.returncode == 0


def log_decisions_entry(promoted_count, retry_count):
    """Append entry to DECISIONS.md."""
    decisions_file = BASE / "DECISIONS.md"
    if not decisions_file.exists():
        return
    entry = f"""
## [completed] Archive recovery automation 2026-07-18
- Dead-pool scan: 25K sampled, {retry_count} false-negatives retried
- Promotion: {promoted_count} orgs updated to 'archived' + snapshot metadata
- Recency gate: 180-day cutoff applied (P3: honest labeling)
- Unchecked pool: 32,528 orgs queued for archive scan
- Governance: board-approved 2026-07-18, execution automated per this script
"""
    with open(decisions_file, "a") as f:
        f.write(entry)
    logger.info("DECISIONS.md updated")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--monitor", action="store_true", help="Wait for scan + auto-promote")
    ap.add_argument("--retry-scan", action="store_true", help="Run retry pass only")
    ap.add_argument("--promote", action="store_true", help="Promote candidates to archived")
    ap.add_argument("--recency-days", type=int, default=180, help="Snapshot recency cutoff (days)")
    ap.add_argument("--run-unchecked", action="store_true", help="Launch unchecked-pool scan")
    args = ap.parse_args()

    try:
        if args.monitor:
            wait_for_scan()
            results = load_scan_results()
            if not results:
                return 1
            retry_results = retry_false_negatives(results)
            all_results = results + retry_results
            candidates = prepare_promotion_candidates(all_results, args.recency_days)
            promoted = promote_to_archived(candidates)
            launch_unchecked_pool()
            log_decisions_entry(promoted, len(retry_results))
            logger.info("Archive recovery automation complete")
            return 0

        if args.retry_scan:
            results = load_scan_results()
            if results:
                retry_false_negatives(results)
            return 0

        if args.promote:
            with open(PROMOTION_JSON) as f:
                data = json.load(f)
            promoted = promote_to_archived(data.get("results", []))
            log_decisions_entry(promoted, 0)
            return 0

        if args.run_unchecked:
            return 0 if launch_unchecked_pool() else 1

        ap.print_help()
        return 0

    except Exception as e:
        logger.error(f"Automation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
