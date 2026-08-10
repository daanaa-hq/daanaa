================================================================================
DAANAA MONITORING INFRASTRUCTURE — COMPLETE
================================================================================

BUILD COMPLETE: 5 monitoring scripts + unified dashboard + systemd service

================================================================================
DELIVERABLES
================================================================================

✓ MONITORING SCRIPTS (5 total)
  1. scripts/phase4_monitor.py (270 lines)
     - Real-time Phase 4 semantic verification progress
     - GPU speed, ETA, stall detection
     - Updates: every 30 seconds
     - Alert: speed < 10 embeddings/min

  2. scripts/api_health_dashboard.py (360 lines)
     - API /health and /api/stats endpoint monitoring
     - Gunicorn memory usage and process status
     - Response time trending (last 10 samples)
     - Updates: every 5 seconds
     - Alerts: response time > 2s, memory > 1GB

  3. scripts/backup_status.py (290 lines)
     - Backup integrity verification (gzip + SQLite)
     - Size (≥ 1GB) and age (≤ 24h) checks
     - Backup directory statistics
     - JSON output support

  4. scripts/cron_job_monitor.py (360 lines)
     - Tracks 5 maintenance cron jobs:
       • health_check (every 5 min)
       • backup_verify (daily 03:00 UTC)
       • cleanup_stale (daily 04:00 UTC)
       • db_optimize (daily 05:00 UTC)
       • precompute_orgs (weekly Sunday 06:00 UTC)
     - Detects overdue jobs (2× interval with no run)
     - JSON output support

  5. scripts/daanaa_status.py (400 lines)
     - UNIFIED DASHBOARD combining all 4 monitors
     - System status (CPU, memory, disk, uptime)
     - Real-time updates every 30 seconds
     - Color-coded status (green/yellow/red)
     - One-time check mode for scripting
     - Background mode for systemd service

✓ SYSTEMD SERVICE
  config/daanaa-status.service
  - Auto-start unified dashboard at boot
  - Resource limits: 256MB memory, 10% CPU
  - Restart on failure with 30s delay
  - Logs to journalctl

✓ DOCUMENTATION (2 guides + inline comments)
  docs/MONITORING.md (400+ lines)
  - Comprehensive reference guide
  - Setup instructions, usage examples
  - Troubleshooting, performance notes
  - Integration with existing systems

  MONITORING_SETUP.md (300+ lines)
  - Quick start guide
  - Installation steps
  - Monitor descriptions
  - Common troubleshooting

✓ SUMMARY DOCUMENTS
  MONITORING_DELIVERABLES.md - Full feature matrix
  MONITORING_README.txt - This file

================================================================================
QUICK START
================================================================================

