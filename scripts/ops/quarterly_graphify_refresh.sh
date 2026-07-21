#!/bin/bash
# Quarterly graphify refresh — mechanical only, no judgment calls.
#
# Re-runs the code-only knowledge-graph extraction (frontend/ + scripts/) so
# the graph stays current with 90 days of new commits, then logs a dated
# reminder in TODOS.md for a human/Claude Code session to run the actual
# dead-code AUDIT (verify findings, decide what's safe to archive, apply the
# 30-day recall pattern from archive/dead_code_20260721/). This script never
# moves or deletes files itself — see DECISIONS.md 2026-07-21 for why the
# review step stays human-in-the-loop (STEWARDSHIP.md P10).
#
# Installed via crontab: 0 6 1 */3 * (quarterly, 1st of every 3rd month, 6am)
set -euo pipefail
cd "$(dirname "$0")/../.."

LOG="logs/graphify_refresh.log"
echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') — quarterly graphify refresh ===" >> "$LOG"

if ! command -v graphify >/dev/null 2>&1; then
  echo "graphify CLI not found on PATH — skipping refresh, logging reminder only" >> "$LOG"
else
  graphify extract ./frontend/ --code-only --out ./frontend/ >> "$LOG" 2>&1 || echo "frontend/ extraction failed, see log" >> "$LOG"
  graphify extract ./scripts/ --code-only --out ./scripts/ >> "$LOG" 2>&1 || echo "scripts/ extraction failed, see log" >> "$LOG"
  graphify merge-graphs ./frontend/graphify-out/graph.json ./scripts/graphify-out/graph.json --out graphify-out/graph.json >> "$LOG" 2>&1 || echo "merge failed, see log" >> "$LOG"
  echo "Graph refreshed: $(date '+%Y-%m-%d')" >> "$LOG"
fi

REMINDER_DATE=$(date '+%Y-%m-%d')
NEXT_DATE=$(date -d '+90 days' '+%Y-%m-%d' 2>/dev/null || date -v+90d '+%Y-%m-%d' 2>/dev/null || echo "+90 days from $REMINDER_DATE")
{
  echo ""
  echo "## Quarterly graphify dead-code audit due ($REMINDER_DATE)"
  echo "Graph refreshed automatically. Run the actual audit manually (or ask Claude Code):"
  echo "grep the graph for duplicate function/class names across files + isolated"
  echo "(<=1 edge) nodes, verify each with git log + grep for live references,"
  echo "archive confirmed-dead files to archive/dead_code_\$(date +%Y%m%d)/ with a"
  echo "30-day recall README. See DECISIONS.md 2026-07-21 for the reference pattern."
  echo "(Next auto-reminder: ~$NEXT_DATE)"
  echo ""
} >> TODOS.md

echo "Reminder logged to TODOS.md" >> "$LOG"
