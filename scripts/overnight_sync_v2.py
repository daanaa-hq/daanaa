#!/usr/bin/env python3
"""
MeritGiving Overnight Sync v2 — COPY-AND-SWAP (no lock contention)
"""
import sqlite3, json, glob, os, sys, re, time, shutil
from datetime import datetime

DB_PATH = os.path.expanduser("~/meritgiving/data/merit_registry.db")
WORK_DB = os.path.expanduser("~/meritgiving/data/merit_registry_work.db")
BACKUP_DB = os.path.expanduser("~/meritgiving/data/merit_registry_backup.db")
DATA_DIR = os.path.expanduser("~/meritgiving/data")
LOG_DIR = os.path.expanduser("~/meritgiving/logs")
LOG_FILE = os.path.join(LOG_DIR, "overnight_sync_v2.log")

os.makedirs(LOG_DIR, exist_ok=True)

def log(msg):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{t}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def copy_db():
    log("=== COPYING DB TO WORK FILE ===")
    if os.path.exists(WORK_DB):
        os.remove(WORK_DB)
    shutil.copy2(DB_PATH, WORK_DB)
    size = os.path.getsize(WORK_DB) / (1024**3)
    log(f"Copied: {size:.2f} GB")

def phase1_dedupe(conn):
    log("=== PHASE 1: DEDUPE ===")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM registry_enriched")
    before = c.fetchone()[0]
    log(f"Before: {before:,}")
    
    c.execute("DROP TABLE IF EXISTS registry_deduped")
    c.execute("""
        CREATE TABLE registry_deduped AS
        SELECT * FROM registry_enriched re1
        WHERE re1.rowid = (
            SELECT re2.rowid FROM registry_enriched re2
            WHERE re2.EIN = re1.EIN
            ORDER BY re2.total_revenue DESC, COALESCE(re2.ntee1_percentile,0) DESC
            LIMIT 1
        )
    """)
    
    c.execute("SELECT COUNT(*) FROM registry_deduped")
    after = c.fetchone()[0]
    log(f"After dedupe: {after:,} | Removed {before-after:,} duplicates")
    
    c.execute("DROP TABLE registry_enriched")
    c.execute("ALTER TABLE registry_deduped RENAME TO registry_enriched")
    conn.commit()

def phase2_merge_990s(conn):
    log("=== PHASE 2: MERGE IRS 990s ===")
    c = conn.cursor()
    
    # Find JSON files
    files = []
    for root, dirs, fnames in os.walk(DATA_DIR):
        for f in fnames:
            if f.endswith('.json') and 'merit_registry' not in f:
                fpath = os.path.join(root, f)
                if os.path.getsize(fpath) > 1024:
                    files.append(fpath)
    
    log(f"Scanning {len(files)} JSON files...")
    
    inserted = 0
    updated = 0
    
    for i, fpath in enumerate(files):
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
        except:
            continue
        
        records = []
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            for key in ['organizations', 'filings', 'data', 'results', 'Filings']:
                if key in data and isinstance(data[key], list):
                    records = data[key]
                    break
            if not records:
                records = [data]
        
        for rec in records:
            if not isinstance(rec, dict):
                continue
            
            ein = str(rec.get('EIN', rec.get('ein', ''))).replace('-','').strip()
            if not ein or len(ein) != 9 or not ein.isdigit():
                continue
            
            name = str(rec.get('OrganizationName', rec.get('organization_name', rec.get('name', '')))).strip()
            ntee = str(rec.get('NTEECode', rec.get('NTEE1', rec.get('NTEE', '')))).strip()
            city = str(rec.get('City', rec.get('city', ''))).strip()
            state = str(rec.get('State', rec.get('state', rec.get('STATE', '')))).strip()
            
            revenue = None
            for key in ['TotalRevenueAmt', 'total_revenue', 'TotalRevenue', 'CYTotalRevenueAmt']:
                val = rec.get(key)
                if val is not None:
                    try:
                        revenue = float(val)
                        break
                    except:
                        pass
            
            if revenue is None:
                rd = rec.get('ReturnData', rec.get('return_data', {}))
                if isinstance(rd, dict):
                    irs990 = rd.get('IRS990', rd.get('irs990', {}))
                    if isinstance(irs990, dict):
                        for key in ['TotalRevenueAmt', 'CYTotalRevenueAmt']:
                            val = irs990.get(key)
                            if val is not None:
                                try:
                                    revenue = float(val)
                                    break
                                except:
                                    pass
            
            if revenue is not None and revenue > 0:
                c.execute("""
                    INSERT INTO registry_enriched (EIN, organization_name, NTEE1, CITY, STATE, total_revenue, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(EIN) DO UPDATE SET
                        total_revenue = MAX(excluded.total_revenue, registry_enriched.total_revenue),
                        source = 'NCCS_IRS990_MERGED',
                        organization_name = COALESCE(NULLIF(excluded.organization_name, ''), registry_enriched.organization_name),
                        NTEE1 = COALESCE(NULLIF(excluded.NTEE1, ''), registry_enriched.NTEE1),
                        CITY = COALESCE(NULLIF(excluded.CITY, ''), registry_enriched.CITY),
                        STATE = COALESCE(NULLIF(excluded.STATE, ''), registry_enriched.STATE)
                """, (ein, name, ntee, city, state, revenue, 'IRS990'))
                updated += 1
        
        if i % 100 == 0 and i > 0:
            conn.commit()
            log(f"  {i}/{len(files)} files | upserts: {updated}")
    
    conn.commit()
    c.execute("SELECT COUNT(*) FROM registry_enriched")
    total = c.fetchone()[0]
    log(f"Phase 2 done: {updated:,} upserts | Total rows: {total:,}")

