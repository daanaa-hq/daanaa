#!/bin/bash
# check_decision_queue.sh — 12-hour decision-queue check.
# Counts open items in governance/DECISION_QUEUE.md. If any exist, writes a
# marker + log line so the next active session runs the board simulation.
# Protocol: docs/DECISION_WORKFLOW.md

QUEUE="/home/akbar/meritgiving/governance/DECISION_QUEUE.md"
MARKER="/home/akbar/meritgiving/logs/.DECISIONS_PENDING"
LOG="/home/akbar/meritgiving/logs/decision_queue.log"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

if [ ! -f "$QUEUE" ]; then
  echo "[$(ts)] queue file missing" >> "$LOG"
  exit 0
fi

OPEN=$(grep -c '^## \[open\]' "$QUEUE")

if [ "$OPEN" -gt 0 ]; then
  {
    echo "[$(ts)] $OPEN open decision(s) awaiting board simulation:"
    grep '^## \[open\]' "$QUEUE" | sed 's/^## \[open\] /  - /'
  } | tee -a "$LOG" > "$MARKER"
else
  rm -f "$MARKER"
  echo "[$(ts)] queue clear" >> "$LOG"
fi
