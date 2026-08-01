# Database Protection Procedures

**Incident:** Jul 31, 2026 — Database corruption during Phase 1 deployment  
**Impact:** 1.85M org pages unable to load for ~2 hours  
**Root Cause:** Unknown corruption event during precompute rebuild  
**Resolution:** Restored from Jul 28 backup (loss of 3 days of enrichment data)  
**Cost:** 2 hours downtime, 3 days of website/donation link discovery lost

This document establishes procedures to prevent future data loss.

---

## Three-Tier Backup Strategy

### Tier 1: Hourly Snapshots (24-hour retention)
- **Purpose:** Recovery from very recent corruption/mistakes
- **Frequency:** Hourly, automated via cron
- **Retention:** Last 24 hours (oldest deleted)
- **Use Case:** "Restore to 2 hours ago" if a bad batch write occurs

### Tier 2: Daily Full Backups (30-day retention)
- **Purpose:** Disaster recovery with minimal data loss
- **Frequency:** Once per day, automated via cron
- **Retention:** Last 30 days (older moved to archive)
- **Use Case:** "Restore to yesterday" if corruption discovered late
- **File Size:** ~23 GB each (disk space: ~690 GB for 30 days)

### Tier 3: Pre-Enrichment Checkpoints (last 5 only)
- **Purpose:** Atomicity check before major data mutations
- **Frequency:** Manual, before enrichment/scoring pipelines run
- **Retention:** Last 5 checkpoints
- **Use Case:** "Restore to pre-pipeline state" if enrichment fails/corrupts

### Tier 4: Archive (indefinite)
- **Purpose:** Long-term historical record, incident investigation
- **Frequency:** Older tiers rotate here automatically
- **Retention:** All archived backups (until manually cleaned)
- **Use Case:** "What was the database state on July 15?" for post-mortems

---

## Automated Backup Cron Schedule

Add these lines to crontab (`crontab -e`):

```bash
# Hourly backup (runs every hour at minute 05)
5 * * * * /home/akbar/meritgiving/scripts/backup_strategy.sh >> /home/akbar/meritgiving/logs/backup_cron.log 2>&1

# Daily backup (runs at 2:00 AM UTC / 9:00 PM CDT)
0 2 * * * /home/akbar/meritgiving/scripts/backup_strategy.sh >> /home/akbar/meritgiving/logs/backup_cron.log 2>&1

# Database integrity check (daily, 3:00 AM UTC / 10:00 PM CDT)
0 3 * * * sqlite3 /home/akbar/meritgiving/data/merit_registry.db "PRAGMA integrity_check LIMIT 1;" >> /home/akbar/meritgiving/logs/integrity_check.log 2>&1
```

Install with:
```bash
crontab -e
# Paste the above lines
# Save and exit
```

Verify:
```bash
crontab -l | grep backup_strategy
```

---

## Pre-Enrichment Protection

**Before running any major pipeline (enrichment, scoring, website discovery):**

```bash
# 1. Create pre-enrichment checkpoint
/home/akbar/meritgiving/scripts/backup_strategy.sh pre-enrichment

# 2. Run your pipeline
python3 /home/akbar/meritgiving/scripts/overnight_pipeline.py

# 3. Verify success (check org page loads)
curl http://localhost:5000/api/organizations/264837170 | head -5
```

If pipeline fails/corrupts:
```bash
# List available checkpoints
/home/akbar/meritgiving/scripts/backup_strategy.sh list

# Restore to the pre-enrichment state
/home/akbar/meritgiving/scripts/backup_strategy.sh restore /home/akbar/meritgiving/backups/production/merit_registry_pre_enrichment_YYYYMMDD_HHMMSS.db
```

---

## Recovery Procedures

### Scenario 1: "Pages are loading slowly / with missing data"
**Symptom:** Org pages respond but with NULL fields (website, donate_url)  
**Action:** Likely not a DB issue; check data pipeline logs instead  
**Recovery Time:** N/A (not a backup issue)

### Scenario 2: "Database says corrupted / org pages are 500 errors"
**Symptom:** API returns 500, or "database disk image is malformed"  
**Action:** Restore from most recent hourly backup

```bash
# 1. List available backups
/home/akbar/meritgiving/scripts/backup_strategy.sh list

# 2. Pick the most recent hourly backup BEFORE corruption started
# Example: merit_registry_hourly_20260801_120000.db

# 3. Restore
/home/akbar/meritgiving/scripts/backup_strategy.sh restore /home/akbar/meritgiving/backups/production/merit_registry_hourly_20260801_120000.db

# 4. Verify
curl http://localhost:5000/health
curl http://localhost:5000/api/organizations/264837170
```

**Recovery Time:** ~2-3 minutes (API restart included)  
**Data Loss:** Last 1 hour of writes (worst case)

### Scenario 3: "Enrichment pipeline corrupted the database"
**Symptom:** Error occurs during nightly pipeline, org pages fail afterward  
**Action:** Restore from pre-enrichment checkpoint

