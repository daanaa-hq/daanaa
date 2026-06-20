# Daanaa Backup & Disaster Recovery Strategy

## What actually runs

### Critical tables (nightly, 02:30 cron)
`org_claims`, `org_activity`, `feedback`, `waitlist` — the irreplaceable, non-derivable rows.

- Script: `scripts/ops/daanaa_backup.sh`
- Output: `backups/critical/critical_YYYYMMDD.sql.gz` (~1 KB each)
- Retention: 30 days rolling
- Error detection: warns if dump contains "ERROR" or file is <400 bytes

### Full registry snapshot (weekly, Sunday 02:30)
The entire `merit_registry.db` (~10 GB) via SQLite `.backup` (online, non-blocking).

- Output: `backups/full/full_YYYYMMDD.db.gz` (~7 GB compressed)
- Retention: 2 most recent Sunday snapshots
- Integrity check: `gzip -t` runs immediately after compression

### Offsite (Google Drive via rclone)
`daanaa-backup:` remote is configured and active. Runs at the end of every backup:

- Critical: `rclone copy --max-age 2d` (last 2 days only, keeps Drive lean)
- Full: all full snapshots mirrored

### Frontend / precompute
Static files. Re-deploy from `scripts/safe_deploy_droplet.sh` if lost.
The droplet serves static files (read-only); no DB backup needed there.

---

## Backup schedule

| What | When | Retention | Offsite |
|------|------|-----------|---------|
| Critical tables dump | Daily 02:30 | 30 days | Google Drive (2 days) |
| Full registry snapshot | Sunday 02:30 | 2 snapshots | Google Drive (all) |

---

## Restore procedures

### Restore critical tables (claims, activity, feedback, waitlist)

```bash
# Find backup to restore from
ls -lh backups/critical/

# Restore to a temp DB and verify before overwriting production
BACKUP=backups/critical/critical_20260620.sql.gz
TMPDB=/tmp/restore_check.db

zcat "$BACKUP" | sqlite3 "$TMPDB"
sqlite3 "$TMPDB" ".tables"
sqlite3 "$TMPDB" "SELECT COUNT(*) FROM org_claims;"
sqlite3 "$TMPDB" "PRAGMA integrity_check;"
rm "$TMPDB"
```

If it looks good, apply to the live DB:
```bash
# Backup current state first
cp data/merit_registry.db data/merit_registry.db.pre_restore

# Apply dump (merges — org_claims has UNIQUE on ein, so duplicate rows skip)
zcat backups/critical/critical_YYYYMMDD.sql.gz | sqlite3 data/merit_registry.db
```

### Restore full registry from Sunday snapshot

RTO ~15 min (7 GB gzip decompress).

```bash
# Verify gzip integrity first
gzip -t backups/full/full_YYYYMMDD.db.gz && echo "OK"

# Decompress to temp location
zcat backups/full/full_YYYYMMDD.db.gz > /tmp/restore_full.db

# Verify
sqlite3 /tmp/restore_full.db "PRAGMA integrity_check;"
sqlite3 /tmp/restore_full.db "SELECT COUNT(*) FROM registry_enriched;"

# Swap in (stop API first)
./restart_api.sh stop  # or: kill $(pgrep gunicorn)
mv data/merit_registry.db data/merit_registry.db.REPLACED_$(date +%s)
mv /tmp/restore_full.db data/merit_registry.db
./restart_api.sh
```

### Restore from Google Drive (offsite)

```bash
# Pull critical backups
rclone copy daanaa-backup:daanaa-backups/critical backups/critical/

# Pull full snapshot
rclone copy daanaa-backup:daanaa-backups/full backups/full/

# Then follow restore procedures above
```

---

## Disaster scenarios

### Scenario 1: merit_registry.db corruption

1. Stop API: `kill $(pgrep gunicorn)`
2. Verify Sunday snapshot: `gzip -t backups/full/full_LATEST.db.gz`
3. Restore (see above). RPO: up to 7 days of scorer runs.
4. Re-run nightly scorer if restore is >24h old.
5. Check `dmesg` for disk errors after restoring.

### Scenario 2: Lost claims / waitlist data

1. Stop API.
2. Restore critical tables dump (see above).
3. Restart API.
4. RPO: <24 hours.

### Scenario 3: Full home server loss

1. Spin up replacement machine.
2. Install dependencies (`venv`, sqlite3, rclone).
3. Pull latest backups from Google Drive.
4. Restore full snapshot.
5. Re-deploy frontend to droplet: `scripts/safe_deploy_droplet.sh`.

### Scenario 4: Droplet failure

The droplet is stateless (serves precomputed files). Run `scripts/safe_deploy_droplet.sh` — it rebuilds from the home server's precompute_output. No backup needed.

### Scenario 5: Nightly scorer fails

```bash
# Check last run
sqlite3 data/merit_registry.db "SELECT run_date FROM score_snapshots ORDER BY run_date DESC LIMIT 1;"

# Re-run manually
source venv/bin/activate
python3 scripts/overnight_pipeline.py
```

---

## Monitoring

The backup script writes status to `logs/backup.log`:
- `backup ok:` — normal run
- `backup warn:` — completed but something was off (check the line)
- `backup error:` — critical failure

Check weekly: `tail -20 logs/backup.log`

---

## Restore drill log

| Date | Backup tested | Method | Result |
|------|--------------|--------|--------|
| 2026-06-20 | critical_20260620.sql.gz | zcat → sqlite3 temp DB | PASS — 2 claims, integrity_check ok |

Next drill: 2026-07-20 (monthly). Test the full Sunday snapshot.

---

**Updated:** 2026-06-20  
**Script:** `scripts/ops/daanaa_backup.sh`
