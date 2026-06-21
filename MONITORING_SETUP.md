# Monitoring Infrastructure Setup Guide

Complete guide to installing and running the Daanaa monitoring infrastructure.

## Files Created

### Monitoring Scripts
- **`scripts/phase4_monitor.py`** — Phase 4 semantic verification progress monitor
- **`scripts/api_health_dashboard.py`** — API health and gunicorn monitoring
- **`scripts/backup_status.py`** — Backup integrity verification
- **`scripts/cron_job_monitor.py`** — Cron job execution tracking
- **`scripts/daanaa_status.py`** — Unified infrastructure dashboard

### Configuration
- **`config/daanaa-status.service`** — systemd service for unified dashboard

### Documentation
- **`docs/MONITORING.md`** — Comprehensive monitoring guide

## Quick Install

### 1. Make Scripts Executable

```bash
chmod +x ~/meritgiving/scripts/{phase4_monitor,api_health_dashboard,backup_status,cron_job_monitor,daanaa_status}.py
```

### 2. Test Individual Monitors

```bash
# Test API health (API must be running on :5000)
python3 ~/meritgiving/scripts/api_health_dashboard.py --once

# Test backup status
python3 ~/meritgiving/scripts/backup_status.py

# Test cron jobs
python3 ~/meritgiving/scripts/cron_job_monitor.py

# Test Phase 4 (only works if Phase 4 is running)
python3 ~/meritgiving/scripts/phase4_monitor.py --once
```

### 3. Test Unified Dashboard

```bash
# One-time check
python3 ~/meritgiving/scripts/daanaa_status.py --once

# Interactive dashboard (Ctrl+C to stop)
python3 ~/meritgiving/scripts/daanaa_status.py
```

### 4. Install as systemd Service (Optional)

```bash
# Copy service file
sudo cp ~/meritgiving/config/daanaa-status.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable daanaa-status
sudo systemctl start daanaa-status

# Verify it's running
sudo systemctl status daanaa-status

# Watch logs
sudo journalctl -u daanaa-status -f
```

## Monitor Descriptions

### Phase 4 Monitor

Tracks semantic verification pipeline:
- Candidates processed
- Verified matches
- Speed (embeddings/min)
- GPU stall detection
- ETA to completion

Reads: `/tmp/phase4_progress.log`
Writes: `~/meritgiving/logs/phase4_monitor.log`

**Alert threshold:** Speed < 10 embeddings/min

### API Health Dashboard

Monitors Daanaa API:
- `/health` endpoint status
- `/api/stats` endpoint validity
- Gunicorn process memory
- Response time trend (last 10)
- Memory trend (last 10)
- Overall success rate

Writes: `~/meritgiving/logs/api_health.log`

**Alert thresholds:**
- Response time > 2s
- Memory > 1GB

### Backup Status Monitor

Verifies backup integrity:
- Latest backup exists
- Size ≥ 1GB
- Age ≤ 24 hours
- Gzip/SQLite integrity check
- Directory stats

Writes: `~/meritgiving/logs/backup_status.log`

### Cron Job Monitor

Tracks 5 maintenance jobs:
- `health_check` (every 5 min)
- `backup_verify` (daily 03:00 UTC)
- `cleanup_stale` (daily 04:00 UTC)
- `db_optimize` (daily 05:00 UTC)
- `precompute_orgs` (weekly Sunday 06:00 UTC)

For each: shows status, age, overdue detection

Writes: `~/meritgiving/logs/cron_monitor.log`

### Unified Dashboard

Combines all monitors:
- System status (CPU, memory, disk)
- Phase 4 progress
- API health
- Backup status
- Cron job status

Updates every 30 seconds (or on-demand).

Writes: `/var/log/daanaa/status.log` (or `~/meritgiving/logs/daanaa_status.log` if /var/log not writable)

## Usage Examples

### Interactive Monitoring

```bash
# Watch unified dashboard (updates every 30s)
python3 ~/meritgiving/scripts/daanaa_status.py

# Watch Phase 4 progress specifically
python3 ~/meritgiving/scripts/phase4_monitor.py

# Watch API health specifically
python3 ~/meritgiving/scripts/api_health_dashboard.py
```

### One-Time Checks

```bash
# Check backup status
python3 ~/meritgiving/scripts/backup_status.py

# Check cron jobs
python3 ~/meritgiving/scripts/cron_job_monitor.py

# Unified status check
python3 ~/meritgiving/scripts/daanaa_status.py --once
```

