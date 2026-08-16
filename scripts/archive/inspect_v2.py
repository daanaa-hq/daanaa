#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"

def deep_inspect(path, label):
    print(f"\n{'='*60}")
    print(f"INSPECT: {label}")
    if not path.exists():
        print("FILE NOT FOUND")
        return
    with open(path) as f:
        data = json.load(f)
    print(f"Type: {type(data).__name__}")
    if isinstance(data, dict) and 'organization' in data:
        org = data['organization']
        print(f"organization keys: {list(org.keys())}")
        for k in ['ein','name','city','state','zipcode','ntee_code','ntee_classification','mission','address']:
            if k in org:
                print(f"  org.{k}: {str(org[k])[:60]}")
        filings = data.get('filings_with_data', [])
        print(f"\nfilings_with_data: {len(filings)} records")
        if filings:
            latest = filings[0]
            print(f"First filing keys: {list(latest.keys())}")
            for k in ['tax_period','total_revenue','total_expenses','total_assets_eoy','total_assets_boy','total_liabilities_eoy','total_liabilities_boy','net_assets_eoy','net_assets_boy']:
                if k in latest:
                    print(f"  filing.{k}: {latest[k]}")
    elif isinstance(data, list):
        print(f"List length: {len(data)}")
        if data and isinstance(data[0], dict):
            print(f"First item keys: {list(data[0].keys())}")
            sample = data[0]
            for path in ['ein','EIN','organization.ein','id','ntee_code']:
                keys = path.split('.')
                val = sample
                for k in keys:
                    val = val.get(k, {}) if isinstance(val, dict) else None
                    if val is None:
                        break
                if val:
                    print(f"  Found {path}: {str(val)[:40]}")
                    break

deep_inspect(DATA / "propublica_cache" / "812414283.json", "Cache Sample")
deep_inspect(DATA / "categories" / "X.json", "Category X")
deep_inspect(DATA / "categories" / "T.json", "Category T")
deep_inspect(DATA / "index" / "sample_2023_2000.json", "Index 2023")
deep_inspect(DATA / "xml_extracted.json", "XML Extracted")

print(f"\n{'='*60}")
print("FILING FIELD AVAILABILITY (20 samples)")
print(f"{'='*60}")
cache_files = sorted((DATA / "propublica_cache").glob("*.json"))[:20]
field_counts = Counter()
for f in cache_files:
    with open(f) as fh:
        d = json.load(fh)
    filings = d.get('filings_with_data', [])
    if filings:
        for k in filings[0].keys():
            field_counts[k] += 1
for k, c in field_counts.most_common(30):
    print(f"  {k}: {c}/20")
