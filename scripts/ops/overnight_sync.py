#!/usr/bin/env python3
"""
MeritGiving Overnight Sync
Phases: 1) Dedupe  2) Merge 990s  3) Recalc Percentiles  4) Patch API
"""
import sqlite3, json, glob, os, sys, re, time
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser("~/meritgiving/data/merit_registry.db")
DATA_DIR = os.path.expanduser("~/meritgiving/data")
LOG_DIR = os.path.expanduser("~/meritgiving/logs")
LOG_FILE = os.path.join(LOG_DIR, "overnight_sync.log")

os.makedirs(LOG_DIR, exist_ok=True)

def log(msg):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{t}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def phase1_dedupe(conn):
    log("=== PHASE 1: DEDUPE registry_enriched ===")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM registry_enriched")
    total = c.fetchone()[0]
    log(f"Total rows: {total:,}")

    # EIN has a UNIQUE constraint so true duplicates cannot accumulate via normal
    # upserts. Check fast; skip the expensive table-swap if nothing to do.
    c.execute("""
        SELECT COUNT(*) FROM (
            SELECT EIN FROM registry_enriched GROUP BY EIN HAVING COUNT(*) > 1
        )
    """)
    dup_eins = c.fetchone()[0]

    if dup_eins == 0:
        log("Phase 1 skipped: no duplicate EINs found")
        return total

    log(f"Found {dup_eins:,} EINs with duplicates — removing lower-revenue rows")
    # Delete duplicate rowids, keeping the one with highest revenue per EIN.
    # Safe in-place DELETE; never drops the main table.
    c.execute("""
        DELETE FROM registry_enriched
        WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM (
                SELECT rowid, EIN,
                       ROW_NUMBER() OVER (PARTITION BY EIN
                                          ORDER BY total_revenue DESC,
                                                   ntee1_percentile DESC) AS rn
                FROM registry_enriched
            ) WHERE rn = 1
        )
    """)
    removed = c.rowcount
    conn.commit()
    log(f"Phase 1 complete: removed {removed:,} duplicate rows")
    c.execute("SELECT COUNT(*) FROM registry_enriched")
    return c.fetchone()[0]

def phase2_merge_990s(conn):
    log("=== PHASE 2: MERGE IRS 990 DOWNLOADS ===")
    c = conn.cursor()
    
    # Find all JSON files from ProPublica downloads
    patterns = [
        os.path.join(DATA_DIR, "**", "sample_*.json"),
        os.path.join(DATA_DIR, "**", "year_*.json"),
        os.path.join(DATA_DIR, "**", "*.json"),
    ]
    
    files = set()
    for p in patterns:
        for f in glob.glob(p, recursive=True):
            # Skip small files (< 1KB) and our own DB/json
            if os.path.getsize(f) > 1024 and 'merit_registry' not in f:
                files.add(f)
    
    files = sorted(files)
    log(f"Found {len(files)} candidate JSON files to scan")
    
    inserted = 0
    updated = 0
    skipped = 0
    
    for fpath in files:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
        except Exception as e:
            skipped += 1
            continue
        
        # Handle both array and dict wrappers
        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            # Common ProPublica wrapper keys
            for key in ['organizations', 'filings', 'data', 'results', 'returns']:
                if key in data and isinstance(data[key], list):
                    records = data[key]
                    break
            if not records and 'Filings' in data:
                records = data.get('Filings', [])
            if not records:
                # Single filing dict
                records = [data]
        
        batch = []
        for rec in records:
            if not isinstance(rec, dict):
                continue
            
            # Extract EIN
            ein = None
            for key in ['EIN', 'ein', 'EINs', 'filer_ein']:
                val = rec.get(key)
                if val:
                    ein = str(val).replace('-', '').strip()
                    break
            
            if not ein or len(ein) != 9 or not ein.isdigit():
                continue
            
            # Extract name
            name = None
            for key in ['OrganizationName', 'organization_name', 'name', 'BusinessNameLine1Txt', 'FilerName']:
                val = rec.get(key)
                if val and str(val).strip():
                    name = str(val).strip()
                    break
            if not name:
                # Nested ProPublica format
                filer = rec.get('Filer', {}) or rec.get('filer', {})
                if isinstance(filer, dict):
                    name = filer.get('Name', {}).get('BusinessNameLine1Txt', '') if isinstance(filer.get('Name'), dict) else str(filer.get('Name', ''))
            
            # Extract revenue
            revenue = None
            for key in ['TotalRevenueAmt', 'total_revenue', 'TotalRevenue', 'Revenue', 'CYTotalRevenueAmt']:
                val = rec.get(key)
                if val is not None:
                    try:
                        revenue = float(val)
                        break
                    except:
                        pass
            if revenue is None:
                # Deep search in ReturnData
                rd = rec.get('ReturnData', rec.get('return_data', {}))
                if isinstance(rd, dict):
                    irs990 = rd.get('IRS990', rd.get('irs990', {}))
                    if isinstance(irs990, dict):
                        for key in ['TotalRevenueAmt', 'CYTotalRevenueAmt', 'TotalRevenue']:
                            val = irs990.get(key)
                            if val is not None:
                                try:
                                    revenue = float(val)
                                    break
                                except:
                                    pass
            
            # Extract city/state
            city = rec.get('City', rec.get('city', ''))
            state = rec.get('State', rec.get('state', rec.get('STATE', '')))
            
            # Extract NTEE
            ntee = rec.get('NTEECode', rec.get('NTEE1', rec.get('ntee', rec.get('NTEE', ''))))
            
            if revenue is not None and revenue > 0:
                batch.append((ein, name or '', ntee or '', city or '', state or '', revenue, 'IRS990'))
        
        # Bulk upsert
        for ein, name, ntee, city, state, rev, src in batch:
            c.execute("""
                INSERT INTO registry_enriched (EIN, organization_name, NTEE1, CITY, STATE, total_revenue, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(EIN) DO UPDATE SET
                    total_revenue = CASE 
                        WHEN excluded.total_revenue > registry_enriched.total_revenue 
                        THEN excluded.total_revenue 
                        ELSE registry_enriched.total_revenue 
                    END,
                    source = 'NCCS_IRS990_MERGED',
                    organization_name = COALESCE(NULLIF(excluded.organization_name, ''), registry_enriched.organization_name),
                    NTEE1 = COALESCE(NULLIF(excluded.NTEE1, ''), registry_enriched.NTEE1),
                    CITY = COALESCE(NULLIF(excluded.CITY, ''), registry_enriched.CITY),
                    STATE = COALESCE(NULLIF(excluded.STATE, ''), registry_enriched.STATE)
            """, (ein, name, ntee, city, state, rev, src))
            
            if c.rowcount > 0:
                if c.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1
        
        if files.index(fpath) % 50 == 0 and files.index(fpath) > 0:
            log(f"  Processed {files.index(fpath)}/{len(files)} files | inserted:{inserted} updated:{updated}")
    
    conn.commit()
    log(f"Phase 2 complete: {inserted:,} inserted, {updated:,} updated, {skipped:,} skipped")
    
    c.execute("SELECT COUNT(*) FROM registry_enriched")
    total = c.fetchone()[0]
    log(f"Total registry_enriched rows: {total:,}")

