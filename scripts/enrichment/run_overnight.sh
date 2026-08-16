#!/bin/bash
# Chains: wait for bge-large → Claude Sonnet cause tags → restart API
set -e

LOGDIR="/home/akbar/meritgiving/logs"
VENV="/home/akbar/meritgiving/venv/bin/python3"

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "Error: ANTHROPIC_API_KEY not set. Run: export ANTHROPIC_API_KEY=sk-ant-..."
  exit 1
fi

echo "[$(date)] Waiting for bge-large embeddings to complete..."
while pgrep -f "build_embeddings.py" > /dev/null 2>&1; do
  sleep 30
done

echo "[$(date)] Embeddings done. Starting Claude Sonnet cause tag extraction..."
$VENV /home/akbar/meritgiving/scripts/extract_cause_tags_claude.py \
  --rebuild \
  2>&1 | tee "$LOGDIR/cause_tags_claude.log"

echo "[$(date)] Cause tags done. Restarting API..."
/home/akbar/meritgiving/restart_merit_api.sh

echo "[$(date)] All done."
