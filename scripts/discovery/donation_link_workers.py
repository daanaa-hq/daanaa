#!/usr/bin/env python3
"""
scripts/donation_link_workers.py

Multi-process donation link discovery orchestrator.

Spawns N worker processes that each claim batches from a priority work queue,
then run Phase 1 discovery concurrently. Workers don't duplicate work because
each batch is atomically claimed. Uses WAL-mode SQLite for concurrent writes.

Priority order: Major → Large → Medium → Small → Micro/Nano

Usage:
    # Populate queue, run 4 workers, auto-release after each batch
    python3 scripts/donation_link_workers.py

    # Just populate the queue (no workers)
    python3 scripts/donation_link_workers.py --queue-only

    # Custom worker count and threads per worker
    python3 scripts/donation_link_workers.py --workers 6 --threads 12

    # Status report only
    python3 scripts/donation_link_workers.py --status

    # Release pending links to the public directory
    python3 scripts/donation_link_workers.py --release
"""

import argparse
import multiprocessing
import os
import random
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
BATCH_SIZE = 50          # EINs claimed per worker per round
CLAIM_TIMEOUT_MIN = 30   # re-claim abandoned batches after this many minutes

# Revenue band → priority (1 = highest)
_BAND_PRIORITY = {"Major": 1, "Large": 2, "Medium": 3, "Small": 4, "Micro": 5, "Nano": 6}

from scripts.donation_link_pipeline import (
    _discover_one,
    write_evidence,
    queue_for_review,
    block_domain,
    domain_of,
    _now,
    cache_page,
    init_schema,
)


# ── Schema ────────────────────────────────────────────────────────────────────

_QUEUE_SCHEMA = """
CREATE TABLE IF NOT EXISTS donate_work_queue (
    ein         TEXT PRIMARY KEY,
    priority    INTEGER DEFAULT 5,
    queued_at   TEXT,
    claimed_at  TEXT,
    claimed_by  TEXT,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_dwq_priority ON donate_work_queue(priority, queued_at)
    WHERE completed_at IS NULL;
"""


def init_queue_schema(db: sqlite3.Connection):
    db.executescript(_QUEUE_SCHEMA)
    db.commit()


# ── Queue population ──────────────────────────────────────────────────────────

def populate_queue(db: sqlite3.Connection) -> int:
    """Add orgs with websites but no checked donate link. Returns new rows added."""
    rows = db.execute("""
        SELECT r.EIN,
               COALESCE(r.revenue_band, 'Nano') as band
        FROM registry_enriched r
        WHERE r.website IS NOT NULL AND TRIM(r.website) != ''
          AND (r.donate_url IS NULL OR TRIM(r.donate_url) = '')
          AND (r.donate_url_status IS NULL
               OR r.donate_url_status NOT IN (
                   'ok','blocked_or_restricted','pending_review',
                   'human_review','no_link_found','rejected'
               ))
          AND NOT EXISTS (
              SELECT 1 FROM donate_work_queue q WHERE q.ein = r.EIN
          )
    """).fetchall()

    if not rows:
        print("[queue] nothing new to add")
        return 0

    to_insert = [
        (ein, _BAND_PRIORITY.get(band, 6), _now())
        for ein, band in rows
    ]
    db.executemany(
        "INSERT OR IGNORE INTO donate_work_queue (ein, priority, queued_at) VALUES (?,?,?)",
        to_insert,
    )
    db.commit()
    print(f"[queue] added {len(to_insert):,} EINs to work queue")
    return len(to_insert)


# ── Queue stats ───────────────────────────────────────────────────────────────

