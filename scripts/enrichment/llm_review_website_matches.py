#!/usr/bin/env python3
"""
scripts/enrichment/llm_review_website_matches.py

Second-pass AI-assisted review for MEDIUM/LOW confidence results from
website_verifier_spider.py's content matching. The original pass (see
match_content() in that spider) uses substring matching only — good for a
fast first sweep, but misses abbreviations, DBA names, and org-name
paraphrases a human (or an LLM) would recognize instantly.

Fetches each org's page fresh (page text wasn't persisted by the original
run), sends org identity + page text to the local LLM, and asks for a
confidence judgment with reasoning. HIGH-confidence LLM verdicts are
auto-promoted (website_status: beta -> ok) with the same evidence
standard as the original Phase 2 promotion — the reasoning is stored,
never a black-box "the AI said so." Everything else stays flagged for a
human glance, now with an LLM-drafted starting point instead of a blank.

Crawler etiquette matches website_verifier_spider.py: honest UA, robots.txt
respected, rate-limited. Runs on-demand rather than via Scrapy's async
event loop (mixing that with blocking LLM calls is awkward) — acceptable
here given the much smaller scale (hundreds, not thousands, of orgs).

Uses the local llama-swap endpoint (port 8080, model="agent") — same
pattern as scripts/enrichment/missions/generate_missions.py. NOT the
directly-documented port 11437 in CLAUDE.md; that port isn't listening
right now (llama-swap manages backend model loading dynamically).

Usage:
    python3 scripts/enrichment/llm_review_website_matches.py --limit 20   # test run
    python3 scripts/enrichment/llm_review_website_matches.py              # full run
"""

import argparse
import json
import re
import sqlite3
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent.parent.parent / "data" / "merit_registry.db"
GEN_URL = "http://127.0.0.1:8080/v1/chat/completions"
MODEL = "agent"
UA = "Mozilla/5.0 (compatible; daanaa-crawler/1.0; +https://daanaa.org/about) llm-review"
TIMEOUT = 10
PER_DOMAIN_DELAY = 2.0  # matches the 2026-07-18 crawler-etiquette decision

_robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}


def robots_allowed(url: str) -> bool:
    domain = urlparse(url).netloc
    if domain not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"https://{domain}/robots.txt")
        try:
            rp.read()
        except Exception:
            _robots_cache[domain] = None  # unreadable robots.txt -> fail closed below
            return False
        _robots_cache[domain] = rp
    rp = _robots_cache[domain]
    return rp is not None and rp.can_fetch(UA, url)


def fetch_page_text(url: str) -> tuple[str | None, str | None]:
    """Returns (page_text, page_title) or (None, None) on any failure."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if not robots_allowed(url):
        return None, None
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA}, allow_redirects=True)
        if resp.status_code != 200 or "text/html" not in resp.headers.get("Content-Type", ""):
            return None, None
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip()[:200] if soup.title and soup.title.string else None
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ", strip=True).split())
        return text[:4000], title  # cap for LLM context budget
    except requests.exceptions.RequestException:
        return None, None


def get_orgs_to_review(limit=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT v.EIN, v.final_url, v.matched_fields, v.content_confidence AS prior_confidence,
               r.organization_name, r.CITY, r.STATE
        FROM website_verification_results v
        JOIN registry_enriched r ON r.EIN = v.EIN
        WHERE v.content_confidence IN ('MEDIUM', 'LOW')
          AND v.verified_at > datetime('now', '-1 day')
          AND r.website_status = 'beta'
        ORDER BY v.EIN
    """).fetchall()
    conn.close()
    return rows[:limit] if limit else rows


