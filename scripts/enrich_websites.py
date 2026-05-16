#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path.home() / "meritgiving"
PROPUBLICA_DIR = BASE_DIR / "data" / "propublica_cache"
OUTPUT_DIR = BASE_DIR / "data"

def main():
    print("MERIT Website URL Extractor")
    print("=" * 50)

    if not PROPUBLICA_DIR.exists():
        print(f"ERROR: Directory not found: {PROPUBLICA_DIR}")
        return

    files = list(PROPUBLICA_DIR.glob("*.json"))
    print(f"Found {len(files):,} ProPublica cache files")

    stats = {"total": len(files), "with_website": 0, "with_phone": 0,
             "with_address": 0, "with_careofname": 0, "with_mission": 0,
             "with_filings": 0, "errors": 0, "website_hosts": Counter()}

    website_urls = {}
    phone_numbers = {}
    addresses = {}
    careof_names = {}
    enrichment_log = []

    for i, filepath in enumerate(files):
        if i % 1000 == 0 and i > 0:
            print(f"  Processed {i:,}/{len(files):,}...")

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
        except Exception:
            stats["errors"] += 1
            continue

        ein = filepath.stem
        org = data.get("organization", {}) if "organization" in data else data
        filings = data.get("filings_with_data", []) if isinstance(data, dict) else []

        record = {"ein": ein}

        # Website URL
        website = None
        for field in ["website", "url", "web_url", "homepage", "site"]:
            val = org.get(field)
            if val and isinstance(val, str) and val.strip():
                website = val.strip()
                break
        if website:
            record["website"] = website
            website_urls[ein] = website
            stats["with_website"] += 1
            wlower = website.lower()
            if ".org" in wlower: stats["website_hosts"][".org"] += 1
            elif ".com" in wlower: stats["website_hosts"][".com"] += 1
            elif ".edu" in wlower: stats["website_hosts"][".edu"] += 1
            elif ".net" in wlower: stats["website_hosts"][".net"] += 1
            else: stats["website_hosts"]["other"] += 1

        # Phone
        phone = None
        for field in ["phone", "telephone", "contact_number"]:
            val = org.get(field)
            if val and isinstance(val, str) and val.strip():
                phone = val.strip()
                break
        if phone:
            record["phone"] = phone
            phone_numbers[ein] = phone
            stats["with_phone"] += 1

        # Address
        addr_parts = []
        for field in ["address", "street", "city", "state", "zip"]:
            val = org.get(field)
            if val and isinstance(val, str) and val.strip():
                addr_parts.append(val.strip())
        if addr_parts:
            record["address"] = ", ".join(addr_parts)
            addresses[ein] = record["address"]
            stats["with_address"] += 1

        # Care-of name (DBA)
        careof = org.get("careofname")
        if careof and isinstance(careof, str) and careof.strip():
            record["careofname"] = careof.strip()
            careof_names[ein] = careof.strip()
            stats["with_careofname"] += 1

        # Mission
        if org.get("mission") and isinstance(org["mission"], str) and org["mission"].strip():
            stats["with_mission"] += 1

        # Filings
        if filings:
            stats["with_filings"] += 1
            record["filing_count"] = len(filings)

        enrichment_log.append(record)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_DIR / "website_urls.json", "w") as f:
        json.dump(website_urls, f, indent=2)

    with open(OUTPUT_DIR / "phone_numbers.json", "w") as f:
        json.dump(phone_numbers, f, indent=2)

    with open(OUTPUT_DIR / "addresses.json", "w") as f:
        json.dump(addresses, f, indent=2)

    with open(OUTPUT_DIR / "careof_names.json", "w") as f:
        json.dump(careof_names, f, indent=2)

    with open(OUTPUT_DIR / "enrichment_full.json", "w") as f:
        json.dump(enrichment_log, f, indent=2)

    def pct(key):
        return f"{stats[key] / stats['total'] * 100:.1f}%" if stats['total'] else "N/A"

    print(f"\nRESULTS")
    print(f"  Total orgs scanned:        {stats['total']:,}")
    print(f"  With website URL:          {stats['with_website']:,} ({pct('with_website')})")
    print(f"  With phone number:         {stats['with_phone']:,} ({pct('with_phone')})")
    print(f"  With full address:         {stats['with_address']:,} ({pct('with_address')})")
    print(f"  With DBA/careofname:       {stats['with_careofname']:,} ({pct('with_careofname')})")
    print(f"  With mission statement:    {stats['with_mission']:,} ({pct('with_mission')})")
    print(f"  With filing history:       {stats['with_filings']:,} ({pct('with_filings')})")
    print(f"  Parse errors:              {stats['errors']}")
    print(f"\n  Website TLD breakdown:")
    for tld, count in stats["website_hosts"].most_common():
        print(f"    {tld}: {count:,}")
    print(f"\n  Sample websites:")
    for ein, url in list(website_urls.items())[:5]:
        print(f"    {ein}: {url}")
    print(f"\nSaved {len(website_urls):,} website URLs to data/website_urls.json")

if __name__ == "__main__":
    main()
