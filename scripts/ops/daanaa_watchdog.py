#!/usr/bin/env python3
"""Daanaa watchdog — runs from cron every 5 minutes on the home box.

Checks:
  local_api    http://localhost:5000/health          (home Flask)
  public_site  https://daanaa.org/health             (droplet + Cloudflare)
  homepage     https://daanaa.org/                   (real page renders; /health can be OK while pages 500)
  claim_path   https://daanaa.org/api/claim/health   (full tunnel path: CF→droplet→tunnel→home)
  wallet_proxy https://daanaa.org/api/wallet/restore (wallet tunnel; 401=auth gate live, 503=tunnel down)
  search       https://daanaa.org/api/search?q=food+bank (FTS index healthy if results>0)
  droplet_disk SSH check: df / on droplet, alert if >85%

Alerts security@daanaa.org on STATE CHANGE (fail→ok / ok→fail), plus a
re-alert every REALERT_HOURS while anything stays down (the 2026-07-05
outage ran 11h on a single buried transition email). State in
logs/watchdog_state.json.
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mailer import send_ops_email

STATE_FILE = Path.home() / "meritgiving/logs/watchdog_state.json"
SSH_KEY = str(Path.home() / ".ssh/daanaa_do_cron")  # passphrase-free automation key (see LESSONS.md 2026-07-05)
DROPLET = "root@107.170.26.8"
DISK_ALERT_PCT = 85
REALERT_HOURS = 6
LATENCY_SLO_S = 3.0
LATENCY_PROBE_WORDS = ["health", "food", "children"]


def check(name, url, ok_statuses, timeout=15):
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code in ok_statuses, f"HTTP {r.status_code}"
    except Exception as e:
        return False, type(e).__name__


def check_homepage():
    """A real page must render. /health stayed 200 through the 2026-07-05
    outage while every SPA route returned 500 — so check what users see."""
    try:
        r = requests.get("https://daanaa.org/", timeout=15)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        if "<!doctype html" not in r.text[:200].lower():
            return False, "200 but no HTML doctype (not the SPA)"
        return True, "HTTP 200 + SPA HTML"
    except Exception as e:
        return False, type(e).__name__


def check_search():
    """FTS healthy = results > 0 for a common query."""
    try:
        r = requests.get("https://daanaa.org/api/search?q=food+bank", timeout=15)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        results = r.json().get("results", [])
        if len(results) == 0:
            return False, "0 results (FTS index may be empty)"
        return True, f"{len(results)} results"
    except Exception as e:
        return False, type(e).__name__


def check_search_latency(prev_breach: bool):
    """SLO: a common-word search must answer in under LATENCY_SLO_S seconds.
    Cache-busted (_cb) so we measure the droplet, not Cloudflare's cache —
    the 2026-07-18 regression (15-21s for common words) ran unalerted because
    nothing measured latency, only reachability. Alerts only on TWO
    consecutive breaches so a one-off blip (concurrent deploy, network hiccup)
    doesn't page; a real regression persists across the 5-minute cron gap.
    Returns (ok, detail, breach_now) — breach_now is carried in the state file
    as "_lat_breach" bookkeeping."""
    word = LATENCY_PROBE_WORDS[(datetime.now().minute // 5) % len(LATENCY_PROBE_WORDS)]
    try:
        t0 = time.monotonic()
        r = requests.get("https://daanaa.org/api/organizations",
                         params={"q": word, "per_page": 24, "_cb": time.time_ns()},
                         timeout=30)
        elapsed = time.monotonic() - t0
        if r.status_code != 200:
            breach, detail = True, f"q={word} HTTP {r.status_code}"
        else:
            breach = elapsed > LATENCY_SLO_S
            detail = f"q={word} {elapsed:.1f}s"
    except Exception as e:
        breach, detail = True, f"q={word} {type(e).__name__}"
    if breach and prev_breach:
        return False, f"{detail} — over {LATENCY_SLO_S}s SLO twice in a row", True
    return True, detail + (" (breach 1/2, watching)" if breach else ""), breach


def check_droplet_disk():
    """SSH to droplet, check root partition usage."""
    try:
        out = subprocess.check_output(
            ["ssh", "-i", SSH_KEY, "-o", "ConnectTimeout=10",
             "-o", "StrictHostKeyChecking=accept-new", DROPLET,
             "df / | tail -1 | awk '{print $5}'"],
            stderr=subprocess.DEVNULL, timeout=20,
        ).decode().strip().rstrip("%")
        pct = int(out)
        if pct >= DISK_ALERT_PCT:
            return False, f"disk {pct}% used (threshold {DISK_ALERT_PCT}%)"
        return True, f"disk {pct}% used"
    except Exception as e:
        return False, f"SSH failed: {type(e).__name__}"


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    prev = {}
    if STATE_FILE.exists():
        try:
            prev = json.loads(STATE_FILE.read_text())
        except Exception:
            prev = {}
    # "_last_alert"/"_lat_breach" are bookkeeping, not checks; keep them out
    # of the diff logic
    last_alert = prev.pop("_last_alert", 0)
    lat_prev_breach = bool(prev.pop("_lat_breach", False))

    lat_ok, lat_detail, lat_breach = check_search_latency(lat_prev_breach)
    checks = {
        "local_api":    check("local_api",    "http://localhost:5000/health",           {200}),
        "public_site":  check("public_site",  "https://daanaa.org/health",              {200}),
        "homepage":     check_homepage(),
        "claim_path":   check("claim_path",   "https://daanaa.org/api/claim/health",    {200, 404}),
        "wallet_proxy": check("wallet_proxy", "https://daanaa.org/api/wallet/restore",  {401}),
        "search":       check_search(),
        "search_latency": (lat_ok, lat_detail),
        "droplet_disk": check_droplet_disk(),
    }

    changes = []
    state = {}
    for name, (ok, detail) in checks.items():
        state[name] = "ok" if ok else "down"
        if prev.get(name, "ok") != state[name]:
            changes.append(f"{name}: {prev.get(name, 'ok')} -> {state[name]} ({detail})")

    # Re-alert while down: one buried transition email cost 11h on 2026-07-05
    stale_downs = [n for n, s in state.items() if s == "down"]
    now_ts = datetime.now().timestamp()
    realert = (not changes and stale_downs
               and now_ts - last_alert > REALERT_HOURS * 3600)
    if realert:
        changes = [f"{n}: STILL down ({checks[n][1]})" for n in stale_downs]

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if changes:
        last_alert = now_ts
    STATE_FILE.write_text(json.dumps(
        {**state, "_last_alert": last_alert, "_lat_breach": lat_breach}))

    if changes:
        downs = [n for n, s in state.items() if s == "down"]
        if downs:
            subject = f"[Daanaa ALERT] {', '.join(downs)} down"
            hints = {
                "claim_path":   "SSH tunnel dropped → systemctl --user restart daanaa-claim-tunnel",
                "wallet_proxy": "Wallet tunnel down (same as claim tunnel) or local API auth broken",
                "local_api":    "cd ~/meritgiving && ./restart_api.sh",
                "public_site":  "ssh root@107.170.26.8 'systemctl restart daanaa-api'",
                "homepage":     "Pages 500 while /health OK → check journalctl -u daanaa-api on droplet; likely bad droplet_api.py deploy → restore /opt/daanaa/droplet_api.py.prev + restart",
                "search":       "FTS index empty → cd ~/meritgiving && venv/bin/python3 scripts/build_fts_index.py --rebuild && bash scripts/deploy_browse.sh",
                "search_latency": "Search slow but up → reproduce ONCE isolated on the droplet, then EXPLAIN QUERY PLAN (join-order flip class, LESSONS.md 2026-07-18); check for concurrent deploys/backups pinning droplet CPU before touching code",
                "droplet_disk": "Droplet disk full → ssh root@107.170.26.8 'du -sh /data/precompute/v1/*/* | sort -rh | head -20'",
            }
            hint = "\n".join(f"• {n}: {hints[n]}" for n in downs if n in hints)
        else:
            subject = "[Daanaa OK] all systems recovered"
            hint = "No action needed."
        send_ops_email("security@daanaa.org", subject,
                       f"Watchdog state change at {now}\n\n" + "\n".join(changes) +
                       f"\n\nCurrent: {json.dumps(state, indent=2)}\n\nFix hints:\n{hint}\n")
        print(f"{now} alerted: {changes}")
    else:
        print(f"{now} no change: {json.dumps(state)}")


if __name__ == "__main__":
    main()
