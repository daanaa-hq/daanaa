#!/usr/bin/env python3
"""
archive_website_finder.py — verify org websites from web archives instead of
crawling the org's own site.

Why (founder-directed 2026-07-18): archives are "just as good" for filling
website gaps, and they sidestep two costs at once — zero load on nonprofits'
servers, and zero bot-blocking (the 2026-07-18 crawler-etiquette change means
robots-disallowed and WAF-blocked sites are unreachable to us directly, but
the Internet Archive and Common Crawl already hold them).

Sources (both free, public, built for programmatic access):
  - Wayback Machine CDX API — snapshot existence + archived HTML retrieval
  - Common Crawl index — independent "this domain is real and crawled" signal

Verification: an archived page counts as identity-verified when enough
distinctive tokens from the org's legal name appear in the page title/text.
An archive hit proves the site EXISTED and matched the org — it does NOT
prove the site is live today, so results are written as evidence with a
recommendation, never directly to donor-facing status (P3: the honest claim
is "archived + matched", and recent-snapshot recency is reported alongside).

Usage:
    python3 scripts/archive_website_finder.py --sample 60 --pool dead
    python3 scripts/archive_website_finder.py --sample 60 --pool unchecked
    python3 scripts/archive_website_finder.py --sample 30 --pool dead --json out.json
"""

import argparse
import json
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "merit_registry.db"

UA = ("Mozilla/5.0 (compatible; DaanaaBot/1.0; "
      "+https://daanaa.org/about) archive-website-verification")
HEADERS = {"User-Agent": UA}

# Archives are built for this, but we still pace ourselves.
ARCHIVE_SPACING_S = 1.0
_last_call = [0.0]

# Generic tokens that appear in most org names and prove nothing.
STOP_TOKENS = {
    "the", "of", "and", "for", "inc", "incorporated", "foundation", "fund",
    "association", "assn", "society", "center", "centre", "corp", "corporation",
    "charitable", "trust", "ministries", "ministry", "church", "county",
    "community", "national", "american", "international", "institute", "council",
    "services", "service", "group", "friends", "club", "committee", "league",
    "org", "organization", "usa", "america", "hospital", "health", "system",
}


def _pace():
    wait = ARCHIVE_SPACING_S - (time.time() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.time()


def distinctive_tokens(name: str) -> set:
    tokens = re.findall(r"[a-z0-9]+", (name or "").lower())
    return {t for t in tokens if len(t) >= 3 and t not in STOP_TOKENS}


def wayback_latest(url: str) -> dict | None:
    """Most recent Wayback snapshot metadata for a URL (or None)."""
    _pace()
    try:
        r = requests.get(
            "https://web.archive.org/cdx/search/cdx",
            params={"url": url, "output": "json", "limit": "-1",
                    "filter": "statuscode:200", "collapse": "digest"},
            headers=HEADERS, timeout=20,
        )
        rows = r.json()
        if len(rows) < 2:
            return None
        # rows[0] is the header; with limit=-1 the last row is the newest
        header, latest = rows[0], rows[-1]
        rec = dict(zip(header, latest))
        return rec
    except Exception:
        return None


def wayback_fetch(timestamp: str, url: str) -> str | None:
    """Fetch raw archived HTML (id_ mode = original bytes, no toolbar)."""
    _pace()
    try:
        r = requests.get(
            f"https://web.archive.org/web/{timestamp}id_/{url}",
            headers=HEADERS, timeout=25,
        )
        if r.ok and "html" in (r.headers.get("content-type") or ""):
            return r.text[:200_000]
    except Exception:
        pass
    return None


def commoncrawl_seen(url: str, index: str = "CC-MAIN-2025-51") -> bool:
    """Independent existence signal from the Common Crawl index."""
    _pace()
    try:
        domain = re.sub(r"^https?://", "", url).split("/")[0]
        r = requests.get(
            f"https://index.commoncrawl.org/{index}-index",
            params={"url": f"{domain}/*", "output": "json", "limit": "1"},
            headers=HEADERS, timeout=20,
        )
        return r.ok and bool(r.text.strip())
    except Exception:
        return False


def identity_match(html: str, org_name: str) -> tuple[bool, float]:
    """Do distinctive org-name tokens appear in the archived page?"""
    want = distinctive_tokens(org_name)
    if not want:
        return False, 0.0
    text = re.sub(r"<[^>]+>", " ", html).lower()
    hits = sum(1 for t in want if t in text)
    ratio = hits / len(want)
    return ratio >= 0.5, round(ratio, 2)


def run(pool: str, sample: int, json_out: str | None) -> int:
    where = {
        "dead": "website_status = 'dead'",
        "unchecked": "(website_status IS NULL OR website_status = '')",
    }[pool]
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    rows = conn.execute(
        f"""SELECT EIN, organization_name, website FROM registry_enriched
            WHERE website IS NOT NULL AND website != '' AND {where}
            ORDER BY EIN LIMIT ?""", (sample,)
    ).fetchall()
    conn.close()

    results = []
    found = matched = cc_confirmed = 0
    for ein, name, website in rows:
        url = website if website.startswith("http") else f"https://{website}"
        rec = wayback_latest(url)
        item = {"ein": ein, "name": name, "website": website,
                "archived": False, "matched": False, "cc_seen": False,
                "snapshot": None, "match_ratio": 0.0}
        if rec:
            item["archived"] = True
            item["snapshot"] = rec.get("timestamp")
            found += 1
            html = wayback_fetch(rec["timestamp"], rec.get("original", url))
            if html:
                ok, ratio = identity_match(html, name)
                item["matched"], item["match_ratio"] = ok, ratio
                if ok:
                    matched += 1
                    if commoncrawl_seen(url):
                        item["cc_seen"] = True
                        cc_confirmed += 1
        results.append(item)
        snap = item["snapshot"] or "-"
        print(f"  [{'✓' if item['matched'] else '✗'}] {name[:44]:<44} "
              f"archived={item['archived']} match={item['match_ratio']} "
              f"snap={snap[:8]} cc={item['cc_seen']}")

    n = len(results)
    print(f"\npool={pool} n={n}: archived {found} ({100*found/max(n,1):.0f}%), "
          f"identity-matched {matched} ({100*matched/max(n,1):.0f}%), "
          f"CC-confirmed {cc_confirmed}")
    if json_out:
        Path(json_out).write_text(json.dumps(
            {"pool": pool, "run_at": datetime.now().isoformat(),
             "results": results}, indent=1))
        print(f"evidence written: {json_out}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", choices=["dead", "unchecked"], required=True)
    ap.add_argument("--sample", type=int, default=60)
    ap.add_argument("--json", dest="json_out", default=None)
    sys.exit(run(ap.parse_args().pool, ap.parse_args().sample,
                 ap.parse_args().json_out))
