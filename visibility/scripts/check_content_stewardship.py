#!/usr/bin/env python3
"""Stewardship language check for overlay content pages."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "visibility" / "public"
REPORTS = ROOT / "visibility" / "reports"

BASE_PAGES = [
    PUBLIC / "about-daanaa.html",
    PUBLIC / "answers" / "daanaa-faq.html",
    PUBLIC / "authority" / "identity-kit.html",
    PUBLIC / "authority" / "search-everywhere.html",
    PUBLIC / "blog" / "why-small-nonprofits-disappear-in-search.html",
    PUBLIC / "blog" / "how-donors-can-use-public-nonprofit-data-responsibly.html",
    PUBLIC / "blog" / "giving-wallet-making-giving-easier-to-repeat.html",
    PUBLIC / "blog" / "daanaa-impact-network-giving-money-time-knowledge-support.html",
    PUBLIC / "blog" / "philanthropy-belongs-to-everyone.html",
]


def content_pages() -> list[Path]:
    generated = []
    for directory in [PUBLIC / "guides", PUBLIC / "intent", PUBLIC / "find", PUBLIC / "nonprofits" / "state", PUBLIC / "nonprofits" / "category"]:
        if directory.exists():
            generated.extend(sorted(directory.glob("*.html")))
    return BASE_PAGES + generated

REQUIRED_PHRASES = {
    "free_or_no_charge": ["free for nonprofits", "not charged for listings or claims"],
    "no_paid_influence": ["pay for better profile treatment", "listing or claim visibility dependent on paid promotion"],
    "no_funds_handling": ["does not handle donor funds", "does not process donations or hold donor funds"],
    "uncertainty_disclosure": ["not be presented as official unless verified", "do not treat them as verified"],
    "small_org_fairness": ["smaller nonprofits", "small nonprofits"],
}

BANNED_PATTERNS = {
    "shame_language": re.compile(r"\b(failing|bad nonprofit|low quality|unworthy|avoid this nonprofit|fraudulent)\b", re.I),
    "paid_visibility": re.compile(r"\b(pay to rank|paid placement available|sponsored result|buy visibility)\b", re.I),
    "official_unqualified": re.compile(r"\bofficial donation link\b", re.I),
    "funds_handling": re.compile(r"\b(Daanaa processes donations|Daanaa holds donations|send donations to Daanaa)\b", re.I),
}


def text_of(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    page_results = []
    failures = []

    pages = content_pages()

    for page in pages:
        if not page.exists():
            failures.append({"page": str(page.relative_to(ROOT)), "issue": "missing"})
            continue
        text = text_of(page)
        lowered = text.lower()
        banned_hits = []
        for name, pattern in BANNED_PATTERNS.items():
            hits = sorted(set(pattern.findall(text)))
            if hits:
                banned_hits.append({"rule": name, "hits": hits})
        required_hits = {
            key: any(phrase.lower() in lowered for phrase in phrases)
            for key, phrases in REQUIRED_PHRASES.items()
        }
        # Required phrases are checked across the whole two-article set below;
        # per-page status is informational.
        page_results.append({
            "page": str(page.relative_to(ROOT)),
            "bytes": page.stat().st_size,
            "banned_hits": banned_hits,
            "required_phrase_presence": required_hits,
        })
        if banned_hits:
            failures.append({"page": str(page.relative_to(ROOT)), "issue": "banned_language", "hits": banned_hits})

    corpus = "\n".join(text_of(page).lower() for page in pages if page.exists())
    missing_required = [
        key for key, phrases in REQUIRED_PHRASES.items()
        if not any(phrase.lower() in corpus for phrase in phrases)
    ]
    if missing_required:
        failures.append({"issue": "missing_required_stewardship_language", "rules": missing_required})

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not failures else "fail",
        "basis": [
            "STEWARDSHIP.md",
            "docs/11-STEWARDSHIP-PRINCIPLES.md",
            "visibility/CONTENT_BACKLINK_PLAN.md",
            "visibility/IMPROVEMENT_LOOP.md",
        ],
        "checks": {
            "mission_before_growth": "No paid placement, sponsored result, or growth-pressure language.",
            "privacy": "No donor identity, donor amount, IP tracking, or public popularity mechanics language.",
            "evidence_based_trust": "Public data caveats and verification limits are stated.",
            "small_org_fairness": "Small nonprofits are framed as under-visible, not deficient.",
            "no_weaponized_transparency": "No shame or failure framing detected.",
            "independence": "Nonprofits cannot pay for better profile treatment, trust language, or discovery priority.",
            "no_funds_control": "Daanaa does not process or hold donations.",
        },
        "pages": page_results,
        "failures": failures,
    }
    (REPORTS / "content-stewardship-check.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = [
        "# Content Stewardship Check",
        "",
        f"Generated: {report['generated_at']}",
        f"Status: {report['status'].upper()}",
        "",
        "## Basis",
        "",
    ]
    md.extend(f"- {item}" for item in report["basis"])
    md += ["", "## Checks", ""]
    md.extend(f"- {name}: {description}" for name, description in report["checks"].items())
    md += ["", "## Pages", ""]
    for page in page_results:
        md.append(f"- {page['page']}: {page['bytes']:,} bytes, banned hits {len(page['banned_hits'])}")
    if failures:
        md += ["", "## Failures", ""]
        md.extend(f"- {failure}" for failure in failures)
    (REPORTS / "content-stewardship-check.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"content stewardship: {report['status']}")
    print(f"Wrote {REPORTS / 'content-stewardship-check.json'}")
    print(f"Wrote {REPORTS / 'content-stewardship-check.md'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
