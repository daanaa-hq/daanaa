#!/usr/bin/env python3
"""
Batch-promote discovered donation links to live ('beta') status.

The frontend only renders donate buttons when donate_url_status is
'beta' or 'claimed' (frontend/src/utils/actionRow.ts), so promotion is a
status flip — fully reversible, no schema change, no droplet contact.
The nightly search deploy ships the result to the droplet with integrity
checks and rollback.

Every link is re-verified with a live HTTP check before going 'beta',
regardless of how it was discovered (Stewardship P3: trust signals must
be evidence-based). Failures are marked 'dead', not silently kept.

Usage:
    python3 scripts/promote_links_batch.py --batch-size 500 --source verified
    python3 scripts/promote_links_batch.py --batch-size 500 --source gpu_verified
    python3 scripts/promote_links_batch.py --dry-run --batch-size 50
"""

import argparse
import logging
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify_discovered_links import LinkVerifier

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler('/home/akbar/meritgiving/logs/promote_links.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
# workers=2: at 8 workers the first canary run marked 324 live links dead —
# local network contention with the discovery pipeline plus per-IP rate
# limits on shared hosts (PayPal returned 429s). Verified 14/15 "dead"
# links were alive on sequential retry. Slow and honest beats fast and wrong.
VERIFY_WORKERS = 2
# Failures that prove the link is gone vs. failures that prove nothing.
# Only definitive failures may mark a link 'dead' (Stewardship P3/P6).
DEFINITIVE_FAILURES = ('HTTP 404', 'HTTP 410', 'HTTP 401', 'HTTP 403')


def get_candidates(source: str, batch_size: int):
    db = sqlite3.connect(str(DB), timeout=30)
    cur = db.cursor()
    cur.execute("""
        SELECT EIN, organization_name, donate_url
        FROM registry_enriched
        WHERE donate_url_status = ?
        AND donate_url IS NOT NULL AND donate_url != ''
        ORDER BY RANDOM()
        LIMIT ?
    """, (source, batch_size))
    rows = cur.fetchall()
    db.close()
    return rows


def verify_one(verifier, ein, name, url):
    try:
        result = verifier.verify_donation_link(url)
        return ein, name, url, bool(result.get('verified')), result.get('reason', '')
    except Exception as e:
        return ein, name, url, False, str(e)[:80]


def promote_batch(source: str, batch_size: int, dry_run: bool):
    candidates = get_candidates(source, batch_size)
    if not candidates:
        logger.info(f"No candidates with status '{source}'. Nothing to do.")
        return 0, 0

    logger.info(f"Batch: {len(candidates)} '{source}' links → re-verify → promote to 'beta'"
                f"{' (DRY RUN)' if dry_run else ''}")

    verifier = LinkVerifier(timeout=10)
    passed, first_fail = [], []

    with ThreadPoolExecutor(max_workers=VERIFY_WORKERS) as pool:
        futures = [pool.submit(verify_one, verifier, ein, name, url)
                   for ein, name, url in candidates]
        for i, fut in enumerate(as_completed(futures), 1):
            ein, name, url, ok, reason = fut.result()
            (passed if ok else first_fail).append((ein, name, url, reason))
            if i % 100 == 0:
                logger.info(f"  verified {i}/{len(candidates)} "
                            f"(pass {len(passed)}, fail {len(first_fail)})")

    # Sequential retry for first-pass failures — transient timeouts and
    # rate limits recover here.
    dead, inconclusive = [], []
    if first_fail:
        logger.info(f"Retrying {len(first_fail)} failures sequentially...")
        retry_verifier = LinkVerifier(timeout=15)
        for ein, name, url, _ in first_fail:
            _, _, _, ok, reason = verify_one(retry_verifier, ein, name, url)
            if ok:
                passed.append((ein, name, url, reason))
            elif any(d in reason for d in DEFINITIVE_FAILURES):
                dead.append((ein, url, reason))
            else:
                inconclusive.append((ein, url, reason))

    pass_rate = len(passed) / len(candidates) * 100
    logger.info(f"Verification: {len(passed)} passed, {len(dead)} definitively dead, "
                f"{len(inconclusive)} inconclusive (kept as-is) "
                f"({pass_rate:.1f}% pass rate)")

    if dry_run:
        logger.info("DRY RUN — no database changes made.")
        return len(passed), len(dead)

    now = datetime.now().isoformat()
    db = sqlite3.connect(str(DB), timeout=30)
    cur = db.cursor()
    for ein, name, url, _ in passed:
        cur.execute(
            "UPDATE registry_enriched SET donate_url_status = 'beta', "
            "donate_checked_at = ? WHERE EIN = ? AND donate_url_status = ?",
            (now, ein, source)
        )
    for ein, url, reason in dead:
        cur.execute(
            "UPDATE registry_enriched SET donate_url_status = 'dead', "
            "donate_checked_at = ? WHERE EIN = ? AND donate_url_status = ?",
            (now, ein, source)
        )
    # inconclusive links keep their source status — retried in a future batch
    db.commit()
    db.close()

    logger.info(f"✅ Promoted {len(passed)} links to 'beta'; {len(dead)} marked 'dead'; "
                f"{len(inconclusive)} left for retry.")
    return len(passed), len(dead)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch-promote verified links to beta (live)')
    parser.add_argument('--batch-size', type=int, default=500)
    parser.add_argument('--source', default='verified',
                        choices=['verified', 'gpu_verified', 'charity_navigator'])
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    promoted, dead = promote_batch(args.source, args.batch_size, args.dry_run)
    logger.info(f"Done: promoted={promoted}, dead={dead}")
