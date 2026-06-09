#!/usr/bin/env python3
"""
Populate is_hidden_gem on registry_enriched.

Definition (revised 2026-06-09): a hidden gem is a SMALL org that ranks HIGH among
its true peers and has verified financial data:
  - merit_score >= 85   (top ~15% within its operating-model + revenue-band cell)
  - total_revenue > 0 AND total_revenue < 500000  (small with verified revenue data)
  - mission present  (it has a readable story)

Sizing at definition time: 32,881 gems total, 5,817 in Education. The top picks are
micro-orgs ($7K-$40K revenue) scoring 100 — tiny but excellent, exactly the point.

This derives from merit_score, so the natural long-term home is right after the
scorer runs (fold into overnight_pipeline). Standalone here for a one-off populate.
Live write uses stop->apply->restart so it doesn't starve on the pipeline writers;
run it in a quiet window (it briefly pauses web_finder/donation/reembed).

  python3 scripts/flag_hidden_gems.py            # dry-run: counts only
  python3 scripts/flag_hidden_gems.py --apply    # write to live (stop/restart)
"""
import argparse, os, signal, sqlite3, subprocess, time
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "merit_registry.db"
PY = str(BASE / "venv" / "bin" / "python3")
STOP_PATTERNS = ["scripts/cpu_night.sh", "scripts/donation_link_pipeline.py",
                 "scripts/web_finder_agent.py", "scripts/reembed_watchdog.py"]

GEM = ("merit_score >= 85 AND total_revenue > 0 AND total_revenue < 500000 "
       "AND mission IS NOT NULL AND TRIM(mission) <> ''")


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def _alive(p):
    try: os.kill(p, 0); return True
    except (ProcessLookupError, PermissionError): return False
def pgrep(pat):
    out = subprocess.run(["pgrep", "-f", pat], capture_output=True, text=True).stdout
    return [int(x) for x in out.split() if x.isdigit() and int(x) != os.getpid()]


def counts(con):
    g = con.execute(f"SELECT COUNT(*) FROM registry_enriched WHERE {GEM}").fetchone()[0]
    return g


def write_flags(con):
    con.execute("PRAGMA busy_timeout=180000")
    con.execute(f"UPDATE registry_enriched SET is_hidden_gem = CASE WHEN {GEM} THEN 1 ELSE 0 END")
    con.commit()
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")


def stop_pipeline():
    pids = sorted({p for pat in STOP_PATTERNS for p in pgrep(pat)})
    log(f"stopping {len(pids)} pipeline writers: {pids}")
    for p in pids:
        try: os.kill(p, signal.SIGTERM)
        except ProcessLookupError: pass
    for _ in range(20):
        if not any(_alive(p) for p in pids): break
        time.sleep(1)
    for p in pids:
        if _alive(p):
            try: os.kill(p, signal.SIGKILL)
            except ProcessLookupError: pass
    return pids


def relaunch_pipeline():
    subprocess.Popen(["bash", str(BASE / "scripts" / "gpu_night.sh"), "start"],
                     stdout=open(BASE / "logs" / "gpu_night.log", "a"),
                     stderr=subprocess.STDOUT, cwd=BASE)
    for lim in ("50000", "25000"):
        subprocess.Popen([PY, "scripts/web_finder_agent.py", "--limit", lim],
                         stdout=open(BASE / "logs" / f"web_finder_{lim}.log", "a"),
                         stderr=subprocess.STDOUT, cwd=BASE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write to live DB (stop/restart)")
    args = ap.parse_args()

    con = sqlite3.connect(DB, timeout=120)
    log(f"hidden gems by current definition: {counts(con):,}")
    if not args.apply:
        log("dry-run only. Re-run with --apply to write is_hidden_gem.")
        con.close()
        return
    con.close()

    stopped = stop_pipeline()
    try:
        con = sqlite3.connect(DB, timeout=180)
        write_flags(con)
        n = con.execute("SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1").fetchone()[0]
        con.close()
        log(f"is_hidden_gem set on {n:,} orgs")
    finally:
        if stopped:
            relaunch_pipeline()


if __name__ == "__main__":
    main()
