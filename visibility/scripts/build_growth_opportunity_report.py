#!/usr/bin/env python3
"""Build read-only growth opportunity reports for claims, donors, volunteers, and vendors."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "merit_registry.db"
REPORTS = ROOT / "visibility" / "reports"


def one(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    return int(conn.execute(sql, params).fetchone()[0])


def rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params))


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    active_filter = "org_status = 'active' AND CAST(deductibility AS TEXT) = '1'"
    total_active = one(conn, f"SELECT COUNT(*) FROM registry_enriched WHERE {active_filter}")
    claimed = one(conn, "SELECT COUNT(DISTINCT ein) FROM org_claims WHERE claim_status = 'verified'")
    claim_started = one(conn, "SELECT COUNT(DISTINCT ein) FROM org_claims")
    websites = one(conn, f"SELECT COUNT(*) FROM registry_enriched WHERE {active_filter} AND COALESCE(website, website_url, '') != ''")
    missions = one(conn, f"SELECT COUNT(*) FROM registry_enriched WHERE {active_filter} AND COALESCE(mission, '') != ''")
    donation_candidates = one(conn, "SELECT COUNT(DISTINCT ein) FROM donation_link_evidence")
    donation_public_allowed = one(
        conn,
        "SELECT COUNT(DISTINCT ein) FROM donation_link_evidence WHERE public_display_allowed = 1 OR decision = 'allow'",
    )
    vendor_count = one(conn, "SELECT COUNT(*) FROM vendors")
    active_vendor_codes = one(conn, "SELECT COUNT(*) FROM vendor_codes WHERE is_active = 1")
    volunteer_events = one(conn, "SELECT COUNT(*) FROM volunteer_events")
    active_volunteer_events = one(conn, "SELECT COUNT(*) FROM volunteer_events WHERE status = 'active'")

    top_states = [
        dict(r)
        for r in rows(
            conn,
            f"""
            SELECT STATE AS state, COUNT(*) AS orgs
            FROM registry_enriched
            WHERE {active_filter} AND COALESCE(STATE, '') != ''
            GROUP BY STATE
            ORDER BY orgs DESC
            LIMIT 20
            """,
        )
    ]
    top_categories = [
        dict(r)
        for r in rows(
            conn,
            f"""
            SELECT SUBSTR(COALESCE(NULLIF(NTEE1, ''), NULLIF(NTEECC, ''), 'Z'), 1, 1) AS category, COUNT(*) AS orgs
            FROM registry_enriched
            WHERE {active_filter}
            GROUP BY category
            ORDER BY orgs DESC
            LIMIT 20
            """,
        )
    ]
    top_metros = [
        dict(r)
        for r in rows(
            conn,
            f"""
            SELECT COALESCE(metro, CITY || ', ' || STATE) AS market, COUNT(*) AS orgs
            FROM registry_enriched
            WHERE {active_filter}
              AND COALESCE(metro, CITY, '') != ''
            GROUP BY market
            ORDER BY orgs DESC
            LIMIT 25
            """,
        )
    ]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "data/merit_registry.db",
        "active_deductible_orgs": total_active,
        "nonprofit_claims": {
            "claim_started_orgs": claim_started,
            "verified_claimed_orgs": claimed,
            "unclaimed_estimate": max(total_active - claimed, 0),
            "claim_started_rate": round(claim_started / total_active, 6) if total_active else 0,
            "verified_claim_rate": round(claimed / total_active, 6) if total_active else 0,
        },
        "donor_readiness": {
            "orgs_with_website": websites,
            "orgs_with_mission": missions,
            "orgs_with_donation_evidence": donation_candidates,
            "orgs_with_public_allowed_donation_evidence": donation_public_allowed,
            "missing_public_allowed_donation_estimate": max(total_active - donation_public_allowed, 0),
        },
        "volunteer_readiness": {
            "volunteer_events": volunteer_events,
            "active_volunteer_events": active_volunteer_events,
        },
        "vendor_market": {
            "vendors": vendor_count,
            "active_vendor_codes": active_vendor_codes,
            "top_states": top_states,
            "top_categories": top_categories,
            "top_markets": top_metros,
        },
    }

    (REPORTS / "growth-opportunity.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    md = f"""# Growth Opportunity Report

Generated: {report["generated_at"]}

## Nonprofit Claims

- Active deductible orgs: {total_active:,}
- Claim started orgs: {claim_started:,}
- Verified claimed orgs: {claimed:,}
- Unclaimed estimate: {max(total_active - claimed, 0):,}

## Donor Readiness

- Orgs with website: {websites:,}
- Orgs with mission: {missions:,}
- Orgs with donation evidence: {donation_candidates:,}
- Orgs with public-allowed donation evidence: {donation_public_allowed:,}
- Missing public-allowed donation path estimate: {max(total_active - donation_public_allowed, 0):,}

## Volunteer Readiness

- Volunteer events: {volunteer_events:,}
- Active volunteer events: {active_volunteer_events:,}

## Vendor Market

- Vendors: {vendor_count:,}
- Active vendor codes: {active_vendor_codes:,}

### Top States

"""
    for item in top_states[:10]:
        md += f"- {item['state']}: {item['orgs']:,}\n"

    md += "\n### Top Categories\n\n"
    for item in top_categories[:10]:
        md += f"- {item['category']}: {item['orgs']:,}\n"

    md += "\n### Top Markets\n\n"
    for item in top_metros[:10]:
        md += f"- {item['market']}: {item['orgs']:,}\n"

    md += """
## Interpretation

The largest immediate opportunity is nonprofit claim acquisition: almost all
active deductible pages are unclaimed. Search and AI visibility should drive
traffic to org pages, then convert nonprofit operators into claim/update flows.

The second opportunity is vendor supply. Vendor tables exist, but no vendors or
active discount codes are present yet. This supports a separate vendor outreach
track aimed at small businesses that serve nonprofits.
"""
    (REPORTS / "growth-opportunity.md").write_text(md, encoding="utf-8")
    print(f"Wrote {REPORTS / 'growth-opportunity.json'}")
    print(f"Wrote {REPORTS / 'growth-opportunity.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

