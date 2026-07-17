#!/bin/bash
# setup_cron_schedules.sh — Configure automated scoring and revocation checks

set -euo pipefail

VENV="$HOME/meritgiving/venv"
REPO="$HOME/meritgiving"

echo "Setting up cron schedules for Daanaa Phase 1..."
echo ""

# Ensure we're in the repo
cd "$REPO"

# Read current crontab (if exists)
CRONTAB_TMP=$(mktemp)
crontab -l > "$CRONTAB_TMP" 2>/dev/null || true

# Remove any existing entries for our scripts (to avoid duplication)
grep -v "delta_scorer_v5_nightly\|sync_irs_revocations\|overnight_pipeline" "$CRONTAB_TMP" > "$CRONTAB_TMP.new" || true

cat > "$CRONTAB_TMP.new" << 'CRON'
# ========== DAANAA DATA PIPELINE ==========
# Authority: Phase 1 Acceleration (July 16, 2026)
# All times UTC. Email output to root@localhost (logs/cron.log).

# Revocation check: DAILY at 03:30 UTC
# Lightweight check using cached IRS data; detects newly-revoked organizations
30 3 * * * source $HOME/meritgiving/venv/bin/activate && cd $HOME/meritgiving && python3 scripts/sync_irs_revocations.py --check >> logs/cron.log 2>&1

# Delta scorer: NIGHTLY (except Saturday) at 02:00 UTC
# Scores newly-added organizations within 24 hours of IRS refresh
0 2 * * 0-5 source $HOME/meritgiving/venv/bin/activate && cd $HOME/meritgiving && python3 scripts/delta_scorer_v5_nightly.py >> logs/cron.log 2>&1

# Overnight full pipeline: SATURDAY at 01:30 UTC
# Comprehensive refresh: revocation sync, full rescoring, FTS rebuild, enrichment
30 1 * * 6 source $HOME/meritgiving/venv/bin/activate && cd $HOME/meritgiving && python3 scripts/overnight_pipeline.py >> logs/cron.log 2>&1

# ========== IRS DATA REFRESH ==========
# IRS data sync: MONDAY at 02:00 UTC (before delta scorer runs)
# Downloads weekly IRS Exempt Organizations list, delta-loads new EINs
0 2 * * 1 source $HOME/meritgiving/venv/bin/activate && cd $HOME/meritgiving && python3 scripts/refresh_irs_data.sh >> logs/cron.log 2>&1
CRON

# Install the new crontab
crontab "$CRONTAB_TMP.new"
rm -f "$CRONTAB_TMP" "$CRONTAB_TMP.new"

echo "✅ Cron schedule installed:"
echo ""
crontab -l | grep -A 20 "DAANAA DATA PIPELINE"
echo ""
echo "Schedule summary:"
echo "  - Revocation check: Daily at 03:30 UTC"
echo "  - Delta scorer: Nightly (Sun-Fri) at 02:00 UTC"
echo "  - Full pipeline: Saturdays at 01:30 UTC"
echo "  - IRS refresh: Mondays at 02:00 UTC"
echo ""
echo "Logs: $REPO/logs/cron.log"
