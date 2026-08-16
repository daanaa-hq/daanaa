import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

HOME = Path.home()
DATA_DIR = HOME / "Meritgiving" / "NCCS Monthly DAta"
DB_PATH = HOME / "meritgiving" / "data" / "meritgiving.db"

print("=" * 60)
print("MeritGiving Clean Rebuild")
print("=" * 60)

master = DATA_DIR / "bmf_master.csv"
print("Using: " + master.name)

print("Loading...")
bmf = pd.read_csv(master, low_memory=False)
print("Loaded: " + str(len(bmf)) + " rows")

print("Filtering...")

# Age
if "ruling_date" in bmf.columns:
    bmf["RULING_YEAR"] = pd.to_numeric(bmf["ruling_date"].astype(str).str[:4], errors="coerce")
    bmf["AGE_YEARS"] = datetime.now().year - bmf["RULING_YEAR"]
else:
    bmf["AGE_YEARS"] = 999

# Revenue (use income_amount — better coverage)
bmf["REVENUE_AMT"] = pd.to_numeric(bmf.get("income_amount", 0), errors="coerce").fillna(0)

# Base filters
mask = pd.Series([True] * len(bmf))
mask &= bmf["AGE_YEARS"] >= 3
mask &= bmf["REVENUE_AMT"] >= 50000
mask &= bmf["REVENUE_AMT"] <= 100000000

# 501(c)(3) only
if "subsection_code" in bmf.columns:
    mask &= bmf["subsection_code"] == 3.0

# Active only
if "status_code" in bmf.columns:
    mask &= bmf["status_code"] == 1.0

# Exclude private foundations by foundation_code
if "foundation_code" in bmf.columns:
    mask &= ~bmf["foundation_code"].isin([15.0, 16.0])

# Exclude private foundations by NTEE
if "ntee_code_clean" in bmf.columns:
    ntee = bmf["ntee_code_clean"].astype(str)
    # T20 = Private Grantmaking, T22 = Community Foundations, T30 = Public Foundations
    mask &= ~ntee.str.startswith("T2")
    mask &= ~ntee.str.startswith("T3")

# Exclude bad NTEE for public-facing data
if "ntee_code_clean" in bmf.columns:
    ntee = bmf["ntee_code_clean"].astype(str)
    mask &= (ntee != "UNDEFINED") & (ntee != "INVALID") & (ntee != "nan")

filtered = bmf[mask].copy()
print("Before: " + str(len(bmf)) + " | After: " + str(len(filtered)))

if len(filtered) == 0:
    print("ERROR: No orgs passed filters")
    exit(1)

if DB_PATH.exists():
    DB_PATH.unlink()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

c.execute("CREATE TABLE registry_enriched (EIN TEXT PRIMARY KEY, NAME TEXT, STATE TEXT, CITY TEXT, ZIP TEXT, NTEE1 TEXT, SUBSECCD TEXT, STATUS TEXT, RULING TEXT, RULING_YEAR INTEGER, AGE_YEARS INTEGER, REVENUE_AMT REAL, ASSET_AMT REAL, INCOME_AMT REAL, FOUNDATION TEXT)")

cols = []
for col in ["EIN", "NAME", "STATE", "CITY", "ZIP", "NTEE1", "SUBSECCD", "STATUS", "RULING", "RULING_YEAR", "AGE_YEARS", "REVENUE_AMT", "ASSET_AMT", "INCOME_AMT", "FOUNDATION"]:
    src = {"EIN": "ein", "NAME": "org_name_display", "STATE": "org_addr_state", "CITY": "org_addr_city", "ZIP": "org_addr_zip5", "NTEE1": "ntee_code_clean", "SUBSECCD": "subsection_code", "STATUS": "status_code", "RULING": "ruling_date", "RULING_YEAR": "RULING_YEAR", "AGE_YEARS": "AGE_YEARS", "REVENUE_AMT": "REVENUE_AMT", "ASSET_AMT": "asset_amount", "INCOME_AMT": "income_amount", "FOUNDATION": "foundation_code"}.get(col, col)
    if src in filtered.columns:
        cols.append((src, col))

