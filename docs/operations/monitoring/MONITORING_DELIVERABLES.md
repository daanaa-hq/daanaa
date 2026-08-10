# Monitoring Infrastructure Deliverables

## Summary

Complete monitoring infrastructure for Phase 4 semantic verification and API health, with real-time dashboards, health checks, and unified status reporting.

## Deliverables

### 1. ✅ Phase 4 Progress Monitor
**File:** `scripts/phase4_monitor.py` (270 lines)

Real-time tracker for semantic verification pipeline.

**Features:**
- Reads `/tmp/phase4_progress.log` in real-time
- Shows: candidates processed, verified count, speed (embeddings/min), ETA
- Updates every 30 seconds to stdout + log file
- GPU stall alert if speed < 10 embeddings/min
- Color-coded status (green/yellow/red)
- Calculates uptime and estimates completion time

**Usage:**
```bash
python3 scripts/phase4_monitor.py              # Interactive
python3 scripts/phase4_monitor.py --log-only   # Background
```

**Logs to:** `~/meritgiving/logs/phase4_monitor.log`

---

### 2. ✅ API Health Dashboard
**File:** `scripts/api_health_dashboard.py` (360 lines)

Monitors Daanaa API and gunicorn process health.

**Features:**
- Checks `/health` endpoint every 5 seconds
- Monitors `/api/stats` endpoint validity
- Tracks gunicorn memory usage and process status
- Maintains rolling window of last 10 response times and memory samples
- Color-coded alerts for slow responses (> 2s) or high memory (> 1GB)
- Shows success rate over time
- Integrates registry stats when available

**Checks:**
- HTTP 200 status on `/health`
- Valid JSON response on `/api/stats`
- Gunicorn process running
- Memory < 1GB threshold
- Response time < 2s threshold

**Usage:**
```bash
python3 scripts/api_health_dashboard.py        # Interactive
python3 scripts/api_health_dashboard.py --log-only  # Background
```

**Logs to:** `~/meritgiving/logs/api_health.log`

---

### 3. ✅ Backup Status Monitor
**File:** `scripts/backup_status.py` (290 lines)

Verifies backup integrity and currency.

**Features:**
- Finds latest backup in `~/meritgiving/backups`
- Validates file size (≥ 1GB minimum)
- Validates age (≤ 24 hours maximum)
- Performs gzip or SQLite integrity checks
- Reports backup directory statistics
- Calculates next scheduled backup time
- Outputs JSON for programmatic access

**Integrity Checks:**
- Gzip files: reads first 1MB to verify compression integrity
- SQLite files: opens database and validates structure
- Ensures backup not corrupted or truncated

**Usage:**
```bash
python3 scripts/backup_status.py               # Human-readable
python3 scripts/backup_status.py --json        # JSON output
python3 scripts/backup_status.py --log-only    # Log only
```

**Exit codes:** 0 = healthy, 1 = problems found

**Logs to:** `~/meritgiving/logs/backup_status.log`

---

### 4. ✅ Cron Job Monitor
**File:** `scripts/cron_job_monitor.py` (360 lines)

Tracks execution status of maintenance cron jobs.

**Monitored Jobs:**

| Job | Schedule | Interval | Log File |
|-----|----------|----------|----------|
| `health_check` | Every 5 min | 5 min | `health_check.log` |
| `backup_verify` | Daily 03:00 UTC | 1440 min | `backup_alert.log` |
| `cleanup_stale` | Daily 04:00 UTC | 1440 min | `cleanup_stale.log` |
| `db_optimize` | Daily 05:00 UTC | 1440 min | `db_optimize.log` |
| `precompute_orgs` | Weekly Sun 06:00 UTC | 10080 min | `precompute_orgs.log` |

**Features:**
- Parses log files (handles .gz compression)
- Extracts last run timestamp and status (SUCCESS/FAILED/WARNING)
- Calculates age since last run
- Detects overdue jobs (no run in 2× scheduled interval)
- Estimates next scheduled run
- Color-coded status display
- JSON output support

**Usage:**
```bash
python3 scripts/cron_job_monitor.py            # Human-readable
python3 scripts/cron_job_monitor.py --json     # JSON output
```

**Logs to:** `~/meritgiving/logs/cron_monitor.log`

