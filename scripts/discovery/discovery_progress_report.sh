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
# 2026-08-19: this used to grep for the pre-folder-migration path
# ("python3 scripts/discovery_daemon.py", missing the discovery/
# subdirectory the file actually moved into), so it always reported
# "Not running" against a real, healthy daemon -- the same
# grep-log-text-instead-of-reading-real-state anti-pattern
# DAEMON_HEALTH_STANDARD.md exists to prevent, just via a stale path
# this time instead of a stale batch-size string. Health verdict now
# comes from discovery_daemon_health.py (state-file based, matches the
# standard); pgrep is kept only for the PID/memory display, with the
# corrected path pattern.
HEALTH_JSON=$(cd /home/akbar/meritgiving && venv/bin/python3 scripts/discovery/discovery_daemon_health.py 2>/dev/null)
HEALTH_ACTION=$(echo "$HEALTH_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('action','unknown'))" 2>/dev/null)
PID=$(pgrep -f "python3 scripts/discovery/discovery_daemon.py")
if [ "$HEALTH_ACTION" = "ok" ]; then
    if [ -n "$PID" ]; then
        RSS=$(ps aux | grep $PID | grep -v grep | awk '{print int($6/1024) "MB"}')
        echo "Status: ✅ Running (PID $PID, Memory: $RSS)"
    else
        echo "Status: ✅ Healthy (state file fresh, PID not matched by display pattern)"
    fi
else
    echo "Status: ❌ ${HEALTH_ACTION:-Not running} -- $HEALTH_JSON"
fi

echo ""
echo "LAST DEPLOYMENT"
sqlite3 "$DB" "SELECT 'Deployed', COUNT(*) FROM registry_enriched WHERE donate_url LIKE 'http%' LIMIT 1;" 2>/dev/null
tail -1 /home/akbar/meritgiving/logs/deployment_cron.log 2>/dev/null | grep -o "Deployed: [0-9]*"

echo ""
echo "=========================================="
