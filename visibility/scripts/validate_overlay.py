#!/usr/bin/env python3
"""Validate the generated visibility overlay without touching production."""

from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "visibility" / "public"
REPORTS = ROOT / "visibility" / "reports"
ORG_CSV = PUBLIC / "data" / "orgs.csv"
SITEMAP_INDEX = PUBLIC / "sitemap-index.xml"
SITEMAPS = PUBLIC / "sitemaps"
BASE_PROFILE = "https://daanaa.org/org/"
EIN_RE = re.compile(r"^\d{9}$")


def fail(message: str) -> None:
    raise SystemExit(message)


def validate_csv() -> dict[str, object]:
    if not ORG_CSV.exists():
        fail(f"Missing {ORG_CSV}")

    required = [
        "ein",
        "name",
        "city",
        "state",
        "category_letter",
        "category_name",
        "profile_url",
    ]
    counts = Counter()
    seen: set[str] = set()
    samples: list[dict[str, str]] = []

    with ORG_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != required:
            fail(f"Unexpected CSV headers: {reader.fieldnames}")
        for row in reader:
            counts["rows"] += 1
            ein = row["ein"]
            if not EIN_RE.match(ein):
                counts["bad_ein"] += 1
            if ein in seen:
                counts["duplicate_ein"] += 1
            seen.add(ein)
            if not row["name"]:
                counts["blank_name"] += 1
            if not row["city"]:
                counts["blank_city"] += 1
            if not row["state"]:
                counts["blank_state"] += 1
            if not row["category_letter"] or not row["category_name"]:
                counts["blank_category"] += 1
            expected_url = f"{BASE_PROFILE}{ein}"
            if row["profile_url"] != expected_url:
                counts["bad_profile_url"] += 1
            if len(samples) < 5:
                samples.append(dict(row))

    return {
        "rows": counts["rows"],
        "unique_eins": len(seen),
        "bad_ein": counts["bad_ein"],
        "duplicate_ein": counts["duplicate_ein"],
        "blank_name": counts["blank_name"],
        "blank_city": counts["blank_city"],
        "blank_state": counts["blank_state"],
        "blank_category": counts["blank_category"],
        "bad_profile_url": counts["bad_profile_url"],
        "samples": samples,
    }


def validate_sitemaps(expected_urls: int) -> dict[str, object]:
    if not SITEMAP_INDEX.exists():
        fail(f"Missing {SITEMAP_INDEX}")
    if not SITEMAPS.exists():
        fail(f"Missing {SITEMAPS}")

    ET.parse(SITEMAP_INDEX)
    files = sorted(SITEMAPS.glob("*.xml"))
    total_urls = 0
    max_urls_per_file = 0
    for path in files:
        tree = ET.parse(path)
        root = tree.getroot()
        urls = root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")
        total_urls += len(urls)
        max_urls_per_file = max(max_urls_per_file, len(urls))
        if len(urls) > 50_000:
            fail(f"Sitemap exceeds 50,000 URL limit: {path}")

    if total_urls != expected_urls:
        fail(f"Sitemap URL count {total_urls} != CSV rows {expected_urls}")

    return {
        "sitemap_files": len(files),
        "sitemap_urls": total_urls,
        "max_urls_per_file": max_urls_per_file,
    }


