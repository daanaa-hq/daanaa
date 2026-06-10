#!/usr/bin/env python3
"""
scripts/gpu_queue_manager.py

GPU workload queue manager.
Monitors Phase 4 completion and automatically queues next GPU work.

Queue format: json file with priority-ordered tasks
Each task specifies:
  - name: descriptive name
  - script: which script to run
  - args: command line arguments
  - priority: 1=high, 2=medium, 3=low
  - max_duration_hours: max time task can run

Workflow:
1. Phase 4A/B finish
2. Check GPU queue
3. Run next highest-priority task
4. Report when done

Usage:
    python3 scripts/gpu_queue_manager.py --check     # See current queue
    python3 scripts/gpu_queue_manager.py --run       # Run next task
    python3 scripts/gpu_queue_manager.py --add-mission-generation  # Add to queue
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
import psutil

QUEUE_FILE = Path.home() / "meritgiving" / ".gpu_queue.json"
LOGS_DIR = Path.home() / "meritgiving" / "logs"
SCRIPT_DIR = Path.home() / "meritgiving" / "scripts"

LOGS_DIR.mkdir(exist_ok=True)

DEFAULT_QUEUE = [
    {
        "name": "Mission Generation (50K template upgrade)",
        "script": "mission_generation_pipeline.py",
        "args": ["--workers=1"],
        "priority": 1,
        "max_duration_hours": 50,
        "enabled": True,
        "status": "pending",
    },
    {
        "name": "Semantic clustering (mission-based peer groups)",
        "script": "semantic_clustering.py",
        "args": [],
        "priority": 2,
        "max_duration_hours": 5,
        "enabled": False,
        "status": "pending",
    },
    {
        "name": "Donation verification (5K+ links)",
        "script": "donation_verification_phase3.py",
        "args": ["--limit=5000"],
        "priority": 2,
        "max_duration_hours": 20,
        "enabled": False,
        "status": "pending",
    },
]

def load_queue():
    """Load GPU queue from disk."""
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return DEFAULT_QUEUE

def save_queue(queue):
    """Save GPU queue to disk."""
    QUEUE_FILE.write_text(json.dumps(queue, indent=2))

def check_gpu_available():
    """Check if GPU is available (not running Phase 4 or other work)."""
    try:
        # Check if any phase 4 process is running
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'phase' in cmdline.lower() and ('4' in cmdline or 'web_finder' in cmdline):
                    return False  # GPU still busy with Phase 4
            except:
                pass
        return True
    except:
        return True  # Assume available if we can't check

def get_next_task(queue):
    """Get next pending task, sorted by priority."""
    pending = [t for t in queue if t.get('status') == 'pending' and t.get('enabled')]
    if not pending:
        return None
    # Sort by priority (1=highest, 3=lowest)
    pending.sort(key=lambda t: t.get('priority', 3))
    return pending[0]

def run_task(task, queue):
    """Run a single GPU task."""
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                 GPU QUEUE TASK EXECUTION                    ║
╚════════════════════════════════════════════════════════════╝

Task:                {task['name']}
Script:              {task['script']}
Args:                {' '.join(task.get('args', []))}
Priority:            {task.get('priority')} (1=high)
Max duration:        {task.get('max_duration_hours')} hours
Started at:          {time.strftime('%Y-%m-%d %H:%M:%S')}
""")

    # Mark as running
    for t in queue:
        if t['name'] == task['name']:
            t['status'] = 'running'
            t['start_time'] = time.time()

    save_queue(queue)

    # Build command
    cmd = [sys.executable, str(SCRIPT_DIR / task['script'])] + task.get('args', [])

    log_file = LOGS_DIR / f"gpu_task_{task['name'].replace(' ', '_')}_{int(time.time())}.log"
    print(f"Logging to:          {log_file}")

    try:
        with open(log_file, 'w') as f:
            result = subprocess.run(
                cmd,
                timeout=task.get('max_duration_hours', 48) * 3600,
                stdout=f,
                stderr=subprocess.STDOUT,
            )

        # Mark as complete
        for t in queue:
            if t['name'] == task['name']:
                t['status'] = 'complete'
                t['end_time'] = time.time()
                t['result'] = 'success' if result.returncode == 0 else 'failed'

        save_queue(queue)

        elapsed = (time.time() - task.get('start_time', time.time())) / 3600
        print(f"""
✓ Task completed
  Duration:          {elapsed:.1f} hours
  Status:            {'SUCCESS' if result.returncode == 0 else 'FAILED'}
  Log:               {log_file}
""")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"✗ Task exceeded max duration ({task.get('max_duration_hours')} hours)")
        for t in queue:
            if t['name'] == task['name']:
                t['status'] = 'timeout'
                t['result'] = 'timeout'
        save_queue(queue)
        return False

    except Exception as e:
        print(f"✗ Task failed: {e}")
        for t in queue:
            if t['name'] == task['name']:
                t['status'] = 'error'
                t['result'] = str(e)
        save_queue(queue)
        return False

def show_queue(queue):
    """Display current queue status."""
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                   GPU WORKLOAD QUEUE                        ║
╚════════════════════════════════════════════════════════════╝

Current time:        {time.strftime('%Y-%m-%d %H:%M:%S')}
GPU available:       {'✓ YES' if check_gpu_available() else '✗ NO (Phase 4 running)'}
""")

    for i, task in enumerate(queue, 1):
        status = task.get('status', 'pending')
        enabled = '✓' if task.get('enabled') else '✗'
        symbol = '→' if status == 'pending' else ('◉' if status == 'running' else ('✓' if status == 'complete' else '✗'))

        print(f"""
{i}. [{enabled}] {symbol} {task['name']}
   Priority:         {task.get('priority', 3)} (1=high)
   Status:           {status}
   Script:           {task['script']}
   Max duration:     {task.get('max_duration_hours')} hours
""")

def main():
    parser = __import__('argparse').ArgumentParser(
        description='GPU queue manager'
    )
    parser.add_argument('--check', action='store_true', help='Check queue status')
    parser.add_argument('--run', action='store_true', help='Run next queued task')
    parser.add_argument('--add-mission-generation', action='store_true', help='Add mission generation to queue')
    parser.add_argument('--enable-task', type=str, help='Enable specific task by name')
    parser.add_argument('--disable-task', type=str, help='Disable specific task by name')
    parser.add_argument('--reset', action='store_true', help='Reset queue to default')
    args = parser.parse_args()

    queue = load_queue()

    if args.check:
        show_queue(queue)
        return

    if args.reset:
        queue = DEFAULT_QUEUE
        save_queue(queue)
        print("✓ Queue reset to default")
        show_queue(queue)
        return

    if args.enable_task:
        for t in queue:
            if args.enable_task.lower() in t['name'].lower():
                t['enabled'] = True
        save_queue(queue)
        print(f"✓ Enabled: {args.enable_task}")
        show_queue(queue)
        return

    if args.disable_task:
        for t in queue:
            if args.disable_task.lower() in t['name'].lower():
                t['enabled'] = False
        save_queue(queue)
        print(f"✓ Disabled: {args.disable_task}")
        show_queue(queue)
        return

    if args.run:
        if not check_gpu_available():
            print("✗ GPU is busy. Check status with --check")
            return
        task = get_next_task(queue)
        if not task:
            print("✓ No pending tasks in queue")
            show_queue(queue)
            return
        run_task(task, queue)
        return

    # Default: show queue
    show_queue(queue)

if __name__ == '__main__':
    main()
