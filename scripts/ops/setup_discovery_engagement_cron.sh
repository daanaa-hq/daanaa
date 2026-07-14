#!/bin/bash
# Setup automatic discovery outreach cron job
# Runs daily at 2 AM to detect discovered orgs and send outreach

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$PROJECT_ROOT/scripts/auto_discovery_engagement.py"
LOG_FILE="$PROJECT_ROOT/logs/discovery_outreach.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Add cron job (if not already present)
CRON_ENTRY="0 2 * * * cd $PROJECT_ROOT && /usr/bin/python3 $SCRIPT >> $LOG_FILE 2>&1"

# Check if already exists
if crontab -l 2>/dev/null | grep -q "auto_discovery_engagement.py"; then
    echo "✅ Discovery outreach cron already configured"
else
    echo "Setting up discovery outreach cron..."
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✅ Cron job installed (runs daily at 2 AM)"
fi

# Manual test run
echo "Running test of discovery outreach system..."
python3 "$SCRIPT"
