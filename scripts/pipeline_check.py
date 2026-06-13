#!/usr/bin/env python3
"""
4-hour pipeline health check — appends one status block to logs/pipeline_status.log
Cron: 0 */4 * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/pipeline_check.py
"""
import sqlite3, subprocess, datetime, pathlib, re

BASE = pathlib.Path.home() / "meritgiving"
DB   = BASE / "data/merit_registry.db"
LOG  = BASE / "logs/pipeline_status.log"
NOW  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

lines = [f"\n{'='*60}", f"Pipeline check — {NOW}", f"{'='*60}"]

def tail_bytes(path, n=600):
    try:
        with open(path, 'rb') as f:
            f.seek(-n, 2)
            return f.read().decode('utf-8', errors='replace')
    except Exception:
        return ""

# ── DB metrics ───────────────────────────────────────────────
try:
    conn = sqlite3.connect(str(DB), timeout=10)
    total    = conn.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    missions = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE mission IS NOT NULL AND mission != ''").fetchone()[0]
    ai_web   = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE mission_source='ai_web'").fetchone()[0]
    donate   = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL AND donate_confidence >= 90").fetchone()[0]
    evidence = conn.execute("SELECT COUNT(DISTINCT ein) FROM donation_link_evidence").fetchone()[0]
    conn.close()
    lines.append(f"Missions   : {missions:,} / {total:,} ({missions/total*100:.1f}%)  ai_web={ai_web:,}")
    lines.append(f"Donate URLs: {donate:,} verified (≥90 conf)  evidence={evidence:,} candidates")
except Exception as e:
    lines.append(f"DB error: {e}")

# ── Running processes ────────────────────────────────────────
procs = subprocess.run(["pgrep", "-af", "python3"], capture_output=True, text=True).stdout
checks = {
    "generate_missions" : "Mission gen",
    "donation_link"     : "Donate links",
    "fetch_org_websites": "Web crawler",
    "lucido_scraper"    : "Lucido",
}
running = []
stopped = []
for pattern, label in checks.items():
    (running if pattern in procs else stopped).append(label)

if running: lines.append(f"Running    : {', '.join(running)}")
if stopped: lines.append(f"Stopped    : {', '.join(stopped)}")

# ── Mission gen progress ─────────────────────────────────────
raw = tail_bytes(BASE / "logs/generate_missions.log")
m = re.search(r'\[\s*(\d+\.\d+)%\]\s+(\S+) written\s+(\S+) errors\s+(\S+)/sec\s+ETA (\S+)', raw)
if m:
    pct, written, errors, rate, eta = m.groups()
    lines.append(f"Mission gen: {pct}% — {written} written  {errors} errors  {rate}/sec  ETA {eta}")
else:
    lines.append("Mission gen: no progress line found (may be done or starting)")

# ── Donate link progress ─────────────────────────────────────
link_logs = sorted((BASE / "logs").glob("link_workers_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
if link_logs:
    raw = tail_bytes(link_logs[0])
    m2 = re.search(r'verified=(\d+)\s+review=(\d+)\s+no_link=(\d+)\s+blocked=(\d+)\s+([\d.]+) orgs/s', raw)
    if m2:
        ver, rev, no_lnk, blk, rate2 = m2.groups()
        lines.append(f"Donate links: verified={ver}  no_link={no_lnk}  blocked={blk}  {rate2} orgs/s")

# ── Alerts ───────────────────────────────────────────────────
alerts = []
if "Mission gen" in stopped:
    alerts.append("ALERT: generate_missions.py not running — restart if < 100%")
if "Donate links" in stopped:
    alerts.append("ALERT: donation_link_workers.py not running")
if alerts:
    lines.append("")
    lines.extend(alerts)

output = "\n".join(lines) + "\n"
with open(LOG, "a") as f:
    f.write(output)

print(output)
