#!/bin/bash
# Monitor for database corruption spread

DB="/home/akbar/meritgiving/data/merit_registry.db"
LOG="/home/akbar/meritgiving/logs/db_corruption_monitor.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running corruption check..." >> "$LOG"

# Quick integrity check (30 second timeout)
RESULT=$(timeout 30 sqlite3 "$DB" "PRAGMA quick_check;" 2>&1)

if [[ "$RESULT" == "ok" ]]; then
    echo "✅ No new corruption detected" >> "$LOG"
else
    echo "⚠️  WARNING: Corruption found or check timed out" >> "$LOG"
    echo "$RESULT" | head -5 >> "$LOG"
fi

# Test basic query functionality
QUERY_TEST=$(timeout 10 sqlite3 "$DB" "SELECT COUNT(*) FROM registry_enriched WHERE org_status='active';" 2>&1)
if [[ "$QUERY_TEST" =~ ^[0-9]+$ ]]; then
    echo "✅ Core queries working ($QUERY_TEST orgs)" >> "$LOG"
else
    echo "❌ ALERT: Core query failed: $QUERY_TEST" >> "$LOG"
fi
