#!/bin/bash
# MeritGiving Overnight Pipeline v1
# Safe to stop (Ctrl+C) and rerun. Skips already-downloaded files.

set -e
cd ~/meritgiving

# --- Config ---
SAMPLE_SIZE=5000
INDEX_CSV="data/index/index_2023.csv"
SAMPLE_JSON="data/index/sample_${SAMPLE_SIZE}.json"
XML_DIR="data/xml/2023"
CSV_DIR="data/csv/2023"
LOG_DIR="logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOGFILE="${LOG_DIR}/overnight_${TIMESTAMP}.log"

mkdir -p "$XML_DIR" "$CSV_DIR" "$LOG_DIR"

exec > >(tee -a "$LOGFILE")
exec 2>&1

echo "========================================"
echo "MERITGIVING OVERNIGHT PIPELINE STARTED"
echo "Time: $(date)"
echo "Target: ${SAMPLE_SIZE} filings"
echo "Log: $LOGFILE"
echo "========================================"

# --- Phase 1: Sample ---
echo ""
echo "[PHASE 1] Sampling ${SAMPLE_SIZE} records..."
~/meritgiving/venv/bin/python << PYEOF
import csv, random, json, os

with open('$INDEX_CSV', 'r', newline='') as f:
    records = list(csv.DictReader(f))

filers = [r for r in records if r.get('RETURN_TYPE') in ('990', '990EZ')]

# Use tax year 2022 (submitted in 2023) as the primary pool
pool = [r for r in filers if str(r.get('TAX_PERIOD', '')).startswith('2022')]

if len(pool) < $SAMPLE_SIZE:
    print(f"WARNING: Only {len(pool)} tax year 2022 filings. Adding others.")
    needed = $SAMPLE_SIZE - len(pool)
    others = [r for r in filers if not str(r.get('TAX_PERIOD', '')).startswith('2022')]
    pool.extend(random.sample(others, min(needed, len(others))))

sample = random.sample(pool, min($SAMPLE_SIZE, len(pool)))

# Add download URLs
for r in sample:
    oid = r.get('OBJECT_ID')
    r['URL'] = f"https://gt990datalake-rawdata.s3.amazonaws.com/EfileData/XmlFiles/{oid}_public.xml"

with open('$SAMPLE_JSON', 'w') as f:
    json.dump(sample, f)

print(f"SAMPLED: {len(sample)} records -> {os.path.basename('$SAMPLE_JSON')}")
PYEOF

# --- Phase 2: Download ---
echo ""
echo "[PHASE 2] Downloading XML files (resumes where left off)..."
~/meritgiving/venv/bin/python << PYEOF
import json, os, requests, time

xml_dir = '$XML_DIR'
with open('$SAMPLE_JSON') as f:
    records = json.load(f)

total = len(records)
existing = 0
downloaded = 0
failed = 0

for i, r in enumerate(records, 1):
    url = r.get('URL')
    filename = f"{r.get('EIN')}_{r.get('TAX_PERIOD')}.xml"
    filepath = os.path.join(xml_dir, filename)
    
    if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
        existing += 1
        if i % 100 == 0:
            print(f"[{i}/{total}] SKIP (exists): {filename}")
        continue
    
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            downloaded += 1
            if downloaded % 50 == 0:
                print(f"[{i}/{total}] DOWNLOADED: {downloaded} new files so far")
        else:
            failed += 1
            if failed % 25 == 0:
                print(f"[{i}/{total}] FAIL {resp.status_code}: {url}")
    except Exception as e:
        failed += 1
    
    # Be polite to the server
    if i % 50 == 0:
        time.sleep(1)

print(f"\nDOWNLOAD SUMMARY:")
print(f"  Already had: {existing}")
print(f"  New:         {downloaded}")
print(f"  Failed:      {failed}")
print(f"  Total XMLs:  {len([f for f in os.listdir(xml_dir) if f.endswith('.xml')])}")
PYEOF

# --- Phase 3: Parse ---
echo ""
echo "[PHASE 3] Parsing XML to CSV..."
~/meritgiving/venv/bin/python << PYEOF
import os, csv, glob, xml.etree.ElementTree as ET

xml_dir = '$XML_DIR'
csv_path = '${CSV_DIR}/sample_${SAMPLE_SIZE}.csv'
os.makedirs(os.path.dirname(csv_path), exist_ok=True)

NS = 'http://www.irs.gov/efile'