def ensure_output_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS website_llm_review (
        EIN TEXT PRIMARY KEY,
        prior_confidence TEXT,
        llm_confidence TEXT,
        llm_reasoning TEXT,
        auto_promoted INTEGER DEFAULT 0,
        reviewed_at TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def call_llm(org_name, city, state, page_text, page_title):
    prompt = f"""You are verifying whether a fetched webpage genuinely belongs to a specific nonprofit organization, for a donor-facing trust signal. Be conservative — err toward LOW if unsure, not MEDIUM or HIGH.

Organization (from IRS records): "{org_name}"
Location: {city or 'unknown'}, {state or 'unknown'}

Page title: "{page_title or '(none)'}"
Page text (truncated): "{page_text}"

Does this page genuinely belong to this specific organization? Consider abbreviations, DBA names, and paraphrases of the org name as valid matches, not just exact substrings — but do not accept a plausible-sounding but generic nonprofit page as a match without a real textual connection to THIS org.

Respond with ONLY a raw JSON object, no markdown, no explanation outside the JSON:
{{"confidence": "HIGH" | "MEDIUM" | "LOW", "reasoning": "one sentence citing specific evidence from the page text"}}"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You output only raw JSON. No markdown, no code blocks, no explanation outside the JSON object."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 200,
    }
    try:
        r = requests.post(GEN_URL, json=payload, timeout=120)
        r.raise_for_status()
        msg = r.json()["choices"][0]["message"]
        content = msg.get("content") or msg.get("reasoning_content") or ""
        m = re.search(r"\{.*\}", content, re.DOTALL)
        content = m.group() if m else content
        parsed = json.loads(content)
        conf = parsed.get("confidence", "").upper()
        if conf not in ("HIGH", "MEDIUM", "LOW"):
            return None, None
        return conf, parsed.get("reasoning", "")[:500]
    except Exception as e:
        return None, f"LLM_ERROR: {e}"[:500]


def main():
    parser = argparse.ArgumentParser(description="LLM-assisted second-pass website match review")
    parser.add_argument("--limit", type=int, default=None, help="Test run: only process first N")
    parser.add_argument("--dry-run", action="store_true", help="Do not write results or promote")
    args = parser.parse_args()

    ensure_output_table()
    orgs = get_orgs_to_review(limit=args.limit)
    print(f"Reviewing {len(orgs)} orgs (MEDIUM/LOW, still website_status='beta')", flush=True)

    conn = sqlite3.connect(DB_PATH)
    stats = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "fetch_failed": 0, "llm_failed": 0, "promoted": 0}
    last_fetch_domain = {}

    for i, org in enumerate(orgs, 1):
        ein, url, org_name = org["EIN"], org["final_url"], org["organization_name"]
        domain = urlparse(url).netloc if url else None

        # Per-domain rate limit
        if domain and domain in last_fetch_domain:
            elapsed = time.time() - last_fetch_domain[domain]
            if elapsed < PER_DOMAIN_DELAY:
                time.sleep(PER_DOMAIN_DELAY - elapsed)

        page_text, page_title = fetch_page_text(url) if url else (None, None)
        if domain:
            last_fetch_domain[domain] = time.time()

        if page_text is None:
            stats["fetch_failed"] += 1
            print(f"[{i}/{len(orgs)}] {ein} ({org_name[:30]}): fetch failed, skipped", flush=True)
            continue

        llm_conf, reasoning = call_llm(org_name, org["CITY"], org["STATE"], page_text, page_title)
        if llm_conf is None:
            stats["llm_failed"] += 1
            print(f"[{i}/{len(orgs)}] {ein}: LLM call failed ({reasoning})", flush=True)
            continue

        stats[llm_conf] += 1
        promoted = 0
        if llm_conf == "HIGH" and not args.dry_run:
            conn.execute(
                "UPDATE registry_enriched SET website_status = 'ok' WHERE EIN = ? AND website_status = 'beta'",
                (ein,),
            )
            promoted = 1
            stats["promoted"] += 1

        if not args.dry_run:
            conn.execute("""
                INSERT OR REPLACE INTO website_llm_review
                (EIN, prior_confidence, llm_confidence, llm_reasoning, auto_promoted, reviewed_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (ein, org["prior_confidence"], llm_conf, reasoning, promoted))
            conn.commit()

        print(f"[{i}/{len(orgs)}] {ein} ({org_name[:30]}): llm={llm_conf}"
              f"{' -> PROMOTED' if promoted else ''} — {reasoning[:80]}", flush=True)

    conn.close()
    print("=" * 60)
    print(f"HIGH: {stats['HIGH']}  MEDIUM: {stats['MEDIUM']}  LOW: {stats['LOW']}")
    print(f"Fetch failed: {stats['fetch_failed']}  LLM failed: {stats['llm_failed']}")
    print(f"Auto-promoted: {stats['promoted']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
