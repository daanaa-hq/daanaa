#!/usr/bin/env bash
# scripts/setup_cron.sh
# Installs the MERIT automated refresh cron jobs.
# Run once; safe to re-run (replaces existing MERIT entries).
#
# Jobs installed:
#   - Weekly ProPublica backfill + percentile recompute (Sun 2 AM)
#   - Monthly API server health check + restart if down (1st of month, 3 AM)

set -euo pipefail

BASE="$HOME/meritgiving"
SCRIPTS="$BASE/scripts"
LOGS="$BASE/autodev/logs"

mkdir -p "$LOGS"
chmod +x "$SCRIPTS/auto_refresh.sh"

# Strip any existing MERIT cron lines, then append fresh ones
TMPFILE=$(mktemp)
crontab -l 2>/dev/null | grep -v "# MERIT_AUTO" > "$TMPFILE" || true

cat >> "$TMPFILE" <<'EOF'

# MERIT_AUTO: weekly data refresh (ProPublica backfill + SOI ingest + percentiles) — Sun 2 AM
0 2 * * 0  /home/akbar/meritgiving/scripts/auto_refresh.sh >> /home/akbar/meritgiving/autodev/logs/refresh.log 2>&1

# MERIT_AUTO: monthly IRS SOI file download — 1st of month at 1 AM
0 1 1 * *  /home/akbar/meritgiving/scripts/download_irs_soi.sh >> /home/akbar/meritgiving/autodev/logs/soi_download.log 2>&1

# MERIT_AUTO: ensure API is running — every 15 minutes
*/15 * * * *  pgrep -f merit_api.py > /dev/null || (source /home/akbar/meritgiving/venv/bin/activate && cd /home/akbar/meritgiving && python3 merit_api.py &) >> /home/akbar/meritgiving/autodev/logs/watchdog.log 2>&1
EOF

crontab "$TMPFILE"
rm "$TMPFILE"

echo "Cron jobs installed:"
crontab -l | grep "MERIT_AUTO"
echo ""
echo "To remove:  crontab -e  (delete lines containing MERIT_AUTO)"
echo "Logs:       $LOGS/refresh.log"
echo "            $LOGS/watchdog.log"
