#!/bin/bash
# setup_cron_schedules.sh — install the FULL Daanaa crontab.
#
# This file is the single source of truth for the crontab. It REPLACES the
# whole crontab on install, so every job must be listed here.
# Schedule evidence recovered from /var/log/syslog on 2026-07-17 after an
# earlier version of this script accidentally wiped the pre-existing jobs
# (see LESSONS.md 2026-07-17).
#
# All times are LOCAL server time (America/Chicago, UTC-5 in summer).

set -euo pipefail

REPO="$HOME/meritgiving"
cd "$REPO"
mkdir -p logs

# Backup current crontab before replacing (kept in repo logs, timestamped)
crontab -l > "logs/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || true

CRONTAB_TMP=$(mktemp)
cat > "$CRONTAB_TMP" << 'CRON'
# ============================================================
# DAANAA CRONTAB — installed by scripts/setup_cron_schedules.sh
# Edit that script, not this crontab directly.
# ============================================================

# ---------- Monitoring & watchdogs ----------
* * * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 infrastructure/monitoring/metrics_collector.py >> /tmp/daanaa_metrics.log 2>&1
* * * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 infrastructure/monitoring/alert_manager.py >> /tmp/daanaa_alerts.log 2>&1
*/5 * * * * cd ~/meritgiving && venv/bin/python3 scripts/ops/daanaa_watchdog.py >> logs/watchdog.log 2>&1
*/15 * * * * /home/akbar/meritgiving/scripts/api_watchdog.sh
*/5 * * * * /home/akbar/meritgiving/scripts/watchdog_discovery.sh
0 * * * * python3 /home/akbar/meritgiving/scripts/monitor_discovery_health.py >> /home/akbar/meritgiving/logs/health_monitor_cron.log 2>&1
0 9 * * * cd /home/akbar/meritgiving && source venv/bin/activate && python3 infrastructure/monitoring/alert_manager.py digest >> /tmp/daanaa_alerts.log 2>&1

# ---------- Backups ----------
30 2 * * * bash ~/meritgiving/scripts/ops/daanaa_backup.sh >> ~/meritgiving/logs/backup.log 2>&1
0 3 * * * bash ~/meritgiving/scripts/ops/monitor_backups.sh >> ~/meritgiving/logs/backup_monitor.log 2>&1

# ---------- Data pipeline ----------
# IRS EO data refresh: Mondays 02:00 (downloads BMF, delta-loads new orgs + FTS)
0 2 * * 1 bash /home/akbar/meritgiving/scripts/refresh_irs_data.sh >> /home/akbar/meritgiving/logs/cron.log 2>&1
# Delta scorer REMOVED 2026-07-17: overnight_pipeline (02:30 daily) already runs
# the FULL v5 scorer + loader nightly, so a separate 02:00 delta pass was pure
# duplication. Script kept for ad-hoc use: scripts/delta_scorer_v5_nightly.py
# Overnight pipeline: daily 02:30 (scoring, FTS, enrichment, snapshot)
30 2 * * * cd /home/akbar/meritgiving && /home/akbar/meritgiving/venv/bin/python3 scripts/overnight_pipeline.py >> logs/overnight.log 2>&1
# IRS revocation sync: daily 03:00 (full sync — marks revoked orgs inactive)
0 3 * * * cd /home/akbar/meritgiving && /home/akbar/meritgiving/venv/bin/python3 scripts/sync_irs_revocations.py >> logs/irs_revocations.log 2>&1
# Daily data audit: 00:30
30 0 * * * python3 /home/akbar/meritgiving/scripts/daily_data_audit.py >> /home/akbar/meritgiving/logs/daily_data_audit.log 2>&1

# GT990 e-file index refresh: Sundays 01:00 (public S3, no auth)
0 1 * * 0 bash /home/akbar/meritgiving/scripts/cron_refresh_gt990.sh >> /home/akbar/meritgiving/logs/gt990_refresh.log 2>&1
# 990 website expansion: Sundays 05:00 — extracts org-attested websites from fresh filings
0 5 * * 0 cd /home/akbar/meritgiving && venv/bin/python3 scripts/expand_990_coverage.py --workers 12 >> logs/expand_990_coverage.log 2>&1