1. MAKE SCRIPTS EXECUTABLE (you'll need to do this manually)

   chmod +x ~/meritgiving/scripts/phase4_monitor.py
   chmod +x ~/meritgiving/scripts/api_health_dashboard.py
   chmod +x ~/meritgiving/scripts/backup_status.py
   chmod +x ~/meritgiving/scripts/cron_job_monitor.py
   chmod +x ~/meritgiving/scripts/daanaa_status.py

2. TEST INDIVIDUAL MONITORS

   # API health (API must be running on :5000)
   python3 ~/meritgiving/scripts/api_health_dashboard.py --once

   # Backup status
   python3 ~/meritgiving/scripts/backup_status.py

   # Cron jobs
   python3 ~/meritgiving/scripts/cron_job_monitor.py

   # Phase 4 (only if Phase 4 is running)
   python3 ~/meritgiving/scripts/phase4_monitor.py

3. TEST UNIFIED DASHBOARD

   # One-time check
   python3 ~/meritgiving/scripts/daanaa_status.py --once

   # Interactive dashboard (Ctrl+C to stop)
   python3 ~/meritgiving/scripts/daanaa_status.py

4. INSTALL SYSTEMD SERVICE (optional)

   # Copy service file
   sudo cp ~/meritgiving/config/daanaa-status.service /etc/systemd/system/

   # Reload and start
   sudo systemctl daemon-reload
   sudo systemctl enable daanaa-status
   sudo systemctl start daanaa-status

   # View logs
   sudo journalctl -u daanaa-status -f

================================================================================
MONITOR DESCRIPTIONS
================================================================================

PHASE 4 MONITOR (scripts/phase4_monitor.py)
  Reads: /tmp/phase4_progress.log
  Displays: candidates processed, verified matches, processing speed (e/min), ETA
  Updates: every 30 seconds
  Alert: speed < 10 embeddings/min (GPU stalled)
  Log: ~/meritgiving/logs/phase4_monitor.log

API HEALTH DASHBOARD (scripts/api_health_dashboard.py)
  Checks: /health endpoint, /api/stats validity, gunicorn memory
  Interval: 5 seconds
  Tracks: response time and memory trends (last 10 each)
  Alerts: response time > 2s, memory > 1GB
  Log: ~/meritgiving/logs/api_health.log

BACKUP STATUS MONITOR (scripts/backup_status.py)
  Verifies: latest backup exists, size ≥ 1GB, age ≤ 24h
  Checks: gzip integrity or SQLite validity
  Reports: backup age, directory stats, next backup time
  Output: human-readable or JSON
  Log: ~/meritgiving/logs/backup_status.log

CRON JOB MONITOR (scripts/cron_job_monitor.py)
  Monitors: 5 maintenance cron jobs
  Shows: last run time, status, age, next scheduled run
  Detects: overdue jobs (not run in 2× interval)
  Output: human-readable or JSON
  Log: ~/meritgiving/logs/cron_monitor.log

UNIFIED DASHBOARD (scripts/daanaa_status.py)
  Integrates: all 4 monitors above
  Displays: system status + Phase 4 + API + Backup + Cron
  Updates: every 30 seconds
  Color: green (healthy), yellow (warning), red (critical)
  Modes: interactive, one-time, background, service
  Log: /var/log/daanaa/status.log (or fallback to ~/meritgiving/logs/)

================================================================================
USAGE EXAMPLES
================================================================================

WATCH PHASE 4 PROGRESS IN REAL-TIME
  python3 ~/meritgiving/scripts/phase4_monitor.py
  # Updates every 30 seconds, shows speed, ETA, alerts

MONITOR API HEALTH
  python3 ~/meritgiving/scripts/api_health_dashboard.py
  # Continuous monitoring of /health, memory, response times

CHECK BACKUP STATUS
  python3 ~/meritgiving/scripts/backup_status.py
  # One-time check: integrity, size, age

LIST CRON JOB STATUS
  python3 ~/meritgiving/scripts/cron_job_monitor.py
  # Shows last run, status, overdue detection for 5 jobs

UNIFIED INFRASTRUCTURE STATUS
  # Interactive (updates every 30s)
  python3 ~/meritgiving/scripts/daanaa_status.py

  # One-time check
  python3 ~/meritgiving/scripts/daanaa_status.py --once

  # As systemd service (persistent)
  sudo systemctl start daanaa-status
  sudo journalctl -u daanaa-status -f

JSON OUTPUT (for scripting)
  python3 ~/meritgiving/scripts/backup_status.py --json
  python3 ~/meritgiving/scripts/cron_job_monitor.py --json

BACKGROUND MODE (for cron)
  python3 ~/meritgiving/scripts/daanaa_status.py --log-only
  # Logs to file, no stdout

================================================================================
LOG FILES
================================================================================

Individual monitor logs:
  ~/meritgiving/logs/phase4_monitor.log      (Phase 4 progress)
  ~/meritgiving/logs/api_health.log          (API health checks)
  ~/meritgiving/logs/backup_status.log       (Backup verification)
  ~/meritgiving/logs/cron_monitor.log        (Cron job status)

Unified dashboard logs:
  /var/log/daanaa/status.log                 (primary, via systemd)
  ~/meritgiving/logs/daanaa_status.log       (fallback if /var/log not writable)

View logs:
  tail -f ~/meritgiving/logs/*.log
  sudo journalctl -u daanaa-status -f

================================================================================
ALERT THRESHOLDS
================================================================================

PHASE 4 MONITOR
  🔴 RED:    speed < 10 embeddings/min (GPU stalled)
  🟡 YELLOW: speed 10-20 embeddings/min (degraded)
  🟢 GREEN:  speed > 20 embeddings/min (healthy)

API HEALTH DASHBOARD
  🔴 RED:    response time > 2s OR memory > 1GB OR endpoint down
  🟡 YELLOW: response time 1-2s OR memory trending high
  🟢 GREEN:  all checks passing

BACKUP STATUS MONITOR
  🔴 RED:    size < 1GB OR age > 24h OR integrity failed
  🟡 YELLOW: approaching thresholds
  🟢 GREEN:  healthy

CRON JOB MONITOR
  🔴 RED:    last run FAILED OR job overdue (2× interval, no run)
  🟡 YELLOW: status WARNING
  🟢 GREEN:  last run SUCCESS and on schedule

================================================================================
TROUBLESHOOTING
================================================================================

MONITORS SHOW "CONNECTION REFUSED"
  → API server is not running on port 5000
  → Start it: cd ~/meritgiving && ./restart_api.sh

PHASE 4 MONITOR SHOWS "NO PROGRESS FILE"
  → Phase 4 semantic verification is not running
  → Start it: python3 scripts/phase4_semantic_verification.py --limit 50000 &

SYSTEMD SERVICE WON'T START
  → Check errors: sudo journalctl -u daanaa-status -n 20 --no-pager
  → Ensure Python packages: pip install psutil requests numpy
  → Fix permissions: sudo chown $(whoami):$(whoami) /var/log/daanaa

CAN'T WRITE TO /var/log/daanaa
  → Create directory: sudo mkdir -p /var/log/daanaa
  → Fix permissions: sudo chown $(whoami):$(whoami) /var/log/daanaa
  → Service will fallback to ~/meritgiving/logs/daanaa_status.log

================================================================================
ARCHITECTURE
================================================================================

Phase 4 Monitor          ┐
API Health Dashboard    ├→ Unified Dashboard → systemd service
Backup Status Monitor   ├→ (integrates all 4) → journalctl
Cron Job Monitor        ┘

All monitors:
  ✓ Run independently
  ✓ Handle missing data gracefully
  ✓ Write to log files for auditability
  ✓ Support JSON output (where applicable)
  ✓ Have color-coded status indicators

Unified dashboard:
  ✓ Combines all 4 monitors
  ✓ Updates every 30 seconds
  ✓ Continues if individual monitor fails
  ✓ Can run interactively or as service
  ✓ One-time check mode for scripting

================================================================================
DOCUMENTATION
================================================================================

READ FIRST:  MONITORING_SETUP.md (this folder)
  → Quick start guide with installation steps

READ NEXT:   docs/MONITORING.md (comprehensive reference)
  → Full feature descriptions, usage examples, troubleshooting

SCRIPT HEADERS: Each script has inline documentation
  → python3 scripts/phase4_monitor.py
  → python3 scripts/api_health_dashboard.py
  → etc.

================================================================================
FILES CREATED
================================================================================

Core Scripts:
  ~/meritgiving/scripts/phase4_monitor.py
  ~/meritgiving/scripts/api_health_dashboard.py
  ~/meritgiving/scripts/backup_status.py
  ~/meritgiving/scripts/cron_job_monitor.py
  ~/meritgiving/scripts/daanaa_status.py

Service:
  ~/meritgiving/config/daanaa-status.service

Documentation:
  ~/meritgiving/docs/MONITORING.md
  ~/meritgiving/MONITORING_SETUP.md
  ~/meritgiving/MONITORING_DELIVERABLES.md

This File:
  ~/meritgiving/MONITORING_README.txt

Log Locations:
  ~/meritgiving/logs/phase4_monitor.log
  ~/meritgiving/logs/api_health.log
  ~/meritgiving/logs/backup_status.log
  ~/meritgiving/logs/cron_monitor.log
  ~/meritgiving/logs/daanaa_status.log
  /var/log/daanaa/status.log

================================================================================
NEXT STEPS
================================================================================

1. Make scripts executable:
   chmod +x ~/meritgiving/scripts/phase4_monitor.py
   chmod +x ~/meritgiving/scripts/api_health_dashboard.py
   chmod +x ~/meritgiving/scripts/backup_status.py
   chmod +x ~/meritgiving/scripts/cron_job_monitor.py
   chmod +x ~/meritgiving/scripts/daanaa_status.py

2. Test individual monitors:
   python3 ~/meritgiving/scripts/api_health_dashboard.py --once

3. Test unified dashboard:
   python3 ~/meritgiving/scripts/daanaa_status.py --once

4. Install systemd service (optional):
   sudo cp ~/meritgiving/config/daanaa-status.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable daanaa-status
   sudo systemctl start daanaa-status

5. View logs:
   sudo journalctl -u daanaa-status -f

================================================================================
SUPPORT
================================================================================

For detailed information, see:
  - MONITORING_SETUP.md (quick start)
  - docs/MONITORING.md (comprehensive guide)
  - Script header comments (usage and examples)

View logs to debug issues:
  tail -f ~/meritgiving/logs/*.log
  sudo journalctl -u daanaa-status -f

================================================================================
END OF README
================================================================================
