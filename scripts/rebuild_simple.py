import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import sys

HOME = Path.home()
DATA_DIR = HOME / 'meritgiving/NCCS Monthly DAtA'
DB_PATH = HOME / 'meritgiving/data/meritgiving.db'

print('=' * 60)
print('MeritGiving Rebuild')
print('=' * 60)

tables = []
if DB_PATH.exists():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in c.fetchall()]
    for t in tables:
        c.execute('SELECT COUNT(*) FROM ' + t)
        print(t + ': ' + str(c.fetchone()[0]) + ' rows')
    conn.close()

if 'registry' in tables:
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM registry_enriched')
    count = c.fetchone()[0]
    conn.close()
    if count > 0:
        print('Already has ' + str(count) + ' rows. Done.')
        sys.exit(0)

print('Finding BMF files...')
all_csvs = sorted(DATA_DIR.glob('*.csv'))
processed = [f for f in all_csvs if '_processed' in f.name and f.name.startswith('bmf_')]
if not processed:
    print('ERROR: No bmf files')
    sys.exit(1)

latest = sorted(processed)[-1]
print('Using: ' + latest.name)

print('Loading BMF...')
bmf = None
for kwargs in [{'low_memory': False}, {'low_memory': False, 'encoding': 'latin1'}, {'low_memory': False, 'sep': '	'}]:
    try:
        bmf = pd.read_csv(latest, **kwargs)
        if len(bmf.columns) > 3:
            print('Loaded: ' + str(len(bmf)) + ' rows')
            break
    except Exception as e:
        print('Failed: ' + str(e)[:60])

if bmf is None:
    print('ERROR')
    sys.exit(1)

print('Filtering...')
if 'RULING' in bmf.columns:
    bmf['RULING_YEAR'] = pd.to_numeric(bmf['RULING'].astype(str).str[:4], errors='coerce')
    bmf['AGE_YEARS'] = datetime.now().year - bmf['RULING_YEAR']
else:
    bmf['AGE_YEARS'] = 999

rev_col = None
for col in ['REVENUE_AMT', 'INCOME_AMT', 'TOTREV']:
    if col in bmf.columns:
        rev_col = col
        break

if rev_col:
    bmf['REVENUE_AMT'] = pd.to_numeric(bmf[rev_col], errors='coerce')
else:
    bmf['REVENUE_AMT'] = 0

mask = pd.Series([True] * len(bmf))
if 'SUBSECCD' in bmf.columns:
    mask &= bmf['SUBSECCD'].astype(str) == '03'
if 'STATUS' in bmf.columns:
    mask &= bmf['STATUS'].astype(str) == '01'
mask &= bmf['AGE_YEARS'] >= 3
mask &= bmf['REVENUE_AMT'] >= 50000
mask &= bmf['REVENUE_AMT'] <= 100000000
if 'FOUNDATION' in bmf.columns:
    mask &= ~bmf['FOUNDATION'].astype(str).isin(['15', '16'])

filtered = bmf[mask].copy()
print('Before: ' + str(len(bmf)) + ' | After: ' + str(len(filtered)))

print('Building database...')
if DB_PATH.exists():
    DB_PATH.unlink()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

c.execute('CREATE TABLE registry_enriched (EIN TEXT PRIMARY KEY, NAME TEXT, STATE TEXT, CITY TEXT, ZIP TEXT, NTEE1 TEXT, SUBSECCD TEXT, STATUS TEXT, RULING TEXT, RULING_YEAR INTEGER, AGE_YEARS INTEGER, REVENUE_AMT REAL, ASSET_AMT REAL, INCOME_AMT REAL, FOUNDATION TEXT)')

cols = []
for col in ['EIN', 'NAME', 'STATE', 'CITY', 'ZIP', 'NTEE1', 'SUBSECCD', 'STATUS', 'RULING', 'RULING_YEAR', 'AGE_YEARS', 'REVENUE_AMT', 'ASSET_AMT', 'INCOME_AMT', 'FOUNDATION']:
    if col in filtered.columns:
        cols.append(col)

ph = ','.join(['?'] * len(cols))
sql = 'INSERT INTO registry_enriched (' + ','.join(cols) + ') VALUES (' + ph + ')'
rows = filtered[cols].values.tolist()

for i in range(0, len(rows), 5000):
    c.executemany(sql, rows[i:i+5000])

conn.commit()
c.execute('SELECT COUNT(*) FROM registry_enriched')
count = c.fetchone()[0]
print('Registry: ' + str(count) + ' rows')

c.execute('CREATE INDEX idx_state ON registry(STATE)')
c.execute('CREATE INDEX idx_ntee ON registry(NTEE1)')
c.execute('CREATE INDEX idx_revenue ON registry(REVENUE_AMT)')
conn.commit()

print('Scoring...')
c.execute('CREATE TABLE scores (EIN TEXT PRIMARY KEY, program_expense_ratio REAL, admin_overhead_ratio REAL, fundraising_efficiency REAL, asset_growth_rate REAL, liquidity_proxy REAL, merit_score REAL, revenue_band TEXT)')

c.execute('SELECT EIN, REVENUE_AMT, ASSET_AMT FROM registry_enriched')
rows = c.fetchall()

score_rows = []
for ein, revenue, assets in rows:
    revenue = float(revenue or 0)
    assets = float(assets or 0)
    per = 0.75
    aor = 0.25
    fe = 20.0
    liq = assets / (revenue / 12) if revenue > 0 else 6.0
    s_per = min(100, max(0, per * 100))
    s_fe = min(100, max(0, (fe / 20) * 100))
    s_agr = 50
    s_liq = min(100, max(0, liq * 10))
    merit = round(s_per * 0.35 + s_fe * 0.20 + s_agr * 0.25 + s_liq * 0.20, 1)
    if revenue < 100000: band = 'small'
    elif revenue < 500000: band = 'medium'
    elif revenue < 1000000: band = 'large'
    elif revenue < 5000000: band = 'major'
    else: band = 'mega'
    score_rows.append((ein, per, aor, fe, 0.0, liq, merit, band))

sql = 'INSERT INTO scores VALUES (?,?,?,?,?,?,?,?)'
for i in range(0, len(score_rows), 5000):
    c.executemany(sql, score_rows[i:i+5000])

conn.commit()
c.execute('SELECT COUNT(*) FROM scores')
score_count = c.fetchone()[0]
c.execute('SELECT MIN(merit_score), MAX(merit_score), AVG(merit_score) FROM scores')
min_s, max_s, avg_s = c.fetchone()

print('=' * 60)
print('COMPLETE')
print('=' * 60)
print('Registry: ' + str(count) + ' orgs')
print('Scores:   ' + str(score_count) + ' orgs')
print('Score:    ' + str(round(min_s, 1)) + ' - ' + str(round(max_s, 1)))
conn.close()
