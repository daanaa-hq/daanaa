#!/usr/bin/env python3
"""
lucido_scraper.py — Harvest mission statements from lucidodata.com org pages.

Robots.txt at lucidodata.com allows /en/organizations/* pages.
Rate limit: 1 req/sec. Fully resumable via checkpoint file.

Phase 0: Download all org sitemaps → build EIN→URL map (CSV cache).
Phase 1: For each EIN in our registry with no mission, fetch Lucido page,
         extract mission text + og:description, write to DB.

Usage:
    python3 scripts/lucido_scraper.py --phase 0          # build sitemap index only
    python3 scripts/lucido_scraper.py --phase 1          # scrape missions (needs phase 0 done)
    python3 scripts/lucido_scraper.py                    # run both phases
    python3 scripts/lucido_scraper.py --dry-run          # phase 0 only, no DB writes
    python3 scripts/lucido_scraper.py --limit 100        # cap phase 1 at N orgs
    python3 scripts/lucido_scraper.py --rate 0.5         # reqs/sec (default 1.0)
    python3 scripts/lucido_scraper.py --workers 3        # concurrent workers (default 3)
"""

import sqlite3, csv, gzip, re, time, os, json, argparse, sys
import urllib.request, urllib.error
import html as html_mod
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

DB_PATH   = Path.home() / "meritgiving/data/merit_registry.db"
DATA_DIR  = Path.home() / "meritgiving/data"
SITEMAP_CSV = DATA_DIR / "lucido_ein_map.csv"
CHECKPOINT  = DATA_DIR / "lucido_checkpoint.txt"
LOG_FILE    = Path("/tmp/lucido_scraper.log")

SITEMAP_INDEX = "https://lucidodata.com/sitemap.xml"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ── Logging ────────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


# ── HTTP helpers ───────────────────────────────────────────────────────────────

def fetch(url: str, binary=False, retries=3) -> bytes | str | None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 429):
                if e.code == 429:
                    log(f"  429 rate-limited on {url}, sleeping 60s")
                    time.sleep(60)
                return None
            log(f"  HTTP {e.code} on {url} (attempt {attempt+1})")
        except Exception as e:
            log(f"  Error fetching {url}: {e} (attempt {attempt+1})")
        if attempt < retries - 1:
            time.sleep(2 ** attempt)
    return None


# ── Sitemap phase ──────────────────────────────────────────────────────────────

def parse_sitemap_urls(xml_text: str) -> list[str]:
    return re.findall(r'<loc>(https://lucidodata\.com/en/organizations/[^<]+)</loc>', xml_text)


def ein_from_url(url: str) -> str | None:
    """Extract and normalize EIN from slug. Last segment after final hyphen = 9-digit EIN."""
    slug = url.rstrip("/").split("/")[-1]
    parts = slug.rsplit("-", 1)
    if len(parts) == 2 and re.fullmatch(r'\d{9}', parts[1]):
        return parts[1]
    return None


