#!/bin/bash
# Monitor domain guessing engine progress
# Usage: ./scripts/monitor_domain_guess.sh

LOG_FILE="logs/domain_guess_production_run.log"
INTERVAL=30  # Check every 30 seconds

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    exit 1
fi

echo "🔍 Monitoring Domain Guessing Engine"
echo "Press Ctrl+C to stop"
echo "=================================="

while true; do
    clear
    echo "🔍 Domain Guessing Engine — Progress Monitor"
    echo "=================================="
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Check if process is running
    if pgrep -f "domain_guess_engine.py" > /dev/null; then
        echo "✅ Process running"
        ps aux | grep "domain_guess_engine.py" | grep -v grep | awk '{print "   CPU: "$3"% | Memory: "$6"K"}'
    else
        echo "⚠️  Process stopped"
    fi

    echo ""

    # Extract latest stats
    if [ -f "$LOG_FILE" ]; then
        # Get found count
        FOUND=$(grep "✅ FOUND:" "$LOG_FILE" | wc -l)
        CHECKED=$(grep "DOMAIN GUESSING ENGINE RESULTS" "$LOG_FILE" | wc -l)

        # Get last 5 successful findings
        echo "📊 Recent Findings:"
        grep "✅ FOUND:" "$LOG_FILE" | tail -5 | sed 's/^/   /'

        echo ""
        echo "📈 Stats:"
        echo "   Found domains: $FOUND"
        echo "   Completion cycles: $CHECKED"

        # Get latest log lines
        echo ""
        echo "📝 Latest Activity:"
        tail -3 "$LOG_FILE" | sed 's/^/   /'
    fi

    echo ""
    echo "=================================="
    sleep $INTERVAL
done
