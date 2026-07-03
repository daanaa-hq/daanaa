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


def enrich_batch(batch_size: int = 100, sleep_secs: float = 2.0):
    index = load_index()
    already = set(index.keys())
    candidates = fetch_candidates(batch_size, already)

    if not candidates:
        print("All hidden gems already indexed.")
        return

    print(f"Enriching {len(candidates)} gems (sleep={sleep_secs}s between requests)...")
    client = get_client()
    found = 0

    for i, org in enumerate(candidates):
        ein = org["EIN"]
        name = org["organization_name"]
        print(f"  [{i+1}/{len(candidates)}] {name[:50]}...", end=" ", flush=True)

        try:
            results = client.search_companies(keywords=[name], limit=3)
        except Exception as e:
            print(f"ERROR: {e}")
            index[ein] = {"name": name, "found": False, "followers": 0, "url": None}
            time.sleep(sleep_secs)
            continue

        if not results:
            print("not found")
            index[ein] = {"name": name, "found": False, "followers": 0, "url": None}
            time.sleep(sleep_secs)
            continue

        # Confidence check: name must overlap
        top = results[0]
        top_name = (top.get("name") or "").lower()
        query_words = set(w for w in name.lower().split() if len(w) > 3)
        match_words = set(top_name.split())
        overlap = query_words & match_words

        if not overlap and len(query_words) > 1:
            print(f"low confidence ({top_name[:30]})")
            index[ein] = {"name": name, "found": False, "followers": 0, "url": None}
            time.sleep(sleep_secs)
            continue

        urn_id = top.get("urn_id", "")
        followers = parse_followers(top.get("subline") or top.get("headline"))
        url = f"https://www.linkedin.com/company/{urn_id}/" if urn_id else None

        print(f"✓ {top_name[:30]} — {followers:,} followers")
        index[ein] = {
            "name": top.get("name", name),
            "found": True,
            "followers": followers,
            "url": url,
            "urn_id": urn_id,
        }
        found += 1
        time.sleep(sleep_secs)

        # Save every 25 to preserve progress
        if (i + 1) % 25 == 0:
            save_index(index)
            print(f"  (saved checkpoint at {i+1})")

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
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds between API calls")
    parser.add_argument("--stats", action="store_true", help="Show index stats")
    args = parser.parse_args()

    if args.stats:
        show_stats()
    else:
        enrich_batch(args.batch, args.sleep)


if __name__ == "__main__":
    main()
