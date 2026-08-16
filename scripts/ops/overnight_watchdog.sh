#!/bin/bash
# Autonomous overnight watchdog: monitor discovery daemon, inference servers,
# and log health metrics every 30min. Alert if anything dies.

LOGDIR="logs"
WATCHDOG_LOG="$LOGDIR/overnight_watchdog.log"
mkdir -p "$LOGDIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$WATCHDOG_LOG"
}

check_discovery() {
  if pgrep -f "discovery_daemon.py" >/dev/null; then
    echo "✓"
  else
    log "ALERT: discovery_daemon.py not running!"
    echo "✗"
  fi
}

check_embed_server() {
  if curl -s -m 3 http://127.0.0.1:11436/health >/dev/null 2>&1; then
    echo "✓"
  else
    log "ALERT: embedding server (11436) not responding!"
    echo "✗"
  fi
}

check_qwen_server() {
  if curl -s -m 3 http://127.0.0.1:11437/health >/dev/null 2>&1; then
    echo "✓"
  else
    log "ALERT: Qwen server (11437) not responding!"
    echo "✗"
  fi
}

# Run checks every 30 min indefinitely
while true; do
  log "Health check: discovery=$(check_discovery) embed=$(check_embed_server) qwen=$(check_qwen_server)"
  
  # Log system stats
  GPU0=$(rocm-smi --showuse 2>/dev/null | grep "GPU\[0\]" | awk '{print $NF}' || echo "N/A")
  LOAD=$(uptime | awk -F'load average:' '{print $2}' | xargs)
  MEM=$(free -h | awk 'NR==2 {print $3"/"$2}')
  log "Resources: GPU[0]=$GPU0%, Load=$LOAD, Memory=$MEM"
  
  sleep 1800  # 30 minutes
done
