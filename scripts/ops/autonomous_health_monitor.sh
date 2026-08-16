#!/bin/bash
# Autonomous Health Monitor — Aug 1-6
# Runs every 30 minutes, self-heals common issues, logs everything
# Zero human intervention required

LOG_FILE="/home/akbar/meritgiving/logs/autonomous_health.log"
ALERT_FILE="/home/akbar/meritgiving/logs/autonomous_alerts.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

alert() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚨 ALERT: $1" | tee -a "$ALERT_FILE"
}

# ============================================================================
# Health Check 1: API Server Status
# ============================================================================

check_api_health() {
    HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health 2>&1)

    if [ "$HEALTH" = "200" ]; then
        log "✅ API healthy (HTTP $HEALTH)"
        return 0
    else
        alert "API not responding (HTTP $HEALTH), attempting restart..."
        pkill -9 -f gunicorn 2>/dev/null || true
        sleep 2
        cd ~/meritgiving && nohup python3 daanaa_api.py > /tmp/daanaa_api_health_check.log 2>&1 &
        sleep 3

        RETRY=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health 2>&1)
        if [ "$RETRY" = "200" ]; then
            log "✅ API restarted successfully"
            return 0
        else
            alert "API restart failed (HTTP $RETRY)"
            return 1
        fi
    fi
}

# ============================================================================
# Health Check 2: Database Integrity
# ============================================================================

check_db_health() {
    DB_PATH="$HOME/meritgiving/data/merit_registry.db"

    # Quick 10-second check
    RESULT=$(timeout 10 sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM registry_enriched;" 2>&1)

    if [[ "$RESULT" =~ ^[0-9]+$ ]]; then
        log "✅ Database healthy ($RESULT orgs)"
        return 0
    else
        alert "Database query failed: $RESULT"
        return 1
    fi
}

# ============================================================================
# Health Check 3: Backup Status
# ============================================================================

check_backup_health() {
    BACKUP_DIR="$HOME/meritgiving/backups/production"
    LATEST=$(find "$BACKUP_DIR" -name "merit_registry_*.db" -type f | head -1)

    if [ -f "$LATEST" ]; then
        SIZE=$(stat -c%s "$LATEST" 2>/dev/null || stat -f%z "$LATEST" 2>/dev/null)
        ORIGINAL_SIZE=$(stat -c%s "$HOME/meritgiving/data/merit_registry.db" 2>/dev/null || stat -f%z "$HOME/meritgiving/data/merit_registry.db" 2>/dev/null)

        # Check if size is within 5% tolerance
        TOLERANCE=$((ORIGINAL_SIZE / 20))
        if [ "$SIZE" -gt "$((ORIGINAL_SIZE - TOLERANCE))" ] && [ "$SIZE" -lt "$((ORIGINAL_SIZE + TOLERANCE))" ]; then
            log "✅ Latest backup valid ($(du -h "$LATEST" | awk '{print $1}'))"
            return 0
        else
            alert "Backup size mismatch (expected ~$(du -h "$HOME/meritgiving/data/merit_registry.db" | awk '{print $1}'), got $(du -h "$LATEST" | awk '{print $1}'))"
            return 1
        fi
    else
        alert "No backups found in $BACKUP_DIR"
        return 1
    fi
}

# ============================================================================
# Health Check 4: Discovery Daemon Status
# ============================================================================

check_discovery_daemon() {
    DAEMON_PID=$(pgrep -f "discovery_daemon.py" | head -1)

    if [ -n "$DAEMON_PID" ]; then
        MEM=$(ps -p "$DAEMON_PID" -o rss= | awk '{printf "%.0f MB", $1/1024}')
        log "✅ Discovery daemon running (PID $DAEMON_PID, $MEM)"
        return 0
    else
        alert "Discovery daemon stopped, attempting restart..."
        cd ~/meritgiving && nohup python3 scripts/discovery_daemon.py 100 > /tmp/discovery_daemon_restart.log 2>&1 &
        sleep 2

        RETRY_PID=$(pgrep -f "discovery_daemon.py" | head -1)
        if [ -n "$RETRY_PID" ]; then
            log "✅ Discovery daemon restarted (PID $RETRY_PID)"
            return 0
        else
            alert "Discovery daemon restart failed"
            return 1
        fi
    fi
}

# ============================================================================
# Health Check 5: Disk Space
# ============================================================================

check_disk_space() {
    DISK_USAGE=$(df -h ~/meritgiving | awk 'NR==2 {print $5}' | sed 's/%//')
    FREE_GB=$(df -BG ~/meritgiving | awk 'NR==2 {print $(NF-2)}' | sed 's/G//')

    if [ "$DISK_USAGE" -lt 80 ]; then
        log "✅ Disk healthy ($DISK_USAGE% used, ${FREE_GB}GB free)"
        return 0
    elif [ "$DISK_USAGE" -lt 90 ]; then
        alert "Disk space running low ($DISK_USAGE% used, ${FREE_GB}GB free)"
        return 1
    else
        alert "CRITICAL: Disk nearly full ($DISK_USAGE% used, ${FREE_GB}GB free)"
        return 1
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log "════════════════════════════════════════"
    log "Autonomous Health Check"
    log "════════════════════════════════════════"

    check_api_health
    check_db_health
    check_backup_health
    check_discovery_daemon
    check_disk_space

    log "════════════════════════════════════════"
    log "Health check complete"
    log "════════════════════════════════════════"
    log ""
}

main "$@"
