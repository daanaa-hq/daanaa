# Daanaa Infrastructure Monitoring

Comprehensive real-time monitoring suite for Phase 4 semantic verification, API health, backup integrity, and cron job execution.

## Overview

The monitoring infrastructure provides four independent monitors plus a unified dashboard:

| Component | Purpose | Update Interval | Log File |
|-----------|---------|-----------------|----------|
| **Phase 4 Monitor** | Semantic verification progress, GPU status, ETA | 30s | `logs/phase4_monitor.log` |
| **API Health Dashboard** | API endpoints, gunicorn memory, response times | 5s | `logs/api_health.log` |
| **Backup Status Monitor** | Backup integrity, age, directory stats | On-demand | `logs/backup_status.log` |
| **Cron Job Monitor** | Execution history, overdue detection | On-demand | `logs/cron_monitor.log` |
| **Unified Dashboard** | Combined view of all monitors | 30s | `/var/log/daanaa/status.log` |

---

## Quick Start

### 1. Test Individual Monitors

```bash
# Phase 4 progress (if running)
python3 scripts/phase4_monitor.py

# API health
python3 scripts/api_health_dashboard.py

# Backup status
python3 scripts/backup_status.py

# Cron jobs
python3 scripts/cron_job_monitor.py
```

### 2. Run Unified Dashboard

```bash
# Interactive dashboard (updates every 30s)
python3 scripts/daanaa_status.py

# One-time check
python3 scripts/daanaa_status.py --once

# Log-only mode (for cron/background)
python3 scripts/daanaa_status.py --log-only
```

### 3. Install as systemd Service

```bash
# Copy service file
sudo cp config/daanaa-status.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable daanaa-status
sudo systemctl start daanaa-status

# View logs
sudo journalctl -u daanaa-status -f

# Or tail the log file
tail -f /var/log/daanaa/status.log
```

---

## Detailed Monitor Descriptions

### Phase 4 Monitor (`scripts/phase4_monitor.py`)

Tracks semantic verification pipeline progress.

**Metrics:**
- Candidates processed (cumulative)
- Verified matches (above similarity threshold)
- Processing speed (embeddings/min)
- Estimated time to completion
- GPU status and stall detection

**Alerts:**
- 🔴 RED: Speed < 10 embeddings/min (GPU stalled)
- 🟡 YELLOW: Speed 10-20 embeddings/min (degraded)
- 🟢 GREEN: Speed > 20 embeddings/min (healthy)

**Data sources:**
- `/tmp/phase4_progress.log` — progress log from Phase 4 script
- `logs/phase4_checkpoint.json` — checkpoint for speed calculation

**Usage:**
```bash
python3 scripts/phase4_monitor.py                 # Interactive
python3 scripts/phase4_monitor.py --log-only      # Background mode
```

### API Health Dashboard (`scripts/api_health_dashboard.py`)

Monitors Daanaa API and gunicorn process health.

**Metrics:**
- `/health` endpoint response (status, latency)
- `/api/stats` endpoint validity
- Gunicorn process status and memory usage
- Last 10 response times (average, max)
- Last 10 memory samples (average, max)
- Overall success rate

**Alerts:**
- 🔴 RED: Endpoint down, memory > 1GB, response time > 2s
- 🟡 YELLOW: Slow response (1-2s), memory trending up
- 🟢 GREEN: All healthy

**Thresholds:**
- Memory limit: 1000 MB
- Response time warning: 2.0s
- Check interval: 5 seconds

**Usage:**
```bash
python3 scripts/api_health_dashboard.py           # Interactive
python3 scripts/api_health_dashboard.py --log-only # Background
```

### Backup Status Monitor (`scripts/backup_status.py`)

Verifies backup integrity and currency.

**Checks:**
- Latest backup exists
- Backup size ≥ 1 GB
- Backup age ≤ 24 hours
- Gzip/SQLite integrity validation
- Backup directory statistics

**Outputs:**
- Backup path, size, modification time
- Integrity check result
- Directory file count and total size
- Next scheduled backup time

**Usage:**
```bash
python3 scripts/backup_status.py                  # Human-readable
python3 scripts/backup_status.py --json           # JSON output
python3 scripts/backup_status.py --log-only       # Log only
```

### Cron Job Monitor (`scripts/cron_job_monitor.py`)

Tracks execution status of maintenance cron jobs.

