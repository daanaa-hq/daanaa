"""
Daily hidden gem Bluesky post for Daanaa — same content strategy as
daily_gem_post.py (LinkedIn), reusing its gem selection and post generation.
Posts more often (hourly, business hours) since Bluesky has no per-post
algorithmic penalty the way LinkedIn company pages do.

Keeps its own featured-log so LinkedIn and Bluesky cadences don't collide
(Bluesky can re-feature a gem LinkedIn already covered, and vice versa).

Usage:
  python3 bluesky_gem_post.py                  # pick, generate, post
  python3 bluesky_gem_post.py --dry-run        # print without posting
  python3 bluesky_gem_post.py --ein 202910382  # force a specific org
"""
import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
FEATURED_LOG = BASE / ".featured_gems_bluesky.json"

sys.path.insert(0, str(BASE))
import daily_gem_post as gem  # reuse pick_gem + generate_post
import bluesky_poster as bsky


def load_featured() -> set:
    if FEATURED_LOG.exists():
        return set(json.loads(FEATURED_LOG.read_text()))
    return set()


def mark_featured(ein: str):
    featured = load_featured()
    featured.add(ein)
    FEATURED_LOG.write_text(json.dumps(sorted(featured), indent=2))


def pick_gem_bluesky(ein: str = None):
    """Same as gem.pick_gem but checks the Bluesky-specific featured log."""
    if ein:
        return gem.pick_gem(ein=ein)

    import sqlite3
    db = sqlite3.connect(gem.DB_PATH)
    db.row_factory = sqlite3.Row
    featured = load_featured()
    featured_list = list(featured) if featured else [""]
    placeholders = ",".join("?" * len(featured_list))
    row = db.execute(f"""
        SELECT EIN, organization_name, CITY, STATE, NTEE1, mission,
               website, merit_score, merit_health_signal_v5,
               merit_band_v5_label, peer_percentile, total_revenue,
               ruling_date, cause_tags
        FROM registry_enriched
        WHERE is_hidden_gem = 1
          AND org_status = 'active'
          AND mission IS NOT NULL
          AND website IS NOT NULL
          AND merit_health_signal_v5 = 'HEALTHY'
          AND EIN NOT IN ({placeholders})
        ORDER BY peer_percentile DESC
        LIMIT 1
    """, featured_list).fetchone()
    db.close()
    return dict(row) if row else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ein", help="feature a specific EIN")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args()

    org = pick_gem_bluesky(args.ein)
    if not org:
        print("No unfeatured hidden gems available for Bluesky. Reset .featured_gems_bluesky.json to restart.")
        return

    name = org["organization_name"].title()
    print(f"\nToday's Bluesky gem: {name} ({org['EIN']}) — {org['CITY'].title()}, {org['STATE']}")

    post_text = gem.generate_post(org, linkedin_page=None, no_llm=args.no_llm)
    print("\n" + "-" * 60)
    print(post_text)
    print("-" * 60)

    if args.dry_run:
        print("\nDry run — not posted.")
        return

    uri = bsky.post_text(post_text)
    mark_featured(org["EIN"])
    print(f"\nPosted: {uri}")


if __name__ == "__main__":
    main()
