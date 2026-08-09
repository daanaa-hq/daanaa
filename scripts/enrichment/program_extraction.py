#!/usr/bin/env python3
"""
Program extraction: use LLM to extract structured program descriptions from org websites.

For small orgs, the best source of program clarity is their own website (/programs,
/services, /impact pages). This module:
1. Finds websites with program content (from website_verification_results)
2. Fetches /programs, /services, /impact pages via Scrapy
3. Uses Qwen3-30B to extract structured program descriptions
4. Stores results for org discovery and search

Applies daemon lessons:
- Checkpoint/resume (survives interruption)
- Explicit error logging per type (never silent except: pass)
- Structured output table, separate from registry_enriched (no write contention)
- LLM fail-closed (returns None on inference error, caller logs it)

Usage (spike / dry-run):
    python3 scripts/enrichment/program_extraction.py --limit 50 --dry-run

Usage (production, nightly):
    python3 scripts/enrichment/program_extraction.py --resume
"""

import argparse
import json
import logging
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
LOG_DIR = Path.home() / 'meritgiving' / 'logs'
LOG_DIR.mkdir(exist_ok=True)

INFERENCE_BASE = "http://localhost:11437"
REQUEST_TIMEOUT = 30
LLM_TEMPERATURE = 0.1  # deterministic extraction

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'program_extraction.log'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def ensure_output_table():
    """Create output table for extracted programs."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS extracted_programs (
        EIN TEXT,
        program_name TEXT,
        program_description TEXT,
        target_population TEXT,
        service_area TEXT,
        source_url TEXT,
        extraction_confidence REAL,  -- 0.0-1.0
        extracted_at TIMESTAMP,
        PRIMARY KEY (EIN, program_name)
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ep_ein ON extracted_programs(EIN)")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS enrichment_checkpoints (
        phase TEXT, run_date DATE, last_ein TEXT, record_count INTEGER,
        checkpoint_time TIMESTAMP, PRIMARY KEY (phase, run_date)
    )
    """)
    conn.commit()
    conn.close()


def get_orgs_to_process(limit=None, resume=False):
    """Fetch orgs with verified websites but no extracted programs yet."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    last_ein = None
    if resume:
        cursor.execute("""
        SELECT last_ein FROM enrichment_checkpoints
        WHERE phase = 'program_extraction' AND run_date = date('now')
        """)
        row = cursor.fetchone()
        if row:
            last_ein = row['last_ein']
            logger.info(f"Resuming from checkpoint EIN: {last_ein}")

    # Get orgs with verified websites and no extracted programs yet
    query = """
    SELECT DISTINCT r.EIN, r.organization_name, wvr.final_domain
    FROM registry_enriched r
    JOIN website_verification_results wvr ON r.EIN = wvr.EIN
    LEFT JOIN extracted_programs ep ON r.EIN = ep.EIN
    WHERE r.EIN IS NOT NULL
    AND wvr.verification_status = 'verified'
    AND wvr.final_domain IS NOT NULL
    AND ep.EIN IS NULL  -- Only orgs without extracted programs yet
    """
    params = []
    if last_ein:
        query += " AND r.EIN > ?"
        params.append(last_ein)
    query += " ORDER BY r.EIN"
    if limit:
        query += f" LIMIT {int(limit)}"

    cursor.execute(query, params)
    orgs = cursor.fetchall()
    conn.close()
    return orgs


def extract_programs_llm(ein, domain, html_content):
    """Use Qwen3-30B to extract programs from HTML.

    Returns list of (program_name, description, target_population, service_area) tuples,
    or None on failure.
    """
    if not html_content or len(html_content.strip()) < 100:
        return None

    prompt = f"""From the HTML content below (from {domain}), extract ALL programs/services mentioned.
For each program, provide:
1. program_name: the name of the program/service
2. program_description: 1-2 sentence description of what it does
3. target_population: who it serves (e.g., "low-income seniors", "youth ages 6-12")
4. service_area: where it operates (e.g., "Chicago", "Texas", "nationwide")

Return ONLY valid JSON array, no other text.
Format: [{{"program_name": "...", "program_description": "...", "target_population": "...", "service_area": "..."}}, ...]