**Monitored Jobs:**
- `health_check` — API health (every 5 min)
- `backup_verify` — Backup integrity (daily 03:00 UTC)
- `cleanup_stale` — Stale file cleanup (daily 04:00 UTC)
- `db_optimize` — Database optimization (daily 05:00 UTC)
- `precompute_orgs` — Org precomputation (weekly Sunday 06:00 UTC)

**For each job:**
- Last run timestamp
- Status (SUCCESS / FAILED / WARNING)
- Age since last run
- Overdue detection (no run in 2× scheduled interval)
- Next scheduled run time

**Usage:**
```bash
python3 scripts/cron_job_monitor.py               # Human-readable
python3 scripts/cron_job_monitor.py --json        # JSON output
```

### Unified Dashboard (`scripts/daanaa_status.py`)

Combined view integrating all monitors above.

**Sections:**
1. **System Status** — CPU, memory, disk, uptime
2. **Phase 4 Progress** — Candidates, matches, speed
3. **API Health** — Endpoint status
4. **Backup Status** — Integrity and age
5. **Cron Jobs** — All 5 jobs with status

**Updates every 30 seconds by default.**

**Usage:**
```bash
# Interactive dashboard
python3 scripts/daanaa_status.py

# One-time check
python3 scripts/daanaa_status.py --once

# Background mode (for cron/service)
python3 scripts/daanaa_status.py --log-only

# As systemd service
sudo systemctl start daanaa-status
sudo journalctl -u daanaa-status -f
```

---

## Installation Steps

### Prerequisites

```bash
# Ensure directories exist
mkdir -p ~/meritgiving/logs
mkdir -p /var/log/daanaa
sudo chown $USER:$USER /var/log/daanaa

# Install Python dependencies
source ~/meritgiving/venv/bin/activate
pip install psutil requests numpy
```

### Install Monitoring Scripts

```bash
# Copy scripts (already in scripts/ directory)
ls -la ~/meritgiving/scripts/phase4_monitor.py
ls -la ~/meritgiving/scripts/api_health_dashboard.py
ls -la ~/meritgiving/scripts/backup_status.py
ls -la ~/meritgiving/scripts/cron_job_monitor.py
ls -la ~/meritgiving/scripts/daanaa_status.py

# Make executable
chmod +x ~/meritgiving/scripts/*.py
```

### Install as systemd Service (Optional)

```bash
# Copy service file
sudo cp ~/meritgiving/config/daanaa-status.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable daanaa-status

# Start service
sudo systemctl start daanaa-status

# Verify running
sudo systemctl status daanaa-status

# View logs
tail -f /var/log/daanaa/status.log
```

### Set Up Cron Jobs (for individual monitors)

Add to `crontab -e` if you want independent scheduled checks:

```bash
# API health check every 5 minutes
*/5 * * * * python3 ~/meritgiving/scripts/api_health_dashboard.py --log-only

# Backup status daily at 03:30 UTC
30 3 * * * python3 ~/meritgiving/scripts/backup_status.py --log-only

# Cron job monitor daily at 07:00 UTC
0 7 * * * python3 ~/meritgiving/scripts/cron_job_monitor.py --log-only

# Unified dashboard every 30 minutes
*/30 * * * * python3 ~/meritgiving/scripts/daanaa_status.py --once --log-only
```

---

## Log Files

All monitors write to local logs:

```
~/meritgiving/logs/
├── phase4_monitor.log          # Phase 4 progress monitor
├── api_health.log              # API health dashboard
├── backup_status.log           # Backup status monitor
├── cron_monitor.log            # Cron job monitor
└── daanaa_status.log           # Unified dashboard (fallback)

/var/log/daanaa/
└── status.log                  # Unified dashboard (preferred)
```

View live logs:

```bash
# Unified dashboard (system log)
sudo journalctl -u daanaa-status -f

# Or tail file directly
tail -f /var/log/daanaa/status.log

# Individual monitor logs
tail -f ~/meritgiving/logs/api_health.log
tail -f ~/meritgiving/logs/phase4_monitor.log
```

---

## JSON Output

All monitors support `--json` output for programmatic access:

```bash
# Get backup status as JSON
python3 scripts/backup_status.py --json

# Get cron status as JSON
python3 scripts/cron_job_monitor.py --json
```

Example output:

```json
{
  "backup_found": true,
  "backup_path": "/home/akbar/meritgiving/backups/merit_registry_20260621.db.gz",
  "backup_size_mb": 7234.5,
  "backup_age_hours": 12.3,
  "integrity_ok": true,
  "age_ok": true,
  "size_ok": true,
  "overall_ok": true,
  "next_backup": "2026-06-22T02:00:00+00:00",
  "dir_stats": {
    "file_count": 45,
    "total_size_gb": 156.23
  }
}
```

---

## Alerting Strategy

### Threshold-Based Alerts

**Phase 4:**
- Speed < 10 embeddings/min → GPU stalled (check server)
- No progress in 5+ minutes → Process hung

**API Health:**
- Response time > 2s → Performance degradation
- Memory > 1GB → Memory leak (restart gunicorn)
- Endpoint down → Service offline (restart)

**Backup:**
- Age > 24h → Backup failed or missed
- Size < 1GB → Truncated/corrupted backup
- Integrity check failed → Backup unusable

**Cron:**
- Last run > 2× interval → Job not running
- Status = FAILED → Job execution error

### Manual Intervention

#### API is down or slow:

```bash
# Check status
curl http://localhost:5000/health

# Restart gunicorn gracefully
systemctl restart daanaa-api

# Or force-kill all workers
pkill -f gunicorn
./restart_api.sh
```

#### GPU is stalled:

```bash
# Check Phase 4 process
ps aux | grep phase4_semantic

# Kill and restart
pkill -f phase4_semantic
python3 scripts/phase4_semantic_verification.py --limit 50000 &

# Monitor progress
python3 scripts/phase4_monitor.py
```

#### Backup is stale:

```bash
# Manual backup
python3 scripts/backup_verify.sh

# Or check cron log
tail -f ~/meritgiving/logs/backup_alert.log
```

---

## Troubleshooting

### Monitor shows "Connection refused"

The API is not running. Start it:

```bash
# Check if running
ps aux | grep gunicorn

# Start API
source ~/meritgiving/venv/bin/activate
./restart_api.sh
```

### Monitor shows "/tmp/phase4_progress.log not found"

Phase 4 is not running. Start it:

```bash
python3 scripts/phase4_semantic_verification.py --limit 50000 &
python3 scripts/phase4_monitor.py  # Then monitor in another terminal
```

### systemd service won't start

Check errors:

```bash
sudo journalctl -u daanaa-status -n 50 --no-pager
```

Common issues:
- Python path wrong → check `/home/akbar/meritgiving/venv/bin/python3`
- Permissions → `sudo chown -R akbar:akbar /var/log/daanaa`
- venv not activated → service runs with system Python (install psutil/requests)

### Log directory not writable

If `/var/log/daanaa` doesn't exist:

```bash
sudo mkdir -p /var/log/daanaa
sudo chown $(whoami):$(whoami) /var/log/daanaa
```

---

## Performance Notes

### Resource Usage

- **Phase 4 Monitor**: <5MB memory, 1 thread, I/O only (reads progress log)
- **API Health Dashboard**: <20MB memory, 1 thread, 5-10 HTTP requests/min
- **Backup Status**: <10MB memory, runs on-demand
- **Cron Monitor**: <5MB memory, runs on-demand
- **Unified Dashboard**: <30MB memory, 1 thread, combines above

All monitors are I/O-bound and CPU-light. Safe to run continuously.

### Log Rotation

Logs grow slowly (~1-2MB/day each). Set up log rotation:

```bash
# /etc/logrotate.d/daanaa (requires sudo)
/var/log/daanaa/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

Or manually clean:

```bash
gzip ~/meritgiving/logs/api_health.log
rm ~/meritgiving/logs/api_health.log.gz.old
```

---

## Integration with Existing Infrastructure

These monitors complement existing infrastructure:

- **metrics_collector.py** — System-level metrics (CPU, disk, database)
- **alert_manager.py** — Alert routing and notifications
- **health_check.py** — API health (5-min interval)
- **verify_backup_integrity.py** — Backup verification (daily)

The unified dashboard integrates all of these for a comprehensive view.

---

## Next Steps

1. ✓ Test individual monitors
2. ✓ Install scripts and systemd service
3. ✓ Verify logs are being written
4. ✓ Configure alerting (email/Twilio integration)
5. ✓ Set up log rotation
6. ✓ Integrate with Grafana/Prometheus (optional)

See `docs/INFRASTRUCTURE.md` for system architecture and `LESSONS.md` for monitoring patterns.
