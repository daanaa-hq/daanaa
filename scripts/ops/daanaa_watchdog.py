#!/usr/bin/env python3
"""Daanaa watchdog — runs from cron every 5 minutes on the home box.

Three checks cover the whole platform:
  local_api    http://localhost:5000/health                 (home Flask)
  public_site  https://daanaa.org/health                    (droplet + Cloudflare)
  claim_path   https://daanaa.org/api/claim/health             (Cloudflare -> droplet
               proxy -> SSH tunnel -> home API; 200/404 from our own API proves
               every link works — the home SPA catch-all answers unknown GETs
               with 200 — while 503/timeout means the tunnel or proxy is down)

Alerts security@daanaa.org only on STATE CHANGE (fail->ok / ok->fail), never
repeats — a 3am outage is one email, not sixty. State in logs/watchdog_state.json.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mailer import send_ops_email

STATE_FILE = Path.home() / "meritgiving/logs/watchdog_state.json"


def check(name, url, ok_statuses, timeout=15):
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code in ok_statuses, f"HTTP {r.status_code}"
    except Exception as e:
        return False, type(e).__name__


def main():
    checks = {
        "local_api":   check("local_api",   "http://localhost:5000/health", {200}),
        "public_site": check("public_site", "https://daanaa.org/health",    {200}),
        "claim_path":  check("claim_path",  "https://daanaa.org/api/claim/health", {200, 404}),
    }
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    prev = {}
    if STATE_FILE.exists():
        try:
            prev = json.loads(STATE_FILE.read_text())
        except Exception:
            prev = {}

    changes = []
    state = {}
    for name, (ok, detail) in checks.items():
        state[name] = "ok" if ok else "down"
        if prev.get(name, "ok") != state[name]:
            changes.append(f"{name}: {prev.get(name, 'ok')} -> {state[name]} ({detail})")

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))

    if changes:
        downs = [n for n, s in state.items() if s == "down"]
        if downs:
            subject = f"[Daanaa ALERT] {', '.join(downs)} down"
            hint = ("claim_path down usually means the SSH tunnel dropped: "
                    "systemctl --user restart daanaa-claim-tunnel\n"
                    "local_api down: cd ~/meritgiving && ./restart_api.sh\n"
                    "public_site down: ssh the droplet, systemctl restart daanaa")
        else:
            subject = "[Daanaa OK] all systems recovered"
            hint = "No action needed."
        send_ops_email("security@daanaa.org", subject,
                       f"Watchdog state change at {now}\n\n" + "\n".join(changes) +
                       f"\n\nCurrent: {json.dumps(state)}\n\n{hint}\n")
        print(f"{now} alerted: {changes}")
    else:
        print(f"{now} no change: {json.dumps(state)}")


if __name__ == "__main__":
    main()
