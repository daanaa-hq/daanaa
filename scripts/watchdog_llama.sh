#!/bin/bash
# Watchdog: restart Qwen2.5-32B llama-server if it stops responding
MODEL="$HOME/models/Qwen2.5-32B-Instruct-Q4_K_M.gguf"
LOG="$HOME/meritgiving/logs/llama-server-qwen32b.log"

start_server() {
  /home/akbar/llama-vulkan/build/bin/llama-server \
    -m "$MODEL" \
    --port 11437 --host 127.0.0.1 \
    -ngl 99 --device Vulkan1 \
    --ctx-size 20480 --batch-size 2048 -np 5 \
    >> "$LOG" 2>&1 &
  echo "[$(date)] Watchdog: started llama-server PID $!" >> "$LOG"
}

while true; do
  if ! curl -sf http://127.0.0.1:11437/health 2>/dev/null | grep -q '"status":"ok"'; then
    echo "[$(date)] Watchdog: server down, restarting..." >> "$LOG"
    pkill -f "llama-server.*11437" 2>/dev/null
    sleep 5
    start_server
    sleep 60  # wait for model to load
  fi
  sleep 30
done
