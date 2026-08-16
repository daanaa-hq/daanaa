#!/usr/bin/env python3
"""
Data Structure Inspector — finds actual field names and schemas
"""
import json, os
from pathlib import Path
from collections import Counter

BASE = Path.home() / "meritgiving"
DATA = BASE / "data"

def inspect_file(path, label, max_depth=3):
    print(f"\n{'='*60}")
    print(f"INSPECTING: {label}")
    print(f"Path: {path}")
    print(f"Exists: {path.exists()}")
    if not path.exists():
        return
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading: {e}")
        return
    
    print(f"Type: {type(data).__name__}")
    if isinstance(data, list):
        print(f"Length: {len(data)}")
        if len(data) > 0:
            sample = data[0]
            print(f"First item type: {type(sample).__name__}")
            if isinstance(sample, dict):
                print(f"Top-level keys: {list(sample.keys())}")
                # Check for common fields
                for field in ['ein', 'name', 'state', 'city', 'revenue', 'total_revenue', 
                              'ntee', 'ntee_code', 'mission', 'address', 'street_address',
                              'total_expenses', 'program_expenses', 'total_assets', 
                              'total_liabilities', 'net_assets', 'tax_year', 'filing_year']:
                    if field in sample:
                        val = sample[field]
                        print(f"  {field}: {type(val).__name__} = {str(val)[:60]}")
                # Check nested structures
                for k, v in sample.items():
                    if isinstance(v, dict):
                        print(f"  {k} -> nested keys: {list(v.keys())}")
    elif isinstance(data, dict):
        print(f"Top-level keys: {list(data.keys())}")
        # Check if 'organizations' key exists
        if 'organizations' in data:
            orgs = data['organizations']
            print(f"'organizations' type: {type(orgs).__name__}, len: {len(orgs) if hasattr(orgs, '__len__') else 'N/A'}")
        # Sample some values
        for k, v in list(data.items())[:5]:
            print(f"  {k}: {type(v).__name__} = {str(v)[:80]}")

# Inspect everything
inspect_file(DATA / "propublica_cache" / "812414283.json", "ProPublica Cache Sample")
inspect_file(DATA / "categories" / "X.json", "Category X")
inspect_file(DATA / "categories" / "T.json", "Category T")
inspect_file(DATA / "index" / "sample_2023_2000.json", "Index 2023 Sample")
inspect_file(DATA / "index" / "sample_2021_10000.json", "Index 2021 10k")
inspect_file(DATA / "xml_extracted.json", "XML Extracted")

# Also check a few more cache files to see variation
print(f"\n{'='*60}")
print("SAMPLING 5 CACHE FILES FOR STRUCTURE VARIATION")
print(f"{'='*60}")
cache_dir = DATA / "propublica_cache"
files = sorted(cache_dir.glob("*.json"))[:5]
all_keys = Counter()
for f in files:
    with open(f) as fh:
        d = json.load(fh)
    items = d if isinstance(d, list) else [d]
    for item in items:
        if isinstance(item, dict):
            for k in item.keys():
                all_keys[k] += 1
print("Field presence across 5 sample cache files:")
for k, c in all_keys.most_common(30):
    print(f"  {k}: {c}/5")

