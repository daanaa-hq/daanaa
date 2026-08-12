#!/usr/bin/env python3
"""
FAISS Documentation Index Builder

Indexes key Daanaa documentation for fast semantic search.
Used to answer architecture questions without full-file context in Codex.

Usage:
    python3 scripts/build_faiss_docs_index.py [--rebuild]

Output:
    - data/docs_faiss_index.db (vector index)
    - data/docs_faiss_metadata.json (doc chunks + embeddings)
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import faiss
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: sentence-transformers not installed. Install with: pip install sentence-transformers")
    sys.exit(1)


class DocsIndexBuilder:
    """Build and search FAISS index of Daanaa documentation."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.data_dir = self.repo_root / "data"
        self.docs_dir = self.repo_root / "docs"
        self.index_path = self.data_dir / "docs_faiss_index.db"
        self.metadata_path = self.data_dir / "docs_faiss_metadata.json"

        # Use mxbai-embed-large for consistency with org embeddings
        print("Loading embedding model (mxbai-embed-large)...")
        self.model = SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")
        self.embedding_dim = 1024

        self.index = None
        self.metadata = []

    def load_docs(self) -> List[Dict[str, str]]:
        """Load key documentation files and split into chunks."""
        docs = []

        # Core architecture docs (max 8KB chunks for efficiency)
        key_docs = [
            ("CLAUDE.md", self.repo_root / "CLAUDE.md"),
            ("STEWARDSHIP.md", self.repo_root / "STEWARDSHIP.md"),
            ("PRIVACY-INVARIANTS.md", self.repo_root / "PRIVACY-INVARIANTS.md"),
            ("DECISIONS.md", self.repo_root / "DECISIONS.md"),
            ("LESSONS.md", self.repo_root / "LESSONS.md"),
            ("institution/CONSTITUTION.md", self.repo_root / "institution" / "CONSTITUTION.md"),
        ]

        for doc_name, doc_path in key_docs:
            if not doc_path.exists():
                print(f"  ⚠️  {doc_name} not found, skipping")
                continue

            print(f"  Loading {doc_name}...")
            content = doc_path.read_text(encoding="utf-8", errors="ignore")

            # Split on section headers (##) to create natural chunks
            chunks = self._chunk_text(content, max_chunk_size=8000)
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) > 100:  # Skip tiny chunks
                    docs.append({
                        "source": doc_name,
                        "chunk_id": i,
                        "text": chunk,
                    })

        print(f"  Total chunks: {len(docs)}")
        return docs

    def _chunk_text(self, text: str, max_chunk_size: int = 8000) -> List[str]:
        """Split text into chunks at section boundaries."""
        chunks = []
        current_chunk = ""

        for line in text.split("\n"):
            if line.startswith("##") and current_chunk and len(current_chunk) > 1000:
                # Start new chunk at section header
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
                if len(current_chunk) > max_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = ""

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def build_index(self, docs: List[Dict[str, str]]) -> None:
        """Build FAISS index from documents."""
        print(f"\nBuilding FAISS index for {len(docs)} chunks...")

        # Embed all docs
        texts = [doc["text"] for doc in docs]
        print(f"  Embedding {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=32)
        embeddings = np.array(embeddings, dtype="float32")

        # Create FAISS index
        print("  Creating FAISS index...")
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.index.add(embeddings)

        # Store metadata
        self.metadata = [
            {
                "source": doc["source"],
                "chunk_id": doc["chunk_id"],
                "text_preview": doc["text"][:200],  # First 200 chars for preview
                "text_length": len(doc["text"]),
                "embedding_shape": embeddings.shape,
            }
            for doc in docs
        ]

        print(f"  Index complete: {len(embeddings)} vectors of {self.embedding_dim} dims")

    def save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        if self.index is None:
            print("ERROR: No index to save. Call build_index() first.")
            sys.exit(1)

        print(f"\nSaving index to {self.index_path}...")
        os.makedirs(self.data_dir, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))

        print(f"Saving metadata to {self.metadata_path}...")
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)

        print("✅ Index saved successfully")

    def load_index(self) -> bool:
        """Load existing FAISS index from disk."""
        if not self.index_path.exists() or not self.metadata_path.exists():
            return False

        print(f"Loading index from {self.index_path}...")
        self.index = faiss.read_index(str(self.index_path))

        with open(self.metadata_path, "r") as f:
            self.metadata = json.load(f)

        print(f"✅ Loaded {len(self.metadata)} chunks")
        return True

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search index for similar documentation."""
        if self.index is None:
            if not self.load_index():
                print("ERROR: No index found. Build with build_index() first.")
                return []

        # Embed query
        query_embedding = self.model.encode([query], show_progress_bar=False)
        query_embedding = np.array(query_embedding, dtype="float32")

        # Search
        distances, indices = self.index.search(query_embedding, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result["distance"] = float(distances[0][i])
                result["rank"] = i + 1
                results.append(result)

        return results


def main():
    rebuild = "--rebuild" in sys.argv

    builder = DocsIndexBuilder(repo_root=".")

    # Try loading existing index
    if not rebuild and builder.load_index():
        print("\n✅ Existing index loaded. Use --rebuild to recreate.")
        return

    # Build new index
    docs = builder.load_docs()
    if not docs:
        print("ERROR: No documents loaded.")
        sys.exit(1)

    builder.build_index(docs)
    builder.save_index()

    # Test search
    print("\n" + "="*60)
    print("Testing search...")
    print("="*60)

    test_queries = [
        "How does V6 scoring work?",
        "What are STEWARDSHIP principles?",
        "How should we handle wallet data?",
        "IRS eligibility verification process",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = builder.search(query, k=3)
        for result in results:
            print(f"  [{result['rank']}] {result['source']} (dist: {result['distance']:.3f})")
            print(f"      {result['text_preview'][:100]}...")


if __name__ == "__main__":
    main()
