# Daanaa v6 Daily and Weekly Data Operations Plan

Status: Operating plan for review
Scope: Local or staging server operations
Production scoring activation: Founder approval required

## Purpose

Keep Daanaa's nonprofit data current without corrupting the registry, losing
historical filings, mixing data sources, or publishing unsupported financial
comparisons.

The operating system must preserve these distinctions:

- IRS and public filing data
- NCCS data
- ProPublica metadata
- Organization-submitted information
- Daanaa inference

No process may silently convert missing values to zero, overwrite a prior tax
year, or replace a historical scoring run.

## Operating principles

1. All jobs are idempotent and safe to rerun.
2. Every source record retains source, source ID, tax year, retrieval time, and
   record hash.
3. Invalid records are quarantined, never silently skipped.
4. Revoked organizations are excluded from active peer groups.
5. Daily ingestion does not automatically change public scoring.
6. Weekly scoring creates a candidate run first.
7. Public activation requires validation and founder approval.
8. Backups are created before database writes.
9. Only one writer may run against the SQLite database at a time.
10. No external communication or production deployment is part of this job.

## Canonical server paths

Repository:

 /home/akbar/meritgiving

Database:

 /home/akbar/meritgiving/data/merit_registry.db

Do not write to legacy databases:

- data/meritgiving.db
- data/merit_state.db
- temporary or backup databases

Required directories:

- logs/v6/
- data/backups/v6/
- data/incoming/
- data/quarantine/v6/
- reports/v6/

## Job locking

Every scheduled job must use:

 data/v6_operation.lock

If a lock exists and the process is alive, exit without starting a second
writer. If the lock is stale, record the stale lock and require operator review
before removal.

Never run daily ingestion and weekly scoring concurrently.

## Daily schedule

### 01:00 — Preflight

Run:

    cd /home/akbar/meritgiving
    source venv/bin/activate

Check:

- Repository is readable
- Canonical database exists
- Disk space is sufficient
- Database is not locked unexpectedly
- Last backup exists
- No previous failed job is unresolved
- Python environment is available
- Required source files or caches are present

Record timestamp, Git commit, database size, free disk space, last successful
ingestion, and last successful candidate run.

Stop if the database fails:

    sqlite3 data/merit_registry.db "PRAGMA integrity_check;"

Expected result: ok

### 01:10 — Source discovery

Check for new or changed local source material:

- IRS BMF and revocation data
- IRS SOI extracts
- NCCS files
- ProPublica cache records
- Organization-submitted assertions awaiting review

For each source, record source name, file name or API record, tax year, file
size, record count, file hash, and retrieval timestamp.

Do not ingest an empty, truncated, unexpected, materially smaller, or already
processed source batch.

### 01:25 — Daily backup

Create a dated backup before any write:

    cp --reflink=auto data/merit_registry.db data/backups/v6/merit_registry_$(date -u +%Y%m%dT%H%M%SZ).db

Verify that the backup opens read-only.

Retain daily backups for 14 days, weekly backups for 12 weeks, and a backup
before every scoring candidate.

### 01:40 — Ingest new source records

Use the normalized ingestion path only.

Target tables:

- org_financial_years
- org_classifications
- org_operating_context
- org_data_assertions
- ingestion_audit_log
- ingestion_quarantine

Requirements:

- Use idempotent inserts
- Key financial records by EIN, tax year, source, and source record ID
- Never update an older tax year with a newer value
- Preserve competing source values
- Validate before scoring
- Quarantine invalid records
- Commit bounded batches
- Roll back a complete failed batch

Do not write directly to scoring assignments during daily ingestion.

### 02:15 — Revocation synchronization

Update revocation status from the current IRS revocation source.

Verify EIN formatting, source date, record count, unexpected mass changes, and
consistency between irs_revoked and org_status.

Run:

    SELECT COUNT(*) FROM registry_enriched
    WHERE irs_revoked = 1 AND org_status <> 'revoked';

    SELECT COUNT(*) FROM registry_enriched
    WHERE org_status = 'revoked' AND irs_revoked <> 1;

Both results must be zero.

Revocation updates may remove an organization from active peer groups, but must
not delete historical records.

### 02:30 — Data quality checks

Check duplicate and invalid EINs, missing tax years, negative financial values,
impossible totals, invalid NTEE codes, invalid geography codes, raw zeros,
broken hashes, and quarantine growth.

