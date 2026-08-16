#!/bin/bash
cd ~/meritgiving || exit 1
mkdir -p data/csv logs

echo "========================================"
echo "MERITGIVING DAEMON — $(date)"
echo "========================================"

STATE_FILE=".state"
TODAY=$(date +%Y%m%d)

# --- 0. Resume check ---
if [ -f "$STATE_FILE" ]; then
    last_run=$(cat "$STATE_FILE")
    if [ "$last_run" = "$TODAY" ]; then
        echo "[0] Already completed today ($TODAY). Skipping to scoring."
        SKIP_PARSE=1
    else
        echo "[0] Last run: $last_run. Today: $TODAY. Running full cycle."
        SKIP_PARSE=0
    fi
else
    SKIP_PARSE=0
fi

# --- 1. Monthly IRS check (only on 1st, only if not done today) ---
DAY_OF_MONTH=$(date +%d)
if [ "$DAY_OF_MONTH" = "01" ] && [ "$SKIP_PARSE" = "0" ]; then
    echo "[1] Monthly IRS data check..."
    CURRENT_YEAR=$(date +%Y)
    python3 scripts/py/download_year.py "$CURRENT_YEAR" 5000
fi

# --- 2. Parse backlog (skip if ANY CSV already exists for that year) ---
if [ "$SKIP_PARSE" = "0" ]; then
    echo "[2] Parsing backlog..."
    for year_dir in data/xml/*/; do
        [ -d "$year_dir" ] || continue
        year=$(basename "$year_dir")
        xml_count=$(ls "$year_dir"/*.xml 2>/dev/null | wc -l)
        
        # ROBUST CHECK: any CSV means this year is done
        if [ -d "data/csv/$year" ] && ls data/csv/$year/*.csv 1>/dev/null 2>/dev/null; then
            echo "  SKIP $year: CSV already exists."
            continue
        fi
        
        if [ "$xml_count" -gt 0 ]; then
            echo "  Parsing $year ($xml_count XMLs)..."
            python3 scripts/py/download_year.py "$year" "$xml_count"
        fi
    done
else
    echo "[2] Parsing skipped (already done today)."
fi

# --- 3. Rebuild percentile engine ---
echo "[3] Rebuilding percentile engine..."
python3 -c "
import csv, os, statistics
from collections import defaultdict

all_orgs = []
for csv_file in os.listdir('data/csv'):
    year_path = os.path.join('data/csv', csv_file)
    if os.path.isdir(year_path):
        for f in os.listdir(year_path):
            if f.endswith('.csv'):
                with open(os.path.join(year_path, f), 'r', encoding='utf-8') as fh:
                    rows = list(csv.DictReader(fh))
                for r in rows:
                    ein = r.get('ein', '').strip()
                    rev_str = r.get('total_revenue', r.get('organizational_scale', '')).strip()
                    if not rev_str or not ein: continue
                    try: revenue = float(rev_str)
                    except: continue
                    all_orgs.append({
                        'ein': ein, 'name': r.get('organization_name', ''),
                        'state': r.get('state', ''), 'tax_year': r.get('tax_year', csv_file),
                        'revenue': revenue, 'form_type': r.get('form_type', 'Unknown')
                    })

bmf = {}
if os.path.exists('data/bmf.csv'):
    with open('data/bmf.csv', 'r', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            ein = row.get('EIN', '').strip()
            ntee = row.get('NTEE_CD', row.get('NTEE', '')).strip()
            if ein and ntee: bmf[ein] = ntee

for org in all_orgs: org['ntee'] = bmf.get(org['ein'], '')

peer_groups = defaultdict(list)
for org in all_orgs:
    ntee_key = org['ntee'][:3] if len(org['ntee']) >= 3 else org['ntee']
    peer_groups[(ntee_key, org['state'])].append(org['revenue'])

percentiles = {}
for key, revenues in peer_groups.items():
    if len(revenues) < 2: continue
    revenues.sort()
    median = statistics.median(revenues)
    for org in all_orgs:
        org_key = (org['ntee'][:3] if len(org['ntee']) >= 3 else org['ntee'], org['state'])
        if org_key != key: continue
        if org['revenue'] <= median:
            pct = 50 * (org['revenue'] / median) if median > 0 else 0
        else:
            max_rev = revenues[-1]
            pct = 50 + 50 * ((org['revenue'] - median) / (max_rev - median)) if max_rev > median else 50
        percentiles[(org['ein'], org['tax_year'])] = {
            'percentile': round(pct, 1), 'peer_count': len(revenues), 'median': median
        }

with open('data/csv/percentile_engine_latest.csv', 'w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=['ein','name','state','tax_year','revenue','ntee','percentile','peer_count','median_revenue','form_type'])
    writer.writeheader()
    for org in all_orgs:
        key = (org['ein'], org['tax_year'])
        if key in percentiles:
            p = percentiles[key]
            writer.writerow({
                'ein': org['ein'], 'name': org['name'], 'state': org['state'],
                'tax_year': org['tax_year'], 'revenue': org['revenue'],
                'ntee': org['ntee'], 'percentile': p['percentile'],
                'peer_count': p['peer_count'], 'median_revenue': p['median'],
                'form_type': org['form_type']
            })

print(f'    Engine: {len(percentiles)} organizations with percentiles')
'

# --- 4. Generate daily report ---
echo "[4] Generating daily report..."
python3 -c "
import csv, os
from collections import Counter
from datetime import datetime

with open('data/csv/percentile_engine_latest.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

missing = sum(1 for r in rows if not r.get('ntee'))
ntee_counts = Counter(r.get('ntee','')[:1] for r in rows if r.get('ntee'))

report = f'''MERITGIVING DAILY REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M')}

DATA INVENTORY
  Total organizations: {len(rows)}
  With percentiles: {len(rows) - missing}
  NTEE coverage: {((len(rows)-missing)/len(rows)*100):.1f}%

TOP CATEGORIES
{chr(10).join(f'  {cat}: {count}' for cat, count in ntee_counts.most_common(5))}

FILE STATUS
  Latest engine: data/csv/percentile_engine_latest.csv
  Size: {os.path.getsize('data/csv/percentile_engine_latest.csv')} bytes

NEXT ACTIONS (Require Human)
  [ ] Show profile card to 1 nonprofit expert
  [ ] File for fiscal sponsorship or 501(c)(3)
  [ ] Build web frontend (EIN lookup → card display)
'''

report_path = f'logs/daily_report_{datetime.now().strftime(\"%Y%m%d\")}.txt'
with open(report_path, 'w') as f:
    f.write(report)

print(f'    Report: {report_path}')
print(report)
"

# --- 5. Mark complete so we never repeat work ---
echo "$TODAY" > "$STATE_FILE"
echo ""
echo "========================================"
echo "DAEMON COMPLETE — $(date)"
echo "========================================"
