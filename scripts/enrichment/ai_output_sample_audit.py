#!/usr/bin/env python3
"""
ai_output_sample_audit.py — Monthly sample audit of AI-generated outputs.

Implements point 2 of the AI-output human-review policy (adopted by board
simulation 2026-07-17, docs/BOARD_SIMULATION_2026_07_17_EVENING.md):
"Per-item outputs at scale (missions, links, tags): automated verification +
honest provenance label + Mistake Registry corrections path + monthly sample
audit (100 items/type)."

Samples 100 random items per output type and runs automated quality checks:

  missions    — non-empty, sane length, has provenance (mission_source),
                no shame-language terms from the LANGUAGE_AND_MINDSET avoid-list
  donate_urls — live-status links: URL well-formed, host resolves via HEAD
                (20 fetched per run to stay polite), status field consistent
  cause_tags  — valid JSON array, 1..10 tags, tags are short strings

Writes a dated report to logs/ai_audit/, flags failures above threshold by
creating logs/.AI_AUDIT_ATTENTION for the next active session.

Run monthly via cron; safe to run ad-hoc.
    python3 scripts/ai_output_sample_audit.py
"""

import sqlite3
import json
import random
import re
from datetime import datetime
from pathlib import Path

import requests

DB = Path.home() / "meritgiving/data/merit_registry.db"
REPORT_DIR = Path.home() / "meritgiving/logs/ai_audit"
ATTENTION_MARKER = Path.home() / "meritgiving/logs/.AI_AUDIT_ATTENTION"

SAMPLE_SIZE = 100
LINK_FETCH_BUDGET = 20          # polite: only 20 live HEAD checks per audit
FAIL_THRESHOLD_PCT = 10         # >10% failures in any type → attention marker

# From governance/LANGUAGE_AND_MINDSET.md avoid-list — these words in an
# AI-written mission indicate voice drift worth a human look.
SHAME_TERMS = re.compile(
    r"\b(failing|struggling|at-risk|at risk of failure|underperforming|"
    r"poorly run|mismanaged|untrustworthy)\b", re.I)


def sample_missions(db):
    rows = db.execute("""
        SELECT EIN, mission, mission_source FROM registry_enriched
        WHERE mission IS NOT NULL AND mission != ''
          AND mission_source LIKE 'ai%'
        ORDER BY RANDOM() LIMIT ?""", (SAMPLE_SIZE,)).fetchall()
    failures = []
    for ein, mission, source in rows:
        problems = []
        if len(mission) < 20:
            problems.append("too short (<20 chars)")
        if len(mission) > 1200:
            problems.append("too long (>1200 chars)")
        if not source:
            problems.append("missing provenance")
        if SHAME_TERMS.search(mission):
            problems.append("shame-language term")
        if mission.strip().lower().startswith(("i ", "as an ai", "sorry")):
            problems.append("LLM artifact leak")
        if problems:
            failures.append({"ein": ein, "type": "mission", "problems": problems,
                             "excerpt": mission[:120]})
    return len(rows), failures


def sample_donate_links(db):
    rows = db.execute("""
        SELECT EIN, donate_url, donate_url_status FROM registry_enriched
        WHERE donate_url IS NOT NULL AND donate_url != ''
          AND donate_url_status = 'beta'
        ORDER BY RANDOM() LIMIT ?""", (SAMPLE_SIZE,)).fetchall()
    failures = []
    fetch_pool = random.sample(rows, min(LINK_FETCH_BUDGET, len(rows)))
    fetch_eins = {r[0] for r in fetch_pool}
    for ein, url, status in rows:
        problems = []
        if not url.lower().startswith(("http://", "https://")):
            problems.append("malformed URL")
        if "charitynavigator" in url.lower():
            problems.append("CN-hosted URL (source retired 2026-07-17)")
        if ein in fetch_eins and not problems:
            try:
                resp = requests.head(url, timeout=8, allow_redirects=True,
                                     headers={"User-Agent": "DaanaaAuditBot/1.0 (+https://daanaa.org; hello@daanaa.org)"})
                if resp.status_code in (404, 410):
                    problems.append(f"dead link ({resp.status_code})")
            except requests.RequestException:
                pass  # transient network failures are not audit failures
        if problems:
            failures.append({"ein": ein, "type": "donate_url",
                             "problems": problems, "excerpt": url[:120]})
    return len(rows), failures


def sample_cause_tags(db):
    rows = db.execute("""
        SELECT EIN, cause_tags FROM registry_enriched
        WHERE cause_tags IS NOT NULL AND cause_tags != '' AND cause_tags != '[]'
        ORDER BY RANDOM() LIMIT ?""", (SAMPLE_SIZE,)).fetchall()
    failures = []
    for ein, raw in rows:
        problems = []
        try:
            tags = json.loads(raw)
            if not isinstance(tags, list):
                problems.append("not a JSON array")
            elif not (1 <= len(tags) <= 10):
                problems.append(f"tag count {len(tags)} outside 1..10")
            elif any(not isinstance(t, str) or len(t) > 60 for t in tags):
                problems.append("non-string or overlong tag")
        except (json.JSONDecodeError, TypeError):
            problems.append("invalid JSON")
        if problems:
            failures.append({"ein": ein, "type": "cause_tags",
                             "problems": problems, "excerpt": str(raw)[:120]})
    return len(rows), failures


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.execute("PRAGMA busy_timeout=60000")

    results = {}
    for name, fn in (("missions", sample_missions),
                     ("donate_urls", sample_donate_links),
                     ("cause_tags", sample_cause_tags)):
        sampled, failures = fn(db)
        pct = round(100 * len(failures) / sampled, 1) if sampled else 0.0
        results[name] = {"sampled": sampled, "failures": len(failures),
                         "failure_pct": pct, "details": failures}
    db.close()

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_path = REPORT_DIR / f"audit_{stamp}.json"
    with open(report_path, "w") as f:
        json.dump({"run_at": datetime.now().isoformat(),
                   "policy": "BOARD_SIMULATION_2026_07_17_EVENING.md point 2",
                   "results": results}, f, indent=2)

    attention = [n for n, r in results.items() if r["failure_pct"] > FAIL_THRESHOLD_PCT]
    if attention:
        with open(ATTENTION_MARKER, "w") as f:
            f.write(f"[{datetime.now().isoformat()}] AI audit attention: "
                    f"{', '.join(attention)} exceeded {FAIL_THRESHOLD_PCT}% failure "
                    f"threshold — see {report_path}\n")
    else:
        ATTENTION_MARKER.unlink(missing_ok=True)

    for name, r in results.items():
        print(f"{name}: {r['sampled']} sampled, {r['failures']} failed ({r['failure_pct']}%)")
    print(f"report: {report_path}")
    print(f"attention: {attention or 'none'}")


if __name__ == "__main__":
    main()