def validate_static_files() -> dict[str, bool]:
    paths = {
        "llms_txt": PUBLIC / "llms.txt",
        "about_daanaa_html": PUBLIC / "about-daanaa.html",
        "answers_daanaa_faq": PUBLIC / "answers" / "daanaa-faq.html",
        "authority_identity_kit": PUBLIC / "authority" / "identity-kit.html",
        "authority_search_everywhere": PUBLIC / "authority" / "search-everywhere.html",
        "intent_index": PUBLIC / "intent" / "index.html",
        "find_index": PUBLIC / "find" / "index.html",
        "intent_pages_sitemap": PUBLIC / "intent-pages.xml",
        "open_data_html": PUBLIC / "open-data.html",
        "robots_txt": PUBLIC / "robots.txt",
        "dataset_json": PUBLIC / "dataset.json",
        "manifest_json": PUBLIC / "visibility-manifest.json",
        "claim_nonprofit_page": PUBLIC / "claim-nonprofit-page.html",
        "vendor_discounts_page": PUBLIC / "nonprofit-vendor-discounts.html",
        "overlay_pages_sitemap": PUBLIC / "overlay-pages.xml",
        "growth_pages_sitemap": PUBLIC / "growth-pages.xml",
        "growth_pages_manifest": PUBLIC / "growth-pages-manifest.json",
        "state_directory_index": PUBLIC / "nonprofits" / "state" / "index.html",
        "category_directory_index": PUBLIC / "nonprofits" / "category" / "index.html",
        "giving_guides_index": PUBLIC / "guides" / "index.html",
        "blog_small_nonprofits": PUBLIC / "blog" / "why-small-nonprofits-disappear-in-search.html",
        "blog_donor_data": PUBLIC / "blog" / "how-donors-can-use-public-nonprofit-data-responsibly.html",
        "blog_giving_wallet": PUBLIC / "blog" / "giving-wallet-making-giving-easier-to-repeat.html",
        "blog_impact_network": PUBLIC / "blog" / "daanaa-impact-network-giving-money-time-knowledge-support.html",
        "blog_philanthropy_everyone": PUBLIC / "blog" / "philanthropy-belongs-to-everyone.html",
    }
    status = {name: path.exists() and path.stat().st_size > 0 for name, path in paths.items()}
    missing = [name for name, ok in status.items() if not ok]
    if missing:
        fail(f"Missing or empty files: {', '.join(missing)}")
    json.loads(paths["dataset_json"].read_text(encoding="utf-8"))
    json.loads(paths["manifest_json"].read_text(encoding="utf-8"))
    json.loads(paths["growth_pages_manifest"].read_text(encoding="utf-8"))
    return status


def write_reports(report: dict[str, object]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "validation.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    csv_report = report["csv"]
    sitemap_report = report["sitemaps"]
    text = f"""# Visibility Overlay Coverage

Generated: {report["generated_at"]}

## CSV

- Rows: {csv_report["rows"]:,}
- Unique EINs: {csv_report["unique_eins"]:,}
- Bad EINs: {csv_report["bad_ein"]:,}
- Duplicate EINs: {csv_report["duplicate_ein"]:,}
- Blank names: {csv_report["blank_name"]:,}
- Blank cities: {csv_report["blank_city"]:,}
- Blank states: {csv_report["blank_state"]:,}
- Blank categories: {csv_report["blank_category"]:,}
- Bad profile URLs: {csv_report["bad_profile_url"]:,}

## Sitemaps

- Files: {sitemap_report["sitemap_files"]:,}
- URLs: {sitemap_report["sitemap_urls"]:,}
- Max URLs in one file: {sitemap_report["max_urls_per_file"]:,}

## Static Files

- `llms.txt`: present
- `about-daanaa.html`: present
- `answers/daanaa-faq.html`: present
- `authority/identity-kit.html`: present
- `authority/search-everywhere.html`: present
- `intent/index.html`: present
- `find/index.html`: present
- `intent-pages.xml`: present
- `open-data.html`: present
- `robots.txt`: present
- `dataset.json`: present
- `visibility-manifest.json`: present
- `claim-nonprofit-page.html`: present
- `nonprofit-vendor-discounts.html`: present
- `overlay-pages.xml`: present
- `growth-pages.xml`: present
- `growth-pages-manifest.json`: present
- `nonprofits/state/index.html`: present
- `nonprofits/category/index.html`: present
- `guides/index.html`: present
- `blog/why-small-nonprofits-disappear-in-search.html`: present
- `blog/how-donors-can-use-public-nonprofit-data-responsibly.html`: present
- `blog/giving-wallet-making-giving-easier-to-repeat.html`: present
- `blog/daanaa-impact-network-giving-money-time-knowledge-support.html`: present
- `blog/philanthropy-belongs-to-everyone.html`: present
"""
    (REPORTS / "coverage.md").write_text(text, encoding="utf-8")


def main() -> int:
    csv_report = validate_csv()
    sitemap_report = validate_sitemaps(int(csv_report["rows"]))
    static_report = validate_static_files()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "csv": csv_report,
        "sitemaps": sitemap_report,
        "static_files": static_report,
        "status": "pass",
    }
    write_reports(report)
    print(f"Overlay validation passed: {csv_report['rows']:,} rows, {sitemap_report['sitemap_files']} sitemap files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
