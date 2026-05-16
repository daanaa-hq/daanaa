#!/usr/bin/env python3
"""
scripts/build_embeddings.py
Generate semantic embeddings for all orgs in registry_enriched using
the AMD GPU via ROCm, then store them in a sqlite-vec virtual table.

Model: BAAI/bge-large-en-v1.5 (1024-dim, state-of-the-art for semantic search)
Storage: org_embeddings table in merit_registry.db via sqlite-vec

Run time: ~15-20 minutes for 551K orgs on the R9700.

Usage:
    python3 scripts/build_embeddings.py              # full build
    python3 scripts/build_embeddings.py --limit 1000 # quick test
    python3 scripts/build_embeddings.py --rebuild     # drop and rebuild
"""

import sqlite3, struct, sys, argparse, time, json
import sqlite_vec
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

BASE    = Path.home() / "meritgiving"
DB_PATH = BASE / "data" / "merit_registry.db"

MODEL_NAME = "BAAI/bge-large-en-v1.5"
DIMS       = 1024
BATCH_SIZE = 512   # safe for 32GB VRAM with bge-large


def _load_ntee_map():
    """Load ntee_map.json and build a flat (NTEECC → full description) lookup."""
    ntee_map_path = BASE / "ntee_map.json"
    broad = {}
    sub   = {}
    if ntee_map_path.exists():
        data = json.loads(ntee_map_path.read_text())
        for letter, info in data.items():
            broad[letter.upper()] = info.get("name", "")
            for suffix, desc in info.get("subs", {}).items():
                code = letter.upper() + f"{int(suffix):02d}"
                sub[code] = desc
    return broad, sub

_NTEE_BROAD, _NTEE_SUB = _load_ntee_map()


def _ntee_description(nteecc: str) -> str:
    """Return the most specific human-readable NTEE description available."""
    if not nteecc:
        return ""
    nteecc = nteecc.strip()
    letter = nteecc[0].upper() if nteecc else ""
    suffix = nteecc[1:]
    try:
        norm_code = letter + f"{int(suffix[:2]):02d}"
    except (ValueError, IndexError):
        norm_code = ""

    if norm_code and norm_code in _NTEE_SUB:
        broad = _NTEE_BROAD.get(letter, "")
        return f"{_NTEE_SUB[norm_code]}, {broad}" if broad else _NTEE_SUB[norm_code]
    if letter in _NTEE_BROAD:
        return _NTEE_BROAD[letter]
    return ""


def make_text(row) -> str:
    """Build a rich text string from an org row for embedding."""
    ein, name, nteecc, city, state, mission = row
    parts = [name or ""]
    desc = _ntee_description(nteecc or "")
    if desc:
        parts.append(desc)
    if city and state:
        parts.append(f"{city}, {state}")
    elif state:
        parts.append(state)
    if mission and len(mission) > 10:
        parts.append(mission[:300].strip())
    return ". ".join(p for p in parts if p).strip()


def serialize(vec: np.ndarray) -> bytes:
    """Pack float32 array to bytes for sqlite-vec storage."""
    return struct.pack(f"{len(vec)}f", *vec.tolist())


