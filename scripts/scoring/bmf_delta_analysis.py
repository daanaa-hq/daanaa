#!/usr/bin/env python3
"""
READ-ONLY analysis of the fresh BMF vs the live registry. Answers two questions
without touching the DB:

  1. Which EXISTING orgs have newer/changed data in the BMF (NTEE, name)?
  2. Which of our orgs look CLOSED (dropped from the BMF, lost c3-deductible
     status, or on the IRS auto-revocation list)?

Nothing is written. Output is a report to inform a safe, non-disruptive update.
"""
import csv, sqlite3
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
BMF = BASE / "data" / "bmf.csv"
DB = BASE / "data" / "merit_registry.db"


def main():
    c = sqlite3.connect(DB, timeout=120)

    # Registry snapshot (EIN -> fields we might refresh/judge)
    reg = {}
    for ein, name, nteecc, src, score in c.execute(
        "SELECT EIN, organization_name, NTEECC, source, merit_score FROM registry_enriched"
    ):
        reg[ein] = (name or "", nteecc or "", src or "", score)
    print(f"registry orgs: {len(reg):,}")

    revoked = set(r[0] for r in c.execute("SELECT ein FROM revoked_eins"))
    print(f"auto-revoked EINs (IRS list): {len(revoked):,}")
    c.close()

    bmf_all = set()           # every EIN in the new BMF (any status)
    bmf_c3 = set()            # 501c3 + deductible
    name_changed = 0
    ntee_changed = 0
    ntee_fill = 0             # registry missing NTEE, BMF has it
    samples_name, samples_ntee = [], []

    with open(BMF, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            ein = (row.get("EIN") or "").strip().zfill(9)
            if not ein:
                continue
            bmf_all.add(ein)
            sub = row.get("SUBSECTION", "").strip()
            ded = row.get("DEDUCTIBILITY", "").strip()
            if sub == "03" and ded == "1":
                bmf_c3.add(ein)
            if ein not in reg:
                continue
            old_name, old_ntee, src, score = reg[ein]
            new_name = (row.get("NAME") or "").strip()[:200]
            new_ntee = (row.get("NTEE_CD") or "").strip()[:10]
            if new_ntee and not old_ntee:
                ntee_fill += 1
            elif new_ntee and old_ntee and new_ntee != old_ntee:
                ntee_changed += 1
                if len(samples_ntee) < 6:
                    samples_ntee.append((ein, old_ntee, new_ntee, old_name[:36]))
            if new_name and old_name and new_name.upper() != old_name.upper():
                name_changed += 1
                if len(samples_name) < 6:
                    samples_name.append((ein, old_name[:36], new_name[:36]))

    reg_eins = set(reg)
    dropped = reg_eins - bmf_all                       # gone from BMF entirely
    lost_c3 = (reg_eins & bmf_all) - bmf_c3            # present but not c3-deductible now
    revoked_ours = reg_eins & revoked                 # on IRS auto-revocation list
    dropped_and_revoked = dropped & revoked
    scored_dropped = sum(1 for e in dropped if reg[e][3] is not None)

    print("\n=== Q1 · EXISTING orgs with newer BMF data (candidates for safe refresh) ===")
    print(f"  NTEE code changed:        {ntee_changed:,}")
    print(f"  NTEE fill (we had none):  {ntee_fill:,}")
    print(f"  Name changed:             {name_changed:,}")
    for e, o, n, nm in samples_ntee:
        print(f"    NTEE {e}: {o!r} -> {n!r}  ({nm})")
    for e, o, n in samples_name:
        print(f"    NAME {e}: {o!r} -> {n!r}")

    print("\n=== Q2 · CLOSURE / revocation signals ===")
    print(f"  on IRS auto-revocation list:        {len(revoked_ours):,}")
    print(f"  dropped from BMF entirely:          {len(dropped):,}")
    print(f"    ...of those, confirmed revoked:   {len(dropped_and_revoked):,}")
    print(f"    ...of those, currently SCORED:    {scored_dropped:,}  (shown on site)")
    print(f"  present but lost c3-deductible:     {len(lost_c3):,}")
    print("\n  (closures are a REVIEW signal — dropping from a single monthly BMF cut can also")
    print("   mean a group-exemption reshuffle or a late re-listing, so verify before hiding.)")


if __name__ == "__main__":
    main()
