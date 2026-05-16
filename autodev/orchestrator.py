#!/usr/bin/env python3
import json, subprocess, sys, time, os, datetime, re
from pathlib import Path

PROJECT = Path.home() / "meritgiving"
TASKS_FILE = Path.home() / "meritgiving/autodev/tasks.json"
LOG_DIR = Path.home() / "meritgiving/autodev/logs"
GOOSE_BIN = "goose"

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_DIR / "autodev.log", "a") as f:
        f.write(line + "\n")

def snapshot(task_id):
    os.chdir(PROJECT)
    if (PROJECT / ".git").exists():
        subprocess.run(["git", "add", "-A"], capture_output=True)
        subprocess.run(["git", "commit", "-m", f"pre-{task_id}", "--allow-empty"], capture_output=True)
        log(f"[{task_id}] 💾 Snapshot saved")
    else:
        log(f"[{task_id}] ⚠ No git repo — run: cd {PROJECT} && git init")

def run_task(task):
    tid = task["id"]
    log(f"[{tid}] ▶️  {task['title']}")
    
    files = task.get("files", [])
    prompt = task["prompt"]
    
    instruction = f"""You are the MERIT AutoDev engineer.
TASK: {prompt}
FILES: {', '.join(files)}
RULES:
- Edit ONLY the listed files.
- After editing, run the build/test command for this project (npm run build, npm test, or equivalent).
- If tests fail, fix the error and retry once.
- Report ONLY: SUCCESS or FAILED + reason.
PROJECT DIR: {PROJECT}
"""
    tmp = LOG_DIR / f"{tid}_prompt.txt"
    tmp.write_text(instruction)
    
    try:
        res = subprocess.run(
            [GOOSE_BIN, "run", "--instructions", str(tmp)],
            cwd=PROJECT, capture_output=True, text=True, timeout=900
        )
    except subprocess.TimeoutExpired:
        log(f"[{tid}] ⏱️ Timeout (15 min)")
        return False, "Timeout"
    
    (LOG_DIR / f"{tid}_out.txt").write_text(res.stdout)
    (LOG_DIR / f"{tid}_err.txt").write_text(res.stderr)
    
    out = res.stdout.lower()
    success = res.returncode == 0 and ("success" in out or "pass" in out or "completed" in out)
    
    if success:
        log(f"[{tid}] ✅ SUCCESS")
    else:
        err_snip = res.stderr[-500:] if res.stderr else res.stdout[-500:]
        log(f"[{tid}] ❌ FAILED: {err_snip.replace(chr(10), ' | ')}")
    
    return success, res.stdout + "\n" + res.stderr

def load_tasks():
    if not TASKS_FILE.exists():
        return []
    return json.loads(TASKS_FILE.read_text())

def save_tasks(tasks):
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))

def main():
    log("🚀 AutoDev Orchestrator Started")
    while True:
        tasks = load_tasks()
        pending = [t for t in tasks if t.get("status") == "pending"]
        if not pending:
            log("😴 No pending tasks. Checking again in 60s...")
            time.sleep(60)
            continue
        
        for task in pending:
            snapshot(task["id"])
            ok, _ = run_task(task)
            
            if ok:
                task["status"] = "done"
                task["finished"] = datetime.datetime.now().isoformat()
            else:
                task["retries"] = task.get("retries", 0) + 1
                if task["retries"] >= 3:
                    task["status"] = "failed"
                    log(f'[{task["id"]}] 🛑 Max retries. Human needed.')
                else:
                    task["status"] = "pending"
                    log(f'[{task["id"]}] 🔄 Retry {task["retries"]}/3')
            
            save_tasks(tasks)
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("🛑 Orchestrator stopped.")
