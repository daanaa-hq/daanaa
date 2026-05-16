#!/usr/bin/env python3
import json, re
from pathlib import Path
from collections import defaultdict

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"
CAT_DIR = DATA / "categories"

def fix_categories():
    print("="*60)
    print("FIX: Category file cleanup")
    print("="*60)
    fixed_count = 0
    for cat_file in CAT_DIR.glob("*.json"):
        try:
            with open(cat_file, 'r') as f:
                data = json.load(f)
            orgs = data if isinstance(data, list) else data.get('organizations', [])
            if not isinstance(orgs, list):
                continue
            seen = set()
            deduped = []
            for org in orgs:
                ein = str(org.get('ein', '')).strip()
                if ein and ein in seen:
                    continue
                if ein:
                    seen.add(ein)
                deduped.append(org)
            modified = False
            for org in deduped:
                for field in ['revenue','total_revenue','expenses','total_expenses','assets']:
                    val = org.get(field)
                    if val is not None:
                        try:
                            org[field] = f"${float(val):,.0f}"
                            modified = True
                        except:
                            pass
                city = org.get('city','')
                state = org.get('state','')
                if not city and not state:
                    org['_display_location'] = 'Location on file'
                    modified = True
                else:
                    parts = [p for p in [city, state] if p]
                    org['_display_location'] = ', '.join(parts)
            if len(deduped) != len(orgs) or modified:
                with open(cat_file, 'w') as f:
                    json.dump(deduped, f, indent=2)
                print(f"  {cat_file.name}: {len(orgs)} -> {len(deduped)} orgs")
                fixed_count += 1
        except Exception as e:
            print(f"  Error: {cat_file.name}: {e}")
    print(f"Fixed {fixed_count} category files")

if __name__ == "__main__":
    fix_categories()
    print("Done.")
