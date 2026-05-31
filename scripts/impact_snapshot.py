#!/usr/bin/env python3
"""
impact_snapshot.py — record a dated, privacy-safe snapshot of Daanaa's impact metrics
into the impact_snapshots table, so we build a growing time-series for JOURNEY.md and
the eventual public impact page.

PRIVACY: this records only aggregate counts about CONTENT (what the AI built) and ORG
actions (claims, corrections). It never reads, stores, or counts any donor's identity
or giving activity. See PRIVACY-INVARIANTS.md. No donor surveillance, by principle.

Tiers captured here:
  Tier 1 (supply/content) — orgs indexed, AI missions, cause-tagged, scored, hidden gems, donate paths
  Tier 2 (org-side realized) — pages claimed, missions org-edited, waitlist interest

Run weekly (cron):
  0 5 * * 1  cd ~/meritgiving && venv/bin/python3 scripts/impact_snapshot.py >> logs/impact.log 2>&1
"""

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

DB = Path.home() / "meritgiving" / "data" / "merit_registry.db"


def col_exists(cur, table, col):
    return any(r[1] == col for r in cur.execute(f"PRAGMA table_info({table})").fetchall())


def table_exists(cur, table):
    return cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS impact_snapshots (
            snapshot_date  TEXT PRIMARY KEY,
            orgs_indexed   INTEGER,
            ai_missions    INTEGER,
            cause_tagged   INTEGER,
            scored         INTEGER,
            hidden_gems    INTEGER,
            donate_paths   INTEGER,
            orgs_claimed   INTEGER,
            waitlist       INTEGER,
            handoffs       INTEGER,
            created_at     TEXT
        )
    """)
    if not col_exists(cur, "impact_snapshots", "handoffs"):
        cur.execute("ALTER TABLE impact_snapshots ADD COLUMN handoffs INTEGER")

    def one(sql, default=0):
        try:
            v = cur.execute(sql).fetchone()
            return v[0] if v and v[0] is not None else default
        except sqlite3.Error:
            return default

    metrics = {
        # Tier 1 — content / supply (about what the AI built, not about people)
        "orgs_indexed": one("SELECT COUNT(*) FROM registry_enriched"),
        "ai_missions":  one("SELECT COUNT(*) FROM registry_enriched WHERE mission_source LIKE 'ai_%'"),
        "cause_tagged": one("SELECT COUNT(*) FROM registry_enriched WHERE cause_tags_source='ai_generated'"),
        "scored":       one("SELECT COUNT(*) FROM registry_enriched WHERE peer_percentile IS NOT NULL"),
        "hidden_gems":  one("SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1"),
        "donate_paths": one("SELECT COUNT(*) FROM registry_enriched WHERE donate_url_status='beta'"),
        # Tier 2 — org-side realized signals (org actions, never donor data)
        "orgs_claimed": one("SELECT COUNT(*) FROM org_claims WHERE claim_status IN ('active','verified')")
                        if table_exists(cur, "org_claims") else 0,
        "waitlist":     one("SELECT COUNT(*) FROM waitlist") if table_exists(cur, "waitlist") else 0,
        # Tier 3 — anonymous realized donor signal (count of give hand-offs, no identity)
        "handoffs":     one("SELECT COALESCE(SUM(count),0) FROM donate_handoffs")
                        if table_exists(cur, "donate_handoffs") else 0,
    }

    today = date.today().isoformat()
    cur.execute("""
        INSERT OR REPLACE INTO impact_snapshots
          (snapshot_date, orgs_indexed, ai_missions, cause_tagged, scored,
           hidden_gems, donate_paths, orgs_claimed, waitlist, handoffs, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (today, metrics["orgs_indexed"], metrics["ai_missions"], metrics["cause_tagged"],
          metrics["scored"], metrics["hidden_gems"], metrics["donate_paths"],
          metrics["orgs_claimed"], metrics["waitlist"], metrics["handoffs"],
          datetime.now(timezone.utc).isoformat()))
    conn.commit()

    # Report this snapshot + delta vs the previous one (the growth curve)
    prev = cur.execute(
        "SELECT * FROM impact_snapshots WHERE snapshot_date < ? ORDER BY snapshot_date DESC LIMIT 1",
        (today,)
    ).fetchone()
    cols = [d[0] for d in cur.description]
    prev_map = dict(zip(cols, prev)) if prev else {}

    print(f"=== Impact snapshot {today} ===")
    for k in ("orgs_indexed", "ai_missions", "cause_tagged", "scored",
              "hidden_gems", "donate_paths", "orgs_claimed", "waitlist", "handoffs"):
        now = metrics[k]
        delta = now - prev_map.get(k, now) if prev_map else None
        d = f"  ({delta:+,} since {prev_map['snapshot_date']})" if (prev_map and delta) else ""
        print(f"  {k:<14} {now:>10,}{d}")

    conn.close()


if __name__ == "__main__":
    main()
