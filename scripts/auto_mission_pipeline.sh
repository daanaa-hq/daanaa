#!/bin/bash
# Auto-mode: maintain Vulkan1 llama-server + run mission generation to completion.
# Restarts the llama-server if it crashes, and loops mission generation until done.
# Run: nohup bash scripts/auto_mission_pipeline.sh &

LLAMA_BIN="/home/akbar/llama-vulkan/build/bin/llama-server"
MODEL="$HOME/models/Qwen2.5-32B-Instruct-Q4_K_M.gguf"
LLAMA_LOG="$HOME/meritgiving/logs/llama-server-qwen32b.log"
MISSION_LOG="$HOME/meritgiving/logs/generate_missions_32b.log"
PORT=11437

start_llama() {
  echo "[$(date)] Starting Vulkan1 llama-server (Qwen2.5-32B)..."
  "$LLAMA_BIN" \
    -m "$MODEL" \
    --port $PORT --host 127.0.0.1 \
    -ngl 99 --device Vulkan1 \
    --ctx-size 20480 --batch-size 2048 -np 5 \
    >> "$LLAMA_LOG" 2>&1 &
  LLAMA_PID=$!
  echo "[$(date)] llama-server started PID $LLAMA_PID"
  # Wait for model to load
  for i in $(seq 1 60); do
    sleep 5
    if curl -sf http://127.0.0.1:$PORT/health 2>/dev/null | grep -q '"status":"ok"'; then
      echo "[$(date)] llama-server ready"
      return 0
    fi
    echo -n "."
  done
  echo "[$(date)] ERROR: llama-server failed to start in 5 minutes"
  return 1
}

ensure_llama() {
  if ! curl -sf http://127.0.0.1:$PORT/health 2>/dev/null | grep -q '"status":"ok"'; then
    pkill -f "llama-server.*$PORT" 2>/dev/null
    sleep 5
    start_llama
  fi
}

cd /home/akbar/meritgiving
source venv/bin/activate

echo "[$(date)] Auto-mission pipeline started"

# Start llama-server if not running
ensure_llama

while true; do
  # Run template missions first (fast, CPU) for name-only sources
  TEMPLATE_REMAINING=$(sqlite3 data/merit_registry.db \
    "SELECT COUNT(*) FROM registry_enriched WHERE (mission IS NULL OR mission = '') AND source IN ('IRS_BMF', 'bmf_stub');" 2>/dev/null)
  if [ "${TEMPLATE_REMAINING:-0}" -gt 0 ]; then
    echo "[$(date)] $TEMPLATE_REMAINING name-only orgs need template missions — running..."
    python3 scripts/generate_template_missions.py >> "$MISSION_LOG" 2>&1
  fi

  # Check how many enriched orgs still need LLM missions (excludes name-only sources)
  REMAINING=$(sqlite3 data/merit_registry.db \
    "SELECT COUNT(*) FROM registry_enriched WHERE (mission IS NULL OR mission = '') AND source NOT IN ('IRS_BMF', 'bmf_stub');" 2>/dev/null)

  echo "[$(date)] Orgs needing LLM missions: $REMAINING"

  if [ "${REMAINING:-0}" -eq 0 ]; then
    echo "[$(date)] All missions complete! Pipeline done."
    break
  fi

  ensure_llama

  echo "[$(date)] Running mission generation (--all-orgs --workers 4)..."
  timeout 7200 python3 scripts/generate_missions.py \
    --all-orgs --workers 2 >> "$MISSION_LOG" 2>&1
  EXIT=$?

  if [ $EXIT -eq 124 ]; then
    echo "[$(date)] Batch timed out after 2h, restarting (resumable)..."
  elif [ $EXIT -ne 0 ]; then
    echo "[$(date)] Mission gen exited with code $EXIT, checking server..."
    ensure_llama
    sleep 10
  fi
done

echo "[$(date)] Auto-mission pipeline finished."
