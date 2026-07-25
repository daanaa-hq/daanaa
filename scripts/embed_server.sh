#!/usr/bin/env bash
# embed_server.sh — Start mxbai-embed-large llama-server on port 11436
# This runs independently of reembed_watchdog to ensure Phase 4 always has embeddings available.
# Usage: bash embed_server.sh start|stop|status

set -u

LLAMA_BIN="$HOME/llama-vulkan/build/bin/llama-server"
EMBED_MODEL="$HOME/models/mxbai-embed-large/gguf/mxbai-embed-large-v1-f16.gguf"
PORT=11436
LOG_DIR="$HOME/meritgiving/logs"
LOG_FILE="$LOG_DIR/embed_server.log"

# Parallel slots. Batch jobs (re-embedding the registry) are throughput bound,
# and 4 slots leaves the GPU idle between requests. Each slot gets
# CTX_SIZE/SLOTS tokens, so these two move together: 16384/16 = 1024 tokens per
# slot, comfortably above the longest name+mission+tags input we embed.
SLOTS="${EMBED_SLOTS:-16}"
CTX_SIZE="${EMBED_CTX:-16384}"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

start() {
  if pgrep -f "llama-server.*mxbai" >/dev/null; then
    echo "[$(ts)] embed_server: already running on :$PORT"
    return 0
  fi

  echo "[$(ts)] embed_server: starting mxbai-embed-large on :$PORT..."
  nohup "$LLAMA_BIN" \
    -m "$EMBED_MODEL" \
    --port "$PORT" \
    --host 127.0.0.1 \
    -ngl 99 \
    --device Vulkan1 \
    --ctx-size "$CTX_SIZE" \
    --batch-size 512 \
    -np "$SLOTS" \
    --embeddings \
    > "$LOG_FILE" 2>&1 &

  # Wait for server to become healthy (up to 2 min)
  for i in {1..60}; do
    if curl -s "http://127.0.0.1:$PORT/health" | grep -q '"status":"ok"'; then
      echo "[$(ts)] embed_server: healthy on :$PORT"
      return 0
    fi
    sleep 2
  done

  echo "[$(ts)] embed_server: ERROR — server did not start in time"
  return 1
}

stop() {
  if pgrep -f "llama-server.*mxbai" >/dev/null; then
    echo "[$(ts)] embed_server: stopping..."
    pkill -f "llama-server.*mxbai"
    fuser -k "${PORT}/tcp" 2>/dev/null || true
    sleep 1
    echo "[$(ts)] embed_server: stopped"
  else
    echo "[$(ts)] embed_server: not running"
  fi
}

status() {
  if pgrep -f "llama-server.*mxbai" >/dev/null; then
    echo "[$(ts)] embed_server: running on :$PORT"
    curl -s "http://127.0.0.1:$PORT/health" 2>/dev/null | jq . || echo "  (health check failed)"
  else
    echo "[$(ts)] embed_server: not running"
  fi
}

case "${1:-status}" in
  start)  start ;;
  stop)   stop ;;
  status) status ;;
  *)
    echo "Usage: $0 {start|stop|status}" >&2
    exit 1
    ;;
esac
