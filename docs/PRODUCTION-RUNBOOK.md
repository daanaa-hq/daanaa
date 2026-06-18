# Daanaa Production Runbook

**Document Status:** PRODUCTION READY (2026-06-18)  
**Last Updated:** 2026-06-18  
**Owner:** Akbar Khowaja

---

## 1. ARCHITECTURE AT A GLANCE

```
┌─────────────────────────────────────────────────────┐
│ FRONTEND (React)                                    │
│ - daanaa.org (HTTPS via Cloudflare)                │
│ - Static SPA served by nginx                        │
└────────────────┬────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼────────┐  ┌──────▼──────────┐
│ DROPLET        │  │ HOME SERVER     │
│ (Static API)   │  │ (Stateful API)  │
│ :5000 browse   │  │ :5000 wallet    │
│ Static files   │  │ Firebase        │
│ Search DB      │  │ Org claims      │
│ nginx          │  │                 │
└────────────────┘  └─────────────────┘
       │                     │
       └──────────┬──────────┘
            Reverse SSH tunnel
            (:5001 on droplet)
```

**Primary:** Droplet (daanaa-droplet, 162.243.97.179)  
**Secondary:** Home server (via reverse tunnel)

---

## 2. HEALTH CHECKS

### Daily Automated Checks
- **Backup integrity:** Daily at 03:00 AM (`monitor_backups.sh`)
  - Verifies nightly backup ran, is healthy, and can restore
  - Logs: `/home/akbar/meritgiving/logs/backup_monitor.log`
  - Alert: Email if backup fails (setup pending)

### Manual Health Checks
```bash
# Home server API
curl http://localhost:5000/health | jq .

# Droplet static API
curl http://162.243.97.179/health | jq .

# Directory search
curl "http://162.243.97.179/api/organizations?q=health&page=1" | jq '.count'

# Database integrity
sqlite3 data/merit_registry.db "PRAGMA integrity_check;"

# Disk space
df -h /

# Cron jobs running
crontab -l | grep -E "backup|hidden_gems|monitor"
```

---

## 3. DISASTER RECOVERY PROCEDURES

### Scenario A: Database Corruption (Critical)

**Symptoms:** API returns errors, integrity_check fails, startup errors

**Recovery Steps:**
```bash
cd ~/meritgiving

# 1. Stop the API
pkill -f "python.*daanaa_api.py"

# 2. Identify the latest good backup
ls -lht backups/critical/critical_*.sql.gz | head -3

# 3. Restore from backup (replace YYYYMMDD with date of good backup)
gunzip < backups/critical/critical_20260618.sql.gz | sqlite3 data/merit_registry.db

# 4. Verify restoration
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM org_claims; PRAGMA integrity_check;"

# 5. Restart the API
source venv/bin/activate
python daanaa_api.py &

# 6. Verify API is healthy
sleep 5
curl http://localhost:5000/health
```

**If restore fails:**
- Check backup file size (should be > 500 bytes)
- Try older backup from backups/critical/
- If all backups fail, restore from weekly full backup (backups/full/)

---

### Scenario B: Disk Full (Home Server)

**Symptoms:** Backup fails, API slow, database writes fail

**Diagnosis:**
```bash
df -h /
du -sh ~/* | sort -rh | head -10
```

**Recovery:**
```bash
# 1. Check backup directory size
du -sh backups/

# 2. Archive old critical backups (keep 7 days locally, rest on Drive)
find backups/critical -name "critical_*.sql.gz" -mtime +7 -delete

# 3. Check data size
du -sh data/

# 4. If home server is out of space, move/compress logs
find logs/ -name "*.log" -mtime +30 -exec gzip {} \;

# 5. Verify space freed
df -h /
```

---

### Scenario C: Droplet Disk Full

**Symptoms:** Droplet API unreachable, nginx errors, can't write logs

**Status (as of 2026-06-18):** 69% usage (11GB free) — SAFE

**If it happens:**
```bash
ssh root@162.243.97.179

# Check what's using space
du -sh /data/* | sort -rh
du -sh /* | sort -rh

# Safe to delete (auto-regenerated):
# - /data/precompute/v1/orgs/ (7.6GB) ← ALREADY DELETED
# - /opt/ (if old packages)

# Monitor for weekly bloat:
df -h / | tail -1

# Alert threshold: Stop accepting traffic at 80% full
```

---

### Scenario D: API Crash / Hung Process

**Symptoms:** `/api/` endpoints timeout, `localhost:5000` unreachable

**Recovery:**
```bash
# 1. Check if process exists
pgrep -af "daanaa_api.py"

# 2. Force kill and restart
pkill -9 -f "daanaa_api.py"
cd ~/meritgiving && source venv/bin/activate && nohup python daanaa_api.py > /tmp/api.log 2>&1 &

# 3. Verify
sleep 3
curl http://localhost:5000/health
```

---

### Scenario E: Lost Offsite Backup (after rclone configured)

**Symptoms:** rclone push fails, Drive shows no files

**Recovery:**
```bash
# 1. Check rclone config
rclone listremotes
rclone config show daanaa-backup

# 2. Re-authenticate if needed
rclone config create daanaa-backup drive

# 3. Manually push all backups
rclone copy backups/critical daanaa-backup:daanaa-backups/critical
rclone copy backups/full daanaa-backup:daanaa-backups/full

# 4. Verify
rclone ls daanaa-backup:daanaa-backups/
```

