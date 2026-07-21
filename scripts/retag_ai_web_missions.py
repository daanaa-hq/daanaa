#!/usr/bin/env python3
"""Re-tag orgs whose mission was already upgraded to ai_web but whose
cause_tags were never re-derived from it (still holding stale/generic tags).

Scoped subset of retag_from_mission.py's population: mission_source='ai_web'
AND cause_tags_source != 'ai_mission'. Reuses the same LLM call, vocabulary,
and controlled-tag logic — just targeted at the smaller, safer population
first (2026-07-20, following the KWA Foundation tag-drift discovery).

Usage:
  python3 scripts/retag_ai_web_missions.py --sample 20 --dry-run
  python3 scripts/retag_ai_web_missions.py --workers 4
"""
import argparse
import json
import os
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))
from retag_from_mission import _call_llm

DB_PATH = os.environ.get("DB_PATH", os.path.expanduser("~/meritgiving/data/merit_registry.db"))


def run(limit=None, workers=4, sample=None, dry_run=False):
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    n = sample or limit
    q = """
        SELECT EIN, organization_name, NTEE1, mission, cause_tags
        FROM registry_enriched
        WHERE mission_source = 'ai_web'
          AND COALESCE(cause_tags_source,'') != 'ai_mission'
        ORDER BY (merit_score IS NULL) ASC, merit_score DESC
    """
    if n:
        q += f" LIMIT {int(n)}"
    rows = [dict(r) for r in conn.execute(q).fetchall()]
    total = len(rows)
    print(f"Re-tagging {total:,} ai_web-mission orgs  workers={workers}"
          f"{'  [DRY RUN]' if dry_run else ''}", flush=True)

    done = err = 0
    write_buf = []

    def process(org):
        tags = _call_llm(org)
        return org, tags

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(process, o) for o in rows]
        for fut in as_completed(futures):
            org, tags = fut.result()
            if not tags:
                err += 1
                continue
            done += 1
            if dry_run:
                try:
                    old_list = json.loads(org.get("cause_tags") or "[]")
                except Exception:
                    old_list = []
                print(f"\n  {org['organization_name'][:48]}  (NTEE {org.get('NTEE1')})")
                print(f"    mission: {(org.get('mission') or '')[:90].strip()}")
                print(f"    OLD: {old_list}")
                print(f"    NEW: {tags}")
            else:
                write_buf.append((json.dumps(tags), org["EIN"]))
                if len(write_buf) >= 200:
                    conn.executemany(
                        "UPDATE registry_enriched SET cause_tags=?, cause_tags_source='ai_mission' WHERE EIN=?",
                        write_buf)
                    conn.commit()
                    write_buf.clear()
                    print(f"  [{done:,}/{total:,}] {err} errors", flush=True)

    if write_buf and not dry_run:
        conn.executemany(
            "UPDATE registry_enriched SET cause_tags=?, cause_tags_source='ai_mission' WHERE EIN=?",
            write_buf)
        conn.commit()
    print(f"\nDone. tagged={done:,}  errors={err:,}", flush=True)
    conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--sample", type=int, help="process only N orgs (for preview)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true", help="print before/after, write nothing")
    args = ap.parse_args()
    run(limit=args.limit, workers=args.workers, sample=args.sample, dry_run=args.dry_run)
