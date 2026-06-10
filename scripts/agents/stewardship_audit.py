#!/usr/bin/env python3
"""
T7 Stewardship & Governance agent — weekly principles audit.

Checks the invariants that protect trust, writes ops/stewardship_audit.md.
Each check maps to a STEWARDSHIP.md principle. A FAIL here should be treated
like a failing test — fix before shipping anything else.

Checks:
  P3 (evidence-based trust signals):
    - no org shows a donate link below confidence threshold as authoritative
    - no merit_score outside 0-100
  P4 (small-org fairness):
    - hidden gems all meet the published definition (score>=85, 0<revenue<500K)
  P8 (never handle funds) / revocation safety:
    - no revoked org carries an active donate_url status
  P9 (explainable):
    - agent_job_log shows agents are logging their runs (silent agents = drift)

Cron: weekly, Monday 05:45. Read-only. No LLM, no network.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

PROJECT = Path.home() / "meritgiving"
DB = PROJECT / "data" / "merit_registry.db"
OUT_DIR = PROJECT / "ops"
OUT = OUT_DIR / "stewardship_audit.md"


def main():
    OUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    checks = []

    def check(principle, name, sql, expect_zero=True):
        try:
            n = conn.execute(sql).fetchone()[0] or 0
        except sqlite3.Error as e:
            checks.append((principle, name, "ERROR", str(e)))
            return
        ok = (n == 0) if expect_zero else (n > 0)
        checks.append((principle, name, "PASS" if ok else "FAIL", f"{n:,}"))

    check("P3", "scores outside 0-100",
          "SELECT COUNT(*) FROM registry_enriched WHERE merit_score < 0 OR merit_score > 100")
    check("P3", "low-confidence links marked verified (conf<90 but status ok)",
          """SELECT COUNT(*) FROM registry_enriched
             WHERE donate_url IS NOT NULL AND donate_confidence < 90
               AND donate_url_status = 'verified'""")
    check("P4", "hidden gems violating published definition",
          """SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1
             AND (merit_score < 85 OR total_revenue <= 0 OR total_revenue >= 500000)""")
    check("P8", "revoked orgs with live donate links",
          """SELECT COUNT(*) FROM registry_enriched
             WHERE (COALESCE(irs_revoked,0)=1 OR org_status='revoked')
               AND donate_url IS NOT NULL AND COALESCE(donate_url_status,'') NOT IN ('', 'withheld', 'revoked')""")
    check("P9", "agent runs logged in last 7 days (expect > 0)",
          f"""SELECT COUNT(*) FROM agent_job_log
              WHERE started_at >= '{(datetime.now() - timedelta(days=7)).isoformat()}'""",
          expect_zero=False)

    conn.close()

    fails = [c for c in checks if c[2] in ("FAIL", "ERROR")]
    status = "ALL CLEAR" if not fails else f"{len(fails)} ISSUE(S) — FIX BEFORE SHIPPING"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Stewardship Audit (weekly, automated)",
        "",
        f"*Generated {now} · Status: **{status}***",
        "",
        "| Principle | Check | Result | Count |",
        "|-----------|-------|--------|-------|",
    ]
    for p, name, result, detail in checks:
        mark = "✅" if result == "PASS" else "❌"
        lines.append(f"| {p} | {name} | {mark} {result} | {detail} |")
    lines += [
        "",
        "Failing checks map to STEWARDSHIP.md principles. Correct the data, then",
        "document the fix (principle 6: mistakes corrected openly).",
        "",
        "*Regenerate: `python3 scripts/agents/stewardship_audit.py`*",
    ]
    OUT.write_text("\n".join(lines) + "\n")
    print(f"[stewardship_audit] {status} — wrote {OUT}")
    # Non-zero exit on failure so cron mail / wrappers can alert
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
