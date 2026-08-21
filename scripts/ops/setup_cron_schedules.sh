#!/bin/bash
# setup_cron_schedules.sh — install the FULL Daanaa crontab.
#
# This file is the single source of truth for the crontab. It REPLACES the
# whole crontab on install, so every job must be listed here.
# Schedule evidence recovered from /var/log/syslog on 2026-07-17 after an
# earlier version of this script accidentally wiped the pre-existing jobs
# (see LESSONS.md 2026-07-17).
#
# Regenerated 2026-08-16 from the LIVE crontab (ground truth), which had
# drifted from this checked-in file two ways: (1) most paths here still
# pointed at pre-folder-migration locations -- e.g. scripts/api_watchdog.sh
# instead of scripts/ops/api_watchdog.sh -- fixed directly on the live
# crontab during an earlier pass this session but never backported here,
# so re-running this script would have silently reinstalled all 26 broken
# entries (see LESSONS.md "A folder migration is not done when the files
# land"); and (2) ~20 jobs had been added straight to the live crontab over
# time and were never added here at all. Both problems are now the same
# problem: this file was not the actual source of truth it claims to be.
# Treat this regeneration as the new baseline -- edit this file for any
# future change, then re-run it, rather than editing the live crontab
# directly again.
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
# DAANAA CRONTAB — installed by scripts/ops/setup_cron_schedules.sh
# Edit that script, not this crontab directly.
# ============================================================

# ---------- Monitoring & watchdogs ----------
# infrastructure/monitoring/metrics_collector.py + alert_manager.py retired
# 2026-08-21 (LESSONS.md same date): metrics_collector checked localhost:5000,
# never production; alert_manager's send_alert_email() built a full email but
# never called smtplib, just logged to /tmp. Both fully superseded by
# daanaa_watchdog.py below, which actually alerts via mailer.py (real Gmail
# send + ntfy push) and checks the real production endpoints. Confirmed via
# Codex read-only investigation: no other file consumes their output.
*/5 * * * * cd ~/meritgiving && venv/bin/python3 scripts/ops/daanaa_watchdog.py >> logs/watchdog.log 2>&1
*/15 * * * * /home/akbar/meritgiving/scripts/ops/api_watchdog.sh
*/5 * * * * /home/akbar/meritgiving/scripts/ops/watchdog_discovery.sh
0 * * * * python3 /home/akbar/meritgiving/scripts/ops/monitor_discovery_health.py >> /home/akbar/meritgiving/logs/health_monitor_cron.log 2>&1
*/30 * * * * python3 scripts/ops/hardware_monitor.py >> logs/hardware_monitor.log 2>&1
0 * * * * python3 scripts/ops/blitz_efficiency_tracker.py >> logs/blitz_efficiency.log 2>&1
*/15 * * * * python3 scripts/ops/monitor_phase1.py >> logs/phase1_monitor.log 2>&1
*/30 * * * * /home/akbar/meritgiving/scripts/ops/autonomous_health_monitor.sh >> /home/akbar/meritgiving/logs/autonomous_health.log 2>&1
0 * * * * /home/akbar/meritgiving/scripts/ops/monitor_db_corruption.sh
0 */2 * * * /home/akbar/meritgiving/scripts/ops/autonomous_precompute_watch.sh
6 7 * * * /home/akbar/.claude/skills/phase1-monitor/bin/run-daily.sh >> /home/akbar/meritgiving/logs/phase1_monitor.log 2>&1
0 20 * * 5 /home/akbar/.claude/skills/phase1-monitor/bin/run-weekly.sh >> /home/akbar/meritgiving/logs/phase1_monitor.log 2>&1

# ---------- Backups ----------
30 2 * * * bash ~/meritgiving/scripts/ops/daanaa_backup.sh >> ~/meritgiving/logs/backup.log 2>&1
0 2 * * * /home/akbar/meritgiving/scripts/ops/backup_strategy.sh >> /home/akbar/meritgiving/logs/backup_daily.log 2>&1
# Offsite core export: ~80MB of crawl/GPU-derived data to S3. The 23GB DB is
# deliberately NOT shipped -- it is re-ingestable/recomputable. Sunday run
# includes a full restore drill; an unverified backup is a belief.
15 3 * * 0 bash $HOME/meritgiving/scripts/ops/backup_core_export.sh --verify-restore >> $HOME/meritgiving/logs/backup_core_export.log 2>&1
15 3 * * 1-6 bash $HOME/meritgiving/scripts/ops/backup_core_export.sh >> $HOME/meritgiving/logs/backup_core_export.log 2>&1
0 3 * * * sqlite3 /home/akbar/meritgiving/data/merit_registry.db "PRAGMA quick_check;" >> /home/akbar/meritgiving/logs/integrity_check.log 2>&1

