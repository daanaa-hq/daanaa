#!/usr/bin/env python3
import sqlite3, polars as pl, os, sys
from pathlib import Path

DB = Path.home() / "meritgiving/data/meritgiving.db"
DATA_DIR = Path.home() / "meritgiving/data/corepcf"

# ============================================================================
# 1. PEEK HEADERS
# ============================================================================
print("=" * 60)
print("STEP 1: Peeking headers")
print("=" * 60)

files = {
    "core_2019_pz":    DATA_DIR / "core_2019_pz.csv",
    "core_2019_pc":    DATA_DIR / "core_2019_pc.csv",
    "core_2019_ot_pz": DATA_DIR / "core_2019_ot_pz.csv",
}

WANTED_MAP = {
    "EIN": ["EIN", "ORG_EIN"],
    "NAME": ["NAME", "ORG_NAME", "ORGANIZATION_NAME"],
    "NTEE": ["NTEE", "NTEECC", "NTEE_CODE", "NTEE1"],
    "REVENUE": ["REVENUE", "TOTALREV", "TOTREV", "TOTAL_REVENUE", "TOTREV2"],
    "ASSETS": ["ASSETS", "TOTALASSETS", "TOTASSETS", "TOTAL_ASSETS", "TOTASSET"],
    "STATE": ["STATE", "ORG_STATE", "ST", "STATE2"],
    "CITY": ["CITY", "ORG_CITY", "CITY2"],
    "ZIP": ["ZIP", "ZIP5", "ORG_ZIP", "ZIPCD"],
}

def find_columns(actual_cols, wanted_map):
    actual_upper = {c.upper(): c for c in actual_cols}
    found = {}
    for want, candidates in wanted_map.items():
        for cand in candidates:
            if cand.upper() in actual_upper:
                found[want] = actual_upper[cand.upper()]
                break
    return found

file_cols = {}
for name, path in files.items():
    if not path.exists():
        print(f"[SKIP] {name}: not found")
        continue
    header_df = pl.read_csv(path, n_rows=0, infer_schema_length=0)
    actual = header_df.columns
    print(f"\n>>> {name} | Total cols: {len(actual)}")
    found = find_columns(actual, WANTED_MAP)
    for want, actual_col in found.items():
        print(f"    {want:10s} → {actual_col}")
    file_cols[name] = found

if not file_cols:
    print("No valid files. Exiting.")
    sys.exit(1)

# ============================================================================
# 2. READ ONLY NEEDED COLUMNS AS STRINGS
# ============================================================================
print("\n" + "=" * 60)
print("STEP 2: Loading selected columns as strings")
print("=" * 60)

dfs = {}
for name, path in files.items():
    if name not in file_cols:
        continue
    found = file_cols[name]
    if not found:
        print(f"[SKIP] {name}: no matching columns")
        continue
    
    cols_to_read = list(found.values())
    print(f"\n>>> Reading {name} — columns: {cols_to_read}")
    
    df = pl.read_csv(
        path,
        columns=cols_to_read,
        schema_overrides={c: pl.Utf8 for c in cols_to_read},
        low_memory=True,
        n_threads=8
    )
    print(f"    Rows: {df.height:,}")
    
    rename_map = {v: k for k, v in found.items()}
    df = df.rename(rename_map)
    
    for want in WANTED_MAP.keys():
        if want not in df.columns:
            df = df.with_columns(pl.lit(None).cast(pl.Utf8).alias(want))
    
    dfs[name] = df

# ============================================================================
# 3. STACK & CLEAN (NULL-SAFE)
# ============================================================================
print("\n" + "=" * 60)
print("STEP 3: Cleaning data (null-safe)")
print("=" * 60)

def safe_str(col, expr):
    return pl.when(pl.col(col).is_not_null()).then(expr).otherwise(None)

def clean_df(df, source_tag):
    keep = ["EIN", "NAME", "NTEE", "REVENUE", "ASSETS", "STATE", "CITY", "ZIP"]
    df = df.select([c for c in keep if c in df.columns])
    
    df = df.with_columns([
        pl.lit(source_tag).alias("SOURCE"),
        pl.lit("2019").alias("TAX_YEAR")
    ])
    
    df = df.with_columns(
        safe_str("EIN", pl.col("EIN").str.replace_all(r"[^0-9]", "").str.zfill(9)).alias("EIN")
    )
    df = df.with_columns(
        safe_str("NAME", pl.col("NAME").str.strip_chars().str.to_titlecase()).alias("NAME")
    )
    df = df.with_columns(
        safe_str("NTEE", pl.col("NTEE").str.to_uppercase().str.slice(0, 3)).alias("NTEE")
    )
    df = df.with_columns(
        safe_str("STATE", pl.col("STATE").str.to_uppercase().str.slice(0, 2)).alias("STATE")
    )
    df = df.with_columns(
        safe_str("CITY", pl.col("CITY").str.strip_chars().str.to_titlecase()).alias("CITY")
    )
    df = df.with_columns(
        safe_str("ZIP", pl.col("ZIP").str.replace_all(r"[^0-9]", "").str.slice(0, 5)).alias("ZIP")
    )
    
    for num_col in ["REVENUE", "ASSETS"]:
        if num_col in df.columns:
            df = df.with_columns(
                pl.when(pl.col(num_col).is_not_null())
                .then(
                    pl.col(num_col)
                    .str.replace_all(r"[$,]", "")
                    .str.replace_all(r"\.0+$", "")
                    .cast(pl.Int64, strict=False)
                )
                .otherwise(None)
                .alias(num_col)
            )
    
    df = df.filter(pl.col("EIN").is_not_null() & (pl.col("EIN") != ""))
    return df

