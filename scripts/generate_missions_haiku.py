#!/usr/bin/env python3
"""
scripts/generate_missions_haiku.py

Supplement local Qwen mission generation with Claude Haiku for NTEE-only orgs
(no page_cache entry — those are reserved for Qwen's ai_web pass).

Targets: merit_score IS NOT NULL, no mission, no cached web page.
Order:   merit_score DESC — highest-visibility orgs get missions first.
Source:  mission_source = 'ai_haiku'

Usage:
    python3 scripts/generate_missions_haiku.py
    python3 scripts/generate_missions_haiku.py --budget 15 --workers 10
    python3 scripts/generate_missions_haiku.py --limit 1000   # test run
"""

import sqlite3, json, time, argparse, re, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import anthropic

DB_PATH   = Path.home() / "meritgiving/data/merit_registry.db"
MODEL     = "claude-haiku-4-5-20251001"
BATCH     = 20
COST_IN   = 0.80  / 1_000_000   # $/input token
COST_OUT  = 4.00  / 1_000_000   # $/output token

_write_lock  = Lock()
_cost_lock   = Lock()
_written     = 0
_errors      = 0
_total_cost  = 0.0

_NTEE_LABELS = {
    "A":"arts, culture, and humanities","B":"education",
    "C":"environment and conservation","D":"animal welfare",
    "E":"health care","F":"mental health and counseling",
    "G":"disease research and medical services","H":"medical research",
    "I":"crime, legal, and justice","J":"employment and job training",
    "K":"food, agriculture, and nutrition","L":"housing and shelter",
    "M":"public safety and disaster relief","N":"recreation, sports, and leisure",
    "O":"youth development","P":"human services",
    "Q":"international and foreign affairs","R":"civil rights and social action",
    "S":"community improvement","T":"philanthropy and grantmaking",
    "U":"science and technology","V":"social science",
    "W":"public benefit","X":"religion and faith",
    "Y":"mutual benefit and membership","Z":"general nonprofit",
}

_FEW_SHOT = """\
Write one-sentence mission descriptions for nonprofit organizations.

Examples:
name="Springfield Meals on Wheels" sector="human services" location="Springfield, IL"
→ Delivers hot meals to homebound elderly and disabled residents across Springfield.

name="Boys & Girls Club of Greater Milwaukee" sector="youth development" location="Milwaukee, WI"
→ Provides after-school programs, mentorship, and safe spaces for young people in Milwaukee.

name="Trout Unlimited — Rocky Mountain Chapter" sector="environment" location="Denver, CO"
→ Protects and restores cold-water fisheries and trout habitat across the Rocky Mountain region.

name="St. Vincent de Paul Society of Omaha" sector="human services" location="Omaha, NE"
→ Operates food pantries, clothing assistance, and emergency financial aid for people in need in Omaha.

Rules:
- Read the NAME first — it usually tells you what the org does.
- One sentence, present tense.
- Do NOT start with the org name.
- Do NOT use: "dedicated to", "strives to", "committed to", "passionate about", "aims to", "is a nonprofit", "was founded".
- Do NOT invent statistics, dollar amounts, or named programs.
- If the name is an acronym or person's name, infer from sector + location.
"""


def _build_prompt(batch: list[dict]) -> str:
    lines = []
    for org in batch:
        ntee  = _NTEE_LABELS.get(org.get("NTEE1") or "Z", "general nonprofit")
        city  = (org.get("CITY") or "").title()
        state = org.get("STATE") or ""
        lines.append(
            f'  {{"ein": "{org["EIN"]}", "name": "{org["organization_name"]}", '
            f'"sector": "{ntee}", "location": "{city}, {state}"}}'
        )
    orgs_json = "[\n" + ",\n".join(lines) + "\n]"
    return (
        _FEW_SHOT + "\n"
        "Now write mission sentences for these organizations. "
        'Return ONLY a JSON array: [{"ein": "...", "mission": "..."}]\n\n'
        "Organizations:\n" + orgs_json
    )


