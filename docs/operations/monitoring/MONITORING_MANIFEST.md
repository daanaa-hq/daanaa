# Monitoring Infrastructure Manifest

## Complete File Listing

### Monitoring Scripts (5 scripts)

| File | Lines | Purpose |
|------|-------|---------|
| `scripts/phase4_monitor.py` | 270 | Real-time Phase 4 semantic verification progress tracker |
| `scripts/api_health_dashboard.py` | 360 | API health monitoring (endpoints, gunicorn, response times) |
| `scripts/backup_status.py` | 290 | Backup integrity and currency verification |
| `scripts/cron_job_monitor.py` | 360 | Cron job execution tracking and overdue detection |
| `scripts/daanaa_status.py` | 400 | Unified infrastructure status dashboard |

**Total Scripts:** 1,680 lines of production Python

### Service Configuration

| File | Lines | Purpose |
|------|-------|---------|
| `config/daanaa-status.service` | 36 | systemd service for unified dashboard auto-start |

### Documentation (3 guides)

| File | Lines | Purpose |
|------|-------|---------|
| `docs/MONITORING.md` | 400+ | Comprehensive monitoring reference and troubleshooting |
| `MONITORING_SETUP.md` | 300+ | Quick start guide with installation steps |
| `MONITORING_DELIVERABLES.md` | 350+ | Complete feature matrix and architecture |

**Additional:**
- `MONITORING_README.txt` — This summary document
- `MONITORING_MANIFEST.md` — This file

### Log Locations

All scripts write to these locations:

| Log File | Purpose |
|----------|---------|
| `logs/phase4_monitor.log` | Phase 4 progress (created by phase4_monitor.py) |
| `logs/api_health.log` | API health checks (created by api_health_dashboard.py) |
| `logs/backup_status.log` | Backup verification (created by backup_status.py) |
| `logs/cron_monitor.log` | Cron job status (created by cron_job_monitor.py) |
| `logs/daanaa_status.log` | Unified dashboard fallback (created by daanaa_status.py) |
| `/var/log/daanaa/status.log` | Unified dashboard primary (when running as service) |

---

## Installation Checklist

- [ ] Read `MONITORING_SETUP.md`
- [ ] Make scripts executable: `chmod +x scripts/*.py`
- [ ] Test API health monitor: `python3 scripts/api_health_dashboard.py --once`
- [ ] Test backup monitor: `python3 scripts/backup_status.py`
- [ ] Test cron monitor: `python3 scripts/cron_job_monitor.py`
- [ ] Test unified dashboard: `python3 scripts/daanaa_status.py --once`
- [ ] Copy systemd service: `sudo cp config/daanaa-status.service /etc/systemd/system/`
- [ ] Reload systemd: `sudo systemctl daemon-reload`
- [ ] Enable service: `sudo systemctl enable daanaa-status`
- [ ] Start service: `sudo systemctl start daanaa-status`
- [ ] Verify service: `sudo systemctl status daanaa-status`
- [ ] Watch logs: `sudo journalctl -u daanaa-status -f`

---

## Features by Monitor

### Phase 4 Monitor
- ✅ Real-time progress tracking
- ✅ GPU speed calculation (embeddings/min)
- ✅ ETA to completion
- ✅ Stall detection (speed < 10 e/min alert)
- ✅ Updates every 30 seconds
- ✅ Color-coded status display
- ✅ Graceful handling if Phase 4 not running

### API Health Dashboard
- ✅ `/health` endpoint monitoring (5-second interval)
- ✅ `/api/stats` endpoint validation
- ✅ Gunicorn process detection and memory tracking
- ✅ Response time trending (last 10 samples)
- ✅ Memory trend tracking (last 10 samples)
- ✅ Success rate calculation
- ✅ Threshold-based alerts (response time > 2s, memory > 1GB)
- ✅ Color-coded status output

### Backup Status Monitor
- ✅ Latest backup detection
- ✅ Size validation (≥ 1GB)
- ✅ Age check (≤ 24 hours)
- ✅ Gzip integrity verification (reads first 1MB)
- ✅ SQLite integrity validation (opens database)
- ✅ Backup directory statistics
- ✅ Next backup time estimation
- ✅ Human-readable and JSON output modes

### Cron Job Monitor
- ✅ Tracks 5 maintenance jobs:
  - `health_check` (every 5 min)
  - `backup_verify` (daily 03:00 UTC)
  - `cleanup_stale` (daily 04:00 UTC)
  - `db_optimize` (daily 05:00 UTC)
  - `precompute_orgs` (weekly Sunday 06:00 UTC)
- ✅ Last run time extraction
- ✅ Status parsing (SUCCESS/FAILED/WARNING)
- ✅ Overdue detection (no run in 2× interval)
- ✅ Log file handling (plain and .gz)
- ✅ Human-readable and JSON output modes

### Unified Dashboard
- ✅ Combines all 4 monitors
- ✅ System status (CPU, memory, disk, uptime)
- ✅ Real-time updates every 30 seconds
- ✅ Color-coded indicators
- ✅ Interactive display mode
- ✅ One-time check mode
- ✅ Background/log-only mode
- ✅ systemd service integration
- ✅ Graceful degradation if monitors fail

