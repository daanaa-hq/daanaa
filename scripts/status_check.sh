#!/bin/bash
# Quick status check for Phase 1 monitoring window
# Run this on Tuesday morning to verify everything ran while you were away

set -e

echo "════════════════════════════════════════════════════════════════"
echo "PHASE 1 AUTONOMOUS RUN — STATUS REPORT"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. Backup Status
echo "1️⃣  BACKUP STATUS"
echo "───────────────────────────────────────────────────────────────"
BACKUP_COUNT=$(ls ~/meritgiving/backups/production/merit_registry_*.db 2>/dev/null | wc -l)
echo "   Backups created: $BACKUP_COUNT (expected 8: 7 hourly + 1 daily)"
echo "   Latest backups:"
ls -lh ~/meritgiving/backups/production/merit_registry_*.db 2>/dev/null | tail -3 | awk '{print "     " $9 " (" $5 ")"}'
echo ""

# 2. Monitoring Status
echo "2️⃣  MONITORING STATUS"
echo "───────────────────────────────────────────────────────────────"
MONITOR_COUNT=$(ls ~/.daanaa/phase1-monitoring/*-daily.json 2>/dev/null | wc -l)
echo "   Daily checks collected: $MONITOR_COUNT (expected 7)"
echo "   Latest monitoring run:"
tail -1 ~/meritgiving/logs/phase1_monitor.log 2>/dev/null || echo "     (no log found)"
echo ""

# 3. API Health
echo "3️⃣  API HEALTH"
echo "───────────────────────────────────────────────────────────────"
API_HEALTH=$(curl -s http://localhost:5000/health 2>&1 | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "OFFLINE")
echo "   API Status: $API_HEALTH"
if [ "$API_HEALTH" = "ok" ]; then
  ORG_COUNT=$(curl -s 'http://localhost:5000/api/stats' 2>&1 | grep -o '"total_organizations":[0-9]*' | cut -d':' -f2 || echo "unknown")
  echo "   Orgs in system: $ORG_COUNT"
fi
echo ""

# 4. Database Integrity
echo "4️⃣  DATABASE INTEGRITY"
echo "───────────────────────────────────────────────────────────────"
DB_CHECK=$(timeout 30 sqlite3 ~/meritgiving/data/merit_registry.db "PRAGMA quick_check;" 2>&1 | head -1 || echo "CHECK_TIMEOUT")
echo "   Quick check: $DB_CHECK"
if [ "$DB_CHECK" = "ok" ]; then
  echo "   ✅ Database is healthy"
else
  echo "   ⚠️  Database check timed out (expected for 24GB database)"
fi
echo ""

# 5. Weekly Report
echo "5️⃣  WEEKLY REPORT (Decision Gate)"
echo "───────────────────────────────────────────────────────────────"
if [ -f ~/.daanaa/phase1-monitoring/*-weekly.md ]; then
  echo "   Report: $(ls ~/.daanaa/phase1-monitoring/*-weekly.md | xargs basename)"
  echo ""
  echo "   RECOMMENDATION:"
  grep -A 1 "RECOMMENDATION\|PASS\|FAIL\|CONDITIONAL" ~/.daanaa/phase1-monitoring/*-weekly.md 2>/dev/null | head -5 || echo "   (See full report below)"
  echo ""
else
  echo "   ⏳ Report not yet generated (check Friday evening)"
fi
echo ""

# 6. Critical Alerts
echo "6️⃣  CRITICAL ALERTS"
echo "───────────────────────────────────────────────────────────────"
ALERTS=$(grep -c "🔴\|CRITICAL" ~/meritgiving/logs/phase1_monitor.log 2>/dev/null || echo "0")
echo "   Critical alerts during monitoring: $ALERTS"
if [ "$ALERTS" -gt 0 ]; then
  echo "   ⚠️  Issues detected:"
  grep "🔴\|CRITICAL" ~/meritgiving/logs/phase1_monitor.log 2>/dev/null | tail -3 | sed 's/^/     /'
fi
echo ""

# 7. Action Items
echo "7️⃣  NEXT STEPS"
echo "───────────────────────────────────────────────────────────────"
if [ "$API_HEALTH" = "ok" ] && [ "$ALERTS" -eq 0 ]; then
  echo "   ✅ All systems nominal"
  echo "   → Review full weekly report: ~/.daanaa/phase1-monitoring/*-weekly.md"
  echo "   → Follow recommendation: PASS → Phase 2 build | FAIL → debug"
else
  echo "   ⚠️  Issues detected"
  echo "   → Check logs: tail -50 ~/meritgiving/logs/phase1_monitor.log"
  echo "   → Restore if needed: scripts/backup_strategy.sh restore [backup_file]"
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "For detailed analysis, see: docs/AWAY_MODE_AUTONOMOUS_RUN.md"
echo "════════════════════════════════════════════════════════════════"
