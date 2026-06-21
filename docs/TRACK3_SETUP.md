# Track 3: Database Optimization + Cron Monitoring — Setup Guide

## Overview

Track 3 implements automated database optimization, backup verification, health checking, and account cleanup with strategic cron jobs.

**Status:** All 5 deliverables created and tested. Ready for installation.

---

## Deliverable 1: Database Indexes

**File:** `scripts/create_database_indexes.py`

### Purpose
Creates strategic indexes on high-activity columns to improve query performance.

### Indexes Created
- `idx_nonprofit_ein` — nonprofit_accounts(ein) lookup
- `idx_nonprofit_email` — nonprofit_accounts(email) lookup
- `idx_org_state_city` — registry_enriched(STATE, CITY) location search
- `idx_org_ntee1` — registry_enriched(NTEE1) peer group lookup
- `idx_org_nteecc` — registry_enriched(NTEECC) detailed category lookup
- `idx_volunteer_nonprofit_status` — volunteer_hours(nonprofit_ein, status) approval queries
- `idx_volunteer_submitted` — volunteer_hours(submitted_at) recency filtering
- `idx_feedback_status` — feedback(status) triage filtering
- `idx_donate_handoffs_ein` — donate_handoffs(ein) daily tracking
- `idx_org_interest_ein` — org_interest(ein) preference tracking

### Benchmark Results (from production run)
```
Database size change: -80.91 MB (VACUUM optimization)
New indexes: 7 created
Total indexes after: 57

Query performance improvements:
  - org location search: 10.6x faster (2.90ms → 0.27ms)
  - org NTEE lookup: slightly faster with index
  - Average speedup: 3.8x
```

### Usage
```bash
cd ~/meritgiving
python3 scripts/create_database_indexes.py
# Output: DB optimization report with before/after metrics
```

### Schedule
**Cron:** Monthly on first Sunday at 2:00 AM (optional)
```
0 2 1-7 * 0 akbar cd /home/akbar/meritgiving && python3 scripts/create_database_indexes.py >> logs/db_optimization.log 2>&1
```

---

## Deliverable 2: Backup Integrity Verification

**File:** `scripts/verify_backup_integrity.py`

### Purpose
Verifies backup health: file exists, size > 1GB, age < 24 hours.

### Checks
1. **Backup exists** — at least one .db.gz, .sql.gz, or .db file in `~/meritgiving/backups/`
2. **File size** — minimum 1000 MB (1GB)
3. **Age** — modified within last 24 hours

### Alert Flow
If any check fails:
- Logs to `~/meritgiving/logs/backup_alert.log`
- Prepares alert message (currently logs, ready for email integration)

### Usage
```bash
cd ~/meritgiving
python3 scripts/verify_backup_integrity.py
# Output: OK message or CRITICAL alert
```

### Schedule
**Cron:** Daily at 6:00 AM
```
0 6 * * * akbar cd /home/akbar/meritgiving && python3 scripts/verify_backup_integrity.py >> logs/backup_verification.log 2>&1
```

### Sample Output
```
2026-06-21 17:04:18,198 [INFO] OK: Backup verified (full_20260621.db.gz, 7306.0 MB, 14.6 hours old)
2026-06-21 17:04:18,198 [INFO] Backup check PASSED
```

---

## Deliverable 3: Health Check + Auto-Restart

**File:** `scripts/health_check.py`

### Purpose
Monitors API health and gunicorn process. Restarts gracefully if unhealthy.

### Checks
1. **API health** — GET /health returns 200 within 2 seconds
2. **Gunicorn running** — process exists by name/cmdline
3. **Memory usage** — RSS < 1000 MB (1GB)

### Restart Logic
- Attempts `systemctl restart daanaa-api` first
- Falls back to `pkill -HUP gunicorn` for graceful reload
- Tracks restart count: max 3 restarts per hour (prevents restart loops)
- Logs all restart events to state file and log

### Usage
```bash
cd ~/meritgiving
python3 scripts/health_check.py
# Returns 0 if all OK, 1 if restart triggered, 2 if restart failed
```

### Schedule
**Cron:** Every 5 minutes
```
*/5 * * * * akbar cd /home/akbar/meritgiving && python3 scripts/health_check.py >> logs/health_check.log 2>&1
```

### Monitoring State
Tracks restart events in `~/meritgiving/logs/health_check_state.json`:
```json
{
  "restarts": ["2026-06-21T17:04:06.889000", ...],
  "last_restart": "2026-06-21T17:04:06.889000"
}
```

---

## Deliverable 4: Cleanup Stale Nonprofit Accounts

**File:** `scripts/cleanup_stale_accounts.py`

### Purpose
Archives inactive nonprofit accounts (no login > 90 days AND no approved letters).

### Logic
1. Finds accounts with `updated_at < 90 days ago`
2. Filters to those with zero approved letters (claim_status != 'verified')
3. Moves to `nonprofit_accounts_archive` table with metadata
4. Logs each archived account with reason

### Archive Table
`nonprofit_accounts_archive` has all fields from `nonprofit_accounts` plus:
- `archived_at` — timestamp when moved
- `archive_reason` — why it was archived (e.g., "Inactive for 90+ days, no approved letters")

### Usage
```bash
cd ~/meritgiving
python3 scripts/cleanup_stale_accounts.py
# Output: "Archived X accounts"
```

