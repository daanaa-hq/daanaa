#!/bin/bash
# Quick Gate 0 health check

echo "═══════════════════════════════════════════════════════════════════"
echo "Gate 0: Operational Stability Check"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

echo "API Health:"
curl -s https://daanaa.org/health | head -20
echo ""

echo "Search Latency Sample (10 queries):"
for i in {1..10}; do
  curl -s -w "Query $i: %{time_total}s\n" -o /dev/null https://daanaa.org/api/search?q=health
done
echo ""

echo "Daemon Status:"
tail -5 logs/discovery_daemon.log 2>/dev/null || echo "(No daemon logs yet)"
echo ""

echo "System Health:"
df -h /home/akbar | tail -1 | awk '{print "Disk: " $3 " used, " $4 " free (" $5 ")"}'
echo ""

