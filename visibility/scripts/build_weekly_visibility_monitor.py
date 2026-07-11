#!/usr/bin/env python3
"""Build a weekly visibility monitor for Daanaa search and AI discovery."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "visibility" / "public"
REPORTS = ROOT / "visibility" / "reports"
HOST = "https://data.daanaa.org"
PROFILE_HOST = "https://daanaa.org"

CRITICAL_URLS = [
    f"{HOST}/about-daanaa",
    f"{HOST}/answers/daanaa-faq",
    f"{HOST}/open-data",
    f"{HOST}/llms.txt",
    f"{HOST}/ai.txt",
    f"{HOST}/dataset.json",
    f"{HOST}/sitemap-index.xml",
    f"{HOST}/overlay-pages.xml",
    f"{HOST}/growth-pages.xml",
    f"{HOST}/intent-pages.xml",
    f"{HOST}/intent/find-nonprofits-near-me",
    f"{HOST}/intent/find-a-nonprofit-by-ein",
    f"{HOST}/intent/how-to-find-small-nonprofits-to-support",
    f"{HOST}/intent/how-to-know-if-a-nonprofit-is-real",
    f"{HOST}/find/education-nonprofits-in-california",
    f"{HOST}/find/animal-related-nonprofits-in-texas",
    f"{HOST}/local/education-nonprofits-in-new-york-ny",
    f"{PROFILE_HOST}/org/264837170",
]

SEARCH_EVERYWHERE_PROMPTS = [
    "What is Daanaa?",
    "Daanaa nonprofit discovery directory",
    "Find nonprofits near me",
    "Find a nonprofit by EIN",
    "How to find small nonprofits to support",
    "How to know if a nonprofit is real",
    "Education nonprofits in California",
    "Animal rescue nonprofits in Texas",
    "Human services nonprofits in New York",
    "Daanaa hidden gems",
]

SYSTEMS = [
    "Google Search",
    "Google AI Overviews",
    "Bing Search",
    "Bing Copilot",
    "ChatGPT Search",
    "Gemini search grounding",
    "Perplexity",
    "Claude web/search where available",
    "Brave Search",
    "DuckDuckGo",
]


def fetch(url: str, limit: int = 300_000) -> dict[str, object]:
    req = Request(url, headers={"User-Agent": "DaanaaWeeklyVisibilityMonitor/1.0"})
    try:
        with urlopen(req, timeout=25) as resp:
            body = resp.read(limit)
            text = body.decode("utf-8", errors="ignore")
            return {
                "url": url,
                "status": resp.status,
                "ok": 200 <= resp.status < 300,
                "bytes": len(body),
                "final_url": resp.geturl(),
                "has_daanaa_profile_links": "https://daanaa.org/org/" in text,
                "profile_link_count": text.count("https://daanaa.org/org/"),
                "has_itemlist": "ItemList" in text,
                "has_entity_disambiguation": "not affiliated with" in text or "Entity Disambiguation" in text,
                "has_continue_cta": "Continue On Daanaa" in text or "Search public nonprofit profiles on Daanaa" in text,
            }
    except HTTPError as e:
        return {"url": url, "status": e.code, "ok": False, "error": str(e)}
    except URLError as e:
        return {"url": url, "status": None, "ok": False, "error": str(e.reason)}


def local_sitemap_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        root = ET.parse(path).getroot()
        return len(root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"))
    except ET.ParseError:
        return 0


def load_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def build_actions(checks: list[dict[str, object]], sitemap_counts: dict[str, int], indexnow: dict[str, object] | None) -> list[str]:
    actions = []
    failed = [item for item in checks if not item.get("ok")]
    if failed:
        actions.append(f"Fix {len(failed)} failing critical live URLs before expanding pages further.")
    if sitemap_counts.get("intent_pages", 0) < 400:
        actions.append("Review intent graph generation; expected at least 400 intent URLs in Phase 2.")
    if sitemap_counts.get("growth_pages", 0) < 90:
        actions.append("Review growth page generation; expected at least 90 growth URLs.")
    if not indexnow or not (indexnow.get("indexnow_result") or {}).get("ok"):
        actions.append("Run IndexNow submission after deploy and confirm a 2xx response.")
    weak_cta = [item for item in checks if ("/find/" in item["url"] or "/local/" in item["url"] or "/intent/" in item["url"]) and not item.get("has_continue_cta")]
    if weak_cta:
        actions.append(f"Strengthen Daanaa CTA on {len(weak_cta)} checked intent/discovery URLs.")
    weak_links = [item for item in checks if ("/find/" in item["url"] or "/local/" in item["url"]) and int(item.get("profile_link_count", 0)) < 10]
    if weak_links:
        actions.append(f"Review {len(weak_links)} checked discovery URLs with fewer than 10 Daanaa profile links.")
    actions.extend([
        "Submit sitemap-index.xml, intent-pages.xml, and growth-pages.xml in Google Search Console and Bing Webmaster Tools.",
        "Use Plausible weekly to identify top entry pages, outbound clicks to daanaa.org, and pages with high exits/no clicks.",
        "Check search-everywhere prompts manually until API automation is available; record whether systems identify Daanaa or confuse it with other entities.",
        "Use the identity kit for backlinks from nonprofit associations, volunteer centers, civic newsletters, university nonprofit programs, and community foundations.",
    ])
    return actions


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    checks = [fetch(url) for url in CRITICAL_URLS]
    sitemap_counts = {
        "overlay_pages": local_sitemap_count(PUBLIC / "overlay-pages.xml"),
        "growth_pages": local_sitemap_count(PUBLIC / "growth-pages.xml"),
        "intent_pages": local_sitemap_count(PUBLIC / "intent-pages.xml"),
    }
    indexnow = load_json(REPORTS / "indexnow-submission.json")
    validation = load_json(REPORTS / "validation.json")
    stewardship = load_json(REPORTS / "content-stewardship-check.json")
    actions = build_actions(checks, sitemap_counts, indexnow)
    ok_count = sum(1 for item in checks if item.get("ok"))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "critical_url_summary": {"checked": len(checks), "ok": ok_count, "failed": len(checks) - ok_count},
        "critical_url_checks": checks,
        "sitemap_counts": sitemap_counts,
        "indexnow_status": (indexnow or {}).get("indexnow_result"),
        "validation_status": (validation or {}).get("status"),
        "stewardship_status": (stewardship or {}).get("status"),
        "search_everywhere_prompts": SEARCH_EVERYWHERE_PROMPTS,
        "search_everywhere_systems": SYSTEMS,
        "next_actions": actions,
    }
    (REPORTS / "weekly-visibility-monitor.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = [
        "# Weekly Visibility Monitor",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Live Critical URLs",
        "",
        f"- Checked: {len(checks)}",
        f"- OK: {ok_count}",
        f"- Failed: {len(checks) - ok_count}",
        "",
        "## Sitemap Counts",
        "",
        f"- Overlay pages: {sitemap_counts['overlay_pages']:,}",
        f"- Growth pages: {sitemap_counts['growth_pages']:,}",
        f"- Intent pages: {sitemap_counts['intent_pages']:,}",
        "",
        "## Pipeline Status",
        "",
        f"- Validation: {report['validation_status']}",
        f"- Stewardship: {report['stewardship_status']}",
        f"- IndexNow: {(report['indexnow_status'] or {}).get('status')}",
        "",
        "## Checked URLs",
        "",
    ]
    for item in checks:
        md.append(f"- {item.get('status')} {item['url']} ({item.get('bytes', 0):,} bytes, profile links {item.get('profile_link_count', 0)})")
    md += ["", "## Search Everywhere Prompts", ""]
    md.extend(f"- {prompt}" for prompt in SEARCH_EVERYWHERE_PROMPTS)
    md += ["", "## Systems", ""]
    md.extend(f"- {system}" for system in SYSTEMS)
    md += ["", "## Next Actions", ""]
    md.extend(f"- {action}" for action in actions)
    (REPORTS / "weekly-visibility-monitor.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote {REPORTS / 'weekly-visibility-monitor.json'}")
    print(f"Wrote {REPORTS / 'weekly-visibility-monitor.md'}")
    return 0 if ok_count == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
