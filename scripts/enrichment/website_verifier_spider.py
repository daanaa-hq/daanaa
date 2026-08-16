#!/usr/bin/env python3
"""
Scrapy spider: website verification for Daanaa org registry.

Applies lessons from retired discovery_daemon.py (see
docs/NIGHTLY_ORCHESTRATOR_DESIGN_LEARNINGS.md):
- Explicit error logging (never silent except: pass)
- Checkpoint/resume support
- Rate-limited, respects robots.txt
- Structured output for downstream conflict resolution

Usage (spike / dry-run):
    python3 scripts/enrichment/website_verifier_spider.py --limit 1000 --dry-run

Usage (production, nightly):
    python3 scripts/enrichment/website_verifier_spider.py --resume
"""

import argparse
import json
import logging
import re
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
LOG_DIR = Path.home() / 'meritgiving' / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'website_verifier.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def get_orgs_to_verify(limit=None, resume=False):
    """Fetch orgs needing website verification.

    Lesson applied (#6, checkpoint/resume): query past the last-verified
    EIN from enrichment_checkpoints rather than restarting from scratch.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrichment_checkpoints (
        phase TEXT,
        run_date DATE,
        last_ein TEXT,
        record_count INTEGER,
        checkpoint_time TIMESTAMP,
        PRIMARY KEY (phase, run_date)
    )
    """)
    conn.commit()

    last_ein = None
    if resume:
        cursor.execute("""
        SELECT last_ein FROM enrichment_checkpoints
        WHERE phase = 'website_verify' AND run_date = date('now')
        """)
        row = cursor.fetchone()
        if row:
            last_ein = row['last_ein']
            logger.info(f"Resuming from checkpoint EIN: {last_ein}")

    query = """
    SELECT EIN, organization_name, website, CITY, STATE
    FROM registry_enriched
    WHERE website IS NOT NULL AND website != ''
    """
    params = []
    if last_ein:
        query += " AND EIN > ?"
        params.append(last_ein)
    query += " ORDER BY EIN"
    if limit:
        query += f" LIMIT {int(limit)}"

    cursor.execute(query, params)
    orgs = cursor.fetchall()
    conn.close()
    return orgs


def save_checkpoint(last_ein, record_count):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    INSERT OR REPLACE INTO enrichment_checkpoints
    VALUES ('website_verify', date('now'), ?, ?, datetime('now'))
    """, (last_ein, record_count))
    conn.commit()
    conn.close()


def ensure_output_table():
    """Structured results table — separate from registry_enriched to avoid
    write contention with the API's live reads (lesson #4)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS website_verification_results (
        EIN TEXT,
        original_url TEXT,
        final_url TEXT,
        final_domain TEXT,
        http_status INTEGER,
        verification_status TEXT,  -- 'verified', 'redirect', 'dead_link', 'timeout', 'dns_fail', 'error'
        error_detail TEXT,
        content_confidence TEXT,   -- 'HIGH', 'MEDIUM', 'LOW', or NULL (not content-checked)
        matched_fields TEXT,       -- JSON array, e.g. '["name", "ein"]' — reviewable evidence (Stewardship P3)
        page_title TEXT,
        verified_at TIMESTAMP,
        PRIMARY KEY (EIN, verified_at)
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_wvr_ein ON website_verification_results(EIN)")
    # ALTER-based migration for tables created before this column set existed —
    # CREATE TABLE IF NOT EXISTS above is a no-op on an existing table.
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(website_verification_results)")}
    for col, coltype in [('content_confidence', 'TEXT'), ('matched_fields', 'TEXT'), ('page_title', 'TEXT')]:
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE website_verification_results ADD COLUMN {col} {coltype}")
    conn.commit()
    conn.close()


def _normalize_for_match(text: str) -> str:
    """Lowercase + collapse whitespace for substring comparison."""
    return ' '.join(text.lower().split())


_ORG_SUFFIXES = re.compile(
    r'\b(inc|incorporated|corp|corporation|foundation|fund|association|assoc|'
    r'organization|org|ltd|llc|co)\b\.?',
    re.IGNORECASE,
)


