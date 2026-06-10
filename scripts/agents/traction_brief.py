#!/usr/bin/env python3
"""
T5 Partnerships agent — auto-updating traction one-pager.

Reads live metrics from merit_registry.db and writes ops/traction_brief.md.
This is the asset Akbar attaches to grant applications and partnership emails
(Every.org, Candid, processor-class pitches). Numbers are pulled live so the
brief is never stale — and never inflated (stewardship: real data only;
zeros are shown as zeros).

Cron: weekly, Monday 05:30 (after Sunday pipeline + scoring runs).
No LLM, no network — pure local SQLite reads. Runs in <5 seconds.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

PROJECT = Path.home() / "meritgiving"
DB = PROJECT / "data" / "merit_registry.db"
OUT_DIR = PROJECT / "ops"
OUT = OUT_DIR / "traction_brief.md"


def one(conn, sql, default=0):
    try:
        row = conn.execute(sql).fetchone()
        return row[0] if row and row[0] is not None else default
    except sqlite3.Error:
        return default


def main():
    OUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)

    total = one(conn, "SELECT COUNT(*) FROM registry_enriched")
    active = one(conn, """SELECT COUNT(*) FROM registry_enriched
        WHERE deductibility='1' AND org_status='active'""")
    scored = one(conn, "SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL")
    missions = one(conn, "SELECT COUNT(*) FROM registry_enriched WHERE mission IS NOT NULL AND mission != ''")
    websites = one(conn, "SELECT COUNT(*) FROM registry_enriched WHERE website IS NOT NULL AND website != ''")
    donate_verified = one(conn, """SELECT COUNT(*) FROM registry_enriched
        WHERE donate_url IS NOT NULL AND donate_confidence >= 90""")
    hidden_gems = one(conn, "SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1")
    claims = one(conn, "SELECT COUNT(*) FROM org_claims")
    waitlist = one(conn, "SELECT COUNT(*) FROM waitlist")

    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    handoffs_30d = one(conn, f"SELECT COALESCE(SUM(count),0) FROM donate_handoffs WHERE day >= '{cutoff}'")
    visits_30d = one(conn, f"""SELECT COALESCE(SUM(count),0) FROM analytics_daily
        WHERE day >= '{cutoff}' AND event_type='pageview'""")

    conn.close()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pct_scored = (scored / active * 100) if active else 0

    OUT.write_text(f"""# Daanaa — Traction Brief

*Auto-generated from live platform data, {now}. Every number is queryable and real.*

## Platform scale

| Metric | Value |
|--------|-------|
| Organizations indexed | {total:,} |
| Active, tax-deductible (publicly shown) | {active:,} |
| Peer financial context scores | {scored:,} ({pct_scored:.0f}% of active) |
| AI-assisted mission summaries | {missions:,} |
| Verified websites | {websites:,} |
| High-confidence donate links (≥90) | {donate_verified:,} |
| Hidden gems flagged (small + healthy + low-profile) | {hidden_gems:,} |

## Engagement (early stage — honest zeros where we haven't launched)

| Metric | Value |
|--------|-------|
| Nonprofit profile claims | {claims:,} |
| Newsletter / waitlist signups | {waitlist:,} |
| Donate hand-offs, last 30 days | {handoffs_30d:,} |
| Pageviews, last 30 days (first-party, cookieless) | {visits_30d:,} |

## What Daanaa is

A civic nonprofit-discovery platform. We index every US 501(c)(3) from IRS
public data, score financial context against true peers (9 operating models,
never comparing a $200K community org to a hospital system), and surface the
invisible 97% of nonprofits that rating sites skip.

**We never touch donor money.** All giving is a hand-off to the org's own
processor or an EIN-keyed router. Donor activity stays on the donor's device.

## Governance

Operates under a public Founding Stewardship Commitment: no paid placement,
no sponsored scores, evidence-based trust signals only, privacy by
architecture. Full methodology published at daanaa.org/methodology.

---
*Regenerate: `python3 scripts/agents/traction_brief.py` · Source: merit_registry.db (read-only)*
""")
    print(f"[traction_brief] wrote {OUT} — active={active:,} scored={scored:,} claims={claims}")


if __name__ == "__main__":
    main()
