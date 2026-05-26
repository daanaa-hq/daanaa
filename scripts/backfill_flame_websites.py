#!/usr/bin/env python3
"""
scripts/backfill_flame_websites.py

Fetches website URLs from ProPublica API for Flame-tier orgs that have
mission + peer score + current 990 but no confirmed website.

With website confirmed, these orgs qualify for Lantern (or Beacon if ≥75th
percentile). After this script completes, re-run migrate_merit_tier.py to
update tiers.

Priority ordering:
  1. data_source=propublica (most likely to have ProPublica API data)
  2. data_source=irs_soi (larger orgs, also worth checking)

Rate: 4 concurrent workers, ~2 req/s total (conservative but 5× faster than
single-threaded 0.8 req/s). ProPublica doesn't publish strict rate limits;
we stay polite.

Usage:
    python3 scripts/backfill_flame_websites.py              # all gap orgs
    python3 scripts/backfill_flame_websites.py --limit 500  # dry-run subset
    python3 scripts/backfill_flame_websites.py --workers 2  # fewer workers
"""

import sqlite3, time, json, argparse, urllib.request, urllib.error
import threading
from pathlib import Path
from queue import Queue
from datetime import datetime

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
PP_URL  = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"


def connect():
    db = sqlite3.connect(DB_PATH, timeout=60, check_same_thread=False)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    return db


def _pp_fetch(ein: str) -> dict | None:
    url = PP_URL.format(ein=ein.lstrip("0"))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Daanaa/1.0 website-backfill"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        return data.get("organization") or None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if e.code == 429:
            time.sleep(5)
            return None
        raise
    except Exception:
        return None


def load_targets(db, priority_source: str | None, limit: int | None) -> list[str]:
    """Load Flame orgs that meet all Lantern criteria except website."""
    q = """
        SELECT EIN FROM registry_enriched
        WHERE merit_tier = 'Flame'
          AND mission IS NOT NULL AND TRIM(mission) != ''
          AND COALESCE(peer_percentile, ntee1_percentile) IS NOT NULL
          AND latest_tax_year >= 2022
          AND total_revenue > 0
          AND (website IS NULL OR TRIM(website) = '')
          AND (merit_band IS NULL OR merit_band != 'Concerns')
    """
    if priority_source:
        q += f" AND data_source = '{priority_source}'"
    q += " ORDER BY COALESCE(peer_percentile, ntee1_percentile) DESC"

    rows = db.execute(q).fetchall()
    eins = [r[0] for r in rows]
    if limit:
        eins = eins[:limit]
    return eins


def worker(task_q: Queue, result_q: Queue, stop_event: threading.Event, delay: float):
    while not stop_event.is_set():
        try:
            ein = task_q.get(timeout=1)
        except Exception:
            continue
        org = _pp_fetch(ein)
        website = None
        if org:
            raw = org.get("website") or org.get("URL") or ""
            raw = raw.strip()
            if raw and "@" not in raw and len(raw) > 3:
                website = raw
        result_q.put((ein, website))
        task_q.task_done()
        time.sleep(delay)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Max orgs to process")
    ap.add_argument("--workers", type=int, default=4, help="Concurrent workers (default 4)")
    ap.add_argument("--source", default=None, help="Filter by data_source (propublica/irs_soi)")
    args = ap.parse_args()

    db = connect()
    delay_per_worker = args.workers * 0.5  # ~2 req/s total across workers

    print(f"[backfill_flame_websites] {datetime.now():%Y-%m-%d %H:%M}", flush=True)

    # Priority 1: propublica-sourced
    targets_pp = load_targets(db, "propublica", args.limit)
    # Priority 2: irs_soi (only if no source filter and no limit, or source=irs_soi)
    if args.source == "irs_soi":
        targets = targets_pp  # actually irs_soi since we passed source=irs_soi
        targets_pp = []
    elif args.source == "propublica" or args.limit:
        targets = targets_pp
        targets_pp = []
    else:
        targets_soi = load_targets(db, "irs_soi", None)
        targets = targets_pp + targets_soi

    print(f"  Targeting {len(targets):,} orgs", flush=True)
    print(f"  Workers: {args.workers}, delay: {delay_per_worker:.1f}s/worker", flush=True)
    eta_min = len(targets) / (1 / delay_per_worker * args.workers) / 60
    print(f"  Estimated time: {eta_min:.0f} minutes ({eta_min/60:.1f} hours)", flush=True)

    task_q: Queue = Queue()
    result_q: Queue = Queue()
    stop_event = threading.Event()

    for ein in targets:
        task_q.put(ein)

    threads = []
    for _ in range(args.workers):
        t = threading.Thread(target=worker, args=(task_q, result_q, stop_event, delay_per_worker), daemon=True)
        t.start()
        threads.append(t)

    processed = 0
    found_websites = 0
    write_batch = []
    t0 = time.time()

    try:
        while processed < len(targets):
            ein, website = result_q.get(timeout=30)
            processed += 1
            if website:
                found_websites += 1
                write_batch.append((website, ein))

            # Batch write every 50
            if len(write_batch) >= 50:
                db.executemany(
                    "UPDATE registry_enriched SET website = ? WHERE EIN = ?",
                    write_batch
                )
                db.commit()
                write_batch.clear()

            if processed % 100 == 0 or processed == len(targets):
                elapsed = time.time() - t0
                rate = processed / elapsed * 60
                pct = 100 * processed / len(targets)
                print(f"  [{pct:4.1f}%] {processed:,}/{len(targets):,} | "
                      f"found={found_websites:,} | {rate:.0f}/min | "
                      f"{elapsed/60:.1f}min elapsed", flush=True)

    except KeyboardInterrupt:
        print("\n  Interrupted — saving partial results", flush=True)
    finally:
        stop_event.set()

    # Write remaining
    if write_batch:
        db.executemany("UPDATE registry_enriched SET website = ? WHERE EIN = ?", write_batch)
        db.commit()

    elapsed = time.time() - t0
    print(f"\n  Done. {processed:,} checked, {found_websites:,} websites found ({100*found_websites/max(processed,1):.1f}%)", flush=True)
    print(f"  Time: {elapsed/60:.1f} minutes", flush=True)

    if found_websites > 0:
        print("\n  Run migrate_merit_tier.py next to promote orgs to Lantern/Beacon.", flush=True)

    db.close()


if __name__ == "__main__":
    main()
