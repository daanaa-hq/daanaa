#!/usr/bin/env python3
import os, time, subprocess
import sys

def get_cpu_info():
    try:
        with open('/proc/loadavg', 'r') as f:
            load = f.read().split()[:3]
        with open('/proc/cpuinfo', 'r') as f:
            cores = sum(1 for line in f if line.startswith('processor'))
        return {"cores": cores, "load_1m": load[0], "load_5m": load[1], "load_15m": load[2]}
    except:
        return {"cores": 8, "load_1m": "?", "load_5m": "?", "load_15m": "?"}

def get_memory_info():
    try:
        r = subprocess.run(['free', '-h'], capture_output=True, text=True)
        lines = r.stdout.splitlines()
        mem_line = [l for l in lines if l.startswith('Mem:')]
        if mem_line:
            parts = mem_line[0].split()
            return {"total": parts[1], "used": parts[2], "free": parts[3]}
    except:
        pass
    return {"total": "?", "used": "?", "free": "?"}

def get_disk_info():
    try:
        r = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
        lines = r.stdout.splitlines()
        if len(lines) > 1:
            parts = lines[1].split()
            return {"total": parts[1], "used": parts[2], "free": parts[3], "pct": parts[4]}
    except:
        pass
    return {"total": "?", "used": "?", "free": "?", "pct": "?"}

def get_processes():
    try:
        r = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = r.stdout.splitlines()
        python_procs = [l for l in lines if 'python' in l.lower() and 'agent' in l.lower()]
        return len(python_procs)
    except:
        return 0

print("="*60)
print("  MERITGIVING SYSTEM MONITOR")
print("  Ctrl+C to stop")
print("="*60)

try:
    while True:
        cpu = get_cpu_info()
        mem = get_memory_info()
        disk = get_disk_info()
        procs = get_processes()
        
        os.system('clear' if os.name != 'nt' else 'cls')
        print(f"""
┌─────────────────────────────────────────────────────────────┐
│  CPU: AMD Ryzen 7 9700X ({cpu['cores']} cores)                              │
│  Load: {cpu['load_1m']} (1m) | {cpu['load_5m']} (5m) | {cpu['load_15m']} (15m)                        │
├─────────────────────────────────────────────────────────────┤
│  RAM: {mem['total']} total | {mem['used']} used | {mem['free']} free                      │
├─────────────────────────────────────────────────────────────┤
│  Disk: {disk['total']} total | {disk['used']} used | {disk['free']} free | {disk['pct']} used        │
├─────────────────────────────────────────────────────────────┤
│  Active Agent Processes: {procs:<3}                                    │
├─────────────────────────────────────────────────────────────┤
│  GPU: RX 7900 XTX — IDLE (data pipeline is CPU-bound)         │
└─────────────────────────────────────────────────────────────┘
        """)
        time.sleep(2)
except KeyboardInterrupt:
    print("\nMonitor stopped.")
