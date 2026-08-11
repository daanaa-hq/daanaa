#!/bin/bash
# Gate 0 Daily Health Check - Run once per day

DATE=$(date "+%Y-%m-%d %H:%M")
LOGFILE="logs/gate0_daily_checks.log"

echo "[$DATE] Gate 0 Health Check" >> $LOGFILE
echo "═══════════════════════════════════════════════════════════════" >> $LOGFILE

# Check 1: API Uptime
echo "1. API Endpoints:" >> $LOGFILE
for endpoint in "/" "/api/stats" "/api/search?q=health"; do
  response=$(curl -s -o /dev/null -w "%{http_code}" https://daanaa.org$endpoint 2>/dev/null || echo "000")
  echo "   $endpoint: $response" >> $LOGFILE
done

# Check 2: Search Latency (sample 5 queries)
echo "2. Search Latency (p50):" >> $LOGFILE
total_time=0
for i in {1..5}; do
  time=$(curl -s -w "%{time_total}" -o /dev/null https://daanaa.org/api/search?q=nonprofit 2>/dev/null | cut -d. -f1)
  total_time=$((total_time + time))
done
avg=$((total_time / 5))
echo "   Avg latency: ${avg}ms (target <300ms)" >> $LOGFILE

# Check 3: Error Rate
echo "3. Recent Errors:" >> $LOGFILE
error_count=$(grep -c "ERROR\|Exception" logs/*.log 2>/dev/null | grep -v ":0$" | wc -l)
echo "   Error files with recent issues: $error_count" >> $LOGFILE

# Check 4: Daemon Health
echo "4. Discovery Daemon:" >> $LOGFILE
if pgrep -f "discovery_daemon" > /dev/null; then
  echo "   Status: Running ✅" >> $LOGFILE
else
  echo "   Status: Not running ⚠️" >> $LOGFILE
fi

# Check 5: Disk Space
echo "5. System Resources:" >> $LOGFILE
disk_used=$(df /home/akbar | tail -1 | awk '{print $5}')
echo "   Disk: $disk_used used" >> $LOGFILE

echo "" >> $LOGFILE

# Print summary to console
echo "Gate 0 Daily Check Complete - Log: $LOGFILE"
tail -15 $LOGFILE | grep -v "^═"

