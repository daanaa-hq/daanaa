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

# Phase 0 once per night: audit ALL existing donate_urls — this is the only
# step that promotes unverified (NULL-status) links to 'beta' so they can
# display, and the only step that catches links that have since died. Added
# 2026-07-10: 883 links were sitting at NULL status because nothing ran this.
echo "[$(ts)] phase 0: audit existing donate links (promote verified -> beta, clear dead)"
python3 scripts/donation_link_pipeline.py --phase 0

while true; do
  echo "[$(ts)] discover up to 200 candidates from verified websites"
  python3 scripts/donation_link_pipeline.py --phase 1 --orgs 200
  echo "[$(ts)] release verified batch (confidence-gated, <=50)"
  python3 scripts/donation_link_pipeline.py --phase 2
  sleep 30
done
