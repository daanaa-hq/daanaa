#!/usr/bin/env python3
"""
Apply new BMF orgs to the live registry — robustly, via stop -> apply -> restart.

Why not just retry the insert? The live DB's pipeline writers (web_finder,
donation_link via cpu_night, reembed) hold the single WAL write-slot across slow
network I/O, starving any bulk insert indefinitely. SIGSTOP is worse: a writer
frozen mid-transaction holds the lock forever (deadlock). So we cleanly SIGTERM
the persistent pipeline writers (they roll back and release locks; they are
batch jobs, safe to relaunch), apply the tiny new-org delta uncontended, then
relaunch the pipeline. The read-only API is never touched.

Run as a script file (not `python -c`) so pgrep patterns don't self-match.
"""
import csv, os, signal, sqlite3, subprocess, time
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
BMF_CSV = BASE / "data" / "bmf.csv"
DB_PATH = BASE / "data" / "merit_registry.db"
PY = str(BASE / "venv" / "bin" / "python3")

# Persistent pipeline writers to stop (NOT the API, NOT short cron jobs).
STOP_PATTERNS = [
    "scripts/cpu_night.sh",
    "scripts/donation_link_pipeline.py",
    "scripts/web_finder_agent.py",
    "scripts/reembed_watchdog.py",
]

INSERT_SQL = """
INSERT OR IGNORE INTO registry_enriched (
    EIN, organization_name, NTEE1, NTEECC, STATE, CITY,
    subsection, deductibility, ruling_date, zipcode, source
) VALUES (?, ?, ?, ?, ?, ?, '3', '1', ?, ?, 'IRS_BMF')
"""


def log(m):
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def ntee1(c):
    return c[0].upper() if c and c[0].isalpha() else None


def pgrep(pat):
    out = subprocess.run(["pgrep", "-f", pat], capture_output=True, text=True).stdout
    return [int(x) for x in out.split() if x.isdigit() and int(x) != os.getpid()]


def stop_pipeline():
    pids = sorted({p for pat in STOP_PATTERNS for p in pgrep(pat)})
    log(f"stopping {len(pids)} pipeline writers (SIGTERM): {pids}")
    for p in pids:
        try: os.kill(p, signal.SIGTERM)
        except ProcessLookupError: pass
    # wait up to 20s for clean exit, then SIGKILL stragglers
    for _ in range(20):
        alive = [p for p in pids if _alive(p)]
        if not alive:
            break
        time.sleep(1)
    for p in pids:
        if _alive(p):
            log(f"  SIGKILL straggler {p}")
            try: os.kill(p, signal.SIGKILL)
            except ProcessLookupError: pass
    return pids


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def apply_new():
    con = sqlite3.connect(DB_PATH, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    before = con.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    existing = set(r[0] for r in con.execute("SELECT EIN FROM registry_enriched"))
    log(f"live before: {before:,} | existing EINs: {len(existing):,}")

    new_rows = []
    with open(BMF_CSV, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if row.get("SUBSECTION", "").strip() != "03": continue
            if row.get("DEDUCTIBILITY", "").strip() != "1": continue
            ein = (row.get("EIN") or "").strip().zfill(9)
            name = (row.get("NAME") or "").strip()[:200]
            if not ein or not name or ein in existing: continue
            ntee = (row.get("NTEE_CD") or "").strip()[:10]
            new_rows.append((
                ein, name, ntee1(ntee), ntee or None,
                (row.get("STATE") or "").strip().upper()[:2],
                (row.get("CITY") or "").strip()[:100],
                (row.get("RULING") or "").strip()[:8],
                (row.get("ZIP") or "").strip()[:10],
            ))
    log(f"genuinely-new orgs: {len(new_rows):,}")
    for i in range(0, len(new_rows), 5000):
        con.executemany(INSERT_SQL, new_rows[i:i + 5000])
        con.commit()
    after = con.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    con.close()
    log(f"live after: {after:,}  (+{after - before:,})")
    return after - before


def relaunch_pipeline():
    log("relaunching overnight pipeline (gpu_night.sh start)")
    subprocess.Popen(["bash", str(BASE / "scripts" / "gpu_night.sh"), "start"],
                     stdout=open(BASE / "logs" / "gpu_night.log", "a"),
                     stderr=subprocess.STDOUT, cwd=BASE)
    for lim in ("50000", "25000"):
        log(f"relaunching web_finder_agent --limit {lim}")
        subprocess.Popen([PY, "scripts/web_finder_agent.py", "--limit", lim],
                         stdout=open(BASE / "logs" / f"web_finder_{lim}.log", "a"),
                         stderr=subprocess.STDOUT, cwd=BASE)


def main():
    stopped = stop_pipeline()
    try:
        added = apply_new()
    finally:
        if stopped:
            relaunch_pipeline()
    log(f"done — {added} new orgs applied, pipeline relaunched")


if __name__ == "__main__":
    main()
