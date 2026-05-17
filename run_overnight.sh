#!/bin/bash
# Chains: wait for bge-large to finish → unload ollama → run cause tags → restart API
set -e

LOGDIR="/home/akbar/meritgiving/logs"
VENV="/home/akbar/meritgiving/venv/bin/python3"

echo "[$(date)] Waiting for bge-large embeddings to complete..."
while pgrep -f "build_embeddings.py" > /dev/null 2>&1; do
  sleep 30
done

echo "[$(date)] Embeddings done. Unloading ollama models from RAM..."
curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5:7b","keep_alive":0,"prompt":""}' > /dev/null 2>&1 || true

sleep 10

echo "[$(date)] Starting cause tag extraction..."
$VENV /home/akbar/meritgiving/scripts/extract_cause_tags.py \
  2>&1 | tee "$LOGDIR/cause_tags.log"

echo "[$(date)] Cause tags done. Restarting API..."
/home/akbar/meritgiving/restart_merit_api.sh

echo "[$(date)] All done."
