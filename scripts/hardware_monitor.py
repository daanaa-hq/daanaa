#!/usr/bin/env python3
"""
Hardware usage monitor — tracks CPU, memory, GPU, and process resource usage.
Run continuously or invoke hourly via cron.
"""

import subprocess
import json
import sqlite3
from datetime import datetime, timedelta
import sys
import os

def get_system_memory():
    """Get system-wide memory stats."""
    result = subprocess.run(['free', '-b'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    for line in lines:
        if 'Mem:' in line:
            parts = line.split()
            return {
                'total_mb': int(parts[1]) // (1024*1024),
                'used_mb': int(parts[2]) // (1024*1024),
                'free_mb': int(parts[3]) // (1024*1024),
                'available_mb': int(parts[6]) // (1024*1024) if len(parts) > 6 else 0,
            }
    return {}

def get_process_memory(pid):
    """Get memory usage for a specific process."""
    try:
        result = subprocess.run(['ps', '-p', str(pid), '-o', 'rss=%'],
                              capture_output=True, text=True, timeout=2)
        if result.stdout.strip():
            return int(result.stdout.strip()) // 1024  # KB to MB
    except:
        pass
    return 0

def get_gpu_stats():
    """Get GPU memory and utilization."""
    try:
        result = subprocess.run(['rocm-smi', '--json'],
                              capture_output=True, text=True, timeout=5)
        data = json.loads(result.stdout)
        return data
    except:
        return None

def get_top_processes(limit=10):
    """Get top N processes by memory usage."""
    result = subprocess.run(['ps', 'aux', '--sort=-%mem'],
                          capture_output=True, text=True)
    procs = []
    for line in result.stdout.split('\n')[1:limit+1]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 11:
            pid = parts[1]
            mem_pct = float(parts[2])
            rss_mb = int(parts[5]) // 1024  # KB to MB
            cmd = ' '.join(parts[10:13])
            if mem_pct > 0.1:  # Only track >0.1% users
                procs.append({
                    'pid': pid,
                    'mem_pct': mem_pct,
                    'rss_mb': rss_mb,
                    'cmd': cmd,
                })
    return procs

def check_critical_processes():
    """Check if critical processes are running."""
    critical = {
        'api': 'gunicorn',
        'embed_server': 'llama-server.*11436',
        'mission_gen': 'llama-server.*11437',
        'discovery': 'discovery_daemon|gpu_optimized_discovery',
    }

    status = {}
    for name, pattern in critical.items():
        result = subprocess.run(['pgrep', '-f', pattern],
                              capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        status[name] = len([p for p in pids if p])
    return status

def log_to_db(stats):
    """Log stats to monitoring database."""
    try:
        db = sqlite3.connect('data/merit_registry.db')
        c = db.cursor()

        # Create table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS hardware_monitor (
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_mb INTEGER,
            used_mb INTEGER,
            free_mb INTEGER,
            available_mb INTEGER,
            gpu0_vram_pct REAL,
            gpu1_vram_pct REAL,
            top_process_cmd TEXT,
            top_process_rss_mb INTEGER,
            api_running BOOLEAN,
            embed_running BOOLEAN,
            mission_running BOOLEAN,
            discovery_workers INTEGER
        )''')

        gpu_data = stats.get('gpu', {})
        gpu0_vram = 0
        gpu1_vram = 0
        if gpu_data and isinstance(gpu_data, dict):
            for key, val in gpu_data.items():
                if 'gpu_memory_used' in str(val):
                    if '0' in str(key):
                        gpu0_vram = val.get('gpu_memory_used', [0])[0] if isinstance(val, dict) else 0
                    elif '1' in str(key):
                        gpu1_vram = val.get('gpu_memory_used', [0])[0] if isinstance(val, dict) else 0

        top_proc = stats.get('top_processes', [{}])[0]
        critical = stats.get('critical', {})

        c.execute('''INSERT INTO hardware_monitor
            (total_mb, used_mb, free_mb, available_mb,
             gpu0_vram_pct, gpu1_vram_pct, top_process_cmd, top_process_rss_mb,
             api_running, embed_running, mission_running, discovery_workers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (stats['memory']['total_mb'],
             stats['memory']['used_mb'],
             stats['memory']['free_mb'],
             stats['memory']['available_mb'],
             gpu0_vram, gpu1_vram,
             top_proc.get('cmd', ''),
             top_proc.get('rss_mb', 0),
             critical.get('api', 0) > 0,
             critical.get('embed_server', 0) > 0,
             critical.get('mission_gen', 0) > 0,
             critical.get('discovery', 0)))

        db.commit()
        db.close()
    except Exception as e:
        print(f"Error logging to DB: {e}", file=sys.stderr)

def main():
    stats = {
        'timestamp': datetime.now().isoformat(),
        'memory': get_system_memory(),
        'top_processes': get_top_processes(5),
        'critical': check_critical_processes(),
        'gpu': get_gpu_stats(),
    }

    # Log to DB
    log_to_db(stats)

    # Print summary
    mem = stats['memory']
    print(f"[{stats['timestamp']}]")
    print(f"  Memory: {mem['used_mb']}/{mem['total_mb']}MB ({mem['available_mb']}MB avail)")

    top = stats['top_processes'][0] if stats['top_processes'] else {}
    if top:
        print(f"  Top process: {top['cmd'][:40]} ({top['rss_mb']}MB)")

    crit = stats['critical']
    print(f"  Critical: API={crit.get('api')>0} Embed={crit.get('embed_server')>0} Mission={crit.get('mission_gen')>0} Discovery={crit.get('discovery', 0)} workers")

if __name__ == '__main__':
    main()
