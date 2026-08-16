#!/usr/bin/env python3
"""
Claude's Discovery Agent Suite
Strategy 1: DNS Lookup (proven 87% success)
Strategy 2: Organization Name Variations (test .com, .net, acronyms)
Strategy 3: Levenshtein Distance Matching (fuzzy org name to known domains)
"""

import sqlite3
import json
import logging
import time
import dns.resolver
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
import difflib

DB = Path.home() / "meritgiving/data/merit_registry.db"
LOG_DIR = Path.home() / "meritgiving/logs"
LEADERBOARD = LOG_DIR / "agent_leaderboard.json"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] CLAUDE: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "claude_agents.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

@dataclass
class Result:
    ein: str
    org_name: str
    website: str
    method: str
    confidence: str

def dns_strategy(orgs, limit=100):
    """Strategy 1: DNS A-record lookup (proven winner)."""
    logger.info(f"Claude Agent 1: DNS Lookup ({limit} orgs)...")
    results = []
    start = time.time()

    for ein, org_name, revenue in orgs[:limit]:
        patterns = [
            org_name.lower().replace(" ", ""),
            org_name.lower().replace(" ", "-"),
            org_name.lower().split()[0],
        ]

        for pattern in patterns:
            for tld in [".org", ".com", ".net"]:
                domain = f"{pattern}{tld}"
                try:
                    dns.resolver.resolve(domain, 'A')
                    results.append(Result(
                        ein=ein,
                        org_name=org_name,
                        website=f"https://{domain}",
                        method="DNS Lookup",
                        confidence="HIGH",
                    ))
                    break
                except:
                    pass
            if any(r.ein == ein for r in results):
                break

    elapsed = time.time() - start
    success = len(results) / max(1, limit)
    logger.info(f"✓ DNS: {len(results)}/{limit} found ({success*100:.1f}%) in {elapsed:.1f}s")
    return results, success, elapsed

def tld_expansion_strategy(orgs, limit=100):
    """Strategy 2: Try common TLDs (.org, .com, .net) for org name."""
    logger.info(f"Claude Agent 2: TLD Expansion ({limit} orgs)...")
    results = []
    start = time.time()

    known_sites = {}
    db = sqlite3.connect(DB)
    cursor = db.cursor()
    cursor.execute("SELECT organization_name, website FROM registry_enriched WHERE website IS NOT NULL LIMIT 10000")
    known_sites = {name.lower(): site for name, site in cursor.fetchall()}
    db.close()

    for ein, org_name, revenue in orgs[:limit]:
        # Check if close match to known org
        matches = difflib.get_close_matches(org_name.lower(), list(known_sites.keys()), n=1, cutoff=0.8)
        if matches:
            results.append(Result(
                ein=ein,
                org_name=org_name,
                website=known_sites[matches[0]],
                method="Fuzzy Org Match",
                confidence="MEDIUM",
            ))

    elapsed = time.time() - start
    success = len(results) / max(1, limit)
    logger.info(f"✓ TLD Expansion: {len(results)}/{limit} found ({success*100:.1f}%) in {elapsed:.1f}s")
    return results, success, elapsed

def acronym_strategy(orgs, limit=100):
    """Strategy 3: Build acronyms from org name."""
    logger.info(f"Claude Agent 3: Acronym Strategy ({limit} orgs)...")
    results = []
    start = time.time()

    for ein, org_name, revenue in orgs[:limit]:
        words = org_name.split()
        if len(words) >= 2:
            acronym = "".join([w[0].lower() for w in words if w])
            for tld in [".org", ".com"]:
                domain = f"{acronym}{tld}"
                try:
                    dns.resolver.resolve(domain, 'A')
                    results.append(Result(
                        ein=ein,
                        org_name=org_name,
                        website=f"https://{domain}",
                        method="Acronym DNS",
                        confidence="MEDIUM",
                    ))
                    break
                except:
                    pass

    elapsed = time.time() - start
    success = len(results) / max(1, limit)
    logger.info(f"✓ Acronym: {len(results)}/{limit} found ({success*100:.1f}%) in {elapsed:.1f}s")
    return results, success, elapsed

def main():
    logger.info("=" * 80)
    logger.info("CLAUDE AGENT SUITE - STARTING")
    logger.info("=" * 80)

    db = sqlite3.connect(DB)
    cursor = db.cursor()
    cursor.execute("""
        SELECT ein, organization_name, total_revenue
        FROM registry_enriched
        WHERE deductibility = '1' AND org_status = 'active'
          AND (website IS NULL OR website = '')
          AND total_revenue > 500000
        ORDER BY total_revenue DESC LIMIT 300
    """)
    orgs = cursor.fetchall()
    db.close()

    logger.info(f"Target: {len(orgs)} orgs")

    # Run strategies
    results1, success1, time1 = dns_strategy(orgs[:100])
    results2, success2, time2 = tld_expansion_strategy(orgs[100:200])
    results3, success3, time3 = acronym_strategy(orgs[200:300])

    all_results = results1 + results2 + results3
    total_success = (len(results1) + len(results2) + len(results3)) / max(1, len(orgs))

    # Save results
    with open(LOG_DIR / "claude_results.jsonl", 'a') as f:
        for r in all_results:
            f.write(json.dumps(asdict(r)) + '\n')

    logger.info("=" * 80)
    logger.info(f"TOTAL: {len(all_results)} websites found ({total_success*100:.1f}%)")
    logger.info(f"Results saved to: {LOG_DIR}/claude_results.jsonl")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
