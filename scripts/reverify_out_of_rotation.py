#!/usr/bin/env python3
"""
One-shot re-verification of beta donate links outside the freshness rotation.

Targets (found 2026-07-19): beta links with donate_checked_at NULL (never
re-checked since promotion) or older than 30 days. Verified links stay beta
and get a fresh stamp; failures move to human_review (non-destructive — the
existing triage queue decides, per the 75-confidence founder exception flow).

Usage:
  python3 scripts/reverify_out_of_rotation.py --dry-run
  python3 scripts/reverify_out_of_rotation.py --confirm [--workers 8]
"""

import sys
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import local

sys.path.insert(0, str(Path(__file__).parent))
from verify_discovered_links import LinkVerifier

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
_tl = local()


def _verifier():
    if not hasattr(_tl, 'v'):
        _tl.v = LinkVerifier(timeout=10)
    return _tl.v


def check(row):
    ein, url = row
    result = _verifier().verify_donation_link(url)
    return ein, url, bool(result.get('verified')), result.get('reason', '')


def main(confirm: bool, workers: int = 8):
    db = sqlite3.connect(str(DB), timeout=30)
    rows = db.execute("""
        SELECT EIN, donate_url FROM registry_enriched
        WHERE donate_url_status = 'beta'
          AND (donate_checked_at IS NULL
               OR julianday('now') - julianday(donate_checked_at) > 30)
    """).fetchall()
    print(f"out-of-rotation beta links: {len(rows)}")
    if not confirm:
        print("DRY RUN — no changes. Use --confirm to verify and stamp.")
        return

    now = datetime.now().isoformat()
    ok = failed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(check, r) for r in rows]
        for fut in as_completed(futures):
            try:
                ein, url, verified, reason = fut.result()
            except Exception as e:
                failed += 1
                print(f"  ! worker error: {str(e)[:80]}")
                continue
            if verified:
                ok += 1
                db.execute(
                    "UPDATE registry_enriched SET donate_checked_at=? WHERE EIN=?",
                    (now, ein))
            else:
                failed += 1
                db.execute(
                    "UPDATE registry_enriched SET donate_url_status='human_review', "
                    "donate_checked_at=? WHERE EIN=?", (now, ein))
                print(f"  ✗ {ein}: {reason[:60]} → human_review")
            if (ok + failed) % 100 == 0:
                db.commit()
                print(f"  … {ok + failed}/{len(rows)} (ok={ok}, failed={failed})")
    db.commit()
    db.close()
    print(f"done: {ok} verified (stay beta), {failed} → human_review")


if __name__ == '__main__':
    confirm = '--confirm' in sys.argv
    workers = 8
    if '--workers' in sys.argv:
        workers = int(sys.argv[sys.argv.index('--workers') + 1])
    main(confirm, workers)
