import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'meritgiving.db'
conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

print('=' * 60)
print('MeritGiving Rescore Trigger v2.1')
print('=' * 60)

c.execute('SELECT COUNT(*) FROM registry_enriched')
current_count = c.fetchone()[0]
print('Current registry: ' + str(current_count) + ' orgs')

c.execute("SELECT row_count FROM data_freshness WHERE table_name = 'scores'")
row = c.fetchone()
last_count = row[0] if row else 0
print('Last rescore: ' + str(last_count) + ' orgs')

delta = current_count - last_count
print('Delta: ' + str(delta) + ' orgs')

if delta < 10000:
    print('Delta < 10,000. Skipping rescore.')
    conn.close()
    exit(0)

print('Delta >= 10,000. Running rescore...')

df = pd.read_sql('SELECT EIN, REVENUE_AMT, ASSET_AMT, NTEE1 FROM registry_enriched', conn)
score_rows = []

for _, row in df.iterrows():
    revenue = float(row['REVENUE_AMT'] or 0)
    assets = float(row['ASSET_AMT'] or 0)
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
    score_rows.append((row['EIN'], per, aor, fe, 0.0, liq, merit, band, datetime.now().isoformat(), '2.1', 'revenue:0.35,liquidity:0.30,size:0.25,ntee_bonus:0.10'))

c.execute('DELETE FROM scores')
sql = 'INSERT INTO scores (EIN, program_expense_ratio, admin_overhead_ratio, fundraising_efficiency, asset_growth_rate, liquidity_proxy, merit_score, revenue_band, scored_at, score_version, model_weights) VALUES (?,?,?,?,?,?,?,?,?,?,?)'
for i in range(0, len(score_rows), 5000):
    c.executemany(sql, score_rows[i:i+5000])

conn.commit()

c.execute('DELETE FROM percentiles')
pct_df = pd.read_sql('SELECT r.EIN, r.NTEE1, s.revenue_band, s.merit_score FROM registry_enriched r JOIN scores s ON r.EIN = s.EIN', conn)
pct_df['ntee_major'] = pct_df['NTEE1'].astype(str).str[:1]
pct_df['peer_percentile'] = pct_df.groupby(['ntee_major', 'revenue_band'])['merit_score'].rank(pct=True) * 100
pct_df['peer_percentile'] = pct_df['peer_percentile'].round(0).astype(int)
pct_df['national_percentile'] = pct_df['merit_score'].rank(pct=True) * 100
pct_df['national_percentile'] = pct_df['national_percentile'].round(0).astype(int)

def tier(pct):
    if pct >= 90: return 'Flagship'
    elif pct >= 75: return 'High-Impact'
    elif pct >= 50: return 'Established'
    elif pct >= 25: return 'Emerging'
    else: return 'Developing'

pct_df['tier'] = pct_df['peer_percentile'].apply(tier)
pct_rows = pct_df[['EIN', 'peer_percentile', 'national_percentile', 'tier']].values.tolist()
c.executemany('INSERT INTO percentiles VALUES (?,?,?,?)', pct_rows)

conn.commit()

c.execute("INSERT OR REPLACE INTO data_freshness VALUES (?, datetime('now'), NULL, ?, ?, ?)", ('scores', len(score_rows), 'auto_rescore', 'Triggered at ' + str(current_count) + ' orgs'))

conn.commit()
conn.close()

print('=' * 60)
print('Rescore complete: ' + str(len(score_rows)) + ' orgs rescored')
print('=' * 60)