def _loose_name(name: str) -> str:
    """Strip common legal suffixes for a looser name match — 'PTA California
    Congress of Parents Teachers & Students Inc' vs the same text without
    'Inc' should still count as a name match."""
    return ' '.join(_ORG_SUFFIXES.sub('', name).split())


def match_content(page_text: str, org_name: str, city: str | None, state: str | None, ein: str) -> tuple[str, list[str]]:
    """Check fetched page text against org identity. Returns
    (confidence, matched_fields) — matched_fields is logged so the basis for
    the confidence label is always reviewable (Stewardship P3), not a black box.

    Confidence:
      HIGH   — name (exact or loose) AND (city OR EIN) both match
      MEDIUM — name matches alone, OR city+EIN match without a name match
      LOW    — no name match and no city+EIN pair; weak or no signal
    """
    text = _normalize_for_match(page_text)
    matched = []

    name_exact = _normalize_for_match(org_name) in text
    name_loose = (not name_exact) and _normalize_for_match(_loose_name(org_name)) in text
    if name_exact:
        matched.append('name_exact')
    elif name_loose:
        matched.append('name_loose')

    city_match = bool(city) and _normalize_for_match(city) in text
    if city_match:
        matched.append('city')

    # EIN may appear as raw 9 digits or IRS-formatted XX-XXXXXXX
    ein_digits = re.sub(r'\D', '', ein)
    ein_formatted = f"{ein_digits[:2]}-{ein_digits[2:]}" if len(ein_digits) == 9 else None
    ein_match = bool(ein_digits) and (ein_digits in re.sub(r'\D', '', text) or (ein_formatted and ein_formatted in page_text))
    if ein_match:
        matched.append('ein')

    has_name = name_exact or name_loose
    has_secondary = city_match or ein_match

    if has_name and has_secondary:
        confidence = 'HIGH'
    elif has_name or (city_match and ein_match):
        confidence = 'MEDIUM'
    else:
        confidence = 'LOW'

    return confidence, matched


