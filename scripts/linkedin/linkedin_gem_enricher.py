"""
LinkedIn enrichment for hidden gems.

Scans hidden gems, finds their LinkedIn company page, extracts follower count.
Stores results in .gem_linkedin_index.json for pick_gem() to sort by.

Run once to seed the index, then periodically to fill gaps:
  python3 linkedin_gem_enricher.py --batch 200
  python3 linkedin_gem_enricher.py --batch 200 --sleep 2.5   # slower, safer
  python3 linkedin_gem_enricher.py --stats                    # show index coverage

The pick_gem() function in daily_gem_post.py reads this index to rank by followers.
"""
import argparse
import json
import re
import sqlite3
import time
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = BASE.parent.parent / "data" / "merit_registry.db"
INDEX_FILE = BASE / ".gem_linkedin_index.json"
CREDS_FILE = BASE / ".session" / "linkedin_creds.json"


def load_index() -> dict:
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text())
    return {}


def save_index(index: dict):
    INDEX_FILE.write_text(json.dumps(index, indent=2))


def parse_followers(subline: str | None) -> int:
    """Extract follower count from LinkedIn subline e.g. '1,234 followers · 5 employees'."""
    if not subline:
        return 0
    m = re.search(r'([\d,]+)\s+follower', subline, re.IGNORECASE)
    if m:
        return int(m.group(1).replace(",", ""))
    return 0


def get_client():
    from linkedin_api import Linkedin
    if not CREDS_FILE.exists():
        raise FileNotFoundError(f"Credentials not found: {CREDS_FILE}")
    creds = json.loads(CREDS_FILE.read_text())
    return Linkedin(creds["username"], creds["pass"])


def fetch_candidates(limit: int, already_indexed: set) -> list[dict]:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    rows = db.execute("""
        SELECT EIN, organization_name, CITY, STATE
        FROM registry_enriched
        WHERE is_hidden_gem = 1
          AND org_status = 'active'
          AND mission IS NOT NULL
          AND website IS NOT NULL
        ORDER BY peer_percentile DESC
        LIMIT ?
    """, (limit * 5,)).fetchall()   # fetch extra, filter in Python
    db.close()

    candidates = []
    for r in rows:
        if r["EIN"] not in already_indexed:
            candidates.append(dict(r))
        if len(candidates) >= limit:
            break
    return candidates


def _search_one(args: tuple) -> tuple[str, dict]:
    """Worker: search LinkedIn for one org. Returns (ein, result_dict)."""
    ein, name, client, sleep_secs = args
    time.sleep(sleep_secs)  # rate-limit per worker
    try:
        results = client.search_companies(keywords=[name], limit=3)
    except Exception as e:
        return ein, {"name": name, "found": False, "followers": 0, "url": None, "error": str(e)}

    if not results:
        return ein, {"name": name, "found": False, "followers": 0, "url": None}

    top = results[0]
    top_name = (top.get("name") or "").lower()
    query_words = set(w for w in name.lower().split() if len(w) > 3)
    overlap = query_words & set(top_name.split())
    if not overlap and len(query_words) > 1:
        return ein, {"name": name, "found": False, "followers": 0, "url": None}

    urn_id = top.get("urn_id", "")
    followers = parse_followers(top.get("subline") or top.get("headline"))
    url = f"https://www.linkedin.com/company/{urn_id}/" if urn_id else None
    return ein, {
        "name": top.get("name", name),
        "found": True,
        "followers": followers,
        "url": url,
        "urn_id": urn_id,
    }


def enrich_batch(batch_size: int = 100, sleep_secs: float = 2.0, workers: int = 4):
    """
    Parallel enrichment using CPU thread pool.
    workers=4 → 4x throughput vs serial; each worker sleeps sleep_secs between its own calls.
    LinkedIn's rate limit is per-session, not per-IP, so multiple workers share the same
    session — keep workers ≤ 4 to stay safe.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    index = load_index()
    already = set(index.keys())
    candidates = fetch_candidates(batch_size, already)

    if not candidates:
        print("All hidden gems already indexed.")
        return

    print(f"Enriching {len(candidates)} gems | {workers} workers | {sleep_secs}s sleep each")
    client = get_client()
    found = 0
    lock_data: dict = {}

    args_list = [(org["EIN"], org["organization_name"], client, sleep_secs)
                 for org in candidates]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_search_one, a): a[0] for a in args_list}
        completed = 0
        for fut in as_completed(futures):
            ein, result = fut.result()
            index[ein] = result
            completed += 1
            if result.get("found"):
                found += 1
                print(f"  ✓ [{completed}/{len(candidates)}] {result['name'][:40]} — {result['followers']:,} followers")
            else:
                print(f"  · [{completed}/{len(candidates)}] {result['name'][:40]} — not found")

            if completed % 25 == 0:
                save_index(index)
                print(f"  (checkpoint saved at {completed})")

    save_index(index)
    with_page = sum(1 for v in index.values() if v.get("found"))
    print(f"\nDone. {found} new. Index total: {len(index)} gems, {with_page} with LinkedIn pages.")


def show_stats():
    index = load_index()
    if not index:
        print("Index is empty. Run with --batch to populate.")
        return
    total = len(index)
    found = [v for v in index.values() if v.get("found")]
    with_followers = [v for v in found if v.get("followers", 0) > 0]
    top10 = sorted(found, key=lambda x: x["followers"], reverse=True)[:10]

    print(f"Index: {total} gems scanned")
    print(f"  LinkedIn page found: {len(found)} ({len(found)/total*100:.0f}%)")
    print(f"  With follower data:  {len(with_followers)}")
    print(f"\nTop 10 by followers:")
    for v in top10:
        print(f"  {v['followers']:>6,}  {v['name']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=100, help="Gems to process this run")
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds between API calls per worker")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers (≤4 recommended)")
    parser.add_argument("--stats", action="store_true", help="Show index stats")
    args = parser.parse_args()

    if args.stats:
        show_stats()
    else:
        enrich_batch(args.batch, args.sleep, args.workers)


if __name__ == "__main__":
    main()
