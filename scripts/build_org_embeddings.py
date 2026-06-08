#!/usr/bin/env python3
"""
scripts/build_org_embeddings.py

Embed every scored org via local Ollama. Default: nomic-embed-text (768-dim).
Use --model mxbai-embed-large --dim 1024 --overwrite to upgrade to mxbai.

Throughput: ~800/sec nomic, ~400/sec mxbai with 6 concurrent workers.
545K scored orgs → ~12 min nomic / ~25 min mxbai on the R9700.

Resumable: skips already-embedded EINs (unless --overwrite).

Usage:
    python3 scripts/build_org_embeddings.py                                     # all scored orgs, nomic
    python3 scripts/build_org_embeddings.py --limit 5000                        # test run
    python3 scripts/build_org_embeddings.py --workers 8                         # more concurrency
    python3 scripts/build_org_embeddings.py --model mxbai-embed-large --dim 1024 --overwrite
"""

import sqlite3, json, time, argparse, sys, hashlib
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

DB_PATH       = Path.home() / "meritgiving" / "data" / "merit_registry.db"
OLLAMA_URL    = "http://localhost:11434/api/embed"
VULKAN_URL    = "http://127.0.0.1:11436/v1/embeddings"  # llama-server Vulkan, gfx1201 native
MODEL         = "nomic-embed-text"
BATCH_SIZE    = 100
DIM           = 768
USE_VULKAN    = False  # set True when running mxbai via llama-server

_SCHEMA = """
CREATE TABLE IF NOT EXISTS org_embeddings (
    ein       TEXT PRIMARY KEY,
    vector    BLOB NOT NULL,
    dim       INTEGER NOT NULL,
    text_hash TEXT,
    built_at  TEXT
);
"""

# NTEE1 → human label for richer embedding input
_NTEE_LABELS = {
    "A": "arts culture humanities",
    "B": "education",
    "C": "environment",
    "D": "animal welfare",
    "E": "health care",
    "F": "mental health counseling",
    "G": "disease research medical",
    "H": "medical research",
    "I": "crime legal justice",
    "J": "employment job training",
    "K": "food agriculture nutrition",
    "L": "housing shelter",
    "M": "public safety disaster",
    "N": "recreation sports leisure",
    "O": "youth development",
    "P": "human services family",
    "Q": "international foreign affairs",
    "R": "civil rights social action",
    "S": "community improvement",
    "T": "philanthropy voluntarism grantmaking",
    "U": "science technology research",
    "V": "social science",
    "W": "public benefit society",
    "X": "religion faith spiritual",
    "Y": "mutual benefit member organizations",
    "Z": "unknown",
}

_write_lock = Lock()


def _build_text(row: dict) -> str:
    parts = []
    name = (row.get("organization_name") or "").strip()
    if name:
        parts.append(name)
    ntee1 = row.get("NTEE1") or ""
    label = _NTEE_LABELS.get(ntee1)
    if label:
        parts.append(label)
    tags_raw = row.get("cause_tags") or ""
    if tags_raw:
        try:
            tags = json.loads(tags_raw)
            if isinstance(tags, list) and tags:
                parts.append(", ".join(str(t) for t in tags[:6]))
        except (json.JSONDecodeError, TypeError):
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


