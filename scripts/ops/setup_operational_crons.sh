#!/bin/bash
# Setup operational crons for Daanaa AI partnership
# Run once to install all scheduled agents

REPO="/home/akbar/meritgiving"
VENV="$REPO/venv/bin/python3"

echo "Setting up Daanaa operational automation..."

# Create crontab entries (append to existing)
cat > /tmp/daanaa_crons.txt << 'CRON_EOF'
# ===== DAANAA OPERATIONAL CRONS =====

# DAILY: 6:00 AM CDT (11:00 AM UTC)
0 11 * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/morning_briefing_agent.py >> /home/akbar/meritgiving/logs/cron.log 2>&1

# DAILY: 2:00 PM CDT (19:00 UTC) - Link health check
0 19 * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/link_health_check_agent.py >> /home/akbar/meritgiving/logs/cron.log 2>&1

# WEEKLY: Monday 12:00 AM CDT (6:00 AM UTC)
0 6 * * 1 /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/weekly_summary_agent.py >> /home/akbar/meritgiving/logs/cron.log 2>&1

# MONTHLY: 1st of month, 12:00 AM CDT (6:00 AM UTC)
0 6 1 * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/monthly_rescore_agent.py >> /home/akbar/meritgiving/logs/cron.log 2>&1

# CONTINUOUS: Feedback ingestion (check every 30 min)
*/30 * * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/feedback_ingestion_agent.py >> /home/akbar/meritgiving/logs/cron.log 2>&1

# HOURLY: Phase 4 completion monitor (auto-queue next GPU work when Phase 4 finishes)
0 * * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/phase4_completion_monitor.py >> /home/akbar/meritgiving/logs/cron.log 2>&1

# GPU QUEUE: Run GPU queue manager (if queue is not empty and GPU is idle)
*/4 * * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/gpu_queue_manager.py --run >> /home/akbar/meritgiving/logs/cron.log 2>&1

# NIGHT: 11:00 PM CDT (4:00 AM UTC) - Start heavy compute jobs
0 4 * * * /home/akbar/meritgiving/scripts/night_batch_launcher.sh >> /home/akbar/meritgiving/logs/cron.log 2>&1

CRON_EOF

# Backup existing crontab
crontab -l > /tmp/crontab_backup.txt 2>/dev/null || true

# Append new entries (avoid duplicates)
crontab -l 2>/dev/null | grep -v "===== DAANAA OPERATIONAL CRONS =====" > /tmp/crontab_merged.txt 2>/dev/null || true
cat /tmp/daanaa_crons.txt >> /tmp/crontab_merged.txt
crontab /tmp/crontab_merged.txt

echo "✓ Operational crons installed"
echo "  Daily: 6 AM (morning briefing), 2 PM (link checks)"
echo "  Weekly: Monday 12 AM (summary)"
echo "  Monthly: 1st of month 12 AM (full rescore)"
echo "  Continuous: Feedback ingestion every 30 min"
echo ""
echo "View crontab: crontab -l"
echo "View logs: tail -f /home/akbar/meritgiving/logs/cron.log"
