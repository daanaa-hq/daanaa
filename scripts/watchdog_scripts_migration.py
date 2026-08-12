#!/usr/bin/env python3
"""Generate migrated watchdog scripts that use daemon_health_lib.py"""
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

def create_watchdog_script(name: str, daemon_name: str):
    """Create migrated watchdog script"""
    content = f"""#!/bin/bash
# Watchdog for {daemon_name} - reads daemon-published health state
# No grep, no hardcoded strings; pure decision logic

HEALTH_FILE="/tmp/{daemon_name}_daemon.health.json"
MAX_AGE_SECONDS=900  # 15 minutes

if [ ! -f "$HEALTH_FILE" ]; then
    echo "Health file missing, restarting {daemon_name}..."
    pkill -f {daemon_name} || true
    exit 1
fi

# Read health status
STATUS=$(jq -r '.status // "unknown"' "$HEALTH_FILE" 2>/dev/null)
AGE=$(jq -r '.age_seconds // 9999' "$HEALTH_FILE" 2>/dev/null)

# Decision logic (pure, testable)
if [ "$STATUS" = "failed" ]; then
    echo "Daemon reported failure, restarting..."
    pkill -f {daemon_name} || true
    exit 1
fi

if [ "${{AGE}}" -gt "${{MAX_AGE_SECONDS}}" ]; then
    echo "Health file stale (>15 min), daemon likely hung..."
    pkill -f {daemon_name} || true
    exit 1
fi

exit 0
"""
    script_path = BASE_DIR / "scripts" / f"{name}.sh"
    script_path.write_text(content)
    script_path.chmod(0o755)
    print(f"✅ Created {script_path}")

def main():
    print("Migrating watchdog scripts to use daemon_health_lib...")
    create_watchdog_script("watchdog_discovery", "discovery_daemon")
    create_watchdog_script("watchdog_llama", "llama_server")
    create_watchdog_script("api_watchdog", "droplet_api")
    print("✅ Watchdog migration complete")

if __name__ == "__main__":
    main()
