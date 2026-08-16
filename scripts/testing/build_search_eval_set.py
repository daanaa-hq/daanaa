#!/usr/bin/env python3
"""
scripts/build_search_eval_set.py

Runs every query in data/eval/search_eval_queries.json through the live
semantic search API and emits two files:

  data/eval/search_eval_results_YYYY-MM-DD.csv
      One row per (query × result). Human annotator marks the 'relevant'
      column (1 = relevant, 0 = not relevant). This becomes the labeled set.

  data/eval/search_eval_results_YYYY-MM-DD.json
      Full result objects for programmatic use.

Usage:
    source ~/meritgiving/venv/bin/activate
    python3 scripts/build_search_eval_set.py
    python3 scripts/build_search_eval_set.py --api http://localhost:5000
    python3 scripts/build_search_eval_set.py --top-k 20   # default 10

Annotation instructions (printed at end):
  Open the CSV. For each row, set 'relevant' to:
    1  — this org is a genuinely good match for the query
    0  — this org is irrelevant or only tangentially related
  Save and re-run build_search_eval_set.py --analyze to see Recall@10.
"""

import json
import csv
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error
from datetime import date
from pathlib import Path

BASE_DIR = Path.home() / "meritgiving"
QUERY_FILE = BASE_DIR / "data/eval/search_eval_queries.json"
EVAL_DIR = BASE_DIR / "data/eval"
TODAY = date.today().isoformat()


def fetch_semantic(api_base: str, query: str, top_k: int) -> list[dict]:
    q = urllib.parse.quote_plus(query)
    url = f"{api_base}/api/search/semantic?q={q}&top_k={top_k}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read())
        return data.get("results", [])
    except Exception as e:
        print(f"  WARN: semantic search failed for '{query}': {e}")
        return []


def fetch_keyword(api_base: str, query: str, top_k: int) -> list[dict]:
    q = urllib.parse.quote_plus(query)
    url = f"{api_base}/api/organizations?q={q}&per_page={top_k}&sort=merit_score&order=desc"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read())
        return data.get("organizations", [])
    except Exception as e:
        print(f"  WARN: keyword search failed for '{query}': {e}")
        return []


def analyze(csv_path: Path) -> None:
    """Print metrics from an annotated CSV."""
    rows = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    if not rows:
        print("No rows in CSV.")
        return

    queries = {}
    for row in rows:
        qid = row["query_id"]
        if qid not in queries:
            queries[qid] = {"query": row["query"], "semantic": [], "keyword": []}
        relevant = row.get("relevant", "").strip()
        if relevant not in ("0", "1"):
            continue  # unannotated
        is_rel = int(relevant)
        path = row["search_path"]
        queries[qid][path].append(is_rel)

    print(f"\n{'Query':50s} {'Semantic R@10':>13s} {'Keyword R@10':>12s}")
    print("-" * 78)
    total_s, total_k, count = 0, 0, 0
    for qid, info in sorted(queries.items()):
        q = info["query"][:48]
        s_hits = sum(info["semantic"])
        k_hits = sum(info["keyword"])
        s_label = f"{s_hits}/{len(info['semantic'])}" if info["semantic"] else "—"
        k_label = f"{k_hits}/{len(info['keyword'])}" if info["keyword"] else "—"
        print(f"{q:50s} {s_label:>13s} {k_label:>12s}")
        if info["semantic"]:
            total_s += s_hits / max(len(info["semantic"]), 1)
            count += 1
        if info["keyword"]:
            total_k += k_hits / max(len(info["keyword"]), 1)

    if count:
        print("-" * 78)
        print(f"{'Mean Recall@10 (annotated queries)':50s} {total_s/count:>12.2f}  {total_k/count:>11.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:5000")
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--analyze", metavar="CSV", help="Analyze an annotated CSV instead of running queries")
    args = ap.parse_args()

    if args.analyze:
        analyze(Path(args.analyze))
        return

    with open(QUERY_FILE) as f:
        seed = json.load(f)
    queries = seed["queries"]
    print(f"Loaded {len(queries)} queries from {QUERY_FILE}")

    csv_out = EVAL_DIR / f"search_eval_results_{TODAY}.csv"
    json_out = EVAL_DIR / f"search_eval_results_{TODAY}.json"

    all_rows = []
    csv_rows = []

    for i, q in enumerate(queries, 1):
        qid = q["id"]
        text = q["query"]
        print(f"[{i:2d}/{len(queries)}] {text}")

        sem_results = fetch_semantic(args.api, text, args.top_k)
        kw_results  = fetch_keyword(args.api, text, args.top_k)
        time.sleep(0.1)

        for rank, org in enumerate(sem_results, 1):
            row = {
                "query_id":        qid,
                "query":           text,
                "intent_type":     q.get("intent_type", ""),
                "ntee_hint":       "|".join(q.get("ntee_hint", [])),
                "search_path":     "semantic",
                "rank":            rank,
                "ein":             org.get("EIN", ""),
                "org_name":        org.get("organization_name", ""),
                "city":            org.get("CITY", ""),
                "state":           org.get("STATE", ""),
                "merit_tier":      org.get("merit_tier", ""),
                "merit_score":     org.get("merit_score", ""),
                "total_revenue":   org.get("total_revenue", ""),
                "ntee1":           org.get("NTEE1", ""),
                "relevant":        "",  # human annotates this column
            }
            csv_rows.append(row)
            all_rows.append({**row, "org": org})

        for rank, org in enumerate(kw_results, 1):
            row = {
                "query_id":        qid,
                "query":           text,
                "intent_type":     q.get("intent_type", ""),
                "ntee_hint":       "|".join(q.get("ntee_hint", [])),
                "search_path":     "keyword",
                "rank":            rank,
                "ein":             org.get("EIN", ""),
                "org_name":        org.get("organization_name", ""),
                "city":            org.get("CITY", ""),
                "state":           org.get("STATE", ""),
                "merit_tier":      org.get("merit_tier", ""),
                "merit_score":     org.get("merit_score", ""),
                "total_revenue":   org.get("total_revenue", ""),
                "ntee1":           org.get("NTEE1", ""),
                "relevant":        "",
            }
            csv_rows.append(row)
            all_rows.append({**row, "org": org})

    fieldnames = [
        "query_id", "query", "intent_type", "ntee_hint", "search_path",
        "rank", "ein", "org_name", "city", "state",
        "merit_tier", "merit_score", "total_revenue", "ntee1", "relevant",
    ]
    with open(csv_out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(csv_rows)

    with open(json_out, "w") as f:
        json.dump({"generated": TODAY, "queries": len(queries), "rows": all_rows}, f, indent=2)

    print(f"\nWrote {len(csv_rows)} rows → {csv_out}")
    print(f"Wrote JSON          → {json_out}")
    print()
    print("NEXT STEP — Annotation:")
    print("  Open the CSV in a spreadsheet or editor.")
    print("  For each row, fill the 'relevant' column:")
    print("    1 = this org is a genuine match for the query")
    print("    0 = irrelevant or only tangentially related")
    print("  Annotate at least the top-5 results per query (semantic path).")
    print()
    print("  After annotating, run:")
    print(f"    python3 scripts/build_search_eval_set.py --analyze {csv_out}")
    print("  to see Recall@10 metrics.")


if __name__ == "__main__":
    main()
