#!/usr/bin/env python3
import csv, json, os, glob
from collections import defaultdict
from propublica_fix import get_pp_revenue_history
import time

CSV_DIR = "data/csv"
org_years = defaultdict(dict)  # ein -> {year: {name, revenue, state, ntee, source}}

def load_csv_file(f, year_hint=None):
    """Load a single CSV with flexible column detection."""
    with open(f) as fh:
        sample = fh.read(8192)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.DictReader(fh, dialect=dialect)
        except:
            fh.seek(0)
            reader = csv.DictReader(fh)
        
        fieldnames = [c.lower().strip() for c in (reader.fieldnames or [])]
        
        # Map columns (case-insensitive)
        col_map = {}
        for i, col in enumerate(fieldnames):
            if col in ['ein', 'employer_identification_number']:
                col_map['ein'] = i
            elif col in ['name', 'organization_name', 'taxpayer_name', 'business_name', 'org_name']:
                col_map['name'] = i
            elif col in ['total_revenue', 'revenue', 'totrevenue', 'cy_total_revenue', 'total_revenue_amt']:
                col_map['revenue'] = i
            elif col in ['state', 'state_abbreviation', 'state_cd']:
                col_map['state'] = i
            elif col in ['ntee_cd', 'ntee_code', 'ntee']:
                col_map['ntee'] = i
            elif col in ['tax_year', 'year', 'tax_period', 'filing_year']:
                col_map['year'] = i
        
        rows = []
        for row in reader:
            vals = list(row.values())
            ein_raw = vals[col_map['ein']].strip() if 'ein' in col_map else ''
            if not ein_raw:
                continue
            ein = ein_raw.zfill(9)
            
            rev_raw = vals[col_map['revenue']].strip() if 'revenue' in col_map else '0'
            try:
                rev = float(rev_raw) if rev_raw else 0.0
            except:
                rev = 0.0
            
            name = vals[col_map['name']].strip() if 'name' in col_map else ''
            state = vals[col_map['state']].strip() if 'state' in col_map else ''
            ntee = vals[col_map['ntee']].strip() if 'ntee' in col_map else ''
            
            # Year from column or from filename/path
            yr = year_hint
            if 'year' in col_map:
                yr = vals[col_map['year']].strip() or yr
            
            if not yr:
                continue
                
            rows.append({
                'ein': ein, 'year': yr, 'revenue': rev,
                'name': name, 'state': state, 'ntee': ntee,
                'source': os.path.basename(f)
            })
        return rows

# --- PHASE A: Load all sample CSVs from year subdirectories ---
print("=== Loading year-sampled CSVs ===")
csv_files = glob.glob(f"{CSV_DIR}/*/*.csv", recursive=False)
total_loaded = 0
for f in csv_files:
    # Skip backup and empty files
    if 'backup' in f:
        continue
    if os.path.getsize(f) < 200:  # Just header, skip
        continue
    
    parts = f.replace(CSV_DIR, "").strip(os.sep).split(os.sep)
    year_hint = parts[0] if len(parts) >= 2 else None
    
    rows = load_csv_file(f, year_hint)
    for r in rows:
        existing = org_years[r['ein']].get(r['year'], {})
        org_years[r['ein']][r['year']] = {
            'revenue': r['revenue'],
            'name': r['name'] or existing.get('name', ''),
            'state': r['state'] or existing.get('state', ''),
            'ntee': r['ntee'] or existing.get('ntee', ''),
            'source': r['source']
        }
    total_loaded += len(rows)
    print(f"  {f}: {len(rows)} rows")

# --- PHASE B: Load backup percentile files (RICHEST DATA) ---
print("\n=== Loading backup percentile files ===")
backup_files = [
    'data/csv/backup/percentile_engine_latest.csv',
    'data/csv/backup/percentile_engine_filtered.csv',
    'data/csv/backup/percentile_engine_v1.csv',
    'data/csv/backup/percentile_engine_v2.csv',
]
for f in backup_files:
    if not os.path.exists(f):
        continue
    rows = load_csv_file(f)
    added = 0
    for r in rows:
        if r['ein'] not in org_years or r['year'] not in org_years[r['ein']]:
            # Only add if not already present (backup is enriched)
            existing = org_years[r['ein']].get(r['year'], {})
            org_years[r['ein']][r['year']] = {
                'revenue': r['revenue'],
                'name': r['name'] or existing.get('name', ''),
                'state': r['state'] or existing.get('state', ''),
                'ntee': r['ntee'] or existing.get('ntee', ''),
                'source': 'percentile_backup'
            }
            added += 1
    print(f"  {f}: {added} new rows")

# --- STATS ---
total_orgs = len(org_years)
current_multi = len([e for e, y in org_years.items() if len(y) >= 2])
print(f"\n{'='*50}")
print(f"TOTAL ORGS: {total_orgs}")
print(f"MULTI-YEAR ORGS (2+ years): {current_multi}")
print(f"SINGLE-YEAR ORGS: {total_orgs - current_multi}")
print(f"{'='*50}")

# --- PHASE C: ProPublica backfill for single-year orgs ---
print("\n=== ProPublica backfill ===")
orgs_to_backfill = [ein for ein, years in org_years.items() if len(years) < 2]
print(f"Orgs needing backfill: {len(orgs_to_backfill)}")

backfilled = 0
for i, ein in enumerate(orgs_to_backfill):
    if i % 200 == 0:
        print(f"  Progress: {i}/{len(orgs_to_backfill)} (backfilled {backfilled})")
    try:
        hist = get_pp_revenue_history(ein)
        for h in hist:
            yr = str(h.get("year", ""))
            rev = h.get("revenue")
            if rev and yr and yr not in org_years[ein]:
                existing_years = list(org_years[ein].values())
                existing_name = existing_years[0].get('name', '') if existing_years else ''
                org_years[ein][yr] = {
                    'revenue': float(rev),
                    'name': existing_name,
                    'state': '',
                    'ntee': '',
                    'source': 'propublica'
                }
                backfilled += 1
        time.sleep(0.3)
    except:
        pass

new_multi = len([e for e, y in org_years.items() if len(y) >= 2])
print(f"\nAfter backfill: {new_multi} multi-year (+{new_multi - current_multi})")

# --- WRITE MASTER CSV ---
os.makedirs("data", exist_ok=True)
with open("data/master_orgs.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["EIN", "NAME", "STATE", "NTEE", "YEAR", "REVENUE", "SOURCE"])
    for ein, years in org_years.items():
        for yr, data in years.items():
            writer.writerow([
                ein,
                data.get('name', ''),
                data.get('state', ''),
                data.get('ntee', ''),
                yr,
                data.get('revenue', 0),
                data.get('source', 'irs_990')
            ])

print(f"\nSaved to data/master_orgs.csv")
print(f"Final: {total_orgs} orgs, {new_multi} multi-year")
