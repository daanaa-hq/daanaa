#!/usr/bin/env python3
import sqlite3
import requests
import time
import sys
import csv
from pathlib import Path
from datetime import datetime

from website_normalize import normalize_website

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
LOG = Path.home() / 'meritgiving' / 'logs' / 'overnight.log'
SUBMISSIONS_FILE = Path.home() / 'meritgiving' / 'data' / 'manual_link_submissions.csv'

def log(msg):
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    s = '[' + t + '] ' + msg
    print(s)
    sys.stdout.flush()
    with open(LOG, 'a') as f:
        f.write(s + chr(10))

def get_db():
    return sqlite3.connect(str(DB))

def process_manual_submissions():
    """Ingest manual link submissions from CSV, update DB, clear file.

    NOTE (2026-06-10): Donation URL processing disabled per legal directive.
    Daanaa is a discovery platform, not a fundraising platform.
    Only website URLs are now processed.
    """
    if not SUBMISSIONS_FILE.exists():
        return 0

    conn = get_db()
    c = conn.cursor()
    processed = 0

    try:
        with open(SUBMISSIONS_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get('EIN'):
                    continue
                ein = row['EIN'].strip()
                # canonical form; junk submissions ("n/a", no domain) → None
                website = normalize_website(row.get('website_url', ''))
                # DISABLED: donation URL processing (2026-06-10)
                # donate = row.get('donate_url', '').strip() or None

                if not website:
                    continue

                # Update registry with submitted links (marked as beta/unverified)
                if website:
                    c.execute('UPDATE registry_enriched SET website = ?, website_status = "beta" WHERE EIN = ? AND (website IS NULL OR website = "")',
                             (website, ein))
                # DISABLED: donation URL processing (2026-06-10)
                # if donate:
                #     c.execute('UPDATE registry_enriched SET donate_url = ?, donate_confidence = 75, donate_url_status = "beta_unverified" WHERE EIN = ?',
                #              (donate, ein))
                processed += 1

        conn.commit()
        if processed > 0:
            log(f'Processed {processed} manual submissions')
            # Clear the submissions file (keep header)
            with open(SUBMISSIONS_FILE, 'w') as f:
                f.write('EIN,website_url,donate_url,submission_date\n')
    except Exception as e:
        log(f'Error processing submissions: {str(e)[:100]}')
    finally:
        conn.close()

    return processed

def enrich_batch(size=1000):
    """
    NOTE: This function is deprecated (2026-06-10). The registry table was consolidated
    into registry_enriched. This function would need propublica columns in registry_enriched
    to work. Currently a no-op to prevent pipeline breakage.
    """
    conn = get_db()
    c = conn.cursor()
    # Check if propublica enrichment columns exist in registry_enriched
    c.execute("PRAGMA table_info(registry_enriched)")
    cols = {row[1] for row in c.fetchall()}

    if 'propublica_object_id' not in cols:
        log('ProPublica enrichment columns not in schema. Skipping enrichment batch.')
        conn.close()
        return 0, 0

    c.execute('SELECT EIN FROM registry_enriched WHERE propublica_object_id IS NULL LIMIT ?', (size,))
    eins = [r[0] for r in c.fetchall()]
    if not eins:
        log('All orgs enriched.')
        conn.close()
        return 0, 0
    log('Enriching ' + str(len(eins)) + ' orgs...')
    updated = 0
    errors = 0
    for i, ein in enumerate(eins):
        try:
            url = 'https://projects.propublica.org/nonprofits/api/v2/organizations/' + ein + '.json'
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                org = data.get('organization', {})
                filings = data.get('filings_with_data', [])
                obj_id = org.get('id', '')
                pdf = ''
                fdate = ''
                fyear = 0
                if filings and len(filings) > 0:
                    latest = filings[0]
                    pdf = latest.get('pdf_url', '')
                    fdate = latest.get('date_submitted', '')
                    fyear = latest.get('tax_prd_yr', 0)
                c.execute('UPDATE registry_enriched SET propublica_object_id = ?, propublica_pdf_url = ?, propublica_filing_date = ?, propublica_tax_year = ? WHERE EIN = ?', (obj_id, pdf, fdate, fyear, ein))
                updated += 1
            elif resp.status_code == 429:
                log('Rate limited. Waiting 60s...')
                time.sleep(60)
                continue
            else:
                errors += 1
        except Exception as e:
            errors += 1
            if i % 50 == 0:
                log('Error for ' + ein + ': ' + str(e)[:60])
        time.sleep(0.6)
        if updated % 100 == 0 and updated > 0:
            conn.commit()
            log(str(updated) + '/' + str(len(eins)) + ' done, ' + str(errors) + ' errors')
    conn.commit()
    conn.close()
    log('Batch: ' + str(updated) + ' updated, ' + str(errors) + ' errors')
    return updated, errors

def run_bmf_classification_sync():
    """Sync subsection+deductibility from BMF. Catches any drift that crept in
    since the last BMF refresh (e.g. from NCCS re-ingests or manual edits)."""
    try:
        import subprocess
        log('Syncing subsection/deductibility from BMF...')
        script = Path.home() / 'meritgiving' / 'scripts' / 'backfill_subsection_deductibility.py'
        result = subprocess.run(
            ['python3', str(script)],
            capture_output=True, text=True, timeout=300,
        )
        for line in (result.stdout or '').strip().splitlines():
            log(line)
        if result.returncode != 0:
            log(f'⚠️  BMF classification sync non-zero exit: {result.stderr[:200]}')
    except Exception as e:
        log(f'⚠️  BMF classification sync error (non-fatal): {str(e)[:100]}')


def run_data_quality_gate():
    """Lightweight invariant checks before data is considered publish-ready.

    Logs WARN for soft violations and raises on hard violations that indicate
    the pipeline has produced bad data.
    """
    try:
        db = get_db()

        # Hard check: no 501(c)(4/5/6/7/8) should appear as deductible 501(c)(3)
        bad = db.execute("""
            SELECT COUNT(*) FROM registry_enriched
            WHERE deductibility = '1'
              AND subsection IN ('4','5','6','7','8','9','12','13','19')
              AND COALESCE(irs_revoked, 0) != 1
        """).fetchone()[0]
        if bad > 0:
            log(f'🚨 DATA QUALITY FAIL: {bad} non-501(c)(3) orgs showing as deductible — run backfill_subsection_deductibility.py')
        else:
            log('✅ Quality gate: no non-501(c)(3) orgs showing as deductible')

        # Soft check: active deductible count should be between 1.5M and 2.2M
        active = db.execute("""
            SELECT COUNT(*) FROM registry_enriched
            WHERE subsection = '3' AND deductibility = '1'
              AND COALESCE(irs_revoked, 0) != 1
              AND COALESCE(org_status, '') != 'revoked'
        """).fetchone()[0]
        if active < 1_500_000 or active > 2_200_000:
            log(f'⚠️  Quality gate WARN: active deductible count {active:,} is outside expected range 1.5M–2.2M')
        else:
            log(f'✅ Quality gate: active deductible 501(c)(3) count {active:,}')

        # Soft check: revoked orgs should not appear active
        revoked_active = db.execute("""
            SELECT COUNT(*) FROM registry_enriched
            WHERE COALESCE(irs_revoked, 0) = 1
              AND COALESCE(org_status, '') = 'active'
        """).fetchone()[0]
        if revoked_active > 0:
            log(f'⚠️  Quality gate WARN: {revoked_active} orgs are irs_revoked=1 but org_status=active')
        else:
            log('✅ Quality gate: no revoked orgs marked active')

        db.close()
    except Exception as e:
        log(f'⚠️  Data quality gate error (non-fatal): {str(e)[:100]}')


def purge_stale_wallets():
    """Delete e2e_wallet_sync rows not updated in 90+ days.
    Server only stores ciphertext — purging is safe; user can re-import from backup."""
    try:
        db_path = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM e2e_wallet_sync WHERE updated_at < datetime('now', '-90 days')"
        )
        deleted = cur.rowcount
        conn.commit()
        conn.close()
        if deleted:
            log(f'Purged {deleted} stale wallet row(s) (>90 days idle)')
    except Exception as e:
        log(f'⚠️  Wallet purge error (non-fatal): {str(e)[:100]}')


