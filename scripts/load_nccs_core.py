import pandas as pd
import sqlite3
import sys

DB = "data/merit_registry.db"
FILES = {
    "PC":     "data/corepcf/core_2019_pc.csv",
    "PZ":     "data/corepcf/core_2019_pz.csv",
    "OT_PZ":  "data/corepcf/core_2019_ot_pz.csv",
}

print("=== Loading NCCS Core 2019 ===")

# Read all three files, add scope tag, align columns
frames = []
for scope, path in FILES.items():
    print(f"Reading {scope} from {path} ...")
    try:
        df = pd.read_csv(path, dtype=str, low_memory=False)
    except Exception as e:
        print(f"ERROR reading {scope}: {e}")
        sys.exit(1)
    df.insert(0, "scope", scope)
    frames.append(df)
    print(f"  -> {len(df)} rows, {len(df.columns)} columns")

# Union them: missing columns auto-filled with NaN (becomes NULL in SQLite)
combined = pd.concat(frames, ignore_index=True, sort=False)
print(f"\nCombined: {len(combined)} rows, {len(combined.columns)} columns")

# Write to SQLite (replace existing table)
with sqlite3.connect(DB) as conn:
    combined.to_sql("nccs_core_2019", conn, if_exists="replace", index=False)
    
    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nccs_ein    ON nccs_core_2019(EIN)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nccs_ntee   ON nccs_core_2019(NTEE1)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nccs_state  ON nccs_core_2019(STATE)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nccs_scope  ON nccs_core_2019(scope)")
    conn.commit()

print("\n=== Done. Running audit ===")

# Audit
with sqlite3.connect(DB) as conn:
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM nccs_core_2019")
    print(f"Total rows:        {c.fetchone()[0]:,}")
    
    c.execute("SELECT COUNT(DISTINCT EIN) FROM nccs_core_2019")
    print(f"Unique EINs:       {c.fetchone()[0]:,}")
    
    for s in ["PC","PZ","OT_PZ"]:
        c.execute("SELECT COUNT(*) FROM nccs_core_2019 WHERE scope=?", (s,))
        print(f"{s:6} rows:       {c.fetchone()[0]:,}")
    
    c.execute("""
        SELECT COUNT(*) FROM (
            SELECT EIN FROM nccs_core_2019 WHERE scope='PC'
            INTERSECT
            SELECT EIN FROM nccs_core_2019 WHERE scope='PZ'
        )
    """)
    print(f"EINs in PC+PZ:     {c.fetchone()[0]:,}")
    
    c.execute("""
        SELECT NTEE1, COUNT(*) as n 
        FROM nccs_core_2019 
        WHERE scope='PC' AND NTEE1 IS NOT NULL 
        GROUP BY NTEE1 
        ORDER BY n DESC LIMIT 5
    """)
    print("\nTop 5 NTEE1 (PC):")
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]:,}")
    
    # Revenue coverage check
    c.execute("SELECT COUNT(*) FROM nccs_core_2019 WHERE scope='PC' AND (TOTREV IS NULL OR TOTREV='')")
    print(f"\nPC rows with blank TOTREV: {c.fetchone()[0]:,}")

