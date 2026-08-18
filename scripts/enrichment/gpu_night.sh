#!/usr/bin/env bash
# gpu_night.sh — run the GPU mission-gen pipeline only during the cool overnight
# window (cron starts at 21:00, stops at 09:00). Keeps the house from heating up
# during the day. Usage: gpu_night.sh {start|stop}
#
# Cron (user crontab):
#   0 21 * * * /home/akbar/meritgiving/scripts/gpu_night.sh start >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1
#   0 9  * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop  >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1
#   5 9  * * * /home/akbar/meritgiving/scripts/gpu_night.sh stop_embed_server >> /home/akbar/meritgiving/logs/gpu_night.log 2>&1

set -u

BASE="$HOME/meritgiving"
MODEL="$HOME/models/qwen3-30b-a3b-2507/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf"  # MoE (3B active) — ~5x throughput of dense 32B at similar quality; benched + 11K-mission supervised run 2026-06-10
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
  bash "$BASE/scripts/ops/embed_server.sh" start

  # match by port, not model basename — survives model swaps between edits
  if pgrep -f "llama-server.*--port ${PORT}" >/dev/null; then
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

  if pgrep -f "scripts/generate_missions" >/dev/null; then
    echo "[$(ts)] start: mission generation already running — skipping"
  else
    echo "[$(ts)] start: launching mission generation (upgrade template_ntee → AI, then IRS_BMF backlog)"
    # shellcheck disable=SC1091
    source "$BASE/venv/bin/activate"
    cd "$BASE" || exit 1
    nohup bash -c "python3 scripts/generate_missions.py --workers 6 --upgrade-templates && python3 scripts/generate_missions_irs_bmf.py --workers 6 --upgrade-templates" >> "$GEN_LOG" 2>&1 &
  fi

  # Donate-link night loop (phase 0 audit + phase 1/2 discovery-release).
  # cpu_night.sh's header always claimed gpu_night starts it, but the wiring
  # was never added — casualty of the 2026-06-22 "no websites or donate
  # links" pause, which the founder superseded on 2026-07-07. Wired for real
  # on 2026-07-10; this is why displayable donate links froze at 82 since
  # the Jul 5 launch.
  if pgrep -f "scripts/cpu_night.sh" >/dev/null; then
    echo "[$(ts)] start: cpu_night donate loop already running — skipping"
  else
    echo "[$(ts)] start: launching cpu_night donate-link loop"
    nohup bash "$BASE/scripts/cpu_night.sh" >> "$LOG_DIR/cpu_night.log" 2>&1 &
  fi

  # Website discovery: DISABLED 2026-06-22 per directive — "we are not doing
  # websites or donate links." The web_finder_agent loop is network-bound and
  # off-mission; do not relaunch it. Left in place (commented) for traceability.
  # if pgrep -f "scripts/web_night.sh" >/dev/null; then
  #   echo "[$(ts)] start: web_night discovery loop already running — skipping"
  # else
  #   echo "[$(ts)] start: launching web_night discovery loop"
  #   nohup bash "$BASE/scripts/web_night.sh" >> "$LOG_DIR/web_night.log" 2>&1 &
  # fi

  # Cause tag enrichment: PAUSED 2026-07-07 for validation week — retired in
  # favor of the consolidated enrichment pipeline (scripts/enrich_batch.py),
  # which generates cause tags + mission + website + donate_url together
  # with shared context. Re-enable this block if quality_log shows the new
  # pipeline's tag accuracy regresses vs this script's baseline. See
  # DECISIONS.md 2026-07-07 and docs/superpowers/specs/2026-07-07-*.
  # if pgrep -f "scripts/enrich_cause_tags_llm.py" >/dev/null; then
  #   echo "[$(ts)] start: cause-tag enrichment already running — skipping"
  # else
  #   echo "[$(ts)] start: launching LLM cause-tag enrichment (249K gap)"
  #   nohup "$BASE/venv/bin/python3" "$BASE/scripts/enrich_cause_tags_llm.py" \
  #     >> "$LOG_DIR/cause_tags_llm.log" 2>&1 &
  # fi

  # Re-embed orgs whose mission was (re)written so semantic search stays current.
  # The watchdog runs its own embed server on :11436 (separate from the mission
  # model on :11437) and re-embeds once enough missions are stale, then idles.
  if pgrep -f "scripts/enrichment/embeddings/reembed_watchdog.py" >/dev/null; then
    echo "[$(ts)] start: reembed_watchdog already running — skipping"
  else
    echo "[$(ts)] start: launching reembed_watchdog (re-embeds stale/new missions)"
    nohup "$BASE/venv/bin/python3" "$BASE/scripts/enrichment/embeddings/reembed_watchdog.py" \
      --threshold 5000 --interval 1800 >> "$LOG_DIR/reembed_watchdog.log" 2>&1 &
  fi
  echo "[$(ts)] start: done"
}