# ---------- Discovery & deployment ----------
# Deploy queued verified links every 4 hours
0 */4 * * * python3 /home/akbar/meritgiving/scripts/deploy_queued_links.py >> /home/akbar/meritgiving/logs/deployment_cron.log 2>&1
# Discovery progress report every 6 hours
0 */6 * * * /home/akbar/meritgiving/scripts/discovery_progress_report.sh >> /home/akbar/meritgiving/logs/discovery_progress.log 2>&1
# Nightly search DB deploy to droplet: 08:15
15 8 * * * bash /home/akbar/meritgiving/scripts/ops/nightly_search_deploy.sh >> /home/akbar/meritgiving/logs/nightly_search_deploy.log 2>&1
# Morning deploy: 14:00
0 14 * * * /home/akbar/meritgiving/scripts/deploy_morning.sh

# Nonprofit discovery orchestrator: 11:00 daily (multi-source website batch)
0 11 * * * cd /home/akbar/meritgiving && venv/bin/python3 scripts/nonprofit_discovery_orchestrator.py >> logs/discovery_orchestrator.log 2>&1
# Discovery efficiency monitor: every 30 min (80%-of-peak reconnect signal)
*/30 * * * * cd /home/akbar/meritgiving && venv/bin/python3 scripts/monitor_discovery_efficiency.py >> logs/efficiency_monitor.log 2>&1

# ---------- GPU night mode ----------
0 21 * * * /home/akbar/meritgiving/scripts/gpu_night.sh start >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1
0 2 * * * /home/akbar/meritgiving/scripts/enrichment_loop_8pm_8am.sh
0 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1
5 9 * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop_embed_server >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1

# ---------- Marketing / campaigns ----------
*/5 * * * * cd /home/akbar/meritgiving && python3 scripts/campaigns_orchestrator.py --action monitor_posted_campaigns >> logs/cron_monitor.log 2>&1
0 18 * * * cd /home/akbar/meritgiving && python3 scripts/campaigns_orchestrator.py --action collect_daily_metrics >> logs/cron_metrics.log 2>&1

# ---------- Email agent ----------
0 */2 * * * cd /home/akbar/meritgiving && /home/akbar/meritgiving/venv/bin/python3 -m scripts.email_agent.run --limit 50 --query 'newer_than:2d -label:daanaa/triaged' >> /home/akbar/meritgiving/logs/email_agent.log 2>&1

# ---------- Governance ----------
# Decision queue check: every 12h (08:00 + 20:00) — surfaces open decisions for board simulation (docs/DECISION_WORKFLOW.md)
0 8,20 * * * bash /home/akbar/meritgiving/scripts/check_decision_queue.sh

# AI-output sample audit: 1st of month 06:00 (policy: BOARD_SIMULATION_2026_07_17_EVENING point 2)
0 6 1 * * cd /home/akbar/meritgiving && venv/bin/python3 scripts/ai_output_sample_audit.py >> logs/ai_audit/cron.log 2>&1

# ---------- Weekly ----------
# Public visibility monitor every 48 hours; report-only, no deploy or external communication
20 6 */2 * * cd /home/akbar/meritgiving && /home/akbar/meritgiving/venv/bin/python3 visibility/scripts/build_weekly_visibility_monitor.py >> logs/visibility/monitor_cron.log 2>&1
# Token review: Mondays 08:00
0 8 * * 1 bash /home/akbar/meritgiving/scripts/ops/token_review.sh >> /home/akbar/meritgiving/logs/token_review/cron.log 2>&1
CRON

crontab "$CRONTAB_TMP"
rm -f "$CRONTAB_TMP"

echo "Crontab installed ($(crontab -l | grep -c '^[0-9*]') jobs). Backup of previous crontab in logs/."