---

### 5. ✅ Unified Dashboard
**File:** `scripts/daanaa_status.py` (400 lines)

Comprehensive infrastructure status combining all monitors.

**Dashboard Sections:**
1. **System Status** — CPU, memory, disk usage, uptime
2. **Phase 4 Progress** — Candidates, matches, processing speed
3. **API Health** — Endpoint status summary
4. **Backup Status** — Integrity, age, directory stats
5. **Cron Jobs** — All 5 jobs with status and timestamps

**Features:**
- Integrates all 4 specialized monitors
- Updates every 30 seconds (configurable)
- Color-coded status indicators (🟢 green / 🟡 yellow / 🔴 red)
- Runs interactively or as background service
- One-time check mode for cron/scripting
- Log-only mode for background execution
- Graceful fallback when monitors unavailable

**Usage:**
```bash
python3 scripts/daanaa_status.py               # Interactive (30s updates)
python3 scripts/daanaa_status.py --once        # One-time check
python3 scripts/daanaa_status.py --log-only    # Background mode
```

**Logs to:** `/var/log/daanaa/status.log` (or `~/meritgiving/logs/daanaa_status.log` if /var/log not writable)

---

### 6. ✅ Systemd Service
**File:** `config/daanaa-status.service` (30 lines)

System service for unified dashboard auto-start.

**Features:**
- Auto-starts at boot with `WantedBy=multi-user.target`
- Configured for user `akbar` (non-root)
- Resource limits: 256MB memory, 10% CPU
- Restart on failure with 30s delay
- Logs to journalctl for easy viewing
- Security hardening: PrivateTmp, NoNewPrivileges

**Installation:**
```bash
sudo cp config/daanaa-status.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable daanaa-status
sudo systemctl start daanaa-status
sudo journalctl -u daanaa-status -f
```

---

### 7. ✅ Documentation
**File:** `docs/MONITORING.md` (400+ lines)

Comprehensive monitoring guide covering:
- Overview of all monitors and their update intervals
- Quick start (test monitors, run dashboard, install service)
- Detailed descriptions of each monitor
- Installation steps with prerequisites
- Log file locations and monitoring commands
- JSON output examples
- Alerting strategy and intervention procedures
- Troubleshooting guide
- Performance notes and log rotation
- Integration with existing infrastructure

**File:** `MONITORING_SETUP.md` (300+ lines)

Quick start guide with:
- Files created summary
- Quick install steps
- Monitor descriptions
- Usage examples (interactive, one-time, JSON, background)
- Log file reference
- Troubleshooting
- Next steps

---

## Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                  Monitoring Infrastructure               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Phase 4 Monitor ───┐                                   │
│  - /tmp/phase4_progress.log                             │
│  - Calculates speed, ETA                                │
│                      │                                   │
│  API Health ────────┤ ┌──→ Unified Dashboard ──→ systemd service
│  - :5000/health     │ │    - Combines all 4        │
│  - Gunicorn memory  │ │    - Updates every 30s      │
│                      │ │    - Color-coded display    │
│  Backup Status ────┤ │    - JSON output            │
│  - ~/backups/       │ │    - Interactive + service   │
│  - Integrity check  │ │                              │
│                      │ │                              │
│  Cron Monitor ─────┘ │                              │
│  - 5 job log files   │                              │
│  - Overdue detection │                              │
│                      └─→ Log files (all monitors)       │
│                          │ phase4_monitor.log           │
│                          │ api_health.log               │
│                          │ backup_status.log            │
│                          │ cron_monitor.log             │
│                          │ /var/log/daanaa/status.log  │
│                                                        │
└─────────────────────────────────────────────────────────┘
```

### File Structure

```
~/meritgiving/
├── scripts/
│   ├── phase4_monitor.py           # Phase 4 progress tracker
│   ├── api_health_dashboard.py      # API & gunicorn monitor
│   ├── backup_status.py             # Backup integrity checker
│   ├── cron_job_monitor.py          # Cron job tracker
│   └── daanaa_status.py             # Unified dashboard
│
├── config/
│   └── daanaa-status.service        # systemd service
│
├── docs/
│   └── MONITORING.md                # Comprehensive guide
│
├── logs/
│   ├── phase4_monitor.log
│   ├── api_health.log
│   ├── backup_status.log
│   ├── cron_monitor.log
│   └── daanaa_status.log
│
└── MONITORING_SETUP.md              # Quick start guide

