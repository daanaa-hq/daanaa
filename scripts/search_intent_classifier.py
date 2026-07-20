#!/usr/bin/env python3
"""
Search Intent Classifier — Detect cause vs. organization name queries (Search Phase 2).

Goal: Route cause-shaped queries ("mental health", "food justice") to semantic search
(org embeddings + themes) instead of FTS keyword matching (organization_name).

Heuristic (fast, no ML):
- Cause patterns: plural nouns, adjective+noun, common cause keywords
- Org patterns: proper nouns (title case), acronyms, EINs
- Semantic path: query embedding → cosine similarity against org embeddings
- FTS path: keyword FTS5 on organization_name (exact match first)

Usage:
  python3 scripts/search_intent_classifier.py --test
  python3 scripts/search_intent_classifier.py --classify "mental health"
  python3 scripts/search_intent_classifier.py --classify "Cleveland Foundation"
"""

import re
import sys
import json
import sqlite3
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).parent.parent
DB = REPO_ROOT / "data" / "merit_registry.db"

# Cause keywords commonly searched (mined from zero-result analytics + domain)
CAUSE_KEYWORDS = {
    "food", "hunger", "mental health", "health", "healthcare", "education",
    "homeless", "homelessness", "housing", "poverty", "justice", "environment",
    "climate", "water", "animal", "animals", "pet", "pets", "arts", "culture",
    "music", "youth", "elder", "elderly", "disability", "disabled", "women",
    "lgbtq", "racial justice", "voting", "immigrant", "refugee", "disaster",
    "relief", "community", "development", "economic", "job", "jobs", "training",
    "literacy", "medical", "medicine", "research", "disease", "cure", "foster",
    "adoption", "domestic violence", "sexual assault", "substance", "addiction",
    "recovery", "counseling", "therapy", "faith", "religion", "conservation",
    "wildlife", "parks", "trails", "local", "outreach", "nonprofit", "charity",
}

class SearchIntentClassifier:
    def __init__(self, db_path=DB):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row

    def classify(self, query: str) -> dict:
        """Classify query as 'cause', 'organization', or 'ambiguous'."""
        query_lower = query.strip().lower()
        query_tokens = query_lower.split()

        # EIN: pure digits → organization
        if re.match(r'^\d{9}$', query_lower):
            return {
                "query": query,
                "intent": "organization",
                "confidence": 0.99,
                "reason": "EIN format",
                "suggested_path": "fts_exact"
            }

        # Acronym (e.g., "YMCA", "WWF") → organization
        if re.match(r'^[A-Z]{2,}$', query) and len(query) <= 6:
            return {
                "query": query,
                "intent": "organization",
                "confidence": 0.85,
                "reason": "acronym pattern",
                "suggested_path": "fts_exact"
            }

        # Title case (proper noun) → organization
        if query != query_lower and not re.match(r'^[a-z]', query):
            return {
                "query": query,
                "intent": "organization",
                "confidence": 0.70,
                "reason": "title case (proper noun)",
                "suggested_path": "fts_exact"
            }

        # Cause keyword detection (word boundary — don't match "education" in "educational technology")
        cause_matches = 0
        for kw in CAUSE_KEYWORDS:
            if re.search(rf'\b{re.escape(kw)}\b', query_lower):
                cause_matches += 1
        cause_score = min(cause_matches / max(1, len(query_tokens)), 1.0)

        # Multi-word cause patterns: "food justice", "mental health", etc.
        if len(query_tokens) >= 2:
            # Common patterns: <adjective/noun> <cause noun>
            # "affordable housing", "youth employment", "racial justice"
            if any(kw in query_lower for kw in ["housing", "health", "justice", "employment", "violence", "justice"]):
                cause_score = min(cause_score + 0.3, 1.0)

        # Plural noun → likely cause (multiple orgs in category)
        if query_tokens[-1].endswith('s') and query_lower not in ["corps", "arts"]:
            cause_score = min(cause_score + 0.15, 1.0)

        # Decide based on cause_score
        if cause_score >= 0.65:
            return {
                "query": query,
                "intent": "cause",
                "confidence": min(cause_score, 1.0),
                "reason": "cause keyword(s) detected",
                "suggested_path": "semantic_embedding"
            }
        elif cause_score <= 0.25:
            return {
                "query": query,
                "intent": "organization",
                "confidence": 1 - cause_score,
                "reason": "likely organization name",
                "suggested_path": "fts_exact"
            }
        else:
            return {
                "query": query,
                "intent": "ambiguous",
                "confidence": 0.5,
                "reason": "could be either; try both paths",
                "suggested_path": "fts_with_semantic_rerank"
            }

    def test_queries(self):
        """Test on known cause and org queries."""
        test_cases = [
            # Causes
            ("mental health services", "cause"),
            ("food banks", "cause"),
            ("homeless shelters", "cause"),
            ("youth employment", "cause"),
            ("racial justice", "cause"),
            ("animal rescue", "cause"),
            # Organizations
            ("Cleveland Foundation", "organization"),
            ("YMCA", "organization"),
            ("Red Cross", "organization"),
            ("123456789", "organization"),
            ("Boys and Girls Club", "organization"),
            # Ambiguous
            ("community health center", "ambiguous"),
            ("education", "ambiguous"),
            ("local nonprofits", "ambiguous"),
        ]

        print("Testing Search Intent Classifier")
        print("=" * 60)
        passed = 0
        for query, expected in test_cases:
            result = self.classify(query)
            status = "✓" if result["intent"] == expected else "✗"
            if result["intent"] == expected:
                passed += 1
            print(f"{status} {query:40} → {result['intent']:12} (conf={result['confidence']:.2f})")
        print("=" * 60)
        print(f"Passed {passed}/{len(test_cases)}")
        return passed == len(test_cases)


if __name__ == "__main__":
    classifier = SearchIntentClassifier()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            sys.exit(0 if classifier.test_queries() else 1)
        elif sys.argv[1] == "--classify" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            result = classifier.classify(query)
            print(json.dumps(result, indent=2))
        else:
            print(__doc__)
            sys.exit(1)
    else:
        print(__doc__)
