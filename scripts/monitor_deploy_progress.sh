#!/bin/bash
# Real-time deployment progress monitor

TOTAL_ORGS=$(sqlite3 -readonly data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE org_status = 'active';")
VERIFIED_BOTH=$(sqlite3 -readonly data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE org_status = 'active' AND donate_url IS NOT NULL AND volunteer_url IS NOT NULL;")

while true; do
  clear
  echo "════════════════════════════════════════════════════════════"
  echo "DEPLOYMENT & DISCOVERY PROGRESS — $(date '+%H:%M:%S')"
  echo "════════════════════════════════════════════════════════════"
  echo ""
  
  # Deployment status
  echo "DEPLOYMENT STATUS:"
  if pgrep -f "precompute_orgs.py" >/dev/null; then
    PS_INFO=$(ps aux | grep precompute_orgs.py | grep -v grep)
    CPU=$(echo "$PS_INFO" | awk '{print $3}')
    MEM=$(echo "$PS_INFO" | awk '{print int($6/1024)"MB"}')
    echo "  ⚙️  Precomputing org files: CPU=$CPU%, Memory=$MEM"
    echo "  Est. completion: 08:25 AM"
  elif pgrep -f "build_fts_index" >/dev/null; then
    echo "  🔍 Building search index..."
  elif pgrep -f "safe_deploy" >/dev/null; then
    echo "  🚀 Deploying to droplet..."
  else
    echo "  ✅ Deployment complete!"
  fi
  echo ""
  
  # Discovery status
  VERIFIED_NOW=$(sqlite3 -readonly data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE org_status = 'active' AND donate_url IS NOT NULL AND volunteer_url IS NOT NULL;")
  NEWLY_VERIFIED=$((VERIFIED_NOW - VERIFIED_BOTH))
  VERIFIED_BOTH=$VERIFIED_NOW
  
  echo "DISCOVERY PROGRESS:"
  echo "  ✅ Orgs with both donate+volunteer links: $VERIFIED_NOW / $TOTAL_ORGS"
  echo "  📊 Discovered this session: $NEWLY_VERIFIED"
  echo "  🔄 Discovery daemon: $(ps aux | grep 'discovery_daemon.py' | grep -v grep >/dev/null && echo 'running' || echo 'stopped')"
  echo ""
  
  # System health
  echo "SYSTEM HEALTH:"
  LOAD=$(uptime | awk -F'load average:' '{print $2}')
  MEM_FREE=$(free -h | awk 'NR==2 {print $4}')
  GPU=$(rocm-smi --showuse 2>/dev/null | grep "GPU\[0\]" | awk '{print $NF}')
  echo "  Load: $LOAD | Memory free: $MEM_FREE | GPU[0]: ${GPU}%"
  echo ""
  
  if ! pgrep -f "safe_deploy|precompute_orgs" >/dev/null; then
    echo "════════════════════════════════════════════════════════════"
    echo "✅ DEPLOYMENT COMPLETE"
    echo "════════════════════════════════════════════════════════════"
    break
  fi
  
  sleep 30
done
