#!/usr/bin/env python3
"""
Migrate all watchdog scripts from log-parsing anti-pattern to daemon_health_lib.py.

Root cause: Watchdog scripts use grep + hardcoded log format to detect health.
When log format changes or daemon internals drift, watchdog silently fails to detect problems.

Solution: Each daemon publishes its own authoritative state (via daemon_health_lib.py);
watchdog scripts read that state using pure decision logic (never grep, never hardcode).

This script generates migrated versions of all watchdog scripts.
Run ONCE: python3 watchdog_scripts_migration.py --apply
Then test locally BEFORE deploying.
"""

import subprocess
from pathlib import Path
import sys


def generate_migrated_watchdog_discovery():
    """
    Generate watchdog_discovery.sh → uses daemon_health_lib.py
    instead of grepping "discovered" from logs.
    """
    return '''#!/bin/bash
# Watchdog for discovery daemon (migrated to daemon_health_lib.py 2026-08-10)
# No longer greps log text; reads daemon's published state instead.

HEALTH_FILE="/tmp/discovery_daemon.health.json"
PID_FILE="/tmp/discovery_daemon.pid"
STARTUP_GRACE_PERIOD=30

# If health file is missing/stale, assume something is wrong
if [ ! -f "$HEALTH_FILE" ]; then
    echo "[$(date)] No health file; daemon may have crashed"
    # Read actual PID, kill if stale process
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null; then
            echo "[$(date)] Killing stale process $OLD_PID"
            kill -9 "$OLD_PID" 2>/dev/null || true
        fi
    fi
    exit 1
fi

# Parse health state (JSON)
STATUS=$(jq -r '.status // "unknown"' "$HEALTH_FILE" 2>/dev/null)
LAST_RUN=$(jq -r '.last_updated_at // ""' "$HEALTH_FILE" 2>/dev/null)

# If status is "failed", restart immediately
if [ "$STATUS" = "failed" ]; then
    echo "[$(date)] Status=failed; restarting daemon"
    exit 1
fi

# If last_run is >15 min old, daemon is stuck
if [ -n "$LAST_RUN" ]; then
    LAST_RUN_EPOCH=$(date -d "$LAST_RUN" +%s 2>/dev/null || echo 0)
    NOW_EPOCH=$(date +%s)
    AGE=$((NOW_EPOCH - LAST_RUN_EPOCH))

    if [ "$AGE" -gt 900 ]; then  # 900s = 15 min
        echo "[$(date)] Last run was $AGE seconds ago (>900s); daemon stuck"
        exit 1
    fi
fi

# If we get here, daemon is healthy
echo "[$(date)] Discovery daemon healthy (status=$STATUS, age=${AGE:-startup}s)"
exit 0
'''


def generate_migrated_watchdog_llama():
    """
    Generate watchdog_llama.sh → uses daemon_health_lib.py
    instead of checking port directly.
    """
    return '''#!/bin/bash
# Watchdog for llama inference server (migrated to daemon_health_lib.py 2026-08-10)

PORT=${1:-11437}
HEALTH_FILE="/tmp/llama_server.health.json"
TIMEOUT=2

# Step 1: Check published health state
if [ -f "$HEALTH_FILE" ]; then
    STATUS=$(jq -r '.status // "unknown"' "$HEALTH_FILE" 2>/dev/null)
    LAST_RUN=$(jq -r '.last_updated_at // ""' "$HEALTH_FILE" 2>/dev/null)

    if [ "$STATUS" = "failed" ]; then
        echo "[$(date)] Status=failed in health file"
        exit 1
    fi

    if [ -n "$LAST_RUN" ]; then
        LAST_RUN_EPOCH=$(date -d "$LAST_RUN" +%s 2>/dev/null || echo 0)
        NOW_EPOCH=$(date +%s)
        AGE=$((NOW_EPOCH - LAST_RUN_EPOCH))

        if [ "$AGE" -gt 900 ]; then
            echo "[$(date)] Llama health file stale ($AGE seconds)"
            exit 1
        fi
    fi

    echo "[$(date)] Llama server healthy (status=$STATUS)"
    exit 0
fi

# Step 2: Fallback — if no health file, check port directly
if timeout "$TIMEOUT" bash -c "echo > /dev/tcp/localhost/$PORT" 2>/dev/null; then
    echo "[$(date)] Llama server port $PORT is open"
    exit 0
else
    echo "[$(date)] Llama server port $PORT is closed"
    exit 1
fi
'''


