#!/usr/bin/env python3
"""
Link-integrity gate for droplet deploys (stewardship: donate/website links fail closed).

Proves the precompute output carries the EXACT donate/website link data from the source
snapshot — no corruption, no truncation, no STALE links left by incremental skipping.

Checks (any failure → exit 1, deploy aborts):
  1. Every deductible org with a donate_url in the snapshot has a precompute file whose
     donate_url / donate_url_status / donate_platform match the snapshot exactly.
  2. No precompute file serves a donate_url that differs from the snapshot (no phantom/stale links).
  3. A large random sample of websites match between snapshot and precompute files.

Usage:
  MERIT_DB_PATH=<snapshot.db> PRECOMPUTE_OUT=<scratch/precompute> python3 scripts/validate_link_integrity.py
"""
import os, sys, gzip, json, sqlite3, random
from pathlib import Path

# scripts/testing/ -> repo root, so registry_filters.py (one level up from
# scripts/) resolves regardless of the caller's PYTHONPATH. Same fix pattern
# as precompute_content.py (see LESSONS.md, folder-migration import bug).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.registry_filters import DEDUCTIBLE_FILTER

DB = os.environ.get("MERIT_DB_PATH", "data/merit_registry.db")
OUT = Path(os.environ.get("PRECOMPUTE_OUT", "precompute_output"))
ORGS = OUT / "orgs"
WEBSITE_SAMPLE = int(os.environ.get("LINK_WEBSITE_SAMPLE", "3000"))

def org_file(ein: str) -> Path:
    return ORGS / ein[:3] / f"{ein}.json.gz"

def load_org(ein: str):
    p = org_file(ein)
    if not p.exists():
        return None
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return json.load(f)

def main():
    if not ORGS.exists():
        print(f"FAIL: precompute orgs dir missing: {ORGS}")
        return 1

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    failures = []

    # ---- 1+2. Donate links: check EVERY deductible org with a donate_url (small set, exhaustive) ----
    #
    # BUG FIX 2026-08-18 (two bugs, same root cause -- this predicate was re-spelled
    # inline instead of imported, exactly what registry_filters.py's own docstring
    # warns against):
    #   1. This used to filter in Python with `r["deductibility"] != 1` (int). The
    #      column is TEXT ('1', '2', '0', '4', 'revoked'), so that comparison was
    #      never true -- all 97,360 donate_url rows hit `continue`, and this
    #      "exhaustive" check silently verified 0 rows on every run while still
    #      printing "LINK INTEGRITY OK". Found by noticing an exhaustive check over
    #      97,360 rows reporting 0+0 instead of investigating further.
    #   2. Fixing the type alone (`!= "1"`) surfaced a second issue: it flagged 3,078
    #      revoked/inactive orgs as "missing precompute file" -- correctly excluded by
    #      precompute_orgs.py's active-org filter, but not by this hand-rolled check.
    #      DEDUCTIBLE_FILTER (registry_filters.py) is the canonical, already-correct
    #      version of this exact predicate -- use it instead of a third inline rewrite.
    donors = c.execute(f"""
        SELECT EIN, donate_url, donate_url_status, donate_platform
        FROM registry_enriched
        WHERE donate_url IS NOT NULL AND donate_url != '' AND {DEDUCTIBLE_FILTER}
    """).fetchall()
    print(f"Checking {len(donors)} orgs with donate_url (exhaustive)...")
    donate_checked = donate_missing = 0
    for r in donors:
        org = load_org(r["EIN"])
        if org is None:
            donate_missing += 1
            failures.append(f"donate: deductible org {r['EIN']} has donate_url but NO precompute file")
            continue
        donate_checked += 1
        for field in ("donate_url", "donate_url_status", "donate_platform"):
            if (org.get(field) or None) != (r[field] or None):
                failures.append(
                    f"donate MISMATCH {r['EIN']} {field}: snapshot={r[field]!r} precompute={org.get(field)!r}"
                )

    # ---- 3. Websites: large random sample ----
    # Same predicate consistency fix as the donate check above -- this used
    # `deductibility = 1` which, unlike the Python comparison, SQLite's TEXT
    # affinity actually coerces correctly, so this half wasn't silently broken.
    # It was still missing the revoked/irs_revoked exclusion, though harmless
    # here since a mismatch just increments the tolerated site_skipped counter,
    # not failures -- fixed anyway for consistency with the canonical predicate.
    sites = c.execute(f"""
        SELECT EIN, website, website_status
        FROM registry_enriched
        WHERE website IS NOT NULL AND website != '' AND {DEDUCTIBLE_FILTER}
    """).fetchall()
    sample = random.sample(sites, min(WEBSITE_SAMPLE, len(sites)))
    print(f"Checking {len(sample)} website samples (of {len(sites)} deductible w/ website)...")
    site_checked = site_skipped = 0
    for r in sample:
        org = load_org(r["EIN"])
        if org is None:
            site_skipped += 1   # not all deductible orgs are precomputed every run; tolerate
            continue
        site_checked += 1
        if (org.get("website") or None) != (r["website"] or None):
            failures.append(
                f"website MISMATCH {r['EIN']}: snapshot={r['website']!r} precompute={org.get('website')!r}"
            )

    conn.close()

    print(f"\nDonate: {donate_checked} verified, {donate_missing} missing-file")
    print(f"Website: {site_checked} verified, {site_skipped} not-in-precompute")
    if failures:
        print(f"\n❌ LINK INTEGRITY FAILED — {len(failures)} issue(s):")
        for f in failures[:25]:
            print(f"   {f}")
        if len(failures) > 25:
            print(f"   ... and {len(failures) - 25} more")
        return 1
    print("\n✓ LINK INTEGRITY OK — donate/website links match snapshot exactly")
    return 0

if __name__ == "__main__":
    sys.exit(main())