### JSON Output (for scripting)

```bash
# Get backup status as JSON
python3 ~/meritgiving/scripts/backup_status.py --json

# Get cron jobs as JSON
python3 ~/meritgiving/scripts/cron_job_monitor.py --json
```

### Background/Cron Mode

```bash
# All monitors have --log-only flag for background execution
python3 ~/meritgiving/scripts/daanaa_status.py --log-only

# Add to crontab for periodic checks
*/30 * * * * python3 ~/meritgiving/scripts/daanaa_status.py --once --log-only
```

### As systemd Service

```bash
# Start/stop/restart
sudo systemctl start daanaa-status
sudo systemctl stop daanaa-status
sudo systemctl restart daanaa-status

# View status
sudo systemctl status daanaa-status

# View logs
sudo journalctl -u daanaa-status -f

# View recent logs
sudo journalctl -u daanaa-status -n 100

# Check if enabled at boot
sudo systemctl is-enabled daanaa-status
```

## Log Files

All monitors write to local logs for auditability:

```
~/meritgiving/logs/
├── phase4_monitor.log         # Phase 4 progress (updated every 30s)
├── api_health.log              # API health checks (updated every 5s)
├── backup_status.log           # Backup verification (on-demand)
├── cron_monitor.log            # Cron job status (on-demand)
└── daanaa_status.log           # Unified dashboard (fallback)

/var/log/daanaa/
└── status.log                  # Unified dashboard primary log
```

View logs:

```bash
# Real-time unified dashboard
sudo journalctl -u daanaa-status -f

# Or tail the log file
tail -f /var/log/daanaa/status.log

# Individual monitor logs
tail -f ~/meritgiving/logs/api_health.log
tail -f ~/meritgiving/logs/phase4_monitor.log
```

## Troubleshooting

### Monitors show "API connection refused"

The API server is not running on port 5000. Start it:

```bash
# Start API server
cd ~/meritgiving
source venv/bin/activate
./restart_api.sh
```

### Phase 4 monitor shows "No progress file"

Phase 4 semantic verification is not running. Start it:

```bash
cd ~/meritgiving
source venv/bin/activate
python3 scripts/phase4_semantic_verification.py --limit 50000 &
```

Then monitor in another terminal:

```bash
python3 scripts/phase4_monitor.py
```

### systemd service won't start

Check for errors:

```bash
sudo systemctl start daanaa-status
sudo journalctl -u daanaa-status -n 20 --no-pager
```

Common issues:
1. **Python path** — Verify `/usr/bin/python3` exists and has required packages
2. **Permissions** — Check `/var/log/daanaa` directory permissions
3. **Dependencies** — Ensure `psutil` and `requests` are installed:
   ```bash
   source ~/meritgiving/venv/bin/activate
   pip install psutil requests numpy
   ```

### Can't write to /var/log/daanaa

Create the directory with proper permissions:

```bash
sudo mkdir -p /var/log/daanaa
sudo chown $(whoami):$(whoami) /var/log/daanaa
sudo chmod 755 /var/log/daanaa
```

If systemd service still fails, it will fall back to `~/meritgiving/logs/daanaa_status.log`.

### Logs growing too large

Manually compress old logs:

```bash
gzip ~/meritgiving/logs/*.log
```

Set up automatic rotation (requires sudo):

```bash
# Create /etc/logrotate.d/daanaa
sudo tee /etc/logrotate.d/daanaa > /dev/null <<EOF
/var/log/daanaa/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

## Integration with Existing Systems

These monitors work alongside existing infrastructure:

- **metrics_collector.py** — System-level metrics (separate, runs in background)
- **alert_manager.py** — Alert routing (integrate with these monitors)
- **health_check.py** — API health verification (5-min interval, older implementation)
- **verify_backup_integrity.py** — Backup verification (daily, older implementation)

The new monitoring suite provides:
- Real-time updates (not just cron-based)
- Unified dashboard view
- JSON output for programmatic access
- Better alert thresholds and color coding
- Phase 4 GPU monitoring (new)

## Next Steps

1. ✅ Scripts created and tested
2. ✅ Install scripts (make executable)
3. ✅ Test individual monitors
4. ✅ Test unified dashboard
5. ⏭️ Install systemd service (optional)
6. ⏭️ Configure email/Twilio alerts (future)
7. ⏭️ Integrate with Grafana/Prometheus (future)

See `docs/MONITORING.md` for comprehensive documentation.
