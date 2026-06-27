#!/usr/bin/env python3
"""
Daily IRS data watch — TOP PRIORITY overnight job.

Checks IRS sources every day via Last-Modified headers and, on a real delta,
runs the appropriate safe pipeline. All three sources are checked every run;
a no-delta run is just three cheap HEAD requests.

Sources watched:
  - IRS EO BMF monthly (eo1-4.csv)               -> additive new 501c3 orgs
  - IRS auto-revocation list (monthly ~)          -> flag irs_revoked in registry
  - IRS 990-N ePostcard file (monthly ~)          -> swap flat file for downstream use
  - IRS SOI annual 990 extract (NNeoextract990)   -> HEAD probe, alert only

State in data/cache/irs_watch_state.json.

  cron (priority — runs before other overnight jobs):
    0 21 * * * cd ~/meritgiving && venv/bin/python3 scripts/daily_irs_check.py \
               >> logs/daily_irs_check.log 2>&1
"""
import io, json, shutil, sqlite3, subprocess, urllib.request, zipfile
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
STATE_FILE  = DATA / "cache" / "irs_watch_state.json"
BMF_CSV     = DATA / "bmf.csv"
REVOC_CACHE = DATA / "irs_revocation_cache.csv"
EPOST_TXT   = DATA / "data-download-epostcard.txt"
BMF_URL     = "https://www.irs.gov/pub/irs-soi"
REVOC_URL   = "https://apps.irs.gov/pub/epostcard/data-download-revocation.zip"
EPOST_URL   = "https://apps.irs.gov/pub/epostcard/data-download-epostcard.zip"
REGIONALS   = ["eo1.csv", "eo2.csv", "eo3.csv", "eo4.csv"]
SOI_PROBE   = ["25eoextract990.zip", "26eoextract990.zip"]


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def head(url, timeout=30):
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Last-Modified")
    except Exception as e:
        return getattr(e, "code", 0), None


def lm_iso(lm_str):
    return parsedate_to_datetime(lm_str).astimezone(timezone.utc).isoformat()


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(s):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s, indent=2))


def run(cmd):
    log(f"$ {' '.join(cmd)}")
    r = subprocess.run([str(a) for a in cmd], cwd=BASE)
    if r.returncode != 0:
        raise SystemExit(f"step failed ({r.returncode}): {' '.join(cmd)}")


def check_revocations(state, py):
    code, lm = head(REVOC_URL)
    if code != 200 or not lm:
        log(f"   Revocation: HTTP {code} — skipping this cycle")
        return
    lm = lm_iso(lm)
    prev = state.get("revoc_last_modified")
    log(f"   Revocation upstream Last-Modified: {lm} | last applied: {prev}")
    if lm == prev:
        log("   No revocation delta.")
        return
    log("** REVOCATION DELTA — sandbox-first sync **")
    # Rebuild sandbox, then force-sync against live (sync script has its own integrity gate)
    sandbox = DATA / "sandbox" / "merit_sandbox.db"
    sandbox.parent.mkdir(parents=True, exist_ok=True)
    if sandbox.exists():
        sandbox.unlink()
    con = sqlite3.connect(str(DATA / "merit_registry.db"), timeout=180)
    con.execute(f"VACUUM INTO '{sandbox}'")
    con.close()
    log("   Sandbox rebuilt for revocation dry-run")
    run([py, "scripts/sync_irs_revocations.py", "--force"])
    state["revoc_last_modified"] = lm
    state["revoc_last_applied_at"] = datetime.now(timezone.utc).isoformat()
    log("   Revocation sync complete.")


def check_epostcard(state):
    code, lm = head(EPOST_URL)
    if code != 200 or not lm:
        log(f"   990-N ePostcard: HTTP {code} — skipping this cycle")
        return
    lm = lm_iso(lm)
    prev = state.get("epost_last_modified")
    log(f"   990-N ePostcard upstream Last-Modified: {lm} | last applied: {prev}")
    if lm == prev:
        log("   No 990-N delta.")
        return
    log("** 990-N DELTA — downloading and swapping ePostcard file **")
    bak = EPOST_TXT.with_name(f"data-download-epostcard.txt.bak-{datetime.now():%Y%m%d}")
    if EPOST_TXT.exists():
        shutil.copy2(EPOST_TXT, bak)
        log(f"   backed up old ePostcard → {bak.name}")
    with urllib.request.urlopen(EPOST_URL, timeout=300) as r:
        raw = r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        EPOST_TXT.write_bytes(zf.read(zf.namelist()[0]))
    rows = sum(1 for line in EPOST_TXT.open(encoding="utf-8", errors="replace") if line.strip())
    log(f"   ePostcard file updated: {EPOST_TXT.stat().st_size/1e6:.1f}MB, {rows:,} rows")
    state["epost_last_modified"] = lm
    state["epost_last_applied_at"] = datetime.now(timezone.utc).isoformat()


def main():
    log("=== Daily IRS watch ===")
    state = load_state()
    py = str(BASE / "venv" / "bin" / "python3")

    # --- SOI annual probe (alert only) ---
    for f in SOI_PROBE:
        code, _ = head(f"{BMF_URL}/{f}")
        if code == 200:
            log(f"!! NEW SOI annual extract available: {f} — ingest manually")
            state.setdefault("soi_seen", [])
            if f not in state["soi_seen"]:
                state["soi_seen"].append(f)
        else:
            log(f"   SOI {f}: HTTP {code} (not published)")

    # --- Revocation list (Last-Modified gated) ---
    check_revocations(state, py)
    save_state(state)

    # --- 990-N ePostcard (Last-Modified gated) ---
    check_epostcard(state)
    save_state(state)

    # --- BMF monthly delta (Last-Modified gated) ---
    lm_latest = None
    for f in REGIONALS:
        code, lm = head(f"{BMF_URL}/{f}")
        if code != 200 or not lm:
            log(f"   BMF {f}: HTTP {code} — skipping BMF check this cycle")
            save_state(state)
            return
        dt = parsedate_to_datetime(lm)
        if lm_latest is None or dt > lm_latest:
            lm_latest = dt
    bmf_lm = lm_latest.astimezone(timezone.utc).isoformat()
    prev = state.get("bmf_last_modified")
    log(f"   BMF upstream Last-Modified: {bmf_lm} | last applied: {prev}")

    if prev == bmf_lm:
        log("   No BMF delta.")
        save_state(state)
        log("=== Done (no deltas). ===")
        return

    log("** BMF DELTA — download -> assemble -> sandbox -> apply **")

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
                        continue
                    out.write(line)
    log(f"   assembled bmf.csv: {sum(1 for _ in open(BMF_CSV)):,} rows")

    sandbox = DATA / "sandbox" / "merit_sandbox.db"
    sandbox.parent.mkdir(parents=True, exist_ok=True)
    if sandbox.exists():
        sandbox.unlink()
    c = sqlite3.connect(str(DATA / "merit_registry.db"), timeout=180)
    c.execute(f"VACUUM INTO '{sandbox}'")
    c.close()
    run([py, "scripts/sandbox_bmf_validate.py", "--sandbox", str(sandbox), "--bmf", str(BMF_CSV)])
    run([py, "scripts/refresh_bmf_apply.py"])
    run([py, "scripts/refresh_bmf_existing.py", "--live"])

    state["bmf_last_modified"] = bmf_lm
    state["bmf_last_applied_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    log("=== Done. New BMF orgs applied; GPU pipeline will fill missions/embeddings/scores. ===")


if __name__ == "__main__":
    main()