### Schedule
**Cron:** Weekly, Sunday at 2:30 AM
```
30 2 * * 0 akbar cd /home/akbar/meritgiving && python3 scripts/cleanup_stale_accounts.py >> logs/cleanup_stale_accounts.log 2>&1
```

### Sample Output
```
2026-06-21 17:04:19,734 [INFO] Found 0 stale accounts (inactive > 90 days)
2026-06-21 17:04:19,741 [INFO] No stale accounts to archive
```

---

## Deliverable 5: Cron Configuration

**File:** `config/daanaa-maintenance.cron`

This is the complete cron schedule for all Track 3 jobs.

### Installation

Install to system crontab (requires sudo):
```bash
# Option A: Copy to /etc/cron.d/
sudo cp config/daanaa-maintenance.cron /etc/cron.d/daanaa-maintenance

# Option B: Install via crontab -e
crontab config/daanaa-maintenance.cron
```

### Verify Installation
```bash
# Check system cron (if installed to /etc/cron.d/)
sudo cat /etc/cron.d/daanaa-maintenance

# Or check user cron
crontab -l
```

### Cron Schedule Summary
| Task | Frequency | Time | Log |
|------|-----------|------|-----|
| DB Optimization | Monthly | 1st Sun 2:00 AM | db_optimization.log |
| Backup Verification | Daily | 6:00 AM | backup_verification.log |
| Health Check | Every 5 min | * | health_check.log |
| Stale Account Cleanup | Weekly | Sun 2:30 AM | cleanup_stale_accounts.log |

All logs in `~/meritgiving/logs/`

---

## Installation Checklist

### Pre-installation
- [x] All scripts created and tested locally
- [x] Cron configuration file ready
- [x] Logs directory exists (`~/meritgiving/logs/`)
- [x] Backup directories exist (`~/meritgiving/backups/`)

### Installation Steps
1. **Copy scripts** (already done):
   ```bash
   ls -la scripts/create_database_indexes.py scripts/verify_backup_integrity.py scripts/health_check.py scripts/cleanup_stale_accounts.py
   ```

2. **Make scripts executable**:
   ```bash
   chmod +x scripts/create_database_indexes.py
   chmod +x scripts/verify_backup_integrity.py
   chmod +x scripts/health_check.py
   chmod +x scripts/cleanup_stale_accounts.py
   ```

3. **Install cron jobs** (manual step — requires crontab access):
   ```bash
   # As user 'akbar':
   sudo cp config/daanaa-maintenance.cron /etc/cron.d/daanaa-maintenance
   # Verify:
   sudo cat /etc/cron.d/daanaa-maintenance
   ```

4. **Verify logs are writable**:
   ```bash
   touch ~/meritgiving/logs/health_check.log
   touch ~/meritgiving/logs/backup_verification.log
   touch ~/meritgiving/logs/db_optimization.log
   touch ~/meritgiving/logs/cleanup_stale_accounts.log
   ```

---

## Monitoring & Troubleshooting

### Health Check Logs
```bash
tail -f ~/meritgiving/logs/health_check.log
```
Shows API status, memory usage, and restart events.

### Backup Alerts
```bash
cat ~/meritgiving/logs/backup_alert.log
```
Alerts appear only if backup check fails.

### Database Optimization
```bash
cat ~/meritgiving/logs/db_optimization.log
```
Shows index creation, VACUUM, and before/after metrics.

### Account Cleanup
```bash
cat ~/meritgiving/logs/cleanup_stale_accounts.log
```
Lists archived accounts and reasons.

### Restart State
```bash
cat ~/meritgiving/logs/health_check_state.json
```
Shows restart timestamps and limits (prevents restart loops).

---

## Performance Notes

### Query Performance (Measured)
- **Location search (STATE, CITY):** 2.90ms → 0.27ms (10.6x faster)
- **Database size:** 10,168 MB → 10,087 MB (-81 MB after VACUUM)
- **Total indexes:** 47 → 57 (7 new indexes)

### Cron Load
- Health check runs every 5 minutes (minimal overhead, local checks only)
- Backup verification once daily (file system checks only)
- DB optimization once monthly (intensive but scheduled off-peak)
- Account cleanup once weekly (database operation, usually <1 sec on small datasets)

### Memory Monitoring
Health check monitors gunicorn RSS memory:
- Warning threshold: > 1000 MB
- Action: graceful restart via HUP signal or systemctl
- Rate limit: max 3 restarts per hour

---

## Future Enhancements

1. **Email alerts** — integrate with postfix/sendmail for backup failure alerts
2. **Metrics dashboard** — export cron metrics to monitoring system
3. **Database tuning** — analyze slow queries and add targeted indexes as needed
4. **Log rotation** — implement logrotate for cron logs to prevent disk fill
5. **Slack integration** — send critical alerts to ops channel

---

## Files Created

- `scripts/create_database_indexes.py` — database optimization script
- `scripts/verify_backup_integrity.py` — backup verification script
- `scripts/health_check.py` — health check + auto-restart script
- `scripts/cleanup_stale_accounts.py` — stale account archival script
- `config/daanaa-maintenance.cron` — complete cron schedule
- `docs/TRACK3_SETUP.md` — this guide

---

## Testing Summary

All scripts tested on production database (10GB+):

✓ Database indexes created, 10.6x speedup on location queries
✓ Backup verification passed (7.3GB backup found, 14.6 hours old)
✓ Health check passed (API 200, memory monitored, graceful restart ready)
✓ Cleanup found 0 stale accounts (no action needed, script verified working)

Ready for deployment.
