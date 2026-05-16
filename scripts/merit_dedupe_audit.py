#!/usr/bin/env python3
"""
MERIT Dedupe & Data Quality Audit
Run on your ecomargins server from ~/meritgiving/
Usage: python3 scripts/merit_dedupe_audit.py
"""
import json, os, glob
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path.home() / "meritgiving"
DATA_DIR = BASE / "data"
CACHE_DIR = DATA_DIR / "propublica_cache"
CAT_DIR = DATA_DIR / "categories"
INDEX_DIR = DATA_DIR / "index"

def audit_propublica_cache():
    print("\n" + "="*60)
    print("AUDIT 1: ProPublica Cache Files")
    print("="*60)
    files = list(CACHE_DIR.glob("*.json"))
    print(f"Total cache files: {len(files)}")
    ein_counts = Counter()
    org_names = {}
    filing_years = defaultdict(list)
    missing_mission = 0
    missing_ntee = 0
    ntee_codes = Counter()
    for f in files[:5000]:
        try:
            with open(f, 'r') as fh:
                data = json.load(fh)
            orgs = data if isinstance(data, list) else [data]
            for org in orgs:
                ein = str(org.get('ein', org.get('organization', {}).get('ein', ''))).strip()
                if not ein: continue
                ein_counts[ein] += 1
                name = org.get('name', org.get('organization', {}).get('name', 'UNKNOWN'))
                org_names[ein] = name
                tax_period = org.get('tax_period', org.get('filings_with_data', [{}])[0].get('tax_period', ''))
                if tax_period: filing_years[ein].append(tax_period)
                mission = org.get('mission', org.get('organization', {}).get('mission', ''))
                if not mission or mission.strip() == '': missing_mission += 1
                ntee = org.get('ntee_code', org.get('organization', {}).get('ntee_code', ''))
                if not ntee: ntee = org.get('ntee_classification', '')
                if not ntee: missing_ntee += 1
                else: ntee_codes[ntee[:3] if len(ntee) >= 3 else ntee] += 1
        except: pass
    duplicates = {ein: count for ein, count in ein_counts.items() if count > 1}
    print(f"\nUnique EINs: {len(ein_counts)}")
    print(f"Duplicate EINs: {len(duplicates)}")
    if duplicates:
        print("\nTop 10 most duplicated EINs:")
        for ein, count in Counter(duplicates).most_common(10):
            print(f"  {ein}: {count} records | {org_names.get(ein, 'UNKNOWN')}")
    contradictions = 0
    for ein, years in filing_years.items():
        if len(years) > 1:
            year_nums = [int(str(y)[:4]) for y in years if str(y).isdigit() or len(str(y)) >= 4]
            if year_nums and max(year_nums) - min(year_nums) > 5: contradictions += 1
    print(f"\nEINs with >5 year filing span contradictions: {contradictions}")
    print(f"Orgs missing mission: {missing_mission}")
    print(f"Orgs missing NTEE: {missing_ntee}")
    print(f"\nTop NTEE codes:")
    for code, count in ntee_codes.most_common(10): print(f"  {code}: {count}")

def audit_category_files():
    print("\n" + "="*60)
    print("AUDIT 2: Category Files")
    print("="*60)
    cat_files = list(CAT_DIR.glob("*.json"))
    print(f"Category files: {len(cat_files)}")
    for cat_file in cat_files:
        try:
            with open(cat_file, 'r') as f: orgs = json.load(f)
            if not isinstance(orgs, list): continue
            cat_name = cat_file.stem
            ein_counts = Counter()
            empty_city_state = 0
            broken_address = 0
            raw_float_revenue = 0
            unclassified_ntee = 0
            for org in orgs:
                ein = str(org.get('ein', '')).strip()
                if ein: ein_counts[ein] += 1
                city = org.get('city', '')
                state = org.get('state', '')
                if not city and not state: empty_city_state += 1
                street = org.get('street_address', org.get('address', ''))
                if street and (city in street or state in street):
                    if street.startswith(city) or street.startswith(state): broken_address += 1
                revenue = org.get('revenue', org.get('total_revenue', ''))
                if isinstance(revenue, float) or (isinstance(revenue, str) and '.0' in revenue and '$' not in revenue): raw_float_revenue += 1
                ntee = org.get('ntee', org.get('ntee_code', ''))
                if not ntee or ntee.lower() in ['unclassified', 'none', '']: unclassified_ntee += 1
            duplicates = sum(1 for c in ein_counts.values() if c > 1)
            if duplicates or empty_city_state or broken_address or raw_float_revenue or unclassified_ntee:
                print(f"\n  Category {cat_name}: {len(orgs)} orgs")
                print(f"    Duplicates: {duplicates} | Empty city/state: {empty_city_state}")
                print(f"    Broken addresses: {broken_address} | Raw float revenue: {raw_float_revenue}")
                print(f"    Unclassified NTEE: {unclassified_ntee}")
                if duplicates:
                    dup_eins = [ein for ein, count in ein_counts.items() if count > 1]
                    print(f"    Dup EINs: {dup_eins[:5]}")
        except Exception as e: print(f"  Error reading {cat_file}: {e}")

def audit_index_files():
    print("\n" + "="*60)
    print("AUDIT 3: Index/Sample Files")
    print("="*60)
    index_files = list(INDEX_DIR.glob("*.json"))
    print(f"Index files: {len(index_files)}")
    total_orgs = 0; all_eins = set(); states = set()
    for idx_file in index_files:
        try:
            with open(idx_file, 'r') as f: data = json.load(f)
            orgs = data if isinstance(data, list) else data.get('organizations', [])
            if not isinstance(orgs, list): continue
            total_orgs += len(orgs)
            for org in orgs:
                ein = str(org.get('ein', '')).strip()
                if ein: all_eins.add(ein)
                state = org.get('state', '')
                if state: states.add(state.upper())
        except: pass
    print(f"Total org records: {total_orgs}")
    print(f"Unique EINs: {len(all_eins)}")
    print(f"States found: {len(states)} — {sorted(states)[:10]}...")
    if len(states) not in [50, 51, 56]:
        print(f"\n  ⚠️  STATE COUNT BUG: {len(states)} states detected.")
        print(f"      Expected 50, 51 (incl DC), or 56 (incl territories)")
        print(f"      Actual: {sorted(states)}")

if __name__ == "__main__":
    print("MERIT Data Quality Audit")
    if not CACHE_DIR.exists():
        print(f"\nERROR: Cache dir not found at {CACHE_DIR}")
        print("Adjust BASE path in script if needed.")
    else:
        audit_propublica_cache()
        audit_category_files()
        audit_index_files()
        print("\n" + "="*60)
        print("AUDIT COMPLETE")
        print("="*60)
