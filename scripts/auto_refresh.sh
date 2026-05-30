#!/usr/bin/env bash
# scripts/auto_refresh.sh
# Automated data freshness pipeline — safe to run on a cron schedule.
#
# What it does:
#   1. ProPublica backfill — updates revenue/assets/mission for cached EINs
#   2. IRS SOI ingest — pulls latest available year from data/irs_soi/
#      (run scripts/download_irs_soi.sh first to refresh the source files)
#   3. Recomputes peer groups + provisional revenue percentiles
#   4. Composite scorer — upgrades peer_percentile to the documented
#      0.65 revenue / 0.35 reserve formula within regional peer groups.
#      MUST run after step 3 (it reads the peer_group that step 3 writes).
#
# Typical schedule (set via:  crontab -e):
#   Weekly full refresh — every Sunday at 2 AM:
#     0 2 * * 0  /home/akbar/meritgiving/scripts/auto_refresh.sh >> /home/akbar/meritgiving/autodev/logs/refresh.log 2>&1
#   Monthly SOI file download — 1st of each month at 1 AM:
#     0 1 1 * *  /home/akbar/meritgiving/scripts/download_irs_soi.sh >> /home/akbar/meritgiving/autodev/logs/soi_download.log 2>&1
#
# Manual run:
#   ./scripts/auto_refresh.sh

set -euo pipefail

BASE="$HOME/meritgiving"
VENV="$BASE/venv/bin/activate"
LOG_DIR="$BASE/autodev/logs"
STAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

mkdir -p "$LOG_DIR"

echo ""
echo "=========================================="
echo " MERIT Data Refresh — $STAMP"
echo "=========================================="

source "$VENV"

cd "$BASE"

echo ""
echo "[1/4] ProPublica backfill..."
python3 scripts/propublica_backfill.py

echo ""
echo "[2/4] IRS SOI ingest (latest year only)..."
LATEST_YEAR=$(ls data/irs_soi/*eoextract990.zip 2>/dev/null | sort -r | head -1 | grep -oP '(?<=soi/)\d{2}' | head -1)
if [ -n "$LATEST_YEAR" ]; then
    python3 scripts/ingest_irs_soi.py --year $((2000 + LATEST_YEAR))
else
    echo "  No SOI files found — skipping. Run scripts/download_irs_soi.sh first."
fi

echo ""
echo "[3/4] Recomputing peer groups + provisional percentiles..."
python3 scripts/recompute_percentiles.py

echo ""
echo "[4/4] Composite score (0.65 revenue / 0.35 reserve, regional peer groups)..."
python3 scripts/compute_composite_score.py

echo ""
echo "Refresh complete — $STAMP"
echo "=========================================="
