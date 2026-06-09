#!/usr/bin/env python3
"""
Daily IRS data watch — TOP PRIORITY overnight job.

Checks IRS sources every day and, on a real delta, runs the full safe pipeline:
download -> assemble -> sandbox-validate (never touches live) -> quiesced apply
of only NEW orgs -> record marker. Gap-covering (missions/embeddings/scoring)
is left to the existing GPU pipeline, which picks up rows with NULL mission/score.

Sources watched:
  - IRS EO BMF monthly (eo1-4.csv) via Last-Modified  -> additive new 501c3 orgs
  - IRS SOI annual 990 extract (NNeoextract990.zip)   -> HEAD probe, alert only

Idempotent: a no-delta run is a cheap HEAD check and exits. State in
data/cache/irs_watch_state.json.

  cron (priority — runs before other heavy overnight jobs):
    0 21 * * * cd ~/meritgiving && venv/bin/python3 scripts/daily_irs_check.py \
               >> logs/daily_irs_check.log 2>&1
"""
import json, subprocess, sys, urllib.request
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
STATE_FILE = DATA / "cache" / "irs_watch_state.json"
BMF_CSV = DATA / "bmf.csv"
BMF_URL = "https://www.irs.gov/pub/irs-soi"
REGIONALS = ["eo1.csv", "eo2.csv", "eo3.csv", "eo4.csv"]
# Next unpublished SOI annual extract to probe (bump as years roll).
SOI_PROBE = ["25eoextract990.zip", "26eoextract990.zip"]


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def head(url, timeout=30):
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Last-Modified")
    except Exception as e:
        return getattr(e, "code", 0), None


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(s):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s, indent=2))


def run(cmd):
    log(f"$ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=BASE)
    if r.returncode != 0:
        raise SystemExit(f"step failed ({r.returncode}): {' '.join(cmd)}")


def main():
    log("=== Daily IRS watch ===")
    state = load_state()
    py = str(BASE / "venv" / "bin" / "python3")

    # --- SOI annual probe (alert only) ---
    for f in SOI_PROBE:
        code, _ = head(f"{BMF_URL}/{f}")
        if code == 200:
            log(f"!! NEW SOI annual extract available: {f} (HTTP 200) — ingest manually")
            state.setdefault("soi_seen", [])
            if f not in state["soi_seen"]:
                state["soi_seen"].append(f)
        else:
            log(f"   SOI {f}: HTTP {code} (not published)")

    # --- BMF monthly delta ---
    lm_latest = None
    for f in REGIONALS:
        code, lm = head(f"{BMF_URL}/{f}")
        if code != 200 or not lm:
            log(f"   BMF {f}: HTTP {code} — skipping this cycle")
            save_state(state)
            return
        dt = parsedate_to_datetime(lm)
        if lm_latest is None or dt > lm_latest:
            lm_latest = dt
    lm_iso = lm_latest.astimezone(timezone.utc).isoformat()
    prev = state.get("bmf_last_modified")
    log(f"   BMF upstream Last-Modified: {lm_iso} | last applied: {prev}")

    if prev == lm_iso:
        log("   No BMF delta. Done (cheap check).")
        save_state(state)
        return

    log("** BMF DELTA DETECTED — running download -> assemble -> sandbox -> apply **")

    # 1) download + assemble (backup current first)
    if BMF_CSV.exists():
        bak = DATA / f"bmf.csv.bak-{datetime.now():%Y%m%d}"
        BMF_CSV.replace(bak)
        log(f"   backed up old bmf.csv -> {bak.name}")
    tmpdir = DATA / "cache" / "bmf_new"
    tmpdir.mkdir(parents=True, exist_ok=True)
    for f in REGIONALS:
        run(["curl", "-s", "-L", "--max-time", "600", "-o", str(tmpdir / f), f"{BMF_URL}/{f}"])
    with open(BMF_CSV, "w", encoding="utf-8", errors="replace") as out:
        for i, f in enumerate(REGIONALS):
            with open(tmpdir / f, encoding="utf-8", errors="replace") as src:
                for j, line in enumerate(src):
                    if j == 0 and i > 0:
                        continue  # header only once
                    out.write(line)
    log(f"   assembled bmf.csv: {sum(1 for _ in open(BMF_CSV)):,} rows")

    # 2) sandbox validate against a fresh snapshot (never the live DB)
    sandbox = DATA / "sandbox" / "merit_sandbox.db"
    sandbox.parent.mkdir(parents=True, exist_ok=True)
    if sandbox.exists():
        sandbox.unlink()
    import sqlite3
    c = sqlite3.connect(DATA / "merit_registry.db", timeout=180)
    c.execute(f"VACUUM INTO '{sandbox}'")
    c.close()
    run([py, "scripts/sandbox_bmf_validate.py", "--sandbox", str(sandbox), "--bmf", str(BMF_CSV)])

    # 3) apply genuinely-new orgs via stop->apply->restart (the approach that actually
    #    beats the writer contention; SIGSTOP/retry both starve — see LESSONS)
    run([py, "scripts/refresh_bmf_apply.py"])

    # 4) refresh existing orgs non-disruptively: fill missing NTEE, update names, and
    #    recompute the REVERSIBLE closure flags (irs_revoked / bmf_present). Reinstated
    #    or re-listed orgs un-flag automatically next run — no rework, nothing deleted.
    #    (NTEE *changes* on scored orgs are deliberately left for a separate rescore pass.)
    run([py, "scripts/refresh_bmf_existing.py", "--live"])

    # 4) record marker
    state["bmf_last_modified"] = lm_iso
    state["bmf_last_applied_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    log("=== Done. New orgs applied; GPU pipeline will fill missions/embeddings/scores. ===")


if __name__ == "__main__":
    main()
