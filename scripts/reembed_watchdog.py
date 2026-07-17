#!/usr/bin/env python3
"""
reembed_watchdog.py — Watches for orgs whose embedding is stale or missing
and triggers a full re-embed pass when enough have accumulated.

Stale = stored text_hash differs from current hash (mission was written/updated
after the embedding was built).

Threshold: re-embed when stale+missing count exceeds REEMBED_THRESHOLD.
Runs as a long-lived background process; checks every CHECK_INTERVAL seconds.

Usage:
    python3 scripts/reembed_watchdog.py
    python3 scripts/reembed_watchdog.py --threshold 5000 --interval 600
"""

import sqlite3, subprocess, time, json, argparse, sys, hashlib
import requests
from pathlib import Path
from datetime import datetime

DB_PATH          = Path.home() / "meritgiving/data/merit_registry.db"
LOG_FILE         = Path.home() / "meritgiving/logs/reembed_watchdog.log"
EMBED_SCRIPT     = Path.home() / "meritgiving/scripts/build_org_embeddings.py"
VENV_PYTHON      = Path.home() / "meritgiving/venv/bin/python3"
LLAMA_BIN        = Path.home() / "llama-vulkan/build/bin/llama-server"
EMBED_MODEL      = Path.home() / "models/mxbai-embed-large/gguf/mxbai-embed-large-v1-f16.gguf"
EMBED_PORT       = 11436
EMBED_URL        = f"http://127.0.0.1:{EMBED_PORT}/health"
EMBED_LOG        = Path.home() / "meritgiving/logs/llama-server-embed.log"

REEMBED_THRESHOLD = 10_000   # trigger when this many orgs need re-embedding
CHECK_INTERVAL    = 1800     # seconds between checks (30 min)

_NTEE_LABELS = {
    "A": "arts culture humanities", "B": "education", "C": "environment",
    "D": "animal welfare", "E": "health care", "F": "mental health counseling",
    "G": "disease research medical", "H": "medical research",
    "I": "crime legal justice", "J": "employment job training",
    "K": "food agriculture nutrition", "L": "housing shelter",
    "M": "public safety disaster", "N": "recreation sports leisure",
    "O": "youth development", "P": "human services family",
    "Q": "international foreign affairs", "R": "civil rights social action",
    "S": "community improvement", "T": "philanthropy voluntarism grantmaking",
    "U": "science technology research", "V": "social science",
    "W": "public benefit society", "X": "religion faith spiritual",
    "Y": "mutual benefit member organizations", "Z": "unknown",
}


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def _build_text(row: dict) -> str:
    parts = []
    name = (row.get("organization_name") or "").strip()
    if name:
        parts.append(name)
    label = _NTEE_LABELS.get(row.get("NTEE1") or "")
    if label:
        parts.append(label)
    tags_raw = row.get("cause_tags") or ""
    if tags_raw:
        try:
            tags = json.loads(tags_raw)
            if isinstance(tags, list) and tags:
                parts.append(", ".join(str(t) for t in tags[:6]))
        except Exception:
            if tags_raw.strip():
                parts.append(tags_raw.strip()[:120])
    mission = (row.get("mission") or "").strip()
    if mission and len(mission) > 10:
        parts.append(mission[:400])
    city  = (row.get("CITY") or "").strip()
    state = (row.get("STATE") or "").strip()
    if city and state:
        parts.append(f"{city}, {state}")
    elif state:
        parts.append(state)
    return " | ".join(parts)


def _text_hash(text: str) -> str:
    return hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()[:8]


def count_stale(conn: sqlite3.Connection) -> tuple[int, int]:
    """Returns (missing_count, stale_count)."""
    # Missing: have a mission, not in org_embeddings at all
    missing = conn.execute("""
        SELECT COUNT(*) FROM registry_enriched r
        WHERE r.mission IS NOT NULL AND r.mission != ''
          AND r.merit_score IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM org_embeddings e WHERE e.ein = r.EIN)
    """).fetchone()[0]

    # Stale: in org_embeddings but text_hash has changed (mission updated since embed)
    # Sample 5000 to estimate — full scan is slow on 1.8M rows
    rows = conn.execute("""
        SELECT r.EIN, r.organization_name, r.NTEE1, r.cause_tags,
               r.CITY, r.STATE, r.mission, e.text_hash
        FROM registry_enriched r
        JOIN org_embeddings e ON e.ein = r.EIN
        WHERE r.mission IS NOT NULL AND r.mission != ''
          AND r.merit_score IS NOT NULL
        ORDER BY RANDOM() LIMIT 5000
    """).fetchall()
    cols = ["EIN", "organization_name", "NTEE1", "cause_tags", "CITY", "STATE", "mission", "stored_hash"]
    sample_stale = 0
    for row in rows:
        d = dict(zip(cols, row))
        current_hash = _text_hash(_build_text(d))
        if current_hash != d["stored_hash"]:
            sample_stale += 1

    # Extrapolate from sample to full embedded population
    total_embedded = conn.execute("SELECT COUNT(*) FROM org_embeddings").fetchone()[0]
    stale_rate = sample_stale / max(len(rows), 1)
    stale_estimate = int(stale_rate * total_embedded)

    return missing, stale_estimate


