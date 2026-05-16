#!/usr/bin/env python3
import json, csv
from pathlib import Path

BASE = Path.home() / "meritgiving"
INPUT = BASE / "data/scored/all_990_scored.json"
OUTPUT = BASE / "data/scored/merit_scores_export.csv"

with open(INPUT) as f:
    data = json.load(f)

rows = []
for ein, record in data.items():
    org = record['org']
    merit = record['merit']
    rows.append({
        'EIN': ein,
        'Name': org.get('NAME', ''),
        'City': org.get('CITY', ''),
        'State': org.get('STATE', ''),
        'NTEE_Code': org.get('NTEE', '')[:3] if org.get('NTEE') else '',
        'Revenue': org.get('REVENUE', ''),
        'Total_Expenses': org.get('TOTAL_EXPENSES', ''),
        'Program_Expenses': org.get('PROGRAM_EXPENSES', ''),
        'Net_Assets': org.get('NET_ASSETS', ''),
        'Total_Assets': org.get('TOTAL_ASSETS', ''),
        'Employees': org.get('EMPLOYEES', ''),
        'Volunteers': org.get('VOLUNTEERS', ''),
        'Mission': org.get('MISSION', '')[:300],
        'MERIT_Score': merit.get('merit_score', ''),
        'MERIT_Band': merit.get('merit_band', ''),
        'Peer_Group': merit.get('peer_group', ''),
        'Peer_Count': merit.get('peer_count', ''),
        'Program_Ratio': merit.get('metrics', {}).get('program_ratio', ''),
        'Sustainability_Ratio': merit.get('metrics', {}).get('sustainability_ratio', ''),
        'Reserves_Ratio': merit.get('metrics', {}).get('reserves_ratio', ''),
        'Leverage_Ratio': merit.get('metrics', {}).get('leverage_ratio', ''),
    })

with open(OUTPUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Exported {len(rows)} records to {OUTPUT}")