def build_sitemap_index(dry_run=False) -> dict[str, str]:
    """Download all org sitemaps and return {ein: url} map. Caches to CSV."""
    if SITEMAP_CSV.exists() and not dry_run:
        log(f"Loading cached sitemap index from {SITEMAP_CSV}")
        ein_map: dict[str, str] = {}
        with open(SITEMAP_CSV, newline="") as f:
            for row in csv.DictReader(f):
                ein_map[row["ein"]] = row["url"]
        log(f"  Loaded {len(ein_map):,} EINs from cache")
        return ein_map

    log("Fetching sitemap index...")
    index_xml = fetch(SITEMAP_INDEX)
    if not index_xml:
        log("ERROR: could not fetch sitemap index")
        sys.exit(1)

    # Find all org sitemap URLs (gzipped and plain)
    sitemap_urls = re.findall(r'<loc>(https://[^<]+org-\d+\.xml[^<]*)</loc>', index_xml)
    log(f"  Found {len(sitemap_urls)} org sitemaps")

    ein_map: dict[str, str] = {}
    for i, sm_url in enumerate(sitemap_urls, 1):
        log(f"  Sitemap {i}/{len(sitemap_urls)}: {sm_url[:80]}")
        raw = fetch(sm_url, binary=True)
        if not raw:
            log(f"    SKIP — could not fetch")
            continue
        try:
            text = gzip.decompress(raw).decode("utf-8", errors="replace")
        except Exception:
            text = raw.decode("utf-8", errors="replace")

        urls = parse_sitemap_urls(text)
        for url in urls:
            ein = ein_from_url(url)
            if ein:
                ein_map[ein] = url
        log(f"    {len(urls):,} URLs, running total: {len(ein_map):,}")
        time.sleep(0.3)

    # Save to CSV
    with open(SITEMAP_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ein", "url"])
        for ein, url in ein_map.items():
            writer.writerow([ein, url])
    log(f"Saved {len(ein_map):,} EINs to {SITEMAP_CSV}")
    return ein_map


# ── Page extraction ────────────────────────────────────────────────────────────

def extract_org_data(html: str) -> dict:
    """Extract mission, description, and website from a Lucido org page."""
    result: dict = {}

    # ── og:description (short description, always present) ─────────────────
    m = re.search(r'<meta\s+(?:name|property)="(?:og:description|description)"\s+content="([^"]+)"', html)
    if m:
        desc = html_mod.unescape(m.group(1))
        # Filter out the boilerplate Lucido description
        if "IRS Form 990" not in desc and "executive compensation" not in desc.lower():
            result["og_description"] = desc

    # ── JSON-LD NGO schema ─────────────────────────────────────────────────
    ld_matches = re.findall(r'application/ld\+json">\s*(\{[^<]+\})', html)
    for ld_str in ld_matches:
        try:
            ld = json.loads(ld_str)
            if ld.get("@type") == "NGO":
                result["name_lucido"] = ld.get("name")
                if ld.get("url"):
                    result["website"] = ld.get("url")
        except Exception:
            pass

    # ── Clean rendered text ────────────────────────────────────────────────
    clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    clean = html_mod.unescape(clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # ── Mission statement (appears between "Mission" and "Quick facts") ────
    # Lucido renders: "Mission [mission text] Quick facts EIN ..."
    # Or: "Mission Mission statement not available in filing."
    m = re.search(r'\bMission\b\s+(.+?)\s+(?:Quick facts|Quick Facts|EIN\b)', clean)
    if m:
        mission_text = m.group(1).strip()
        # Skip if it's just the "not available" fallback or an i18n key
        if (
            "not available" not in mission_text.lower()
            and "missionNotAvailable" not in mission_text
            and len(mission_text) > 20
        ):
            result["mission"] = mission_text[:2000]

    # ── Website from page text ────────────────────────────────────────────
    if "website" not in result:
        m2 = re.search(r'Website\s+(https?://[^\s<>"]+)', clean)
        if m2:
            result["website"] = m2.group(1).strip()

    return result


# ── Scrape phase ──────────────────────────────────────────────────────────────

def load_checkpoint() -> str | None:
    if CHECKPOINT.exists():
        return CHECKPOINT.read_text().strip() or None
    return None


def save_checkpoint(ein: str):
    CHECKPOINT.write_text(ein)


def run_scrape(ein_map: dict[str, str], rate: float, limit: int, dry_run: bool, workers: int = 3):
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # Find orgs in our registry that are in Lucido's sitemap and have no mission
    log("Querying registry for orgs with no mission...")
    rows = db.execute("""
        SELECT EIN, organization_name, mission
        FROM registry_enriched
        WHERE (mission IS NULL OR mission = '')
        ORDER BY total_revenue DESC NULLS LAST
    """).fetchall()

    # Filter to those in Lucido's sitemap
    candidates = [(r["EIN"], r["organization_name"]) for r in rows if r["EIN"] in ein_map]
    log(f"  {len(candidates):,} orgs in Lucido sitemap with no mission")

    if limit:
        candidates = candidates[:limit]
        log(f"  Capped at {limit} (--limit)")

    # Resume from checkpoint
    checkpoint = load_checkpoint()
    if checkpoint:
        try:
            start_idx = next(i for i, (ein, _) in enumerate(candidates) if ein == checkpoint)
            candidates = candidates[start_idx:]
            log(f"  Resuming from checkpoint EIN {checkpoint} ({len(candidates):,} remaining)")
        except StopIteration:
            log(f"  Checkpoint EIN {checkpoint} not in candidate list — starting fresh")

    interval = 1.0 / rate  # seconds between requests per worker slot
    written = 0
    skipped = 0
    errors = 0
    start_time = time.time()

    # Thread-safety: all counter/DB mutations happen under this lock
    lock = threading.Lock()
    # Global 429 backoff: when any worker hits rate-limit, all workers pause
    backoff_until = [0.0]

    log(f"Starting scrape: {len(candidates):,} orgs at {rate:.1f} req/s with {workers} workers")

    def fetch_one(ein: str):
        url = ein_map[ein]

        # Respect global 429 backoff
        wait = backoff_until[0] - time.time()
        if wait > 0:
            time.sleep(wait)

        t0 = time.time()
        html = fetch(url)

        if html is None:
            with lock:
                backoff_until[0] = max(backoff_until[0], time.time() + 5)
            return ein, False, None, None  # fetch_ok=False

        data = extract_org_data(html)

        # Pace: sleep remainder of interval window before returning
        elapsed = time.time() - t0
        sleep_time = max(0, interval - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)

        return ein, True, data.get("mission"), data.get("website")  # fetch_ok=True

    # Process in batches to avoid creating 600K future objects at once
    BATCH = 500
    done_count = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for batch_start in range(0, len(candidates), BATCH):
            batch = [ein for ein, _ in candidates[batch_start:batch_start + BATCH]]
            futures = {pool.submit(fetch_one, ein): ein for ein in batch}

            for future in as_completed(futures):
                ein, fetch_ok, mission, website = future.result()
                done_count += 1

                with lock:
                    if not fetch_ok:
                        errors += 1
                    else:
                        if mission and not dry_run:
                            db.execute(
                                "UPDATE registry_enriched SET mission = ?, mission_source = 'lucido' WHERE EIN = ? AND (mission IS NULL OR mission = '')",
                                (mission, ein)
                            )
                            db.commit()
                            written += 1
                        elif not mission:
                            skipped += 1

                        if website and not dry_run:
                            db.execute(
                                "UPDATE registry_enriched SET website = ? WHERE EIN = ? AND (website IS NULL OR website = '')",
                                (website, ein)
                            )
                            db.commit()

                    if done_count % 100 == 0:
                        elapsed = time.time() - start_time
                        rate_actual = done_count / elapsed if elapsed > 0 else 0
                        log(f"  [{done_count}/{len(candidates)}] written={written} skipped={skipped} errors={errors} {rate_actual:.1f} req/s")
                        save_checkpoint(ein)

    # Final stats
    db.close()
    total_time = time.time() - start_time
    log(f"\nDone in {total_time:.0f}s")
    log(f"  Written:  {written:,}")
    log(f"  Skipped:  {skipped:,}  (no mission on Lucido page)")
    log(f"  Errors:   {errors:,}")
    if CHECKPOINT.exists():
        CHECKPOINT.unlink()
    log("Checkpoint cleared.")


# ── Coverage report ────────────────────────────────────────────────────────────

def coverage_report(ein_map: dict[str, str]):
    db = sqlite3.connect(DB_PATH)
    total_ours = db.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    # Count overlap via temp table to avoid SQL variable limit
    db.execute("CREATE TEMP TABLE _lucido_eins (ein TEXT PRIMARY KEY)")
    db.executemany("INSERT OR IGNORE INTO _lucido_eins VALUES (?)", [(e,) for e in ein_map])
    overlap = db.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE EIN IN (SELECT ein FROM _lucido_eins)"
    ).fetchone()[0]
    no_mission = db.execute("SELECT COUNT(*) FROM registry_enriched WHERE mission IS NULL OR mission = ''").fetchone()[0]
    db.close()

    log(f"\n── Coverage Report ──────────────────────────────")
    log(f"  Lucido orgs (sitemap):      {len(ein_map):>10,}")
    log(f"  Our registry:               {total_ours:>10,}")
    log(f"  Overlap (matchable):        {overlap:>10,}  ({overlap/total_ours*100:.1f}% of ours)")
    log(f"  Our orgs with no mission:   {no_mission:>10,}")
    log(f"  Scrapeable mission targets: {min(overlap, no_mission):>10,}")
    log(f"────────────────────────────────────────────────\n")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, choices=[0, 1], help="0=sitemaps only, 1=scrape only, omit=both")
    parser.add_argument("--dry-run", action="store_true", help="No DB writes")
    parser.add_argument("--limit", type=int, default=0, help="Max orgs to scrape in phase 1")
    parser.add_argument("--rate", type=float, default=1.0, help="Requests per second per worker (default 1.0)")
    parser.add_argument("--workers", type=int, default=3, help="Concurrent fetch workers (default 3)")
    args = parser.parse_args()

    run_phase0 = args.phase in (0, None) or args.phase is None
    run_phase1 = args.phase in (1, None) or args.phase is None
    if args.phase is None:
        run_phase0 = run_phase1 = True

    log(f"lucido_scraper.py starting — phase={'both' if run_phase0 and run_phase1 else args.phase} rate={args.rate} workers={args.workers} limit={args.limit or 'all'} dry_run={args.dry_run}")

    ein_map: dict[str, str] = {}

    if run_phase0:
        ein_map = build_sitemap_index(dry_run=args.dry_run)
        coverage_report(ein_map)

    if run_phase1:
        if not ein_map:
            if SITEMAP_CSV.exists():
                ein_map = {}
                with open(SITEMAP_CSV, newline="") as f:
                    for row in csv.DictReader(f):
                        ein_map[row["ein"]] = row["url"]
                log(f"Loaded {len(ein_map):,} EINs from {SITEMAP_CSV}")
            else:
                log("ERROR: sitemap CSV not found. Run phase 0 first.")
                sys.exit(1)
        run_scrape(ein_map, args.rate, args.limit, args.dry_run, args.workers)


if __name__ == "__main__":
    main()
