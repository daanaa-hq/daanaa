#!/usr/bin/env python3
"""
Build FAISS approximate nearest neighbor index from org embeddings with GPU acceleration.
Runs on home server weekly; outputs ~300MB faiss_index.bin + ein_map.json.
Used for fast semantic search on droplet.
"""

import sqlite3
import numpy as np
import json
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

DB_PATH = "data/merit_registry.db"
OUTPUT_DIR = "precompute_output"


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

    # Load embeddings for ALL TAX-DEDUCTIBLE ORGS (501c3, deductibility=1)
    print("  Loading embeddings for tax-deductible orgs (deductibility=1)...")
    cursor.execute("""
        SELECT oe.ein, oe.vector
        FROM org_embeddings oe
        JOIN registry_enriched re ON oe.ein = re.EIN
        WHERE re.deductibility = 1
        ORDER BY oe.ein
    """)

    vectors = []
    ein_list = []
    skipped = 0

    for ein, blob in cursor.fetchall():
        vec = decode_vector(blob)
        if vec is not None:
            vectors.append(vec)
            ein_list.append(ein)
        else:
            skipped += 1

    total = len(ein_list)
    print(f"  Loaded {total} vectors (skipped {skipped} invalid)")

    if total < 100:
        print("ERROR: Too few vectors to build index")
        sys.exit(1)

    # Convert to numpy array
    vectors_np = np.array(vectors, dtype=np.float32)

    # Normalize vectors for cosine similarity
    print("  Normalizing vectors...")
    norms = np.linalg.norm(vectors_np, axis=1, keepdims=True)
    vectors_np = vectors_np / (norms + 1e-10)

    print(f"  Vector shape: {vectors_np.shape}")

    # Build FAISS index with GPU acceleration
    print("  Building FAISS index...")
    d = 1024  # dimension
    nlist = max(100, min(total // 50000, 500))  # ~50K vectors per cluster, max 500 clusters

    if HAS_GPU:
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
