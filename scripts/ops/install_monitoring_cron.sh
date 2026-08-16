#!/bin/bash
# Install monitoring as automated cron jobs
# Run this once to set up background monitoring
#
# Usage: bash scripts/install_monitoring_cron.sh
#
# This creates cron entries for:
#   • Service health checks (hourly)
#   • Pre-flight checks (before enrichment, 7:50pm)
#   • Dashboard snapshots (daily, 8:30pm after enrichment)
#   • Efficiency metrics (daily, 8:30pm after enrichment)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CRON_DIR="/etc/cron.d"
CRON_FILE="daanaa-enrichment-monitoring"

echo "📋 Setting up enrichment monitoring cron jobs"
echo "Repository root: $REPO_ROOT"
echo ""

# Check if we can write to /etc/cron.d (requires sudo)
if [ ! -w "$CRON_DIR" ]; then
    echo "⚠️  /etc/cron.d is not writable (need sudo)"
    echo ""
    echo "Installing to ~/cron instead (manual installation needed)"
    CRON_DIR="$HOME/cron"
    mkdir -p "$CRON_DIR"
fi

# Create cron jobs
cat > "${CRON_DIR}/${CRON_FILE}" << 'CRON'
# Daanaa Enrichment Monitoring — Automated Health Checks
# Prevents silent failures, tracks progress, validates data quality

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Service health check (every hour)
# Logs failures to logs/service_health.jsonl for alerting
0 * * * * cd /home/akbar/meritgiving && python3 scripts/service_health_check.py --alert >> logs/cron_service_health.log 2>&1

# Enrichment pre-flight checks (7:50pm, 10 min before enrichment)
# Exits 1 if infrastructure is not ready; prevents silent failures
50 19 * * * cd /home/akbar/meritgiving && python3 scripts/enrichment_preflight.py --strict >> logs/cron_preflight.log 2>&1

# Dashboard snapshot (8:30pm, after enrichment completes)
# Captures progress metrics for visibility
30 20 * * * cd /home/akbar/meritgiving && python3 scripts/enrichment_dashboard.py --hourly >> logs/cron_dashboard.log 2>&1

# Efficiency metrics log (8:30pm, after enrichment completes)
# Tracks coverage growth (websites, missions, donation links)
30 20 * * * cd /home/akbar/meritgiving && python3 scripts/enrichment_efficiency.py --log-run >> logs/cron_efficiency.log 2>&1

# Archive recovery monitoring (every 30min while daemon is running)
# Polls for daemon completion, generates impact report
*/30 * * * * cd /home/akbar/meritgiving && bash scripts/archive_monitor.sh >> logs/cron_archive_monitor.log 2>&1
CRON

echo "✅ Cron jobs installed to: ${CRON_DIR}/${CRON_FILE}"
echo ""
echo "📅 Schedule:"
echo "   • Hourly:     Service health check (catch failures immediately)"
echo "   • 7:50pm:     Pre-flight checks (verify infra before enrichment)"
echo "   • 8:30pm:     Dashboard + efficiency logs (after enrichment)"
echo "   • Every 30min: Archive recovery monitoring (while daemon runs)"
echo ""
echo "📍 Log locations:"
echo "   • Service health: logs/cron_service_health.log (failures only)"
echo "   • Pre-flight:     logs/cron_preflight.log (readiness checks)"
echo "   • Dashboard:      logs/cron_dashboard.log (progress snapshots)"
echo "   • Efficiency:     logs/cron_efficiency.log + logs/enrichment_metrics/"
echo "   • Archive:        logs/cron_archive_monitor.log"
echo ""

# Install to system cron if we have permissions
if [ "$CRON_DIR" = "/etc/cron.d" ]; then
    echo "✅ System cron installation complete"
    echo ""
    echo "Verify installation:"
    echo "  sudo cat /etc/cron.d/${CRON_FILE}"
    echo ""
else
    echo "⚠️  Installed to home directory (requires manual activation)"
    echo ""
    echo "To enable system-wide monitoring, run:"
    echo "  sudo cp ${CRON_DIR}/${CRON_FILE} /etc/cron.d/"
    echo ""
    echo "Or, to activate just for this user, add to your crontab:"
    echo "  crontab -e"
    echo "  # Then add:"
    echo "  # @hourly cd /home/akbar/meritgiving && python3 scripts/service_health_check.py --alert >> logs/cron_service_health.log 2>&1"
    echo "  # [etc for other jobs]"
fi

echo ""
echo "🧪 Test installation (manual pre-flight check):"
echo "  cd $REPO_ROOT"
echo "  python3 scripts/service_health_check.py"
echo "  python3 scripts/enrichment_preflight.py --strict"
echo "  python3 scripts/enrichment_dashboard.py --hourly"
echo ""