### Systemd Service
- ✅ Auto-start at boot
- ✅ Automatic restart on failure (30s delay)
- ✅ Resource limits (256MB memory, 10% CPU)
- ✅ Security hardening (PrivateTmp, NoNewPrivileges)
- ✅ journalctl integration
- ✅ Non-root execution (user: akbar)

---

## Usage Modes

Each monitor supports multiple modes:

### Interactive
```bash
python3 scripts/phase4_monitor.py
python3 scripts/api_health_dashboard.py
python3 scripts/daanaa_status.py
```

### One-Time Check
```bash
python3 scripts/backup_status.py
python3 scripts/cron_job_monitor.py
python3 scripts/daanaa_status.py --once
```

### JSON Output
```bash
python3 scripts/backup_status.py --json
python3 scripts/cron_job_monitor.py --json
```

### Background/Log-Only
```bash
python3 scripts/daanaa_status.py --log-only
```

### Systemd Service
```bash
sudo systemctl start daanaa-status
sudo systemctl status daanaa-status
sudo journalctl -u daanaa-status -f
```

---

## Alert Thresholds

| Monitor | Alert Type | Threshold |
|---------|-----------|-----------|
| Phase 4 | GPU Stalled | Speed < 10 embeddings/min |
| API Health | Slow Response | Response time > 2 seconds |
| API Health | High Memory | Gunicorn memory > 1 GB |
| API Health | Endpoint Down | /health returns non-200 |
| Backup | Too Small | Size < 1 GB |
| Backup | Too Old | Age > 24 hours |
| Backup | Corrupt | Integrity check fails |
| Cron Jobs | Overdue | No run in 2× scheduled interval |
| Cron Jobs | Failed | Last run status = FAILED |

---

## Performance Metrics

| Component | Memory | CPU | I/O | Update Interval |
|-----------|--------|-----|-----|-----------------|
| Phase 4 Monitor | <5MB | Low | Reads log file | 30 seconds |
| API Health Dashboard | <20MB | Low | HTTP requests | 5 seconds |
| Backup Status Monitor | <10MB | Medium | File reads | On-demand |
| Cron Job Monitor | <5MB | Low | Log file reads | On-demand |
| Unified Dashboard | <30MB | Low | Subprocess calls | 30 seconds |

**All monitors are I/O-bound and safe to run continuously.**

---

## Dependencies

### Python Packages
```bash
# In venv
pip install psutil requests numpy
```

### System Requirements
- Python 3.8+
- systemd (for service)
- `/usr/bin/python3` (for systemd service)

### Optional
- `/var/log/daanaa/` directory (for system log storage)
- Sufficient permissions in `/var/log/daanaa/`

---

## Integration Points

### Reads From
- `/tmp/phase4_progress.log` — Phase 4 progress updates
- `logs/phase4_checkpoint.json` — Phase 4 checkpoint
- `http://localhost:5000/health` — API health endpoint
- `http://localhost:5000/api/stats` — API statistics
- `~/meritgiving/backups/` — Backup directory
- `logs/*.log` — Cron job log files

### Writes To
- `logs/phase4_monitor.log` — Phase 4 monitor updates
- `logs/api_health.log` — API health checks
- `logs/backup_status.log` — Backup status
- `logs/cron_monitor.log` — Cron job status
- `/var/log/daanaa/status.log` — Unified dashboard (systemd)
- `logs/daanaa_status.log` — Unified dashboard (fallback)

### Complements
- `metrics_collector.py` — System-level metrics
- `alert_manager.py` — Alert routing
- `health_check.py` — API health (older implementation)
- `verify_backup_integrity.py` — Backup verification (older)

---

## Documentation Map

```
MONITORING_README.txt           ← Start here (you are here)
├── MONITORING_SETUP.md         ← Quick start guide
├── docs/MONITORING.md          ← Comprehensive reference
├── MONITORING_DELIVERABLES.md  ← Feature matrix
└── Script headers              ← Inline documentation
    ├── phase4_monitor.py
    ├── api_health_dashboard.py
    ├── backup_status.py
    ├── cron_job_monitor.py
    └── daanaa_status.py
```

---

## Status

✅ **All deliverables completed:**
- [x] 5 monitoring scripts (1,680 lines)
- [x] systemd service configuration
- [x] 3 comprehensive documentation guides
- [x] Error handling and graceful degradation
- [x] Color-coded status display
- [x] Real-time and on-demand monitoring modes
- [x] JSON output support
- [x] Log file integration
- [x] Alert thresholds

✅ **Ready for:**
- [x] Testing (use MONITORING_SETUP.md)
- [x] Deployment (use config/daanaa-status.service)
- [x] Production monitoring
- [x] Integration with existing infrastructure

---

## Support

See appropriate documentation:
- **Quick Start:** MONITORING_SETUP.md
- **Comprehensive:** docs/MONITORING.md
- **Features:** MONITORING_DELIVERABLES.md
- **Troubleshooting:** docs/MONITORING.md → Troubleshooting section

View logs for debugging:
```bash
tail -f ~/meritgiving/logs/*.log
sudo journalctl -u daanaa-status -f
```
