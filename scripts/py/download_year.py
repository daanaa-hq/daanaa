import sys, csv, random, json, os, requests, time
import xml.etree.ElementTree as ET

YEAR = sys.argv[1]
SAMPLE_SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
BASE = "/home/akbar/meritgiving"

INDEX_CSV = f"{BASE}/data/index/index_{YEAR}.csv"
SAMPLE_JSON = f"{BASE}/data/index/sample_{YEAR}_{SAMPLE_SIZE}.json"
XML_DIR = f"{BASE}/data/xml/{YEAR}"
CSV_DIR = f"{BASE}/data/csv/{YEAR}"
LOG_DIR = f"{BASE}/logs"
os.makedirs(XML_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

LOGFILE = f"{LOG_DIR}/year_{YEAR}_{time.strftime('%Y%m%d_%H%M%S')}.log"

def log(msg):
    print(msg)
    with open(LOGFILE, 'a') as f:
        f.write(msg + '\n')

log("=" * 50)
log(f"DOWNLOAD YEAR: {YEAR} | Target: {SAMPLE_SIZE}")
log(f"Started: {time.strftime('%c')}")
log("=" * 50)

# --- Download Index ---
if not os.path.exists(INDEX_CSV) or os.path.getsize(INDEX_CSV) < 1000:
    log(f"[INDEX] Downloading index for {YEAR}...")
    url = f"https://apps.irs.gov/pub/epostcard/990/xml/{YEAR}/index_{YEAR}.csv"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        with open(INDEX_CSV, 'wb') as f:
            f.write(r.content)
        log(f"[INDEX] Saved: {INDEX_CSV}")
    except Exception as e:
        log(f"[INDEX] FAILED: {e}")
        sys.exit(1)
else:
    log(f"[INDEX] Already exists: {INDEX_CSV}")

# --- Sample ---
with open(INDEX_CSV, 'r', newline='') as f:
    records = list(csv.DictReader(f))

filers = [r for r in records if r.get('RETURN_TYPE') in ('990', '990EZ')]
pool = [r for r in filers if str(r.get('TAX_PERIOD', '')).startswith(YEAR)]

if len(pool) < SAMPLE_SIZE:
    log(f"WARNING: Only {len(pool)} tax year {YEAR} filings. Adding others.")
    needed = SAMPLE_SIZE - len(pool)
    others = [r for r in filers if not str(r.get('TAX_PERIOD', '')).startswith(YEAR)]
    if others:
        pool.extend(random.sample(others, min(needed, len(others))))

sample = random.sample(pool, min(SAMPLE_SIZE, len(pool)))

for r in sample:
    oid = r.get('OBJECT_ID')
    r['URL'] = f"https://gt990datalake-rawdata.s3.amazonaws.com/EfileData/XmlFiles/{oid}_public.xml"

with open(SAMPLE_JSON, 'w') as f:
    json.dump(sample, f)

log(f"SAMPLED: {len(sample)} -> {os.path.basename(SAMPLE_JSON)}")

# --- Download XMLs ---
with open(SAMPLE_JSON) as f:
    records = json.load(f)

total = len(records)
existing = downloaded = failed = 0

for i, r in enumerate(records, 1):
    url = r.get('URL')
    filename = f"{r.get('EIN')}_{r.get('TAX_PERIOD')}.xml"
    filepath = os.path.join(XML_DIR, filename)
    
    if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
        existing += 1
        continue
    
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            downloaded += 1
        else:
            failed += 1
    except Exception as e:
        failed += 1
    
    if i % 100 == 0:
        log(f"[{i}/{total}] Existing: {existing} | New: {downloaded} | Fail: {failed}")
        time.sleep(1)

log(f"\nDOWNLOAD DONE: Existing={existing}, New={downloaded}, Fail={failed}")

# --- Parse to CSV ---
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
        revenue = expenses = None
        
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

files = sorted([f for f in os.listdir(XML_DIR) if f.endswith('.xml')])
results = [parse_xml(os.path.join(XML_DIR, f)) for f in files]

csv_path = f"{CSV_DIR}/sample_{SAMPLE_SIZE}.csv"
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'filename','ein','organization_name','state',
        'tax_year','form_type','total_revenue','total_expenses','error'
    ])
    writer.writeheader()
    writer.writerows(results)

success = sum(1 for r in results if 'error' not in r)
rev = sum(1 for r in results if r.get('total_revenue'))
log(f"PARSED: {len(results)} files | Success: {success} | With Revenue: {rev}")
log(f"CSV: {csv_path}")
log("=" * 50)
log(f"YEAR {YEAR} COMPLETE: {time.strftime('%c')}")
log("=" * 50)
