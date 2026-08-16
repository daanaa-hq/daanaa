#!/usr/bin/env python3
"""
Sandbox validation for a fresh IRS BMF refresh.

Runs the exact import_bmf_orgs.py logic (INSERT OR IGNORE, 501c3 + deductible
only) against a SANDBOX COPY of merit_registry.db — never the live DB — then
reports what *would* change so we can eyeball alignment before applying to prod:

  - new orgs that would be added (count + NTEE1 / state breakdown + samples)
  - field-alignment sanity checks (EIN format, missing names, NTEE coverage)
  - revocation / gap signal: orgs we already have whose EIN is absent from the
    new BMF (candidate revocations or filers that dropped out of the EO file)

Usage:
  python3 scripts/sandbox_bmf_validate.py \
      --sandbox data/sandbox/merit_sandbox.db \
      --bmf data/bmf.csv
"""
import argparse
import csv
import sqlite3
from collections import Counter
from datetime import datetime

INSERT_SQL = """
INSERT OR IGNORE INTO registry_enriched (
    EIN, organization_name, NTEE1, NTEECC, STATE, CITY,
    subsection, deductibility, ruling_date, zipcode, source
) VALUES (?, ?, ?, ?, ?, ?, '3', '1', ?, ?, 'IRS_BMF')
"""


def ntee1(code):
    return code[0].upper() if code and code[0].isalpha() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sandbox", default="data/sandbox/merit_sandbox.db")
    ap.add_argument("--bmf", default="data/bmf.csv")
    args = ap.parse_args()

    con = sqlite3.connect(args.sandbox, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")

    before = con.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    print(f"[{datetime.now():%H:%M:%S}] SANDBOX validation against {args.sandbox}")
    print(f"  rows before: {before:,}")

    # Existing EIN set (for revocation/gap signal)
    existing = set(
        r[0] for r in con.execute("SELECT EIN FROM registry_enriched")
    )
    print(f"  existing EINs loaded: {len(existing):,}")

    new_ntee = Counter()
    new_state = Counter()
    new_samples = []
    bmf_c3_eins = set()
    bad_ein = 0
    no_name = 0
    no_ntee = 0
    inserted = 0
    skipped = 0
    batch = []

    with open(args.bmf, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if row.get("SUBSECTION", "").strip() != "03":
                skipped += 1
                continue
            if row.get("DEDUCTIBILITY", "").strip() != "1":
                skipped += 1
                continue

            ein = (row.get("EIN") or "").strip().zfill(9)
            name = (row.get("NAME") or "").strip()[:200]
            ntee = (row.get("NTEE_CD") or "").strip()[:10]
            state = (row.get("STATE") or "").strip().upper()[:2]
            city = (row.get("CITY") or "").strip()[:100]
            ruling = (row.get("RULING") or "").strip()[:8]
            zipcode = (row.get("ZIP") or "").strip()[:10]

            if not ein or not name:
                skipped += 1
                if not name:
                    no_name += 1
                continue
            if len(ein) != 9 or not ein.isdigit():
                bad_ein += 1

            bmf_c3_eins.add(ein)
            if not ntee:
                no_ntee += 1

            # Is this org genuinely new to our registry?
            if ein not in existing:
                new_ntee[ntee1(ntee) or "?"] += 1
                new_state[state or "?"] += 1
                if len(new_samples) < 12:
                    new_samples.append((ein, name, ntee1(ntee), state, city))

            batch.append((ein, name, ntee1(ntee), ntee or None, state, city, ruling, zipcode))
            if len(batch) >= 10_000:
                con.executemany(INSERT_SQL, batch)
                con.commit()
                inserted += len(batch)
                batch = []

    if batch:
        con.executemany(INSERT_SQL, batch)
        con.commit()
        inserted += len(batch)

    after = con.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    added = after - before

    # Revocation / gap signal: orgs we have that are NOT 501c3-deductible in the
    # new BMF. Could be revoked, reclassified, or dropped from the EO extract.
    missing_from_bmf = len(existing - bmf_c3_eins)

    print("\n  ── RESULT ─────────────────────────────────────────")
    print(f"  rows after:            {after:,}")
    print(f"  NEW orgs added:        {added:,}")
    print(f"  c3+deductible in BMF:  {len(bmf_c3_eins):,}")
    print(f"  rows skipped (non-c3): {skipped:,}")
    print("\n  ── ALIGNMENT CHECKS ──────────────────────────────")
    print(f"  malformed EINs:        {bad_ein:,}")
    print(f"  rows w/o name:         {no_name:,}")
    print(f"  c3 orgs w/o NTEE code: {no_ntee:,}")
    print("\n  ── NEW ORGS by NTEE1 (top) ───────────────────────")
    for k, v in new_ntee.most_common(12):
        print(f"    {k:<3} {v:,}")
    print("\n  ── NEW ORGS by STATE (top) ───────────────────────")
    for k, v in new_state.most_common(10):
        print(f"    {k:<3} {v:,}")
    print("\n  ── SAMPLE NEW ORGS ───────────────────────────────")
    for ein, name, n1, st, city in new_samples:
        print(f"    {ein}  [{n1 or '?'}|{st or '??'}]  {name[:48]}  {city}")
    print("\n  ── REVOCATION / GAP SIGNAL ───────────────────────")
    print(f"  existing EINs NOT c3-deductible in new BMF: {missing_from_bmf:,}")
    print("  (candidates for revoked/reclassified — review before purging)")

    con.close()
    print(f"\n[{datetime.now():%H:%M:%S}] sandbox validation done (live DB untouched)")


if __name__ == "__main__":
    main()
