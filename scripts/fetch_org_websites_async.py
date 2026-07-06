#!/usr/bin/env python3
"""
fetch_org_websites_async.py — Async variant using aiohttp (10-50x faster).

Identical output to fetch_org_websites.py but uses:
- aiohttp for async HTTP (instead of requests)
- asyncio with Semaphore for concurrency (instead of ThreadPool)
- Per-domain throttling via asyncio.sleep

Rate limit: 2-3s per domain (via per-domain queue)
Concurrent connections: 100-500 (configurable)
Throughput: 30-100 requests/sec (vs current ~3)

Usage:
    python3 scripts/fetch_org_websites_async.py --limit 500
    python3 scripts/fetch_org_websites_async.py --workers 100  # Concurrent connections
"""

import asyncio
import aiohttp
import sqlite3
import zlib
import re
import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import logging

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
LOG_FILE = Path.home() / "meritgiving/logs/fetch_org_websites_async.log"
UA = "Mozilla/5.0 (X11; Linux x86_64; compatible; Daanaa/1.0; +https://daanaa.org/about)"
TIMEOUT = 10

# Async-safe logging
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AsyncRateLimiter:
    """Per-domain rate limiter using asyncio."""

    def __init__(self, min_interval_sec: float = 2.5):
        self.min_interval = min_interval_sec
        self.last_request_time = {}  # domain -> timestamp
        self.locks = {}  # domain -> asyncio.Lock

    async def wait(self, domain: str):
        """Wait before fetching from domain."""
        if domain not in self.locks:
            self.locks[domain] = asyncio.Lock()

        async with self.locks[domain]:
            last = self.last_request_time.get(domain, 0)
            wait_time = self.min_interval - (asyncio.get_event_loop().time() - last)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.last_request_time[domain] = asyncio.get_event_loop().time()


rate_limiter = AsyncRateLimiter()
robots_cache = {}
robots_lock = asyncio.Lock()

# Statistics
stats = {"written": 0, "skipped": 0, "errors": 0}
stats_lock = asyncio.Lock()


async def can_fetch(session: aiohttp.ClientSession, url: str) -> bool:
    """Quick robots.txt check. Defaults to allowed on error."""
    parsed = urlparse(url)
    if not parsed.netloc:
        return True

    domain = parsed.netloc.lower()

    async with robots_lock:
        if domain in robots_cache:
            return robots_cache[domain]

    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    allowed = True

    try:
        async with session.get(robots_url, timeout=5) as resp:
            if resp.status == 200:
                text = await resp.text(errors="replace")
                rp = RobotFileParser()
                rp.set_url(robots_url)
                rp.parse(text.splitlines())
                allowed = rp.can_fetch(UA, url)
    except Exception:
        allowed = True  # any error → assume allowed

    async with robots_lock:
        robots_cache[domain] = allowed

    return allowed


def is_cloudflare_block(html: str, status: int) -> bool:
    """Check if response is Cloudflare challenge."""
    if status in (403, 503) and "cloudflare" in html.lower()[:2000]:
        return True
    if "challenge-platform" in html[:3000]:
        return True
    return False


def normalize_url(url: str) -> str:
    """Add https:// if missing."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


async def fetch_url(url: str, session: aiohttp.ClientSession) -> tuple[int, bytes | None]:
    """Fetch URL and return (status_code, html_bytes_or_none)."""
    url = normalize_url(url)

    try:
        async with session.get(
            url,
            headers={"User-Agent": UA},
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
            allow_redirects=True,
            ssl=False  # Ignore SSL errors for compatibility
        ) as resp:
            if is_cloudflare_block(await resp.text(errors="replace"), resp.status):
                return 403, None
            if resp.status in (429,):
                return 429, None

            if resp.status == 200:
                return 200, await resp.read()
            else:
                return resp.status, None

    except asyncio.TimeoutError:
        return 408, None
    except aiohttp.ClientConnectorError:
        return 0, None
    except aiohttp.ClientSSLError:
        return 495, None
    except Exception as e:
        logger.debug(f"Fetch error on {url}: {e}")
        return -1, None


def extract_text_snippet(html_bytes: bytes, max_chars: int = 600) -> str:
    """Extract text snippet from HTML."""
    try:
        html = html_bytes.decode("utf-8", errors="replace")
    except Exception:
        return ""

    # og:description
    m = re.search(
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^\'"]{10,})["\']',
        html,
        re.IGNORECASE
    )
    if m:
        text = re.sub(r'\s+', ' ', m.group(1)).strip()
        if len(text) >= 40:
            return text[:max_chars]

    # Standard description
    m = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^\'"]{10,})["\']',
        html,
        re.IGNORECASE
    )
    if m:
        text = re.sub(r'\s+', ' ', m.group(1)).strip()
        if len(text) >= 40:
            return text[:max_chars]

    # Body text fallback
    body = re.sub(r'<(script|style|nav|footer|header)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<[^>]+>', ' ', body)
    body = re.sub(r'&[a-z#0-9]+;', ' ', body)
    body = re.sub(r'\s+', ' ', body).strip()
    return body[:max_chars]


async def store_page(conn: sqlite3.Connection, ein: str, url: str, status: int, html_bytes: bytes | None):
    """Store page to database."""
    now = datetime.now(timezone.utc).isoformat()
    gz = zlib.compress(html_bytes) if html_bytes else None
    clen = len(html_bytes) if html_bytes else 0

    conn.execute(
        """INSERT OR REPLACE INTO page_cache(url, ein, fetched_at, status_code, html_gz, content_len)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (url, ein, now, status, gz, clen)
    )
    conn.commit()


