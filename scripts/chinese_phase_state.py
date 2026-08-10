#!/usr/bin/env python3
"""
Chinese Phase deterministic execution-state generator.

No LLM calls. No git writes. No network calls. No external connectors.
Reads real, verifiable sources only. Reports UNKNOWN rather than fabricating
a healthy value when a source doesn't exist or isn't instrumented.

Source-of-truth convention (documented here because none existed before this
script; establishing it is part of what this script does):

  academic_partnerships : file exists at
      docs/partnerships/chinese/<university-slug>.confirmed.md
      Deterministic file-glob count. 0 confirmed files = 0 (a real, measured
      zero), not UNKNOWN — the source exists (the docs/ directory), it's just
      empty of matches.

  papers_submitted      : file exists at
      docs/papers/chinese-phase-paper-<n>.md with a top line "STATUS: SUBMITTED"
      Same reasoning: file glob is a real source; 0 matches = real 0.

  pilot_organizations    : `pilot_invitations` table in data/merit_registry.db.
      NOT_INSTRUMENTED for Chinese-Phase specifically: the table has no
      phase/region/language column, so a count from it cannot be attributed to
      the Chinese Phase without guessing. Reported UNKNOWN with an explicit
      reason, not folded into a number.

  academic_partnerships / papers_submitted : a source directory that exists
      with zero matching files is a genuine measured 0. A directory that does
      not exist at all is UNKNOWN, not 0 (Codex review 2026-08-10: absence of
      the source is not evidence the source was checked and found empty).

Checkpoints are reported as FACTS ONLY (dates, days remaining, the plan's free-
text required_outcomes) with verdict "NOT_EVALUATED". This generator does NOT
compute ON_TRACK/OFF_TRACK/BLOCKED. An earlier version did, by string-matching
"2+" in required_outcomes text and ignoring every other requirement (papers,
follower counts, pilot thresholds, "channels live", workshops) -- Codex review
(2026-08-10) found this would produce a false ON_TRACK the moment currently-
UNKNOWN metrics became measured but still missed other thresholds, and was
only correct so far by accident. Computing a real verdict requires a
structured {metric, operator, target} requirements schema that does not exist
yet in CHINESE_PHASE_PLAN.json -- adding one is tracked as future work in
governance/DECISIONS.md, not done here.

  social_followers (WeChat / Bilibili / Zhihu) : requires platform API
      credentials as env vars (WECHAT_API_KEY, BILIBILI_API_KEY, ZHIHU_API_KEY).
      None configured as of this script's authoring. Reported UNKNOWN.

Fail-closed rules:
  - Missing/unreadable merit_registry.db -> hard exit(1), previous valid state
    file is left untouched (not overwritten with guessed values).
  - Any metric whose source doesn't exist or isn't instrumented -> "UNKNOWN"
    with a "reason" string, never coerced to 0 or "healthy".
  - Script never contacts a network, never invokes git, never sends anything.

Idempotent: running twice against the same repository/db state produces the
same metrics and the same checkpoint statuses (only `generated_at` differs,
which is metadata, not a measured value).
"""

import json
import os
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = REPO_ROOT / ".claude" / "autonomous" / "CHINESE_PHASE_PLAN.json"
DB_PATH = REPO_ROOT / "data" / "merit_registry.db"
OUTPUT_PATH = REPO_ROOT / ".claude" / "autonomous" / "chinese-phase-status.json"
PARTNERSHIPS_DIR = REPO_ROOT / "docs" / "partnerships" / "chinese"
PAPERS_DIR = REPO_ROOT / "docs" / "papers"

SCHEMA_VERSION = 1
GENERATOR_VERSION = "1.0.0"

SOCIAL_ENV_VARS = {
    "wechat_followers": "WECHAT_API_KEY",
    "bilibili_subscribers": "BILIBILI_API_KEY",
    "zhihu_followers": "ZHIHU_API_KEY",
}


class SourceUnavailable(Exception):
    """Raised when a required source (e.g. the database) cannot be read at all.
    This is a hard failure -> fail closed, do not write output."""


def count_confirmed_partnerships():
    """Real, deterministic file-glob count. A directory that exists with zero
    matches is a genuine measured 0. A directory that doesn't exist at all is
    NOT evidence of zero (per Codex review 2026-08-10: absence of the source
    is not the same as a measured empty source) -> UNKNOWN."""
    if not PARTNERSHIPS_DIR.exists():
        return {"value": None, "status": "UNKNOWN", "source": str(PARTNERSHIPS_DIR),
                "reason": "directory does not exist; source has never been "
                          "initialized, so absence is not a measured zero"}
    files = sorted(PARTNERSHIPS_DIR.glob("*.confirmed.md"))
    return {"value": len(files), "status": "MEASURED", "source": str(PARTNERSHIPS_DIR),
            "files": [f.name for f in files]}


def count_submitted_papers():
    """Real, deterministic file-glob + content check. Same UNKNOWN-if-absent
    convention as count_confirmed_partnerships (Codex review 2026-08-10)."""
    if not PAPERS_DIR.exists():
        return {"value": None, "status": "UNKNOWN", "source": str(PAPERS_DIR),
                "reason": "directory does not exist; source has never been "
                          "initialized, so absence is not a measured zero"}
    submitted = []
    for f in sorted(PAPERS_DIR.glob("chinese-phase-paper-*.md")):
        try:
            first_line = f.read_text(encoding="utf-8").splitlines()[0].strip()
        except (IndexError, UnicodeDecodeError, OSError):
            continue
        if first_line.upper() == "STATUS: SUBMITTED":
            submitted.append(f.name)
    return {"value": len(submitted), "status": "MEASURED", "source": str(PAPERS_DIR),
            "files": submitted}


