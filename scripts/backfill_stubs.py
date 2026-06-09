#!/usr/bin/env python3
"""
scripts/backfill_stubs.py

Backfills gap data for bmf_stub records from public sources:

  Phase 1 — 990-N postcards (S3, no auth):
    • website  — col 8 of the postcard file
    • latest_tax_year — most recent tax year filed
    Skips orgs that already have a website.

  Phase 2 — ProPublica API:
    • mission, website, total_revenue, net_assets, months_of_reserve, NTEECC
    Only runs on stubs with ruling dates before 2015 (likely 990 filers).
    Rate-limited to ~0.8 req/s to stay polite.

Usage:
    python3 scripts/backfill_stubs.py              # both phases
    python3 scripts/backfill_stubs.py --phase 1    # 990-N only
    python3 scripts/backfill_stubs.py --phase 2    # ProPublica only
    python3 scripts/backfill_stubs.py --limit 500  # stop after N stubs
"""

import sqlite3, subprocess, csv, io, time, json, argparse, urllib.request, urllib.error
from pathlib import Path

DB_PATH   = Path.home() / "meritgiving" / "data" / "merit_registry.db"
CACHE_DIR = Path.home() / "meritgiving" / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

POSTCARD_S3 = "s3://gt990datalake-rawdata/EfileData/Postcards/990N_Postcards_2026_5_18_raw.txt"
PP_URL      = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"


def connect():
    db = sqlite3.connect(DB_PATH, timeout=60)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    return db


# ── Phase 1: 990-N postcards ─────────────────────────────────────────────────

