#!/usr/bin/env python3
import sqlite3, numpy as np, sys
from pathlib import Path
from sentence_transformers import SentenceTransformer

DB = Path.home() / "meritgiving/data/meritgiving.db"

def load_index():
    """Load all embeddings into RAM once (880MB for 573K × 384 dims)."""
    conn = sqlite3.connect(str(DB))
    cursor = conn.cursor()
    print("Loading index into RAM...")
    cursor.execute("SELECT EIN, vector FROM org_embeddings")
    eins, vectors = [], []
    for ein, blob in cursor:
        eins.append(ein)
        vectors.append(np.frombuffer(blob, dtype=np.float32))
    conn.close()
    return np.array(eins), np.array(vectors)

EINS, INDEX = load_index()
print(f"Index ready: {INDEX.shape[0]:,} orgs × {INDEX.shape[1]} dims")

model = SentenceTransformer('all-MiniLM-L6-v2')

def search(query, top_k=10):
    qvec = model.encode([query], convert_to_numpy=True)
    qvec = qvec / np.linalg.norm(qvec)
    
    # Cosine similarity via dot product (vectors are pre-normalized)
    scores = np.dot(INDEX, qvec[0])
    top_idx = np.argsort(scores)[-top_k:][::-1]
    
    conn = sqlite3.connect(str(DB))
    cursor = conn.cursor()
    print(f"\nTop {top_k} matches for: '{query}'")
    print("-" * 70)
    for rank, idx in enumerate(top_idx, 1):
        ein = EINS[idx]
        score = scores[idx]
        row = cursor.execute(
            "SELECT NAME, NTEE, REVENUE, STATE FROM registry_enriched WHERE EIN=?", (ein,)
        ).fetchone()
        name, ntee, rev, state = row if row else ("?", "?", 0, "?")
        rev_str = f"${rev:,.0f}" if rev else "$0"
        print(f"{rank:2d}. {name} | {ntee} | {state} | {rev_str:<15s} | {score:.3f}")
    conn.close()

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "cancer research"
    search(query)
