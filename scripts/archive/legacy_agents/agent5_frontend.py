#!/usr/bin/env python3
"""
AGENT 5: FRONTEND FIXER
Mission: Deploy new app.py and templates, fix null-byte corruption.
"""
import os, shutil, sys, subprocess
from pathlib import Path

print("[AGENT 5] Starting frontend rebuild...")

SWARM_DIR = Path(__file__).parent
NEW_APP = SWARM_DIR.parent / "app.py"
TEMPLATES_SRC = SWARM_DIR.parent / "templates"
TEMPLATES_DST = Path("templates")

if not NEW_APP.exists():
    print(f"[AGENT 5] New app.py not found at {NEW_APP}")
    print("[AGENT 5] Looking in current directory...")
    if Path("app.py.new").exists():
        NEW_APP = Path("app.py.new")
    else:
        print("[AGENT 5] ERROR: Cannot find new app.py")
        sys.exit(1)

if Path("app.py").exists():
    backup_name = f"app.py.backup.{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}"
    shutil.copy("app.py", backup_name)
    print(f"[AGENT 5] Backed up old app.py to {backup_name}")

if Path("app.py").exists():
    with open("app.py", 'rb') as f:
        content = f.read()
    if b'\x00' in content:
        print("[AGENT 5] Detected null-byte corruption in old app.py — removing")
        os.remove("app.py")

shutil.copy(NEW_APP, "app.py")
print("[AGENT 5] Deployed new app.py")

TEMPLATES_DST.mkdir(exist_ok=True)

for tmpl in ["index.html", "org.html"]:
    src = TEMPLATES_SRC / tmpl
    dst = TEMPLATES_DST / tmpl
    if src.exists():
        shutil.copy(src, dst)
        print(f"[AGENT 5] Deployed template: {tmpl}")
    else:
        print(f"[AGENT 5] Template missing: {src}")

print("[AGENT 5] Verifying app.py imports...")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("app", "app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("[AGENT 5] app.py loads without errors")
except Exception as e:
    print(f"[AGENT 5] app.py has import errors: {e}")
    sys.exit(1)

print("[AGENT 5]")
print("[AGENT 5] To restart the server, run:")
print("[AGENT 5]   pkill -f uvicorn")
print("[AGENT 5]   nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8081 &")
print("[AGENT 5]")
print("[AGENT 5] Frontend rebuild complete")
