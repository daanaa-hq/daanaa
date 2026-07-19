#!/usr/bin/env python3
"""
Search Semantic Reranker — Boost cause queries with org embeddings (Search Phase 2).

For queries identified as 'cause' by intent classifier, rerank FTS5 results
using cosine similarity against org embeddings (mxbai-embed-large vectors).

This delivers "mental health organization" results where:
- FTS5 gives relevance (keyword match quality)
- Embeddings give semantics (orgs whose embedding is similar to cause query)

Pipeline:
1. Classify query (cause vs. org)
2. If cause: embed query using local inference (llama.cpp:11436)
3. Fetch top-20 FTS5 keyword results
4. Compute cosine similarity (query_embedding · org_embeddings)
5. Rerank: (FTS5 BM25 score * 0.3) + (cosine similarity * 0.7)
6. Return top-N by composite score

This is non-invasive — frontend still gets exact same org objects,
just in better order for cause queries.

Usage:
  python3 scripts/search_semantic_reranker.py --test
  python3 scripts/search_semantic_reranker.py --embed "mental health"
  python3 scripts/search_semantic_reranker.py --rerank "mental health" --top 10
"""

import sys
import json
import sqlite3
import requests
from pathlib import Path
from typing import Optional
import numpy as np

REPO_ROOT = Path(__file__).parent.parent
DB = REPO_ROOT / "data" / "merit_registry.db"

# Local embedding server (llama.cpp, mxbai-embed-large)
EMBED_URL = "http://127.0.0.1:11436/api/embeddings"
EMBED_MODEL = "mxbai-embed-large"

# Weights for composite score: (BM25 * w_fts) + (cosine_sim * w_semantic)
W_FTS = 0.3
W_SEMANTIC = 0.7

class SearchSemanticReranker:
    def __init__(self, db_path=DB):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        # Preload embeddings from database (if org_embeddings table exists)
        self._embeddings_cache = {}
        self._load_embeddings_cache()

    def _load_embeddings_cache(self):
        """Load org→embedding mapping from database (expensive on startup)."""
        try:
            cursor = self.conn.execute("SELECT ein, embedding FROM org_embeddings LIMIT 1000")
            for row in cursor.fetchall():
                ein = row[0]
                embedding_json = row[1]
                if embedding_json:
                    try:
                        self._embeddings_cache[ein] = np.array(json.loads(embedding_json))
                    except (json.JSONDecodeError, TypeError):
                        pass
        except sqlite3.OperationalError:
            pass  # org_embeddings table may not exist

    def embed_query(self, query: str) -> Optional[np.ndarray]:
        """Get embedding for query string via local inference."""
        try:
            resp = requests.post(
                EMBED_URL,
                json={"input": query, "model": EMBED_MODEL},
                timeout=5
            )
            resp.raise_for_status()
            data = resp.json()
            embedding = data.get("data", [{}])[0].get("embedding")
            if embedding:
                return np.array(embedding)
        except Exception as e:
            pass  # Fallback: no semantic reranking
        return None

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        try:
            dot = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(dot / (norm_a * norm_b))
        except Exception:
            return 0.0

    def rerank_fts_results(self, query: str, fts_results: list) -> list:
        """
        Rerank FTS5 results using semantic similarity to query.

        Args:
            query: search query string
            fts_results: list of dicts with {ein, org_name, fts_score, ...}

        Returns:
            Reranked list (same objects, sorted by composite score)
        """
        if not fts_results:
            return fts_results

        # Get query embedding
        query_embedding = self.embed_query(query)
        if query_embedding is None:
            # Fallback: return FTS order unchanged
            return fts_results

        # Compute composite scores
        scored = []
        for result in fts_results:
            ein = result.get('ein')
            fts_score = result.get('fts_score', 0.0)  # Normalized 0-1

            # Get org embedding (from cache or DB)
            org_embedding = self._embeddings_cache.get(ein)
            if org_embedding is None:
                try:
                    row = self.conn.execute(
                        "SELECT embedding FROM org_embeddings WHERE ein = ?",
                        (ein,)
                    ).fetchone()
                    if row and row[0]:
                        org_embedding = np.array(json.loads(row[0]))
                except (sqlite3.OperationalError, json.JSONDecodeError, TypeError):
                    pass

            # Compute similarity
            similarity = 0.0
            if org_embedding is not None:
                similarity = self.cosine_similarity(query_embedding, org_embedding)

            # Composite score: weighted blend
            composite = (fts_score * W_FTS) + (similarity * W_SEMANTIC)

            scored.append({
                **result,
                'semantic_score': similarity,
                'composite_score': composite
            })

        # Rerank by composite score (descending)
        reranked = sorted(scored, key=lambda x: x['composite_score'], reverse=True)
        return reranked

    def test_reranking(self):
        """Test reranking on a known cause query."""
        print("Testing Search Semantic Reranker")
        print("=" * 60)

        # Simulate FTS results (ein, name, bm25_score)
        test_query = "mental health"
        test_fts_results = [
            {"ein": "123456789", "name": "Mental Health Foundation", "fts_score": 0.95},
            {"ein": "234567890", "name": "Community Health Center", "fts_score": 0.80},
            {"ein": "345678901", "name": "Wellness Alliance", "fts_score": 0.70},
        ]

        print(f"Query: {test_query}")
        print(f"FTS Results (before): {len(test_fts_results)} orgs")

        # Try reranking
        print(f"\nEmbedding query '{test_query}'...")
        query_emb = self.embed_query(test_query)
        if query_emb is not None:
            print(f"✓ Query embedding: {len(query_emb)}-dim vector")
            reranked = self.rerank_fts_results(test_query, test_fts_results)
            print("\nReranked results:")
            for i, result in enumerate(reranked[:3], 1):
                print(f"  {i}. {result['name']}")
                print(f"     FTS={result.get('fts_score', 0):.2f}, "
                      f"Semantic={result.get('semantic_score', 0):.2f}, "
                      f"Composite={result.get('composite_score', 0):.3f}")
        else:
            print("✗ Could not embed query (inference server down?)")
            print("  This is OK — fallback to FTS order")

        print("=" * 60)


if __name__ == "__main__":
    reranker = SearchSemanticReranker()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            reranker.test_reranking()
        elif sys.argv[1] == "--embed" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            emb = reranker.embed_query(query)
            if emb is not None:
                print(f"Query: {query}")
                print(f"Embedding: {emb[:5]}... ({len(emb)}-dim)")
            else:
                print(f"Could not embed: {query}")
        else:
            print(__doc__)
    else:
        print(__doc__)
