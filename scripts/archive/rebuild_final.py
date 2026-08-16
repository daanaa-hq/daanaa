import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

HOME = Path.home()
DATA_DIR = HOME / "Meritgiving" / "NCCS Monthly DAta"
DB_PATH = HOME / "meritgiving" / "data" / "meritgiving.db"

print("=" * 60)
print("MeritGiving Rebuild")
print("=" * 60)

if not DATA_DIR.exists():
    print("ERROR: Data dir not found: " + str(DATA_DIR))
    exit(1)

master = DATA_DIR / "bmf_master.csv"
if master.exists():
    print("Using MASTER file")
    latest = master
else:
    all_csvs = sorted(DATA_DIR.glob("*.csv"))
    processed = [f for f in all_csvs if "_processed" in f.name and f.name.startswith("bmf_") and "(1)" not in f.name]
    latest = sorted(processed)[-1]
    print("Using: " + latest.name)

print("Loading...")
bmf = pd.read_csv(latest, low_memory=False)
print("Loaded: " + str(len(bmf)) + " rows, " + str(len(bmf.columns)) + " columns")

print("Filtering...")
if "RULING" in bmf.columns:
    bmf["RULING_YEAR"] = pd.to_numeric(bmf["RULING"].astype(str).str[:4], errors="coerce")
    bmf["AGE_YEARS"] = datetime.now().year - bmf["RULING_YEAR"]
else:
    bmf["AGE_YEARS"] = 999

rev_col = "REVENUE_AMT" if "REVENUE_AMT" in bmf.columns else ("INCOME_AMT" if "INCOME_AMT" in bmf.columns else "TOTREV")
bmf["REVENUE_AMT"] = pd.to_numeric(bmf[rev_col], errors="coerce")

mask = pd.Series([True] * len(bmf))
if "SUBSECCD" in bmf.columns: mask &= bmf["SUBSECCD"].astype(str) == "03"
if "STATUS" in bmf.columns: mask &= bmf["STATUS"].astype(str) == "01"
mask &= bmf["AGE_YEARS"] >= 3
mask &= bmf["REVENUE_AMT"] >= 50000
mask &= bmf["REVENUE_AMT"] <= 100000000
if "FOUNDATION" in bmf.columns: mask &= ~bmf["FOUNDATION"].astype(str).isin(["15", "16"])

filtered = bmf[mask].copy()
print("Before: " + str(len(bmf)) + " | After: " + str(len(filtered)))

print("Building database...")
if DB_PATH.exists(): DB_PATH.unlink()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

c.execute("CREATE TABLE registry_enriched (EIN TEXT PRIMARY KEY, NAME TEXT, STATE TEXT, CITY TEXT, ZIP TEXT, NTEE1 TEXT, SUBSECCD TEXT, STATUS TEXT, RULING TEXT, RULING_YEAR INTEGER, AGE_YEARS INTEGER, REVENUE_AMT REAL, ASSET_AMT REAL, INCOME_AMT REAL, FOUNDATION TEXT)")

cols = []
for col in ["EIN", "NAME", "STATE", "CITY", "ZIP", "NTEE1", "SUBSECCD", "STATUS", "RULING", "RULING_YEAR", "AGE_YEARS", "REVENUE_AMT", "ASSET_AMT", "INCOME_AMT", "FOUNDATION"]:
    if col in filtered.columns: cols.append(col)

ph = ",".join(["?"] * len(cols))
sql = "INSERT INTO registry_enriched (" + ",".join(cols) + ") VALUES (" + ph + ")"
rows = filtered[cols].values.tolist()

for i in range(0, len(rows), 5000):
    c.executemany(sql, rows[i:i+5000])
    if (i // 5000) % 10 == 0: print("  " + str(i) + " / " + str(len(rows)))

conn.commit()
c.execute("SELECT COUNT(*) FROM registry_enriched")
count = c.fetchone()[0]
print("Registry: " + str(count) + " rows")

c.execute("CREATE INDEX idx_state ON registry(STATE)")
c.execute("CREATE INDEX idx_ntee ON registry(NTEE1)")
c.execute("CREATE INDEX idx_revenue ON registry(REVENUE_AMT)")
conn.commit()

print("Scoring...")
c.execute("CREATE TABLE scores (EIN TEXT PRIMARY KEY, program_expense_ratio REAL, admin_overhead_ratio REAL, fundraising_efficiency REAL, asset_growth_rate REAL, liquidity_proxy REAL, merit_score REAL, revenue_band TEXT)")

c.execute("SELECT EIN, REVENUE_AMT, ASSET_AMT FROM registry_enriched")
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
    if revenue < 100000: band = "small"
    elif revenue < 500000: band = "medium"
    elif revenue < 1000000: band = "large"
    elif revenue < 5000000: band = "major"
    else: band = "mega"
    score_rows.append((ein, per, aor, fe, 0.0, liq, merit, band))

sql = "INSERT INTO scores VALUES (?,?,?,?,?,?,?,?)"
for i in range(0, len(score_rows), 5000):
    c.executemany(sql, score_rows[i:i+5000])

conn.commit()
c.execute("SELECT COUNT(*) FROM scores")
score_count = c.fetchone()[0]
c.execute("SELECT MIN(merit_score), MAX(merit_score), AVG(merit_score) FROM scores")
min_s, max_s, avg_s = c.fetchone()

print("=" * 60)
print("COMPLETE")
print("=" * 60)
print("Registry: " + str(count) + " orgs")
print("Scores:   " + str(score_count) + " orgs")
print("Score:    " + str(round(min_s, 1)) + " - " + str(round(max_s, 1)))
conn.close()
