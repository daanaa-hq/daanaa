#!/usr/bin/env python3
"""
join_nccs_to_registry.py

Pulls key fields from nccs_core_2019 (801K rows, multiple years per EIN)
into registry_enriched, using the most recent FISYR per EIN.

Fields added:
  employee_count   - NOEMPLYEESW3CNT (W-3 form employee count)
  activ1           - primary NTEE activity code (3-digit)
  activ2           - secondary activity code
  activ3           - tertiary activity code
  program_expense_pct - program service as % of total expenses (efficiency metric)
  nccs_year        - fiscal year the NCCS data is from
"""
import sqlite3
from pathlib import Path

DB = Path.home() / "meritgiving/data/merit_registry.db"
conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")

# Add columns
NEW_COLS = [
    ("employee_count",      "INTEGER"),
    ("activ1",              "TEXT"),
    ("activ2",              "TEXT"),
    ("activ3",              "TEXT"),
    ("program_expense_pct", "REAL"),   # pct expenses going to programs
    ("nccs_year",           "INTEGER"),
]
for col, typ in NEW_COLS:
    try:
        conn.execute(f"ALTER TABLE registry_enriched ADD COLUMN {col} {typ}")
    except Exception:
        pass
conn.commit()
print("Columns added. Running join...")

# Materialize best NCCS row per EIN into a temp table
conn.execute("DROP TABLE IF EXISTS _nccs_best")
conn.execute("""
    CREATE TEMP TABLE _nccs_best AS
    SELECT EIN,
           NOEMPLYEESW3CNT               as empl,
           CAST(ACTIV1 AS TEXT)          as a1,
           CAST(ACTIV2 AS TEXT)          as a2,
           CAST(ACTIV3 AS TEXT)          as a3,
           FISYR                         as yr,
           EXPS                          as tot_exp,
           PROGREV                       as prog_rev
    FROM nccs_core_2019
    WHERE (EIN, FISYR) IN (
        SELECT EIN, MAX(FISYR) FROM nccs_core_2019 GROUP BY EIN
    )
""")
print("Temp table built.")

# Compute program_expense_pct: program revenue as % of total expenses (proxy)
conn.execute("""
    UPDATE _nccs_best
    SET prog_rev = CASE
        WHEN tot_exp > 0 AND prog_rev IS NOT NULL THEN ROUND(prog_rev * 100.0 / tot_exp, 1)
        ELSE NULL
    END
""")

# Apply to registry_enriched
result = conn.execute("""
    UPDATE registry_enriched
    SET employee_count      = COALESCE(employee_count, (SELECT empl FROM _nccs_best n WHERE n.EIN = registry_enriched.EIN AND empl > 0)),
        activ1              = COALESCE(activ1,          (SELECT a1   FROM _nccs_best n WHERE n.EIN = registry_enriched.EIN)),
        activ2              = COALESCE(activ2,          (SELECT a2   FROM _nccs_best n WHERE n.EIN = registry_enriched.EIN)),
        activ3              = COALESCE(activ3,          (SELECT a3   FROM _nccs_best n WHERE n.EIN = registry_enriched.EIN)),
        program_expense_pct = COALESCE(program_expense_pct, (SELECT prog_rev FROM _nccs_best n WHERE n.EIN = registry_enriched.EIN)),
        nccs_year           = COALESCE(nccs_year,       (SELECT yr   FROM _nccs_best n WHERE n.EIN = registry_enriched.EIN))
    WHERE EXISTS (SELECT 1 FROM _nccs_best n WHERE n.EIN = registry_enriched.EIN)
""")
conn.commit()

rows_updated = result.rowcount
print(f"Updated {rows_updated:,} rows in registry_enriched.")

# Stats
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
print(f"  Orgs with employee count: {stats[1]:,} ({stats[2]:,} non-zero, avg {stats[3]})")
print(f"  Orgs with program expense %: {stats[4]:,} (avg {stats[5]}%)")
conn.close()
print("\nDone.")