Track coverage for NTEECC, state, archetype, revenue, expenses, assets,
liabilities, net assets, reserves, tax year, program expenses, employees, and
board data.

### 03:00 — Post-ingestion integrity

Run:

    sqlite3 data/merit_registry.db "PRAGMA integrity_check;"

Verify foreign keys, normalized row counts, audit log, quarantine report,
database size change, and no unexpected changes to legacy scoring tables.

If any check fails, stop, preserve logs and the failed database, and do not
publish or rescore.

### 03:15 — Daily report

Write reports/v6/daily_YYYYMMDD.md containing job status, source batches,
records inserted, duplicates, quarantined records, revocation changes, field
coverage, integrity result, backup path, and follow-up work.

## Weekly scoring schedule

### Monday 02:00 — Weekly preflight

Confirm seven days of daily reports, no unresolved ingestion failures, completed
revocation sync, passing database integrity, populated normalized tables, a
complete source snapshot, and a fresh backup.

### Monday 02:15 — Freeze input snapshot

Create an immutable snapshot identifier containing backup path, source batch
IDs, source hashes, tax years, Git commit, and methodology version.

Scoring must read from this snapshot, not a changing live database.

### Monday 02:30 — Generate candidate scoring run

Create a new run ID with status candidate.

The scorer must:

- Exclude revoked organizations
- Use active deductible organizations
- Map states to four Census regions
- Use national fallback for DC, territories, military, overseas, and unknown
- Use verified revenue bands only
- Treat raw zero revenue as unavailable
- Apply the five-tier hierarchy
- Require at least five scoreable peers for numeric context
- Store conditional band context separately
- Exclude the organization itself from direct peer metrics
- Record source years and confidence

Never mark a new run active automatically.

### Monday 04:00 — Candidate validation

Check that assignment count matches the active population, EINs are unique,
revoked assignments equal zero, Tier 1 has verified revenue, Tier 2 is regional
conditional context, Tier 3 is broader regional context, Tier 4 is national,
Tier 5 contains no numeric values, numeric tiers have at least five scoreable
peers, and no invented revenue bands exist.

### Monday 05:00 — Fairness and stewardship review

Compare the candidate with the prior approved run by revenue band, region, NTEE,
archetype, organization size, data availability, and revocation status.

Flag large tier shifts caused only by missing data, disproportionate changes for
small organizations, regional coverage differences, unexplained archetype
changes, and sudden Tier 5 increases.

No tier is a moral or organizational quality judgment.

### Monday 06:00 — Candidate report

Write reports/v6/v6_candidate_RUN_ID.md with run ID, commit, input snapshot,
source years, tier distribution, field coverage, regional coverage, archetype
coverage, revenue-band coverage, threshold results, revocation results,
fairness findings, privacy results, and differences from the prior run.

### Monday 09:00 — Approval gate

The candidate remains inactive until the founder or authorized steward approves
the run ID, methodology version, input snapshot, limitations, reviewer, and
date.

Without approval, do not update public API selection, enable the frontend flag,
or deploy.

## Monitoring thresholds

Stop and alert if database integrity fails, source counts drop unexpectedly,
quarantine rises materially, revocations spike unexpectedly, numeric coverage
falls by more than five percentage points, Tier 5 rises by more than five
percentage points, any revoked organization enters a peer group, any numeric
tier has fewer than five scoreable peers, or private fields appear in an API
response.

## Rollback

For ingestion failure, stop the writer, preserve the failed database and logs,
restore the latest verified backup only after review, rerun integrity checks,
and mark the batch failed.

For scoring failure, leave the candidate inactive, preserve the run and report,
and continue serving the prior approved run.

For activation failure, disable the v6 flag, restore the prior selected run ID,
confirm frontend fallback, and record the incident.

## Required automation files

The dev team should implement:

- scripts/v6_daily_operations.sh
- scripts/v6_weekly_candidate.sh
- scripts/v6_validate_run.py
- scripts/v6_source_manifest.py
- scripts/v6_restore_verified_backup.sh

Each script must support dry-run mode, report output, explicit database paths,
explicit run IDs, locking, structured logs, and nonzero exit codes on failed
gates.

## Final rule

Daily work may improve the data foundation.

Weekly work may create a new candidate score.

Only an approved candidate may become the active public v6 context.
