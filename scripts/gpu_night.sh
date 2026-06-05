#!/usr/bin/env bash
# gpu_night.sh — run the GPU mission-gen pipeline only during the cool overnight
# window (cron starts at 22:00, stops at 06:00). Keeps the house from heating up
# during the day. Usage: gpu_night.sh {start|stop}
#
# Cron (user crontab):
#   0 22 * * * /home/akbar/meritgiving/scripts/gpu_night.sh start >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1
#   0 6  * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop  >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1

set -u

BASE="$HOME/meritgiving"
MODEL="$HOME/models/Qwen2.5-14B-Instruct-Q4_K_M.gguf"   # faster + cooler than 32B; quality validated for missions
SERVER_BIN="$HOME/llama-vulkan/build/bin/llama-server"
PORT=11437
LOG_DIR="$BASE/logs"
SERVER_LOG="$LOG_DIR/llama_32b.log"
GEN_LOG="$LOG_DIR/generate_missions_32b.log"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

start() {
  # Start independent embed server first — Phase 4 (web_finder_agent) depends on it.
  # This runs separately from mission generation so reembed issues don't block embeddings.
  echo "[$(ts)] start: launching embed_server (mxbai-embed-large on :11436)"
  bash "$BASE/scripts/embed_server.sh" start

  if pgrep -f "llama-server.*$(basename "$MODEL")" >/dev/null; then
    echo "[$(ts)] start: llama-server already running — skipping"
  else
    echo "[$(ts)] start: launching llama-server $(basename "$MODEL") (6 slots, continuous batching)"
    nohup "$SERVER_BIN" -m "$MODEL" --device Vulkan1 -ngl 99 -fa 1 \
      --parallel 6 --ctx-size 24576 --cont-batching \
      --port "$PORT" --host 127.0.0.1 --jinja \
      > "$SERVER_LOG" 2>&1 &
    # wait up to ~3 min for the server to be ready
    for _ in $(seq 1 60); do
      grep -q "server is listening\|all slots are idle" "$SERVER_LOG" 2>/dev/null && break
      sleep 3
    done
  fi

  if pgrep -f "scripts/generate_missions.py" >/dev/null; then
    echo "[$(ts)] start: generate_missions already running — skipping"
  else
    echo "[$(ts)] start: launching generate_missions (6 workers, resumable)"
    # shellcheck disable=SC1091
    source "$BASE/venv/bin/activate"
    cd "$BASE" || exit 1
    nohup python3 scripts/generate_missions.py --workers 6 >> "$GEN_LOG" 2>&1 &
  fi

  # CPU side: loop donate-link discovery/release so the CPU isn't idle (low heat)
  if pgrep -f "scripts/cpu_night.sh" >/dev/null; then
    echo "[$(ts)] start: cpu_night donate loop already running — skipping"
  else
    echo "[$(ts)] start: launching cpu_night donate loop"
    nohup bash "$BASE/scripts/cpu_night.sh" >> "$LOG_DIR/cpu_night.log" 2>&1 &
  fi

  # Re-embed orgs whose mission was (re)written so semantic search stays current.
  # The watchdog runs its own embed server on :11436 (separate from the mission
  # model on :11437) and re-embeds once enough missions are stale, then idles.
  if pgrep -f "scripts/reembed_watchdog.py" >/dev/null; then
    echo "[$(ts)] start: reembed_watchdog already running — skipping"
  else
    echo "[$(ts)] start: launching reembed_watchdog (re-embeds stale/new missions)"
    nohup "$BASE/venv/bin/python3" "$BASE/scripts/reembed_watchdog.py" \
      --threshold 5000 --interval 1800 >> "$LOG_DIR/reembed_watchdog.log" 2>&1 &
  fi
  echo "[$(ts)] start: done"
}

stop() {
  echo "[$(ts)] stop: halting cpu_night donate loop"
  pkill -f "scripts/cpu_night.sh" 2>/dev/null
  pkill -f "scripts/donation_link_pipeline.py" 2>/dev/null
  echo "[$(ts)] stop: halting generate_missions"
  pkill -f "scripts/generate_missions.py" 2>/dev/null
  sleep 2
  echo "[$(ts)] stop: halting reembed_watchdog"
  pkill -f "scripts/reembed_watchdog.py" 2>/dev/null
  echo "[$(ts)] stop: halting llama-server (mission generation)"
  pkill -f "llama-server.*$(basename "$MODEL")" 2>/dev/null
  sleep 2
  # belt-and-suspenders: free the mission port
  fuser -k "${PORT}/tcp" 2>/dev/null
  # NOTE: embed_server (port 11436) is kept running until Phase 4 completes.
  # Phase 4 may run until 07:00+. See stop_embed_server() cron job (runs at 08:00).
  echo "[$(ts)] stop: done (GPU freed, embed_server still running for Phase 4)"
}

stop_embed_server() {
  echo "[$(ts)] stop_embed_server: halting embed_server (used by Phase 4)"
  bash "$BASE/scripts/embed_server.sh" stop
}

case "${1:-}" in
  start)              start ;;
  stop)               stop ;;
  stop_embed_server)  stop_embed_server ;;
  *) echo "usage: $0 {start|stop|stop_embed_server}" >&2; exit 1 ;;
esac
