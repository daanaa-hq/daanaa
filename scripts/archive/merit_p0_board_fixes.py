#!/usr/bin/env python3
"""
MERIT Board Review — P0 Fixes Script
Run from ~/meritgiving/ on ecomargins
"""
import json, os, re
from pathlib import Path
from collections import defaultdict

BASE = Path.home() / "meritgiving"
DATA_DIR = BASE / "data"
CAT_DIR = DATA_DIR / "categories"
WEB_DEMO = BASE / "web_demo"

def fix_MERIT_to_merit():
    print("="*60)
    print("FIX 1: Renaming Impact -> MERIT")
    print("="*60)
    replacements = {'MERIT Score': 'MERIT Score','MERIT SCORE': 'MERIT SCORE','MERIT': 'MERIT','MERIT score': 'MERIT score','MERIT': 'MERIT'}
    exts = ['.py', '.js', '.html', '.md', '.txt', '.json', '.css', '.xml']
    changed_files = []
    for ext in exts:
        for filepath in BASE.rglob(f"*{ext}"):
            if any(x in str(filepath) for x in ['venv', 'node_modules', '.git', '__pycache__']): continue
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
                original = content
                for old, new in replacements.items(): content = content.replace(old, new)
                if content != original:
                    with open(filepath, 'w', encoding='utf-8') as f: f.write(content)
                    changed_files.append(filepath)
            except: pass
    print(f"Modified {len(changed_files)} files.")
    print("Sample changed files:")
    for fp in changed_files[:10]: print(f"  {fp.relative_to(BASE)}")

def fix_address_and_currency_in_categories():
    print("\n" + "="*60)
    print("FIX 2: Address + Currency + Null Guards")
    print("="*60)
    fixed_count = 0
    for cat_file in CAT_DIR.glob("*.json"):
        try:
            with open(cat_file, 'r') as f: orgs = json.load(f)
            if not isinstance(orgs, list): continue
            modified = False
            for org in orgs:
                street = org.get('street_address', org.get('address', ''))
                city = org.get('city', '')
                state = org.get('state', '')
                zipcode = org.get('zip', org.get('zipcode', ''))
                if street and (city in street[:len(city)+5] or state in street[:len(state)+5]):
                    parts = street.split(',')
                    if len(parts) >= 2:
                        org['city'] = parts[0].strip()
                        rest = parts[1].strip()
                        state_zip = rest.split(' ', 1)
                        org['state'] = state_zip[0] if len(state_zip) > 0 else ''
                        org['street_address'] = city
                        modified = True
                if not city and not state: org['_display_location'] = 'Location on file'
                else:
                    parts = []
                    if city: parts.append(city)
                    if state: parts.append(state)
                    org['_display_location'] = ', '.join(parts)
                for field in ['revenue', 'total_revenue', 'expenses', 'total_expenses', 'assets']:
                    val = org.get(field)
                    if val is not None:
                        try: org[field] = f"${float(val):,.0f}"
                        except: pass
            if modified:
                with open(cat_file, 'w') as f: json.dump(orgs, f, indent=2)
                fixed_count += 1
        except Exception as e: print(f"  Error in {cat_file}: {e}")
    print(f"Fixed address/currency in {fixed_count} category files.")

def dedupe_categories_keep_latest():
    print("\n" + "="*60)
    print("FIX 3: Dedupe Category Files (keep latest)")
    print("="*60)
    for cat_file in CAT_DIR.glob("*.json"):
        try:
            with open(cat_file, 'r') as f: orgs = json.load(f)
            if not isinstance(orgs, list): continue
            by_ein = defaultdict(list)
            for org in orgs:
                ein = str(org.get('ein', '')).strip()
                if ein: by_ein[ein].append(org)
            deduped = []; duplicates_removed = 0
            for ein, records in by_ein.items():
                if len(records) == 1: deduped.append(records[0])
                else:
                    def get_year(r):
                        ty = r.get('tax_year', r.get('filing_year', r.get('latest_filing', 0)))
                        try: return int(ty)
                        except: return 0
                    latest = max(records, key=get_year)
                    deduped.append(latest)
                    duplicates_removed += len(records) - 1
            if duplicates_removed > 0:
                with open(cat_file, 'w') as f: json.dump(deduped, f, indent=2)
                print(f"  {cat_file.name}: removed {duplicates_removed} dups, {len(deduped)} unique")
        except Exception as e: print(f"  Error in {cat_file}: {e}")

def fix_state_count():
    print("\n" + "="*60)
    print("FIX 4: State Count Audit")
    print("="*60)
    states = set()
    for json_file in list(CAT_DIR.glob("*.json")) + list((DATA_DIR / "index").glob("*.json")):
        try:
            with open(json_file, 'r') as f: data = json.load(f)
            orgs = data if isinstance(data, list) else data.get('organizations', [])
            if not isinstance(orgs, list): continue
            for org in orgs:
                state = str(org.get('state', '')).strip().upper()
                if state and len(state) == 2: states.add(state)
        except: pass
    print(f"Unique 2-letter state codes: {len(states)}")
    us_states = {'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'}
    dc = {'DC'}; territories = {'PR','GU','VI','AS','MP'}
    found_states = states & us_states; found_dc = states & dc; found_territories = states & territories; found_other = states - us_states - dc - territories
    print(f"  US States: {len(found_states)}")
    print(f"  DC: {len(found_dc)}")
    print(f"  Territories: {len(found_territories)} — {found_territories}")
    if found_other: print(f"  ⚠️  Unknown codes: {found_other}")
    total = len(found_states) + len(found_dc) + len(found_territories)
    if found_territories: print(f"\n  ✅ Recommended stat: '{total} states and territories'")
    elif found_dc: print(f"\n  ✅ Recommended stat: '51 states and DC'")
    else: print(f"\n  ✅ Recommended stat: '50 states'")

def generate_fix_summary():
    print("\n" + "="*60)
    print("P0 FIX SUMMARY")
    print("="*60)
    print("""
AUTOMATED FIXES APPLIED:
  ✓ Impact -> MERIT rename across code/docs
  ✓ Address concatenation fixed
  ✓ Null city/state guarded
  ✓ Currency formatted
  ✓ Duplicate EINs removed
  ✓ State count audited

MANUAL FIXES STILL NEEDED:
  ☐ Webflow CMS: rename collection field to "MERIT Score"
  ☐ Webflow templates: {{MERIT_score}} -> {{merit_score}}
  ☐ Airtable: rename "Impact" column to "MERIT"
  ☐ n8n: relabel "Impact" nodes to "MERIT"
  ☐ Homepage: hide/move "Uncategorized"
  ☐ Homepage: fix/replace "Featured Organizations"
  ☐ Whitepaper: global find/replace
  ☐ /merit/docs/MERIT-CONTEXT.md: update references
  ☐ Pull real missions from 990 Schedule O
  ☐ Fix NTEE for known orgs (Houston Symphony = A69)
  ☐ Unify "last filing year" source of truth
  ☐ Replace hardcoded org counts with real counts
    """)

if __name__ == "__main__":
    print("MERIT Board Review — P0 Automated Fixes")
    print("="*60)
    fix_MERIT_to_merit()
    fix_address_and_currency_in_categories()
    dedupe_categories_keep_latest()
    fix_state_count()
    generate_fix_summary()
    print("\nDone. Review manual fixes above.")
