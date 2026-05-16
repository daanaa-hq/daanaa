#!/bin/bash
set -e
export DATABASE_URL="mysql://4E8vsnxzs7obsTq.root:w6bStKHUVhHK5ORBxmRj00Ni00sXryzq@ep-t4ni387b5e83b7519dc8.epsrv-t4n281l4mrmemi4zls9a.ap-southeast-1.privatelink.aliyuncs.com:4000/19e1bda0-5e92-832e-8000-0954986ba6ff"
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
