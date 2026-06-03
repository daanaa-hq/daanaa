#!/usr/bin/env python3
"""Re-derive cause_tags from the generated MISSION (not the IRS NTEE code).

Why: existing cause_tags were generated from NTEE codes, which the IRS often
miscodes (e.g. an education/anti-poverty academy coded NTEE1=E "Health" got
tagged health/healthcare). Now that ~630K orgs have accurate plain-language
missions, the mission is the better signal. This picks 3-5 tags from a clean
controlled vocabulary based on the mission text (+ NTEE as a hint).

Local Qwen on llama-server (port 11437), same model as mission generation.
Resumable: marks cause_tags_source='ai_mission' and skips already-done orgs.

Usage:
  python3 scripts/retag_from_mission.py --sample 100 --dry-run   # preview, no writes
  python3 scripts/retag_from_mission.py --workers 6              # full run, resumable
  python3 scripts/retag_from_mission.py --limit 5000 --workers 6 # bounded batch
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

DB_PATH = os.environ.get("DB_PATH", os.path.expanduser("~/meritgiving/data/merit_registry.db"))
GEN_URL = "http://127.0.0.1:11437/v1/chat/completions"
MODEL   = "Qwen2.5-14B-Instruct-Q4_K_M"

# Controlled vocabulary — tags must come from this list so they stay clean and
# searchable. Grouped for readability; the model sees a flat list.
VOCAB = [
    # education
    "education", "k-12 education", "higher education", "early childhood",
    "scholarships", "literacy", "vocational training", "student support",
    # arts & culture
    "arts", "music", "theater", "visual arts", "museums", "libraries",
    "cultural heritage", "historical preservation",
    # health
    "health", "healthcare", "mental health", "disease research", "public health",
    "medical access", "addiction recovery", "disability support",
    # human services
    "human services", "food security", "housing", "homelessness", "poverty relief",
    "family services", "youth development", "senior services", "crisis support",
    "refugee support", "veterans",
    # animals & environment
    "animal welfare", "wildlife", "conservation", "environment", "climate", "sustainability",
    # community
    "community development", "economic development", "civic engagement", "neighborhood improvement",
    # faith
    "faith", "religious", "spiritual",
    # international
    "international development", "global health", "humanitarian aid",
    # justice & rights
    "civil rights", "social justice", "legal aid", "advocacy",
    # recreation
    "sports", "recreation",
    # science & tech
    "science", "technology", "research",
    # philanthropy & safety
    "grantmaking", "volunteering", "disaster relief", "public safety",
]
VOCAB_SET = set(VOCAB)

NTEE_HINT = {
    "A": "arts/culture", "B": "education", "C": "environment", "D": "animals",
    "E": "health", "F": "mental health", "G": "disease/medical", "H": "medical research",
    "I": "crime/legal", "J": "employment", "K": "food/agriculture", "L": "housing",
    "M": "public safety/disaster", "N": "recreation/sports", "O": "youth development",
    "P": "human services", "Q": "international", "R": "civil rights", "S": "community",
    "T": "philanthropy", "U": "science/tech", "V": "social science", "W": "public benefit",
    "X": "religion", "Y": "mutual benefit",
}

SYSTEM = (
    "You tag U.S. nonprofits by cause. You are given an organization's mission and you "
    "choose the tags that genuinely describe what it does. Aim for about 5 tags for good "
    "search coverage, but only use tags that truly fit: use 3 or 4 if that is all that "
    "applies, and up to 7. Never add a weak or irrelevant tag just to reach a number. "
    "Choose ONLY from the provided tag list. Prefer the mission over the IRS "
    "category hint when they disagree. Order the tags most-relevant first. "
    "Output ONLY a JSON array of tag strings, nothing else."
)


def _build_prompt(org: dict) -> str:
    mission = (org.get("mission") or "").strip()[:600]
    hint = NTEE_HINT.get((org.get("NTEE1") or "").strip().upper(), "")
    return (
        f"Organization: {org.get('organization_name','')}\n"
        f"IRS category hint (may be wrong): {hint or 'unknown'}\n"
        f"Mission: {mission}\n\n"
        f"Allowed tags: {', '.join(VOCAB)}\n\n"
        f"Return a JSON array of the genuinely fitting tags (aim for ~5, but 3 to 7 is fine), most relevant first."
    )


def _call_llm(org: dict) -> list[str] | None:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": _build_prompt(org)},
        ],
        "temperature": 0.1,
        "max_tokens": 110,
    }
    try:
        r = requests.post(GEN_URL, json=payload, timeout=120)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1:
            return None
        raw = json.loads(text[start:end + 1])
        # keep only valid vocab tags, dedupe, cap at 5
        seen, out = set(), []
        for t in raw:
            t = str(t).strip().lower()
            if t in VOCAB_SET and t not in seen:
                seen.add(t); out.append(t)
            if len(out) >= 7:
                break
        return out or None
    except Exception:
        return None


def run(limit=None, workers=6, sample=None, dry_run=False):
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    n = sample or limit
    q = """
        SELECT EIN, organization_name, NTEE1, mission, cause_tags
        FROM registry_enriched
        WHERE mission IS NOT NULL AND mission != ''
          AND COALESCE(cause_tags_source,'') != 'ai_mission'
        ORDER BY (merit_score IS NULL) ASC, merit_score DESC
    """
    if n:
        q += f" LIMIT {int(n)}"
    rows = [dict(r) for r in conn.execute(q).fetchall()]
    total = len(rows)
    print(f"Re-tagging {total:,} orgs from mission  model={MODEL}  workers={workers}"
          f"{'  [DRY RUN]' if dry_run else ''}", flush=True)

    done = err = 0
    write_buf: list[tuple] = []

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
            old = org.get("cause_tags")
            if dry_run:
                try:
                    old_list = json.loads(old) if old else []
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
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--dry-run", action="store_true", help="print before/after, write nothing")
    args = ap.parse_args()
    run(limit=args.limit, workers=args.workers, sample=args.sample, dry_run=args.dry_run)