def phase1(db, limit=None):
    print("[phase 1] 990-N postcard → website + tax year", flush=True)

    # Load stub EINs that are still missing a website
    rows = db.execute("""
        SELECT EIN FROM registry_enriched
        WHERE source='bmf_stub'
          AND (website IS NULL OR website='')
    """).fetchall()
    stub_eins = {r[0] for r in rows}
    print(f"  {len(stub_eins):,} stubs still need a website", flush=True)

    if not stub_eins:
        print("  nothing to do", flush=True)
        return

    # Stream S3 file via aws cli — no full download needed
    print("  streaming 990-N file from S3 …", flush=True)
    proc = subprocess.Popen(
        ["aws", "s3", "cp", POSTCARD_S3, "-", "--no-sign-request"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )

    updates: dict[str, dict] = {}  # ein → {website, latest_tax_year}
    lines_read = 0

    for raw_line in proc.stdout:
        lines_read += 1
        try:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\n")
        except Exception:
            continue

        parts = line.split("|")
        if len(parts) < 8:
            continue

        ein = parts[0].strip().lstrip("0") or parts[0].strip()
        # EINs in postcard file may lack leading zeros — normalise
        ein_padded = parts[0].strip().zfill(9)

        tax_year_raw = parts[1].strip()
        website_raw  = parts[7].strip()

        # Match against stub EINs (both forms)
        matched = None
        if ein_padded in stub_eins:
            matched = ein_padded
        elif ein in stub_eins:
            matched = ein

        if matched is None:
            continue

        try:
            tax_year = int(tax_year_raw)
        except ValueError:
            tax_year = None

        prev = updates.get(matched, {})
        website = website_raw if website_raw and not "@" in website_raw else prev.get("website")
        prev_year = prev.get("latest_tax_year", 0) or 0
        latest_year = max(prev_year, tax_year or 0) or None

        updates[matched] = {"website": website, "latest_tax_year": latest_year}

        if lines_read % 500_000 == 0:
            print(f"  … {lines_read:,} lines scanned, {len(updates):,} hits so far", flush=True)

        if limit and len(updates) >= limit:
            break

    proc.terminate()
    proc.wait()

    with_site = sum(1 for v in updates.values() if v.get("website"))
    print(f"  scanned {lines_read:,} lines → {len(updates):,} stubs matched, {with_site:,} with website", flush=True)

    written = 0
    for ein, data in updates.items():
        site = data.get("website") or None
        yr   = data.get("latest_tax_year")
        db.execute(
            """UPDATE registry_enriched
               SET website=CASE WHEN ? IS NOT NULL THEN ? ELSE website END,
                   latest_tax_year=CASE WHEN ? IS NOT NULL THEN
                     MAX(COALESCE(latest_tax_year,0), ?) ELSE latest_tax_year END
               WHERE EIN=? AND source='bmf_stub'""",
            (site, site, yr, yr, ein),
        )
        written += 1
        if written % 5000 == 0:
            db.commit()
    db.commit()
    print(f"  wrote {written:,} rows", flush=True)


# ── Phase 2: ProPublica API ───────────────────────────────────────────────────

def _pp_fetch(ein: str) -> dict | None:
    url = PP_URL.format(ein=ein.lstrip("0"))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MeritGiving/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        return data.get("organization") or None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None


def phase2(db, limit=None, only_source=None):
    print("[phase 2] ProPublica API → mission, financials, NTEE", flush=True)
    src_clause = "source = '%s'" % only_source if only_source else "source IN ('bmf_stub', 'IRS_BMF')"

    # Cover both stub conventions: bmf_stub AND IRS_BMF (the daily-watch import
    # labels new orgs IRS_BMF). The mission-IS-NULL filter naturally targets only
    # un-missioned stubs, so already-handled orgs are skipped. Oldest-ruling first
    # (more likely to have 990 financials on file at ProPublica).
    rows = db.execute(f"""
        SELECT EIN FROM registry_enriched
        WHERE {src_clause}
          AND (mission IS NULL OR mission='')
        ORDER BY ruling_date ASC
    """).fetchall()

    targets = [r[0] for r in rows]
    if limit:
        targets = targets[:limit]
    print(f"  {len(targets):,} stubs targeted ({src_clause}, no mission)", flush=True)

    hits = 0
    misses = 0
    errors = 0
    t0 = time.time()

    for i, ein in enumerate(targets, 1):
        org = _pp_fetch(ein)
        time.sleep(1.25)  # ~0.8 req/s

        if org is None:
            misses += 1
        else:
            hits += 1
            nteecc = org.get("ntee_code") or None
            ntee1  = nteecc[0] if nteecc else None
            mission = (org.get("mission") or "").strip() or None
            website = (org.get("website") or "").strip() or None
            revenue = org.get("income_amount") or None
            assets  = org.get("asset_amount") or None

            db.execute("""
                UPDATE registry_enriched SET
                  NTEECC=CASE WHEN ? IS NOT NULL THEN ? ELSE NTEECC END,
                  NTEE1=CASE WHEN ? IS NOT NULL THEN ? ELSE NTEE1 END,
                  mission=CASE WHEN ? IS NOT NULL THEN ? ELSE mission END,
                  website=CASE WHEN ? IS NOT NULL THEN ? ELSE website END,
                  total_revenue=CASE WHEN ? IS NOT NULL THEN ? ELSE total_revenue END,
                  total_assets=CASE WHEN ? IS NOT NULL THEN ? ELSE total_assets END,
                  data_source=CASE WHEN ? IS NOT NULL THEN 'propublica' ELSE data_source END
                WHERE EIN=? AND source IN ('bmf_stub', 'IRS_BMF')
            """, (nteecc, nteecc, ntee1, ntee1, mission, mission,
                  website, website, revenue, revenue, assets, assets,
                  mission or website, ein))
            db.commit()

        if i % 50 == 0:
            elapsed = time.time() - t0
            rate = i / elapsed * 3600
            print(
                f"  {i:>6,}/{len(targets):,}  hits={hits}  misses={misses}  "
                f"~{rate:.0f}/hr  elapsed={elapsed:.0f}s",
                flush=True,
            )

    print(f"\n[phase 2 done]  hits={hits}  misses={misses}  errors={errors}", flush=True)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, choices=[1, 2], help="Run only this phase")
    parser.add_argument("--limit", type=int, help="Stop after N stubs per phase")
    parser.add_argument("--source", help="Restrict to one source label (e.g. IRS_BMF)")
    args = parser.parse_args()

    db = connect()

    if args.phase in (None, 1):
        phase1(db, limit=args.limit)
    if args.phase in (None, 2):
        phase2(db, limit=args.limit, only_source=args.source)

    print("\n[backfill complete]", flush=True)


if __name__ == "__main__":
    main()
