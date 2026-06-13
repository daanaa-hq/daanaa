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


def run_v4_scorer():
    """Run merit_scorer_v4_0 to keep scores fresh. Logs but doesn't fail pipeline if scorer errors."""
    try:
        import subprocess
        log('Running merit_scorer_v4_0...')
        scorer_script = Path.home() / 'meritgiving' / 'scripts' / 'merit_scorer_v4_0.py'
        scores_file = Path.home() / 'meritgiving' / f'scores_v4_0_{datetime.now().strftime("%Y%m%d")}.json'

        result = subprocess.run(
            ['python3', str(scorer_script), '--output', str(scores_file)],
            capture_output=True, text=True, timeout=14400,  # 4 hour timeout
        )

        if result.returncode == 0 and scores_file.exists():
            log(f'✅ Scorer completed: {scores_file}')
            # Load scores into DB
            load_script = Path.home() / 'meritgiving' / 'scripts' / 'load_v4_scores.py'
            load_result = subprocess.run(
                ['python3', str(load_script), str(scores_file)],
                capture_output=True, text=True, timeout=600,
            )
            if load_result.returncode == 0:
                log('✅ Scores loaded into registry_enriched')
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
    run_revocation_check()
    process_manual_submissions()
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
    log('=' * 60)
    log('Complete: ' + str(total) + ' enriched, ' + str(errs) + ' errors')
    log('=' * 60)
    # Re-score with v4.0 if any data changed (non-blocking)
    log('Running merit_scorer_v4_0 to keep scores fresh...')
    run_v4_scorer()
    # Rebuild cause-cohort context from fresh scores (non-blocking)
    run_cohort_context()
    log('=' * 60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log('FATAL: ' + str(e))
        sys.exit(1)