# ---------- Data pipeline ----------
# IRS EO data refresh: Mondays 02:00 (downloads BMF, delta-loads new orgs + FTS)
0 2 * * 1 bash /home/akbar/meritgiving/scripts/migrations/refresh_irs_data.sh >> /home/akbar/meritgiving/logs/cron.log 2>&1
# Delta scorer REMOVED 2026-07-17: overnight_pipeline (02:30 daily) already runs
# the FULL v5 scorer + loader nightly, so a separate 02:00 delta pass was pure
# duplication. Script kept for ad-hoc use: scripts/scoring/delta_scorer_v5_nightly.py
# Overnight pipeline: daily 02:30 (scoring, FTS, enrichment, snapshot)
30 2 * * * cd /home/akbar/meritgiving && /home/akbar/meritgiving/venv/bin/python3 scripts/core/overnight_pipeline.py >> logs/overnight.log 2>&1
# IRS revocation sync: daily 03:00 (full sync -- marks revoked orgs inactive)
0 3 * * * cd /home/akbar/meritgiving && /home/akbar/meritgiving/venv/bin/python3 scripts/ops/sync_irs_revocations.py >> logs/irs_revocations.log 2>&1
# Daily data audit: 00:30
30 0 * * * python3 /home/akbar/meritgiving/scripts/ops/daily_data_audit.py >> /home/akbar/meritgiving/logs/daily_data_audit.log 2>&1

# GT990 e-file index refresh: Sundays 01:00 (public S3, no auth)
0 1 * * 0 bash /home/akbar/meritgiving/scripts/cron_refresh_gt990.sh >> /home/akbar/meritgiving/logs/gt990_refresh.log 2>&1
# 990 website expansion: Sundays 05:00 — extracts org-attested websites from fresh filings
0 5 * * 0 cd /home/akbar/meritgiving && venv/bin/python3 scripts/discovery/expand_990_coverage.py --workers 12 >> logs/expand_990_coverage.log 2>&1
# IRS direct-filing recent-batch refresh: daily 04:15 -- checks apps.irs.gov's
# monthly XML batches directly (updates monthly, vs gt990's ~2-3mo bulk-rebuild
# cadence) and refreshes any registry org found in a batch not yet processed.
# Never-downgrade + reconciliation rules owned by fetch_irs_direct_filing.py.
15 4 * * * /home/akbar/meritgiving/venv/bin/python3 -m scripts.ops.refresh_recent_filings_batch --apply >> logs/irs_direct_recent_filings.log 2>&1

# ---------- Discovery & deployment ----------
# Deploy queued verified links hourly. Drains verified links into
# registry_enriched.donate_url. Takes ~2s for ~1,300 links, so hourly is
# cheap; the earlier 4-hourly schedule meant links sat undeployed for up to
# 4h. flock -n prevents overlapping runs writing the same EIN rows (see the
# 2026-07-25 concurrent-write incident that lost 45K links).
0 * * * * /usr/bin/flock -n /tmp/daanaa-deploy-links.lock python3 /home/akbar/meritgiving/scripts/ops/deploy_queued_links.py >> /home/akbar/meritgiving/logs/deployment_cron.log 2>&1
# Discovery progress report every 6 hours
0 */6 * * * /home/akbar/meritgiving/scripts/discovery/discovery_progress_report.sh >> /home/akbar/meritgiving/logs/discovery_progress.log 2>&1
# Nightly search DB deploy to droplet: 08:15
15 8 * * * bash /home/akbar/meritgiving/scripts/ops/nightly_search_deploy.sh >> /home/akbar/meritgiving/logs/nightly_search_deploy.log 2>&1
# Morning deploy: 14:00
0 14 * * * /home/akbar/meritgiving/scripts/ops/deploy_morning.sh

