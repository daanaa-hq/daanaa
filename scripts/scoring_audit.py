#!/usr/bin/env python3
"""
scripts/scoring_audit.py
Audit trail for MERIT scoring runs.

As a module:
    from scoring_audit import start_run, complete_run

As a CLI:
    python3 scoring_audit.py --list
    python3 scoring_audit.py --backfill-initial
"""
import sqlite3, hashlib, json, uuid, sys, argparse
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path.home() / "meritgiving/data/merit_registry.db"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS scoring_runs (
    run_id          TEXT PRIMARY KEY,
    scorer_version  TEXT NOT NULL,
    started_at      TEXT NOT NULL,
    completed_at    TEXT,
    input_file      TEXT,
    input_hash      TEXT,
    input_ein_count INTEGER,
    scorable_count  INTEGER,
    output_ein_count INTEGER,
    output_file     TEXT,
    output_hash     TEXT,
    peer_group_count INTEGER,
    score_min       REAL,
    score_max       REAL,
    score_mean      REAL,
    score_median    REAL,
    band_distribution TEXT,
    notes           TEXT,
    git_commit      TEXT
);
"""


def _connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute(CREATE_TABLE)
    db.commit()
    return db


def _now():
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> str:
    try:
        import subprocess
        result = subprocess.run(
            ["git", "-C", str(Path.home() / "meritgiving"), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def start_run(scorer_version: str, input_file: str, notes: str = None) -> str:
    """
    Call at the start of a scoring run. Returns run_id to pass to complete_run().
    """
    run_id = str(uuid.uuid4())[:8]
    input_hash = _sha256(input_file) if Path(input_file).exists() else None
    try:
        with open(input_file) as f:
            data = json.load(f)
        input_ein_count = len(data)
    except Exception:
        input_ein_count = None

    db = _connect()
    db.execute(
        """INSERT INTO scoring_runs
           (run_id, scorer_version, started_at, input_file, input_hash,
            input_ein_count, notes, git_commit)
           VALUES (?,?,?,?,?,?,?,?)""",
        (run_id, scorer_version, _now(), input_file, input_hash,
         input_ein_count, notes, _git_commit())
    )
    db.commit()
    db.close()
    print(f"[AUDIT] Run started: {run_id} (scorer v{scorer_version})")
    return run_id


def complete_run(run_id: str, results: dict):
    """
    Call at the end of a scoring run.
    results dict keys: output_file, scorable_count, output_ein_count,
                       peer_group_count, scores (list), bands (dict)
    """
    scores = results.get("scores", [])
    bands  = results.get("bands", {})
    output_file = results.get("output_file")
    output_hash = _sha256(output_file) if output_file and Path(output_file).exists() else None

    score_min    = min(scores) if scores else None
    score_max    = max(scores) if scores else None
    score_mean   = round(sum(scores) / len(scores), 2) if scores else None
    score_median = sorted(scores)[len(scores) // 2] if scores else None

    db = _connect()
    db.execute(
        """UPDATE scoring_runs SET
               completed_at      = ?,
               scorable_count    = ?,
               output_ein_count  = ?,
               output_file       = ?,
               output_hash       = ?,
               peer_group_count  = ?,
               score_min         = ?,
               score_max         = ?,
               score_mean        = ?,
               score_median      = ?,
               band_distribution = ?
           WHERE run_id = ?""",
        (_now(),
         results.get("scorable_count"),
         results.get("output_ein_count"),
         output_file,
         output_hash,
         results.get("peer_group_count"),
         score_min, score_max, score_mean, score_median,
         json.dumps(bands),
         run_id)
    )
    db.commit()
    db.close()
    print(f"[AUDIT] Run completed: {run_id} | {len(scores)} scored | mean={score_mean}")


def backfill_initial(version="3.3", output_ein_count=43000, notes="Initial load — pre-audit-trail baseline"):
    """Insert a synthetic row representing the dataset as it existed before audit logging."""
    run_id = "initial0"
    db = _connect()
    existing = db.execute("SELECT 1 FROM scoring_runs WHERE run_id=?", (run_id,)).fetchone()
    if existing:
        print(f"[AUDIT] Initial load row already exists, skipping.")
        db.close()
        return
    db.execute(
        """INSERT INTO scoring_runs
           (run_id, scorer_version, started_at, completed_at,
            output_ein_count, notes)
           VALUES (?,?,?,?,?,?)""",
        (run_id, version,
         "2026-05-14T00:00:00+00:00",
         "2026-05-14T00:00:00+00:00",
         output_ein_count, notes)
    )
    db.commit()
    db.close()
    print(f"[AUDIT] Backfilled initial load row (run_id={run_id}).")


def list_runs():
    db = _connect()
    rows = db.execute(
        "SELECT * FROM scoring_runs ORDER BY started_at DESC"
    ).fetchall()
    db.close()

    if not rows:
        print("No scoring runs recorded.")
        return

    print(f"\n{'RUN ID':<10} {'VERSION':<8} {'STARTED':<26} {'SCORED':>7} {'MEAN':>6}  NOTES")
    print("-" * 80)
    for r in rows:
        scored = r["output_ein_count"] or "-"
        mean   = f"{r['score_mean']:.1f}" if r["score_mean"] else "-"
        note   = (r["notes"] or "")[:40]
        print(f"{r['run_id']:<10} {r['scorer_version']:<8} {r['started_at']:<26} {str(scored):>7} {mean:>6}  {note}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MERIT scoring audit log")
    parser.add_argument("--list", action="store_true", help="List all scoring runs")
    parser.add_argument("--backfill-initial", action="store_true", help="Insert baseline row for pre-audit data")
    args = parser.parse_args()

    if args.backfill_initial:
        backfill_initial()
    elif args.list:
        list_runs()
    else:
        parser.print_help()
