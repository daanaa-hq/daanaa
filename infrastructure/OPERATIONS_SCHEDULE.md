# Daanaa Operations Schedule

Automated infrastructure tasks that keep the system healthy.

## Cron Jobs (Home Server)

Add these to `crontab -e`:

```bash
# ═══════════════════════════════════════════════════════════════
# MONITORING & ALERTING
# ═══════════════════════════════════════════════════════════════

# Collect metrics every minute
* * * * * cd /home/akbar/meritgiving && source venv/bin/activate && \
  python3 infrastructure/monitoring/metrics_collector.py >> /var/log/daanaa_metrics.log 2>&1

# Process alerts every minute (sends CRITICAL emails immediately)
* * * * * cd /home/akbar/meritgiving && source venv/bin/activate && \
  python3 infrastructure/monitoring/alert_manager.py >> /var/log/daanaa_alerts.log 2>&1

# Send daily digest at 9 AM
0 9 * * * cd /home/akbar/meritgiving && source venv/bin/activate && \
  python3 infrastructure/monitoring/alert_manager.py digest >> /var/log/daanaa_alerts.log 2>&1

# ═══════════════════════════════════════════════════════════════
# BACKUPS
# ═══════════════════════════════════════════════════════════════

# Daily home server backup (2 AM)
0 2 * * * cd /home/akbar/meritgiving && bash infrastructure/backup/daily_backup.sh \
  >> /var/log/daanaa_backup.log 2>&1

# Daily droplet backup (3 AM) — SSH into droplet
0 3 * * * bash /home/akbar/meritgiving/infrastructure/backup/backup_droplet.sh \
  >> /var/log/daanaa_backup.log 2>&1

# Cleanup old backups (keep 30 days of home, 14 days of droplet)
0 4 * * 0 cd /home/akbar/meritgiving && bash infrastructure/backup/cleanup_old_backups.sh \
  >> /var/log/daanaa_backup.log 2>&1

# Monthly backup integrity test (1st of month, 10 AM)
0 10 1 * * cd /home/akbar/meritgiving && bash infrastructure/backup/test_restore.sh \
  >> /var/log/daanaa_backup.log 2>&1

# ═══════════════════════════════════════════════════════════════
# DATA PIPELINE
# ═══════════════════════════════════════════════════════════════

# Nightly scorer (11 PM)
0 23 * * * cd /home/akbar/meritgiving && source venv/bin/activate && \
  bash scripts/overnight_pipeline.sh >> /var/log/nightly_pipeline.log 2>&1

# Weekly hidden gems rotation (Monday 2 AM)
0 2 * * 1 cd /home/akbar/meritgiving && source venv/bin/activate && \
  python3 scripts/precompute_hidden_gems.py && \
  rsync -avz precompute_output/browse/hidden_gems/ \
    root@162.243.97.179:/data/precompute/v1/browse/hidden_gems/ \
  >> /var/log/hidden_gems.log 2>&1

# ═══════════════════════════════════════════════════════════════
# MAINTENANCE
# ═══════════════════════════════════════════════════════════════

# Rotate logs (daily, keep 7 days)
0 1 * * * find /var/log/daanaa*.log -mtime +7 -delete

# Database VACUUM (weekly, Sunday 3 AM) — optimizes file size
0 3 * * 0 cd /home/akbar/meritgiving && \
  sqlite3 data/merit_registry.db "VACUUM;" >> /var/log/daanaa_maintenance.log 2>&1
```

## Cron Jobs (Droplet)

SSH into droplet and add to root's crontab:

```bash
# ═══════════════════════════════════════════════════════════════
# DROPLET MONITORING & CLEANUP
# ═══════════════════════════════════════════════════════════════

# Health check (every 5 minutes) — simple uptime monitor
*/5 * * * * curl -s http://localhost:5000/health > /dev/null 2>&1 || \
  echo "$(date): API down" >> /var/log/health_check.log

# Cleanup old logs (daily)
0 2 * * * journalctl --vacuum=100M

# Sync precomputed files from home server (fallback, if cron on home fails)
0 4 * * 1 rsync -avz root@HOME_IP:/home/akbar/meritgiving/precompute_output/browse/hidden_gems/ \
  /data/precompute/v1/browse/hidden_gems/ > /dev/null 2>&1
```

## Manual Tasks

### Weekly (Monday Morning)

**Operations checklist** — 15 minutes

```bash
# 1. Check overnight pipeline (check log for errors)
tail -50 /var/log/nightly_pipeline.log | grep -i error

# 2. Verify backups created
ls -lh /backups/merit_registry/ | tail -3
ls -lh /backups/search.db/ | tail -3

# 3. Check current metrics
python3 infrastructure/monitoring/metrics_collector.py
cat /tmp/daanaa_metrics.json | jq '.alerts'

# 4. Review database size growth
sqlite3 data/merit_registry.db "
  SELECT 
    (SELECT COUNT(*) FROM registry_enriched) as total_orgs,
    ROUND(page_count * page_size / 1024.0 / 1024, 2) as size_mb
  FROM pragma_page_count(), pragma_page_size();
"

# 5. Check droplet disk usage
ssh root@162.243.97.179 "du -sh /data/* | sort -rh"

# 6. Verify gems refresh happened
ssh root@162.243.97.179 "ls -lh /data/precompute/v1/browse/hidden_gems/ALL_1.json.gz"
```

### Monthly (1st of Month)

**Backup integrity test** — 30 minutes (usually automated, but verify)

```bash
# Manually test a restore
bash infrastructure/backup/test_restore.sh

# Check backup retention
find /backups -type f | wc -l  # Should have ~60 files total
```

**Database analysis** — 15 minutes

```bash
# Run PRAGMA integrity_check
sqlite3 data/merit_registry.db "PRAGMA integrity_check;" | head -5

# Check for any corrupted rows
sqlite3 data/merit_registry.db "
  SELECT COUNT(*) as orgs_missing_required_fields
  FROM registry_enriched
  WHERE organization_name IS NULL OR EIN IS NULL;
"
```

## Alert Response Workflow

| Alert | Action | Owner | SLA |
|-------|--------|-------|-----|
| Disk >80% | Free space or expand volume | Ops | 4h |
| Memory >85% | Review running processes | Ops | 2h |
| API down | Check logs; restart gunicorn | Ops | 15m |
| Scorer not run in 26h | Manually trigger overnight_pipeline.sh | Data | 2h |
| FTS5 out of sync | Rebuild: `bash scripts/build_fts_index.py` | Data | 4h |
| Search.db corrupted | Restore from backup | Ops | 30m |
| Backup missing >26h | Check cron; manually run backup script | Ops | 2h |

## Runbook Quick Links

- **API not responding?** → `docs/INFRASTRUCTURE_MONITORING.md` → Troubleshooting
- **Deploy went wrong?** → `infrastructure/deployment/rollback.sh`
- **Database corruption?** → `infrastructure/backup/backup_strategy.md` → Scenario recovery
- **Need to add a new metric?** → `infrastructure/monitoring/metrics_collector.py` → Add method

## Dashboard (Future)

When ready to add a visual dashboard:

```bash
# Install Prometheus + Grafana (docker-compose)
# Point Prometheus to /tmp/daanaa_metrics.json via node-exporter
# Create Grafana dashboard with:
#   - System health (CPU, memory, disk)
#   - API latency (directory, org detail, search)
#   - Data freshness (scorer age, FTS status)
#   - Database metrics (size, org count, coverage)
#   - Backup status (last run, size, integrity)
```

---

**Last updated:** 2026-06-20  
**Owner:** [TBD]  
**Next review:** 2026-07-20