def _call_haiku(client: anthropic.Anthropic, batch: list[dict]) -> tuple[dict[str, str], float]:
    """Returns ({ein: mission}, cost_usd)."""
    prompt = _build_prompt(batch)
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=max(400, 80 * len(batch)),
            messages=[{"role": "user", "content": prompt}],
        )
        content = msg.content[0].text if msg.content else ""
        cost = (msg.usage.input_tokens * COST_IN +
                msg.usage.output_tokens * COST_OUT)
        m = re.search(r"\[.*\]", content, re.DOTALL)
        parsed = json.loads(m.group() if m else content)
        if isinstance(parsed, dict):
            parsed = next((v for v in parsed.values() if isinstance(v, list)), [])
        results = {
            item["ein"]: item["mission"].strip()
            for item in parsed
            if "ein" in item and "mission" in item and item["mission"].strip()
        }
        return results, cost
    except Exception:
        return {}, 0.0


def _write_batch(results: dict[str, str], conn: sqlite3.Connection, batch_size: int):
    global _written, _errors
    if not results:
        with _write_lock:
            _errors += batch_size
        return
    with _write_lock:
        conn.executemany(
            "UPDATE registry_enriched SET mission=?, mission_source='ai_haiku' WHERE EIN=?",
            [(mission, ein) for ein, mission in results.items()]
        )
        conn.commit()
        _written += len(results)
        _errors  += batch_size - len(results)


def run(budget: float, workers: int, limit: int | None):
    # Load from .env directly — env var may be set to a placeholder in shell config
    env_file = Path.home() / "meritgiving/.env"
    api_key = None
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break
    if not api_key or not api_key.startswith("sk-"):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    client = anthropic.Anthropic(api_key=api_key)

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(f"""
        SELECT re.EIN, re.organization_name, re.NTEE1, re.CITY, re.STATE
        FROM registry_enriched re
        WHERE (re.mission IS NULL OR re.mission = '')
          AND re.merit_score IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM page_cache pc
              WHERE pc.ein = re.EIN AND pc.html_gz IS NOT NULL
          )
        ORDER BY re.merit_score DESC
        {'LIMIT ' + str(limit) if limit else ''}
    """).fetchall()
    conn.close()

    total = len(rows)
    if not total:
        print("Nothing to generate.", flush=True)
        return

    batches = [rows[i:i+BATCH] for i in range(0, total, BATCH)]
    print(
        f"Haiku mission generation — {total:,} orgs  {len(batches):,} batches  "
        f"budget=${budget:.2f}  workers={workers}  model={MODEL}",
        flush=True
    )

    start = time.time()
    global _total_cost

    def process(batch):
        global _total_cost
        with _cost_lock:
            if _total_cost >= budget:
                return  # budget exhausted
        tconn = sqlite3.connect(DB_PATH, timeout=30)
        tconn.row_factory = sqlite3.Row
        try:
            results, cost = _call_haiku(client, [dict(r) for r in batch])
            with _cost_lock:
                _total_cost += cost
            _write_batch(results, tconn, len(batch))
        finally:
            tconn.close()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(process, b) for b in batches]
        for fut in as_completed(futs):
            try:
                fut.result()
            except Exception as exc:
                print(f"\n  [error] {exc}", flush=True)
            elapsed = time.time() - start
            rate    = _written / elapsed if elapsed > 0 else 0
            pct     = (_written + _errors) / total * 100
            eta     = (total - _written - _errors) / rate / 60 if rate > 0 else 0
            print(
                f"\r  [{pct:5.1f}%] {_written:,} written  {_errors:,} errors  "
                f"${_total_cost:.2f}  {rate:.0f}/sec  ETA {eta:.0f}m",
                end="", flush=True
            )
            if _total_cost >= budget:
                print(f"\n  Budget cap ${budget:.2f} reached — stopping.", flush=True)
                pool.shutdown(wait=False, cancel_futures=True)
                break

    elapsed = time.time() - start
    print(
        f"\n\nDone in {elapsed/60:.1f} min — "
        f"{_written:,} missions written  {_errors:,} errors  "
        f"${_total_cost:.3f} spent",
        flush=True
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget",  type=float, default=15.0)
    ap.add_argument("--workers", type=int,   default=10)
    ap.add_argument("--limit",   type=int,   default=None)
    args = ap.parse_args()
    run(budget=args.budget, workers=args.workers, limit=args.limit)
