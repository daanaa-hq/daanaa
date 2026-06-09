#!/usr/bin/env python3
"""
Build FAISS approximate nearest neighbor index from org embeddings with GPU acceleration.
Runs on home server weekly; outputs ~300MB faiss_index.bin + ein_map.json.
Used for fast semantic search on droplet.
"""

import sqlite3
import numpy as np
import json
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    import faiss
except ImportError:
    print("ERROR: FAISS not installed. Install with: pip install faiss-gpu or faiss-cpu")
    sys.exit(1)

# Check for GPU support
try:
    res = faiss.StandardGpuResources()
    HAS_GPU = True
    print("✓ GPU (FAISS-GPU) available for acceleration")
except Exception:
    HAS_GPU = False
    print("⚠ GPU not available for FAISS, using CPU")

DB_PATH = os.environ.get("MERIT_DB_PATH", "data/merit_registry.db")
OUTPUT_DIR = os.environ.get("PRECOMPUTE_OUT", "precompute_output")


def decode_vector(blob):
    """Decode BLOB to numpy array (1024-dim float32)."""
    if not blob:
        return None
    try:
        if len(blob) == 4096:  # 1024 * 4 bytes
            return np.frombuffer(blob, dtype=np.float32)
        else:
            return None
    except Exception:
        return None


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Building FAISS index from embeddings ({'GPU' if HAS_GPU else 'CPU'})...")

    # Load embeddings for ALL TAX-DEDUCTIBLE ORGS (501c3, deductibility=1).
    # Memory-safe: count → preallocate one array → stream-fill row by row. This avoids
    # the list-of-1.85M-arrays + np.array() peak (~3x RAM) that OOM-killed the build.
    d = 1024  # dimension
    print("  Counting tax-deductible orgs with embeddings (deductibility=1)...")
    n_rows = cursor.execute("""
        SELECT COUNT(*) FROM org_embeddings oe
        JOIN registry_enriched re ON oe.ein = re.EIN
        WHERE re.deductibility = 1
    """).fetchone()[0]
    # Disk-backed memmap so we never hold the full ~7GB matrix in RAM. This lets the
    # build coexist with the live :5000 API (which preloads ~6GB of embeddings) on a
    # memory-constrained box without OOM. Peak RAM stays ~one row + one add-batch.
    memmap_path = Path(OUTPUT_DIR) / "vectors.f32.memmap"
    print(f"  Streaming {n_rows:,} vectors into disk memmap (~{n_rows * d * 4 / 1e9:.1f}GB on disk)...")
    vectors_np = np.memmap(memmap_path, dtype=np.float32, mode="w+", shape=(n_rows, d))
    ein_list = []
    skipped = 0

    # Server-side streaming cursor (no fetchall — don't pull all blobs into RAM at once).
    stream = conn.cursor()
    stream.execute("""
        SELECT oe.ein, oe.vector
        FROM org_embeddings oe
        JOIN registry_enriched re ON oe.ein = re.EIN
        WHERE re.deductibility = 1
        ORDER BY oe.ein
    """)
    i = 0
    for ein, blob in stream:
        vec = decode_vector(blob)
        if vec is not None and vec.shape[0] == d and i < n_rows:
            n = np.linalg.norm(vec) + 1e-10
            vectors_np[i] = vec / n   # normalize-on-write for cosine similarity
            ein_list.append(ein)
            i += 1
            if i % 200_000 == 0:
                vectors_np.flush()
                print(f"    ...{i:,} loaded", flush=True)
        else:
            skipped += 1
    vectors_np.flush()
    total = i
    vectors_np = vectors_np[:total]  # view into the memmap, no copy
    print(f"  Loaded {total:,} vectors (skipped {skipped} invalid)")

    if total < 100:
        print("ERROR: Too few vectors to build index")
        sys.exit(1)

    print(f"  Vector shape: {vectors_np.shape} (memmap-backed)")

    # Build FAISS index with GPU acceleration
    print("  Building FAISS index...")
    nlist = max(100, min(total // 50000, 500))  # ~50K vectors per cluster, max 500 clusters

    # FAISS_PQ=1 → product-quantized index (IndexIVFPQ): ~64 bytes/vector instead of
    # 4096 (fp32 flat). Shrinks the index ~60x (6.3G → ~150-300M) so it fits the
    # droplet's disk budget. Recall loss is negligible for "similar orgs" surfacing.
    USE_PQ = os.environ.get("FAISS_PQ", "0") == "1"
    PQ_M = int(os.environ.get("FAISS_PQ_M", "64"))   # sub-quantizers (bytes/vector); 1024 % M == 0

    if USE_PQ:
        # Product-quantized index: builds the `index` object, then falls through
        # to the shared save path below (which also writes the required ein_map).
        print(f"  Quantized index (IVFPQ): m={PQ_M} bytes/vector (~{total * PQ_M / 1e6:.0f}MB est)")
        quantizer = faiss.IndexFlatL2(d)
        index = faiss.IndexIVFPQ(quantizer, d, nlist, PQ_M, 8)  # 8 bits per sub-quantizer
        # Train on a sample — PQ codebooks don't need all vectors, and full-set training
        # is memory-heavy. ~256 vectors/centroid is ample.
        train_n = min(total, max(50_000, nlist * 256))
        sample_idx = np.sort(np.random.choice(total, train_n, replace=False))
        train_vecs = np.ascontiguousarray(vectors_np[sample_idx], dtype=np.float32)
        print(f"  Training IVFPQ on {train_n:,} sampled vectors (CPU)...")
        index.train(train_vecs)
        del train_vecs
        print(f"  Adding {total:,} vectors (CPU, batched from memmap)...")
        for off in range(0, total, 100_000):
            batch = np.ascontiguousarray(vectors_np[off:off + 100_000], dtype=np.float32)
            index.add(batch)
    elif HAS_GPU:
        # GPU-accelerated index building
        print("  Using GPU for index training and adding...")

        # Create GPU resources
        res = faiss.StandardGpuResources()

        # Train on GPU first with subset if too large
        if total > 1000000:
            print(f"  Large index detected ({total} vectors). Training on GPU subset...")
            sample_size = min(100000, total // 10)
            sample_indices = np.random.choice(total, sample_size, replace=False)
            vectors_train = vectors_np[sample_indices]
        else:
            vectors_train = vectors_np

        # Create and train index on GPU
        quantizer = faiss.IndexFlatL2(d)
        index = faiss.IndexIVFFlat(quantizer, d, nlist)

        # Transfer quantizer to GPU for training
        gpu_quantizer = faiss.index_cpu_to_gpu(res, 0, quantizer)
        gpu_index = faiss.IndexIVFFlat(gpu_quantizer, d, nlist)

        # Train on GPU
        print(f"  Training on {len(vectors_train)} vectors (GPU)...")
        gpu_index.train(vectors_train)

        # Add all vectors to GPU index
        print(f"  Adding {total} vectors to GPU index (in batches)...")
        batch_size = 100000
        for i in range(0, total, batch_size):
            batch = vectors_np[i:i+batch_size]
            gpu_index.add(batch)
            if i % (batch_size * 5) == 0:
                print(f"    Added {min(i + batch_size, total)}/{total} vectors")

        # Move trained index back to CPU for storage
        print("  Transferring trained index back to CPU...")
        index = faiss.index_gpu_to_cpu(gpu_index)

    else:
        # CPU-only index building
        print("  Using CPU for index training and adding...")
        quantizer = faiss.IndexFlatL2(d)
        index = faiss.IndexIVFFlat(quantizer, d, nlist)

        print(f"  Training index (CPU)...")
        index.train(vectors_np)

        print(f"  Adding {total} vectors (CPU)...")
        index.add(vectors_np)

    print(f"  Index built: {index.ntotal} vectors, {nlist} clusters")

    # Save index
    index_path = Path(OUTPUT_DIR) / "faiss_index.bin"
    print("  Saving index to disk...")
    faiss.write_index(index, str(index_path))
    print(f"  Index saved: {index_path}")

    # Save EIN mapping
    print("  Saving EIN mapping...")
    ein_map = {str(i): ein for i, ein in enumerate(ein_list)}
    ein_map_path = Path(OUTPUT_DIR) / "ein_map.json.gz"

    import gzip
    with gzip.open(ein_map_path, 'wt', encoding='utf-8', compresslevel=1) as f:
        json.dump(ein_map, f, separators=(',', ':'))

    print(f"  EIN map saved: {ein_map_path}")

    # Drop the disk memmap — it's a build scratch file, must NOT ship to the droplet.
    try:
        del vectors_np
        memmap_path.unlink(missing_ok=True)
        print(f"  Cleaned up memmap scratch: {memmap_path.name}")
    except Exception as e:
        print(f"  WARN: could not remove memmap {memmap_path}: {e}")

    conn.close()

    # Summary
    print(f"\n[{datetime.now().isoformat()}] FAISS index build complete!")
    print(f"  Vectors: {total}")
    print(f"  Output: {OUTPUT_DIR}")

    # File sizes
    index_size = index_path.stat().st_size / 1024 / 1024
    ein_map_size = ein_map_path.stat().st_size / 1024 / 1024
    print(f"  Index size: {index_size:.1f} MB")
    print(f"  EIN map size: {ein_map_size:.1f} MB")


if __name__ == '__main__':
    main()
