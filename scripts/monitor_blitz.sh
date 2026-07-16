#!/bin/bash

# Real-time discovery blitz monitor
# Shows progress, throughput, and eta to completion

DB="/home/akbar/meritgiving/data/merit_registry.db"
LOG="/home/akbar/meritgiving/logs/discovery_daemon_blitz.log"

clear

while true; do
  clear
  echo "╔════════════════════════════════════════════════════════════╗"
  echo "║        DAANAA DISCOVERY BLITZ — 12 HOUR OPTIMIZATION       ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo ""

  # Timestamp
  echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""

  # Instance status
  echo "━ INSTANCES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  ps aux | grep discovery_daemon.py | grep -v grep | wc -l | xargs echo "Active daemons:"
  echo ""

  # Link counts
  echo "━ LINK INVENTORY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  TOTAL_WITH_LINKS=$(sqlite3 $DB "SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL OR volunteer_url IS NOT NULL;")
  REMAINING=$(sqlite3 $DB "SELECT COUNT(*) FROM registry_enriched WHERE website IS NOT NULL AND website != '' AND (donate_url IS NULL OR volunteer_url IS NULL);")

  echo "With discovery links:    $TOTAL_WITH_LINKS orgs"
  echo "Still needing discovery: $REMAINING orgs"
  echo ""

  # Recent activity
  echo "━ RECENT ACTIVITY (Last 30s) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  RECENT_SUCCESS=$(tail -500 $LOG 2>/dev/null | grep -c "✅")
  RECENT_ERRORS=$(tail -500 $LOG 2>/dev/null | grep -c "❌")

  echo "Successfully verified:   $RECENT_SUCCESS orgs"
  echo "Failed/skipped:          $RECENT_ERRORS orgs"

  if [ "$RECENT_SUCCESS" -gt 0 ]; then
    AVG_LINKS_PER_ORG=$(sqlite3 $DB "SELECT CAST(COUNT(*) AS FLOAT) / (SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL OR volunteer_url IS NOT NULL) FROM registry_enriched WHERE donate_url IS NOT NULL OR volunteer_url IS NOT NULL;" 2>/dev/null)
    echo "Avg links per org:       ${AVG_LINKS_PER_ORG} (2-3 is typical)"
  fi
  echo ""

  # Progress estimate
  if [ "$REMAINING" -gt 0 ] && [ "$RECENT_SUCCESS" -gt 0 ]; then
    echo "━ PROGRESS ESTIMATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Assuming ~50 orgs/30s per instance = 200 orgs/30s total from 4 instances
    RATE=$(echo "scale=1; $RECENT_SUCCESS / 30" | bc 2>/dev/null || echo "6.7")
    HOURS_TO_COMPLETE=$(echo "scale=1; $REMAINING / ($RATE * 120)" | bc 2>/dev/null || echo "?")

    echo "Processing rate:         ~$RATE orgs/sec (4 instances)"
    echo "Time to clear backlog:   ~$HOURS_TO_COMPLETE hours"
    echo ""
  fi

  # Current operations
  echo "━ CURRENT OPERATIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  tail -20 $LOG 2>/dev/null | grep -E "Iteration|Progress" | tail -1
  echo ""

  # Latest discoveries
  echo "━ LATEST DISCOVERIES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  tail -30 $LOG 2>/dev/null | grep "✅" | tail -5 | sed 's/.*✅ /  ✓ /' | sed 's/: .*//'
  echo ""

  echo "Press Ctrl+C to exit. Refreshing every 10 seconds..."
  sleep 10
done
