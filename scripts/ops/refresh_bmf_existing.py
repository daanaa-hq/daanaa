#!/usr/bin/env python3
"""
Refresh EXISTING orgs from the fresh BMF — safely, reversibly, no score churn.

Applies only the non-disruptive parts of a BMF refresh:
  * NTEE fill   — set NTEE where we had none (better categorization, no peer-group
                  change because un-scored stubs had no peer group anyway)
  * Name update — adopt the BMF's more-specific name (group-exemption subordinates,
                  rebrands) where it differs
  * REVERSIBLE flags (recomputed every run, never destructive):
      irs_revoked = on the IRS auto-revocation list right now
      bmf_present = present in the latest BMF cut right now
    A reinstated / re-listed org flips back automatically next run — no rework,
    nothing hidden or deleted.

NOT touched here (deliberately): NTEE *changes* on already-scored orgs (those move
peer groups → need a rescore pass) and any financial/mission/score field.

Reads bmf.csv; writes registry_enriched. Pass a DB path; --live wraps the write in
the proven stop->apply->restart so it beats the pipeline writers.
"""
import argparse, csv, os, signal, sqlite3, subprocess, time
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
BMF = BASE / "data" / "bmf.csv"
PY = str(BASE / "venv" / "bin" / "python3")
STOP_PATTERNS = ["scripts/cpu_night.sh", "scripts/donation_link_pipeline.py",
                 "scripts/web_finder_agent.py", "scripts/reembed_watchdog.py"]


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def ntee1(c): return c[0].upper() if c and c[0].isalpha() else None
def _alive(p):
    try: os.kill(p, 0); return True
    except (ProcessLookupError, PermissionError): return False
def pgrep(pat):
    out = subprocess.run(["pgrep", "-f", pat], capture_output=True, text=True).stdout
    return [int(x) for x in out.split() if x.isdigit() and int(x) != os.getpid()]


def ensure_columns(con):
    cols = [r[1] for r in con.execute("PRAGMA table_info(registry_enriched)")]
    for col in ("irs_revoked", "bmf_present"):
        if col not in cols:
            con.execute(f"ALTER TABLE registry_enriched ADD COLUMN {col} INTEGER")
            log(f"added column {col}")


def refresh(db_path):
    con = sqlite3.connect(db_path, timeout=180)
    con.execute("PRAGMA busy_timeout=180000")
    ensure_columns(con)

    revoked = set(r[0] for r in con.execute("SELECT ein FROM revoked_eins"))
    reg = {}
    for ein, name, nteecc in con.execute(
        "SELECT EIN, organization_name, NTEECC FROM registry_enriched"):
        reg[ein] = (name or "", nteecc or "")
    log(f"registry {len(reg):,} | revoked list {len(revoked):,}")

    bmf_present = set()
    ntee_fills, name_updates = [], []
    with open(BMF, newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            ein = (row.get("EIN") or "").strip().zfill(9)
            if not ein:
                continue
            bmf_present.add(ein)
            if ein not in reg:
                continue
            old_name, old_ntee = reg[ein]
            new_ntee = (row.get("NTEE_CD") or "").strip()[:10]
            new_name = (row.get("NAME") or "").strip()[:200]
            if new_ntee and not old_ntee:
                ntee_fills.append((new_ntee, ntee1(new_ntee), ein))
            if new_name and old_name and new_name.upper() != old_name.upper():
                name_updates.append((new_name, ein))

    log(f"NTEE fills: {len(ntee_fills):,} | name updates: {len(name_updates):,}")

    # 1) NTEE fills (only where empty — no score disruption)
    con.executemany(
        "UPDATE registry_enriched SET NTEECC=?, NTEE1=? WHERE EIN=? AND (NTEECC IS NULL OR NTEECC='')",
        ntee_fills)
    # 2) name updates
    con.executemany(
        "UPDATE registry_enriched SET organization_name=? WHERE EIN=?", name_updates)
    con.commit()

    # 3) reversible flags — set for ALL rows from current truth
    con.execute("UPDATE registry_enriched SET bmf_present=0, irs_revoked=0")
    con.commit()
    con.executemany("UPDATE registry_enriched SET bmf_present=1 WHERE EIN=?",
                    [(e,) for e in bmf_present])
    con.execute(
        "UPDATE registry_enriched SET irs_revoked=1 "
        "WHERE EIN IN (SELECT ein FROM revoked_eins)")
    con.commit()

    rev = con.execute("SELECT COUNT(*) FROM registry_enriched WHERE irs_revoked=1").fetchone()[0]
    gone = con.execute("SELECT COUNT(*) FROM registry_enriched WHERE bmf_present=0").fetchone()[0]
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    con.close()
    log(f"flags set -> irs_revoked={rev:,}  not-in-BMF={gone:,}")
    return len(ntee_fills), len(name_updates), rev, gone


def stop_pipeline():
    pids = sorted({p for pat in STOP_PATTERNS for p in pgrep(pat)})
    log(f"stopping {len(pids)} pipeline writers (SIGTERM): {pids}")
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
    log("relaunching pipeline (gpu_night.sh start + web_finder)")
    subprocess.Popen(["bash", str(BASE / "scripts" / "gpu_night.sh"), "start"],
                     stdout=open(BASE / "logs" / "gpu_night.log", "a"),
                     stderr=subprocess.STDOUT, cwd=BASE)
    for lim in ("50000", "25000"):
        subprocess.Popen([PY, "scripts/web_finder_agent.py", "--limit", lim],
                         stdout=open(BASE / "logs" / f"web_finder_{lim}.log", "a"),
                         stderr=subprocess.STDOUT, cwd=BASE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(BASE / "data" / "merit_registry.db"))
    ap.add_argument("--live", action="store_true",
                    help="wrap write in stop->apply->restart (use for the live DB)")
    args = ap.parse_args()

    if args.live:
        stopped = stop_pipeline()
        try:
            refresh(args.db)
        finally:
            if stopped:
                relaunch_pipeline()
    else:
        refresh(args.db)


if __name__ == "__main__":
    main()
