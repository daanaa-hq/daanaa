#!/bin/bash
# Real-time progress dashboard toward 100K donation links

while true; do
  clear
  echo "════════════════════════════════════════════════════════════════"
  echo "📊 PHASE 1 PROGRESS DASHBOARD — $(date '+%H:%M:%S on %A, %B %d')"
  echo "════════════════════════════════════════════════════════════════"
  echo ""
  
  # Get current state
  TOTAL=$(sqlite3 -readonly data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE org_status = 'active';")
  DONATE=$(sqlite3 -readonly data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL AND donate_url != '';")
  BOTH=$(sqlite3 -readonly data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL AND donate_url != '' AND volunteer_url IS NOT NULL AND volunteer_url != '';")
  
  TARGET=100000
  PROGRESS=$((DONATE * 100 / TARGET))
  
  # Progress bar
  BAR_WIDTH=50
  FILLED=$((PROGRESS * BAR_WIDTH / 100))
  BAR=$(printf "%-${FILLED}s" | tr ' ' '█')
  EMPTY=$(printf "%-$((BAR_WIDTH - FILLED))s" | tr ' ' '░')
  
  echo "DONATION LINK COVERAGE"
  echo "[$BAR$EMPTY] $PROGRESS% ($DONATE / $TARGET)"
  echo ""
  
  # Breakdown
  echo "COMPLETENESS"
  DONATE_PCT=$((DONATE * 100 / TOTAL))
  BOTH_PCT=$((BOTH * 100 / TOTAL))
  echo "  • $DONATE orgs with donate link ($DONATE_PCT% of $TOTAL)"
  echo "  • $BOTH orgs with both donate + volunteer ($BOTH_PCT% of $TOTAL)"
  echo ""
  
  # Velocity
  echo "DISCOVERY ACTIVITY"
  RECENT=$(tail -20 logs/discovery_daemon.log 2>/dev/null | grep -c "✅")
  echo "  • Last 20 log entries: $RECENT successful discoveries"
  tail -3 logs/discovery_daemon.log 2>/dev/null | grep "✅\|❌" | awk '{print "  " $0}'
  echo ""
  
  # Milestones
  echo "DEPLOYMENT MILESTONES"
  echo "  Next: 25K (reach at +$((25000 - DONATE)) more links)"
  echo "  Then: 30K, 35K, 40K... 100K"
  if [ -f logs/milestone_deploys.log ]; then
    echo "  Last deploy: $(tail -1 logs/milestone_deploys.log 2>/dev/null)"
  fi
  echo ""
  
  # System health
  echo "SYSTEM HEALTH"
  LOAD=$(uptime | awk -F'load average:' '{print $2}')
  MEM=$(free -h | awk 'NR==2 {print $3 "/" $2}')
  GPU=$(rocm-smi --showuse 2>/dev/null | grep "GPU\[0\]" | awk '{print $NF}')
  echo "  • Load: $LOAD"
  echo "  • Memory: $MEM"
  echo "  • GPU[0]: ${GPU}%"
  echo ""
  
  echo "════════════════════════════════════════════════════════════════"
  echo "Target: 100K links by 2026-07-24 (6 days)"
  echo "Current velocity: ~11.4K/day needed"
  echo "════════════════════════════════════════════════════════════════"
  echo ""
  echo "Press Ctrl+C to exit. Refreshes every 30 seconds."
  sleep 30
done