def pilot_organizations_signed():
    """Deliberately UNKNOWN: pilot_invitations has no phase/region column, so a
    count from it cannot be honestly attributed to the Chinese Phase."""
    if not DB_PATH.exists():
        raise SourceUnavailable(f"database not found: {DB_PATH}")
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM pilot_invitations WHERE signup_completed = 1")
        total_all_phases = cur.fetchone()[0]
        conn.close()
    except sqlite3.Error as exc:
        raise SourceUnavailable(f"pilot_invitations query failed: {exc}") from exc
    return {
        "value": None,
        "status": "UNKNOWN",
        "reason": "pilot_invitations table has no phase/region column; "
                  "cannot attribute rows to the Chinese Phase specifically",
        "unattributed_total_all_phases": total_all_phases,
    }


def social_followers():
    result = {}
    for metric, env_var in SOCIAL_ENV_VARS.items():
        if os.environ.get(env_var):
            # Credential present but no client implemented yet -> still UNKNOWN,
            # never fabricate a follower count.
            result[metric] = {
                "value": None,
                "status": "UNKNOWN",
                "reason": f"{env_var} is set but no API client is implemented yet",
            }
        else:
            result[metric] = {
                "value": None,
                "status": "UNKNOWN",
                "reason": f"{env_var} not configured; account/API not connected",
            }
    return result


def load_plan():
    if not PLAN_PATH.exists():
        raise SourceUnavailable(f"plan file not found: {PLAN_PATH}")
    with open(PLAN_PATH, encoding="utf-8") as f:
        return json.load(f)


def checkpoint_days_remaining(checkpoint, today):
    """Pure calendar-date arithmetic (Codex review 2026-08-10: comparing
    timezone-aware datetimes at midnight UTC made a checkpoint go past_due
    immediately after UTC midnight on its stated date; compare calendar
    dates instead)."""
    if not isinstance(today, date) or isinstance(today, datetime):
        raise TypeError(f"today must be a datetime.date, got {type(today)!r}")
    checkpoint_date = datetime.strptime(checkpoint["date"], "%Y-%m-%d").date()
    return (checkpoint_date - today).days


def describe_checkpoint(checkpoint, today):
    """Deterministic, but deliberately NOT a status verdict.

    Codex review (2026-08-10) found the original evaluator only checked the
    single literal "2+" academic-partnership requirement via string parsing
    and silently ignored every other required outcome (papers, follower
    counts, pilot thresholds, "channels live", workshops). It would have
    produced a false ON_TRACK the moment currently-UNKNOWN metrics became
    measured but still fell short of the other thresholds -- it was only
    correct by accident (global UNKNOWN forcing BLOCKED).

    Per Codex's recommended minimal-scope fix: this generator reports facts
    (days remaining, which required outcomes exist as free text) and does
    NOT compute an authoritative ON_TRACK/OFF_TRACK/BLOCKED verdict. That
    requires a structured {metric, operator, target} requirements schema
    that does not exist yet in CHINESE_PHASE_PLAN.json. Adding one is future
    work, tracked in governance/DECISIONS.md.
    """
    return {
        "week": checkpoint["week"],
        "date": checkpoint["date"],
        "milestone": checkpoint["milestone"],
        "days_remaining": checkpoint_days_remaining(checkpoint, today),
        "required_outcomes": checkpoint.get("required_outcomes", []),
        "verdict": "NOT_EVALUATED",
        "verdict_reason": "no structured {metric, operator, target} schema exists "
                           "yet to evaluate required_outcomes against measured "
                           "metrics; see governance/DECISIONS.md 2026-08-10",
    }


def generate():
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    plan = load_plan()

    metrics = {
        "academic_partnerships": count_confirmed_partnerships(),
        "papers_submitted": count_submitted_papers(),
        "pilot_organizations": pilot_organizations_signed(),
        "social_followers": social_followers(),
    }

    checkpoints = [
        describe_checkpoint(cp, today) for cp in plan["checkpoints"]
    ]

    data_quality_flags = []
    for metric_name in ("academic_partnerships", "papers_submitted", "pilot_organizations"):
        if metrics[metric_name]["status"] == "UNKNOWN":
            data_quality_flags.append(f"{metric_name}: {metrics[metric_name]['reason']}")
    for m, v in metrics["social_followers"].items():
        if v["status"] == "UNKNOWN":
            data_quality_flags.append(f"{m}: {v['reason']}")

    state = {
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "generated_at": now_utc.isoformat(),
        "source_freshness": {
            "plan_file": str(PLAN_PATH.relative_to(REPO_ROOT)),
            "db_file": str(DB_PATH.relative_to(REPO_ROOT)) if DB_PATH.exists() else None,
        },
        "phase": plan.get("phase"),
        "metrics": metrics,
        "checkpoints": checkpoints,
        "data_quality": {
            "unknown_metric_count": sum(
                1 for f in data_quality_flags
            ),
            "flags": data_quality_flags,
        },
    }
    return state


def write_state_atomic(state):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = OUTPUT_PATH.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp_path.replace(OUTPUT_PATH)  # atomic on POSIX


def main():
    try:
        state = generate()
    except SourceUnavailable as exc:
        # Fail closed: do not touch any existing state file.
        print(f"FAIL-CLOSED: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - deliberate catch-all, fail closed
        print(f"FAIL-CLOSED (unexpected error): {exc}", file=sys.stderr)
        return 1

    write_state_atomic(state)
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
