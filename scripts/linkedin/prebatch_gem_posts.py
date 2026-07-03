"""
Nightly pre-generation of gem posts.

Runs overnight (cron or scheduler) to pre-generate the next N days of gem posts
using the GPU while it's otherwise idle. At post time, daily_gem_post.py just
pops from the queue — no LLM wait at 10:00 / 14:00.

Usage:
  python3 prebatch_gem_posts.py --days 7      # pre-generate 1 week (14 posts)
  python3 prebatch_gem_posts.py --days 1      # just tomorrow (2 posts)
  python3 prebatch_gem_posts.py --status      # show queue size

Queue file: .post_queue.json
  [{"ein": "...", "text": "...", "slot": 0, "generated_at": "..."}, ...]
"""
import json
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

import daily_gem_post as gem
import llm_client as llm

QUEUE_FILE = BASE / ".post_queue.json"


def load_queue() -> list:
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return []


def save_queue(q: list):
    QUEUE_FILE.write_text(json.dumps(q, indent=2))


def queue_eins() -> set:
    return {item["ein"] for item in load_queue()}


def pop_next(slot: int = 0) -> dict | None:
    """Consume the next queued post for the given slot. Called by daily_gem_post.py."""
    q = load_queue()
    for i, item in enumerate(q):
        if item.get("slot") == slot:
            q.pop(i)
            save_queue(q)
            return item
    return None


def _generate_one(args: tuple) -> dict | None:
    org, slot = args
    ein = org["EIN"]
    try:
        li_page = gem.find_linkedin_page(org["organization_name"], ein=ein)
        text = gem.generate_post(org, li_page)
        return {
            "ein": ein,
            "name": org["organization_name"].title(),
            "slot": slot,
            "text": text,
            "li_url": li_page["url"] if li_page else None,
            "followers": li_page["followers"] if li_page else 0,
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        print(f"  ERROR generating {ein}: {e}")
        return None


def prebatch(days: int = 7, workers: int = 4):
    """Pre-generate days × 2 posts (slot 0 + slot 1 per day) in parallel."""
    needed = days * 2
    q = load_queue()
    already_queued = len(q)
    already_eins = queue_eins() | gem.load_featured()

    print(f"Queue: {already_queued} posts already queued. Generating {needed} more ({days} days)...")

    # Collect candidates: alternating slot 0 and slot 1 picks
    candidates = []
    seen_today = set()
    for slot in [0, 1] * days:
        offset = len(seen_today)
        org = None
        # Pick next unfeatured gem not already in this batch
        li_index = gem._load_linkedin_index()
        ranked = sorted(
            [(v["followers"], ein) for ein, v in li_index.items()
             if v.get("found") and ein not in already_eins and ein not in seen_today],
            reverse=True,
        )
        if ranked:
            target_ein = ranked[0][1]
            db = sqlite3.connect(gem.DB_PATH)
            db.row_factory = sqlite3.Row
            row = db.execute("""
                SELECT EIN, organization_name, CITY, STATE, NTEE1, mission,
                       website, merit_score, merit_health_signal_v5,
                       merit_band_v5_label, peer_percentile, total_revenue,
                       ruling_date, cause_tags
                FROM registry_enriched WHERE EIN = ? AND org_status = 'active'
            """, (target_ein,)).fetchone()
            db.close()
            if row:
                org = dict(row)
        if org:
            seen_today.add(org["EIN"])
            candidates.append((org, slot))

    if not candidates:
        print("No candidates available. Run enricher first.")
        return

    print(f"Generating {len(candidates)} posts using GPU (workers={workers})...")
    new_posts = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_generate_one, c): c for c in candidates}
        for i, fut in enumerate(as_completed(futures)):
            result = fut.result()
            if result:
                new_posts.append(result)
                print(f"  [{i+1}/{len(candidates)}] ✓ {result['name'][:45]} (slot {result['slot']}, {result['followers']:,} followers)")

    q.extend(new_posts)
    save_queue(q)
    print(f"\nQueue now has {len(q)} posts ready.")


def show_status():
    q = load_queue()
    if not q:
        print("Queue is empty. Run with --days to pre-generate.")
        return
    slot0 = [x for x in q if x["slot"] == 0]
    slot1 = [x for x in q if x["slot"] == 1]
    print(f"Queue: {len(q)} posts ready ({len(slot0)} morning, {len(slot1)} afternoon)")
    print(f"  Days of runway: {min(len(slot0), len(slot1))}")
    print(f"\nNext up:")
    for item in q[:4]:
        li = f"  {item['followers']:,} followers" if item.get("followers") else ""
        print(f"  Slot {item['slot']}: {item['name']}{li}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel GPU generation workers")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if args.status:
        show_status()
    else:
        prebatch(args.days, args.workers)


if __name__ == "__main__":
    main()
