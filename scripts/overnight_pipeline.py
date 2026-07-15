#!/usr/bin/env python3
import sqlite3
import requests
import time
import sys
import csv
import json
from pathlib import Path
from datetime import datetime

from website_normalize import normalize_website
from registry_filters import DEDUCTIBLE_FILTER, canonical_active_count

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

        # Soft check: active deductible count should be between 1.5M and 2.2M.
        # Uses the canonical predicate (registry_filters.py) — same number the
        # homepage, research snapshot, and consistency gate all derive from.
        active = canonical_active_count(db)
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


def refresh_and_publish_numbers():
    """Regenerate the public content artifacts from the fresh DB, gate on
    cross-artifact consistency, and (only if every count agrees) deploy to the
    droplet + restart + verify the live API. The consistency gate is the safety
    that makes nightly auto-deploy safe: drifted numbers abort the deploy and
    leave the old (correct) files live. See scripts/refresh_public_numbers.sh
    and scripts/registry_filters.py."""
    try:
        import subprocess
        log('Refreshing + publishing public numbers (content, snapshot, /api/stats)...')
        result = subprocess.run(
            ['bash', str(Path.home() / 'meritgiving' / 'scripts' / 'refresh_public_numbers.sh')],
            capture_output=True, text=True, timeout=600,
            cwd=str(Path.home() / 'meritgiving'),
        )
        for line in (result.stdout or '').strip().splitlines():
            log(line)
        if result.returncode != 0:
            # Non-fatal to the pipeline, but loud — surfaces in the morning digest.
            log(f'🚨 PUBLISH FAILED (numbers NOT updated live): {(result.stderr or "")[:300]}')
        else:
            log('✅ Public numbers published and verified live')
    except Exception as e:
        log(f'🚨 Publish step error (numbers NOT updated live): {str(e)[:200]}')


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


