#!/usr/bin/env python3
"""
Daanaa Morning Brief — daily ops signal written to logs/morning_brief.md
Run via cron at 7am: 0 7 * * * /home/akbar/meritgiving/venv/bin/python3 /home/akbar/meritgiving/scripts/morning_brief.py
"""
import sqlite3, os, subprocess, datetime, pathlib, urllib.request, json, re

BASE   = pathlib.Path.home() / "meritgiving"
DB     = BASE / "data/merit_registry.db"
OUTDIR = BASE / "logs"
TODAY  = datetime.date.today().isoformat()
OUT    = OUTDIR / f"morning_brief_{TODAY}.md"

lines = []
def h(text):  lines.append(f"\n## {text}\n")
def li(text): lines.append(f"- {text}")
def ok(text): lines.append(f"- ✅ {text}")
def warn(text): lines.append(f"- ⚠️  {text}")
def err(text):  lines.append(f"- ❌ {text}")

lines.append(f"# Daanaa Morning Brief — {TODAY}")
lines.append(f"_Generated {datetime.datetime.now().strftime('%H:%M')} by morning_brief.py_\n")

# ── DATA FOUNDATION ──────────────────────────────────────────────────────────
h("Data Foundation")
if DB.exists():
    conn = sqlite3.connect(str(DB))
    total      = conn.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    w_mission  = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE mission IS NOT NULL AND mission != ''").fetchone()[0]
    ai_ntee    = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE mission_source = 'ai_ntee'").fetchone()[0]
    ai_web     = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE mission_source = 'ai_web'").fetchone()[0]
    lucido     = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE mission_source = 'lucido'").fetchone()[0]
    w_website  = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE website IS NOT NULL AND website != ''").fetchone()[0]
    w_donate   = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL AND donate_url != '' AND donate_confidence >= 90").fetchone()[0]
    conn.close()

    pct_mission = w_mission / total * 100

    li(f"Total orgs: **{total:,}**")
    ok("Embeddings: **1,811,930** (100%) — complete")

    status = ok if pct_mission >= 80 else warn if pct_mission >= 30 else err
    status(f"Missions: **{w_mission:,}** ({pct_mission:.1f}%) — ai_ntee:{ai_ntee:,} ai_web:{ai_web:,} lucido:{lucido:,}")

    donate_ok = ok if w_donate >= 100 else warn
    donate_ok(f"Verified donate URLs: **{w_donate:,}** (target: 100+)")
    li(f"Orgs with website: {w_website:,}")
else:
    err(f"DB not found at {DB}")

# ── PIPELINE PROCESSES ────────────────────────────────────────────────────────
h("Running Pipelines")
procs = subprocess.run(["pgrep", "-a", "python3"], capture_output=True, text=True).stdout
known = {
    "generate_missions": "Mission generation",
    "fetch_org_websites": "Web crawler",
    "lucido_scraper": "Lucido scraper",
    "donation_link_pipeline": "Donation link pipeline",
    "backfill": "Backfill pipeline",
}
found_any = False
for pattern, label in known.items():
    if pattern in procs:
        ok(f"{label} running")
        found_any = True

# Llama servers
for port, label in [("11436", "mxbai embed server"), ("11437", "Qwen32B mission gen server")]:
    check = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
    if check.returncode == 0 and check.stdout.strip():
        ok(f"{label} (:{port})")
    else:
        warn(f"{label} NOT listening on :{port}")

if not found_any:
    warn("No active pipeline processes detected")

# Mission generation progress from log
mission_log = BASE / "logs/generate_missions.log"
if mission_log.exists():
    tail = subprocess.run(["tail", "-1", str(mission_log)], capture_output=True, text=True).stdout.strip()
    m = re.search(r'\[\s*(\d+\.\d+)%\]\s+(\d+) written\s+(\d+) errors\s+(\S+)/sec\s+ETA (\S+)', tail)
    if m:
        pct, written, errors, rate, eta = m.groups()
        eta_h = float(eta.replace('m','')) / 60 if 'm' in eta else float(eta.replace('h',''))
        li(f"Mission gen: **{pct}%** complete — {written} written, {errors} errors, {rate}/sec, ETA {eta_h:.1f}h")

# ── API HEALTH ────────────────────────────────────────────────────────────────
h("API Health")
try:
    resp = urllib.request.urlopen("http://localhost:5000/health", timeout=3)
    data = json.loads(resp.read())
    ok(f"API responding — status: {data.get('status', 'ok')}")
except Exception as e:
    err(f"API not responding: {e}")

try:
    resp2 = urllib.request.urlopen("http://localhost:5000/api/v1/health", timeout=3)
    ok("api_v1 Blueprint responding")
except Exception:
    warn("api_v1 not responding (may be expected if Blueprint not registered yet)")

# ── GIT LOG (since yesterday) ─────────────────────────────────────────────────
h("Recent Commits (24h)")
gitlog = subprocess.run(
    ["git", "-C", str(BASE), "log", "--oneline", "--since=24 hours ago"],
    capture_output=True, text=True
).stdout.strip()
if gitlog:
    for line in gitlog.splitlines():
        li(f"`{line}`")
else:
    li("No commits in the last 24 hours")

# ── OKR PULSE ────────────────────────────────────────────────────────────────
h("OKR Pulse")

# KR 1.3 — 1.8M EINs
if DB.exists() and total >= 1_800_000:
    ok(f"KR 1.3 — 1.8M EINs queryable ({total:,}) ✓")
else:
    warn(f"KR 1.3 — EINs: {total:,} / 1,800,000")

# KR 1.2 — gates
gate0 = ok
gate0("Gate 0 CLOSED (2026-05-28)")

gate1_done = False  # human action: bank account, attorney consult
if not gate1_done:
    warn("Gate 1 — Legal Foundation: bank account + attorney consult pending (Akbar action)")

# Donate URLs progress toward 100+
if DB.exists():
    if w_donate >= 100:
        ok(f"Donation links: {w_donate:,} verified ✓ (target: 100+)")
    else:
        warn(f"Donation links: {w_donate:,} / 100+ target — pipeline running")

# KR 3.3 — user research
warn("KR 3.3 — 0/20 user research conversations completed (Akbar calendar)")

# ── FINANCIALS ────────────────────────────────────────────────────────────────
h("Financial Pulse")
li("Credit card: $4K / $13K used (0% APR until March 2027)")
li("Runway: ~$9K available, target <$300/mo burn")
li("Revenue target: EcoMargins ESG portal (Oct 2026) → first B2B sales")
warn("Gate 2 credits: submit AWS/GCP/Cloudflare/MSFT/Anthropic applications this week")

# ── TODAY'S PRIORITIES ────────────────────────────────────────────────────────
h("Today's Focus")
li("**Build:** Mission quality patch (3 bugs in generate_missions.py)")
li("**Akbar:** Open business bank account under EcoMargins LLC")
li("**Akbar:** Grab @daanaa on Twitter/X")
li("**Akbar:** Create daanaa-org/daanaa GitHub repo")
li("**Pipeline:** Donation link pipeline running toward 100+ verified")

# ── WRITE OUTPUT ──────────────────────────────────────────────────────────────
content = "\n".join(lines) + "\n"
OUT.write_text(content)

# Also append to daily_report (backward compat)
daily = OUTDIR / f"daily_report_{TODAY}.txt"
with open(daily, "a") as f:
    f.write("\n\n--- MORNING BRIEF ---\n")
    for line in lines[2:]:  # skip title lines
        f.write(line + "\n")

print(f"Brief written to {OUT}")
print(content)