class WebsiteVerifierSpider(scrapy.Spider):
    """Verifies org website URLs: follows redirects, checks status, extracts
    the final canonical domain.

    Lesson #3 applied: every error path logs explicitly, tagged by type.
    Lesson #1 applied: exposes throughput via self.stats for the
    orchestrator's ProductivityWatchdog to read.
    """
    name = 'website_verifier'

    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 0.5,          # ~2 req/sec per domain
        'CONCURRENT_REQUESTS': 16,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_TIMEOUT': 10,
        'RETRY_TIMES': 1,
        'USER_AGENT': 'Mozilla/5.0 (compatible; daanaa-crawler/1.0; +https://daanaa.org/about)',
        'LOG_LEVEL': 'WARNING',  # We do our own structured logging above
    }

    def __init__(self, orgs=None, dry_run=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orgs = orgs or []
        self.dry_run = dry_run
        self.results = []
        self.stats_local = {'verified': 0, 'redirect': 0, 'dead_link': 0, 'timeout': 0, 'dns_fail': 0, 'error': 0}
        self.start_time = time.time()

    async def start(self):
        """Scrapy 2.13+ replaced start_requests() with this async generator.
        Kept the same yield contract so parse()/errback() are unaffected."""
        for org in self.orgs:
            url = org['website'].strip()
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.errback,
                meta={
                    'ein': org['EIN'],
                    'org_name': org['organization_name'],
                    'original_url': org['website'],
                    'city': org['CITY'] if 'CITY' in org.keys() else None,
                    'state': org['STATE'] if 'STATE' in org.keys() else None,
                },
                dont_filter=True,
            )

    def parse(self, response):
        ein = response.meta['ein']
        org_name = response.meta['org_name']
        original_url = response.meta['original_url']
        final_url = response.url
        final_domain = urlparse(final_url).netloc

        status = 'redirect' if final_url != response.meta.get('original_url') else 'verified'
        self.stats_local[status] += 1

        # Content verification: does this page actually belong to this org?
        # Only meaningful for text/html responses — skip PDFs, images, etc.
        confidence, matched_fields, page_title = None, [], None
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='replace')
        if 'text/html' in content_type:
            page_text = ' '.join(response.css('body ::text').getall())
            confidence, matched_fields = match_content(
                page_text, org_name, response.meta.get('city'), response.meta.get('state'), ein
            )
            page_title = response.css('title::text').get()
            if page_title:
                page_title = page_title.strip()[:200]

        result = {
            'EIN': ein,
            'original_url': original_url,
            'final_url': final_url,
            'final_domain': final_domain,
            'http_status': response.status,
            'verification_status': status,
            'error_detail': None,
            'content_confidence': confidence,
            'matched_fields': json.dumps(matched_fields) if matched_fields else None,
            'page_title': page_title,
        }
        self.results.append(result)
        conf_str = f" content={confidence}({','.join(matched_fields)})" if confidence else ""
        logger.info(f"OK  {ein} ({org_name[:30]}): {final_domain} [{response.status}]{conf_str}")

    def errback(self, failure):
        ein = failure.request.meta['ein']
        org_name = failure.request.meta['org_name']
        original_url = failure.request.meta['original_url']

        # Lesson #3: classify and log every error explicitly, never swallow.
        error_type = 'error'
        detail = repr(failure.value)

        if failure.check(scrapy.exceptions.IgnoreRequest):
            error_type = 'robots_disallowed'
        elif 'TimeoutError' in detail or 'TCPTimedOutError' in detail:
            error_type = 'timeout'
        elif 'DNSLookupError' in detail:
            error_type = 'dns_fail'
        elif 'HttpError' in detail:
            error_type = 'dead_link'

        self.stats_local[error_type] = self.stats_local.get(error_type, 0) + 1
        logger.warning(f"FAIL {ein} ({org_name[:30]}): {error_type} — {detail[:100]}")

        self.results.append({
            'EIN': ein,
            'original_url': original_url,
            'final_url': None,
            'final_domain': None,
            'http_status': None,
            'verification_status': error_type,
            'error_detail': detail[:500],
            'content_confidence': None,
            'matched_fields': None,
            'page_title': None,
        })

    def closed(self, reason):
        elapsed = time.time() - self.start_time
        total = len(self.results)
        rate = total / elapsed * 3600 if elapsed > 0 else 0

        logger.info("=" * 60)
        logger.info(f"SPIDER CLOSED: {reason}")
        logger.info(f"Total processed: {total} in {elapsed:.1f}s ({rate:.0f}/hour)")
        for status, count in self.stats_local.items():
            logger.info(f"  {status}: {count}")
        logger.info("=" * 60)

        if not self.dry_run and self.results:
            self._save_results()

    def _save_results(self):
        conn = sqlite3.connect(DB_PATH)
        conn.executemany("""
        INSERT INTO website_verification_results
        (EIN, original_url, final_url, final_domain, http_status, verification_status, error_detail,
         content_confidence, matched_fields, page_title, verified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, [
            (r['EIN'], r['original_url'], r['final_url'], r['final_domain'],
             r['http_status'], r['verification_status'], r['error_detail'],
             r.get('content_confidence'), r.get('matched_fields'), r.get('page_title'))
            for r in self.results
        ])
        conn.commit()
        conn.close()

        if self.results:
            last_ein = max(r['EIN'] for r in self.results)
            save_checkpoint(last_ein, len(self.results))
        logger.info(f"Saved {len(self.results)} results to website_verification_results")


def main():
    parser = argparse.ArgumentParser(description='Website verification spider')
    parser.add_argument('--limit', type=int, default=1000, help='Max orgs to process (spike default: 1000)')
    parser.add_argument('--dry-run', action='store_true', help='Do not write results to DB')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    args = parser.parse_args()

    ensure_output_table()
    orgs = get_orgs_to_verify(limit=args.limit, resume=args.resume)

    if not orgs:
        logger.info("No orgs to verify (empty queue or checkpoint exhausted).")
        return

    logger.info(f"Starting verification: {len(orgs)} orgs, dry_run={args.dry_run}")

    process = CrawlerProcess(settings={'LOG_ENABLED': False})
    process.crawl(WebsiteVerifierSpider, orgs=orgs, dry_run=args.dry_run)
    process.start()


if __name__ == '__main__':
    main()
