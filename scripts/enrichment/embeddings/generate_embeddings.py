#!/usr/bin/env python3
import sqlite3, numpy as np, sys, time
from pathlib import Path
DB = Path.home() / "meritgiving/data/meritgiving.db"
try:
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    if device == 'cuda':
        print(f"GPU detected: {torch.cuda.get_device_name(0)}")
except ImportError:
    device = 'cpu'
from sentence_transformers import SentenceTransformer
print(f"Loading model on {device}...")
model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
print("Model loaded. 384-dim embeddings.")
conn = sqlite3.connect(str(DB))
cursor = conn.cursor()
cursor.execute("SELECT EIN, NAME FROM registry_enriched WHERE NAME IS NOT NULL AND NAME != ''")
rows = cursor.fetchall()
total = len(rows)
print(f"Found {total:,} organizations to embed")
cursor.execute("DROP TABLE IF EXISTS org_embeddings")
cursor.execute("CREATE TABLE org_embeddings (EIN TEXT PRIMARY KEY, vector BLOB, dim INTEGER)")
batch_size = 512 if device == 'cuda' else 48
start = time.time()
for i in range(0, total, batch_size):
    batch = rows[i:i+batch_size]
    eins = [r[0] for r in batch]
    names = [r[1] for r in batch]
    vecs = model.encode(names, convert_to_numpy=True, show_progress_bar=False)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1
    vecs = (vecs / norms).astype(np.float32)
    to_insert = [(eins[j], vecs[j].tobytes(), vecs.shape[1]) for j in range(len(batch))]
    cursor.executemany("INSERT INTO org_embeddings VALUES (?, ?, ?)", to_insert)
    if (i // batch_size) % 20 == 0:
        elapsed = time.time() - start
        rate = (i + len(batch)) / elapsed if elapsed > 0 else 0
        print(f"  {min(i+batch_size, total):,} / {total:,}  ({rate:.0f}/sec)")
conn.commit()
count = cursor.execute("SELECT COUNT(*) FROM org_embeddings").fetchone()[0]
print(f"\nDone. Stored {count:,} embeddings in {time.time()-start:.1f}s")
conn.close()
