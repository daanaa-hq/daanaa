#!/usr/bin/env python3
import json
from pathlib import Path

BASE = Path.home() / "meritgiving"
CACHE_DIR = BASE / "data/propublica_cache"
XML_FILE = BASE / "data/xml_extracted.json"

with open(XML_FILE) as f:
    existing = set(json.load(f).keys())

missing = []
for f in CACHE_DIR.glob("*.json"):
    try:
        with open(f) as fh:
            d = json.load(fh)
        ein = str(d.get('organization', {}).get('ein', '')).strip()
        if ein and ein not in existing:
            missing.append(ein)
    except:
        pass

print(f"Orgs needing 990 extraction: {len(missing)}")
print("This requires ProPublica API calls (rate limit ~1000/day) or IRS bulk download.")
print(f"Sample missing: {missing[:10]}")

with open(BASE / "data/missing_990_eins.json", "w") as f:
    json.dump(missing, f, indent=2)

print(f"Saved missing list to data/missing_990_eins.json")
