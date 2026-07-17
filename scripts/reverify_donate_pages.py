#!/usr/bin/env python3
"""
reverify_donate_pages.py — verify that low-confidence live donate links
actually present a donation path (P3: trust signals must be evidence-based).

Scope: donate_url_status='beta' AND donate_confidence < 70 whose URL does not
already look donate-like (those pass on URL evidence alone). For the rest we
fetch the page and look for donation markers:
  - embedded donation processors (donorbox, classy, givebutter, ...)
  - donate-intent link/button text ("donate", "give now", "make a gift", ...)

Verdict policy (LESSONS 2026-07-16: definitive vs inconclusive):
  - Page loads and HAS markers            -> keep live, stamp donate_checked_at
  - Page loads (200) and has NO markers   -> demote to 'pending_review'
  - Definitive dead (404/410/401/403)     -> demote to 'pending_review'
  - Inconclusive (timeout, 429, 5xx, DNS) -> leave untouched for a later pass

Demotion is a status flip stamped with donate_checked_at — reversible by
timestamp window, never a destructive write.

Concurrency stays at 2 workers while the discovery daemon shares the network
(LESSONS 2026-07-16).

Run:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/reverify_donate_pages.py [--limit N] [--dry-run]
"""

import argparse
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests

DB = Path.home() / "meritgiving/data/merit_registry.db"
LOG = Path.home() / "meritgiving/logs/reverify_donate_pages.log"

WORKERS = 2
TIMEOUT = 15
UA = "Mozilla/5.0 (compatible; DaanaaLinkCheck/1.0; +https://daanaa.org)"

# URLs matching these need no content check — the URL itself is donate evidence
URL_PASS = re.compile(
    r"donat|/give|giving|contribut|support-?us|paypal\.com|gofundme|networkforgood"
    r"|donorbox|givebutter|classy\.org|every\.org|givelively|fundrais|/gift",
    re.I,
)

# Donation processors whose presence in page HTML is strong evidence
PROCESSORS = re.compile(
    r"donorbox|givebutter|classy\.org|networkforgood|qgiv|bloomerang|kindful"
    r"|neonone|neoncrm|givelively|every\.org|fundraiseup|snowballfundraising"
    r"|continuetogive|tithe\.ly|pushpay|easytithe|givesmart|onecause|paypal\.com/donate"
    r"|paypal\.com/cgi-bin|streamlabscharity|justgiving|givecampus|raisely|zeffy"
    r"|stripe\.com|squareup\.com|venmo\.com",
    re.I,
)

# Donate-intent text in links/buttons (word-boundary, case-insensitive)
INTENT = re.compile(
    r"\bdonate\b|\bgive now\b|\bgive today\b|\bmake a (?:gift|donation)\b"
    r"|\bsupport us\b|\bways to give\b|\bgive online\b|\bcontribute\b"
    r"|\bplanned giving\b|\bone-?time gift\b|\bmonthly gift\b",
    re.I,
)

DEFINITIVE_DEAD = {401, 403, 404, 410}


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as fh:
        fh.write(line + "\n")


def check_page(url: str) -> str:
    """Return verdict: 'pass' | 'fail' | 'dead' | 'inconclusive'."""
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA},
                            allow_redirects=True)
    except requests.RequestException:
        return "inconclusive"
    if resp.status_code in DEFINITIVE_DEAD:
        return "dead"
    if resp.status_code != 200:
        return "inconclusive"
    html = resp.text[:500_000]
    if PROCESSORS.search(html) or INTENT.search(html):
        return "pass"
    # Final-URL rescue: some sites redirect the odd path to their donate page
    if URL_PASS.search(resp.url or ""):
        return "pass"
    return "fail"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=120000")
    rows = con.execute("""
        SELECT EIN, donate_url FROM registry_enriched
        WHERE donate_url_status='beta' AND donate_confidence < 70
          AND donate_url IS NOT NULL AND donate_url != ''
        ORDER BY EIN
    """).fetchall()

    targets = [(ein, url) for ein, url in rows if not URL_PASS.search(url)]
    log(f"{len(rows):,} low-confidence beta links; {len(targets):,} need a content check "
        f"({len(rows) - len(targets):,} pass on URL evidence)")

    if args.limit:
        targets = targets[: args.limit]

    now = datetime.now(timezone.utc).isoformat()
    counts = {"pass": 0, "fail": 0, "dead": 0, "inconclusive": 0}
    pending_updates = []  # (verdict, ein)

    def flush():
        if args.dry_run or not pending_updates:
            pending_updates.clear()
            return
        demote = [(now, ein) for v, ein in pending_updates if v in ("fail", "dead")]
        keep = [(now, ein) for v, ein in pending_updates if v == "pass"]
        if demote:
            con.executemany("""
                UPDATE registry_enriched
                SET donate_url_status='pending_review', donate_checked_at=?
                WHERE EIN=? AND donate_url_status='beta'
            """, demote)
        if keep:
            con.executemany("""
                UPDATE registry_enriched SET donate_checked_at=?
                WHERE EIN=? AND donate_url_status='beta'
            """, keep)
        con.commit()
        pending_updates.clear()

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(check_page, url): ein for ein, url in targets}
        done = 0
        for fut in as_completed(futures):
            ein = futures[fut]
            verdict = fut.result()
            counts[verdict] += 1
            if verdict != "inconclusive":
                pending_updates.append((verdict, ein))
            done += 1
            if len(pending_updates) >= 200:
                flush()
            if done % 500 == 0:
                rate = done / (time.time() - t0)
                eta_min = (len(targets) - done) / rate / 60 if rate else 0
                log(f"{done:,}/{len(targets):,} checked ({rate:.1f}/s, ~{eta_min:.0f} min left) "
                    f"| pass {counts['pass']} fail {counts['fail']} "
                    f"dead {counts['dead']} inconclusive {counts['inconclusive']}")
    flush()
    con.close()

    log(f"DONE: {counts['pass']:,} verified donate pages kept | "
        f"{counts['fail']:,} not-a-donate-page demoted | {counts['dead']:,} dead demoted | "
        f"{counts['inconclusive']:,} inconclusive left for retry"
        + (" [DRY RUN — no writes]" if args.dry_run else ""))


if __name__ == "__main__":
    main()
