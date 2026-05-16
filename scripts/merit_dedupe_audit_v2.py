#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter, defaultdict

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"
CACHE_DIR = DATA / "propublica_cache"
CAT_DIR = DATA / "categories"
INDEX_DIR = DATA / "index"

def get_org_field(org_dict, field, default=''):
    return str(org_dict.get(field, default)).strip()

def get_latest_filing(filings):
    if not filings:
        return {}
    try:
        return max(filings, key=lambda f: str(f.get('tax_period', '')))
    except:
        return filings[0]

def audit_cache():
    print("="*60)
    print("AUDIT 1: ProPublica Cache (ALL files)")
    print("="*60)
    files = list(CACHE_DIR.glob("*.json"))
    print(f"Total files: {len(files)}")
    ein_records = defaultdict(list)
    missing_mission = 0
    missing_ntee = 0
    ntee_codes = Counter()
    for f in files:
        try:
            with open(f) as fh:
                data = json.load(fh)
            org = data.get('organization', {})
            ein = get_org_field(org, 'ein')
            if not ein:
                continue
            filings = data.get('filings_with_data', [])
            latest = get_latest_filing(filings)
            ein_records[ein].append({
                'file': f.name,
                'name': get_org_field(org, 'name'),
                'city': get_org_field(org, 'city'),
                'state': get_org_field(org, 'state'),
                'ntee': get_org_field(org, 'ntee_code') or get_org_field(org, 'ntee_classification'),
                'mission': get_org_field(org, 'mission'),
                'latest_tax_period': str(latest.get('tax_period', '')),
                'latest_revenue': latest.get('total_revenue'),
                'filing_count': len(filings)
            })
            mission = get_org_field(org, 'mission')
            if not mission:
                missing_mission += 1
            ntee = get_org_field(org, 'ntee_code') or get_org_field(org, 'ntee_classification')
            if not ntee:
                missing_ntee += 1
            else:
                ntee_codes[ntee[:3] if len(ntee) >= 3 else ntee] += 1
        except:
            pass
    multi_file_eins = {ein: recs for ein, recs in ein_records.items() if len(recs) > 1}
    print(f"\nUnique EINs: {len(ein_records)}")
    print(f"EINs with multiple cache files: {len(multi_file_eins)}")
    if multi_file_eins:
        print("\nTop 10 EINs by file count:")
        for ein, recs in sorted(multi_file_eins.items(), key=lambda x: -len(x[1]))[:10]:
            print(f"  {ein}: {len(recs)} files | {recs[0]['name']}")
    contradictions = 0
    for ein, recs in ein_records.items():
        years = []
        for r in recs:
            tp = r['latest_tax_period']
            if len(tp) >= 4:
                try:
                    years.append(int(tp[:4]))
                except:
                    pass
        if len(years) > 1 and max(years) - min(years) > 5:
            contradictions += 1
    print(f"\nEINs with >5yr filing contradictions: {contradictions}")
    print(f"Orgs missing mission: {missing_mission}")
    print(f"Orgs missing NTEE: {missing_ntee}")
    print(f"\nTop NTEE codes:")
    for code, count in ntee_codes.most_common(10):
        print(f"  {code}: {count}")
    states = set()
    for recs in ein_records.values():
        state = recs[0]['state'].upper()
        if state and len(state) == 2:
            states.add(state)
    print(f"\nStates in cache: {len(states)}")
    print(f"  {sorted(states)[:20]}")
    if len(states) not in [50, 51, 56]:
        print(f"  ⚠️  STATE BUG: {len(states)} states")

def audit_categories():
    print("\n" + "="*60)
    print("AUDIT 2: Category Files")
    print("="*60)
    cat_files = list(CAT_DIR.glob("*.json"))
    print(f"Files: {len(cat_files)}")
    for cat_file in cat_files:
        try:
            with open(cat_file) as f:
                data = json.load(f)
            orgs = data if isinstance(data, list) else data.get('organizations', [])
            if not isinstance(orgs, list):
                continue
            ein_counts = Counter()
            empty_loc = 0
            raw_float = 0
            no_ntee = 0
            for org in orgs:
                ein = ''
                for path in ['ein', 'EIN', 'organization.ein']:
                    keys = path.split('.')
                    val = org
                    for k in keys:
                        val = val.get(k, {}) if isinstance(val, dict) else None
                        if val is None:
                            break
                    if val:
                        ein = str(val).strip()
                        break
                if ein:
                    ein_counts[ein] += 1
                city = org.get('city', '')
                state = org.get('state', '')
                if not city and not state:
                    empty_loc += 1
                rev = org.get('revenue', org.get('total_revenue', ''))
                if isinstance(rev, float) or (isinstance(rev, str) and '.0' in rev and '$' not in rev):
                    raw_float += 1
                ntee = org.get('ntee', org.get('ntee_code', ''))
                if not ntee:
                    no_ntee += 1
            dups = sum(1 for c in ein_counts.values() if c > 1)
            if dups or empty_loc or raw_float or no_ntee:
                print(f"\n  {cat_file.name}: {len(orgs)} orgs")
                print(f"    Dups: {dups} | Empty loc: {empty_loc} | Raw float: {raw_float} | No NTEE: {no_ntee}")
                if dups:
                    print(f"    Dup EINs: {[e for e,c in ein_counts.items() if c>1][:5]}")
        except Exception as e:
            print(f"  Error: {cat_file.name}: {e}")

def audit_index():
    print("\n" + "="*60)
    print("AUDIT 3: Index Files")
    print("="*60)
    idx_files = list(INDEX_DIR.glob("*.json"))
    print(f"Files: {len(idx_files)}")
    total = 0
    all_eins = set()
    states = set()
    for f in idx_files:
        try:
            with open(f) as fh:
                data = json.load(fh)
            orgs = data if isinstance(data, list) else data.get('organizations', [])
            if not isinstance(orgs, list):
                continue
            total += len(orgs)
            for org in orgs:
                ein = str(org.get('ein', '')).strip()
                if ein:
                    all_eins.add(ein)
                state = str(org.get('state', '')).strip().upper()
                if state and len(state) == 2:
                    states.add(state)
        except:
            pass
    print(f"Total records: {total}")
    print(f"Unique EINs: {len(all_eins)}")
    print(f"States: {len(states)} — {sorted(states)[:15]}")
    if len(states) not in [50, 51, 56]:
        print(f"  ⚠️  BUG: {len(states)} states")

if __name__ == "__main__":
    print("MERIT Data Quality Audit v2")
    audit_cache()
    audit_categories()
    audit_index()
    print("\n" + "="*60)
    print("AUDIT COMPLETE")
    print("="*60)
