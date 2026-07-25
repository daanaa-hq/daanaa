#!/usr/bin/env python3
"""
Harvest official websites from IRS Form 990 e-file XML.

Every NCCS summary row carries the S3 URL of the org's raw 990 XML, and that
XML holds <WebsiteAddressTxt> — the website the organization itself reported on
its tax return. That is the strongest website evidence available to us: self
reported, public record, dated. Stewardship P3 (evidence-based signals).

Newest filing year first; an org already holding a website is never overwritten,
so re-runs only fill holes. Progress is checkpointed per year, so a kill and
restart resumes rather than refetching.

Usage:
    python3 scripts/harvest_990_websites.py --year 2023 [--concurrency 50] [--limit N]
"""
import argparse
import asyncio
import csv
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import aiohttp

DB = Path.home() / "meritgiving" / "data" / "merit_registry.db"
NCCS_DIR = Path.home() / "meritgiving" / "data" / "nccs"
LOG_DIR = Path.home() / "meritgiving" / "logs"
LOG = LOG_DIR / "harvest_990_websites.log"

WEBSITE_RE = re.compile(r"<WebsiteAddressTxt>(.*?)</WebsiteAddressTxt>", re.IGNORECASE | re.DOTALL)
# Values orgs write when they have no site. Treated as "no website", not a URL.
NULL_TOKENS = {
    "", "N/A", "NA", "NONE", "N A", "NO", "NOT APPLICABLE", "NONE.", "N/A.",
    "NO WEBSITE", "NOWEBSITE", "N/A NO WEBSITE", "0", "-", "--", "WWW", "TBD",
}
FLUSH_EVERY = 2_000


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as fh:
        fh.write(line + "\n")


def normalize(raw):
    """Return a usable https URL, or None when the filer reported no site."""
    if not raw:
        return None
    val = raw.strip().strip('"').strip()
    if val.upper() in NULL_TOKENS:
        return None
    val = val.split()[0] if " " in val else val
    val = val.rstrip(".,;")
    if val.lower().startswith(("http://", "https://")):
        host = val.split("://", 1)[1]
    else:
        host = val
    host = host.strip("/")
    if "." not in host or len(host) < 4:
        return None
    if any(c in host for c in "<>\"' "):
        return None
    return "https://" + host.lower()


def load_targets(year, limit=None):
    """EINs still missing a website, paired with their 990 XML URL."""
    conn = sqlite3.connect(str(DB), timeout=120)
    missing = {r[0] for r in conn.execute(
        "SELECT EIN FROM registry_enriched WHERE website IS NULL OR website = ''"
    )}
    conn.close()
    log(f"{len(missing):,} orgs currently have no website")

    path = NCCS_DIR / f"F9-P01-T00-SUMMARY-{year}.CSV"
    targets = []
    seen = set()
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for row in csv.DictReader(fh):
            ein = (row.get("ORG_EIN") or "").strip().zfill(9)
            url = (row.get("URL") or "").strip().strip('"')
            if not ein or not url.startswith("http") or ein in seen:
                continue
            if ein not in missing:
                continue
            seen.add(ein)
            targets.append((ein, url))
            if limit and len(targets) >= limit:
                break
    log(f"{year}: {len(targets):,} filings to fetch")
    return targets


def checkpoint_path(year):
    return LOG_DIR / f".harvest_990_{year}.done"


def load_done(year):
    p = checkpoint_path(year)
    if not p.exists():
        return set()
    return set(p.read_text().split())


async def fetch_one(session, sem, ein, url):
    async with sem:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return ein, None
                body = await resp.text(errors="ignore")
        except Exception:
            return ein, None
    m = WEBSITE_RE.search(body)
    return ein, normalize(m.group(1)) if m else None


async def run(year, concurrency, limit):
    targets = load_targets(year, limit)
    done = load_done(year)
    if done:
        targets = [t for t in targets if t[0] not in done]
        log(f"{year}: resuming — {len(done):,} already fetched, {len(targets):,} left")
    if not targets:
        log(f"{year}: nothing to do")
        return 0

    conn = sqlite3.connect(str(DB), timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")
    ckpt = open(checkpoint_path(year), "a")

    sem = asyncio.Semaphore(concurrency)
    timeout = aiohttp.ClientTimeout(total=25)
    connector = aiohttp.TCPConnector(limit=concurrency, ttl_dns_cache=300)
    headers = {"User-Agent": "Daanaa-DataBot/1.0 (hello@daanaa.org)"}

    found = fetched = written = 0
    pending = []
    started = datetime.now()

    async with aiohttp.ClientSession(timeout=timeout, connector=connector, headers=headers) as session:
        tasks = [fetch_one(session, sem, ein, url) for ein, url in targets]
        for coro in asyncio.as_completed(tasks):
            ein, site = await coro
            fetched += 1
            ckpt.write(ein + "\n")
            if site:
                found += 1
                pending.append((site, year, ein))

            if len(pending) >= FLUSH_EVERY:
                conn.executemany(
                    "UPDATE registry_enriched SET website=?, website_source='irs_990_xml', "
                    "website_last_verified=? WHERE EIN=? AND (website IS NULL OR website='')",
                    pending,
                )
                conn.commit()
                written += len(pending)
                pending.clear()
                ckpt.flush()

            if fetched % 10_000 == 0:
                rate = fetched / max(1, (datetime.now() - started).total_seconds())
                remaining = (len(targets) - fetched) / max(rate, 0.1) / 60
                log(f"{year}: {fetched:,}/{len(targets):,} fetched | {found:,} sites "
                    f"({100*found/fetched:.1f}%) | {rate:.0f}/s | ~{remaining:.0f}m left")

    if pending:
        conn.executemany(
            "UPDATE registry_enriched SET website=?, website_source='irs_990_xml', "
            "website_last_verified=? WHERE EIN=? AND (website IS NULL OR website='')",
            pending,
        )
        conn.commit()
        written += len(pending)

    total = conn.execute("SELECT COUNT(website) FROM registry_enriched").fetchone()[0]
    conn.close()
    ckpt.close()

    log("=" * 70)
    log(f"{year} complete: {fetched:,} filings fetched, {found:,} websites found, {written:,} written")
    log(f"Website coverage now: {total:,}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default="2023")
    ap.add_argument("--concurrency", type=int, default=50)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    sys.exit(asyncio.run(run(args.year, args.concurrency, args.limit)))
