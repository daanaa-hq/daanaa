#!/usr/bin/env bash
# Overnight CPU work — loops donate-link discovery + release through the night so
# the CPU keeps producing beta donate links instead of going idle. Network-bound,
# near-zero heat. Started/stopped by gpu_night.sh (10pm-6am window); killable.
set -u

BASE="$HOME/meritgiving"
cd "$BASE" || exit 1
# shellcheck disable=SC1091
source "$BASE/venv/bin/activate"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
echo "[$(ts)] cpu_night: donate loop starting"

while true; do
  echo "[$(ts)] discover up to 200 candidates from verified websites"
  python3 scripts/donation_link_pipeline.py --phase 1 --orgs 200
  echo "[$(ts)] release verified batch (confidence-gated, <=50)"
  python3 scripts/donation_link_pipeline.py --phase 2
  sleep 30
done
