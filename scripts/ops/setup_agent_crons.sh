#!/bin/bash
# Setup cron jobs for autonomous agents
# These run automatically to detect surges, apply boosts, and analyze outcomes

CRON_CMD="source venv/bin/activate"

# Agent 1: Surge Monitor (runs every 10 minutes during daytime, hourly off-hours)
# Detects spikes in search queries and identifies event types
SURGE_CRON="*/10 8-22 * * * $CRON_CMD && python3 scripts/agent_surge_monitor.py >> logs/agent_surge.log 2>&1"

# Agent 2: Outcome Analyzer (runs nightly at 2 AM)
# Measures whether boosts helped users, generates insights
OUTCOME_CRON="0 2 * * * $CRON_CMD && python3 scripts/agent_outcome_analyzer.py >> logs/agent_outcome.log 2>&1"

# Install crons
(crontab -l 2>/dev/null | grep -v "agent_surge_monitor\|agent_outcome_analyzer"; echo "$SURGE_CRON"; echo "$OUTCOME_CRON") | crontab -

echo "Agent crons installed:"
crontab -l | grep agent_

mkdir -p /home/akbar/meritgiving/logs
touch /home/akbar/meritgiving/logs/agent_surge.log
touch /home/akbar/meritgiving/logs/agent_outcome.log

echo ""
echo "Logs will appear in:"
echo "  - logs/agent_surge.log (every 10 min 8am-10pm)"
echo "  - logs/agent_outcome.log (nightly at 2am)"