async def crawl_one(
    ein: str,
    website: str,
    session: aiohttp.ClientSession,
    conn: sqlite3.Connection
) -> bool:
    """Crawl single org's website."""
    global stats

    website = normalize_url(website)
    domain = urlparse(website).netloc.lower()

    if not domain:
        async with stats_lock:
            stats["errors"] += 1
        return False

    # Check robots.txt
    if not await can_fetch(session, website):
        async with stats_lock:
            stats["skipped"] += 1
        return False

    # Rate limit
    await rate_limiter.wait(domain)

    # Fetch homepage
    status, html_bytes = await fetch_url(website, session)
    await asyncio.to_thread(store_page, conn, ein, website, status, html_bytes)

    if status != 200 or not html_bytes:
        async with stats_lock:
            stats["errors"] += 1
        return False

    # If homepage is thin, try /about
    snippet = extract_text_snippet(html_bytes)
    if len(snippet) < 200:
        about_url = urljoin(website, "/about")
        if await can_fetch(session, about_url):
            await rate_limiter.wait(domain)
            about_status, about_bytes = await fetch_url(about_url, session)
            if about_status == 200 and about_bytes:
                await asyncio.to_thread(store_page, conn, ein, about_url, about_status, about_bytes)

    async with stats_lock:
        stats["written"] += 1

    return True


async def run_async(
    orgs: list[tuple[str, str]],
    max_concurrent: int = 100
):
    """Run async crawl with semaphore-based concurrency control."""
    logger.info(f"Starting async crawl: {len(orgs)} orgs, {max_concurrent} concurrent connections")

    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)

    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_crawl(ein: str, website: str, session: aiohttp.ClientSession):
        async with semaphore:
            return await crawl_one(ein, website, session, conn)

    start = asyncio.get_event_loop().time()

    # Create session with connection pool
    connector = aiohttp.TCPConnector(limit=max_concurrent, limit_per_host=5)
    timeout = aiohttp.ClientTimeout(total=60, connect=10, sock_read=10)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [bounded_crawl(ein, website, session) for ein, website in orgs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    duration = asyncio.get_event_loop().time() - start
    conn.close()

    return duration, results


def run(limit: int = 0, workers: int = 100):
    """Main entry point."""
    logger.info(f"fetch_org_websites_async.py starting — workers={workers} limit={limit or 'all'}")

    # Load orgs from DB
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT r.EIN, r.website
        FROM registry_enriched r
        WHERE r.website_status = 'ok'
          AND r.website IS NOT NULL AND r.website != ''
          AND r.EIN NOT IN (
              SELECT ein FROM page_cache WHERE ein IS NOT NULL
          )
        ORDER BY r.merit_score DESC NULLS LAST
    """

    if limit:
        query += f" LIMIT {limit}"

    rows = [(r["EIN"], r["website"]) for r in conn.execute(query)]
    conn.close()

    total = len(rows)
    logger.info(f"  {total:,} orgs to crawl")

    if not total:
        logger.info("Nothing to do.")
        return

    # Run async crawl
    duration, results = asyncio.run(run_async(rows, max_concurrent=workers))

    logger.info(
        f"\nDone in {duration/60:.1f} min — "
        f"{stats['written']:,} written, {stats['skipped']:,} skipped, {stats['errors']:,} errors"
    )
    logger.info(f"Throughput: {stats['written'] / duration:.1f} requests/sec")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Max orgs to crawl (0=all)")
    parser.add_argument("--workers", type=int, default=100, help="Concurrent connections")
    args = parser.parse_args()

    run(limit=args.limit, workers=args.workers)