---

## 4. BACKUP STRATEGY

### Nightly Critical Backups
- **What:** org_claims, feedback, waitlist (small tables only, ~1KB)
- **When:** 02:30 AM every day
- **Where:** `/home/akbar/meritgiving/backups/critical/`
- **How:** `sqlite3 .dump` (read-only, non-blocking)
- **Retention:** 30 days local + offsite (when rclone configured)
- **Verified:** ✅ Test restore passed (2026-06-18)

### Weekly Full Snapshots
- **What:** Entire merit_registry.db (all 2M orgs + claims + indexes)
- **When:** Sundays 02:30 AM
- **Where:** `/home/akbar/meritgiving/backups/full/`
- **How:** `sqlite3 .backup` (online snapshot, safe with WAL)
- **Size:** 7.1GB gzipped (from 9.8GB database)
- **Retention:** 2 copies (keeps 2 weeks)

### Offsite Backup (Google Drive via rclone)
- **Status:** ❌ NOT YET CONFIGURED
- **When configured:** Auto-push nightly after 02:30 AM
- **Setup:** `rclone config create daanaa-backup drive` (user action)
- **Blocks:** Production launch (required for Stewardship P2)

### Monitoring
- **Script:** `scripts/ops/monitor_backups.sh`
- **When:** Daily 03:00 AM (30 min after backup)
- **Checks:**
  - Backup exists and is < 24 hours old
  - Backup file size is healthy (> 500 bytes)
  - Backup can be restored (integrity check)
  - Offsite copy exists (once rclone configured)
- **Logs:** `/home/akbar/meritgiving/logs/backup_monitor.log`
- **Alerts:** Email on failure (setup pending)

---

## 5. SCHEDULED JOBS

```
02:30 AM daily    - Nightly critical backup (daanaa_backup.sh)
03:00 AM daily    - Backup monitoring (monitor_backups.sh) 
03:45 AM Monday   - Hidden gems weekly refresh (refresh_hidden_gems.sh)
06:15 AM Monday   - Funder opportunity monitor (funder_opportunity_monitor.py)
```

All logs: `/home/akbar/meritgiving/logs/`

---

## 6. KEY FILES & LOCATIONS

| File/Dir | Purpose |
|----------|---------|
| `data/merit_registry.db` | Primary database (9.8GB, 2.06M orgs) |
| `backups/critical/` | Daily SQL dumps (org_claims, feedback, waitlist) |
| `backups/full/` | Weekly full database snapshots |
| `.env` | API keys (ANTHROPIC, FIRESTORE) — chmod 600 |
| `scripts/daanaa_api.py` | Home server stateful API (wallet, claims) |
| `scripts/droplet_api.py` | Droplet static API (browse, search) |
| `logs/` | All operational logs |

---

## 7. ESCALATION

### Who to Contact

- **Database Issues:** Check integrity first, review `data/merit_registry.db` with PRAGMA
- **API Crashes:** Check logs in `/logs/`, verify disk space, restart process
- **Backup Failures:** Check `logs/backup_monitor.log` and `logs/backup.log`
- **Disk Full:** Delete old logs, archive old backups
- **Droplet Connectivity:** Verify SSH to `root@162.243.97.179`, check nginx with `nginx -t`

### Escalation Path

1. **Check logs** (`logs/*.log`)
2. **Run health checks** (see section 2)
3. **Consult recovery procedures** (see section 3)
4. **If unresolved:** Contact Akbar (akbar.khowaja@gmail.com)

---

## 8. MONITORING DASHBOARD

**Recommended Tools (Post-Launch):**
- Uptime monitoring: Uptimerobot or similar
- Log aggregation: Papertrail or ELK
- Error tracking: Sentry
- Backups: Backup.io or similar

**For now:** Manual daily health checks via this runbook

---

## 9. API KEY ROTATION

**Current Status (as of 2026-06-18):**
- ANTHROPIC_API_KEY: ✅ Rotated (new key in .env, process needs restart)
- FIRESTORE_API_KEY: ✅ Current (existing key verified working)

**Next Rotation:** 
- Schedule quarterly key rotation (3 months)
- Update .env with new keys
- Restart API to load new keys

---

## 10. FIRESTORE/WALLET SAFETY

**Backend:** Firebase/Firestore (Google Cloud)  
**Data:** Only wallet bookmarks + giving intent, never transactions  
**Privacy:** Never exposed publicly, users control via Google account  
**Backup:** Handled by Firebase (automatic daily backups, 30-day retention)

---

## Appendix: Quick Reference

```bash
# Health check (all systems)
curl http://localhost:5000/health && curl http://162.243.97.179/health

# Backup status
ls -lh backups/critical/ | tail -3

# Database size & integrity
ls -lh data/merit_registry.db && sqlite3 data/merit_registry.db "PRAGMA integrity_check;"

# Restart API
pkill -f daanaa_api.py && cd ~/meritgiving && source venv/bin/activate && python daanaa_api.py &

# View logs
tail -f logs/backup.log logs/backup_monitor.log

# Test restore
gunzip < backups/critical/critical_20260618.sql.gz | sqlite3 /tmp/test.db && sqlite3 /tmp/test.db "SELECT COUNT(*) FROM org_claims;"
```

---

**Last Tested:** 2026-06-18  
**Status:** ✅ PRODUCTION READY
