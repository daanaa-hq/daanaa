#!/usr/bin/env python3
"""
GPU-accelerated link verification using semantic embeddings.

Uses mxbai-embed-large on GPU (port 11436) for batch similarity matching.
Boosts verification confidence using semantic similarity between:
- Candidate link text/URL
- Known donation link patterns
"""

import requests
import numpy as np
import json
import logging
from typing import List, Dict, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

EMBEDDING_SERVICE = "http://127.0.0.1:11436/v1/embeddings"
BATCH_SIZE = 32  # Batch size for GPU embedding

# Known donation link patterns (as reference embeddings)
DONATION_PATTERNS = {
    "donate": "Make a donation to support this organization",
    "give": "Give money to support our mission",
    "fund": "Fund our programs and initiatives",
    "support": "Support this nonprofit with a financial contribution",
    "contribute": "Contribute to our cause",
    "sponsor": "Sponsor our work"
}


class GPULinkVerifier:
    """GPU-accelerated link verification using embeddings."""

    def __init__(self):
        self.pattern_embeddings = None
        self._load_pattern_embeddings()

    def _load_pattern_embeddings(self):
        """Pre-compute embeddings for donation patterns."""
        try:
            patterns_text = list(DONATION_PATTERNS.values())
            response = requests.post(
                EMBEDDING_SERVICE,
                json={"input": patterns_text, "model": "mxbai-embed-large"},
                timeout=10
            )
            if response.status_code == 200:
                self.pattern_embeddings = np.array([
                    item["embedding"] for item in response.json()["data"]
                ], dtype=np.float32)
                logger.info(f"Loaded {len(self.pattern_embeddings)} pattern embeddings on GPU")
            else:
                logger.warning(f"Failed to load pattern embeddings: {response.status_code}")
        except Exception as e:
            logger.warning(f"GPU embedding service unavailable: {e}")

    def embed_batch(self, texts: List[str], timeout=2.0) -> np.ndarray:
        """Embed a batch of texts on GPU with short timeout (non-blocking)."""
        try:
            response = requests.post(
                EMBEDDING_SERVICE,
                json={"input": texts, "model": "mxbai-embed-large"},
                timeout=timeout  # Very short timeout — fail fast if GPU is busy
            )
            if response.status_code == 200:
                embeddings = np.array([
                    item["embedding"] for item in response.json()["data"]
                ], dtype=np.float32)
                return embeddings
        except requests.Timeout:
            logger.debug(f"GPU embedding timeout ({timeout}s) — falling back to CPU")
        except Exception as e:
            logger.debug(f"GPU embedding failed (non-blocking): {e}")
        return None  # Return None on any failure — don't block

    def semantic_similarity(self, candidate_embedding: np.ndarray) -> float:
        """Compute max cosine similarity to any donation pattern."""
        if self.pattern_embeddings is None or candidate_embedding is None:
            return 0.0

        # Normalize for cosine similarity
        candidate_norm = np.linalg.norm(candidate_embedding)
        if candidate_norm == 0:
            return 0.0

        candidate_normalized = candidate_embedding / candidate_norm

        # Compare to all patterns
        similarities = []
        for pattern_emb in self.pattern_embeddings:
            pattern_norm = np.linalg.norm(pattern_emb)
            if pattern_norm > 0:
                pattern_normalized = pattern_emb / pattern_norm
                sim = np.dot(candidate_normalized, pattern_normalized)
                similarities.append(max(0.0, sim))

        return max(similarities) if similarities else 0.0

    def verify_batch(self, candidates: List[Dict]) -> List[Dict]:
        """
        Verify a batch of candidate links using GPU embeddings.

        Args:
            candidates: [{"url": "...", "text": "...", "link_type": "donate|volunteer"}, ...]

        Returns:
            [{"url": "...", "confidence": 0.0-1.0, "semantic_match": float, ...}, ...]
        """
        if not candidates or not self.pattern_embeddings:
            return candidates

        # Extract text for embedding
        texts = [
            f"{c.get('text', '')} {urlparse(c.get('url', '')).path}"
            for c in candidates
        ]

        # Batch embed on GPU
        embeddings = self.embed_batch(texts)
        if embeddings is None or len(embeddings) == 0:
            return candidates

        # Score each candidate
        verified = []
        for candidate, embedding in zip(candidates, embeddings):
            semantic_score = self.semantic_similarity(embedding)
            verified.append({
                **candidate,
                "semantic_match": semantic_score,
                "gpu_verified": True
            })

        return verified


def batch_verify_links(links: List[Dict], verifier: GPULinkVerifier) -> List[Dict]:
    """Verify links in GPU batches."""
    verified = []
    for i in range(0, len(links), BATCH_SIZE):
        batch = links[i:i+BATCH_SIZE]
        verified.extend(verifier.verify_batch(batch))
    return verified


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    verifier = GPULinkVerifier()

    # Test batch
    test_links = [
        {"url": "https://example.org/donate", "text": "Donate now", "link_type": "donate"},
        {"url": "https://example.org/about", "text": "About us", "link_type": "about"},
        {"url": "https://example.org/support", "text": "Support our work", "link_type": "donate"},
    ]

    results = batch_verify_links(test_links, verifier)
    for r in results:
        print(f"{r['url']}: semantic_match={r.get('semantic_match', 0):.3f}")
