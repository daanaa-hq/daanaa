#!/usr/bin/env python3
"""tag_template_ntee.py — deterministic cause tags for stub-mission orgs.

Orgs whose mission is a generated stub (mission_source='template_ntee') carry
no information beyond name + location + NTEE category. An LLM given that stub
just re-derives the NTEE category and occasionally hallucinates (a civil-rights
org got tagged "animals"). A deterministic NTEE1 -> tag map is strictly better
here: same information, zero fabrication, fully explainable (Stewardship P3/P9),
and free (no GPU). Tags are free-text searchable in org_fts, so this makes a
tiny org findable on "food" / "veterans" etc., not just via the category filter.

Default scope is ADDITIVE: only orgs with empty cause_tags are touched. Existing
tags (e.g. a prior pass) are left alone unless --overwrite is passed.

The tag basis is the canonical NTEE1 label map (kept in sync with
generate_missions_irs_bmf.py / frontend categories), expanded into clean
lowercase search terms.

Usage:
    python3 scripts/tag_template_ntee.py --dry-run
    python3 scripts/tag_template_ntee.py            # fill empty only
"""
import argparse
import json
import sqlite3
import time
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"

# NTEE1 major group -> deterministic, human-searchable cause tags.
# Derived from the canonical _NTEE_LABELS (generate_missions_irs_bmf.py), split
# into discrete search terms. These are categories, not claims about a specific
# org's activity, so they are evidence-based (the org's own IRS NTEE code).
NTEE1_TAGS = {
    "A": ["arts", "culture", "humanities"],
    "B": ["education"],
    "C": ["environment", "conservation"],
    "D": ["animals", "animal welfare"],
    "E": ["health care"],
    "F": ["mental health"],
    "G": ["disease research", "patient support"],
    "H": ["medical research"],
    "I": ["crime", "legal services"],
    "J": ["employment", "job training"],
    "K": ["food", "nutrition"],
    "L": ["housing", "shelter"],
    "M": ["public safety", "disaster relief"],
    "N": ["sports", "recreation"],
    "O": ["youth development"],
    "P": ["human services"],
    "Q": ["international"],
    "R": ["civil rights", "advocacy"],
    "S": ["community improvement"],
    "T": ["philanthropy", "grantmaking"],
    "U": ["science", "technology"],
    "V": ["social science"],
    "W": ["public benefit"],
    "X": ["faith", "religion"],
    "Y": ["membership", "mutual benefit"],
    "Z": ["community service"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--overwrite", action="store_true",
                    help="Also replace existing tags (default: fill empty only)")
    args = ap.parse_args()

    db = sqlite3.connect(DB_PATH, timeout=60)
    db.row_factory = sqlite3.Row

    tag_clause = "" if args.overwrite else \
        "AND (cause_tags IS NULL OR cause_tags IN ('[]','null','{}',''))"
    where = (f"mission_source='template_ntee' AND deductibility=1 "
             f"AND org_status='active' AND NTEE1 IS NOT NULL AND NTEE1!='' "
             f"{tag_clause}")

    rows = db.execute(
        f"SELECT EIN, NTEE1 FROM registry_enriched WHERE {where}"
    ).fetchall()
    print(f"target orgs: {len(rows):,} "
          f"({'overwrite' if args.overwrite else 'fill-empty'})", flush=True)

    if args.dry_run:
        from collections import Counter
        c = Counter(r["NTEE1"].strip().upper()[:1] for r in rows)
        for code, n in c.most_common():
            print(f"  {code}: {n:,} -> {NTEE1_TAGS.get(code, ['(unmapped)'])}")
        db.close()
        return

    t0 = time.time()
    written = skipped = 0
    for r in rows:
        code = (r["NTEE1"] or "").strip().upper()[:1]
        tags = NTEE1_TAGS.get(code)
        if not tags:
            skipped += 1
            continue
        db.execute("UPDATE registry_enriched SET cause_tags=? WHERE EIN=?",
                   (json.dumps(tags), r["EIN"]))
        written += 1
        if written % 50000 == 0:
            db.commit()
            print(f"  {written:,} written ({time.time()-t0:.0f}s)", flush=True)
    db.commit()
    db.close()
    print(f"Done: {written:,} tagged, {skipped:,} skipped (unmapped NTEE1) "
          f"in {(time.time()-t0)/60:.1f}m")


if __name__ == "__main__":
    main()
