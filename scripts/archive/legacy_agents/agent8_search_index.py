#!/usr/bin/env python3
"""
AGENT 8: SEARCH INDEX BUILDER
Mission: Build persistent inverted search index.
"""
import json, re
import pandas as pd

print("[AGENT 8] Building search index...")

df = pd.read_csv("data/csv/final_profiles.csv", dtype=str)
df['EIN'] = df['EIN'].astype(str).str.replace('.0', '').str.strip()

index = {}
for _, row in df.iterrows():
    ein = row['EIN']
    tokens = []
    name = str(row.get('NAME', '')).lower()
    tokens.extend(name.split())
    city = str(row.get('CITY', row.get('CITY_bmf', ''))).lower()
    state = str(row.get('STATE', '')).lower()
    tokens.extend([city, state])
    ntee = str(row.get('NTEE', '')).lower()
    tokens.append(ntee)
    mission = str(row.get('propub_mission', row.get('mission_ext', ''))).lower()
    tokens.extend(mission.split()[:30])
    
    for token in tokens:
        token = re.sub(r'[^a-z0-9]', '', token)
        if len(token) > 2:
            if token not in index:
                index[token] = []
            if ein not in index[token]:
                index[token].append(ein)

with open("data/search_index.json", 'w', encoding='utf-8') as f:
    json.dump(index, f)

print(f"[AGENT 8] Index built: {len(index)} tokens, {len(df)} orgs")
