# Daanaa Backup & Disaster Recovery Strategy

## Backup Targets

### Home Server (Primary)
- **merit_registry.db** (1.8M orgs, ~8 GB)
  - Daily encrypted snapshot
  - 30-day retention (rolling)
  - Stored: `/backups/merit_registry/`

- **Precomputed browse cache** (1M org files, ~800 MB)
  - Weekly snapshot (after nightly pipeline)
  - Stored: `/backups/browse_cache/`

### Droplet (Production)
- **search.db** (FTS5 index, ~200 MB)
  - Daily automated snapshot
  - Stored: `/backups/search.db/`
  
- **Frontend assets** (3 MB)
  - Already tracked in git; re-deploy from source if needed
  - Stored: git history

## Backup Schedule

| What | When | Frequency | Retention | Time to Restore |
|------|------|-----------|-----------|-----------------|
| merit_registry.db | 2:00 AM daily | Daily | 30 days | 10 min |
| search.db (droplet) | 3:00 AM daily | Daily | 14 days | 5 min |
| browse cache | Sun 4:00 AM | Weekly | 8 weeks | 15 min |
| Frontend | On each deploy | Manual | Git history | 2 min |

## Backup Execution

### Home Server Daily Backup (2 AM)
```bash
# Encrypt + compress merit_registry.db
gzip -c data/merit_registry.db | \
  openssl enc -aes-256-cbc -salt \
  -out /backups/merit_registry/db_$(date +%Y%m%d).db.gz.enc

# Verify backup integrity
openssl enc -aes-256-cbc -d -in /backups/merit_registry/db_$(date +%Y%m%d).db.gz.enc \
  | gzip -t  # Test gzip integrity
```

### Droplet Daily Backup (3 AM)
```bash
# SSH into droplet and backup search.db
ssh root@162.243.97.179 "
  tar -czf /tmp/search.db.tar.gz /data/precompute/v1/search.db
  openssl enc -aes-256-cbc -salt \
    -in /tmp/search.db.tar.gz \
    -out /backups/search.db_\$(date +%Y%m%d).tar.gz.enc
"

# Copy to home server for redundancy
scp root@162.243.97.179:/backups/search.db_*.tar.gz.enc /backups/search.db/
```

## Disaster Recovery Procedures

### Scenario 1: merit_registry.db Corruption

**RTO:** 10 minutes | **RPO:** < 24 hours

```bash
# 1. Identify the backup (latest good snapshot)
ls -lh /backups/merit_registry/ | tail -5

# 2. Decrypt and decompress
BACKUP_DATE=20260620
openssl enc -aes-256-cbc -d \
  -in /backups/merit_registry/db_${BACKUP_DATE}.db.gz.enc | \
  gzip -dc > /tmp/restore.db

# 3. Restore (rename current, restore from backup)
mv data/merit_registry.db data/merit_registry.db.CORRUPT_$(date +%s)
cp /tmp/restore.db data/merit_registry.db

# 4. Verify
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched;"

# 5. Restart API (if running)
systemctl restart gunicorn  # or equivalent
```

**Post-disaster:**
- Check dmesg for disk errors
- Run VACUUM and PRAGMA integrity_check to verify the restored DB
- Alert to re-run nightly scorer if you restored from >24h ago

### Scenario 2: search.db Corruption (Droplet)

**RTO:** 5 minutes | **RPO:** < 24 hours

```bash
# SSH into droplet
ssh root@162.243.97.179 "

# 1. Stop gunicorn
systemctl stop gunicorn

# 2. Backup the corrupted file
mv /data/precompute/v1/search.db /data/precompute/v1/search.db.CORRUPT

# 3. Restore from backup
cd /backups/search.db
BACKUP_DATE=20260620
openssl enc -aes-256-cbc -d \
  -in search.db_${BACKUP_DATE}.tar.gz.enc | \
  tar -xz -C /data/precompute/v1/

# 4. Verify
sqlite3 /data/precompute/v1/search.db 'SELECT COUNT(*) FROM orgs;'

# 5. Restart API
systemctl start gunicorn
"
```

### Scenario 3: Droplet Disk Full

**RTO:** < 2 minutes | **RPO:** None (read-only operation)

The droplet serves precomputed files (read-only). If disk fills:

```bash
ssh root@162.243.97.179 "

# Identify large files
du -sh /data/* | sort -rh | head -10

# If precompute cache is the issue:
# - Remove old gem snapshots: rm /data/precompute/v1/browse/hidden_gems/OLD_*
# - Or: rsync --delete fresh copy from home server

# If search.db is too large (shouldn't happen; it's ~200 MB):
# - Rebuild from fresh export

# Free up space
du -sh /var/log/*  # Check logs
journalctl --vacuum=100M  # Trim systemd logs
"
```

### Scenario 4: Nightly Scorer Fails (Home Server)

**RTO:** Manual rerun | **RPO:** 1 day

```bash
# Check if scorer ran recently
sqlite3 data/merit_registry.db \
  "SELECT run_date FROM score_snapshots ORDER BY run_date DESC LIMIT 1;"

# If missing or stale, manually trigger
cd /home/akbar/meritgiving && \
  source venv/bin/activate && \
  python3 scripts/merit_scorer_v4_0.py

# Check for errors
tail -100 /var/log/nightly_pipeline.log | grep -i error

# After scoring, rebuild FTS:
python3 scripts/build_fts_index.py
```

### Scenario 5: Complete Droplet Failure

**RTO:** 30 minutes | **RPO:** 24 hours

1. **Spin up new droplet** (snapshot existing one for backup)
2. **Deploy from home server:**
   ```bash
   bash scripts/safe_deploy_droplet.sh
   ```
   This will:
   - Sync precomputed browse cache
   - Deploy droplet_api.py
   - Deploy frontend assets
   - Restart services

3. **Restore search.db from backup:**
   ```bash
   scp /backups/search.db/search.db_LATEST.tar.gz.enc root@NEW_IP:/tmp/
   # Decrypt and restore on new droplet
   ```

## Testing & Verification

### Monthly Backup Drill (1st of month, 10 AM)

```bash
# 1. Restore merit_registry.db to a test location
openssl enc -aes-256-cbc -d \
  -in /backups/merit_registry/db_$(date +%Y%m01).db.gz.enc | \
  gzip -dc > /tmp/test_registry.db

# 2. Verify integrity
sqlite3 /tmp/test_registry.db "
  PRAGMA integrity_check;
  SELECT COUNT(*) FROM registry_enriched;
  SELECT COUNT(*) FROM org_fts;
"

# 3. Verify recent org
sqlite3 /tmp/test_registry.db \
  "SELECT organization_name, updated_at FROM registry_enriched ORDER BY updated_at DESC LIMIT 1;"

# 4. Log results
echo "$(date): Backup test PASSED" >> /var/log/backup_tests.log
```

### Restore Speed Test (Quarterly)

Time an actual restore from the latest backup to measure RTO:

```bash
time (
  openssl enc -aes-256-cbc -d \
    -in /backups/merit_registry/db_LATEST.db.gz.enc | \
    gzip -dc > /tmp/speed_test.db
)
# Should complete in < 10 seconds
```

## Retention Policy

| Backup | Daily | Weekly | Monthly | Yearly |
|--------|-------|--------|---------|--------|
| merit_registry.db | 30 copies | 1 copy | 1 copy | 1 copy |
| search.db | 14 copies | — | — | — |
| browse cache | — | 8 copies | — | — |

**Cleanup cron (runs weekly):**
```bash
# Remove merit_registry backups >30 days old
find /backups/merit_registry -name "db_*.db.gz.enc" -mtime +30 -delete

# Remove search.db backups >14 days old
find /backups/search.db -name "*.tar.gz.enc" -mtime +14 -delete
```

## Offsite Backup (Optional Enhancement)

For production hardening, consider:
- **AWS S3 + lifecycle policies** (encrypt at rest, 90-day retention)
- **Backblaze B2** (cheap, $6/TB/month)
- **Home server NAS backup** (rsync to a second drive)

This is "nice to have" but not critical given the data is derived from public IRS records (rebuilding from source is possible, just slow).

## Alert Integration

Backup failures should trigger alerts:
- No backup file created in 26 hours → CRITICAL
- Backup file < 100 MB → WARNING (may be truncated)
- Test restore fails → CRITICAL

These are checked by `metrics_collector.py` and alerted via `alert_manager.py`.

---

**Last tested:** [TBD — schedule first drill]  
**Owner:** [TBD — assign ops lead]  
**Updated:** 2026-06-20
