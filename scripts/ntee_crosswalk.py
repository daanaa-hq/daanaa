#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

BASE = Path.home() / "meritgiving"
CACHE_DIR = BASE / "data/propublica_cache"

print("Loading ProPublica cache for NTEE audit...")
fixed = 0
still_missing = 0
ntee_fixes = {}

for f in CACHE_DIR.glob("*.json"):
    try:
        with open(f) as fh:
            d = json.load(fh)
        org = d.get('organization', {})
        ein = str(org.get('ein', '')).strip()
        ntee = str(org.get('ntee_code', '')).strip().upper()
        
        if not ntee or ntee in ['NON', 'NONE', '']:
            class_codes = org.get('classification_codes', [])
            if class_codes:
                ntee = str(class_codes[0]).upper()[:3]
                if ntee and ntee not in ['NON', 'NONE', '']:
                    fixed += 1
                    ntee_fixes[ein] = ntee
                    continue
            still_missing += 1
    except:
        pass

print(f"Fixed via classification_codes: {fixed}")
print(f"Still missing NTEE: {still_missing}")

with open(BASE / "data/ntee_fixes.json", "w") as f:
    json.dump(ntee_fixes, f, indent=2)

print(f"Saved {len(ntee_fixes)} NTEE fixes to data/ntee_fixes.json")
print("Next: Apply fixes to xml_extracted.json and re-score")