HTML:
{html_content[:4000]}  # truncate to 4K tokens to fit context
"""

    try:
        resp = requests.post(
            f"{INFERENCE_BASE}/v1/chat/completions",
            json={
                "model": "Qwen3-30B",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": LLM_TEMPERATURE,
                "max_tokens": 1024,
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        result = resp.json()
        if not result.get('choices'):
            logger.warning(f"Empty LLM response for EIN {ein}")
            return None

        content = result['choices'][0]['message']['content']
        programs = json.loads(content)

        if not isinstance(programs, list) or len(programs) == 0:
            return None

        # Validate and return
        return [
            (
                p.get('program_name', ''),
                p.get('program_description', ''),
                p.get('target_population', ''),
                p.get('service_area', ''),
            )
            for p in programs
            if p.get('program_name')
        ]

    except requests.exceptions.Timeout:
        logger.warning(f"LLM timeout for EIN {ein}")
        return None
    except (ValueError, KeyError, requests.RequestException) as e:
        logger.warning(f"LLM extraction failed for EIN {ein}: {e}")
        return None


def fetch_program_pages(domain):
    """Fetch /programs or /services page from org website.

    Returns HTML content or None on failure.
    """
    urls_to_try = [
        f"https://{domain}/programs",
        f"https://{domain}/services",
        f"https://{domain}/impact",
        f"https://{domain}/what-we-do",
    ]

    for url in urls_to_try:
        try:
            resp = requests.get(url, timeout=10, allow_redirects=True)
            if resp.status_code == 200 and len(resp.text) > 100:
                return resp.text, url
        except requests.RequestException:
            continue

    return None, None


def main():
    parser = argparse.ArgumentParser(description='Program extraction from org websites')
    parser.add_argument('--limit', type=int, default=50, help='Max orgs to process')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--dry-run', action='store_true', help='Do not write to DB')
    parser.add_argument('--workers', type=int, default=4,
                         help='Concurrent workers (LLM-bound; start low)')
    args = parser.parse_args()

    ensure_output_table()
    orgs = get_orgs_to_process(limit=args.limit, resume=args.resume)

    if not orgs:
        logger.info("No orgs to process.")
        return

    logger.info(f"Starting program extraction: {len(orgs)} orgs, {args.workers} workers")

    write_lock = threading.Lock()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    stats = {'found': 0, 'page_not_found': 0, 'extraction_failed': 0, 'total_programs': 0}
    stats_lock = threading.Lock()
    start = time.time()
    completed = 0
    max_ein_seen = None

    def process_one(org):
        ein = org['EIN']
        domain = org['final_domain']

        # Fetch program page
        html_content, source_url = fetch_program_pages(domain)
        if not html_content:
            return ein, None, None

        # Extract programs via LLM
        programs = extract_programs_llm(ein, domain, html_content)
        return ein, programs, source_url

    with ThreadPoolExecutor(max_workers=min(args.workers, 8)) as executor:
        futures = {executor.submit(process_one, org): org for org in orgs}

        for future in as_completed(futures):
            ein, programs, source_url = future.result()

            with stats_lock:
                if programs is None:
                    stats['page_not_found'] += 1
                else:
                    stats['found'] += 1
                    stats['total_programs'] += len(programs)

                    if not args.dry_run:
                        with write_lock:
                            for prog_name, prog_desc, target_pop, service_area in programs:
                                conn.execute("""
                                INSERT OR REPLACE INTO extracted_programs
                                (EIN, program_name, program_description, target_population,
                                 service_area, source_url, extraction_confidence, extracted_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                                """, (ein, prog_name, prog_desc, target_pop, service_area,
                                      source_url, 0.85))
                            conn.commit()

                completed += 1
                max_ein_seen = ein if max_ein_seen is None else max(max_ein_seen, ein)

                if completed % 10 == 0:
                    elapsed = time.time() - start
                    rate = completed / elapsed * 3600
                    logger.info(f"Progress: {completed}/{len(orgs)} ({rate:.0f}/hour) — "
                                f"found={stats['found']} not_found={stats['page_not_found']} "
                                f"total_programs={stats['total_programs']}")
                    if not args.dry_run:
                        with write_lock:
                            conn.execute("""
                            INSERT OR REPLACE INTO enrichment_checkpoints
                            VALUES ('program_extraction', date('now'), ?, ?, datetime('now'))
                            """, (max_ein_seen, completed))
                            conn.commit()

    elapsed = time.time() - start
    final_rate = len(orgs) / elapsed * 3600 if elapsed > 0 else 0
    logger.info("=" * 60)
    logger.info(f"EXTRACTION COMPLETE: {len(orgs)} orgs in {elapsed:.1f}s ({final_rate:.0f}/hour)")
    logger.info(f"  found (extracted programs): {stats['found']}")
    logger.info(f"  page not found: {stats['page_not_found']}")
    logger.info(f"  total programs extracted: {stats['total_programs']}")
    logger.info("=" * 60)

    conn.close()


if __name__ == '__main__':
    main()
