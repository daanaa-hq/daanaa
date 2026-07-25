#!/usr/bin/env python3
"""
Capture organizations' own mission statements from Form 990 Part I.

Today 1.58M of our missions are AI-generated and only a handful come from the
organization. The 990 carries the mission the organization wrote itself, on a
public filing, with a date attached. That is strictly better evidence, so it
supersedes anything we inferred (Stewardship P3, P10).

Precedence, strongest first:
    claimed / nonprofit_supplied   (org told us directly — never overwritten)
    irs_990                        (org told the IRS — this script)
    ai_*                           (we guessed — replaced on sight)

Newest filing year wins, so 2023 is processed first and earlier years only fill
what is still missing.

Usage:
    python3 scripts/ingest_990_missions.py [--dry-run] [--limit-years N]
"""
import argparse
import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path.home() / "meritgiving" / "data" / "merit_registry.db"
NCCS_DIR = Path.home() / "meritgiving" / "data" / "nccs"
LOG = Path.home() / "meritgiving" / "logs" / "ingest_990_missions.log"

MISSION_COL = "F9_01_ACT_GVRN_ACT_MISSION"
# Sources we must never clobber: the organization spoke to us directly.
PROTECTED_SOURCES = ("claimed", "nonprofit_supplied", "lucido")
MIN_LEN = 25
MAX_LEN = 2000
COMMIT_EVERY = 25_000

# Filers who use the box to say nothing.
JUNK = {
    "N/A", "NA", "NONE", "SEE SCHEDULE O", "SEE SCH O", "SEE ATTACHED",
    "SAME AS PRIOR YEAR", "NO CHANGE", "SEE PART III", "TBD", "N/A.",
}


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as fh:
        fh.write(line + "\n")


def clean(raw):
    """Return a usable mission string, or None when the box holds no content."""
    if not raw:
        return None
    val = " ".join(str(raw).replace('"', " ").split())
    if len(val) < MIN_LEN or len(val) > MAX_LEN:
        return None
    if val.upper().rstrip(".") in JUNK:
        return None
    # Filings that just cross-reference another schedule carry no mission.
    if val.upper().startswith(("SEE SCHEDULE", "SEE SCH", "SEE PART", "SEE ATTACH")):
        return None
    return val


def ingest(dry_run=False, limit_years=None):
    files = sorted(NCCS_DIR.glob("F9-P01-T00-SUMMARY-*.CSV"), reverse=True)
    if limit_years:
        files = files[:limit_years]

    conn = sqlite3.connect(str(DB), timeout=180)
    conn.execute("PRAGMA busy_timeout=180000")
    cur = conn.cursor()

    protected = set()
    for src in PROTECTED_SOURCES:
        protected |= {r[0] for r in cur.execute(
            "SELECT EIN FROM registry_enriched WHERE mission_source = ?", (src,)
        )}
    log(f"{len(protected):,} orgs have an org-supplied mission — protected from overwrite")

    # An org's newest filing wins; once written we skip it in older years.
    written_eins = set()
    grand = 0

    for path in files:
        year = path.stem.split("-")[-1]
        rows = updated = skipped_junk = 0
        log(f"{year}: reading {path.name}")

        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            reader = csv.DictReader(fh)
            if MISSION_COL not in (reader.fieldnames or []):
                log(f"{year}: SKIP — {MISSION_COL} absent")
                continue

            for row in reader:
                rows += 1
                ein = (row.get("ORG_EIN") or "").strip().zfill(9)
                if not ein or ein in protected or ein in written_eins:
                    continue

                mission = clean(row.get(MISSION_COL))
                if not mission:
                    skipped_junk += 1
                    continue

                if not dry_run:
                    cur.execute(
                        "UPDATE registry_enriched "
                        "SET mission = ?, mission_source = 'irs_990', "
                        "    mission_last_verified = ? "
                        "WHERE EIN = ? "
                        "  AND (mission_source IS NULL OR mission_source LIKE 'ai_%' "
                        "       OR mission IS NULL OR mission = '')",
                        (mission, year, ein),
                    )
                    if cur.rowcount:
                        updated += 1
                        written_eins.add(ein)
                else:
                    updated += 1
                    written_eins.add(ein)

                if rows % COMMIT_EVERY == 0:
                    if not dry_run:
                        conn.commit()
                    log(f"{year}: {rows:,} rows | {updated:,} missions written")

        if not dry_run:
            conn.commit()
        grand += updated
        log(f"{year}: DONE — {rows:,} rows | {updated:,} written | {skipped_junk:,} empty/boilerplate")

    if not dry_run:
        breakdown = cur.execute(
            "SELECT mission_source, COUNT(*) FROM registry_enriched "
            "WHERE mission IS NOT NULL AND mission != '' "
            "GROUP BY mission_source ORDER BY 2 DESC LIMIT 6"
        ).fetchall()
        log("=" * 70)
        log(f"Missions written from 990 filings: {grand:,}")
        for src, n in breakdown:
            log(f"  {src or '(none)':<22} {n:,}")
    else:
        log(f"DRY RUN — would write {grand:,} missions")

    conn.close()
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit-years", type=int, default=None)
    args = ap.parse_args()
    sys.exit(ingest(args.dry_run, args.limit_years))
