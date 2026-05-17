#!/usr/bin/env python3
"""
join_nccs_to_registry_v2.py
Fast Python-side join of nccs_core_2019 → registry_enriched.
Avoids slow SQLite row-value IN subquery; reads NCCS in one pass.
"""
import sqlite3
from pathlib import Path

DB = Path.home() / "meritgiving/data/merit_registry.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA cache_size=-131072")  # 128MB

# Add columns (idempotent)
NEW_COLS = [
    ("employee_count",      "INTEGER"),
    ("activ1",              "TEXT"),
    ("activ2",              "TEXT"),
    ("activ3",              "TEXT"),
    ("program_expense_pct", "REAL"),
    ("nccs_year",           "INTEGER"),
]
for col, typ in NEW_COLS:
    try:
        conn.execute(f"ALTER TABLE registry_enriched ADD COLUMN {col} {typ}")
    except Exception:
        pass
conn.commit()
print("Columns ready.")

# Read nccs_core_2019 once, keep only the most recent FISYR per EIN
print("Reading nccs_core_2019 (801K rows)...")
best = {}  # ein -> (fisyr, empl, a1, a2, a3, prog_pct)

cursor = conn.execute("""
    SELECT EIN, FISYR,
           NOEMPLYEESW3CNT as empl,
           CAST(ACTIV1 AS TEXT) as a1,
           CAST(ACTIV2 AS TEXT) as a2,
           CAST(ACTIV3 AS TEXT) as a3,
           CAST(EXPS AS REAL) as tot_exp,
           CAST(PROGREV AS REAL) as prog_rev
    FROM nccs_core_2019
    ORDER BY EIN, FISYR ASC
""")

for row in cursor:
    ein  = row["EIN"]
    yr   = row["FISYR"] or 0
    empl = row["empl"]
    a1   = row["a1"]
    a2   = row["a2"]
    a3   = row["a3"]
    exp  = row["tot_exp"]
    prgrev = row["prog_rev"]

    prog_pct = None
    if exp and exp > 0 and prgrev is not None:
        prog_pct = round(prgrev * 100.0 / exp, 1)

    cur = best.get(ein)
    if cur is None or yr > cur[0]:
        best[ein] = (yr, empl, a1, a2, a3, prog_pct)

print(f"  {len(best):,} unique EINs in NCCS")

# Build batch updates
batch = []
for ein, (yr, empl, a1, a2, a3, prog_pct) in best.items():
    try:
        empl_int = int(empl) if empl else 0
    except (TypeError, ValueError):
        empl_int = 0
    empl_val = empl_int if empl_int > 0 else None
    batch.append((empl_val, a1, a2, a3, prog_pct, yr, ein))

print(f"Applying {len(batch):,} updates to registry_enriched...")

# Process in chunks
CHUNK = 5000
for i in range(0, len(batch), CHUNK):
    conn.executemany("""
        UPDATE registry_enriched
        SET employee_count      = COALESCE(employee_count, ?),
            activ1              = COALESCE(activ1, ?),
            activ2              = COALESCE(activ2, ?),
            activ3              = COALESCE(activ3, ?),
            program_expense_pct = COALESCE(program_expense_pct, ?),
            nccs_year           = COALESCE(nccs_year, ?)
        WHERE EIN = ?
    """, batch[i:i+CHUNK])
    if (i // CHUNK) % 20 == 0:
        conn.commit()
        print(f"  {i+len(batch[i:i+CHUNK]):,}/{len(batch):,} processed")

conn.commit()

stats = conn.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(employee_count) as has_empl,
        COUNT(CASE WHEN employee_count > 0 THEN 1 END) as nonzero_empl,
        ROUND(AVG(CASE WHEN employee_count > 0 THEN employee_count END), 1) as avg_empl,
        COUNT(program_expense_pct) as has_pct,
        ROUND(AVG(program_expense_pct), 1) as avg_prog_pct
    FROM registry_enriched
""").fetchone()

print(f"\nStats:")
print(f"  Employee count: {stats[1]:,} orgs ({stats[2]:,} non-zero, avg {stats[3]})")
print(f"  Program expense %: {stats[4]:,} orgs (avg {stats[5]}%)")
conn.close()
print("\nDone.")
