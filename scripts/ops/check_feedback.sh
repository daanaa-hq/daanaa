#!/bin/bash
# Pull fresh feedback + analytics from the production live DB every 6 hours.
# Appends new submissions to logs/feedback_live.log and prints a summary.
set -e

DROPLET="root@107.170.26.8"
SSH_KEY="/home/akbar/.ssh/daanaa_do_cron"  # passphrase-free automation key (see LESSONS.md 2026-07-05)
LIVE_DB="/tmp/daanaa_live_check.db"
LOG="/home/akbar/meritgiving/logs/feedback_live.log"
SEEN_FILE="/home/akbar/meritgiving/logs/feedback_last_rowid"
TS="$(date '+%Y-%m-%d %H:%M:%S')"

rsync -az -q -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    "$DROPLET:/opt/daanaa/data/daanaa_live.db" "$LIVE_DB"

LAST=$(cat "$SEEN_FILE" 2>/dev/null || echo 0)

NEW=$(sqlite3 "$LIVE_DB" "SELECT rowid, created_at, category, message FROM feedback WHERE rowid > $LAST ORDER BY rowid;")

if [ -n "$NEW" ]; then
    echo "[$TS] NEW FEEDBACK:" | tee -a "$LOG"
    echo "$NEW" | tee -a "$LOG"
    MAX=$(sqlite3 "$LIVE_DB" "SELECT MAX(rowid) FROM feedback;")
    echo "$MAX" > "$SEEN_FILE"
else
    echo "[$TS] No new feedback (last rowid: $LAST)" >> "$LOG"
fi

# Always log visit summary
VISITS=$(sqlite3 "$LIVE_DB" "SELECT metric, count FROM visit_counter;")
TODAY=$(sqlite3 "$LIVE_DB" "SELECT path, count, dwell_secs FROM analytics_daily WHERE day = date('now') ORDER BY count DESC LIMIT 5;")
echo "[$TS] Visits: $VISITS | Top pages today: $TODAY" >> "$LOG"

rm -f "$LIVE_DB"
