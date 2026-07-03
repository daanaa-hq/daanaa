"""
Scheduled LinkedIn posting for Daanaa.
Uses the `schedule` library (github.com/dbader/schedule) to run weekly posts.

Run as a long-lived process (or via systemd/cron) to post carousels automatically.

Usage:
  python3 schedule_posts.py                  # start the scheduler (blocks)
  python3 schedule_posts.py --next           # show next scheduled run times
  python3 schedule_posts.py --run-now        # trigger Monday carousel immediately

Cadence (configurable below):
  Monday 09:00  → hidden_gems carousel (rotates type weekly)
  Thursday 09:00 → text post stat from DB (printed to stdout for manual copy-paste)
"""
import datetime
import logging
import schedule
import sqlite3
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

import post_carousel as pc
import daily_gem_post as gem
import prebatch_gem_posts as prebatch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "output" / "schedule.log"),
    ]
)
log = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "data" / "merit_registry.db"

# Weekly carousel rotation (cycles week-of-year % len)
CAROUSEL_ROTATION = [
    "hidden_gems",
    "sector_insight",
    "hidden_gems",
    "myth_bust",
]


def _carousel_type_this_week() -> str:
    week = datetime.date.today().isocalendar()[1]
    return CAROUSEL_ROTATION[week % len(CAROUSEL_ROTATION)]


def monday_carousel():
    carousel_type = _carousel_type_this_week()
    log.info(f"Monday carousel: {carousel_type}")
    try:
        pdf_path, caption = pc.run(carousel_type=carousel_type)
        log.info(f"Posted: {pdf_path}")
    except Exception as e:
        log.error(f"Carousel failed: {e}")
        log.info("Manual fallback: run post_carousel.py --type hidden_gems")


def _post_gem(slot: int):
    """Post one hidden gem. slot 0 = top follower count, slot 1 = second."""
    if datetime.today().weekday() >= 5:
        return
    label = "morning" if slot == 0 else "afternoon"
    log.info(f"Gem post ({label}, slot={slot}): picking org...")
    try:
        org = gem.pick_gem(slot=slot)
        if not org:
            log.warning("No unfeatured gems left — reset .featured_gems.json")
            return
        name = org["organization_name"].title()
        log.info(f"  Gem: {name} ({org['EIN']})")
        li_page = gem.find_linkedin_page(org["organization_name"], ein=org["EIN"])
        if li_page:
            log.info(f"  LinkedIn: {li_page['name']} ({li_page['followers']:,} followers)")
        post_text = gem.generate_post(org, li_page)
        log.info(f"  Post generated ({len(post_text)} chars)")
        import linkedin_poster as poster
        poster.post_text(post_text, "133385169")
        gem.mark_featured(org["EIN"])
        log.info(f"  Done. {name} featured and marked.")
    except Exception as e:
        log.error(f"Gem post (slot {slot}) failed: {e}")


def daily_gem_morning():
    _post_gem(slot=0)


def daily_gem_afternoon():
    _post_gem(slot=1)


def nightly_prebatch():
    """02:00 — GPU generates next week's gem posts while machine is otherwise idle."""
    remaining = len(prebatch.load_queue())
    if remaining >= 14:   # 7 days × 2 posts — already stocked
        log.info(f"Prebatch: queue has {remaining} posts, skipping.")
        return
    log.info(f"Prebatch: queue has {remaining} posts, generating 7 more days...")
    try:
        prebatch.prebatch(days=7, workers=4)
        log.info(f"Prebatch: done. Queue: {len(prebatch.load_queue())} posts ready.")
    except Exception as e:
        log.error(f"Prebatch failed: {e}")


def thursday_text():
    """Generate a data-backed text post and print it for manual review/copy."""
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        rows = db.execute("""
            SELECT ntee1_label,
                   COUNT(*) as total,
                   SUM(CASE WHEN merit_health_signal_v5 = 'CAUTION' THEN 1 ELSE 0 END) as caution
            FROM registry_enriched
            WHERE org_status='active'
              AND ntee1_label IS NOT NULL
              AND merit_health_signal_v5 IS NOT NULL
            GROUP BY ntee1_label HAVING total > 500
            ORDER BY CAST(caution AS FLOAT)/total DESC LIMIT 1
        """).fetchall()
        db.close()

        if rows:
            r = rows[0]
            pct = round(r["caution"] / r["total"] * 100)
            sector = r["ntee1_label"]
            post = (
                f"{pct}% of {sector} organizations in the U.S. are showing limited financial reserves.\n\n"
                f"That doesn't mean they're doing something wrong. "
                f"Many are spending almost everything they raise on programs — by choice.\n\n"
                f"Daanaa shows you the full picture, not just the bottom line.\n\n"
                f"daanaa.org\n#nonprofits #philanthropy #{sector.replace(' ', '').replace('&', 'and')[:20]}"
            )
            log.info("Thursday text post ready (copy below):\n" + "─" * 40)
            print("\n" + post + "\n" + "─" * 40)
        else:
            log.warning("No data for Thursday text post — DB query returned empty")
    except Exception as e:
        log.error(f"Thursday text post failed: {e}")


def show_next_runs():
    jobs = schedule.get_jobs()
    if not jobs:
        print("No jobs scheduled.")
        return
    for j in jobs:
        print(f"  {j.next_run}  →  {j.job_func.__name__}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--next", action="store_true", help="Show next scheduled runs")
    parser.add_argument("--run-now", action="store_true", help="Trigger Monday carousel now")
    args = parser.parse_args()

    Path(Path(__file__).parent / "output").mkdir(exist_ok=True)

    schedule.every().monday.at("09:00").do(monday_carousel)
    schedule.every().thursday.at("09:00").do(thursday_text)
    schedule.every().day.at("10:00").do(daily_gem_morning)    # top gem by LinkedIn followers
    schedule.every().day.at("14:00").do(daily_gem_afternoon)  # second gem by LinkedIn followers
    schedule.every().day.at("02:00").do(nightly_prebatch)     # GPU generates next week's queue while idle

    if args.next:
        show_next_runs()
        return

    if args.run_now:
        monday_carousel()
        return

    log.info("Daanaa LinkedIn scheduler started")
    log.info(f"  Monday 09:00   → carousel ({_carousel_type_this_week()} this week)")
    log.info("  Thursday 09:00 → sector stat text post")
    log.info("  Daily 10:00    → gem #1 (highest LinkedIn followers, Mon–Fri)")
    log.info("  Daily 14:00    → gem #2 (second highest, Mon–Fri)")
    log.info("  Daily 02:00    → GPU pre-generates next week's posts (if queue < 14)")
    log.info("Ctrl-C to stop")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
