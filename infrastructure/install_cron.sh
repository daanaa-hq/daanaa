#!/bin/bash
# Install all Daanaa infrastructure cron jobs
# Run once: bash infrastructure/install_cron.sh

CRON_JOB='# ═══════════════════════════════════════════════════════════════
# DAANAA INFRASTRUCTURE JOBS (installed via infrastructure/install_cron.sh)
# ═══════════════════════════════════════════════════════════════

# Collect metrics every minute
* * * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 infrastructure/monitoring/metrics_collector.py >> /tmp/daanaa_metrics.log 2>&1

# Process alerts every minute (sends CRITICAL emails immediately)
* * * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 infrastructure/monitoring/alert_manager.py >> /tmp/daanaa_alerts.log 2>&1

# Send daily digest at 9 AM
0 9 * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 infrastructure/monitoring/alert_manager.py digest >> /tmp/daanaa_alerts.log 2>&1

# Daily home server backup (2 AM)
0 2 * * * cd /home/akbar/meritgiving && bash infrastructure/backup/daily_backup.sh >> /tmp/daanaa_backup.log 2>&1

# Cleanup old backups (weekly, Sunday 4 AM)
0 4 * * 0 cd /home/akbar/meritgiving && bash infrastructure/backup/cleanup_old_backups.sh >> /tmp/daanaa_backup.log 2>&1

# Monthly backup integrity test (1st of month, 10 AM)
0 10 1 * * cd /home/akbar/meritgiving && bash infrastructure/backup/test_restore.sh >> /tmp/daanaa_backup.log 2>&1

# Rotate logs (daily, keep 7 days)
0 1 * * * find /tmp/daanaa*.log -mtime +7 -delete 2>/dev/null || true
'

# Backup existing crontab
BACKUP_FILE="/tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || true
echo "Existing crontab backed up to: $BACKUP_FILE"

# Append new jobs
(crontab -l 2>/dev/null || true; echo ""; echo "$CRON_JOB") | crontab -
echo "✓ Cron jobs installed"
echo ""
echo "Installed jobs:"
crontab -l | grep -v "^#" | grep -v "^$" | tail -10
