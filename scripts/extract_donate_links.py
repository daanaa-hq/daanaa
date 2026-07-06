#!/usr/bin/env python3
"""
scripts/extract_donate_links.py

Extract donation links from all org websites on a rolling refresh cycle.
Independent of mission generation — processes all 1.7M orgs continuously.

Usage:
    python3 scripts/extract_donate_links.py
    python3 scripts/extract_donate_links.py --batch-size 5000
    python3 scripts/extract_donate_links.py --limit 100  # test run
"""

import sqlite3
import argparse
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from check_link_health import extract_donate_url

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'

_extracted = 0
_errors = 0
_skipped = 0


def extract_batch(batch_size=5000, refresh_days=30, limit=None, force_all=False):
    """
    Extract donation links from all orgs with cached HTML.
    Refreshes links that haven't been checked in refresh_days.
    If force_all=True, re-check all orgs regardless of last check time.
    """
    global _extracted, _errors, _skipped

    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row

    # Select orgs with cached HTML that haven't been checked recently
    if force_all:
        query = """
        SELECT re.EIN, re.organization_name
        FROM registry_enriched re
        INNER JOIN page_cache pc ON pc.ein = re.EIN
        WHERE pc.html_gz IS NOT NULL
        ORDER BY re.donate_checked_at ASC NULLS FIRST
        """
        params = ()
    else:
        refresh_cutoff = (datetime.now() - timedelta(days=refresh_days)).isoformat()
        query = """
        SELECT re.EIN, re.organization_name
        FROM registry_enriched re
        INNER JOIN page_cache pc ON pc.ein = re.EIN
        WHERE pc.html_gz IS NOT NULL
          AND (re.donate_checked_at IS NULL OR re.donate_checked_at < ?)
        ORDER BY re.donate_checked_at ASC NULLS FIRST
        """
        params = (refresh_cutoff,)

    if limit:
        query += f" LIMIT {limit}"
    else:
        query += f" LIMIT {batch_size}"

    rows = conn.execute(query, params).fetchall()
    total = len(rows)

    if total == 0:
        print(f"No orgs to process (all refreshed within {refresh_days} days)")
        conn.close()
        return 0

    print(f"Extracting donation links from {total:,} orgs...")

    updates = []
    now = datetime.now().isoformat()

    for i, org_row in enumerate(rows, 1):
        try:
            ein = org_row['EIN']

            # Get cached HTML
            html_row = conn.execute(
                "SELECT html_gz FROM page_cache WHERE ein = ? AND html_gz IS NOT NULL LIMIT 1",
                (ein,)
            ).fetchone()

            if not html_row or not html_row[0]:
                _skipped += 1
                continue

            # Decompress HTML
            import zlib
            try:
                html_bytes = zlib.decompress(html_row[0])
                html_str = html_bytes.decode('utf-8', errors='replace')
            except Exception:
                _errors += 1
                continue

            # Extract donate URL
            donate_url, platform = extract_donate_url(html_str)

            if donate_url:
                updates.append((
                    donate_url,
                    platform or "",
                    85,  # confidence: AI-extracted
                    "ai_suggested",  # status: org can claim
                    now,
                    ein
                ))
                _extracted += 1

            # Progress
            if i % 500 == 0 or i == total:
                print(f"  [{i}/{total}] {_extracted} extracted, {_errors} errors, {_skipped} skipped")

        except Exception as e:
            _errors += 1
            if i % 1000 == 0:
                print(f"    Error on {ein}: {str(e)[:60]}")

    # Write all updates
    if updates:
        conn.executemany(
            """UPDATE registry_enriched SET
               donate_url=?, donate_platform=?, donate_confidence=?,
               donate_url_status=?, donate_checked_at=? WHERE EIN=?""",
            updates
        )
        conn.commit()
        print(f"✓ Updated {len(updates)} donation links")

    conn.close()
    return len(updates)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Extract donation links from all org websites")
    ap.add_argument("--batch-size", type=int, default=5000, help="Orgs per run")
    ap.add_argument("--limit", type=int, help="Test run limit")
    ap.add_argument("--refresh-days", type=int, default=30, help="Re-check links older than N days")
    ap.add_argument("--all", action="store_true", help="Force re-check all orgs (ignore refresh-days)")
    args = ap.parse_args()

    try:
        count = extract_batch(
            batch_size=args.batch_size,
            refresh_days=args.refresh_days,
            limit=args.limit,
            force_all=args.all
        )
        print(f"\nDone: {_extracted} extracted, {_errors} errors, {_skipped} skipped")
    except Exception as e:
        print(f"FATAL: {str(e)}")
        sys.exit(1)
