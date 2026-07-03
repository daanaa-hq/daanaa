"""
LinkedIn prospect search for Daanaa outreach.
Uses linkedin-api (github.com/tomquirk/linkedin-api) to find nonprofit leaders.

Usage:
  python3 linkedin_search.py --org "Food Bank of NYC" --role "Executive Director"
  python3 linkedin_search.py --keywords "nonprofit philanthropy civic tech" --limit 10
  python3 linkedin_search.py --funders                   # search known funder profiles
"""
import argparse
import json
import os
import sys
from pathlib import Path

_CREDS_FILE = Path(__file__).parent / ".session" / "linkedin_creds.json"

FUNDER_KEYWORDS = [
    "program officer philanthropy",
    "civic tech foundation",
    "DRK Foundation",
    "Trust for Civic Life",
    "Knight Foundation nonprofit",
]


def _get_client():
    from linkedin_api import Linkedin
    if not _CREDS_FILE.exists():
        print("No LinkedIn credentials found.")
        print(f"Create {_CREDS_FILE} with: {{\"username\": \"...\", \"pass\": \"...\"}}")
        sys.exit(1)
    creds = json.loads(_CREDS_FILE.read_text())
    return Linkedin(creds["username"], creds["pass"])


def search_person(org_name: str = None, role: str = None, keywords: str = None, limit: int = 5):
    client = _get_client()
    if keywords:
        results = client.search_people(keywords=keywords, limit=limit)
    else:
        kw = " ".join(filter(None, [org_name, role]))
        results = client.search_people(keywords=kw, limit=limit)

    prospects = []
    for r in results:
        name = r.get("name", "Unknown")
        headline = r.get("headline", "")
        profile_id = r.get("public_id", "")
        prospects.append({
            "name": name,
            "headline": headline,
            "url": f"https://linkedin.com/in/{profile_id}" if profile_id else "",
        })
    return prospects


def search_funders():
    client = _get_client()
    all_prospects = []
    for kw in FUNDER_KEYWORDS:
        results = client.search_people(keywords=kw, limit=3)
        for r in results:
            name = r.get("name", "Unknown")
            headline = r.get("headline", "")
            profile_id = r.get("public_id", "")
            all_prospects.append({
                "name": name,
                "headline": headline,
                "keyword": kw,
                "url": f"https://linkedin.com/in/{profile_id}" if profile_id else "",
            })
    return all_prospects


def main():
    parser = argparse.ArgumentParser(description="LinkedIn prospect search for Daanaa outreach")
    parser.add_argument("--org", help="Org name to search for")
    parser.add_argument("--role", help="Job title filter (e.g. 'Executive Director')")
    parser.add_argument("--keywords", help="Free-form keywords")
    parser.add_argument("--funders", action="store_true", help="Search known funder profile keywords")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--save", help="Save results to this JSON file")
    args = parser.parse_args()

    if args.funders:
        results = search_funders()
    else:
        results = search_person(args.org, args.role, args.keywords, args.limit)

    print(json.dumps(results, indent=2))

    if args.save:
        Path(args.save).write_text(json.dumps(results, indent=2))
        print(f"\nSaved to {args.save}")


if __name__ == "__main__":
    main()