def run(limit=None, rebuild=False):
    import torch
    from sentence_transformers import SentenceTransformer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    if device == "cuda":
        props = torch.cuda.get_device_properties(0)
        print(f"GPU:    {props.name}  ({props.total_memory // 1024**3} GB VRAM)")

    print(f"Model:  {MODEL_NAME}  ({DIMS} dims)")
    print(f"Batch:  {BATCH_SIZE}\n")

    # Load model
    print("Loading model...")
    t0 = time.time()
    model = SentenceTransformer(MODEL_NAME, device=device)
    print(f"  loaded in {time.time()-t0:.1f}s\n")

    # Connect DB + load sqlite-vec
    db = sqlite3.connect(DB_PATH)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)

    if rebuild:
        print("Dropping existing embedding table...")
        db.execute("DROP TABLE IF EXISTS org_embeddings")
        db.execute("DROP TABLE IF EXISTS org_embeddings_meta")
        db.commit()

    # Create virtual table (sqlite-vec) and a metadata companion
    db.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS org_embeddings
        USING vec0(
            ein TEXT PRIMARY KEY,
            embedding float[{DIMS}]
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS org_embeddings_meta (
            ein TEXT PRIMARY KEY,
            text_used TEXT,
            embedded_at TEXT
        )
    """)
    db.commit()

    # Find orgs that need embedding
    already = {r[0] for r in db.execute("SELECT ein FROM org_embeddings_meta").fetchall()}
    print(f"Already embedded: {len(already):,}")

    rows = db.execute("""
        SELECT EIN, organization_name, NTEECC, CITY, STATE, mission
        FROM registry_enriched
        ORDER BY COALESCE(ntee1_percentile, 0) DESC
    """).fetchall()

    if limit:
        rows = rows[:limit]

    to_embed = [r for r in rows if r[0] not in already]
    print(f"To embed:         {len(to_embed):,}")
    print(f"Total orgs:       {len(rows):,}\n")

    if not to_embed:
        print("Nothing to do — all orgs already embedded.")
        db.close()
        return

    now    = datetime.now(timezone.utc).isoformat()
    total  = len(to_embed)
    done   = 0
    t_start = time.time()

    for batch_start in range(0, total, BATCH_SIZE):
        batch = to_embed[batch_start : batch_start + BATCH_SIZE]
        texts = [make_text(r) for r in batch]

        vecs = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            normalize_embeddings=True,   # cosine sim = dot product after normalizing
            device=device,
        )

        vec_rows  = [(r[0], serialize(vecs[i])) for i, r in enumerate(batch)]
        meta_rows = [(r[0], texts[i], now) for i, r in enumerate(batch)]

        db.executemany(
            "INSERT OR REPLACE INTO org_embeddings(ein, embedding) VALUES (?, ?)",
            vec_rows
        )
        db.executemany(
            "INSERT OR REPLACE INTO org_embeddings_meta(ein, text_used, embedded_at) VALUES (?, ?, ?)",
            meta_rows
        )
        db.commit()

        done += len(batch)
        elapsed = time.time() - t_start
        rate    = done / elapsed
        eta     = (total - done) / rate if rate > 0 else 0
        pct     = done / total * 100
        print(f"  [{pct:5.1f}%] {done:,}/{total:,}  "
              f"{rate:.0f} orgs/s  ETA {eta/60:.1f}m", end="\r", flush=True)

    print(f"\n\nDone — {done:,} embeddings in {(time.time()-t_start)/60:.1f} minutes")

    # Quick sanity: find most similar to a known org
    print("\nSanity check — orgs most similar to 'American Red Cross':")
    ref = db.execute(
        "SELECT embedding FROM org_embeddings e "
        "JOIN registry_enriched r ON r.EIN = e.ein "
        "WHERE r.organization_name LIKE '%Red Cross%' LIMIT 1"
    ).fetchone()
    if ref:
        similar = db.execute("""
            SELECT r.organization_name, r.NTEE1, r.STATE,
                   distance
            FROM org_embeddings
            JOIN registry_enriched r ON r.EIN = org_embeddings.ein
            WHERE embedding MATCH ? AND k = 5
            ORDER BY distance
        """, (ref[0],)).fetchall()
        for name, ntee, state, dist in similar:
            print(f"  {name[:50]:<50} | {ntee} | {state} | dist={dist:.4f}")

    db.close()
    print(f"\nEmbeddings stored in {DB_PATH}")
    print("Next: restart merit_api.py to enable /api/search/semantic\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Only embed N orgs (for testing)")
    parser.add_argument("--rebuild", action="store_true", help="Drop and rebuild all embeddings")
    args = parser.parse_args()
    run(limit=args.limit, rebuild=args.rebuild)