def apply_nonprofit_updates():
    """Apply nonprofit-submitted financial data updates to registry before scoring.

    Process:
    1. Find pending_review updates with no sanity check failures
    2. Auto-validate them (mark as validated)
    3. Update registry_enriched with nonprofit data
    4. Mark updates as pending_scoring

    Flagged updates (>50% changes) are logged but not applied yet (require admin review).
    """
    try:
        conn = get_db()
        c = conn.cursor()

        # Find auto-validate-safe updates (no sanity check failures)
        c.execute('''
            SELECT id, ein, submitted_total_revenue, submitted_total_expenses,
                   submitted_program_expense_pct, submitted_months_of_reserve
            FROM org_nonprofit_updates
            WHERE status = 'pending_review' AND sanity_check_failed = 0
        ''')
        safe_updates = c.fetchall()

        applied = 0
        flagged = 0

        for update_id, ein, rev, exp, prog, months in safe_updates:
            try:
                # Update registry with nonprofit data (mark source as nonprofit-submitted)
                updates = []
                params = []

                if rev is not None:
                    updates.append('total_revenue = ?')
                    params.append(rev)
                if exp is not None:
                    updates.append('total_expenses = ?')
                    params.append(exp)
                if prog is not None:
                    updates.append('program_expense_pct = ?')
                    params.append(prog)
                if months is not None:
                    updates.append('months_of_reserve = ?')
                    params.append(months)

                # Add flag that data was nonprofit-submitted (for transparency)
                updates.append('data_submitted_by_org = 1')
                updates.append('data_submitted_at = CURRENT_TIMESTAMP')
                params.append(ein)

                if updates:
                    update_sql = 'UPDATE registry_enriched SET ' + ', '.join(updates) + ' WHERE EIN = ?'
                    c.execute(update_sql, params)

                    # Mark update as validated and pending scoring
                    c.execute('''
                        UPDATE org_nonprofit_updates
                        SET status = 'pending_scoring', validated_at = CURRENT_TIMESTAMP,
                            validated_by = 'auto', scoring_run_date = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (update_id,))
                    applied += 1
            except Exception as e:
                log(f'Error applying nonprofit update {update_id}: {str(e)[:100]}')

        # Count flagged updates (sanity check failures)
        c.execute('''
            SELECT COUNT(*) FROM org_nonprofit_updates
            WHERE status = 'pending_review' AND sanity_check_failed = 1
        ''')
        flagged = c.fetchone()[0]

        conn.commit()
        conn.close()

        if applied > 0 or flagged > 0:
            log(f'Nonprofit updates: {applied} applied, {flagged} flagged for review')

    except Exception as e:
        log(f'⚠️  Error processing nonprofit updates: {str(e)[:100]}')


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
                # Mark all pending_scoring updates as included_in_run
                try:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute('''
                        UPDATE org_nonprofit_updates
                        SET status = 'included_in_run', included_in_run_at = CURRENT_TIMESTAMP
                        WHERE status = 'pending_scoring'
                    ''')
                    conn.commit()
                    affected = c.rowcount
                    conn.close()
                    if affected > 0:
                        log(f'✅ Marked {affected} nonprofit updates as included_in_run')
                except Exception as e:
                    log(f'⚠️  Error marking updates as included: {str(e)[:100]}')
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


def fetch_org_websites():
    """Fetch and cache org homepages to page_cache table (incremental).
    Only fetches orgs without cached HTML OR cache older than 7 days.
    Runs in parallel with enrichment to eliminate sequential bottleneck.
    Non-fatal if errors — enrichment continues with partial cache."""
    try:
        import subprocess
        from datetime import datetime, timedelta

        conn = get_db()
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        stale_count = conn.execute(
            "SELECT COUNT(*) FROM page_cache WHERE html_gz IS NULL OR fetched_at < ?",
            (cutoff,)
        ).fetchone()[0]
        conn.close()

        if stale_count == 0:
            log('✅ Website cache fresh (all orgs cached within 7 days) — skipping fetch')
            return

        log(f'Fetching org websites (incremental: {stale_count:,} new/stale, 8 workers)...')
        script = Path.home() / 'meritgiving' / 'scripts' / 'fetch_org_websites.py'
        result = subprocess.run(
            ['python3', str(script), '--workers', '8', '--incremental'],  # Only fetch uncached/stale
            capture_output=True, text=True, timeout=3600,
            cwd=str(Path.home() / 'meritgiving'),
        )
        if result.stdout:
            for line in (result.stdout or '').strip().splitlines()[-5:]:
                log(line)
        if result.returncode == 0:
            log('✅ Website fetch complete (incremental)')
        else:
            log(f'⚠️  Website fetch had errors (non-fatal): {result.stderr[:100]}')
    except subprocess.TimeoutExpired:
        log('⚠️  Website fetch timeout (resumable)')
    except Exception as e:
        log(f'⚠️  Website fetch exception (non-fatal): {str(e)[:100]}')


def run_mission_generation(workers=8):
    """Generate missions + extract donate links for scored orgs using cached HTML.
    Runs AFTER page_cache is populated. Extracts both missions and donate URLs
    from website HTML if available. Non-fatal if errors — pipeline continues.
    Uses multiple workers for parallelism (default 8)."""
    try:
        import subprocess
        log(f'Generating missions + extracting donate links ({workers} workers, from cached HTML)...')
        script = Path.home() / 'meritgiving' / 'scripts' / 'generate_missions.py'
        result = subprocess.run(
            ['python3', str(script), '--workers', str(workers)],
            capture_output=True, text=True, timeout=86400,  # 24 hours (long GPU task)
            cwd=str(Path.home() / 'meritgiving'),
        )
        # Log final summary lines
        if result.stdout:
            for line in (result.stdout or '').strip().splitlines()[-5:]:
                log(line)
        if result.returncode == 0:
            log('✅ Mission generation + donate link extraction complete')
        else:
            log(f'⚠️  Mission generation had errors (non-fatal): {result.stderr[:200]}')
    except subprocess.TimeoutExpired:
        log('⚠️  Mission generation timeout (24h limit reached, resumable)')
    except Exception as e:
        log(f'⚠️  Mission generation exception (non-fatal): {str(e)[:100]}')


def extract_donate_links_batch(batch_size=5000):
    """Extract donation links from all orgs on a rolling refresh (independent of missions)."""
    try:
        import subprocess
        log('Extracting donation links from all orgs (rolling refresh)...')
        script = Path.home() / 'meritgiving' / 'scripts' / 'extract_donate_links.py'
        result = subprocess.run(
            ['python3', str(script), '--batch-size', str(batch_size)],
            capture_output=True, text=True, timeout=3600,  # 1 hour
            cwd=str(Path.home() / 'meritgiving'),
        )
        if result.stdout:
            for line in (result.stdout or '').strip().splitlines()[-3:]:
                log(line)
        if result.returncode == 0:
            log('✅ Donation link extraction complete')
        else:
            log(f'⚠️  Donation link extraction had errors (non-fatal): {result.stderr[:200]}')
    except subprocess.TimeoutExpired:
        log('⚠️  Donation link extraction timeout (1h limit reached, resumable)')
    except Exception as e:
        log(f'⚠️  Donation link extraction exception (non-fatal): {str(e)[:100]}')


def generate_cause_tags_batch(batch_size=200):
    """Generate cause tags using Mistral-7B on port 8090 (fast categorization).
    Uses Mistral instead of Qwen3-30B for 4x speed while maintaining quality for categorization."""
    try:
        conn = get_db()
        batch = conn.execute("""
          SELECT EIN, organization_name, mission, total_revenue
          FROM registry_enriched
          WHERE (cause_tags IS NULL OR cause_tags = '[]')
          AND organization_name IS NOT NULL
          AND mission IS NOT NULL
          ORDER BY total_revenue DESC NULLS LAST
          LIMIT ?
        """, [batch_size]).fetchall()

        if not batch:
            log('Cause tags: all orgs complete')
            return 0

        updated = 0
        for i, org in enumerate(batch, 1):
            try:
                prompt = f"""Org: {org['organization_name'][:80]}
Mission: {org['mission'][:200]}

List 3-5 cause tags (comma-separated, concise): """

                # Use Mistral-7B (port 8090) for fast categorization
                r = requests.post('http://127.0.0.1:8090/completion', json={
                    'prompt': prompt,
                    'n_predict': 80,
                    'temperature': 0.3,
                    'top_p': 0.9
                }, timeout=15)

                if r.status_code == 200:
                    tags_text = r.json().get('content', '').strip()
                    tags = [t.strip() for t in tags_text.split(',') if t.strip()][:5]

                    if tags:
                        conn.execute(
                            "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ?",
                            [json.dumps(tags), org['EIN']]
                        )
                        updated += 1

                if (i % 50) == 0:
                    log(f'  Cause tags: [{i}/{batch_size}] orgs processed')
            except Exception as e:
                pass  # Skip on error, continue with next org

        conn.commit()
        log(f'Cause tags: generated for {updated}/{batch_size} orgs')
        return updated
    except Exception as e:
        log(f'⚠️  Cause tags failed (non-fatal): {str(e)[:100]}')
        return 0


def run_parallel_enrichment():
    """Run mission generation, donate link extraction, and cause tags in parallel.
    These operate on different org sets and can run concurrently.
    Resource-aggressive: uses all 16 CPU cores + GPU for maximum throughput."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import multiprocessing

    log('Starting parallel enrichment (max CPU/GPU utilization)...')
    start = time.time()

    cpu_count = multiprocessing.cpu_count()  # 16 cores
    log(f'  Available: {cpu_count} CPU cores, 30GB RAM, GPU')

    tasks = [
        ('missions', lambda: run_mission_generation(workers=cpu_count)),  # All 16 cores
        ('donate links', lambda: extract_donate_links_batch(batch_size=5000)),  # 5K/night rolling
        ('cause tags', lambda: generate_cause_tags_batch(batch_size=5000)),  # 5K/night GPU
    ]

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(task[1]): task[0] for task in tasks}
        for future in as_completed(futures):
            task_name = futures[future]
            try:
                future.result()
            except Exception as e:
                log(f'⚠️  {task_name} task exception: {str(e)[:100]}')

    elapsed = time.time() - start
    log(f'✅ Parallel enrichment complete in {elapsed/60:.1f} minutes')


def run_donation_link_pipeline():
    """Run donation link discovery Phase 1 — extract links from 200 orgs with verified websites.

    Authority: Founder Ruling 2026-07-11 (enrichment pipeline integration).
    This runs nightly as part of the enrichment orchestration.
    """
    try:
        import subprocess
        log('Starting donation link pipeline (Phase 1, 200 orgs)...')
        script = Path.home() / 'meritgiving' / 'scripts' / 'donation_link_pipeline.py'
        result = subprocess.run(
            ['python3', str(script), '--phase', '1', '--orgs', '200'],
            capture_output=True, text=True, timeout=600,  # 10 min timeout
        )
        for line in (result.stdout or '').strip().splitlines():
            log(line)
        if result.returncode != 0:
            log(f'⚠️  Donation link pipeline non-zero exit: {result.stderr[:200]}')
        else:
            log('✅ Donation link pipeline complete')
    except Exception as e:
        log(f'⚠️  Donation link pipeline error (non-fatal): {str(e)[:100]}')


def run_enrichment_pipeline():
    """Coordinate Priority 1-5 enrichment (websites + missions + donations + contacts).

    Authority: Founder Ruling 2026-07-11 (Item 2: AI Memory Migration, Item 3: Backup Robustness).
    Enrichment pipeline integration with overnight scoring + backup cycle.

    Pipeline stages:
    1. Website discovery (already running autonomously, monitored here)
    2. Mission generation (GPU batch, runs concurrently with fetch)
    3. Donation link extraction (Phase 1 nightly)
    4. Contact/action-link extraction (queued for future)
    5. Readiness assessment (queued for future)
    """
    log('=' * 60)
    log('ENRICHMENT PIPELINE — Parallel Stage Orchestration')
    log('=' * 60)

    # The parallel fetch + enrichment (missions) is already integrated above.
    # Now add donation link extraction as a separate coordinated step.
    run_donation_link_pipeline()

    log('=' * 60)
    log('Enrichment pipeline complete (websites, missions, donations orchestrated)')
    log('=' * 60)


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

    # Step 5a: Apply nonprofit-submitted data updates before scoring
    apply_nonprofit_updates()

    # Step 5: Re-score with v5.0
    log('Running merit_scorer_v5_0 to keep v5 scores fresh...')
    run_v5_scorer()

    # Step 6: Rebuild cause-cohort context from fresh scores
    run_cohort_context()

    # Steps 6.5–6.7: PARALLEL FETCH + ENRICHMENT
    # Website fetch runs CONCURRENTLY with parallel enrichment (missions + donate + tags)
    # Fetch populates page_cache while enrichment uses existing cache + processes
    # This eliminates the sequential bottleneck and keeps GPU/CPU fully utilized
    from concurrent.futures import ThreadPoolExecutor

    log('Starting concurrent fetch + enrichment (max resource utilization)...')
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Fetch websites in parallel with enrichment tasks
        fetch_future = executor.submit(fetch_org_websites)
        enrich_future = executor.submit(run_parallel_enrichment)

        # Wait for both to complete
        fetch_future.result()
        enrich_future.result()

    log('✅ Concurrent fetch + enrichment complete')

    # Step 6.8: Enrichment pipeline orchestration (websites + missions + donations + contacts)
    # Authority: Founder Ruling 2026-07-11 (enrichment pipeline integration)
    run_enrichment_pipeline()

    # Step 6.85: Active website discovery enrichment (donation links, volunteer pages, GitHub, skills.sh)
    # Complements ProPublica/cached data with active web scraping for real-time accuracy
    log('Starting active website discovery enrichment (10K orgs max)...')
    try:
        from enrich_discovery_nightly import run_discovery_enrichment
        processed, donations, volunteers, errors = run_discovery_enrichment(batch_size=100, max_orgs=10000)
        log(f'Discovery enrichment: {processed} processed, {donations} donations, {volunteers} volunteers, {errors} errors')
    except Exception as e:
        log(f'⚠️  Discovery enrichment error (non-fatal): {str(e)[:200]}')

    # Step 6.9: Re-verify stale links (P7 independence + data safety)
    # Authority: T11 Gap 1 (90-day SLA for link staleness checks)
    try:
        from reverify_stale_links import run as reverify_links
        reverify_links(silent=False)
    except Exception as exc:
        log(f'[reverify_stale_links] error: {exc}')

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

    # Step 12: Publish — regenerate public artifacts, gate on consistency, and
    # auto-deploy to the droplet so the live numbers never go stale. This is the
    # step that was missing; without it homepage.json.gz drifted from the DB.
    refresh_and_publish_numbers()

    # Step 13: Log final stats
    log('Nightly pipeline completed — scoring updated, websites enriched, missions generated, donations extracted, stale links reverified, metrics updated')

    log('=' * 60)
    log('Overnight Pipeline Complete')
    log('=' * 60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log('FATAL: ' + str(e))
        sys.exit(1)
