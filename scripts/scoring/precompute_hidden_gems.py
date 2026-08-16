#!/usr/bin/env python3
"""
Pre-compute the weekly-rotating Hidden Gems browse pages.

Hidden gems = small, financially healthy, low-profile orgs (is_hidden_gem = 1,
~40k of them). The directory landing surfaces these first. To give every gem a
fair turn in the spotlight — Stewardship P4 (small orgs deserve fairness),
mirroring the cause-spotlight fixed rotation — the order reshuffles every ISO
week with a deterministic seed (stable Mon-Sun, fresh order each week).

Output: precompute_output/browse/hidden_gems/ALL_<page>.json.gz  (same shape as
the rest of the browse cache). Run weekly via cron, then rsync the directory to
the droplet. The droplet serves these as static files, so the landing stays a
static read with zero live-query cost — search speed is unaffected.

Usage:
    python3 scripts/precompute_hidden_gems.py
"""

import gzip
import hashlib
import json
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

# Reuse the canonical row->dict mapper, page size, and DB path (DRY).
from precompute_browse import org_to_dict, PAGE_SIZE, DB_PATH

OUTPUT_DIR = os.path.join(
    os.environ.get("PRECOMPUTE_OUT", "precompute_output"), "browse", "hidden_gems"
)

# Column order MUST match org_to_dict()'s positional mapping in precompute_browse.
SELECT_SQL = """
    SELECT
        EIN, organization_name, NTEE1, NTEECC, CITY, STATE,
        total_revenue, ntee1_percentile, ntee1_total_orgs, source,
        revenue_band, peer_percentile, peer_rank, peer_total, peer_group,
        latest_tax_year, data_source, updated_at, merit_tier, merit_score,
        merit_band, financial_health, months_of_reserve, net_assets,
        total_expenses, employee_count, program_expense_pct,
        mission, mission_source, website, website_status, cause_tags,
        merit_score_v5, merit_health_signal_v5, merit_archetype_v5,
        merit_archetype_v5_label, merit_band_v5, merit_band_v5_label,
        merit_peer_group_v5, merit_peer_count_v5, is_hidden_gem
    FROM registry_enriched
    -- Same deductibility/active gate as the rest of the browse cache: only
    -- surface orgs where donating is currently tax-deductible. Fail closed.
    WHERE is_hidden_gem = 1 AND deductibility = 1 AND org_status = 'active'
"""


def week_seed(d: date | None = None) -> str:
    """ISO year-week, e.g. '2026-W24'. Changes every Monday."""
    y, w, _ = (d or date.today()).isocalendar()
    return f"{y}-W{w:02d}"


def shuffle_key(ein: str, seed: str) -> str:
    """Deterministic per-week ordering key: stable within a week, reshuffles
    when the seed rolls over. Hash so the order is uncorrelated with EIN,
    revenue, or score — every gem gets equal odds of a front-page slot."""
    return hashlib.md5(f"{ein}|{seed}".encode()).hexdigest()


def main():
    seed = week_seed()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(SELECT_SQL).fetchall()
    finally:
        conn.close()

    orgs = [org_to_dict(r) for r in rows]
    orgs.sort(key=lambda o: shuffle_key(o["EIN"], seed))

    out = Path(OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    # Clear stale pages from a previous run (the gem count can shrink).
    for old in out.glob("ALL_*.json.gz"):
        old.unlink()

    num_pages = max(1, (len(orgs) + PAGE_SIZE - 1) // PAGE_SIZE)
    for page in range(1, num_pages + 1):
        chunk = orgs[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]
        payload = {
            "organizations": chunk,
            "total": len(orgs),
            "page": page,
            "per_page": PAGE_SIZE,
            "pages": num_pages,
            "collection": "hidden_gems",
            "rotation_week": seed,
        }
        with gzip.open(out / f"ALL_{page}.json.gz", "wt", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

    print(
        f"[{datetime.now().isoformat()}] hidden_gems: {len(orgs)} orgs, "
        f"{num_pages} pages, week {seed} -> {out}"
    )


if __name__ == "__main__":
    main()