def phase3_recalc_percentiles(conn):
    log("=== PHASE 3: RECALC PERCENTILES ===")
    c = conn.cursor()
    
    c.execute("SELECT EIN, NTEE1, total_revenue FROM registry_enriched WHERE total_revenue > 0")
    rows = c.fetchall()
    
    from collections import defaultdict
    ntee_groups = defaultdict(list)
    for ein, ntee, rev in rows:
        if ntee:
            ntee_groups[ntee].append((ein, rev))
    
    updates = []
    for ntee, group in ntee_groups.items():
        group.sort(key=lambda x: x[1])
        n = len(group)
        for i, (ein, rev) in enumerate(group):
            pct = round((i / max(n-1, 1)) * 100, 2)
            updates.append((pct, ein))
    
    # Batch in chunks to avoid huge transaction
    chunk_size = 50000
    for i in range(0, len(updates), chunk_size):
        chunk = updates[i:i+chunk_size]
        c.executemany("UPDATE registry_enriched SET ntee1_percentile = ? WHERE EIN = ?", chunk)
        conn.commit()
        log(f"  Percentiles batch {i//chunk_size + 1}/{(len(updates)-1)//chunk_size + 1}")
    
    log(f"Recalculated {len(updates):,} percentiles across {len(ntee_groups)} NTEE groups")

def phase4_patch_api():
    log("=== PHASE 4: PATCH API FILES ===")
    patched = 0
    for root, dirs, files in os.walk(os.path.expanduser("~/meritgiving")):
        for f in files:
            if f.endswith('.py') and 'overnight' not in f:
                fpath = os.path.join(root, f)
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                orig = content
                content = re.sub(r'FROM\s+registry\b(?!\w)', 'FROM registry_enriched', content, flags=re.IGNORECASE)
                content = re.sub(r'INTO\s+registry\b(?!\w)', 'INTO registry_enriched', content, flags=re.IGNORECASE)
                if content != orig:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    patched += 1
    log(f"Patched {patched} API files")

def swap_db():
    log("=== SWAPPING DB BACK ===")
    if os.path.exists(BACKUP_DB):
        os.remove(BACKUP_DB)
    shutil.move(DB_PATH, BACKUP_DB)
    shutil.move(WORK_DB, DB_PATH)
    log(f"Swapped complete. Backup: {BACKUP_DB}")

def main():
    log("=" * 60)
    log("OVERNIGHT SYNC v2 STARTED")
    log("=" * 60)
    
    t0 = time.time()
    copy_db()
    
    conn = sqlite3.connect(WORK_DB)
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA synchronous=NORMAL")
    
    try:
        phase1_dedupe(conn)
        phase2_merge_990s(conn)
        phase3_recalc_percentiles(conn)
        phase4_patch_api()
        conn.close()
        swap_db()
        elapsed = time.time() - t0
        log(f"ALL DONE in {elapsed/60:.1f} minutes")
    except Exception as e:
        log(f"FATAL: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
