#!/usr/bin/env python3
"""Build a repeatable improvement loop for Daanaa visibility."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "visibility" / "reports"
GROWTH = REPORTS / "growth-opportunity.json"
CONTENT = REPORTS / "content-targets.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(numerator: int | float, denominator: int | float) -> float:
    return 0.0 if not denominator else float(numerator) / float(denominator) * 100.0


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    growth = load(GROWTH)
    content = load(CONTENT)

    claims = growth["nonprofit_claims"]
    donor = growth["donor_readiness"]
    volunteer = growth["volunteer_readiness"]
    vendor = growth["vendor_market"]

    active_orgs = int(growth["active_deductible_orgs"])
    claim_started = int(claims["claim_started_orgs"])
    verified_claimed = int(claims["verified_claimed_orgs"])
    unclaimed_estimate = int(claims["unclaimed_estimate"])
    website_count = int(donor["orgs_with_website"])
    donation_evidence = int(donor["orgs_with_donation_evidence"])
    public_donation = int(donor["orgs_with_public_allowed_donation_evidence"])
    volunteer_events = int(volunteer["volunteer_events"])
    vendor_count = int(vendor["vendors"])
    active_vendor_codes = int(vendor["active_vendor_codes"])

    mission = "Make smaller nonprofits more visible so they can get funded and find volunteers."

    loop = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mission": mission,
        "principles": [
            "Start with public discovery: profiles, sitemaps, llms.txt, dataset metadata, and AI guidance.",
            "Convert discovery into claims: help nonprofit operators find and claim their pages.",
            "Convert claims into funding and volunteer readiness: donation and volunteer paths should be visible and clear.",
            "Grow supply: recruit nonprofit-friendly vendors, discount codes, and service partners.",
            "Measure and repeat: refresh reports, submissions, and content on a fixed cadence.",
        ],
        "current_state": {
            "active_deductible_orgs": active_orgs,
            "claim_started_orgs": claim_started,
            "verified_claimed_orgs": verified_claimed,
            "unclaimed_estimate": unclaimed_estimate,
            "orgs_with_website": website_count,
            "orgs_with_donation_evidence": donation_evidence,
            "orgs_with_public_allowed_donation_evidence": public_donation,
            "volunteer_events": volunteer_events,
            "vendors": vendor_count,
            "active_vendor_codes": active_vendor_codes,
            "claim_started_rate": round(pct(claim_started, active_orgs), 4),
            "verified_claim_rate": round(pct(verified_claimed, active_orgs), 4),
            "public_donation_rate": round(pct(public_donation, active_orgs), 4),
        },
        "priority_loops": [
            {
                "name": "Search And AI Discovery",
                "goal": "Keep the overlay crawlable and easy to understand for Google, Bing, and AI tools.",
                "artifacts": [
                    "sitemap-index.xml",
                    "robots.txt",
                    "llms.txt",
                    "ai.txt",
                    "dataset.json",
                    "open-data.html",
                ],
                "cadence": "Every pipeline run and after any content change.",
            },
            {
                "name": "Nonprofit Claim Conversion",
                "goal": "Turn visibility into claim starts for unclaimed nonprofit pages.",
                "artifacts": [
                    "claim-nonprofit-page",
                    "claim outreach email",
                    "content-targets report",
                ],
                "cadence": "Weekly review, with outreach updates as needed.",
            },
            {
                "name": "Donation And Volunteer Readiness",
                "goal": "Surface clear paths for donors and volunteers when public data supports them.",
                "artifacts": [
                    "nonprofit-data-sources",
                    "nonprofit-profile-guide",
                    "open-data.html",
                ],
                "cadence": "Weekly review, prioritizing lower-footprint nonprofits first.",
            },
            {
                "name": "Vendor Supply",
                "goal": "Recruit nonprofit-friendly vendors and discount-code partners.",
                "artifacts": [
                    "nonprofit-vendor-discounts",
                    "vendor recruitment email",
                    "vendor targets report",
                ],
                "cadence": "Biweekly review until vendor supply exists.",
            },
            {
                "name": "Measurement And Feedback",
                "goal": "Track search indexing, traffic, claims, and partner replies.",
                "artifacts": [
                    "search-submission report",
                    "indexnow-submission report",
                    "production-url-audit",
                    "content-targets report",
                ],
                "cadence": "Every pipeline run, plus monthly summary.",
            },
        ],
        "next_actions": [
            "Keep the overlay deployed and publicly reachable.",
            "Submit or monitor Google Search Console and Bing Webmaster coverage for data.daanaa.org.",
            "Use Plausible to watch pageviews, referrers, and entry pages on data.daanaa.org.",
            "Use the content-target report to build the next set of pages and outreach.",
            "Prioritize nonprofits with low public footprint, missing claim activity, or missing donation and volunteer paths.",
            "Re-run IndexNow whenever the overlay content changes.",
        ],
        "success_metrics": [
            "Indexed overlay pages in Google and Bing.",
            "More traffic from search to daanaa.org/org/{ein} pages.",
            "More claim starts and verified claims.",
            "More nonprofit pages with usable donation and volunteer paths.",
            "More partner replies from associations, foundations, and vendors.",
            "Plausible confirms that overlay and nonprofit pages are getting search-driven visits.",
        ],
        "target_pages": content["target_pages"],
    }

    (REPORTS / "improvement-loop.json").write_text(
        json.dumps(loop, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    md_lines = [
        "# Continuous Improvement Loop",
        "",
        f"Generated: {loop['generated_at']}",
        "",
        f"Mission: {mission}",
        "",
        "## Core Principles",
        "",
    ]
    md_lines.extend(f"- {item}" for item in loop["principles"])
    md_lines += [
        "",
        "## Current State",
        "",
        f"- Active deductible orgs: {active_orgs:,}",
        f"- Claim started orgs: {claim_started:,} ({pct(claim_started, active_orgs):.4f}%)",
        f"- Verified claimed orgs: {verified_claimed:,} ({pct(verified_claimed, active_orgs):.4f}%)",
        f"- Unclaimed estimate: {unclaimed_estimate:,}",
        f"- Orgs with website: {website_count:,}",
        f"- Orgs with donation evidence: {donation_evidence:,}",
        f"- Orgs with public-allowed donation evidence: {public_donation:,}",
        f"- Volunteer events: {volunteer_events:,}",
        f"- Vendors: {vendor_count:,}",
        f"- Active vendor codes: {active_vendor_codes:,}",
        "",
        "## Priority Loops",
        "",
    ]
    for item in loop["priority_loops"]:
        md_lines.extend([
            f"### {item['name']}",
            f"- Goal: {item['goal']}",
            f"- Cadence: {item['cadence']}",
            "- Artifacts:",
        ])
        md_lines.extend(f"  - {artifact}" for artifact in item["artifacts"])
        md_lines.append("")

    md_lines += [
        "## Next Actions",
        "",
    ]
    md_lines.extend(f"- {item}" for item in loop["next_actions"])
    md_lines += [
        "",
        "## Success Metrics",
        "",
    ]
    md_lines.extend(f"- {item}" for item in loop["success_metrics"])
    md_lines += [
        "",
        "## Mission Alignment Notes",
        "",
        "- Smaller nonprofits usually need visibility before they need growth tooling, so the loop prioritizes public discovery first.",
        "- Claim conversion comes next so nonprofits can add mission, donation, and volunteer context themselves.",
        "- Vendor onboarding is separate so service providers do not distort nonprofit rankings or trust signals.",
        "- Search and AI discovery are treated as distribution layers, not as product changes.",
    ]

    (REPORTS / "improvement-loop.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORTS / 'improvement-loop.json'}")
    print(f"Wrote {REPORTS / 'improvement-loop.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