# Nonprofit discovery orchestrator: 11:00 daily (multi-source website batch)
0 11 * * * cd /home/akbar/meritgiving && venv/bin/python3 scripts/discovery/nonprofit_discovery_orchestrator.py >> logs/discovery_orchestrator.log 2>&1
# Discovery efficiency monitor: every 30 min (80%-of-peak reconnect signal)
*/30 * * * * cd /home/akbar/meritgiving && venv/bin/python3 scripts/ops/monitor_discovery_efficiency.py >> logs/efficiency_monitor.log 2>&1
23 * * * * python3 scripts/discovery/website_discovery_engine.py >> logs/website_discovery.log 2>&1
0 20 * * * bash scripts/discovery/evening_discovery_batch.sh
0 18,20,22,0,2,4 * * * bash -c 'source venv/bin/activate && python3 scripts/discovery/multi_agent_discovery.py >> logs/discovery_2hr_checkpoints.log 2>&1' &
# Parallel discovery agents. agent_coordinator.py was retired to
# scripts/archive/legacy_agents/ on 2026-08-12 (Task #6 Phase 4 legacy-agent
# cleanup) -- this job called it silently for 4 days after that with no
# error visible anywhere but the log. Dropped the dead half, fixed
# claude_agents.py's path to its actual current location.
0 6,8,10,12,14,16,18,20,22,0,2,4 * * * bash -c 'source ~/meritgiving/venv/bin/activate && python3 ~/meritgiving/scripts/ops/claude_agents.py >> ~/meritgiving/logs/dual_agent_checkpoints.log 2>&1' &

# ---------- GPU night mode ----------
0 21 * * * /home/akbar/meritgiving/scripts/enrichment/gpu_night.sh start >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1
0 2 * * * /home/akbar/meritgiving/scripts/ops/enrichment_loop_8pm_8am.sh
0 9 * * * /home/akbar/meritgiving/scripts/enrichment/gpu_night.sh stop >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1
5 9 * * * /home/akbar/meritgiving/scripts/enrichment/gpu_night.sh stop_embed_server >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1

# ---------- Marketing / campaigns ----------
*/5 * * * * cd /home/akbar/meritgiving && python3 scripts/admin/campaigns_orchestrator.py --action monitor_posted_campaigns >> logs/cron_monitor.log 2>&1
0 18 * * * cd /home/akbar/meritgiving && python3 scripts/admin/campaigns_orchestrator.py --action collect_daily_metrics >> logs/cron_metrics.log 2>&1

# ---------- Email agent ----------
0 */2 * * * cd /home/akbar/meritgiving && /home/akbar/meritgiving/venv/bin/python3 -m scripts.email_agent.run --limit 50 --query 'newer_than:2d -label:daanaa/triaged' >> /home/akbar/meritgiving/logs/email_agent.log 2>&1

# ---------- Governance ----------
# Decision queue check: every 12h (08:00 + 20:00) — surfaces open decisions for board simulation (docs/DECISION_WORKFLOW.md)
0 8,20 * * * bash /home/akbar/meritgiving/scripts/ops/check_decision_queue.sh

# AI-output sample audit: 1st of month 06:00 (policy: BOARD_SIMULATION_2026_07_17_EVENING point 2)
0 6 1 * * cd /home/akbar/meritgiving && venv/bin/python3 scripts/enrichment/ai_output_sample_audit.py >> logs/ai_audit/cron.log 2>&1

# ---------- Weekly ----------
# Public visibility monitor every 48 hours; report-only, no deploy or external
# communication. NOTE: source script (visibility/scripts/build_weekly_visibility_monitor.py)
# was archived to archive/projects/visibility/ -- this job is currently DEAD
# (fails silently into logs/visibility/monitor_cron.log every run) and kept
# here only so it's visible for a founder decision to either restore the
# script or remove the job, rather than being invisible drift again.
20 6 */2 * * cd /home/akbar/meritgiving && /home/akbar/meritgiving/venv/bin/python3 visibility/scripts/build_weekly_visibility_monitor.py >> logs/visibility/monitor_cron.log 2>&1
# Token review: Mondays 08:00
0 8 * * 1 bash /home/akbar/meritgiving/scripts/ops/token_review.sh >> /home/akbar/meritgiving/logs/token_review/cron.log 2>&1
# fixed 2026-08-08: "PRAGMA integrity_check LIMIT 1" is invalid SQL and errored
# every night since install. quick_check is the correct pragma (see above,
# ---------- Backups ----------).
# fixed 2026-08-08: was "6 * * * *" (hourly) for a script named run-daily.
CRON

crontab "$CRONTAB_TMP"
rm -f "$CRONTAB_TMP"

echo "Crontab installed ($(crontab -l | grep -c '^[0-9*]') jobs). Backup of previous crontab in logs/."
