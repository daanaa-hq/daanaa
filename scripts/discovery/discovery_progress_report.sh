#!/bin/bash
# Discovery pipeline daily progress report
# Runs at 06:00, 12:00, 18:00, 00:00

DB="/home/akbar/meritgiving/data/merit_registry.db"

echo "=========================================="
echo "Discovery Pipeline Status — $(date)"
echo "=========================================="

echo ""
echo "PHASE 1 (Website-based discovery)"
sqlite3 "$DB" "SELECT 'Discovered & queued', COUNT(*) FROM link_deployment_queue WHERE deployed_at IS NULL UNION ALL SELECT 'Already deployed', COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL;" 2>/dev/null

echo ""
echo "ORGS STATUS"
sqlite3 "$DB" "SELECT 'Missing donation link', COUNT(*) FROM registry_enriched WHERE donate_url IS NULL AND EIN > 0;" 2>/dev/null

echo ""
echo "DEPLOYMENT QUEUE"
sqlite3 "$DB" "SELECT status, COUNT(*) FROM link_deployment_queue GROUP BY status ORDER BY COUNT(*) DESC;" 2>/dev/null

echo ""
echo "DAEMON HEALTH"
if pgrep -f "python3 scripts/discovery_daemon.py" > /dev/null; then
    PID=$(pgrep -f "python3 scripts/discovery_daemon.py")
    RSS=$(ps aux | grep $PID | grep -v grep | awk '{print int($6/1024) "MB"}')
    echo "Status: ✅ Running (PID $PID, Memory: $RSS)"
else
    echo "Status: ❌ Not running"
fi

echo ""
echo "LAST DEPLOYMENT"
sqlite3 "$DB" "SELECT 'Deployed', COUNT(*) FROM registry_enriched WHERE donate_url LIKE 'http%' LIMIT 1;" 2>/dev/null
tail -1 /home/akbar/meritgiving/logs/deployment_cron.log 2>/dev/null | grep -o "Deployed: [0-9]*"

echo ""
echo "=========================================="