/var/log/daanaa/
└── status.log                       # Unified dashboard primary log

/etc/systemd/system/
└── daanaa-status.service            # Installed service
```

---

## Key Features

### Real-Time Monitoring
- Phase 4: 30-second updates
- API Health: 5-second checks
- Others: on-demand with instant results
- Updates without blocking

### Comprehensive Checks
- **Phase 4:** GPU speed, progress, ETA, stall detection
- **API:** Endpoint health, memory, response time trend
- **Backup:** Integrity validation, age check, size verification
- **Cron:** Status tracking, overdue detection
- **System:** CPU, memory, disk usage

### Alerting
- Color-coded status (green/yellow/red)
- Threshold-based alerts:
  - GPU speed < 10 embeddings/min → RED
  - Response time > 2s → YELLOW/RED
  - Memory > 1GB → RED
  - Backup age > 24h → RED
  - Backup size < 1GB → RED
  - Cron job overdue → RED

### Flexibility
- Interactive dashboards for real-time watching
- One-time checks for scripting
- Background mode for cron jobs
- JSON output for programmatic access
- systemd service for auto-start and persistent monitoring

### Graceful Degradation
- Monitors work independently
- Unified dashboard continues if one monitor fails
- Falls back to home directory logs if /var/log not writable
- Handles missing log files gracefully
- No dependencies on other infrastructure

---

## Installation

### Prerequisites
```bash
# Python packages (in venv)
source ~/meritgiving/venv/bin/activate
pip install psutil requests numpy
```

### Quick Setup
```bash
# Make scripts executable (you'll need to do this manually)
chmod +x ~/meritgiving/scripts/{phase4_monitor,api_health_dashboard,backup_status,cron_job_monitor,daanaa_status}.py

# Test unified dashboard
python3 ~/meritgiving/scripts/daanaa_status.py --once

# Install as service (optional)
sudo cp ~/meritgiving/config/daanaa-status.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable daanaa-status
sudo systemctl start daanaa-status
```

---

## Usage Examples

### Watch Phase 4 Progress
```bash
python3 scripts/phase4_monitor.py
# Updates every 30 seconds until Ctrl+C
```

### Check API Health
```bash
python3 scripts/api_health_dashboard.py --once
# Single health check
```

### Verify Backup
```bash
python3 scripts/backup_status.py --json
# JSON output for scripting
```

### Monitor Cron Jobs
```bash
python3 scripts/cron_job_monitor.py
# Shows all 5 jobs and last run status
```

### Unified Dashboard Service
```bash
# Start service
sudo systemctl start daanaa-status

# Watch in real-time
sudo journalctl -u daanaa-status -f

# Or check once
python3 scripts/daanaa_status.py --once
```

---

## Testing Checklist

- [x] All 5 monitor scripts created with proper error handling
- [x] Graceful handling of missing data files/endpoints
- [x] Color-coded status output
- [x] Log file writing to appropriate locations
- [x] JSON output support (where applicable)
- [x] Threshold-based alerting
- [x] ETA calculations for Phase 4
- [x] Speed/performance tracking
- [x] Cron job overdue detection
- [x] Backup integrity validation (gzip + SQLite)
- [x] Unified dashboard integration
- [x] systemd service configuration
- [x] Comprehensive documentation (2 guides + inline code comments)

---

## Next Steps

1. **Manual Setup:** Make scripts executable and test individually
2. **Service Installation:** Install systemd service for persistent monitoring
3. **Log Rotation:** Set up log rotation for long-term operation
4. **Alerting Integration:** Connect to email/Twilio for alerts (future)
5. **Dashboard Integration:** Embed in Grafana/Prometheus (future)
6. **Performance Tuning:** Adjust check intervals based on production load

---

## Support

See `docs/MONITORING.md` for comprehensive documentation.

See `MONITORING_SETUP.md` for quick start guide.

Check individual script headers for usage examples.

Report issues by reviewing log files:
```bash
tail -f ~/meritgiving/logs/*.log
sudo journalctl -u daanaa-status -f
```
