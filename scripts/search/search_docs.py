#!/usr/bin/env python3
"""
Search Documentation Index

Fast semantic search of Daanaa docs without loading full files.
Used in Codex prompts to reduce context overhead.

Usage:
    python3 scripts/search_docs.py "How does V6 scoring work?" [--k 3]

Output:
    JSON array of top-k most relevant docs
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import faiss

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: sentence-transformers not installed. Install with: pip install sentence-transformers")
    sys.exit(1)


class DocsSearcher:
    """Search FAISS index of Daanaa documentation."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.index_path = self.repo_root / "data" / "docs_faiss_index.db"
        self.metadata_path = self.repo_root / "data" / "docs_faiss_metadata.json"
        self.docs_dir = self.repo_root / "docs"

        self.model = SentenceTransformer("mixedbread-ai/mxbai-embed-large-v1")
        self.index = None
        self.metadata = []
        self._load()

    def _load(self) -> bool:
        """Load FAISS index and metadata."""
        if not self.index_path.exists():
            print(f"ERROR: Index not found at {self.index_path}")
            print("Build with: python3 scripts/build_faiss_docs_index.py")
            return False

        self.index = faiss.read_index(str(self.index_path))

        with open(self.metadata_path, "r") as f:
            self.metadata = json.load(f)

        return True

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documentation."""
        if self.index is None:
            return []

        # Embed query
        query_embedding = self.model.encode([query], show_progress_bar=False)
        query_embedding = np.array(query_embedding, dtype="float32")

        # Search
        distances, indices = self.index.search(query_embedding, min(k, len(self.metadata)))

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                meta = self.metadata[idx].copy()
                meta["distance"] = float(distances[0][i])
                meta["rank"] = i + 1

                # Load full text
                source_path = self.repo_root / meta["source"]
                if source_path.exists():
                    full_text = source_path.read_text(encoding="utf-8", errors="ignore")
                    # Extract relevant chunk
                    meta["full_text"] = full_text[:2000]  # First 2KB for brevity
                else:
                    meta["full_text"] = None

                results.append(meta)

        return results

    def format_for_codex(self, query: str, k: int = 3) -> str:
        """Format search results for Codex prompt."""
        results = self.search(query, k)

        output = []
        output.append(f"Documentation Search Results for: {query}\n")
        output.append("=" * 70)

        for result in results:
            output.append(f"\n[{result['rank']}] {result['source']}")
            output.append(f"    Distance: {result['distance']:.3f} (lower = more relevant)")
            output.append(f"    Length: {result['text_length']} chars")
            if result['full_text']:
                output.append(f"    Content:\n{result['full_text'][:500]}")
            output.append("")

        return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/search_docs.py '<query>' [--k 5] [--json]")
        print("\nExample:")
        print("  python3 scripts/search_docs.py 'How does V6 scoring work?'")
        print("  python3 scripts/search_docs.py 'privacy principles' --k 5 --json")
        sys.exit(1)

    query = sys.argv[1]
    k = 3
    output_json = False

    for arg in sys.argv[2:]:
        if arg.startswith("--k="):
            k = int(arg.split("=")[1])
        elif arg == "--k" and len(sys.argv) > sys.argv.index(arg) + 1:
            k = int(sys.argv[sys.argv.index(arg) + 1])
        elif arg == "--json":
            output_json = True

    searcher = DocsSearcher(repo_root=".")

    if output_json:
        results = searcher.search(query, k)
        print(json.dumps(results, indent=2))
    else:
        formatted = searcher.format_for_codex(query, k)
        print(formatted)


if __name__ == "__main__":
    main()