def _embed_batch(texts: list[str]) -> np.ndarray | None:
    """Call embedding server; return (n, DIM) float32 array or None on error."""
    try:
        if USE_VULKAN:
            # llama-server /v1/embeddings (OpenAI-compatible)
            r = requests.post(
                VULKAN_URL,
                json={"input": texts},
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()["data"]
            vecs = np.array([d["embedding"] for d in data], dtype=np.float32)
        else:
            r = requests.post(
                OLLAMA_URL,
                json={"model": MODEL, "input": texts},
                timeout=60,
            )
            r.raise_for_status()
            vecs = np.array(r.json()["embeddings"], dtype=np.float32)
        # L2-normalise for cosine similarity via dot product
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vecs / norms
    except Exception as e:
        print(f"\n  [embed error] {e}", flush=True)
        return None


def _write_batch(db: sqlite3.Connection, eins: list[str],
                 vecs: np.ndarray, texts: list[str], now: str):
    rows = [
        (ein, vecs[i].tobytes(), DIM,
         hashlib.md5(texts[i].encode(), usedforsecurity=False).hexdigest()[:8], now)
        for i, ein in enumerate(eins)
    ]
    with _write_lock:
        db.executemany(
            "INSERT OR REPLACE INTO org_embeddings (ein, vector, dim, text_hash, built_at)"
            " VALUES (?,?,?,?,?)",
            rows,
        )
        db.commit()


def run(limit=None, workers=6, model=MODEL, dim=DIM, overwrite=False, vulkan=False, all_orgs=False):
    global MODEL, DIM, USE_VULKAN
    MODEL      = model
    DIM        = dim
    USE_VULKAN = vulkan

    db = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(_SCHEMA)
    db.commit()

    backend = f"Vulkan:{VULKAN_URL}" if USE_VULKAN else f"Ollama:{MODEL}"
    scope   = "all orgs" if all_orgs else "scored orgs only"
    if overwrite:
        already = set()
        print(f"--overwrite: re-embedding {scope}  backend={backend}  dim={DIM}", flush=True)
    else:
        already = {r[0] for r in db.execute("SELECT ein FROM org_embeddings")}
        print(f"Already embedded: {len(already):,}  scope={scope}  backend={backend}  dim={DIM}", flush=True)

    if all_orgs:
        rows = db.execute("""
            SELECT EIN, organization_name, NTEE1, cause_tags, CITY, STATE, mission
            FROM registry_enriched
            ORDER BY ROWID
        """).fetchall()
    else:
        rows = db.execute("""
            SELECT EIN, organization_name, NTEE1, cause_tags, CITY, STATE, mission
            FROM registry_enriched
            WHERE merit_score IS NOT NULL AND merit_score > 0
            ORDER BY merit_score DESC
        """).fetchall()
    cols = ["EIN", "organization_name", "NTEE1", "cause_tags", "CITY", "STATE", "mission"]
    rows = [dict(zip(cols, r)) for r in rows if r[0] not in already]

    if limit:
        rows = rows[:limit]

    total = len(rows)
    print(f"To embed: {total:,}  (workers={workers}, batch={BATCH_SIZE})", flush=True)
    if total == 0:
        print("Nothing to do.")
        db.close()
        return

    # Pre-compute texts
    texts_all = [_build_text(r) for r in rows]
    eins_all  = [r["EIN"] for r in rows]

    # Split into BATCH_SIZE chunks
    chunks = [
        (eins_all[i:i+BATCH_SIZE], texts_all[i:i+BATCH_SIZE])
        for i in range(0, total, BATCH_SIZE)
    ]

    done = 0
    errors = 0
    t0 = time.time()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(_embed_batch, texts): (eins, texts)
                for eins, texts in chunks}
        for fut in as_completed(futs):
            eins, texts = futs[fut]
            vecs = fut.result()
            if vecs is not None and len(vecs) == len(eins):
                _write_batch(db, eins, vecs, texts, now)
                done += len(eins)
            else:
                errors += len(eins)

            if (done + errors) % 5000 < BATCH_SIZE or done + errors == total:
                elapsed = time.time() - t0 + 1e-9
                rate = done / elapsed
                eta  = (total - done - errors) / rate / 60 if rate else 0
                pct  = (done + errors) / total * 100
                print(
                    f"  [{pct:5.1f}%] {done:,} embedded  {errors:,} errors  "
                    f"{rate:.0f}/sec  ETA {eta:.1f}m",
                    end="\r", flush=True,
                )

    elapsed = (time.time() - t0) / 60
    total_stored = db.execute("SELECT COUNT(*) FROM org_embeddings").fetchone()[0]
    print(f"\n\nDone in {elapsed:.1f} min")
    print(f"Total in org_embeddings: {total_stored:,}")
    if errors:
        print(f"Errors (not embedded): {errors:,}")
    db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit",     type=int)
    ap.add_argument("--workers",   type=int, default=6)
    ap.add_argument("--model",     type=str, default=MODEL)
    ap.add_argument("--dim",       type=int, default=DIM)
    ap.add_argument("--overwrite", action="store_true",
                    help="Re-embed all orgs, replacing existing vectors")
    ap.add_argument("--vulkan", action="store_true",
                    help="Use llama-server Vulkan endpoint at 127.0.0.1:11436 instead of Ollama")
    ap.add_argument("--all-orgs", action="store_true",
                    help="Embed all 1.8M orgs, not just scored ones (fills 1.27M gap)")
    args = ap.parse_args()
    run(limit=args.limit, workers=args.workers,
        model=args.model, dim=args.dim, overwrite=args.overwrite,
        vulkan=args.vulkan, all_orgs=args.all_orgs)