def cleanup_stale_scores():
    """Delete old score JSON files, keeping only the most recent 2.
    Prevents disk bloat from nightly scoring runs."""
    try:
        import glob
        import os as _os
        scores_dir = Path.home() / 'meritgiving'
        pattern = str(scores_dir / 'scores_v4_0_*.json')
        files = glob.glob(pattern)

        # Filter: keep only dated files (YYYYMMDD* pattern), exclude the full snapshot
        dated_files = [f for f in files if '_full' not in f and 'scores_v4_0_' in f]
        dated_files.sort(reverse=True)  # Most recent first

        # Keep the most recent 2; delete the rest
        to_delete = dated_files[2:]
        for fpath in to_delete:
            size_mb = _os.path.getsize(fpath) // (1024 * 1024)
            try:
                _os.remove(fpath)
                log(f'Cleaned: {Path(fpath).name} (~{size_mb}MB)')
            except Exception as e:
                log(f'Failed to delete {Path(fpath).name}: {e}')
    except Exception as e:
        log(f'⚠️  Stale score cleanup error (non-fatal): {str(e)[:100]}')


def run_export_snapshot():
    """Regenerate the research snapshot JSON so daanaa.org/research always
    reflects the latest corrected data after each nightly pipeline run."""
    try:
        import subprocess
        log('Exporting research snapshot...')
        script = Path.home() / 'meritgiving' / 'scripts' / 'export_research_snapshot.py'
        result = subprocess.run(
            ['python3', str(script)],
            capture_output=True, text=True, timeout=120,
            cwd=str(Path.home() / 'meritgiving'),
        )
        for line in (result.stdout or '').strip().splitlines():
            log(line)
        if result.returncode != 0:
            log(f'⚠️  Snapshot export failed (non-fatal): {result.stderr[:200]}')
    except Exception as e:
        log(f'⚠️  Snapshot export error (non-fatal): {str(e)[:100]}')