def phase3_recalc_percentiles(conn):
    log("=== PHASE 3: RECALCULATE PERCENTILES ===")
    c = conn.cursor()
    
    # SQLite doesn't have native percentile, so we use a Python approach for accuracy
    c.execute("SELECT EIN, NTEE1, total_revenue FROM registry_enriched WHERE total_revenue > 0")
    rows = c.fetchall()
    
    from collections import defaultdict
    ntee_groups = defaultdict(list)
    ein_data = {}
    
    for ein, ntee, rev in rows:
        if ntee:
            ntee_groups[ntee].append((ein, rev))
        ein_data[ein] = {'ntee': ntee, 'rev': rev}
    
    # Calculate percentiles per NTEE
    percentile_updates = []
    for ntee, group in ntee_groups.items():
        group.sort(key=lambda x: x[1])
        n = len(group)
        for i, (ein, rev) in enumerate(group):
            pct = round((i / (n - 1)) * 100, 2) if n > 1 else 50.0
            percentile_updates.append((pct, ein))
    
    # Batch update
    c.executemany("UPDATE registry_enriched SET ntee1_percentile = ? WHERE EIN = ?", percentile_updates)
    conn.commit()
    log(f"Recalculated percentiles for {len(percentile_updates):,} orgs across {len(ntee_groups)} NTEE categories")

def phase4_patch_api():
    # Legacy phase: patched app.py / merit_app.py which no longer exist.
    # daanaa_api.py already queries registry_enriched directly; nothing to patch.
    log("=== PHASE 4: PATCH API — skipped (daanaa_api.py needs no patching) ===")

def main():
    log("=" * 60)
    log("MERIT OVERNIGHT SYNC STARTED")
    log("=" * 60)
    
    if not os.path.exists(DB_PATH):
        log(f"FATAL: DB not found at {DB_PATH}")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    
    try:
        t0 = time.time()
        phase1_dedupe(conn)
        phase2_merge_990s(conn)
        phase3_recalc_percentiles(conn)
        phase4_patch_api()
        elapsed = time.time() - t0
        log(f"=" * 60)
        log(f"ALL PHASES COMPLETE in {elapsed/60:.1f} minutes")
        log(f"=" * 60)
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