insert_df = filtered[[src for src, dst in cols]].copy()
insert_df.columns = [dst for src, dst in cols]

ph = ",".join(["?"] * len(cols))
sql = "INSERT INTO registry_enriched (" + ",".join([dst for src, dst in cols]) + ") VALUES (" + ph + ")"
rows = insert_df.values.tolist()

for i in range(0, len(rows), 5000):
    c.executemany(sql, rows[i:i+5000])

conn.commit()
c.execute("SELECT COUNT(*) FROM registry_enriched")
count = c.fetchone()[0]
print("Registry: " + str(count) + " rows")

c.execute("CREATE INDEX idx_state ON registry(STATE)")
c.execute("CREATE INDEX idx_ntee ON registry(NTEE1)")
c.execute("CREATE INDEX idx_revenue ON registry(REVENUE_AMT)")
conn.commit()

# Better scoring using revenue bands and asset ratios
print("Scoring...")
c.execute("CREATE TABLE scores (EIN TEXT PRIMARY KEY, program_expense_ratio REAL, admin_overhead_ratio REAL, fundraising_efficiency REAL, asset_growth_rate REAL, liquidity_proxy REAL, merit_score REAL, revenue_band TEXT)")

c.execute("SELECT EIN, REVENUE_AMT, ASSET_AMT, NTEE1 FROM registry_enriched")
rows = c.fetchall()

# Compute percentiles for scoring
import numpy as np

score_rows = []
for ein, revenue, assets, ntee in rows:
    revenue = float(revenue or 0)
    assets = float(assets or 0)
    
    # Revenue band score (0-100)
    if revenue < 100000: rev_score = 20
    elif revenue < 250000: rev_score = 40
    elif revenue < 500000: rev_score = 60
    elif revenue < 1000000: rev_score = 75
    elif revenue < 5000000: rev_score = 90
    else: rev_score = 100
    
    # Liquidity score
    liq = assets / (revenue / 12) if revenue > 0 else 6.0
    liq_score = min(100, max(0, liq * 8))
    
    # Size stability (log scale)
    size_score = min(100, max(0, np.log10(revenue / 50000) * 25))
    
    # NTEE diversity bonus (less common = higher score for discovery)
    ntee_bonus = 10 if ntee and ntee[0] not in ["T", "B"] else 0
    
    # Composite
    merit = round(rev_score * 0.25 + liq_score * 0.30 + size_score * 0.35 + ntee_bonus * 0.10, 1)
    
    if revenue < 100000: band = "small"
    elif revenue < 500000: band = "medium"
    elif revenue < 1000000: band = "large"
    elif revenue < 5000000: band = "major"
    else: band = "mega"
    
    score_rows.append((ein, 0.75, 0.25, 20.0, 0.0, liq, merit, band))

sql = "INSERT INTO scores VALUES (?,?,?,?,?,?,?,?)"
for i in range(0, len(score_rows), 5000):
    c.executemany(sql, score_rows[i:i+5000])

conn.commit()
c.execute("SELECT COUNT(*) FROM scores")
score_count = c.fetchone()[0]
c.execute("SELECT MIN(merit_score), MAX(merit_score), AVG(merit_score), COUNT(DISTINCT merit_score) FROM scores")
min_s, max_s, avg_s, distinct = c.fetchone()

print("=" * 60)
print("COMPLETE")
print("=" * 60)
print("Registry: " + str(count) + " orgs")
print("Scores:   " + str(score_count) + " orgs")
print("Range:    " + str(round(min_s, 1)) + " - " + str(round(max_s, 1)))
print("Distinct: " + str(distinct) + " unique scores")
conn.close()