def find_text(root, paths):
    for path in paths:
        el = root.find(path)
        if el is not None and el.text:
            return el.text.strip()
    return None

def parse_xml(path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        
        ein = find_text(root, [
            f'.//{{{NS}}}ReturnHeader/{{{NS}}}Filer/{{{NS}}}EIN',
            './/ReturnHeader/Filer/EIN', './/EIN'
        ])
        
        name = find_text(root, [
            f'.//{{{NS}}}ReturnHeader/{{{NS}}}Filer/{{{NS}}}BusinessName/{{{NS}}}BusinessNameLine1Txt',
            './/ReturnHeader/Filer/BusinessName/BusinessNameLine1Txt',
            './/BusinessNameLine1Txt', './/BusinessNameLine1'
        ])
        
        state = find_text(root, [
            f'.//{{{NS}}}ReturnHeader/{{{NS}}}Filer/{{{NS}}}USAddress/{{{NS}}}StateAbbreviationCd',
            './/ReturnHeader/Filer/USAddress/StateAbbreviationCd',
            './/StateAbbreviationCd'
        ])
        
        tax_period = find_text(root, [
            f'.//{{{NS}}}ReturnHeader/{{{NS}}}TaxPeriodEndDt',
            './/ReturnHeader/TaxPeriodEndDt', './/TaxPeriodEndDt'
        ])
        tax_year = tax_period[:4] if tax_period else None
        
        form_type = 'Unknown'
        revenue = None
        expenses = None
        
        irs990 = root.find(f'.//{{{NS}}}IRS990') or root.find('.//IRS990')
        if irs990 is not None:
            form_type = '990'
            revenue = find_text(irs990, [
                f'.//{{{NS}}}CYTotalRevenueAmt', './/CYTotalRevenueAmt',
                f'.//{{{NS}}}TotalRevenueAmt', './/TotalRevenueAmt'
            ])
            expenses = find_text(irs990, [
                f'.//{{{NS}}}CYTotalExpensesAmt', './/CYTotalExpensesAmt',
                f'.//{{{NS}}}TotalExpensesAmt', './/TotalExpensesAmt'
            ])
        else:
            irs990ez = root.find(f'.//{{{NS}}}IRS990EZ') or root.find('.//IRS990EZ')
            if irs990ez is not None:
                form_type = '990EZ'
                revenue = find_text(irs990ez, [
                    f'.//{{{NS}}}TotalRevenueAmt', './/TotalRevenueAmt'
                ])
                expenses = find_text(irs990ez, [
                    f'.//{{{NS}}}TotalExpensesAmt', './/TotalExpensesAmt'
                ])
        
        return {
            'filename': os.path.basename(path), 'ein': ein,
            'organization_name': name, 'state': state, 'tax_year': tax_year,
            'form_type': form_type, 'total_revenue': revenue,
            'total_expenses': expenses
        }
    except Exception as e:
        return {'filename': os.path.basename(path), 'error': str(e)}

files = sorted(glob.glob(os.path.join(xml_dir, '*.xml')))
results = [parse_xml(f) for f in files]

with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'filename','ein','organization_name','state',
        'tax_year','form_type','total_revenue','total_expenses','error'
    ])
    writer.writeheader()
    writer.writerows(results)

success = sum(1 for r in results if 'error' not in r)
rev = sum(1 for r in results if r.get('total_revenue'))
name = sum(1 for r in results if r.get('organization_name'))
state = sum(1 for r in results if r.get('state'))

print(f"\nPARSE SUMMARY:")
print(f"  Total XMLs parsed: {len(results)}")
print(f"  Successful:        {success}")
print(f"  With Name:         {name}")
print(f"  With State:        {state}")
print(f"  With Revenue:      {rev}")
print(f"  CSV:               {csv_path}")
PYEOF

# --- Phase 4: Morning Report ---
echo ""
echo "========================================"
echo "PIPELINE COMPLETE"
echo "Time: $(date)"
echo "========================================"
echo ""
echo "FILES:"
echo "  Sample:    $SAMPLE_JSON"
echo "  XMLs:      $XML_DIR"
echo "  CSV:       ${CSV_DIR}/sample_${SAMPLE_SIZE}.csv"
echo "  Log:       $LOGFILE"
echo ""
echo "QUICK CHECK:"
wc -l "${CSV_DIR}/sample_${SAMPLE_SIZE}.csv"
echo ""
echo "To review: tail -50 $LOGFILE"
