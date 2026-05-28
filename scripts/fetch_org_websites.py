#!/usr/bin/env python3
"""
fetch_org_websites.py — Background crawler that stores org homepage HTML to page_cache.

Priority: orgs with website_status='ok', ordered by merit_score DESC (highest value first).
Stores compressed HTML to page_cache(url, ein, fetched_at, status_code, html_gz, content_len).
If homepage yields <200 chars of useful text, also tries /about page.

Rate limit: 2-3s per domain (via per-domain lock + timestamp tracking).
Workers: 8 threads (network-bound, no GPU contention).
Resumable: skips EINs already in page_cache.

Usage:
    python3 scripts/fetch_org_websites.py
    python3 scripts/fetch_org_websites.py --limit 500     # test run
    python3 scripts/fetch_org_websites.py --workers 4
    python3 scripts/fetch_org_websites.py --no-mission-only  # only orgs missing missions
"""

import sqlite3, zlib, re, time, argparse, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests

DB_PATH  = Path.home() / "meritgiving/data/merit_registry.db"
LOG_FILE = Path.home() / "meritgiving/logs/fetch_org_websites.log"
UA       = "Mozilla/5.0 (X11; Linux x86_64; compatible; Daanaa/1.0; +https://daanaa.org/about)"
TIMEOUT  = 10
MIN_DOMAIN_INTERVAL = 2.5   # seconds between requests to the same domain

_log_lock = threading.Lock()
_domain_locks: dict[str, threading.Lock] = {}
_domain_last: dict[str, float] = {}
_domain_meta_lock = threading.Lock()

_written = 0
_skipped = 0
_errors  = 0
_counter_lock = threading.Lock()


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    with _log_lock:
        print(line, flush=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")


def _domain_of(url: str) -> str:
    return urlparse(url).netloc.lower()


def _get_domain_lock(domain: str) -> threading.Lock:
    with _domain_meta_lock:
        if domain not in _domain_locks:
            _domain_locks[domain] = threading.Lock()
        return _domain_locks[domain]


def _rate_wait(domain: str):
    lock = _get_domain_lock(domain)
    with lock:
        last = _domain_last.get(domain, 0)
        wait = MIN_DOMAIN_INTERVAL - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        _domain_last[domain] = time.time()


_robots_cache: dict[str, bool] = {}
_robots_lock = threading.Lock()


def _can_fetch(url: str) -> bool:
    """Quick robots.txt check with timeout. Defaults to allowed on any error."""
    parsed = urlparse(url)
    if not parsed.netloc:
        return True
    domain = parsed.netloc.lower()
    with _robots_lock:
        if domain in _robots_cache:
            return _robots_cache[domain]
    # Fetch outside lock so one slow host doesn't block all workers
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    allowed = True
    try:
        import urllib.request as _ureq
        req = _ureq.Request(robots_url, headers={"User-Agent": UA})
        with _ureq.urlopen(req, timeout=5) as resp:
            text = resp.read(32768).decode("utf-8", errors="replace")
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.parse(text.splitlines())
        allowed = rp.can_fetch(UA, url)
    except Exception:
        allowed = True  # any error → assume allowed
    with _robots_lock:
        _robots_cache[domain] = allowed
    return allowed


def _is_cloudflare_block(html: str, status: int) -> bool:
    if status in (403, 503) and "cloudflare" in html.lower()[:2000]:
        return True
    if "challenge-platform" in html[:3000]:
        return True
    return False


def _normalize_url(url: str) -> str:
    """Add https:// scheme and lowercase if missing."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def fetch_url(url: str) -> tuple[int, bytes | None]:
    """Fetch a URL. Returns (status_code, raw_bytes_or_None)."""
    url = _normalize_url(url)
    try:
        r = requests.get(
            url,
            headers={"User-Agent": UA},
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        if _is_cloudflare_block(r.text, r.status_code):
            return 403, None
        if r.status_code in (429,):
            return 429, None
        return r.status_code, r.content if r.status_code == 200 else None
    except requests.exceptions.SSLError:
        return 495, None
    except requests.exceptions.ConnectionError:
        return 0, None
    except requests.exceptions.Timeout:
        return 408, None
    except Exception:
        return -1, None


def extract_text_snippet(html_bytes: bytes, max_chars: int = 600) -> str:
    """Extract the most useful plain-text snippet from HTML for LLM context."""
    try:
        html = html_bytes.decode("utf-8", errors="replace")
    except Exception:
        return ""

    # 1. og:description (social preview = best org summary)
    m = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']{10,})["\']', html, re.IGNORECASE)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']{10,})["\'][^>]+property=["\']og:description["\']', html, re.IGNORECASE)
    if m:
        text = re.sub(r'\s+', ' ', m.group(1)).strip()
        if len(text) >= 40:
            return text[:max_chars]

    # 2. twitter:description
    m = re.search(r'<meta[^>]+name=["\']twitter:description["\'][^>]+content=["\']([^"\']{10,})["\']', html, re.IGNORECASE)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']{10,})["\'][^>]+name=["\']twitter:description["\']', html, re.IGNORECASE)
    if m:
        text = re.sub(r'\s+', ' ', m.group(1)).strip()
        if len(text) >= 40:
            return text[:max_chars]

    # 3. Standard <meta name="description">
    m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{10,})["\']', html, re.IGNORECASE)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']{10,})["\'][^>]+name=["\']description["\']', html, re.IGNORECASE)
    if m:
        text = re.sub(r'\s+', ' ', m.group(1)).strip()
        if len(text) >= 40:
            return text[:max_chars]

    # 4. Body text fallback — strip scripts, styles, nav, footer
    body = re.sub(r'<(script|style|nav|footer|header)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<[^>]+>', ' ', body)
    body = re.sub(r'&[a-z#0-9]+;', ' ', body)
    body = re.sub(r'\s+', ' ', body).strip()
    return body[:max_chars]


def _store_page(conn: sqlite3.Connection, lock: threading.Lock, ein: str, url: str, status: int, html_bytes: bytes | None):
    now = datetime.now(timezone.utc).isoformat()
    gz = zlib.compress(html_bytes) if html_bytes else None
    clen = len(html_bytes) if html_bytes else 0
    with lock:
        conn.execute(
            """INSERT OR REPLACE INTO page_cache(url, ein, fetched_at, status_code, html_gz, content_len)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (url, ein, now, status, gz, clen)
        )
        conn.commit()


