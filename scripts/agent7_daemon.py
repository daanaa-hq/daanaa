#!/usr/bin/env python3
"""
AGENT 7: OVERNIGHT DAEMON
Mission: Run the entire swarm unattended.
Usage: nohup python3 scripts/agent7_daemon.py &
"""
import os, sys, subprocess, time, datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

AGENTS = [
    ("Agent 1: Parser", "python3 scripts/agent1_parser.py"),
    ("Agent 2: Scorer", "python3 scripts/agent2_scorer.py"),
    ("Agent 3: Enricher", "python3 scripts/agent3_enricher.py"),
    ("Agent 4: Validator", "python3 scripts/agent4_validator.py"),
    ("Agent 5: Frontend", "python3 scripts/agent5_frontend.py"),
]

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(f"{LOG_DIR}/daemon.log", 'a') as f:
        f.write(line + "\n")

def run_agent(name, cmd):
    log(f">>> {name}")
    log(f"    Command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        log(f"    [OUT] {line}")
    for line in result.stderr.splitlines():
        log(f"    [ERR] {line}")
    if result.returncode == 0:
        log(f"    {name} PASSED")
        return True
    else:
        log(f"    {name} FAILED (exit code {result.returncode})")
        return False

log("="*60)
log("MERITGIVING OVERNIGHT DAEMON STARTED")
log("="*60)

all_passed = True
for name, cmd in AGENTS:
    success = run_agent(name, cmd)
    if not success:
        all_passed = False
        log("Daemon stopping due to failure")
        break
    time.sleep(2)

if all_passed:
    log("="*60)
    log("ALL AGENTS COMPLETED SUCCESSFULLY")
    log("Data layer is ready. Check VALIDATION_REPORT.txt")
    log("="*60)
else:
    log("="*60)
    log("SWARM FAILED — Check logs/daemon.log for details")
    log("="*60)
