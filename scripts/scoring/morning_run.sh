#!/bin/bash
# MERIT Morning Autopilot — Run this when you wake up
# Applies overnight GPU NTEE fixes, re-scores everything, exports CSV

set -e
cd ~/meritgiving

echo "=========================================="
echo "MERIT Morning Autopilot"
echo "$(date)"
echo "=========================================="

# Check if GPU job finished
if [ -f logs/gpu_bulk_pid.txt ]; then
    GPU_PID=$(cat logs/gpu_bulk_pid.txt)
    if ps -p $GPU_PID > /dev/null 2>&1; then
        echo "GPU job still running (PID $GPU_PID). Wait or kill it."
        tail -5 logs/gpu_bulk_ntee.log
        exit 1
    else
        echo "GPU job finished."
        tail -5 logs/gpu_bulk_ntee.log
    fi
fi

# Step 1: Load overnight fixes
echo ""
echo "[1/4] Loading NTEE fixes from overnight GPU batch..."
python3 -c "
import json
from pathlib import Path
from collections import Counter

base = Path.home() / 'meritgiving'

with open(base / 'data/ntee_fixes.json') as f:
    fixes = json.load(f)

with open(base / 'data/xml_extracted.json') as f:
    data = json.load(f)

applied = 0
already = 0
for ein, org in data.items():
    ntee = str(org.get('NTEE', '')).strip().upper()
    if ntee and ntee not in ['NON', 'NONE', '']:
        already += 1
    elif ein in fixes:
        org['NTEE'] = fixes[ein]
        applied += 1

with open(base / 'data/xml_extracted.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f'Already valid: {already}')
print(f'Applied overnight fixes: {applied}')
print(f'Total with NTEE: {already + applied}')

# Count scorable
scorable = 0
for ein, org in data.items():
    ntee = str(org.get('NTEE', '')).strip().upper()
    rev = org.get('REVENUE', 0)
    exp = org.get('TOTAL_EXPENSES', 0)
    if ntee and ntee not in ['NON', 'NONE', ''] and rev and float(rev) > 0 and exp and float(exp) > 0:
        scorable += 1
print(f'Projected scorable orgs: {scorable}')
"

# Step 2: Re-score with all fixes
echo ""
echo "[2/4] Re-scoring all orgs with complete NTEE..."
python3 scripts/merit_scorer_v3_3.py --output data/scored/all_990_scored_morning.json | tee logs/morning_score.log

# Step 3: Export to CSV
echo ""
echo "[3/4] Exporting to CSV..."
python3 -c "
import json, csv
from pathlib import Path

base = Path.home() / 'meritgiving'
with open(base / 'data/scored/all_990_scored_morning.json') as f:
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

output = base / 'data/scored/merit_scores_final_export.csv'
with open(output, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f'Exported {len(rows)} records to {output}')
"

# Step 4: Summary
echo ""
echo "[4/4] Morning run complete!"
echo ""
echo "Files ready for import:"
echo "  - data/scored/all_990_scored_morning.json (full scored dataset)"
echo "  - data/scored/merit_scores_final_export.csv (Webflow/Airtable import)"
echo ""
echo "Next: Import CSV to Airtable/Webflow, update templates, show board."
echo "=========================================="
