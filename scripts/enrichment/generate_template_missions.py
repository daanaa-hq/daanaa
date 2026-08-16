#!/usr/bin/env python3
"""
Fast template-based mission generation for IRS_BMF-only orgs that have
no financial data, no web content — just name, NTEE, city, state.
Uses NTEE category labels to produce a one-sentence description.
Instant: ~100K orgs/min on CPU. No GPU needed.
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/merit_registry.db")

NTEE_LABELS = {
    "A": "arts, culture, and humanities",
    "B": "education and learning",
    "C": "environmental conservation",
    "D": "animal welfare",
    "E": "healthcare and medical services",
    "F": "mental health and counseling",
    "G": "disease research and medical advocacy",
    "H": "health research",
    "I": "crime prevention, legal aid, and justice",
    "J": "employment and workforce development",
    "K": "food, agriculture, and nutrition",
    "L": "housing and shelter",
    "M": "public safety and disaster relief",
    "N": "recreation, sports, and youth activities",
    "O": "youth development and mentorship",
    "P": "human services and social support",
    "Q": "international affairs and global development",
    "R": "civil rights and social advocacy",
    "S": "community development and civic engagement",
    "T": "philanthropy and grantmaking",
    "U": "science and technology",
    "V": "social sciences research",
    "W": "public benefit and policy",
    "X": "religious and spiritual development",
    "Y": "mutual aid and membership benefit",
    "Z": "general nonprofit activities",
}


def make_mission(name: str, ntee1: str, city: str, state: str) -> str:
    label = NTEE_LABELS.get((ntee1 or "").upper(), "community services")
    loc = f"{city.title()}, {state}" if city and state else (state or "")
    if loc:
        return f"{name} is a nonprofit organization based in {loc} that advances {label}."
    return f"{name} is a nonprofit organization that advances {label}."


def main():
    print(f"[{datetime.now():%H:%M:%S}] Generating template missions for name-only orgs (IRS_BMF + bmf_stub)...")
    con = sqlite3.connect(DB_PATH)

    rows = con.execute("""
        SELECT EIN, organization_name, NTEE1, CITY, STATE
        FROM registry_enriched
        WHERE source IN ('IRS_BMF', 'bmf_stub')
          AND (mission IS NULL OR mission = '')
    """).fetchall()

    print(f"  Orgs to update: {len(rows):,}")

    batch = []
    for ein, name, ntee1, city, state in rows:
        if not name:
            continue
        mission = make_mission(name, ntee1, city, state)
        batch.append((mission, "template_ntee", ein))
        if len(batch) >= 10_000:
            con.executemany(
                "UPDATE registry_enriched SET mission=?, mission_source=? WHERE EIN=?",
                batch
            )
            con.commit()
            batch = []

    if batch:
        con.executemany(
            "UPDATE registry_enriched SET mission=?, mission_source=? WHERE EIN=?",
            batch
        )
        con.commit()

    after = con.execute(
        "SELECT COUNT(*) FROM registry_enriched WHERE mission IS NOT NULL AND mission != ''"
    ).fetchone()[0]
    con.close()

    print(f"[{datetime.now():%H:%M:%S}] Done! Orgs with missions: {after:,}")


if __name__ == "__main__":
    main()