def generate_migrated_watchdog_api():
    """
    Generate api_watchdog.sh → uses daemon_health_lib.py
    """
    return '''#!/bin/bash
# Watchdog for API daemon (migrated to daemon_health_lib.py 2026-08-10)

HEALTH_FILE="/tmp/droplet_api.health.json"
PORT=5000

# Step 1: Check published health state
if [ -f "$HEALTH_FILE" ]; then
    STATUS=$(jq -r '.status // "unknown"' "$HEALTH_FILE" 2>/dev/null)

    if [ "$STATUS" = "failed" ]; then
        echo "[$(date)] API status=failed"
        exit 1
    fi

    echo "[$(date)] API daemon healthy (status=$STATUS)"
    exit 0
fi

# Step 2: Fallback — HTTP GET to /health endpoint
TIMEOUT=2
if timeout "$TIMEOUT" curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
    echo "[$(date)] API /health endpoint responding"
    exit 0
else
    echo "[$(date)] API /health endpoint not responding"
    exit 1
fi
'''


def generate_pre_commit_hook():
    """
    Generate .git/hooks/pre-commit to catch issues before they deploy.
    """
    return '''#!/bin/bash
# Pre-commit hook: catch operational risks before they reach production

set -e

echo "🔍 Pre-commit checks..."

# 1. Python syntax validation
echo "  Checking Python imports..."
for py_file in scripts/*.py; do
    if [ -f "$py_file" ]; then
        python3 -m py_compile "$py_file" || {
            echo "❌ Syntax error in $py_file"
            exit 1
        }
    fi
done

# 2. Anti-pattern detection
echo "  Scanning for anti-patterns..."

# Grep for hardcoded timeouts (600, 3600) without context
if grep -r "sleep 600\\|sleep 3600\\|timeout 600\\|timeout 3600" scripts/ --include="*.py" | grep -v "def\\|#"; then
    echo "⚠️  Warning: hardcoded timeouts found (review for flexibility)"
fi

# Grep for hardcoded log format parsing
if grep -r "discovered\\|batch_size" scripts/*.sh | grep grep; then
    echo "⚠️  Warning: log parsing found (use daemon_health_lib instead)"
fi

# 3. Config validation
echo "  Checking configuration..."
if ! grep -q "DAANAA_ADMIN_KEY\\|DAANAA_PROD" .env.local 2>/dev/null; then
    if [ -f .env.local ]; then
        echo "⚠️  .env.local missing critical keys (OK if testing)"
    fi
fi

# 4. Secrets check (existing privacy_check.sh)
if [ -f privacy_check.sh ]; then
    bash privacy_check.sh || exit 1
fi

echo "✅ Pre-commit checks passed"
exit 0
'''


def apply_migrations():
    """
    Apply all watchdog migrations.
    """
    scripts_dir = Path.home() / "meritgiving" / "scripts"
    marker = Path.home() / "meritgiving" / ".daemon_health_migrated"

    if marker.exists():
        print("✅ Migration already applied (marker file exists)")
        return True

    print("\n📝 Applying watchdog migrations...\n")

    # Generate migrated watchdogs
    migrations = {
        "watchdog_discovery.sh": generate_migrated_watchdog_discovery(),
        "watchdog_llama.sh": generate_migrated_watchdog_llama(),
        "api_watchdog.sh": generate_migrated_watchdog_api(),
    }

    for filename, content in migrations.items():
        filepath = scripts_dir / filename
        print(f"  Writing {filename}...")
        filepath.write_text(content)
        filepath.chmod(0o755)

    # Generate pre-commit hook
    git_hooks_dir = Path.home() / "meritgiving" / ".git" / "hooks"
    if git_hooks_dir.exists():
        pre_commit_path = git_hooks_dir / "pre-commit"
        print(f"  Writing .git/hooks/pre-commit...")
        pre_commit_path.write_text(generate_pre_commit_hook())
        pre_commit_path.chmod(0o755)
    else:
        print(f"  ⚠️  .git/hooks directory not found (may be OK if not in git repo)")

    # Create marker
    marker.write_text("Watchdog migration completed 2026-08-10\n")

    print("\n✅ Watchdog migrations applied\n")
    return True


def main():
    if "--apply" in sys.argv:
        apply_migrations()
    else:
        print("""
Watchdog Migration Script
=========================

This script migrates all watchdog scripts from the log-parsing anti-pattern
to the daemon_health_lib.py standard.

Usage:
  python3 watchdog_scripts_migration.py --apply    # Apply migrations
  python3 watchdog_scripts_migration.py --test      # Test (not yet implemented)

The log-parsing anti-pattern (grepping for "discovered", "batch_size", etc.)
silently breaks when log format changes. The daemon_health_lib pattern is
more robust: daemons publish their own state, watchdogs read published state.

Generated files:
  - watchdog_discovery.sh (updated to read /tmp/discovery_daemon.health.json)
  - watchdog_llama.sh (updated to read /tmp/llama_server.health.json)
  - api_watchdog.sh (updated to read /tmp/droplet_api.health.json)
  - .git/hooks/pre-commit (new: catches import errors + anti-patterns)

To apply: python3 watchdog_scripts_migration.py --apply
        """)


if __name__ == "__main__":
    main()
