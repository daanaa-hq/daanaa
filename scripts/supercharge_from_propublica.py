#!/usr/bin/env python3
"""
supercharge_from_propublica.py

Extracts the full value from data/propublica_cache/*.json:
1. Org-level fields into registry_enriched new columns:
   ruling_date, accounting_period, deductibility_code, foundation_code,
   zipcode, address, net_assets, total_liabilities, total_expenses, months_of_reserve
2. Multi-year financial history into propublica_financials table
3. 990 PDF URLs into propublica_pdfs table

Run time: ~3-5 min for 45K files.
"""
import sqlite3, json, sys
from pathlib import Path

DB    = Path.home() / "meritgiving/data/merit_registry.db"
CACHE = Path.home() / "meritgiving/data/propublica_cache"

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")

# ── 1. Add new columns to registry_enriched (safe – ALTER TABLE IF NOT EXISTS is not
#       supported, so we try each and ignore errors)
NEW_COLS = [
    ("ruling_date",        "TEXT"),
    ("accounting_period",  "INTEGER"),  # fiscal year end month (1-12)
    ("foundation_code",    "INTEGER"),
    ("net_assets",         "REAL"),     # totnetassetend from most recent filing
    ("total_expenses",     "REAL"),     # totfuncexpns from most recent filing
    ("total_liabilities",  "REAL"),     # totliabend
    ("months_of_reserve",  "REAL"),     # (net_assets / monthly_expenses), capped
    ("zipcode",            "TEXT"),
    ("address",            "TEXT"),
]
for col, typ in NEW_COLS:
    try:
        conn.execute(f"ALTER TABLE registry_enriched ADD COLUMN {col} {typ}")
    except Exception:
        pass  # already exists
conn.commit()
print("Columns ready.")

# ── 2. Create propublica_financials table (multi-year history)
conn.execute("""
CREATE TABLE IF NOT EXISTS propublica_financials (
    EIN            TEXT    NOT NULL,
    tax_prd_yr     INTEGER NOT NULL,
    totrevenue     REAL,
    totfuncexpns   REAL,
    totassetsend   REAL,
    totliabend     REAL,
    totnetassetend REAL,
    totcntrbgfts   REAL,
    totprgmrevnue  REAL,
    compnsatncurrofcr REAL,
    pdf_url        TEXT,
    PRIMARY KEY (EIN, tax_prd_yr)
)""")
conn.execute("CREATE INDEX IF NOT EXISTS idx_ppf_ein ON propublica_financials(EIN)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_ppf_yr  ON propublica_financials(tax_prd_yr)")
conn.commit()
print("propublica_financials table ready.")

# ── 3. Main loop
files = sorted(CACHE.glob("*.json"))
print(f"Processing {len(files):,} cache files…\n")

updated = missing = empty = errors = 0
financials_inserted = 0

for i, f in enumerate(files):
    ein = f.stem
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        errors += 1
        continue

    org = data.get("organization") or {}
    filings = data.get("filings_with_data") or []

    # ── Org-level fields
    ruling_date      = org.get("ruling_date") or None
    acct_period      = org.get("accounting_period") or None
    foundation_code  = org.get("foundation_code") or None
    zipcode          = (org.get("zipcode") or "").strip() or None
    address          = (org.get("address") or "").strip() or None

    # ── From most recent filing
    net_assets   = total_expenses = total_liabilities = None
    if filings:
        recent = sorted(filings, key=lambda x: x.get("tax_prd_yr", 0) or 0, reverse=True)[0]
        net_assets       = recent.get("totnetassetend")
        total_expenses   = recent.get("totfuncexpns")
        total_liabilities = recent.get("totliabend")

    months_of_reserve = None
    if net_assets is not None and total_expenses and total_expenses > 0:
        monthly = total_expenses / 12.0
        months_of_reserve = round(net_assets / monthly, 2)
        months_of_reserve = max(-999.0, min(999.0, months_of_reserve))  # cap extremes

    row = conn.execute("SELECT EIN FROM registry_enriched WHERE EIN = ?", (ein,)).fetchone()
    if not row:
        missing += 1
    else:
        conn.execute("""
            UPDATE registry_enriched SET
                ruling_date       = COALESCE(ruling_date, ?),
                accounting_period = COALESCE(accounting_period, ?),
                foundation_code   = COALESCE(foundation_code, ?),
                net_assets        = CASE WHEN net_assets IS NULL THEN ? ELSE net_assets END,
                total_expenses    = CASE WHEN total_expenses IS NULL THEN ? ELSE total_expenses END,
                total_liabilities = CASE WHEN total_liabilities IS NULL THEN ? ELSE total_liabilities END,
                months_of_reserve = CASE WHEN months_of_reserve IS NULL THEN ? ELSE months_of_reserve END,
                zipcode           = COALESCE(zipcode, ?),
                address           = COALESCE(address, ?)
            WHERE EIN = ?
        """, (ruling_date, acct_period, foundation_code,
              net_assets, total_expenses, total_liabilities, months_of_reserve,
              zipcode, address, ein))
        updated += 1

    # ── Multi-year financials
    for fil in filings:
        yr = fil.get("tax_prd_yr")
        if not yr:
            continue
        try:
            conn.execute("""
                INSERT OR IGNORE INTO propublica_financials
                    (EIN, tax_prd_yr, totrevenue, totfuncexpns, totassetsend,
                     totliabend, totnetassetend, totcntrbgfts, totprgmrevnue,
                     compnsatncurrofcr, pdf_url)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (ein, yr,
                  fil.get("totrevenue"), fil.get("totfuncexpns"), fil.get("totassetsend"),
                  fil.get("totliabend"), fil.get("totnetassetend"), fil.get("totcntrbgfts"),
                  fil.get("totprgmrevnue"), fil.get("compnsatncurrofcr"),
                  fil.get("pdf_url")))
            financials_inserted += 1
        except Exception:
            pass

    if not ruling_date and not filings:
        empty += 1

    if (i + 1) % 5000 == 0:
        conn.commit()
        print(f"  {i+1:,}/{len(files):,}  "
              f"org_updated={updated:,}  financials={financials_inserted:,}  "
              f"missing={missing:,}")

conn.commit()
conn.close()

print(f"\n{'='*60}")
print(f"Done.")
print(f"  registry_enriched updated: {updated:,}")
print(f"  multi-year rows inserted:  {financials_inserted:,}")
print(f"  not in DB:                 {missing:,}")
print(f"  errors:                    {errors:,}")
print(f"\nNew columns: ruling_date, accounting_period, foundation_code,")
print(f"             net_assets, total_expenses, total_liabilities,")
print(f"             months_of_reserve, zipcode, address")
print(f"New table:   propublica_financials  ({financials_inserted:,} year×org rows)")