def print_status(db: sqlite3.Connection):
    total, done, claimed, waiting = db.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(completed_at) as done,
            COUNT(CASE WHEN claimed_at IS NOT NULL AND completed_at IS NULL
                            AND claimed_at > datetime('now', ?)
                       THEN 1 END) as active,
            COUNT(CASE WHEN (claimed_at IS NULL
                             OR claimed_at <= datetime('now', ?))
                            AND completed_at IS NULL
                       THEN 1 END) as waiting
        FROM donate_work_queue
    """, (f"-{CLAIM_TIMEOUT_MIN} minutes", f"-{CLAIM_TIMEOUT_MIN} minutes")).fetchone()

    print(f"\n[status] Queue: {total:,} total  |  {done:,} done  |  {claimed:,} active  |  {waiting:,} waiting")

    # Band breakdown of waiting
    rows = db.execute("""
        SELECT priority, COUNT(*) as cnt
        FROM donate_work_queue
        WHERE completed_at IS NULL
        GROUP BY priority ORDER BY priority
    """).fetchall()
    band_inv = {v: k for k, v in _BAND_PRIORITY.items()}
    for pri, cnt in rows:
        print(f"  priority {pri} ({band_inv.get(pri,'?'):6}): {cnt:>6,} waiting")

    # Registry results
    conf_counts = db.execute("""
        SELECT
            COUNT(CASE WHEN donate_confidence >= 90 AND donate_url IS NOT NULL THEN 1 END) as ready,
            COUNT(CASE WHEN donate_url_status = 'pending_review' THEN 1 END) as pending,
            COUNT(CASE WHEN donate_url_status = 'human_review' THEN 1 END) as review,
            COUNT(CASE WHEN donate_url_status = 'no_link_found' THEN 1 END) as no_link
        FROM registry_enriched
    """).fetchone()
    print(f"\n[results] ready≥90: {conf_counts[0]:,}  |  pending_review: {conf_counts[1]:,}  |  human_review: {conf_counts[2]:,}  |  no_link: {conf_counts[3]:,}")


# ── Atomic batch claim ────────────────────────────────────────────────────────

def claim_batch(db: sqlite3.Connection, worker_id: str) -> list[str]:
    """Claim up to BATCH_SIZE unclaimed (or stale) EINs. Returns list of EINs."""
    timeout_clause = f"-{CLAIM_TIMEOUT_MIN} minutes"
    # Use IMMEDIATE to get an exclusive write lock for the claim
    db.execute("BEGIN IMMEDIATE")
    try:
        eins = [r[0] for r in db.execute("""
            SELECT ein FROM donate_work_queue
            WHERE completed_at IS NULL
              AND (claimed_at IS NULL OR claimed_at <= datetime('now', ?))
            ORDER BY priority, queued_at
            LIMIT ?
        """, (timeout_clause, BATCH_SIZE)).fetchall()]

        if not eins:
            db.execute("COMMIT")
            return []

        placeholders = ",".join("?" * len(eins))
        db.execute(f"""
            UPDATE donate_work_queue
            SET claimed_at=datetime('now'), claimed_by=?
            WHERE ein IN ({placeholders})
        """, [worker_id] + eins)
        db.execute("COMMIT")
        return eins
    except Exception:
        db.execute("ROLLBACK")
        raise


def mark_complete(db: sqlite3.Connection, eins: list[str]):
    if not eins:
        return
    placeholders = ",".join("?" * len(eins))
    db.execute(
        f"UPDATE donate_work_queue SET completed_at=datetime('now') WHERE ein IN ({placeholders})",
        eins,
    )
    db.commit()


# ── Worker process ────────────────────────────────────────────────────────────

def _worker_process(worker_id: int, n_threads: int, stop_event, progress_queue):
    """Runs in a separate process. Claims batches and processes them until queue empty."""
    db = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    init_schema(db)  # ensure page_cache table exists

    wid = f"worker-{worker_id}-{os.getpid()}"
    blocked_set = {r[0] for r in db.execute("SELECT domain FROM blocked_domains")}

    stats = {"verified": 0, "review": 0, "no_link": 0, "blocked": 0, "batches": 0}

    while not stop_event.is_set():
        try:
            eins = claim_batch(db, wid)
        except Exception as e:
            time.sleep(2)
            continue

        if not eins:
            break  # queue exhausted

        # Load org rows for this batch
        placeholders = ",".join("?" * len(eins))
        rows = db.execute(f"""
            SELECT EIN, organization_name, website, CITY, STATE
            FROM registry_enriched
            WHERE EIN IN ({placeholders})
        """, eins).fetchall()

        completed_eins = []

        with ThreadPoolExecutor(max_workers=n_threads) as pool:
            futs = {pool.submit(_discover_one, r, blocked_set): r for r in rows}
            for fut in as_completed(futs):
                res = fut.result()
                dec = res["decision"] or "unknown"
                now = _now()

                if res["blocked"]:
                    dom = domain_of(res["website"])
                    if dom:
                        block_domain(db, dom, res["blocked_reason"])
                        blocked_set.add(dom)
                    db.execute("""
                        UPDATE registry_enriched
                        SET donate_url_status='blocked_or_restricted', donate_checked_at=?
                        WHERE EIN=?
                    """, (now, res["ein"]))
                    db.commit()
                    stats["blocked"] += 1

                elif dec == "new_candidate_verified":
                    db.execute("""
                        UPDATE registry_enriched
                        SET donate_url=?, donate_platform=?,
                            donate_url_status='pending_review',
                            donate_confidence=?, donate_source_page=?,
                            donate_identity_match=?, donate_checked_at=?
                        WHERE EIN=?
                    """, (res["donate_url"], res["donate_platform"], res["confidence"],
                          res["source_page"], res["match_level"], now, res["ein"]))
                    write_evidence(db, ein=res["ein"], legal_name=res["name"],
                                   official_website=res["website"],
                                   source_page=res["source_page"],
                                   candidate_url=res["donate_url"],
                                   final_url=res["donate_url"],
                                   processor=res["donate_platform"],
                                   match_level=res["match_level"],
                                   confidence=res["confidence"],
                                   risk_level="low", decision="publish_eligible",
                                   public_display_allowed=False,
                                   notes="pending Phase 2 release batch")
                    db.commit()
                    stats["verified"] += 1

                elif dec == "human_review_required":
                    db.execute("""
                        UPDATE registry_enriched
                        SET donate_url=?, donate_platform=?,
                            donate_url_status='human_review',
                            donate_confidence=?, donate_source_page=?,
                            donate_identity_match=?, donate_checked_at=?, donate_human_review=1
                        WHERE EIN=?
                    """, (res["donate_url"], res["donate_platform"], res["confidence"],
                          res["source_page"], res["match_level"], now, res["ein"]))
                    queue_for_review(db, ein=res["ein"], legal_name=res["name"],
                                     reason="confidence_75_89",
                                     candidate_website=res["website"],
                                     candidate_donation_url=res["donate_url"],
                                     confidence=res["confidence"],
                                     risk_flags={"match_level": res["match_level"],
                                                 "notes": res["notes"]},
                                     recommended_action="verify donation link matches org identity")
                    write_evidence(db, ein=res["ein"], legal_name=res["name"],
                                   official_website=res["website"],
                                   source_page=res["source_page"],
                                   candidate_url=res["donate_url"],
                                   final_url=res["donate_url"],
                                   processor=res["donate_platform"],
                                   match_level=res["match_level"],
                                   confidence=res["confidence"],
                                   risk_level="medium", decision="human_review",
                                   public_display_allowed=False,
                                   notes="confidence 75–89 — in human review queue")
                    db.commit()
                    stats["review"] += 1

                else:
                    new_status = "rejected" if res["donate_url"] else "no_link_found"
                    db.execute("""
                        UPDATE registry_enriched
                        SET donate_url_status=?, donate_checked_at=?
                        WHERE EIN=?
                    """, (new_status, now, res["ein"]))
                    if res["donate_url"]:
                        write_evidence(db, ein=res["ein"], legal_name=res["name"],
                                       official_website=res["website"],
                                       source_page=res["source_page"],
                                       candidate_url=res["donate_url"],
                                       final_url=res["donate_url"],
                                       processor=res["donate_platform"],
                                       match_level=res["match_level"],
                                       confidence=res["confidence"],
                                       risk_level="high", decision="rejected",
                                       public_display_allowed=False,
                                       notes=f"confidence {res['confidence']} < 75")
                    db.commit()
                    stats["no_link"] += 1

                # Store fetched page HTML for future pipeline reuse (volunteering etc.)
                for pg_url, pg_body, pg_status in res.get("cached_pages", []):
                    try:
                        cache_page(db, res["ein"], pg_url, pg_body, pg_status)
                    except Exception:
                        pass  # non-critical — never fail a batch over caching
                if res.get("cached_pages"):
                    db.commit()

                completed_eins.append(res["ein"])

        mark_complete(db, completed_eins)
        stats["batches"] += 1
        progress_queue.put((worker_id, stats.copy()))

    db.close()
    progress_queue.put((worker_id, {**stats, "done": True}))


# ── Phase 2: release verified links to public directory ───────────────────────

def phase2_release(db: sqlite3.Connection, max_links: int = 200) -> int:
    """Promote pending_review links (conf>=90) to live. Returns count released."""
    rows = db.execute("""
        SELECT EIN, donate_url, donate_platform, donate_confidence,
               donate_source_page, donate_identity_match
        FROM registry_enriched
        WHERE donate_url_status = 'pending_review'
          AND donate_confidence >= 90
          AND donate_url IS NOT NULL
        ORDER BY donate_confidence DESC
        LIMIT ?
    """, (max_links,)).fetchall()

    if not rows:
        print("[release] nothing pending")
        return 0

    now = _now()
    released = 0
    for ein, url, platform, conf, src, match in rows:
        db.execute("""
            UPDATE registry_enriched
            SET donate_url_status='ok', donate_checked_at=?
            WHERE EIN=?
        """, (now, ein))
        db.execute("""
            UPDATE donation_link_evidence
            SET public_display_allowed=1, decision='published'
            WHERE ein=? AND candidate_url=?
        """, (ein, url))
        released += 1

    db.commit()
    print(f"[release] promoted {released:,} links to live")
    return released


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_workers(n_workers: int, n_threads: int):
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    init_queue_schema(db)

    added = populate_queue(db)
    print_status(db)

    # Count waiting work
    waiting = db.execute("""
        SELECT COUNT(*) FROM donate_work_queue
        WHERE completed_at IS NULL
          AND (claimed_at IS NULL OR claimed_at <= datetime('now', ?))
    """, (f"-{CLAIM_TIMEOUT_MIN} minutes",)).fetchone()[0]
    db.close()

    if waiting == 0:
        print("\n[workers] Queue empty — nothing to do. Run --release to publish pending links.")
        return

    print(f"\n[workers] Starting {n_workers} workers × {n_threads} threads = {n_workers * n_threads} concurrent HTTP connections")
    print(f"[workers] {waiting:,} orgs waiting in queue\n")

    ctx = multiprocessing.get_context("fork")
    stop_event = ctx.Event()
    progress_queue = ctx.Queue()

    workers = []
    for i in range(n_workers):
        p = ctx.Process(
            target=_worker_process,
            args=(i, n_threads, stop_event, progress_queue),
            daemon=True,
        )
        p.start()
        workers.append(p)
        time.sleep(0.3)  # stagger starts slightly

    t0 = time.time()
    totals = {"verified": 0, "review": 0, "no_link": 0, "blocked": 0, "batches": 0}
    active_workers = n_workers
    done_workers = set()

    try:
        while active_workers > 0:
            try:
                wid, stats = progress_queue.get(timeout=5)
            except Exception:
                # Timeout — print heartbeat
                elapsed = time.time() - t0
                rate = (totals["verified"] + totals["review"] + totals["no_link"]) / max(elapsed, 1)
                print(f"  [{elapsed:5.0f}s] verified={totals['verified']:,}  review={totals['review']:,}  no_link={totals['no_link']:,}  blocked={totals['blocked']:,}  {rate:.1f} orgs/s", end="\r")
                continue

            if stats.get("done") and wid not in done_workers:
                done_workers.add(wid)
                active_workers -= 1

            totals["verified"] += stats.get("verified", 0) - (totals.get(f"_prev_verified_{wid}", 0))
            totals["review"]   += stats.get("review", 0)   - (totals.get(f"_prev_review_{wid}", 0))
            totals["no_link"]  += stats.get("no_link", 0)  - (totals.get(f"_prev_no_link_{wid}", 0))
            totals["blocked"]  += stats.get("blocked", 0)  - (totals.get(f"_prev_blocked_{wid}", 0))
            totals[f"_prev_verified_{wid}"] = stats.get("verified", 0)
            totals[f"_prev_review_{wid}"]   = stats.get("review", 0)
            totals[f"_prev_no_link_{wid}"]  = stats.get("no_link", 0)
            totals[f"_prev_blocked_{wid}"]  = stats.get("blocked", 0)

    except KeyboardInterrupt:
        print("\n\n[workers] Stopping workers (Ctrl+C) …")
        stop_event.set()

    for p in workers:
        p.join(timeout=15)

    elapsed = time.time() - t0
    print(f"\n\n[done] {elapsed:.0f}s elapsed")
    print(f"  verified (conf≥90): {totals['verified']:,}")
    print(f"  human review:       {totals['review']:,}")
    print(f"  no link found:      {totals['no_link']:,}")
    print(f"  blocked/captcha:    {totals['blocked']:,}")

    # Auto-release after workers finish
    db2 = sqlite3.connect(DB_PATH, timeout=30)
    db2.execute("PRAGMA journal_mode=WAL")
    released = phase2_release(db2)
    db2.close()
    if released:
        print(f"\n[release] {released:,} new donate links are now live in the directory")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    cpu_count = multiprocessing.cpu_count()
    default_workers = max(2, min(4, cpu_count // 2))

    parser = argparse.ArgumentParser()
    parser.add_argument("--workers",    type=int, default=default_workers,
                        help=f"worker processes (default: {default_workers})")
    parser.add_argument("--threads",    type=int, default=8,
                        help="HTTP threads per worker (default: 8)")
    parser.add_argument("--queue-only", action="store_true",
                        help="populate queue only, don't run workers")
    parser.add_argument("--status",     action="store_true",
                        help="print queue status and exit")
    parser.add_argument("--max-links",  type=int, default=500,
                        help="Max links to release per --release run (default 500, 0=unlimited)")
    parser.add_argument("--release",    action="store_true",
                        help="promote pending_review links (conf>=90) to live")
    args = parser.parse_args()

    db = sqlite3.connect(DB_PATH, timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    init_queue_schema(db)

    if args.status:
        populate_queue(db)
        print_status(db)
        db.close()
        return

    if args.release:
        cap = args.max_links if args.max_links > 0 else 999_999
        phase2_release(db, max_links=cap)
        db.close()
        return

    if args.queue_only:
        populate_queue(db)
        print_status(db)
        db.close()
        return

    db.close()
    run_workers(args.workers, args.threads)


if __name__ == "__main__":
    main()
