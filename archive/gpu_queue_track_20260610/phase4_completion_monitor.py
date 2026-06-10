#!/usr/bin/env python3
"""
scripts/phase4_completion_monitor.py

Monitor Phase 4 progress and auto-queue next GPU work when Phase 4 completes.

This script:
1. Checks Phase 4A and 4B log files
2. Determines if Phase 4 is complete
3. If complete, automatically adds mission generation to GPU queue
4. Can be run hourly via cron to check progress

Usage:
    python3 scripts/phase4_completion_monitor.py
    python3 scripts/phase4_completion_monitor.py --force-check
    python3 scripts/phase4_completion_monitor.py --check-status
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import re

LOGS_DIR = Path.home() / "meritgiving" / "logs"
CHECKPOINT_FILE = Path.home() / "meritgiving" / ".phase4_monitor_checkpoint"
SCRIPT_DIR = Path.home() / "meritgiving" / "scripts"

def check_phase4_status():
    """Check if Phase 4A and 4B are complete."""
    phase4a_log = LOGS_DIR / "web_finder_50k.log"
    phase4b_log = LOGS_DIR / "web_finder_25k.log"

    status = {
        'phase4a_exists': phase4a_log.exists(),
        'phase4b_exists': phase4b_log.exists(),
        'phase4a_complete': False,
        'phase4b_complete': False,
        'phase4a_progress': '0%',
        'phase4b_progress': '0%',
        'last_update': None,
    }

    # Check Phase 4A
    if phase4a_log.exists():
        content = phase4a_log.read_text()
        # Look for completion markers
        if 'Complete' in content or 'COMPLETE' in content or '100%' in content:
            status['phase4a_complete'] = True
        # Extract progress
        matches = re.findall(r'(\d+)/50000', content)
        if matches:
            last_match = matches[-1]
            pct = int(last_match) / 50000 * 100
            status['phase4a_progress'] = f"{pct:.1f}%"
        status['phase4a_mtime'] = phase4a_log.stat().st_mtime

    # Check Phase 4B
    if phase4b_log.exists():
        content = phase4b_log.read_text()
        if 'Complete' in content or 'COMPLETE' in content or '100%' in content:
            status['phase4b_complete'] = True
        matches = re.findall(r'(\d+)/25000', content)
        if matches:
            last_match = matches[-1]
            pct = int(last_match) / 25000 * 100
            status['phase4b_progress'] = f"{pct:.1f}%"
        status['phase4b_mtime'] = phase4b_log.stat().st_mtime

    return status

def load_checkpoint():
    """Load last checkpoint state."""
    if CHECKPOINT_FILE.exists():
        lines = CHECKPOINT_FILE.read_text().strip().split('\n')
        return {
            'state': lines[0] if lines else None,
            'timestamp': float(lines[1]) if len(lines) > 1 else None,
        }
    return {'state': None, 'timestamp': None}

def save_checkpoint(state):
    """Save checkpoint."""
    CHECKPOINT_FILE.write_text(f"{state}\n{time.time()}\n")

def queue_mission_generation():
    """Add mission generation to GPU queue."""
    print("  ✓ Enabling mission generation in GPU queue...")

    # Use the gpu_queue_manager to enable mission generation
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "gpu_queue_manager.py"),
         "--enable-task=Mission Generation"],
        capture_output=True
    )

    if result.returncode == 0:
        print("  ✓ Mission generation queued")
        save_checkpoint('phase4_complete_mission_queued')
        return True
    else:
        print(f"  ✗ Failed to queue mission generation: {result.stderr.decode()}")
        return False

def show_status(status):
    """Display Phase 4 status."""
    print(f"""
╔════════════════════════════════════════════════════════════╗
║              PHASE 4 COMPLETION MONITOR                     ║
╚════════════════════════════════════════════════════════════╝

Check time:          {time.strftime('%Y-%m-%d %H:%M:%S')}

PHASE 4A (50K websites):
  Log file:          {LOGS_DIR / 'web_finder_50k.log'}
  Status:            {'✓ COMPLETE' if status['phase4a_complete'] else '⏳ IN PROGRESS'}
  Progress:          {status['phase4a_progress']}

PHASE 4B (25K websites):
  Log file:          {LOGS_DIR / 'web_finder_25k.log'}
  Status:            {'✓ COMPLETE' if status['phase4b_complete'] else ('⏳ IN PROGRESS' if status['phase4b_exists'] else '⏸ NOT STARTED')}
  Progress:          {status['phase4b_progress']}

OVERALL:
  Status:            {'✓ ALL COMPLETE' if (status['phase4a_complete'] and status['phase4b_complete']) else ('⏳ RUNNING' if (status['phase4a_exists'] or status['phase4b_exists']) else '⏸ NOT STARTED')}
""")

def main():
    parser = __import__('argparse').ArgumentParser(
        description='Phase 4 completion monitor'
    )
    parser.add_argument('--check-status', action='store_true', help='Show Phase 4 status only')
    parser.add_argument('--force-check', action='store_true', help='Ignore checkpoint, always check')
    args = parser.parse_args()

    status = check_phase4_status()
    checkpoint = load_checkpoint()

    if args.check_status:
        show_status(status)
        return

    # Show status
    show_status(status)

    # Check if Phase 4 is complete
    phase4_complete = status['phase4a_complete'] and status['phase4b_complete']

    if not phase4_complete:
        print("\n⏳ Phase 4 still running. Check again later.\n")
        return

    # Phase 4 is complete
    print("\n✓ Phase 4 complete! Checking if mission generation should start...\n")

    # Don't re-queue if already done
    if not args.force_check and checkpoint['state'] == 'phase4_complete_mission_queued':
        print("  ✓ Mission generation already queued (from previous check)")
        print("  → Check GPU queue with: python3 scripts/gpu_queue_manager.py --check\n")
        return

    # Queue mission generation
    if queue_mission_generation():
        print("""
  ✓ Mission generation is now in GPU queue!

Next steps:
  1. Monitor queue: python3 scripts/gpu_queue_manager.py --check
  2. Run manually:  python3 scripts/gpu_queue_manager.py --run
  3. Or wait for next cron cycle to auto-run

GPU queue will automatically start mission generation when ready.
""")
    else:
        print("  ✗ Failed to queue mission generation\n")

if __name__ == '__main__':
    main()
