#!/usr/bin/env python3
"""
Web Candidate Generator — Fast heuristic-based website discovery

Strategy:
1. Generate domain candidates using org name patterns (no network calls)
2. Store candidates in database for batch verification
3. Later: use SerpAPI or semantic matching to verify which actually exist

This MVP is fast, reliable, and produces 5-10 candidates per org.
Can be verified later with: curl, SerpAPI, or manual review.

Run:
    python3 scripts/web_candidate_generator.py --limit 1000
    python3 scripts/web_candidate_generator.py --limit 100 --dry-run
"""

import sqlite3
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"
LOG_PATH = Path.home() / "meritgiving/logs/web_candidates.log"

def log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")

def generate_candidates(org_name: str, city: str = "", state: str = "") -> list[str]:
    """
    Generate 5-10 domain candidates for an organization.
    Based on: name patterns, city, abbreviations, common TLDs.
    """
    candidates = []

    # Normalize
    name = org_name.strip().lower()
    city = (city or "").strip().lower()

    # Remove common suffixes to get core name
    core = name
    for suffix in [' inc', ' llc', ' ltd', ' foundation', ' association', ' group',
                   ' partners', ' healthcare', ' hospital', ' university', ' college',
                   ' school', ' center', ' centre', ' institute', ' corp', ' co.']:
        if core.endswith(suffix):
            core = core[:-len(suffix)].strip()

    # Pattern 1: Full name, various TLDs
    for sep in ['', '-']:
        clean = sep.join(core.split())
        candidates.extend([
            f"{clean}.org",
            f"{clean}.com",
            f"{clean}.net",
        ])

    # Pattern 2: Initials
    initials = ''.join(w[0] for w in core.split() if w)
    if len(initials) > 1:
        candidates.extend([
            f"{initials}.org",
            f"{initials}.com",
        ])

    # Pattern 3: First + Last word
    words = core.split()
    if len(words) >= 2:
        first_last = words[0] + words[-1]
        candidates.extend([
            f"{first_last}.org",
            f"{first_last}.com",
        ])

    # Pattern 4: City + org name (for local nonprofits)
    if city and len(city) > 2:
        for sep in ['', '-']:
            city_org = sep.join([city, clean] if '/' not in core else [city])
            candidates.append(f"{city_org}.org")

    # Pattern 5: First word
    if words:
        first = words[0]
        candidates.extend([
            f"{first}.org",
            f"{first}.com",
        ])

    # Deduplicate and return
    return list(dict.fromkeys(candidates))[:10]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=1000)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    log("━" * 70)
    log("Web Candidate Generator — Pattern-based discovery")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Orgs with revenue but no website
    query = """
        SELECT EIN, organization_name, CITY, STATE, total_revenue
        FROM registry_enriched
        WHERE deductibility = '1'
          AND total_revenue > 50000
          AND (website IS NULL OR website = '')
        ORDER BY total_revenue DESC
        LIMIT ?
    """

    orgs = c.execute(query, (args.limit,)).fetchall()
    log(f"Found {len(orgs)} orgs to process")

    if args.dry_run:
        log("DRY RUN — not saving results\n")

    processed = 0
    total_candidates = 0

    for row in orgs:
        ein, name, city, state, revenue = row
        candidates = generate_candidates(name, city, state)
        total_candidates += len(candidates)

        log(f"[{processed+1}/{len(orgs)}] {name} ({len(candidates)} candidates)")
        if not args.dry_run and candidates:
            # Store candidates as JSON in a new column or temp table
            candidates_json = '|'.join(candidates)  # Simple pipe-delimited
            c.execute("""
                UPDATE registry_enriched
                SET website_candidates = ?
                WHERE EIN = ?
            """, (candidates_json, ein))

        for i, cand in enumerate(candidates[:3], 1):  # Show first 3
            log(f"    {i}. {cand}")

        processed += 1

    if not args.dry_run:
        conn.commit()

    conn.close()

    log(f"\n━ Summary ━")
    log(f"Processed: {processed} orgs")
    log(f"Generated: {total_candidates} candidates")
    log(f"Avg per org: {total_candidates / max(1, processed):.1f}")
    log(f"\nNext: Use SerpAPI / Google Search to validate candidates")

if __name__ == "__main__":
    main()