cleaned = []
for name, df in dfs.items():
    tag = name.replace("core_", "").replace("_", "-").upper()
    c = clean_df(df, tag)
    print(f"    {name}: {c.height:,} rows after clean")
    cleaned.append(c)

if not cleaned:
    print("No data to process. Exiting.")
    sys.exit(1)

stacked = pl.concat(cleaned, how="diagonal")
print(f"\nTotal stacked: {stacked.height:,}")

# ============================================================================
# 4. DEDUPE BY EIN (keep max revenue)
# ============================================================================
print("\n" + "=" * 60)
print("STEP 4: Deduplicating by EIN")
print("=" * 60)

before = stacked.height
deduped = stacked.sort("REVENUE", descending=True, nulls_last=True).unique(subset=["EIN"], keep="first")
after = deduped.height
print(f"    Before: {before:,} | After: {after:,} | Removed: {before - after:,}")

# ============================================================================
# 5. WRITE TO SQLITE (direct from Polars, no pandas/pyarrow)
# ============================================================================
print("\n" + "=" * 60)
print("STEP 5: Writing to SQLite")
print("=" * 60)

DB.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(str(DB), timeout=30)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")

conn.execute("DROP TABLE IF EXISTS core_2019_staging")
conn.execute("""
CREATE TABLE core_2019_staging (
    EIN TEXT PRIMARY KEY,
    NAME TEXT,
    NTEE TEXT,
    REVENUE INTEGER,
    ASSETS INTEGER,
    STATE TEXT,
    CITY TEXT,
    ZIP TEXT,
    TAX_YEAR TEXT,
    SOURCE TEXT
)
""")

# Stream directly from Polars — no pandas, no pyarrow
cols = ["EIN", "NAME", "NTEE", "REVENUE", "ASSETS", "STATE", "CITY", "ZIP", "TAX_YEAR", "SOURCE"]
batch_size = 50000
total = 0

for batch in deduped.iter_slices(batch_size):
    rows = list(batch.iter_rows(named=False))
    conn.executemany("""
        INSERT OR REPLACE INTO core_2019_staging 
        (EIN, NAME, NTEE, REVENUE, ASSETS, STATE, CITY, ZIP, TAX_YEAR, SOURCE)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    total += len(rows)
    print(f"    Batch: {total:,} / {after:,}")

conn.commit()
print(f"    Written {total:,} rows to core_2019_staging")

# ============================================================================
# 6. MERGE INTO MASTER REGISTRY
# ============================================================================
print("\n" + "=" * 60)
print("STEP 6: Merging INTO registry_enriched")
print("=" * 60)

conn.execute("DROP TABLE IF EXISTS registry")
conn.execute("""
CREATE TABLE IF NOT EXISTS registry (
    EIN TEXT PRIMARY KEY,
    NAME TEXT,
    NTEE TEXT,
    REVENUE INTEGER,
    ASSETS INTEGER,
    STATE TEXT,
    CITY TEXT,
    ZIP TEXT,
    SOURCE TEXT,
    FIRST_SEEN TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

conn.execute("""
INSERT OR REPLACE INTO registry_enriched (EIN, NAME, NTEE, REVENUE, ASSETS, STATE, CITY, ZIP, SOURCE)
SELECT EIN, NAME, NTEE, REVENUE, ASSETS, STATE, CITY, ZIP, 
       'CORE-2019-' || SOURCE
FROM core_2019_staging
""")
conn.commit()

merged = conn.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
print(f"    Registry total: {merged:,}")

# ============================================================================
# 7. REVENUE PERCENTILES BY NTEE
# ============================================================================
print("\n" + "=" * 60)
print("STEP 7: Building NTEE revenue percentiles")
print("=" * 60)

conn.execute("DROP TABLE IF EXISTS ntee_percentiles")
conn.execute("""
CREATE TABLE ntee_percentiles AS
WITH ranked AS (
    SELECT 
        NTEE,
        REVENUE,
        NTILE(100) OVER (PARTITION BY NTEE ORDER BY REVENUE) as pctile
    FROM registry_enriched
    WHERE REVENUE IS NOT NULL AND NTEE IS NOT NULL AND NTEE != ''
)
SELECT NTEE, pctile, 
       MIN(REVENUE) as rev_min, 
       MAX(REVENUE) as rev_max,
       AVG(REVENUE) as rev_avg,
       COUNT(*) as org_count
FROM ranked
GROUP BY NTEE, pctile
""")
conn.commit()

ntees = conn.execute("SELECT COUNT(DISTINCT NTEE) FROM ntee_percentiles").fetchone()[0]
print(f"    Built percentiles for {ntees:,} NTEE categories")

# ============================================================================
# 8. SUMMARY
# ============================================================================
print("\n" + "=" * 60)
print("STEP 8: Summary")
print("=" * 60)

stats = conn.execute("""
SELECT 
    COUNT(*) as total_orgs,
    COUNT(DISTINCT NTEE) as ntee_categories,
    COUNT(DISTINCT STATE) as states,
    SUM(REVENUE) as total_revenue,
    AVG(REVENUE) as avg_revenue,
    SUM(ASSETS) as total_assets
FROM registry_enriched
""").fetchone()

print(f"    Total orgs:      {stats[0]:,}")
print(f"    NTEE categories: {stats[1]:,}")
print(f"    States:          {stats[2]}")
print(f"    Total revenue:   ${stats[3]:,.0f}")
print(f"    Avg revenue:     ${stats[4]:,.0f}")
print(f"    Total assets:    ${stats[5]:,.0f}")

conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
conn.close()
print("\n" + "=" * 60)
print("DONE. Ready for GPU embeddings next.")
print("=" * 60)
