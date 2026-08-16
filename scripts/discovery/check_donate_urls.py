#!/usr/bin/env python3
"""
scripts/check_donate_urls.py

Health-checks all donate_url entries in registry_enriched.
Adds donate_url_status column: 'ok' | 'dead' | 'unknown'

Platforms that can't be reliably validated by HEAD (paypal, venmo) → 'ok' by default.
Dead = 4xx response from the donation platform.

Usage:
    python3 scripts/check_donate_urls.py
    python3 scripts/check_donate_urls.py --workers 20
    python3 scripts/check_donate_urls.py --dry-run
"""

import sqlite3, urllib.request, urllib.error, argparse, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"

# These platforms return 200 for any URL (even invalid) — can't validate by status code
SKIP_CHECK_PLATFORMS = {"paypal", "venmo"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MeritGiving link checker)",
    "Accept": "text/html",
}


def check_url(ein: str, url: str, platform: str) -> tuple[str, str]:
    """Returns (ein, status) where status is 'ok' | 'dead' | 'unknown'."""
    if platform in SKIP_CHECK_PLATFORMS:
        return ein, "ok"

    try:
        req = urllib.request.Request(url, headers=HEADERS, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception:
        # Timeout, connection refused, SSL error — treat as unknown
        return ein, "unknown"

    if code in (200, 201, 301, 302, 303, 307, 308):
        return ein, "ok"
    if code in (400, 403, 404, 405, 410, 451):
        return ein, "dead"
    # 429 rate limit, 5xx server error — don't penalise the org
    return ein, "unknown"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = sqlite3.connect(DB_PATH, timeout=30)
    db.execute("PRAGMA journal_mode=WAL")

    # Add column if missing
    cols = {r[1] for r in db.execute("PRAGMA table_info(registry_enriched)")}
    if "donate_url_status" not in cols:
        db.execute("ALTER TABLE registry_enriched ADD COLUMN donate_url_status TEXT")
        db.commit()
        print("[schema] added donate_url_status column")

    rows = db.execute("""
        SELECT EIN, donate_url, donate_platform
        FROM registry_enriched
        WHERE donate_url IS NOT NULL AND donate_url != ''
    """).fetchall()

    total = len(rows)
    print(f"[check] {total} donate URLs  workers={args.workers}")

    if args.dry_run:
        for ein, url, platform in rows[:5]:
            print(f"  [{platform}] {url}")
        print(f"\n[dry-run] would check {total} URLs — no writes")
        return

    results: dict[str, str] = {}
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(check_url, ein, url, platform or ""): ein
                for ein, url, platform in rows}
        for i, fut in enumerate(as_completed(futs), 1):
            ein, status = fut.result()
            results[ein] = status
            if i % 50 == 0:
                elapsed = time.time() - t0
                print(f"  {i}/{total}  ({elapsed:.0f}s)")

    # Write results
    for ein, status in results.items():
        db.execute(
            "UPDATE registry_enriched SET donate_url_status=? WHERE EIN=?",
            (status, ein)
        )
    db.commit()

    counts = {"ok": 0, "dead": 0, "unknown": 0}
    for s in results.values():
        counts[s] = counts.get(s, 0) + 1

    print(f"\n[done] in {time.time()-t0:.0f}s")
    print(f"  ok:      {counts['ok']}")
    print(f"  dead:    {counts['dead']}")
    print(f"  unknown: {counts['unknown']}")

    # Show dead ones
    dead = [(ein, url) for ein, url, _ in rows if results.get(ein) == "dead"]
    if dead:
        print(f"\n[dead donate URLs — {len(dead)} total]")
        for ein, url in dead[:20]:
            name = db.execute("SELECT organization_name FROM registry_enriched WHERE EIN=?", (ein,)).fetchone()
            print(f"  {(name[0] if name else ein)[:45]:45}  {url[:60]}")


if __name__ == "__main__":
    main()
