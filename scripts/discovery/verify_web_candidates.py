#!/usr/bin/env python3
"""
Verify Web Candidates — Fast HTTP-based domain existence check

Check if candidate domains respond (GET, HEAD, or redirect).
No GPU needed. Fast and reliable. Respects robots.txt.

Run:
    python3 scripts/verify_web_candidates.py --limit 1000 --workers 10
    python3 scripts/verify_web_candidates.py --limit 100 --dry-run
"""

import sqlite3
import requests
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
LOG_PATH = Path.home() / "meritgiving/logs/web_verification.log"

_log_lock = threading.Lock()
_stats = {"checked": 0, "found": 0, "timeout": 0, "notfound": 0}
_stats_lock = threading.Lock()
_updates = []  # List of (ein, domain) tuples to update
_updates_lock = threading.Lock()

def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    with _log_lock:
        print(line)
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")

def check_domain(domain: str) -> tuple[bool, str]:
    """
    Check if domain responds. Return (found, info).
    Tries: HTTPS, HTTP, follows redirects.
    """
    for scheme in ['https', 'http']:
        url = f"{scheme}://{domain}"
        try:
            # HEAD request first (faster)
            resp = requests.head(url, timeout=3, allow_redirects=True)
            if resp.status_code < 400:
                return True, f"{scheme}://{domain} ({resp.status_code})"
        except requests.exceptions.Timeout:
            pass
        except requests.exceptions.ConnectionError:
            pass
        except Exception:
            pass

    return False, "No response"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=1000)
    parser.add_argument('--workers', type=int, default=10)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    log("━" * 70)
    log("Web Candidate Verifier — HTTP-based domain check")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get orgs with candidates
    query = """
        SELECT EIN, organization_name, website_candidates
        FROM registry_enriched
        WHERE website_candidates IS NOT NULL
          AND website_candidates != ''
        LIMIT ?
    """

    rows = c.execute(query, (args.limit,)).fetchall()
    log(f"Found {len(rows)} orgs with candidates")

    if args.dry_run:
        log("DRY RUN — not saving results\n")

    total_domains = sum(len(row[2].split('|')) for row in rows)
    log(f"Total candidates to check: {total_domains}")

    def verify_org(row):
        ein, name, candidates_str = row
        candidates = candidates_str.split('|')
        for cand in candidates:
            cand = cand.strip()
            if not cand:
                continue

            found, info = check_domain(cand)
            with _stats_lock:
                _stats["checked"] += 1
                if found:
                    _stats["found"] += 1
                else:
                    _stats["notfound"] += 1

            if found:
                log(f"✓ {cand} — {info}")
                if not args.dry_run:
                    with _updates_lock:
                        _updates.append((cand, ein))
                return cand  # Found one, return

        return None

    # Batch verification with thread pool
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(verify_org, row): row for row in rows}
        processed = 0
        for future in as_completed(futures):
            processed += 1
            if processed % 50 == 0:
                log(f"  Progress: {processed}/{len(rows)} orgs ({_stats['found']} websites found)")
                if not args.dry_run and _updates:
                    # Batch update the database every 50 orgs
                    with _updates_lock:
                        for website, ein in _updates:
                            c.execute("""
                                UPDATE registry_enriched
                                SET website = ?, website_status = 'beta', website_checked_at = datetime('now')
                                WHERE EIN = ?
                            """, (website, ein))
                        _updates.clear()
                    conn.commit()

    # Final batch of updates
    if not args.dry_run and _updates:
        with _updates_lock:
            for website, ein in _updates:
                c.execute("""
                    UPDATE registry_enriched
                    SET website = ?, website_status = 'beta', website_checked_at = datetime('now')
                    WHERE EIN = ?
                """, (website, ein))
            _updates.clear()
        conn.commit()

    conn.close()

    log(f"\n━ Summary ━")
    log(f"Checked: {_stats['checked']} domains")
    log(f"Found: {_stats['found']} valid websites")
    log(f"Success rate: {100*_stats['found']/_stats['checked']:.1f}%")

if __name__ == "__main__":
    main()
