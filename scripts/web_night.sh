#!/usr/bin/env bash
# Overnight website discovery — loops web_finder_agent through the night so the
# GPU embed server (:11436) verifies candidate domains while the CPU crawls.
# Each pass takes a fresh revenue-DESC slice (failed attempts are marked and
# skipped for 90 days). Started/stopped by gpu_night.sh; killable.
set -u

BASE="$HOME/meritgiving"
cd "$BASE" || exit 1
# shellcheck disable=SC1091
source "$BASE/venv/bin/activate"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
echo "[$(ts)] web_night: website discovery loop starting"

while true; do
  echo "[$(ts)] web_finder pass: 200 orgs, high-revenue first"
  python3 scripts/web_finder_agent.py --limit 200 --priority high-revenue
  sleep 60
done
