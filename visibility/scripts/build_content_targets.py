#!/usr/bin/env python3
"""Build content and backlink targets from local nonprofit data.

This is overlay-only planning. It does not modify the app or deployment config.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "merit_registry.db"
REPORTS = ROOT / "visibility" / "reports"


def one(conn: sqlite3.Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def rows(conn: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    return list(conn.execute(sql))


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    active_filter = "org_status = 'active' AND CAST(deductibility AS TEXT) = '1'"
    total_active = one(conn, f"SELECT COUNT(*) FROM registry_enriched WHERE {active_filter}")
    website_count = one(
        conn,
        f"SELECT COUNT(*) FROM registry_enriched WHERE {active_filter} AND COALESCE(website, website_url, '') != ''",
    )
    claim_started = one(conn, "SELECT COUNT(DISTINCT ein) FROM org_claims")
    verified_claimed = one(conn, "SELECT COUNT(DISTINCT ein) FROM org_claims WHERE claim_status = 'verified'")
    donation_evidence = one(conn, "SELECT COUNT(DISTINCT ein) FROM donation_link_evidence")
    volunteer_events = one(conn, "SELECT COUNT(*) FROM volunteer_events")
    vendor_count = one(conn, "SELECT COUNT(*) FROM vendors")

    top_states = [dict(r) for r in rows(conn, f"""
        SELECT COALESCE(STATE, '') AS state, COUNT(*) AS orgs
        FROM registry_enriched
        WHERE {active_filter}
        GROUP BY state
        ORDER BY orgs DESC
        LIMIT 25
    """)]
    top_categories = [dict(r) for r in rows(conn, f"""
        SELECT SUBSTR(COALESCE(NULLIF(NTEE1, ''), NULLIF(NTEECC, ''), 'Z'), 1, 1) AS category, COUNT(*) AS orgs
        FROM registry_enriched
        WHERE {active_filter}
        GROUP BY category
        ORDER BY orgs DESC
        LIMIT 25
    """)]
    top_markets = [dict(r) for r in rows(conn, f"""
        SELECT COALESCE(metro, CITY || ', ' || STATE) AS market, COUNT(*) AS orgs
        FROM registry_enriched
        WHERE {active_filter}
          AND COALESCE(metro, CITY, '') != ''
        GROUP BY market
        ORDER BY orgs DESC
        LIMIT 25
    """)]

    target_pages = [
        {
            "path": "/claim-nonprofit-page",
            "purpose": "Nonprofit claim acquisition",
            "why": "Highest conversion path for unclaimed nonprofit pages.",
        },
        {
            "path": "/nonprofit-vendor-discounts",
            "purpose": "Vendor acquisition",
            "why": "Create a separate entry point for small businesses serving nonprofits.",
        },
        {
            "path": "/open-data",
            "purpose": "Open data landing page",
            "why": "Explains the data corpus to search engines and AI tools.",
        },
        {
            "path": "/nonprofit-data-sources",
            "purpose": "Source transparency",
            "why": "Useful for trust, citations, and AI context extraction.",
        },
        {
            "path": "/nonprofit-profile-guide",
            "purpose": "User education",
            "why": "Helps nonprofit staff understand how to use and claim a page.",
        },
        {
            "path": "/nonprofit-vendor-guide",
            "purpose": "Vendor education",
            "why": "Explains nonprofit-friendly vendor participation and discount codes.",
        },
    ]

    prospect_targets = [
        "State nonprofit associations",
        "United Way chapters",
        "Community foundations",
        "Volunteer centers",
        "Small business development centers",
        "University nonprofit-management programs",
        "Grantmaker associations",
        "Local chambers of commerce",
        "Accounting and bookkeeping firms serving nonprofits",
        "Web, design, and printing firms serving nonprofits",
    ]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "data/merit_registry.db",
        "counts": {
            "active_deductible_orgs": total_active,
            "orgs_with_website": website_count,
            "claim_started": claim_started,
            "verified_claimed": verified_claimed,
            "donation_evidence": donation_evidence,
            "volunteer_events": volunteer_events,
            "vendors": vendor_count,
        },
        "target_pages": target_pages,
        "prospect_targets": prospect_targets,
        "top_states": top_states,
        "top_categories": top_categories,
        "top_markets": top_markets,
    }

    (REPORTS / "content-targets.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    md_lines: list[str] = [
        "# Content Targets",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Core Counts",
        "",
        f"- Active deductible orgs: {total_active:,}",
        f"- Orgs with website: {website_count:,}",
        f"- Claim started orgs: {claim_started:,}",
        f"- Verified claimed orgs: {verified_claimed:,}",
        f"- Donation evidence records: {donation_evidence:,}",
        f"- Volunteer events: {volunteer_events:,}",
        f"- Vendors: {vendor_count:,}",
        "",
        "## Priority Pages",
        "",
    ]
    for item in target_pages:
        md_lines.append(f"- `{item['path']}` - {item['purpose']}: {item['why']}")

    md_lines += ["", "## Prospect Targets", ""]
    md_lines.extend(f"- {item}" for item in prospect_targets)

    md_lines += ["", "## Top States", ""]
    md_lines.extend(f"- {item['state'] or 'Unknown'}: {item['orgs']:,}" for item in top_states[:10])

    md_lines += ["", "## Top Categories", ""]
    md_lines.extend(f"- {item['category']}: {item['orgs']:,}" for item in top_categories[:10])

    md_lines += ["", "## Top Markets", ""]
    md_lines.extend(f"- {item['market']}: {item['orgs']:,}" for item in top_markets[:10])

    md_lines += [
        "",
        "## Recommended Content Themes",
        "",
        "- Public nonprofit profile discovery.",
        "- How nonprofits can claim and update their page.",
        "- How donors can use Daanaa to read public context before giving.",
        "- How nonprofit-friendly vendors can join with transparent discounts.",
        "- Why public data transparency improves trust and search discoverability.",
    ]

    (REPORTS / "content-targets.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote {REPORTS / 'content-targets.json'}")
    print(f"Wrote {REPORTS / 'content-targets.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