start_exclusive() {
  echo "[$(ts)] start_exclusive: launching embed_server only (mission-gen/reembed paused for backlog clear)"
  bash "$BASE/scripts/ops/embed_server.sh" start

  if pgrep -f "llama-server.*--port ${PORT}" >/dev/null; then
    echo "[$(ts)] start_exclusive: llama-server already running — skipping"
  else
    echo "[$(ts)] start_exclusive: launching llama-server $(basename "$MODEL")"
    nohup "$SERVER_BIN" -m "$MODEL" --device Vulkan1 -ngl 99 -fa 1 \
      --parallel 6 --ctx-size 24576 --cont-batching \
      --port "$PORT" --host 127.0.0.1 --jinja \
      > "$SERVER_LOG" 2>&1 &
    for _ in $(seq 1 60); do
      grep -q "server is listening\|all slots are idle" "$SERVER_LOG" 2>/dev/null && break
      sleep 3
    done
  fi
  echo "[$(ts)] start_exclusive: done — mission-gen and reembed_watchdog intentionally NOT launched"
}

stop() {
  echo "[$(ts)] stop: halting cpu_night donate-link loop"
  pkill -f "scripts/cpu_night.sh" 2>/dev/null
  pkill -f "scripts/donation_link_pipeline.py" 2>/dev/null
  echo "[$(ts)] stop: halting web_night discovery loop"
  pkill -f "scripts/web_night.sh" 2>/dev/null
  pkill -f "scripts/web_finder_agent.py" 2>/dev/null
  echo "[$(ts)] stop: halting mission generation"
  pkill -f "scripts/generate_missions" 2>/dev/null
  # echo "[$(ts)] stop: halting LLM cause-tag enrichment"
  # pkill -f "scripts/enrich_cause_tags_llm.py" 2>/dev/null
  sleep 2
  echo "[$(ts)] stop: halting reembed_watchdog"
  pkill -f "scripts/enrichment/embeddings/reembed_watchdog.py" 2>/dev/null
  echo "[$(ts)] stop: halting llama-server (mission generation)"
  # by port, not model basename — if MODEL was edited since start, the
  # basename match would miss the running server and leave the GPU busy
  pkill -f "llama-server.*--port ${PORT}" 2>/dev/null
  sleep 2
  # belt-and-suspenders: free the mission port
  fuser -k "${PORT}/tcp" 2>/dev/null
  # NOTE: embed_server (port 11436) is kept running until web_finder completes.
  # See stop_embed_server() cron job (runs at 09:05).

  # Rebuild FTS index so missions written overnight are immediately searchable.
  # Runs after workers are killed so there are no competing DB writes.
  echo "[$(ts)] stop: rebuilding FTS index (new missions from tonight)"
  source "$BASE/venv/bin/activate"
  cd "$BASE" || exit 1
  python3 scripts/search/build_fts_index.py --rebuild >> "$LOG_DIR/gpu_night.log" 2>&1 \
    && echo "[$(ts)] stop: FTS rebuild complete" \
    || echo "[$(ts)] stop: FTS rebuild FAILED — check logs"

  echo "[$(ts)] stop: done (GPU freed, embed_server still running for web_finder)"
}

# Poka-yoke: the founder can lift the night-only GPU rule for a stated window
# (e.g. away from home, heat is not a concern). Before this guard existed the
# 09:05 cron stopped the embed server anyway and nothing restarted it, so live
# search lost query embedding silently — that happened on 2026-07-25.
#
# Hold the window open with an expiry timestamp, so a forgotten override cannot
# disable the heat protection permanently:
#   date -d '+36 hours' +%s > ~/meritgiving/.gpu_override_until
GPU_OVERRIDE_FILE="$BASE/.gpu_override_until"

gpu_override_active() {
  [ -f "$GPU_OVERRIDE_FILE" ] || return 1
  local until_ts
  until_ts=$(tr -cd '0-9' < "$GPU_OVERRIDE_FILE")
  [ -n "$until_ts" ] || return 1
  [ "$(date +%s)" -lt "$until_ts" ]
}

stop_embed_server() {
  if gpu_override_active; then
    echo "[$(ts)] stop_embed_server: SKIPPED — GPU override active until $(date -d "@$(tr -cd '0-9' < "$GPU_OVERRIDE_FILE")" '+%Y-%m-%d %H:%M')"
    return 0
  fi
  echo "[$(ts)] stop_embed_server: halting embed_server (used by Phase 4)"
  bash "$BASE/scripts/ops/embed_server.sh" stop
}

case "${1:-}" in
  start)              start ;;
  start_exclusive)    start_exclusive ;;
  stop)               stop ;;
  stop_embed_server)  stop_embed_server ;;
  *) echo "usage: $0 {start|start_exclusive|stop|stop_embed_server}" >&2; exit 1 ;;
esac