def crawl_one(ein: str, website: str, conn: sqlite3.Connection, db_lock: threading.Lock) -> bool:
    """Crawl an org's homepage (and /about if homepage is thin). Returns True on success."""
    global _written, _skipped, _errors

    website = _normalize_url(website)
    domain = _domain_of(website)
    if not domain:
        with _counter_lock:
            _errors += 1
        return False

    # Check robots.txt
    if not _can_fetch(website):
        with _counter_lock:
            _skipped += 1
        return False

    _rate_wait(domain)
    status, html_bytes = fetch_url(website)
    _store_page(conn, db_lock, ein, website, status, html_bytes)

    if status != 200 or not html_bytes:
        with _counter_lock:
            _errors += 1
        return False

    # If homepage text is thin, also try /about
    snippet = extract_text_snippet(html_bytes)
    if len(snippet) < 200:
        about_url = urljoin(website, "/about")
        if _can_fetch(about_url):
            _rate_wait(domain)
            about_status, about_bytes = fetch_url(about_url)
            if about_status == 200 and about_bytes:
                _store_page(conn, db_lock, ein, about_url, about_status, about_bytes)

    with _counter_lock:
        _written += 1
    return True


def run(limit: int = 0, workers: int = 8, no_mission_only: bool = False):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log(f"fetch_org_websites.py starting — workers={workers} limit={limit or 'all'} no_mission_only={no_mission_only}")

    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    db_lock = threading.Lock()

    mission_filter = "AND (r.mission IS NULL OR r.mission = '')" if no_mission_only else ""
    query = f"""
        SELECT r.EIN, r.website
        FROM registry_enriched r
        WHERE r.website_status = 'ok'
          AND r.website IS NOT NULL AND r.website != ''
          {mission_filter}
          AND r.EIN NOT IN (
              SELECT ein FROM page_cache WHERE ein IS NOT NULL
          )
        ORDER BY r.merit_score DESC NULLS LAST
    """
    if limit:
        query += f" LIMIT {limit}"

    rows = [(r["EIN"], r["website"]) for r in conn.execute(query)]
    total = len(rows)
    log(f"  {total:,} orgs to crawl")
    if not total:
        log("Nothing to do.")
        conn.close()
        return

    start = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(crawl_one, ein, url, conn, db_lock): (ein, url) for ein, url in rows}
        done = 0
        for fut in as_completed(futs):
            done += 1
            if done % 100 == 0:
                elapsed = time.time() - start
                rate = done / elapsed if elapsed else 0
                eta = (total - done) / rate / 60 if rate else 0
                log(f"  [{done}/{total}] ok={_written} skip={_skipped} err={_errors} {rate:.1f}/s ETA {eta:.0f}m")

    elapsed = time.time() - start
    log(f"\nDone in {elapsed/60:.1f} min — {_written:,} pages fetched, {_skipped:,} skipped, {_errors:,} errors")
    conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit",   type=int, default=0, help="Max orgs to crawl (0=all)")
    ap.add_argument("--workers", type=int, default=8, help="Concurrent fetch threads")
    ap.add_argument("--no-mission-only", action="store_true", help="Only crawl orgs that have no mission yet")
    args = ap.parse_args()
    run(limit=args.limit, workers=args.workers, no_mission_only=args.no_mission_only)