def embed_server_running() -> bool:
    try:
        r = requests.get(EMBED_URL, timeout=3)
        return r.json().get("status") == "ok"
    except Exception:
        return False


def start_embed_server() -> subprocess.Popen:
    log("Starting mxbai-embed-large llama-server on port 11436...")
    proc = subprocess.Popen(
        [
            str(LLAMA_BIN),
            "-m", str(EMBED_MODEL),
            "--port", str(EMBED_PORT),
            "--host", "127.0.0.1",
            "-ngl", "99",
            "--device", "Vulkan1",
            "--ctx-size", "8192",
            "--batch-size", "512",
            "-np", "4",
            "--embeddings",
        ],
        stdout=open(EMBED_LOG, "a"),
        stderr=subprocess.STDOUT,
    )
    # Wait for server to become healthy
    for _ in range(60):
        time.sleep(2)
        if embed_server_running():
            log(f"Embed server up (PID {proc.pid})")
            return proc
    log("ERROR: embed server did not start in time")
    proc.terminate()
    return None


def run_reembed(max_retries: int = 5):
    """Run embedding job with exponential backoff retry on database locks.

    Incremental by design: NO --overwrite, so build_org_embeddings skips every
    already-embedded EIN (it is resumable) and only embeds the missing ones.
    This is the whole point of the watchdog — keep newly discovered orgs
    embedded — without ever re-doing the full corpus. A true full refresh
    (--overwrite) belongs in a deliberate manual/weekly run, not this loop.
    """
    log("Launching build_org_embeddings.py --all-orgs (incremental, missing only) ...")

    for attempt in range(1, max_retries + 1):
        result = subprocess.run(
            [
                str(VENV_PYTHON),
                str(EMBED_SCRIPT),
                "--all-orgs",
                "--model", "mxbai-embed-large",
                "--dim", "1024",
                "--workers", "2",
                "--vulkan",
            ],
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        last_lines = "\n".join(output.strip().splitlines()[-5:])

        # Check if database was locked
        if "database is locked" in output.lower():
            if attempt < max_retries:
                wait_time = 2 ** attempt  # 2, 4, 8, 16, 32 seconds
                log(f"Attempt {attempt}: database locked — retrying in {wait_time}s")
                time.sleep(wait_time)
            else:
                log(f"Attempt {attempt}/{max_retries}: database locked (giving up)")
                log(f"Embed job output:\n{last_lines}")
                return False
        else:
            log(f"Embed job finished:\n{last_lines}")
            return result.returncode == 0

    return False


def main(threshold: int, interval: int):
    log(f"reembed_watchdog started — threshold={threshold:,} interval={interval}s")
    conn = sqlite3.connect(DB_PATH, timeout=30)

    while True:
        missing, stale = count_stale(conn)
        total = missing + stale
        log(f"Status: {missing:,} missing embeddings, ~{stale:,} stale — total {total:,}")

        # Trigger on the EXACT missing count only, never the sampled `stale`
        # estimate. `stale` is extrapolated from a 5,000-row hash-mismatch
        # sample × the full 2M corpus, so a handful of edited missions inflates
        # to thousands and crosses the threshold — which then launched a full
        # `--all-orgs --overwrite` re-embed of 2M already-embedded orgs, pinning
        # the shared GPU (2026-07-16 capacity audit). Missing = real gaps that
        # genuinely need work; the incremental job (no --overwrite) only touches
        # those. Stale embeddings (mission text changed) are refreshed by the
        # weekly overnight_pipeline, not this hot-path watchdog.
        if missing >= threshold:
            log(f"Threshold {threshold:,} reached ({missing:,} missing) — triggering incremental embed")
            server_proc = None
            server_was_running = embed_server_running()

            if not server_was_running:
                server_proc = start_embed_server()
                if server_proc is None:
                    log("ERROR: embed server failed to start")
                    time.sleep(interval)
                    continue

            # Run reembed (with retries for database locks).
            # Server stays running even if reembed fails — Phase 4 still needs it.
            success = run_reembed(max_retries=5)

            if not success:
                log("WARNING: Embed job did not complete successfully, but keeping server running for Phase 4")

            if server_proc is not None:
                log("Embed server will continue running (managed by gpu_night.sh)")
        else:
            log(f"Below threshold — sleeping {interval}s")

        time.sleep(interval)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=int, default=REEMBED_THRESHOLD)
    ap.add_argument("--interval",  type=int, default=CHECK_INTERVAL)
    args = ap.parse_args()
    main(args.threshold, args.interval)
