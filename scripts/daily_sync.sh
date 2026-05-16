#!/bin/bash
set -e
export DATABASE_URL="[REDACTED_ROTATED_CREDENTIAL]"
export PATH="$HOME/.local/bin:$PATH"
BASE="$HOME/meritgiving"
LOG="$BASE/logs/sync-$(date +%Y%m%d).log"
mkdir -p "$BASE/logs"
echo "[$(date '+%H:%M:%S')] Starting MERIT sync" >> "$LOG"
cd "$BASE"
python3 "$BASE/scripts/batch_import.py" >> "$LOG" 2>&1
python3 "$BASE/scripts/enrich_v2.py" >> "$LOG" 2>&1
python3 "$BASE/scripts/logo_fetcher.py" >> "$LOG" 2>&1
echo "[$(date '+%H:%M:%S')] Done" >> "$LOG"
find "$BASE/logs" -name "sync-*.log" -mtime +30 -delete 2>/dev/null || true
