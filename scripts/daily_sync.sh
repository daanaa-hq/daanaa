#!/bin/bash
# RETIRED 2026-06-09 — legacy TiDB pipeline, removed from cron. Credential scrubbed:
# DATABASE_URL must come from a gitignored .env file, never hardcoded. The old
# credential was leaked in git history and MUST be rotated in the TiDB/Aliyun console.
set -e
[ -f "$HOME/meritgiving/.env" ] && set -a && . "$HOME/meritgiving/.env" && set +a
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