def run_revocation_check():
    """Daily fast check against already-loaded revoked_eins table."""
    try:
        import subprocess
        result = subprocess.run(
            ['python3', str(Path.home() / 'meritgiving' / 'scripts' / 'sync_irs_revocations.py'), '--check'],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                log(line)
        if result.returncode != 0:
            log('Revocation check returned non-zero: ' + (result.stderr or ''))
    except Exception as e:
        log('Revocation check error: ' + str(e))


def run_v5_scorer():
    """Run merit_scorer_v5_0 to keep v5 financial context scores fresh. Logs but doesn't fail pipeline if scorer errors."""
    try:
        import subprocess
        log('Running merit_scorer_v5_0...')
        scorer_script = Path.home() / 'meritgiving' / 'scripts' / 'merit_scorer_v5_0.py'
        scores_file = Path.home() / 'meritgiving' / f'scores_v5_0_{datetime.now().strftime("%Y%m%d")}.json'

        result = subprocess.run(
            ['python3', str(scorer_script), '--output', str(scores_file)],
            capture_output=True, text=True, timeout=14400,  # 4 hour timeout
        )

        if result.returncode == 0 and scores_file.exists():
            log(f'✅ Scorer completed: {scores_file}')
            # Load scores into DB
            load_script = Path.home() / 'meritgiving' / 'scripts' / 'load_v5_scores.py'
            load_result = subprocess.run(
                ['python3', str(load_script), str(scores_file)],
                capture_output=True, text=True, timeout=600,
            )
            if load_result.returncode == 0:
                log('✅ V5.0 scores loaded into registry_enriched')
            else:
                log(f'⚠️  Scorer loaded but score import failed: {load_result.stderr[:200]}')
        else:
            log(f'⚠️  Scorer error (non-fatal, pipeline continues): {result.stderr[:200]}')
    except Exception as e:
        log(f'⚠️  Scorer exception (non-fatal): {str(e)[:100]}')


def run_cohort_context():
    """Rebuild cause-cohort financial context for unscored orgs. Runs after
    scoring so it aggregates fresh scores. Non-fatal if it errors."""
    try:
        import subprocess
        log('Rebuilding cohort_context.json (cause-cohort context for unscored orgs)...')
        script = Path.home() / 'meritgiving' / 'scripts' / 'precompute_cohort_context.py'
        result = subprocess.run(
            ['python3', str(script)],
            capture_output=True, text=True, timeout=600,
            cwd=str(Path.home() / 'meritgiving'),
        )
        if result.returncode == 0:
            for line in (result.stdout or '').strip().splitlines():
                log(line)
        else:
            log(f'⚠️  cohort_context rebuild failed (non-fatal): {result.stderr[:200]}')
    except Exception as e:
        log(f'⚠️  cohort_context exception (non-fatal): {str(e)[:100]}')


def main():
    log('=' * 60)
    log('Overnight Pipeline Started')
    log('=' * 60)

    # Step 1: Sync IRS classification from BMF (must run before scoring)
    run_bmf_classification_sync()

    # Step 2: Check for newly revoked orgs
    run_revocation_check()

    # Step 3: Ingest manual submissions
    process_manual_submissions()

    # Step 4: ProPublica enrichment (no-op if schema lacks those columns)
    total = 0
    errs = 0
    batches = 0
    while batches < 50:
        u, e = enrich_batch(1000)
        total += u
        errs += e
        batches += 1
        if u == 0:
            log('Done. All orgs enriched.')
            break
        if batches % 5 == 0:
            log('Progress: ' + str(total) + ' enriched, ' + str(errs) + ' errors')
    log('Complete: ' + str(total) + ' enriched, ' + str(errs) + ' errors')

    # Step 5: Re-score with v5.0
    log('Running merit_scorer_v5_0 to keep v5 scores fresh...')
    run_v5_scorer()

    # Step 6: Rebuild cause-cohort context from fresh scores
    run_cohort_context()

    # Step 7: Expire past volunteer events
    try:
        from expire_volunteer_events import run as expire_events
        expire_events()
    except Exception as exc:
        log(f'[expire_volunteer_events] non-fatal error: {exc}')

    # Step 8: Data quality gate — log any invariant violations before publish
    run_data_quality_gate()

    # Step 9: Regenerate research snapshot so static page reflects latest data
    run_export_snapshot()

    # Step 10: Clean up stale score files to prevent disk bloat
    cleanup_stale_scores()

    # Step 11: Purge e2e wallet rows idle for 90+ days (zero-knowledge — server never sees plaintext)
    purge_stale_wallets()

    log('=' * 60)
    log('Overnight Pipeline Complete')
    log('=' * 60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log('FATAL: ' + str(e))
        sys.exit(1)