```bash
# 1. List checkpoints
ls -lht /home/akbar/meritgiving/backups/production/merit_registry_pre_enrichment_*.db

# 2. Restore to pre-pipeline state
/home/akbar/meritgiving/scripts/backup_strategy.sh restore /home/akbar/meritgiving/backups/production/merit_registry_pre_enrichment_YYYYMMDD_HHMMSS.db

# 3. Investigate pipeline failure (check logs, fix bug)
tail -100 /tmp/precompute_rebuild.log

# 4. Once fixed, run pipeline again with checkpoint
/home/akbar/meritgiving/scripts/backup_strategy.sh pre-enrichment
python3 /home/akbar/meritgiving/scripts/overnight_pipeline.py
```

**Recovery Time:** ~2-3 minutes  
**Data Loss:** Only the corrupted enrichment run; previous data intact

### Scenario 4: "Accidental data deletion / wrong script ran"
**Symptom:** Critical fields nullified, or bad data committed  
**Action:** Restore from daily backup (accept 1 day data loss)

```bash
# Restore to yesterday's state
/home/akbar/meritgiving/scripts/backup_strategy.sh restore /home/akbar/meritgiving/backups/production/merit_registry_daily_YYYYMMDD.db
```

**Recovery Time:** ~3-5 minutes  
**Data Loss:** Last 24 hours

---

## Monitoring & Alerting

### Manual Health Check (daily)

```bash
# Run this command to verify backup health
/home/akbar/meritgiving/scripts/backup_strategy.sh list

# Expected output: at least 3 recent backups (hourly, daily, checkpoint)
# If any backup is missing, check: /home/akbar/meritgiving/logs/backup_cron.log
```

### Log Files to Watch

```bash
# Backup execution logs
tail -20 /home/akbar/meritgiving/logs/backup_cron.log

# Backup strategy detailed log
tail -20 /home/akbar/meritgiving/logs/backup_strategy.log

# Database integrity checks
tail -20 /home/akbar/meritgiving/logs/integrity_check.log
```

### Red Flags (Escalate Immediately)

- ⚠️ Backup cron job hasn't run in >2 hours (check crontab + logs)
- ⚠️ Backup verification fails ("Backup file is corrupted")
- ⚠️ Database integrity check shows errors (not just timeout)
- ⚠️ Less than 1 hourly backup or 1 daily backup available
- ⚠️ Free disk space <50 GB (backups may fail)

---

## Disk Space Management

**Current:**
- Daily backups: ~23 GB each × 30 = ~690 GB
- Hourly backups: ~23 GB each × 24 = ~552 GB (rolling)
- Archive: Grows indefinitely

**Recommendations:**
1. Monitor disk usage weekly: `du -sh ~/meritgiving/backups/*`
2. If >1.5 TB, manually clean archive: `rm ~/meritgiving/backups/archive/merit_registry_*_2026-0[1-6]*.db`
3. Consider S3 backup for long-term archive (cost: ~$10/month for 1 year of backups)

---

## Operational Guidelines

### ✅ DO

- Create pre-enrichment checkpoint before ANY major data pipeline
- Verify backups exist before starting risky operations
- Check backup logs weekly
- Archive old backups to reduce disk usage
- Document any manual restore in LESSONS.md

### ❌ DON'T

- Run enrichment pipelines without backup (no exception)
- Delete backups manually without archiving first
- Ignore backup_cron.log errors
- Rely on only one tier of backup
- Restore without checking backup integrity first

---

## Incident Post-Mortem (Jul 31, 2026)

**What Happened:**
1. Phase 1 precompute rebuild started
2. Donation link pipeline crashed partway through
3. Database became corrupted (unknown root cause)
4. Org pages returned 500 errors for ~2 hours
5. Restored from Jul 28 backup

**Why It Wasn't Caught Sooner:**
- No hourly backups (procedure didn't exist)
- No pre-enrichment checkpoints
- Database integrity check didn't run
- Precompute logs truncated, error message cut off

**Improvements Made:**
- ✅ Implemented 3-tier backup strategy
- ✅ Automated cron backups (hourly + daily)
- ✅ Pre-enrichment checkpoints before major pipelines
- ✅ Database integrity monitoring
- ✅ This operational playbook

**Residual Risk:** Unknown. Root cause of corruption not identified (possibly: concurrent write, OOM event, disk I/O error, or SQLite bug under specific conditions). Monitoring should catch future incidents within 1 hour.

---

## Quick Reference

```bash
# List all available backups
/home/akbar/meritgiving/scripts/backup_strategy.sh list

# Create emergency checkpoint
/home/akbar/meritgiving/scripts/backup_strategy.sh pre-enrichment

# Restore from backup (replace FILENAME with actual backup)
/home/akbar/meritgiving/scripts/backup_strategy.sh restore /path/to/backup.db

# Check backup logs
tail -50 /home/akbar/meritgiving/logs/backup_strategy.log
```

---

**Last Updated:** 2026-08-01  
**Owner:** Akbar Khowaja (Founder)  
**Reviewed By:** Claude Code (AI Engineering Agent)  
**Status:** Active
